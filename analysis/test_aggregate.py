"""Run: python3 -m unittest discover analysis"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from aggregate import (MIN_N, aggregate, backtest_aggregates, combine, disagreement, expert_weights,
                       prior_questions)
from backtest import run

SCHEMA = """
CREATE TABLE risks (risk_id TEXT PRIMARY KEY, probability TEXT, status TEXT);
CREATE TABLE questions (question_id TEXT PRIMARY KEY, risk_id TEXT, text TEXT, closes_at TEXT, outcome INTEGER);
CREATE TABLE contributions (author_token TEXT, question_id TEXT, prob REAL, agree INTEGER, version INTEGER,
                            rating_probability TEXT, rating_impact TEXT);
CREATE TABLE experts (expert_id TEXT PRIMARY KEY, pseudonym TEXT);
INSERT INTO experts VALUES ('EXP-1', 'Kestrel'), ('EXP-2', 'Linden'), ('EXP-3', 'Heron'), ('EXP-4', 'Wren');
INSERT INTO risks VALUES ('R1', 'High', NULL);
"""


def db(answers, questions=(("Q", "2027-01-31", None),)):
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA)
    for qid, closes, outcome in questions:
        con.execute("INSERT INTO questions VALUES (?, 'R1', ?, ?, ?)", (qid, qid, closes, outcome))
    for a in answers:
        con.execute("INSERT INTO contributions (author_token, question_id, prob, agree, version, rating_probability,"
                    " rating_impact) VALUES (?, ?, ?, ?, ?, ?, ?)", (*a, *(None,) * (7 - len(a))))
    return con


class MinimumNTest(unittest.TestCase):
    def test_fewer_than_three_returns_nothing(self):
        con = db([("psd_EXP-1", "Q", 0.6, None, 1), ("psd_EXP-2", "Q", 0.7, None, 1),
                  ("psd_EXP-2", "Q", 0.8, None, 2)])  # 2 authors, one revised
        self.assertIsNone(aggregate(con, "Q"))
        self.assertIsNone(disagreement(con, "Q"))
        con.execute("INSERT INTO contributions (author_token, question_id, prob, version) VALUES ('anon_x', 'Q', 0.5, 1)")
        self.assertEqual(aggregate(con, "Q")["n"], MIN_N)
        con.close()


class PrivacyTest(unittest.TestCase):
    def test_no_tokens_or_names(self):
        con = db([("psd_EXP-1", "Q", 0.6, 1, 1), ("psd_EXP-2", "Q", 0.7, 0, 1), ("anon_secret_hash", "Q", 0.2, 1, 1)])
        for out in (aggregate(con, "Q"), disagreement(con, "Q")):
            text = json.dumps(out)
            for leak in ("psd_", "anon_", "EXP-", "Kestrel", "Linden"):
                self.assertNotIn(leak, text)
        self.assertEqual(sorted(aggregate(con, "Q")["values"]), [0.2, 0.6, 0.7])
        con.close()


class OutOfSampleTest(unittest.TestCase):
    def test_prior_questions_exclude_itself_and_later(self):
        con = db([], [("A", "2027-01-01", 1), ("B", "2027-02-01", 0), ("C", "2027-03-01", 1), ("D", "2027-02-01", None)])
        self.assertEqual(prior_questions(con, "B"), {"A"})
        self.assertEqual(prior_questions(con, "C"), {"A", "B"})
        con.close()

    def test_own_outcome_never_moves_own_aggregate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bt.db"
            run(path)
            con = sqlite3.connect(path)
            order = [q for (q,) in con.execute(
                "SELECT question_id FROM questions WHERE question_id LIKE '%-MAT' ORDER BY risk_id")]
            target = order[50]
            before = aggregate(con, target, history_qids=set(order[:50]), shuffle=False)
            con.execute("UPDATE questions SET outcome = 1 - outcome WHERE question_id = ?", (target,))
            after = aggregate(con, target, history_qids=set(order[:50]), shuffle=False)
            self.assertEqual(before, after)
            # ...and passing the question itself as history is ignored.
            self.assertEqual(aggregate(con, target, history_qids=set(order[:51]), shuffle=False), before)
            bt = backtest_aggregates(con, order)
            self.assertLess(bt["brier"]["weighted"], bt["brier"]["median"])
            con.close()


class WeightsTest(unittest.TestCase):
    def test_new_expert_gets_group_average_and_few_forecasts_shrink(self):
        by_token = {
            "good": [{"question_id": f"q{i}", "brier": 0.05} for i in range(40)],
            "bad": [{"question_id": f"q{i}", "brier": 0.40} for i in range(40)],
            "lucky": [{"question_id": "q0", "brier": 0.0}],
        }
        hist = {f"q{i}" for i in range(40)}
        w = expert_weights(by_token, hist, ["good", "bad", "lucky", "new"])
        self.assertGreater(w["good"], w["bad"])
        self.assertLess(w["lucky"], w["good"])  # one perfect call doesn't earn a top weight
        group = (5.0 + 0.625 + 5.0) / 3          # raw weights: good 5 (clipped), bad 0.625, lucky 5 (clipped)
        self.assertAlmostEqual(w["new"], group)

    def test_extremizing_pushes_away_from_half(self):
        probs, weights = {"a": 0.7, "b": 0.7, "c": 0.7}, {"a": 1, "b": 1, "c": 1}
        self.assertAlmostEqual(combine(probs, weights, 1.0), 0.7)
        self.assertGreater(combine(probs, weights, 1.5), 0.7)


class DisagreementTest(unittest.TestCase):
    def test_split_flag_and_acaps_distance(self):
        split = db([(f"t{i}", "Q", p, None, 1) for i, p in enumerate([0.1, 0.15, 0.2, 0.8, 0.85, 0.9])])
        d = disagreement(split, "Q")
        self.assertTrue(d["split"])
        self.assertEqual(d["acaps_prob"], 0.78)
        together = db([(f"t{i}", "Q", p, None, 1) for i, p in enumerate([0.7, 0.75, 0.8, 0.8, 0.85])])
        d2 = disagreement(together, "Q")
        self.assertFalse(d2["split"])
        self.assertEqual(d2["vs_acaps"], "close")
        self.assertLess(d2["spread"], d["spread"])
        split.close(); together.close()

    def test_rating_shares(self):
        con = db([("t1", "R", None, None, 1, "too_low", "agree"), ("t2", "R", None, None, 1, "too_low", "agree"),
                  ("t3", "R", None, None, 1, "agree", "too_high"), ("t4", "R", None, None, 1, "too_high", "agree")],
                 [("R", "2027-01-31", None)])
        shares = disagreement(con, "R")["rating_shares"]
        self.assertEqual(shares["probability"], {"too_low": 0.5, "agree": 0.25, "too_high": 0.25})
        self.assertEqual(shares["impact"], {"too_low": 0.0, "agree": 0.75, "too_high": 0.25})
        con.close()


if __name__ == "__main__":
    unittest.main()
