"""Group aggregate for the reveal view and disagreement metrics for the moderator.

Pure functions on a DB with the BOARD.md tables, for Lane B to call next to its own
api/rounds.py::aggregate() (which keeps owning the "submit first" gate and auth):

    aggregate(con, question_id)      -> dict, or None when fewer than MIN_N experts answered
    disagreement(con, question_id)   -> dict, or None when fewer than MIN_N experts answered
    backtest_aggregates(con)         -> median vs weighted vs weighted+extremized on resolved questions

Weighted aggregate: average of each expert's latest forecast in log-odds, weighted by track record,
then multiplied by EXTREMIZE (default 1.5) in log-odds. An expert's weight is 0.25 / their mean Brier
(a coin-flipper gets 1), clipped to [0.2, 5], and shrunk towards the group-average weight with SHRINK_K
pseudo-questions, so experts with few resolved forecasts, and new experts, count about average.
Weights only ever use questions that resolved *before* the one being aggregated, never its own outcome.

Outputs contain no author tokens or names: values are rounded and shuffled.
"""

import math
import random
import statistics

from leaderboard import SHRINK_K, resolved_answers
from scoring import ACAPS_PROB, brier

MIN_N = 3  # same rule as Lane B's api/rounds.py
EXTREMIZE = 1.5
WEIGHT_CLIP = (0.2, 5.0)
P_CLIP = (0.01, 0.99)
CLOSE_TO_ACAPS = 0.10  # |aggregate − ACAPS| below this counts as "close"
SPLIT_GAP = 0.20       # bimodal flag: largest gap between neighbouring answers


def _logit(p):
    p = min(max(p, P_CLIP[0]), P_CLIP[1])
    return math.log(p / (1 - p))


def _sigmoid(x):
    return 1 / (1 + math.exp(-x))


def latest_probs(con, question_id):
    """{author_token: prob} — each author's latest answer to the question."""
    return dict(con.execute("""
        SELECT c.author_token, c.prob FROM contributions c
        WHERE c.question_id = ? AND c.prob IS NOT NULL
          AND c.version = (SELECT MAX(version) FROM contributions c2
                           WHERE c2.author_token = c.author_token AND c2.question_id = c.question_id)
    """, (question_id,)).fetchall())


def prior_questions(con, question_id):
    """Resolved questions that closed strictly before this one (never the question itself)."""
    row = con.execute("SELECT closes_at FROM questions WHERE question_id = ?", (question_id,)).fetchone()
    if not row:
        return set()
    return {qid for (qid,) in con.execute(
        "SELECT question_id FROM questions WHERE outcome IS NOT NULL AND closes_at < ? AND question_id != ?",
        (row[0], question_id))}


def expert_weights(by_token, history_qids, tokens):
    """Track-record weights for `tokens`, using only answers to questions in `history_qids`."""
    raw = {}
    for token in tokens:
        briers = [h["brier"] for h in by_token.get(token, []) if h["question_id"] in history_qids]
        if briers:
            w = 0.25 / max(statistics.mean(briers), 1e-3)
            raw[token] = (min(max(w, WEIGHT_CLIP[0]), WEIGHT_CLIP[1]), len(briers))
    group = statistics.mean(w for w, _ in raw.values()) if raw else 1.0
    weights = {}
    for token in tokens:
        w, n = raw.get(token, (group, 0))
        weights[token] = (n * w + SHRINK_K * group) / (n + SHRINK_K)  # new expert -> group average
    return weights


def combine(probs, weights, extremize=EXTREMIZE):
    """Weighted mean in log-odds, times `extremize`, back to a probability."""
    total = sum(weights[t] for t in probs)
    mean_logit = sum(weights[t] * _logit(p) for t, p in probs.items()) / total
    return _sigmoid(extremize * mean_logit)


def aggregate(con, question_id, extremize=EXTREMIZE, history_qids=None, by_token=None, shuffle=True):
    """Group view for one question, or None when fewer than MIN_N experts answered."""
    probs = latest_probs(con, question_id)
    if len(probs) < MIN_N:
        return None
    by_token = by_token if by_token is not None else resolved_answers(con)
    history_qids = (history_qids if history_qids is not None else prior_questions(con, question_id)) - {question_id}
    weights = expert_weights(by_token, history_qids, probs)
    values = [round(p, 2) for p in probs.values()]
    if shuffle:
        random.SystemRandom().shuffle(values)
    else:
        values.sort()
    return {
        "question_id": question_id,
        "n": len(probs),
        "min_n": MIN_N,
        "median": round(statistics.median(probs.values()), 3),
        "weighted": round(combine(probs, weights, 1.0), 3),
        "weighted_extremized": round(combine(probs, weights, extremize), 3),
        "extremize_factor": extremize,
        "aggregate": round(combine(probs, weights, extremize), 3),  # the one to show
        "n_weighted_by_track_record": sum(1 for t in probs if any(
            h["question_id"] in history_qids for h in by_token.get(t, []))),
        "values": values,  # unnamed, shuffled
    }


# ---------- moderator: disagreement ----------

def _has_column(con, table, column):
    return any(row[1] == column for row in con.execute(f"PRAGMA table_info({table})"))


def _split(values):
    """Bimodal flag: the largest gap between neighbouring sorted answers is ≥ SPLIT_GAP and both
    sides hold at least 2 answers and a quarter of the group."""
    v = sorted(values)
    if len(v) < 4:
        return False, None
    gap, i = max((v[k + 1] - v[k], k) for k in range(len(v) - 1))
    left, right = i + 1, len(v) - i - 1
    need = max(2, math.ceil(len(v) / 4))
    split = gap >= SPLIT_GAP and left >= need and right >= need
    return split, (round((v[i] + v[i + 1]) / 2, 3) if split else None)


def rating_shares(con, question_id):
    """Share of experts saying too_low / agree / too_high on probability and impact, if the
    contributions carry Lane C's rating fields; otherwise agree / disagree from `agree`."""
    latest = """c.version = (SELECT MAX(version) FROM contributions c2
                WHERE c2.author_token = c.author_token AND c2.question_id = c.question_id)"""
    out = {}
    for dim in ("probability", "impact"):
        col = f"rating_{dim}"
        if not _has_column(con, "contributions", col):
            continue
        rows = [r for (r,) in con.execute(
            f"SELECT c.{col} FROM contributions c WHERE c.question_id = ? AND c.{col} IS NOT NULL AND {latest}",
            (question_id,))]
        if len(rows) >= MIN_N:
            out[dim] = {k: round(rows.count(k) / len(rows), 2) for k in ("too_low", "agree", "too_high")}
    if not out:
        rows = [a for (a,) in con.execute(
            f"SELECT c.agree FROM contributions c WHERE c.question_id = ? AND c.agree IS NOT NULL AND {latest}",
            (question_id,))]
        if len(rows) >= MIN_N:
            out["overall"] = {"agree": round(sum(rows) / len(rows), 2), "disagree": round(1 - sum(rows) / len(rows), 2)}
    return out or None


def disagreement(con, question_id, extremize=EXTREMIZE):
    """Moderator view for one question, or None when fewer than MIN_N experts answered.
    For a forecast question: spread, split flag and distance from ACAPS. For the rating question
    (agree / too_low / too_high): the shares. No tokens or names."""
    probs = latest_probs(con, question_id)
    shares = rating_shares(con, question_id)
    if len(probs) < MIN_N and shares is None:
        return None
    out = {"question_id": question_id, "min_n": MIN_N, "rating_shares": shares}
    if len(probs) >= MIN_N:
        values = list(probs.values())
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        split, at = _split(values)
        agg = aggregate(con, question_id, extremize)["aggregate"]
        label = con.execute("SELECT r.probability FROM questions q JOIN risks r USING (risk_id)"
                            " WHERE q.question_id = ?", (question_id,)).fetchone()
        acaps = ACAPS_PROB.get(label[0]) if label else None
        diff = round(agg - acaps, 3) if acaps is not None else None
        out.update({
            "n": len(values),
            "iqr": [round(q1, 3), round(q3, 3)],
            "spread": round(q3 - q1, 3),
            "split": split,
            "split_at": at,
            "aggregate": agg,
            "acaps_prob": acaps,  # ACAPS's rating of the question's risk (for trigger questions, a proxy)
            "aggregate_minus_acaps": diff,
            "vs_acaps": None if diff is None else (
                "close" if abs(diff) < CLOSE_TO_ACAPS else "higher" if diff > 0 else "lower"),
        })
    return out


# ---------- backtest ----------

def backtest_aggregates(con, question_ids_in_time_order, extremize=EXTREMIZE):
    """Score median, weighted and weighted+extremized group forecasts on resolved questions.
    Weights for each question use only the questions *before* it in the given order."""
    by_token = resolved_answers(con)
    outcomes = dict(con.execute("SELECT question_id, outcome FROM questions WHERE outcome IS NOT NULL"))
    scores = {"median": [], "weighted": [], "weighted_extremized": [], "acaps": []}
    labels = dict(con.execute("SELECT q.question_id, r.probability FROM questions q JOIN risks r USING (risk_id)"))
    seen = set()
    for qid in question_ids_in_time_order:
        agg = aggregate(con, qid, extremize, history_qids=set(seen), by_token=by_token, shuffle=False)
        seen.add(qid)
        if agg is None or qid not in outcomes:
            continue
        y = outcomes[qid]
        for key in ("median", "weighted", "weighted_extremized"):
            scores[key].append(brier(agg[key], y))
        scores["acaps"].append(brier(ACAPS_PROB[labels[qid]], y))
    return {
        "n_questions": len(scores["median"]),
        "extremize_factor": extremize,
        "brier": {k: round(statistics.mean(v), 4) for k, v in scores.items() if v},
        "order": "Risk ID (proxy for time); weights use only earlier questions",
    }
