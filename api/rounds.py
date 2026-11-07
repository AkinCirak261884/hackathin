"""Rounds: responses, lifecycle and aggregates (Lane B tasks 3 + 4).

Lifecycle  blind -> reveal -> closed  (moderator advances; never backwards)
- blind:  first answers (v1) only. After your own v1 you get a *locked* view: no numbers yet,
          so the distribution never changes in real time (timing can't identify the latest answer).
- reveal: Delphi round 2. Everyone who answered sees the *frozen v1* distribution and may revise
          once (v2). No new v1 answers (they'd be anchored).
- closed: nothing accepted. View = final answers (each author's latest version).

Always: v1 once per invite per round; v2 once, same author token as v1; aggregates only after your
own v1; each question suppressed until n >= MIN_N distinct authors; dots sorted (unlinkable).
"""
from functools import lru_cache
from pathlib import Path
import re
import csv
import statistics
from datetime import datetime, timezone
from typing import Optional

from api import comments_policy, db, trust

MIN_N = 3
STAGES = ("blind", "reveal", "closed")
REASONING_BASES = ("field_observation", "local_contacts", "media_osint", "reports_data", "experience")


class RoundError(trust.TrustError):
    pass


# ---------- lookups ----------

def get_round(round_id: str) -> dict:
    with db.main_db() as m:
        row = m.execute("SELECT * FROM rounds WHERE round_id = ?", (round_id,)).fetchone()
    if row is None:
        raise RoundError(404, "round not found")
    return dict(row)


def _round_questions(m, rnd: dict) -> dict:
    """The round's own question list; falls back to all questions of the risk."""
    rows = m.execute(
        "SELECT q.* FROM round_questions rq JOIN questions q ON q.question_id = rq.question_id"
        " WHERE rq.round_id = ? ORDER BY q.trigger_id IS NOT NULL, q.question_id", (rnd["round_id"],)).fetchall()
    if not rows:
        rows = m.execute("SELECT * FROM questions WHERE risk_id = ? ORDER BY trigger_id IS NOT NULL, question_id",
                         (rnd["risk_id"],)).fetchall()
    return {r["question_id"]: dict(r) for r in rows}


def _short_trigger(tid: str) -> str:
    return tid.split(" - ")[-1].strip()


def _n_authors(m, round_id: str, version: Optional[int] = None) -> int:
    sql = "SELECT COUNT(DISTINCT author_token) FROM contributions WHERE round_id = ?"
    args: tuple = (round_id,)
    if version:
        sql, args = sql + " AND version = ?", (round_id, version)
    return m.execute(sql, args).fetchone()[0]


# ---------- create / advance (moderator) ----------

def create_round(risk_id: str, question_set: str = "core", question_ids: Optional[list[str]] = None,
                 panel: str = "TCD", round_id: Optional[str] = None) -> dict:
    with db.main_db() as m:
        if not m.execute("SELECT 1 FROM risks WHERE risk_id = ?", (risk_id,)).fetchone():
            raise RoundError(404, "risk not found")
        if question_ids:
            qids = [r[0] for r in m.execute(
                f"SELECT question_id FROM questions WHERE risk_id = ? AND question_id IN "
                f"({','.join('?' * len(question_ids))})", (risk_id, *question_ids))]
            missing = sorted(set(question_ids) - set(qids))
            if missing:
                raise RoundError(422, f"questions not found for {risk_id}: {missing}")
        else:
            qids = [r[0] for r in m.execute(
                "SELECT question_id FROM questions WHERE risk_id = ? AND question_set = ?", (risk_id, question_set))]
        if not qids:
            raise RoundError(422, f"no '{question_set}' questions for {risk_id}")
        if round_id is None:
            n = m.execute("SELECT COUNT(*) FROM rounds WHERE risk_id = ?", (risk_id,)).fetchone()[0]
            prefix = "P" if question_set == "short_horizon" else ""
            round_id = f"RND-{risk_id}-{prefix}{n + 1}"
        m.execute("INSERT INTO rounds (round_id, risk_id, stage, opened_at, panel) VALUES (?,?,?,?,?)",
                  (round_id, risk_id, "blind", datetime.now(timezone.utc).date().isoformat(), panel.upper()))
        m.executemany("INSERT INTO round_questions VALUES (?,?)", [(round_id, q) for q in qids])
    return {"round_id": round_id, "risk_id": risk_id, "stage": "blind", "panel": panel.upper(),
            "question_ids": qids}


def advance(round_id: str, to: Optional[str] = None) -> dict:
    rnd = get_round(round_id)
    i = STAGES.index(rnd["stage"])
    if i == len(STAGES) - 1:
        raise RoundError(409, "round is already closed")
    nxt = STAGES[i + 1]
    if to is not None and to != nxt:
        raise RoundError(409, f"can only advance {rnd['stage']} -> {nxt}")
    with db.main_db() as m:
        n = _n_authors(m, round_id, version=1)
        if nxt == "reveal" and n < MIN_N:
            raise RoundError(409, f"need at least {MIN_N} answers to reveal (have {n})")
        stamp = ", closed_at = ?" if nxt == "closed" else ""
        args = (nxt, datetime.now(timezone.utc).isoformat(), round_id) if stamp else (nxt, round_id)
        m.execute(f"UPDATE rounds SET stage = ?{stamp} WHERE round_id = ?", args)
    return {"round_id": round_id, "from_stage": rnd["stage"], "to_stage": nxt, "n_responses": n}


# ---------- responses ----------

def submit(round_id: str, invite_token: str, tier: str, device_secret: Optional[str], version: int,
           answers: list[dict], triggers_observed: list[str], missing_text: Optional[str],
           reasoning_text: Optional[str] = None, reasoning_basis: Optional[list[str]] = None) -> dict:
    rnd = get_round(round_id)
    if rnd["stage"] == "closed":
        raise RoundError(409, "round is closed")
    if version == 1 and rnd["stage"] != "blind":
        raise RoundError(409, "round 1 is over; you can join the next round")
    if version == 2 and rnd["stage"] != "reveal":
        raise RoundError(409, "revisions open when the moderator reveals the group view")
    token = trust.authenticate(invite_token, tier, device_secret)
    if not answers:
        raise RoundError(422, "no answers")
    bad_basis = sorted(set(reasoning_basis or []) - set(REASONING_BASES))
    if bad_basis:
        raise RoundError(422, f"unknown reasoning_basis: {bad_basis}")
    basis = ",".join(sorted(set(reasoning_basis or []))) or None

    with db.main_db() as m, db.vault_db() as v:
        questions = _round_questions(m, rnd)
        qids = [a["question_id"] for a in answers]
        if len(qids) != len(set(qids)):
            raise RoundError(422, "duplicate question in answers")
        unknown = [q for q in qids if q not in questions]
        if unknown:
            raise RoundError(422, f"questions not in this round: {unknown}")
        valid_triggers = {q["trigger_id"] for q in questions.values() if q["trigger_id"]}
        observed = sorted({_short_trigger(t) for t in triggers_observed})
        if set(observed) - valid_triggers:
            raise RoundError(422, f"triggers not in this round: {sorted(set(observed) - valid_triggers)}")

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
                " missing_text, reasoning_text, reasoning_basis, version, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (round_id, a["question_id"], token, tier, a.get("prob"), None if agree is None else int(agree),
                 *((missing_text, reasoning_text, basis) if i == 0 else (None, None, None)), version, now))
        m.executemany("INSERT INTO observed_triggers VALUES (?,?,?,?)",
                      [(round_id, token, t, version) for t in observed])
        v.execute("INSERT INTO round_participation VALUES (?,?,?)", (round_id, invite_token, version))

    return {"round_id": round_id, "author_token": token, "version": version, "stored": len(answers),
            "can_revise": False, "aggregate_unlocked": rnd["stage"] != "blind",
            "next": "wait for the moderator to reveal the group view" if version == 1 else "thanks, revision saved"}


# ---------- aggregates ----------

def _rows(m, round_id: str, v1_only: bool) -> list:
    """v1_only: frozen round-1 answers. Else one row per (author, question) at its latest version."""
    if v1_only:
        return m.execute("SELECT * FROM contributions WHERE round_id = ? AND version = 1", (round_id,)).fetchall()
    return m.execute(
        "SELECT c.* FROM contributions c JOIN ("
        "  SELECT author_token, question_id, MAX(version) v FROM contributions"
        "  WHERE round_id = ? GROUP BY author_token, question_id) l"
        " ON c.author_token = l.author_token AND c.question_id = l.question_id AND c.version = l.v"
        " WHERE c.round_id = ?", (round_id, round_id)).fetchall()


def _latest_version_join(v1_only: bool) -> str:
    """SQL fragment: per author, the version the current view uses."""
    return ("(SELECT author_token, 1 v FROM contributions WHERE round_id = ? GROUP BY author_token)"
            if v1_only else
            "(SELECT author_token, MAX(version) v FROM contributions WHERE round_id = ? GROUP BY author_token)")


def question_stats(rows: list, qid: str, min_n: int = MIN_N) -> dict:
    qrows = [r for r in rows if r["question_id"] == qid]
    n = len({r["author_token"] for r in qrows})
    if n < min_n:
        return {"question_id": qid, "suppressed": True, "n": f"<{min_n}"}
    item = {"question_id": qid, "suppressed": False, "n": n}
    agrees = [r["agree"] for r in qrows if r["agree"] is not None]
    probs = sorted(r["prob"] for r in qrows if r["prob"] is not None)
    if agrees:
        item["agree_share"] = round(sum(agrees) / len(agrees), 2)
    if len(probs) >= max(min_n, 2):
        p25, p50, p75 = statistics.quantiles(probs, n=4, method="inclusive")
        item.update(median=round(p50, 3), p25=round(p25, 3), p75=round(p75, 3), dots=[round(p, 2) for p in probs])
    return item


def _caller(invite_token: str, device_secret: Optional[str]) -> list[str]:
    trust.rate_limit(invite_token)
    expert_id = trust.check_invite(invite_token)["expert_id"]
    tokens = [trust.pseudonym_token(expert_id)]
    if device_secret:
        tokens.append(trust.anonymous_token(device_secret))
    return tokens


def aggregate(round_id: str, invite_token: str, device_secret: Optional[str] = None) -> dict:
    """Collective view only (team decision, 7 Nov): the caller never gets their own answers back,
    only the group's numbers (which include their answer once n >= 3)."""
    rnd = get_round(round_id)
    candidates = _caller(invite_token, device_secret)
    stage = rnd["stage"]
    with db.main_db() as m:
        latest = _rows(m, round_id, v1_only=False)
        mine = [r for r in latest if r["author_token"] in candidates]
        if not mine:
            raise RoundError(403, "submit your own answer first")
        my_token = mine[0]["author_token"]
        revised = m.execute("SELECT 1 FROM contributions WHERE round_id = ? AND author_token = ? "
                            "AND version = 2 LIMIT 1", (round_id, my_token)).fetchone()
        questions = _round_questions(m, rnd)
        v1_only = stage == "reveal"
        rows = [] if stage == "blind" else _rows(m, round_id, v1_only)
        obs = [] if stage == "blind" else m.execute(
            f"SELECT o.trigger_id, COUNT(DISTINCT o.author_token) n FROM observed_triggers o JOIN "
            f"{_latest_version_join(v1_only)} l ON o.author_token = l.author_token AND o.version = l.v"
            f" WHERE o.round_id = ? GROUP BY o.trigger_id", (round_id, round_id)).fetchall()
        n_authors = _n_authors(m, round_id)

    if stage == "blind":
        out_q = [{"question_id": q, "suppressed": True, "n": None} for q in questions]
    else:
        out_q = [question_stats(rows, q) for q in questions]
    triggers = ([{"trigger_id": r["trigger_id"], "share": round(r["n"] / n_authors, 2)} for r in obs]
                if n_authors >= MIN_N else [])
    return {"round_id": round_id, "stage": stage, "min_n": MIN_N,
            "locked": stage == "blind",
            "view": {"blind": "locked", "reveal": "round_1", "closed": "final"}[stage],
            "suppressed": all(q["suppressed"] for q in out_q),
            "questions": out_q, "triggers_observed": triggers,
            "can_revise": stage == "reveal" and not revised}


def thread(round_id: str, invite_token: str, device_secret: Optional[str] = None) -> dict:
    """Peer view of a round (Lane C's feed thread): the aggregate, reasoning-basis shares and
    moderator-approved themes. Never individual replies, authors, timestamps or verbatim free text."""
    agg = aggregate(round_id, invite_token, device_secret)  # same gates: 403, locked in blind, n >= 3
    basis: list = []
    with db.main_db() as m:
        if not agg["locked"]:
            v1_only = agg["stage"] == "reveal"
            firsts = m.execute(
                f"SELECT c.reasoning_basis FROM contributions c JOIN {_latest_version_join(v1_only)} l"
                f" ON c.author_token = l.author_token AND c.version = l.v"
                f" WHERE c.round_id = ? AND c.reasoning_basis IS NOT NULL", (round_id, round_id)).fetchall()
            n_authors = _n_authors(m, round_id)
            counts: dict[str, int] = {}
            for r in firsts:
                for b in r["reasoning_basis"].split(","):
                    counts[b] = counts.get(b, 0) + 1
            if n_authors >= MIN_N:
                basis = [{"basis": b, "share": round(n / n_authors, 2)} for b, n in sorted(counts.items())]
        approved = m.execute("SELECT approved_text, published_at FROM summaries WHERE round_id = ?",
                             (round_id,)).fetchone()
    themes = [{"text": approved["approved_text"], "approved_at": approved["published_at"]}] if approved else []
    return {**agg, "reasoning_basis": basis, "themes": themes, "comments": round_comments(round_id)}


def round_comments(round_id: str) -> dict:
    """Peer comments on/off for this round: the automatic rule (comments_policy), unless the moderator turned them off."""
    rnd = get_round(round_id)
    with db.main_db() as m:
        risk = _risk(m, rnd["risk_id"])
        off = comments_off(m, round_id)
    return with_moderator(comments_policy.decide(risk), off)


# ---------- moderator override: peer comments off for one round ----------
# Only ever stricter than the automatic rule: the moderator can turn comments off (and back to automatic),
# never force them on where the rule says off.
_SETTINGS_DDL = ("CREATE TABLE IF NOT EXISTS round_settings (round_id TEXT PRIMARY KEY REFERENCES rounds(round_id),"
                 " comments_off INTEGER NOT NULL DEFAULT 0, updated_at TEXT)")
_settings_ready: set = set()


def _ensure_settings(m) -> None:
    """The hosted DB gets schema changes only from `python -m api.seed`, so this table is created on first use."""
    where = db.DATABASE_URL or str(db.MAIN_DB)
    if where in _settings_ready:
        return
    if not db.DATABASE_URL:
        m.execute(_SETTINGS_DDL)
    elif not m.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema()"
                       " AND table_name = 'round_settings'").fetchone():
        m.execute(_SETTINGS_DDL)
        m.execute("ALTER TABLE round_settings ENABLE ROW LEVEL SECURITY")  # same lock-down as pg.init: RLS, no policies
    _settings_ready.add(where)


def comments_off(m, round_id: str) -> bool:
    _ensure_settings(m)
    r = m.execute("SELECT comments_off FROM round_settings WHERE round_id = ?", (round_id,)).fetchone()
    return bool(r and r["comments_off"])


def with_moderator(decision: dict, off: bool) -> dict:
    if not off:
        return {**decision, "moderator_off": False}
    return {**decision, "enabled": False, "basis": "moderator", "moderator_off": True,
            "auto_enabled": decision.get("enabled"),
            "reason": "the ACAPS moderator turned peer comments off for this round"}


def set_comments_off(round_id: str, off: bool) -> dict:
    get_round(round_id)  # 404 if unknown
    with db.main_db() as m:
        _ensure_settings(m)
        m.execute("DELETE FROM round_settings WHERE round_id = ?", (round_id,))
        m.execute("INSERT INTO round_settings (round_id, comments_off, updated_at) VALUES (?,?,?)",
                  (round_id, int(off), datetime.now(timezone.utc).isoformat()))
    return round_comments(round_id)


# ---------- expert-facing round info ----------

def _risk(m, risk_id: str) -> dict:
    r = m.execute("SELECT * FROM risks WHERE risk_id = ?", (risk_id,)).fetchone()
    return dict(r) if r else {"risk_id": risk_id}


def _submitted(m, round_id: str, tokens: list[str]) -> bool:
    if not tokens:
        return False
    return bool(m.execute(
        f"SELECT 1 FROM contributions WHERE round_id = ? AND author_token IN ({','.join('?' * len(tokens))})"
        " LIMIT 1", (round_id, *tokens)).fetchone())


def list_open(panel: str, invite_token: Optional[str] = None, device_secret: Optional[str] = None) -> dict:
    tokens = _caller(invite_token, device_secret) if invite_token else []
    with db.main_db() as m:
        rnds = m.execute("SELECT * FROM rounds WHERE panel = ? AND stage != 'closed' ORDER BY opened_at, round_id",
                         (panel.upper(),)).fetchall()
        out = []
        for r in rnds:
            risk = _risk(m, r["risk_id"])
            out.append({"round_id": r["round_id"], "risk_id": r["risk_id"], "stage": r["stage"],
                        "opened_at": r["opened_at"], "risk_title": risk.get("title"),
                        "n_questions": len(_round_questions(m, dict(r))),
                        "you_submitted": _submitted(m, r["round_id"], tokens) if tokens else None})
    return {"panel": panel.upper(), "rounds": out}


def list_all(panel: Optional[str] = None) -> dict:
    """Moderator: every round with stage and n, newest first."""
    with db.main_db() as m:
        q = "SELECT * FROM rounds" + (" WHERE panel = ?" if panel else "") + " ORDER BY opened_at DESC, round_id"
        rnds = m.execute(q, (panel.upper(),) if panel else ()).fetchall()
        out = []
        for r in rnds:
            risk = _risk(m, r["risk_id"])
            out.append({"round_id": r["round_id"], "risk_id": r["risk_id"], "panel": r["panel"],
                        "stage": r["stage"], "opened_at": r["opened_at"], "risk_title": risk.get("title"),
                        "country": risk.get("country"), "n_responses": _n_authors(m, r["round_id"])})
    return {"rounds": out}


@lru_cache(maxsize=1)
def _radar_rows() -> dict:
    """Risk Radar export by risk id (public ACAPS fields the round card shows: rationale, trend, exposure)."""
    path = Path(__file__).resolve().parent.parent / "data" / "risk-radar-export.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as f:
        return {r["Risk ID"]: r for r in csv.DictReader(f)}


def _radar_extra(risk_id: str) -> dict:
    """Fills the gap Lane A's smoke test found (W3): the expert app shows rationale, trend and exposure."""
    r = _radar_rows().get(risk_id)
    if not r:
        return {}
    text = re.sub(r"\s+", " ", r.get("Rationale") or "").strip()
    short = " ".join(re.split(r"(?<=[.!?])\s+", text)[:2])
    if len(short) > 400:  # cut at a word, never mid-word
        short = short[:400].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    # full text for the app's "Read more": paragraphs kept (one per line), spaces inside a line collapsed
    full = "\n".join(p for p in (re.sub(r"[ \t]+", " ", line).strip()
                                 for line in (r.get("Rationale") or "").splitlines()) if p)
    return {"rationale_short": short or None, "rationale": full or None,
            "trend": (r.get("Risk trend") or "").strip() or None,
            "expected_exposure": (r.get("Expected exposure") or "").strip() or None}


def round_detail(round_id: str) -> dict:
    rnd = get_round(round_id)
    with db.main_db() as m:
        risk = _risk(m, rnd["risk_id"])
        questions = list(_round_questions(m, rnd).values())
        tids = sorted({q["trigger_id"] for q in questions if q["trigger_id"]})
        triggers = [dict(t) for t in m.execute(
            f"SELECT trigger_id, title, description, completion_rate FROM triggers WHERE risk_id = ? AND trigger_id IN "
            f"({','.join('?' * len(tids))}) ORDER BY trigger_id", (rnd["risk_id"], *tids))] if tids else []
        off = comments_off(m, round_id)
    for q in questions:
        q["kind"] = "agree" if q["trigger_id"] is None else "forecast"
        q.pop("outcome", None)  # never reveal resolution data through the round card
    return {"round_id": round_id, "risk_id": rnd["risk_id"], "stage": rnd["stage"], "panel": rnd["panel"],
            "opened_at": rnd["opened_at"], "risk_title": risk.get("title"),
            "risk": {**{k: risk.get(k) for k in ("risk_id", "country", "probability", "impact", "level", "status")},
                     **_radar_extra(rnd["risk_id"])},
            "triggers": triggers, "questions": questions, "comments": with_moderator(comments_policy.decide(risk), off)}


# ---------- moderator view ----------

def moderator_free_text(round_id: str) -> list[dict]:
    """Moderator-only: free text linked to response ids (not to authors)."""
    get_round(round_id)
    with db.main_db() as m:
        rows = m.execute(
            "SELECT id, version, tier, missing_text, reasoning_text, reasoning_basis FROM contributions"
            " WHERE round_id = ? AND (missing_text IS NOT NULL OR reasoning_text IS NOT NULL"
            " OR reasoning_basis IS NOT NULL) ORDER BY id", (round_id,)).fetchall()
    return [{"response_id": r["id"], "version": r["version"], "tier": r["tier"],
             "missing_text": r["missing_text"], "reasoning_text": r["reasoning_text"],
             "reasoning_basis": r["reasoning_basis"].split(",") if r["reasoning_basis"] else []}
            for r in rows]


def demo_reset(round_id: str) -> dict:
    """TEMPORARY demo-only (main.py gates it on GT_DEMO_RESET=1): the round back to 'blind' with no answers,
    so the pitch demo can start again. Deletes this round's answers, "I'm seeing this" ticks, AI-synthesis
    cache, published summary and "this invite already answered" rows, and puts peer comments back to automatic.
    Other rounds are untouched."""
    get_round(round_id)  # 404 if unknown
    with db.main_db() as m, db.vault_db() as v:
        n = m.execute("SELECT COUNT(DISTINCT author_token) FROM contributions WHERE round_id = ?",
                      (round_id,)).fetchone()[0]
        for table in ("contributions", "observed_triggers", "syntheses", "summaries"):
            m.execute(f"DELETE FROM {table} WHERE round_id = ?", (round_id,))
        m.execute("UPDATE rounds SET stage = 'blind', closed_at = NULL WHERE round_id = ?", (round_id,))
        _ensure_settings(m)
        m.execute("DELETE FROM round_settings WHERE round_id = ?", (round_id,))  # comments back to automatic
        v.execute("DELETE FROM round_participation WHERE round_id = ?", (round_id,))
    return {"round_id": round_id, "stage": "blind", "removed_responses": n}


FIELD_BASES = ("field_observation", "local_contacts")


def basis_split(m, round_id: str, questions, rows: list, min_n: int = MIN_N) -> dict:
    """Moderator only: answers from experts who ticked "What I see myself" or "Local contacts" on the "Based on"
    step ('field') next to those who ticked only other sources ('remote'). Self-declared: no location, IP or
    text analysis. Each side only from n >= min_n authors, so a small group can't be singled out."""
    bases: dict[str, set] = {}
    for r in m.execute("SELECT author_token, reasoning_basis FROM contributions"
                       " WHERE round_id = ? AND reasoning_basis IS NOT NULL", (round_id,)).fetchall():
        bases.setdefault(r["author_token"], set()).update(r["reasoning_basis"].split(","))  # v2 rows carry none
    group = {a: "field" if bases.get(a, set()) & set(FIELD_BASES) else "remote" if bases.get(a) else "not_stated"
             for a in {r["author_token"] for r in rows}}
    out = []
    for qid in questions:
        field = question_stats([r for r in rows if group[r["author_token"]] == "field"], qid, min_n)
        remote = question_stats([r for r in rows if group[r["author_token"]] == "remote"], qid, min_n)
        item = {"question_id": qid, "field": field, "remote": remote}
        if field.get("median") is not None and remote.get("median") is not None:
            item["median_gap"] = round(field["median"] - remote["median"], 3)
        if field.get("agree_share") is not None and remote.get("agree_share") is not None:
            item["agree_gap"] = round(field["agree_share"] - remote["agree_share"], 2)
        out.append(item)
    return {"field_bases": list(FIELD_BASES), "min_n": min_n,
            "groups": {g: sum(1 for x in group.values() if x == g) for g in ("field", "remote", "not_stated")},
            "questions": out}


def moderator_view(round_id: str) -> dict:
    """ACAPS moderator only. Sees n and distributions from 1 answer up (trusted), plus revision shifts."""
    rnd = get_round(round_id)
    with db.main_db() as m:
        risk = _risk(m, rnd["risk_id"])
        questions = _round_questions(m, rnd)
        v1 = _rows(m, round_id, v1_only=True)
        final = _rows(m, round_id, v1_only=False)
        v2 = m.execute("SELECT * FROM contributions WHERE round_id = ? AND version = 2", (round_id,)).fetchall()
        # MAX(tier): 'pseudonymous' > 'known', so one pseudonymous answer means "don't resolve me"
        authors = m.execute("SELECT author_token, MAX(tier) tier FROM contributions WHERE round_id = ?"
                            " GROUP BY author_token ORDER BY MIN(id)", (round_id,)).fetchall()
        split = basis_split(m, round_id, questions, final)
        off = comments_off(m, round_id)
    v1_by = {(r["author_token"], r["question_id"]): r for r in v1}
    shifts = []
    for qid in questions:
        d = [r["prob"] - v1_by[(r["author_token"], qid)]["prob"] for r in v2
             if r["question_id"] == qid and r["prob"] is not None
             and (r["author_token"], qid) in v1_by and v1_by[(r["author_token"], qid)]["prob"] is not None]
        if d:
            shifts.append({"question_id": qid, "n_revised": len(d), "mean_shift": round(statistics.mean(d), 3),
                           "mean_abs_shift": round(statistics.mean(abs(x) for x in d), 3)})
    agree_rows = [r["agree"] for r in final if r["agree"] is not None]
    return {
        "round_id": round_id, "risk_id": rnd["risk_id"], "stage": rnd["stage"], "panel": rnd["panel"],
        "n_responses": len(authors), "n_revised": len({r["author_token"] for r in v2}),
        "can_advance_to": None if rnd["stage"] == "closed" else STAGES[STAGES.index(rnd["stage"]) + 1],
        "acaps_rating": {"probability": risk.get("probability"), "impact": risk.get("impact"),
                         "level": risk.get("level")},
        "agree_share": round(sum(agree_rows) / len(agree_rows), 2) if agree_rows else None,
        "questions": {"round_1": [question_stats(v1, q, min_n=1) for q in questions],
                      "final": [question_stats(final, q, min_n=1) for q in questions]},
        "revision_shifts": shifts,
        "basis_split": split,
        "contributors": [{"author_token": a["author_token"], "tier": a["tier"],
                          "identity": trust.resolve_identity(a["author_token"], a["tier"])} for a in authors],
        "free_text": moderator_free_text(round_id),
        "comments": with_moderator(comments_policy.decide(risk), off),
    }
