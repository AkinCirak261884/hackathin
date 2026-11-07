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
- "Super estimator" = at least MIN_RESOLVED resolved forecasts AND *clearly* better than BOTH raw
  and calibrated ACAPS on exactly the same questions: the paired 90% interval of
  (baseline Brier − your Brier) lies above 0 for each. A plain "lower mean" is not enough, because
  hedging towards 50% beats ACAPS by ~0.002 per question with no knowledge at all. Calibrated ACAPS = the historical
  materialisation rate of the question's ACAPS label, leaving the question's own risk out, shrunk
  towards the band midpoint (scoring.calibrated_acaps). Raw ACAPS is kept as secondary info,
  because raw ratings are overconfident at the extremes and can be beaten by hedging alone.
- Anonymous-tier tokens show as "Anonymous expert". Tokens in the optional `leaderboard_opt_out`
  table (author_token TEXT PRIMARY KEY) are left out of the leaderboard entirely.
"""

import math
import statistics

from scoring import ACAPS_PROB, APP_MAPPING, CALIBRATION_PRIOR, brier, calibrated_acaps, label_counts, resolved_outcomes

MIN_RESOLVED = 5
SHRINK_K = 5  # pseudo-forecasts at the group mean

# One-sided 95% t quantiles (= lower bound of a two-sided 90% interval), by degrees of freedom.
# Lookup takes the largest df <= actual df, so it errs on the strict side.
T95 = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833,
       10: 1.812, 12: 1.782, 15: 1.753, 20: 1.725, 25: 1.708, 30: 1.697, 60: 1.671, 120: 1.658}


def _t95(df):
    return T95[max(k for k in T95 if k <= df)] if df >= 1 else float("inf")


def gain_interval(diffs):
    """Paired improvement over a baseline: diffs = baseline Brier − your Brier, per question.
    Returns (mean, lower, upper, sd) of the two-sided 90% t interval; bounds None below 2 questions."""
    n = len(diffs)
    if n < 2:
        return (diffs[0] if diffs else None, None, None, None)
    mean, sd = statistics.mean(diffs), statistics.stdev(diffs)
    half = _t95(n - 1) * sd / math.sqrt(n)
    return (mean, mean - half, mean + half, sd)


def improvement_lower90(diffs):
    """(mean gain, lower bound of its 90% interval). Lower bound > 0 = clearly better."""
    mean, lo, _, _ = gain_interval(diffs)
    return (mean, lo)


def more_forecasts_needed(mean, sd, n):
    """Rough number of extra resolved forecasts until the 90% lower bound clears 0, if the current
    mean gain and spread hold: smallest N with mean − 1.645·sd/√N > 0, and N ≥ MIN_RESOLVED.
    None when the gain is ≤ 0 (no number of forecasts would earn the badge at this rate)."""
    if mean is None or mean <= 0:
        return None
    needed = MIN_RESOLVED if not sd else max(MIN_RESOLVED, math.floor((1.645 * sd / mean) ** 2) + 1)
    return max(0, needed - n)


def resolved_answers(con):
    """Every author's final answer on a resolved question, with ACAPS's forecast for it."""
    rows = con.execute("""
        SELECT c.author_token, c.question_id, q.text, q.closes_at, c.prob, q.outcome, r.probability, r.risk_id
        FROM contributions c
        JOIN questions q ON q.question_id = c.question_id
        JOIN risks r ON r.risk_id = q.risk_id
        WHERE c.prob IS NOT NULL AND q.outcome IS NOT NULL
          AND c.version = (SELECT MAX(version) FROM contributions c2
                           WHERE c2.author_token = c.author_token AND c2.question_id = c.question_id)
        ORDER BY q.closes_at, c.question_id
    """).fetchall()
    resolved = resolved_outcomes(con)
    counts = label_counts(resolved)
    by_token = {}
    for token, qid, text, closes_at, prob, outcome, label, risk_id in rows:
        acaps_p = ACAPS_PROB.get(label)
        own = resolved.get(risk_id)
        cal_p = calibrated_acaps(label, counts, exclude_outcome=own[1] if own else None)
        b = brier(prob, outcome)
        acaps_b = brier(acaps_p, outcome) if acaps_p is not None else None
        cal_b = brier(cal_p, outcome) if cal_p is not None else None
        by_token.setdefault(token, []).append({
            "question_id": qid,
            "risk_id": risk_id,
            "text": text,
            "closes_at": closes_at,
            "outcome": outcome,
            "outcome_label": "happened" if outcome else "didn't happen",
            "your_prob": prob,
            "brier": round(b, 4),
            "acaps_prob": acaps_p,
            "acaps_brier": round(acaps_b, 4) if acaps_b is not None else None,
            "beat_acaps": (b < acaps_b) if acaps_b is not None else None,
            "calibrated_acaps_prob": round(cal_p, 4) if cal_p is not None else None,
            "calibrated_acaps_brier": round(cal_b, 4) if cal_b is not None else None,
            "beat_calibrated_acaps": (b < cal_b) if cal_b is not None else None,
            "verdict": verdict(prob, outcome),
        })
    return by_token


def verdict(prob, outcome):
    """Same rule as Lane C's web/src/stats.js: right side of 50% = correct; exactly 50% = no call."""
    if prob == 0.5:
        return "nocall"
    return "correct" if (prob > 0.5) == bool(outcome) else "wrong"


def record(history):
    """{correct, resolved, no_call}: the "7 of 8 correct" line; resolved excludes no-calls."""
    v = [h["verdict"] for h in history]
    return {"correct": v.count("correct"), "resolved": len(v) - v.count("nocall"), "no_call": v.count("nocall")}


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


def _mean(xs):
    xs = list(xs)
    return statistics.mean(xs) if xs else None


def _r(x):
    return round(x, 4) if x is not None else None


def _stats(history):
    n = len(history)
    raw = [h for h in history if h["acaps_brier"] is not None]
    cal = [h for h in history if h["calibrated_acaps_brier"] is not None]
    cal_same = _mean(h["calibrated_acaps_brier"] for h in cal)
    raw_same = _mean(h["acaps_brier"] for h in raw)
    gain, gain_lo = improvement_lower90([h["calibrated_acaps_brier"] - h["brier"] for h in cal])
    raw_gain, raw_lo = improvement_lower90([h["acaps_brier"] - h["brier"] for h in raw])

    # Badge progress is measured against whichever baseline is stronger on these questions.
    stronger = "calibrated_acaps" if cal_same is not None and (raw_same is None or cal_same <= raw_same) else "raw_acaps"
    pool, key = (cal, "calibrated_acaps_brier") if stronger == "calibrated_acaps" else (raw, "acaps_brier")
    p_mean, p_lo, p_hi, p_sd = gain_interval([h[key] - h["brier"] for h in pool])
    super_estimator = (n >= MIN_RESOLVED and gain_lo is not None and gain_lo > 0
                       and raw_lo is not None and raw_lo > 0)
    return {
        "n_resolved": n,
        "mean_brier": _r(_mean(h["brier"] for h in history)),
        "calibrated_acaps_brier_same_questions": _r(cal_same),
        "n_beat_calibrated_acaps": sum(bool(h["beat_calibrated_acaps"]) for h in cal),
        "gain_vs_calibrated_acaps": _r(gain),           # mean per-question Brier improvement
        "gain_vs_calibrated_acaps_lower90": _r(gain_lo),  # badge needs this > 0
        "acaps_brier_same_questions": _r(raw_same),  # raw ACAPS
        "n_beat_acaps": sum(bool(h["beat_acaps"]) for h in raw),
        "gain_vs_acaps": _r(raw_gain),
        "gain_vs_acaps_lower90": _r(raw_lo),  # badge also needs this > 0
        "super_estimator": super_estimator,
        "badge_progress": {
            "baseline": stronger,  # "raw_acaps" or "calibrated_acaps", whichever is stronger here
            "gain": _r(p_mean),
            "gain_ci90": [_r(p_lo), _r(p_hi)] if p_lo is not None else None,
            "more_forecasts_needed": 0 if super_estimator else more_forecasts_needed(p_mean, p_sd, len(pool)),
        },
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
            "calibrated_acaps_brier_same_questions": s["calibrated_acaps_brier_same_questions"],
            "gain_vs_calibrated_acaps_lower90": s["gain_vs_calibrated_acaps_lower90"],
            "gain_vs_acaps_lower90": s["gain_vs_acaps_lower90"],
            "acaps_brier_same_questions": s["acaps_brier_same_questions"],
            "super_estimator": s["super_estimator"],
            "is_you": token == viewer_token,
        })
    return {
        "min_resolved": MIN_RESOLVED,
        "shrink_k": SHRINK_K,
        "acaps_mapping": APP_MAPPING,
        "badge_baseline": "raw_and_calibrated_acaps",
        "calibration_prior": CALIBRATION_PRIOR,
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
        "calibrated_acaps_baseline_brier": s["calibrated_acaps_brier_same_questions"],  # badge baseline
        "acaps_baseline_brier": s["acaps_brier_same_questions"],  # raw ACAPS, secondary (api/mocks name)
        "badge_baseline": "raw_and_calibrated_acaps",
        "min_resolved": MIN_RESOLVED,
        "forecasts_until_counted": max(0, MIN_RESOLVED - s["n_resolved"]),
        "rank": rank,
        "n_ranked": len(ranked),
        "rank_percentile": round(1 - (rank - 1) / len(ranked), 3) if rank else None,
        "acaps_mapping": APP_MAPPING,
        "record": record(history),
        "history": history,
        "pending": pending_answers(con, author_token),
    }
