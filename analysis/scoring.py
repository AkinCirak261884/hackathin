"""Brier scoring for resolved questions.

    brier = (forecast - outcome)^2      0 = perfect, 0.25 = always saying 50%, 1 = confidently wrong

Each author's *final* answer counts: version 2 if they revised after the reveal, else version 1.
"""

import statistics


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
