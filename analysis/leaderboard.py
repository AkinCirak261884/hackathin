"""Per-question track record and the super-estimator leaderboard.

Works on any DB with the BOARD.md tables (Lane B's api/var/groundtruth.db or analysis/backtest.db):
reads `contributions`, `questions` (with `outcome`), `risks` (ACAPS probability label), `experts`.

    track_record(con, author_token)   -> the shape Lane B serves at GET /me/track-record
                                         (resolved "history" + unresolved "pending")
    leaderboard(con, viewer_token)    -> peer-visible ranking: display names only, no tokens

Rules:
- An expert is ranked only after MIN_RESOLVED resolved forecasts (final answer: v2 if revised).
- Ranking uses mean Brier shrunk towards the group mean: (n·mean + K·group) / (n + K), so a lucky
  expert with few forecasts can't top the board.
- "Super estimator" = at least MIN_RESOLVED resolved forecasts AND mean Brier lower than ACAPS's
  mean Brier on exactly the same questions (paired), using ACAPS's rating of the question's risk.
- Anonymous-tier tokens show as "Anonymous expert". Tokens in the optional `leaderboard_opt_out`
  table (author_token TEXT PRIMARY KEY) are left out of the leaderboard entirely.
"""

import statistics

from scoring import ACAPS_PROB, APP_MAPPING, brier

MIN_RESOLVED = 5
SHRINK_K = 5  # pseudo-forecasts at the group mean


def resolved_answers(con):
    """Every author's final answer on a resolved question, with ACAPS's forecast for it."""
    rows = con.execute("""
        SELECT c.author_token, c.question_id, q.text, q.closes_at, c.prob, q.outcome, r.probability
        FROM contributions c
        JOIN questions q ON q.question_id = c.question_id
        JOIN risks r ON r.risk_id = q.risk_id
        WHERE c.prob IS NOT NULL AND q.outcome IS NOT NULL
          AND c.version = (SELECT MAX(version) FROM contributions c2
                           WHERE c2.author_token = c.author_token AND c2.question_id = c.question_id)
        ORDER BY q.closes_at, c.question_id
    """).fetchall()
    by_token = {}
    for token, qid, text, closes_at, prob, outcome, label in rows:
        acaps_p = ACAPS_PROB.get(label)
        b = brier(prob, outcome)
        acaps_b = brier(acaps_p, outcome) if acaps_p is not None else None
        by_token.setdefault(token, []).append({
            "question_id": qid,
            "text": text,
            "closes_at": closes_at,
            "outcome": outcome,
            "outcome_label": "happened" if outcome else "didn't happen",
            "your_prob": prob,
            "brier": round(b, 4),
            "acaps_prob": acaps_p,
            "acaps_brier": round(acaps_b, 4) if acaps_b is not None else None,
            "beat_acaps": (b < acaps_b) if acaps_b is not None else None,
        })
    return by_token


def _has(con, table, column=None):
    if column is None:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
    return any(row[1] == column for row in con.execute(f"PRAGMA table_info({table})"))


def pending_answers(con, author_token):
    """The author's final answers on questions that haven't resolved yet, soonest deadline first.
    Same item shape as Lane C's fixtures/me_track_record.json "pending"."""
    title = "(SELECT t.title FROM triggers t WHERE t.trigger_id = q.trigger_id)" if _has(con, "triggers") else "NULL"
    created = "c.created_at" if _has(con, "contributions", "created_at") else "NULL"
    rows = con.execute(f"""
        SELECT c.question_id, {title}, q.text, c.prob, q.closes_at, {created}
        FROM contributions c
        JOIN questions q ON q.question_id = c.question_id
        WHERE c.author_token = ? AND c.prob IS NOT NULL AND q.outcome IS NULL
          AND c.version = (SELECT MAX(version) FROM contributions c2
                           WHERE c2.author_token = c.author_token AND c2.question_id = c.question_id)
        ORDER BY q.closes_at, c.question_id
    """, (author_token,)).fetchall()
    return [
        {"question_id": qid, "title": t, "title_fr": None, "text": text, "text_fr": None,
         "your_prob": prob, "closes_at": closes_at, "submitted_at": submitted_at}
        for qid, t, text, prob, closes_at, submitted_at in rows
    ]


def shrunk(mean, n, group_mean, k=SHRINK_K):
    return (n * mean + k * group_mean) / (n + k)


def _stats(history):
    n = len(history)
    paired = [h for h in history if h["acaps_brier"] is not None]
    mean = statistics.mean(h["brier"] for h in history) if history else None
    acaps_same = statistics.mean(h["acaps_brier"] for h in paired) if paired else None
    yours_same = statistics.mean(h["brier"] for h in paired) if paired else None
    return {
        "n_resolved": n,
        "mean_brier": round(mean, 4) if mean is not None else None,
        "acaps_brier_same_questions": round(acaps_same, 4) if acaps_same is not None else None,
        "n_beat_acaps": sum(bool(h["beat_acaps"]) for h in paired),
        "super_estimator": n >= MIN_RESOLVED and bool(paired) and yours_same < acaps_same,
    }


def _display_name(con, token):
    if token.startswith("anon_"):
        return "Anonymous expert"
    if token.startswith("psd_"):
        row = con.execute("SELECT pseudonym FROM experts WHERE expert_id = ?", (token[len("psd_"):],)).fetchone()
        if row:
            return row[0]
    return "Expert"


def _opted_out(con):
    exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='leaderboard_opt_out'").fetchone()
    return {t for (t,) in con.execute("SELECT author_token FROM leaderboard_opt_out")} if exists else set()


def _ranking(con, by_token=None):
    by_token = by_token if by_token is not None else resolved_answers(con)
    all_briers = [h["brier"] for hs in by_token.values() for h in hs]
    group_mean = statistics.mean(all_briers) if all_briers else None
    out = _opted_out(con)
    ranked = []
    for token, history in by_token.items():
        s = _stats(history)
        if token in out or s["n_resolved"] < MIN_RESOLVED:
            continue
        s["shrunk_brier"] = round(shrunk(s["mean_brier"], s["n_resolved"], group_mean), 4)
        ranked.append((token, s))
    ranked.sort(key=lambda ts: ts[1]["shrunk_brier"])
    return ranked, group_mean, by_token


def leaderboard(con, viewer_token=None):
    """Peer-visible leaderboard. Contains no author tokens, invite codes or device secrets."""
    ranked, group_mean, by_token = _ranking(con)
    entries = []
    for rank, (token, s) in enumerate(ranked, start=1):
        entries.append({
            "rank": rank,
            "display_name": _display_name(con, token),
            "n_resolved": s["n_resolved"],
            "shrunk_brier": s["shrunk_brier"],
            "mean_brier": s["mean_brier"],
            "acaps_brier_same_questions": s["acaps_brier_same_questions"],
            "super_estimator": s["super_estimator"],
            "is_you": token == viewer_token,
        })
    return {
        "min_resolved": MIN_RESOLVED,
        "shrink_k": SHRINK_K,
        "acaps_mapping": APP_MAPPING,
        "group_mean_brier": round(group_mean, 4) if group_mean is not None else None,
        "entries": entries,
        "n_not_yet_ranked": sum(1 for t, hs in by_token.items() if len(hs) < MIN_RESOLVED),
    }


def track_record(con, author_token):
    """GET /me/track-record payload for one author (only ever served to that author)."""
    ranked, _, by_token = _ranking(con)
    history = by_token.get(author_token, [])
    s = _stats(history)
    rank = next((i for i, (t, _) in enumerate(ranked, start=1) if t == author_token), None)
    return {
        "author_token": author_token,
        **s,
        "acaps_baseline_brier": s["acaps_brier_same_questions"],  # name used in api/mocks/track_record.json
        "min_resolved": MIN_RESOLVED,
        "forecasts_until_counted": max(0, MIN_RESOLVED - s["n_resolved"]),
        "rank": rank,
        "n_ranked": len(ranked),
        "rank_percentile": round(1 - (rank - 1) / len(ranked), 3) if rank else None,
        "acaps_mapping": APP_MAPPING,
        "history": history,
        "pending": pending_answers(con, author_token),
    }
