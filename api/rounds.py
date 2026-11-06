"""Responses and aggregates (Lane B task 3).

Rules enforced here:
- v1 once per invite per round; v2 (the Delphi revision) once, only after v1,
  and with the same author token as v1. Closed rounds accept nothing.
- Aggregates only after the caller's own v1, and per question only when
  n >= MIN_N distinct authors (each author counted once, latest version).
- Dots are returned sorted, so they cannot be matched to an author.
"""
import statistics
from datetime import datetime, timezone
from typing import Optional

from api import db, trust

MIN_N = 3


class RoundError(trust.TrustError):
    pass


def get_round(round_id: str) -> dict:
    with db.main_db() as m:
        row = m.execute("SELECT * FROM rounds WHERE round_id = ?", (round_id,)).fetchone()
    if row is None:
        raise RoundError(404, "round not found")
    return dict(row)


def _round_questions(m, risk_id: str) -> dict:
    return {r["question_id"]: dict(r) for r in
            m.execute("SELECT question_id, trigger_id FROM questions WHERE risk_id = ?", (risk_id,))}


def _short_trigger(tid: str) -> str:
    return tid.split(" - ")[-1].strip()


def submit(round_id: str, invite_token: str, tier: str, device_secret: Optional[str], version: int,
           answers: list[dict], triggers_observed: list[str], missing_text: Optional[str]) -> dict:
    rnd = get_round(round_id)
    if rnd["stage"] == "closed":
        raise RoundError(409, "round is closed")
    token = trust.authenticate(invite_token, tier, device_secret)
    if not answers:
        raise RoundError(422, "no answers")

    with db.main_db() as m, db.vault_db() as v:
        questions = _round_questions(m, rnd["risk_id"])
        qids = [a["question_id"] for a in answers]
        if len(qids) != len(set(qids)):
            raise RoundError(422, "duplicate question in answers")
        unknown = [q for q in qids if q not in questions]
        if unknown:
            raise RoundError(422, f"questions not in this round: {unknown}")
        valid_triggers = {q["trigger_id"] for q in questions.values() if q["trigger_id"]}
        observed = sorted({_short_trigger(t) for t in triggers_observed})
        if set(observed) - valid_triggers:
            raise RoundError(422, f"triggers not in this risk: {sorted(set(observed) - valid_triggers)}")

        done = {r[0] for r in v.execute(
            "SELECT version FROM round_participation WHERE round_id = ? AND invite_token = ?",
            (round_id, invite_token))}
        if version in done:
            raise RoundError(409, "already submitted" if version == 1 else "already revised once")
        if version == 2:
            if 1 not in done:
                raise RoundError(409, "submit round 1 before revising")
            has_v1 = m.execute("SELECT 1 FROM contributions WHERE round_id = ? AND author_token = ? "
                               "AND version = 1 LIMIT 1", (round_id, token)).fetchone()
            if not has_v1:
                raise RoundError(409, "revise with the same anonymity tier as your first answer")

        if m.execute("SELECT 1 FROM contributions WHERE round_id = ? AND author_token = ? AND version = ?"
                     " LIMIT 1", (round_id, token, version)).fetchone():
            raise RoundError(409, "this author token already answered this version")

        now = datetime.now(timezone.utc).isoformat()
        for i, a in enumerate(answers):
            agree = a.get("agree")
            m.execute(
                "INSERT INTO contributions (round_id, question_id, author_token, tier, prob, agree,"
                " missing_text, version, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (round_id, a["question_id"], token, tier, a.get("prob"),
                 None if agree is None else int(agree), missing_text if i == 0 else None, version, now))
        m.executemany("INSERT INTO observed_triggers VALUES (?,?,?,?)",
                      [(round_id, token, t, version) for t in observed])
        v.execute("INSERT INTO round_participation VALUES (?,?,?)", (round_id, invite_token, version))

    return {"round_id": round_id, "author_token": token, "version": version, "stored": len(answers),
            "can_revise": version == 1, "aggregate_unlocked": True}


def _latest(m, round_id: str) -> list:
    """One row per (author, question): the highest version."""
    return m.execute(
        "SELECT c.* FROM contributions c JOIN ("
        "  SELECT author_token, question_id, MAX(version) v FROM contributions"
        "  WHERE round_id = ? GROUP BY author_token, question_id) l"
        " ON c.author_token = l.author_token AND c.question_id = l.question_id AND c.version = l.v"
        " WHERE c.round_id = ?", (round_id, round_id)).fetchall()


def aggregate(round_id: str, invite_token: str, device_secret: Optional[str] = None) -> dict:
    rnd = get_round(round_id)
    trust.rate_limit(invite_token)
    expert_id = trust.check_invite(invite_token)["expert_id"]
    candidates = [trust.pseudonym_token(expert_id)]
    if device_secret:
        candidates.append(trust.anonymous_token(device_secret))

    with db.main_db() as m:
        rows = _latest(m, round_id)
        mine = [r for r in rows if r["author_token"] in candidates]
        if not mine:
            raise RoundError(403, "submit your own answer first")
        my_token = mine[0]["author_token"]
        revised = m.execute("SELECT 1 FROM contributions WHERE round_id = ? AND author_token = ? "
                            "AND version = 2 LIMIT 1", (round_id, my_token)).fetchone()
        questions = _round_questions(m, rnd["risk_id"])
        obs = m.execute(
            "SELECT o.trigger_id, COUNT(DISTINCT o.author_token) n FROM observed_triggers o JOIN ("
            "  SELECT author_token, MAX(version) v FROM contributions WHERE round_id = ?"
            "  GROUP BY author_token) l ON o.author_token = l.author_token AND o.version = l.v"
            " WHERE o.round_id = ? GROUP BY o.trigger_id", (round_id, round_id)).fetchall()
        n_authors = m.execute("SELECT COUNT(DISTINCT author_token) FROM contributions WHERE round_id = ?",
                              (round_id,)).fetchone()[0]

    out_q = []
    for qid in questions:
        qrows = [r for r in rows if r["question_id"] == qid]
        n = len({r["author_token"] for r in qrows})
        if n < MIN_N:
            out_q.append({"question_id": qid, "suppressed": True, "n": f"<{MIN_N}"})
            continue
        item = {"question_id": qid, "suppressed": False, "n": n}
        agrees = [r["agree"] for r in qrows if r["agree"] is not None]
        probs = sorted(r["prob"] for r in qrows if r["prob"] is not None)
        if agrees:
            item["agree_share"] = round(sum(agrees) / len(agrees), 2)
        if len(probs) >= MIN_N:
            p25, p50, p75 = statistics.quantiles(probs, n=4, method="inclusive")
            item.update(median=round(p50, 3), p25=round(p25, 3), p75=round(p75, 3),
                        dots=[round(p, 2) for p in probs])
        out_q.append(item)

    triggers = ([{"trigger_id": r["trigger_id"], "share": round(r["n"] / n_authors, 2)} for r in obs]
                if n_authors >= MIN_N else [])
    your = {r["question_id"]: (r["prob"] if r["prob"] is not None else bool(r["agree"])) for r in mine}
    return {"round_id": round_id, "stage": rnd["stage"], "min_n": MIN_N,
            "suppressed": all(q["suppressed"] for q in out_q),
            "questions": out_q, "triggers_observed": triggers,
            "your_answers": your, "can_revise": not revised and rnd["stage"] != "closed"}
