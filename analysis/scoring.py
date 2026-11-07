"""Brier scoring for resolved questions.

    brier = (forecast - outcome)^2      0 = perfect, 0.25 = always saying 50%, 1 = confidently wrong

Each author's *final* answer counts: version 2 if they revised after the reveal, else version 1.
"""

import math
import statistics

# ACAPS probability label -> number. ACAPS's 2019 risk methodology uses Medow & Lucey's unequal
# ranges: Very low <10%, Low 10-33%, Moderate 34-66%, High 67-90%, Very high >90%.
# The export calls "Moderate" "Medium".
ACAPS_PROB_MIDPOINT = {"Very Low": 0.05, "Low": 0.22, "Medium": 0.50, "High": 0.78, "Very High": 0.95}
# Earlier, evenly spaced mapping from BOARD.md, kept for comparison.
ACAPS_PROB_EDGE = {"Very Low": 0.10, "Low": 0.30, "Medium": 0.50, "High": 0.70, "Very High": 0.90}
MAPPINGS = {"midpoint": ACAPS_PROB_MIDPOINT, "edge": ACAPS_PROB_EDGE}
APP_MAPPING = "midpoint"  # what the app, leaderboard and badge use
ACAPS_PROB = MAPPINGS[APP_MAPPING]


def brier(prob, outcome):
    return (prob - outcome) ** 2


def final_answers(con):
    """(author_token, question_id, prob, outcome) for every resolved question, latest version only."""
    return con.execute("""
        SELECT c.author_token, c.question_id, c.prob, q.outcome
        FROM contributions c
        JOIN questions q ON q.question_id = c.question_id
        WHERE c.prob IS NOT NULL AND q.outcome IS NOT NULL
          AND c.version = (SELECT MAX(version) FROM contributions c2
                           WHERE c2.author_token = c.author_token AND c2.question_id = c.question_id)
    """).fetchall()


def score_db(con):
    """Recompute the `scores` table. Returns the number of scored answers."""
    con.executescript("""
        DROP TABLE IF EXISTS scores;
        CREATE TABLE scores (author_token TEXT NOT NULL, question_id TEXT NOT NULL,
                             brier REAL NOT NULL, PRIMARY KEY (author_token, question_id));
    """)
    rows = [(token, qid, brier(p, y)) for token, qid, p, y in final_answers(con)]
    con.executemany("INSERT INTO scores VALUES (?, ?, ?)", rows)
    con.commit()
    return len(rows)


def mean_brier(pairs):
    """Mean Brier of (prob, outcome) pairs."""
    return statistics.mean(brier(p, y) for p, y in pairs)


def calibration(pairs, n_bins=5, min_n=3):
    """Bin (prob, outcome) pairs into equal-width bins. Returns [{mean_prob, observed, n}],
    skipping bins with fewer than min_n forecasts."""
    bins = [[] for _ in range(n_bins)]
    for p, y in pairs:
        bins[min(int(p * n_bins), n_bins - 1)].append((p, y))
    return [
        {"mean_prob": statistics.mean(p for p, _ in b), "observed": statistics.mean(y for _, y in b), "n": len(b)}
        for b in bins if len(b) >= min_n
    ]


# ---------- calibrated ACAPS baseline ----------
#
# Raw ACAPS ratings are overconfident at the extremes, so "beat ACAPS" can be won by hedging
# towards 50% with no knowledge at all. The badge therefore compares against *calibrated* ACAPS:
# each label's historical materialisation rate, never using the question's own risk (leave-one-out),
# shrunk towards the band midpoint so labels with few risks don't swing on one outcome.

CALIBRATION_PRIOR = 5  # pseudo-risks at the band midpoint
WILSON_Z90 = 1.645


def wilson(k, n, z=WILSON_Z90):
    """Wilson score interval for k successes out of n (default 90%)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def resolved_outcomes(con):
    """{risk_id: (probability label, outcome)} for every resolved, rated risk in `risks`."""
    return {
        risk_id: (label, 1 if status == "Materialised" else 0)
        for risk_id, label, status in con.execute(
            "SELECT risk_id, probability, status FROM risks"
            " WHERE status IN ('Materialised', 'Not materialised') AND probability IS NOT NULL")
    }


def label_counts(resolved):
    """{label: [n, materialised]} from resolved_outcomes()."""
    counts = {label: [0, 0] for label in ACAPS_PROB_MIDPOINT}
    for label, outcome in resolved.values():
        counts[label][0] += 1
        counts[label][1] += outcome
    return counts


def calibrated_acaps(label, counts, exclude_outcome=None, prior=CALIBRATION_PRIOR):
    """Shrunk historical rate for an ACAPS label. Pass exclude_outcome (0/1) when the question's own
    risk is in `counts`, so its outcome never sets its own baseline (leave-one-out)."""
    if label not in counts:
        return None
    n, k = counts[label]
    if exclude_outcome is not None:
        n, k = n - 1, k - exclude_outcome
    return (k + prior * ACAPS_PROB_MIDPOINT[label]) / (n + prior)


def label_table(con):
    """Per-label sample sizes, Wilson 90% interval and calibrated rate (all resolved risks)."""
    counts = label_counts(resolved_outcomes(con))
    rows = []
    for label, (n, k) in counts.items():
        lo, hi = wilson(k, n)
        rows.append({
            "label": label, "n": n, "materialised": k,
            "rate": round(k / n, 3) if n else None,
            "wilson90": [round(lo, 3), round(hi, 3)],
            "midpoint": ACAPS_PROB_MIDPOINT[label],
            "calibrated": round(calibrated_acaps(label, counts), 3),
        })
    return rows
