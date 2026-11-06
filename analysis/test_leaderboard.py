"""Run: python3 -m unittest discover analysis"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backtest import run
from leaderboard import MIN_RESOLVED, SHRINK_K, improvement_lower90, leaderboard, shrunk, track_record
from scoring import ACAPS_PROB, calibrated_acaps, label_counts, resolved_outcomes, wilson

SCHEMA = """
CREATE TABLE risks (risk_id TEXT PRIMARY KEY, probability TEXT, status TEXT);
CREATE TABLE questions (question_id TEXT PRIMARY KEY, risk_id TEXT, text TEXT, closes_at TEXT, outcome INTEGER);
CREATE TABLE contributions (author_token TEXT, question_id TEXT, prob REAL, version INTEGER);
CREATE TABLE experts (expert_id TEXT PRIMARY KEY, pseudonym TEXT);
INSERT INTO experts VALUES ('EXP-1', 'Kestrel'), ('EXP-2', 'Linden'), ('EXP-3', 'Heron');
"""


_open = []


def tearDownModule():
    for con in _open:
        con.close()


def make_db(questions, answers):
    """questions: [(qid, acaps_label, outcome)]; answers: [(token, qid, prob[, version])]."""
    con = sqlite3.connect(":memory:")
    _open.append(con)
    con.executescript(SCHEMA)
    for qid, label, outcome in questions:
        con.execute("INSERT INTO risks (risk_id, probability) VALUES (?, ?)", (f"R-{qid}", label))
        con.execute("INSERT INTO questions VALUES (?, ?, ?, '2026-05-01', ?)", (qid, f"R-{qid}", f"Q {qid}", outcome))
    for a in answers:
        token, qid, prob, version = (*a, 1) if len(a) == 3 else a
        con.execute("INSERT INTO contributions VALUES (?, ?, ?, ?)", (token, qid, prob, version))
    return con


class BadgeTest(unittest.TestCase):
    def test_needs_minimum_resolved_forecasts(self):
        qs = [(f"Q{i}", "Medium", 1) for i in range(MIN_RESOLVED)]
        answers = [("psd_EXP-1", q, 0.9) for q, _, _ in qs]           # 5 good forecasts
        answers += [("psd_EXP-2", q, 0.9) for q, _, _ in qs[:-1]]     # same quality, only 4
        con = make_db(qs, answers)

        self.assertTrue(track_record(con, "psd_EXP-1")["super_estimator"])
        rec = track_record(con, "psd_EXP-2")
        self.assertFalse(rec["super_estimator"])
        self.assertEqual(rec["forecasts_until_counted"], 1)
        self.assertIsNone(rec["rank"])
        self.assertEqual([e["display_name"] for e in leaderboard(con)["entries"]], ["Kestrel"])
        self.assertEqual(leaderboard(con)["n_not_yet_ranked"], 1)

    def test_paired_against_acaps_on_same_questions(self):
        # 5 easy questions ACAPS nails (Very High, happened) and 5 hard ones it misses (Very High, didn't).
        easy = [(f"E{i}", "Very High", 1) for i in range(5)]
        hard = [(f"H{i}", "Very High", 0) for i in range(5)]
        # Kestrel only answers easy questions, slightly worse than ACAPS on each: mean 0.01,
        # far better than ACAPS's overall mean (~0.45) but worse than ACAPS on *those* questions.
        con = make_db(easy + hard, [("psd_EXP-1", q, 0.9) for q, _, _ in easy])
        rec = track_record(con, "psd_EXP-1")
        self.assertAlmostEqual(rec["mean_brier"], 0.01)
        self.assertAlmostEqual(rec["acaps_brier_same_questions"], 0.0025)
        self.assertFalse(rec["super_estimator"])
        self.assertEqual(rec["n_beat_acaps"], 0)

    def test_uses_final_version(self):
        qs = [(f"Q{i}", "Medium", 1) for i in range(5)]
        answers = [("psd_EXP-1", q, 0.1, 1) for q, _, _ in qs] + [("psd_EXP-1", q, 0.9, 2) for q, _, _ in qs]
        rec = track_record(make_db(qs, answers), "psd_EXP-1")
        self.assertEqual({h["your_prob"] for h in rec["history"]}, {0.9})
        self.assertTrue(all(h["beat_acaps"] for h in rec["history"]))


class PendingTest(unittest.TestCase):
    def test_unresolved_final_answers_soonest_first(self):
        con = make_db([("Q1", "Medium", 1)], [("psd_EXP-1", "Q1", 0.7)])
        con.executescript("""
            INSERT INTO risks (risk_id, probability) VALUES ('R-P', 'High');
            INSERT INTO questions VALUES ('P-late', 'R-P', 'Late question', '2027-05-06', NULL),
                                         ('P-soon', 'R-P', 'Soon question', '2027-01-31', NULL);
            INSERT INTO contributions VALUES ('psd_EXP-1', 'P-late', 0.3, 1), ('psd_EXP-1', 'P-soon', 0.4, 1),
                                             ('psd_EXP-1', 'P-soon', 0.55, 2), ('psd_EXP-2', 'P-soon', 0.9, 1);
        """)
        rec = track_record(con, "psd_EXP-1")
        self.assertEqual([p["question_id"] for p in rec["pending"]], ["P-soon", "P-late"])
        self.assertEqual(rec["pending"][0]["your_prob"], 0.55)  # final version
        self.assertEqual(set(rec["pending"][0]), {"question_id", "title", "title_fr", "text", "text_fr",
                                                  "your_prob", "closes_at", "submitted_at"})
        self.assertEqual([h["question_id"] for h in rec["history"]], ["Q1"])  # resolved stays in history


class ShrinkageTest(unittest.TestCase):
    def test_formula(self):
        self.assertAlmostEqual(shrunk(0.10, 5, 0.20), (5 * 0.10 + SHRINK_K * 0.20) / (5 + SHRINK_K))
        self.assertAlmostEqual(shrunk(0.10, 10_000, 0.20), 0.10, places=3)

    def test_few_lucky_forecasts_do_not_top_the_board(self):
        # Kestrel: 5 perfect calls. Linden: 40 calls, slightly worse each. Heron drags the group mean up.
        qs = [(f"Q{i}", "Medium", 1) for i in range(40)]
        answers = [("psd_EXP-1", f"Q{i}", 1.0) for i in range(5)]
        answers += [("psd_EXP-2", f"Q{i}", 0.85) for i in range(40)]
        answers += [("psd_EXP-3", f"Q{i}", 0.2) for i in range(40)]
        board = leaderboard(make_db(qs, answers))
        self.assertEqual([e["display_name"] for e in board["entries"]], ["Linden", "Kestrel", "Heron"])
        kestrel = board["entries"][1]
        self.assertEqual(kestrel["mean_brier"], 0)  # best raw score, ranked second after shrinkage


class AnonymityTest(unittest.TestCase):
    def test_anonymous_name_and_opt_out(self):
        qs = [(f"Q{i}", "Medium", 1) for i in range(5)]
        answers = [("anon_abc123", q, 0.9) for q, _, _ in qs] + [("psd_EXP-1", q, 0.8) for q, _, _ in qs]
        con = make_db(qs, answers)
        names = [e["display_name"] for e in leaderboard(con)["entries"]]
        self.assertEqual(names, ["Anonymous expert", "Kestrel"])

        con.execute("CREATE TABLE leaderboard_opt_out (author_token TEXT PRIMARY KEY)")
        con.execute("INSERT INTO leaderboard_opt_out VALUES ('anon_abc123')")
        self.assertEqual([e["display_name"] for e in leaderboard(con)["entries"]], ["Kestrel"])
        self.assertEqual(track_record(con, "anon_abc123")["n_resolved"], 5)  # still sees own record

    def test_leaderboard_has_no_tokens_and_marks_viewer(self):
        qs = [(f"Q{i}", "Medium", 1) for i in range(5)]
        con = make_db(qs, [("psd_EXP-1", q, 0.9) for q, _, _ in qs])
        board = leaderboard(con, viewer_token="psd_EXP-1")
        self.assertTrue(board["entries"][0]["is_you"])
        self.assertNotIn("psd_", json.dumps(board))


class HedgingTest(unittest.TestCase):
    """The badge must not be winnable by hedging ACAPS towards 50% with no extra knowledge."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Path(cls.tmp.name) / "bt.db"
        cls.summary, cls.board, _ = run(db)
        cls.con = sqlite3.connect(db)
        cls.con.execute("INSERT INTO experts (expert_id, pseudonym, country_panel, lang, default_tier)"
                        " VALUES ('EXP-HEDGE', 'Hedger', 'TCD', 'en', 'pseudonymous')")
        for qid, label in cls.con.execute(
            "SELECT q.question_id, r.probability FROM questions q JOIN risks r USING (risk_id)"
            " WHERE q.question_id LIKE '%-MAT'").fetchall():
            hedged = 0.5 + 0.8 * (ACAPS_PROB[label] - 0.5)  # pull every rating 20% towards 50%
            cls.con.execute("INSERT INTO contributions (round_id, question_id, author_token, tier, prob, version,"
                            " created_at) VALUES ('BT', ?, 'psd_EXP-HEDGE', 'pseudonymous', ?, 1, '')", (qid, hedged))

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.tmp.cleanup()

    def test_hedger_beats_raw_acaps_on_average_but_gets_no_badge(self):
        rec = track_record(self.con, "psd_EXP-HEDGE")
        self.assertEqual(rec["n_resolved"], 99)
        # The trap is real: on average, hedging beats both raw and calibrated ACAPS...
        self.assertLess(rec["mean_brier"], rec["acaps_baseline_brier"])
        self.assertLess(rec["mean_brier"], rec["calibrated_acaps_baseline_brier"])
        # ...but not clearly, so no badge.
        self.assertLessEqual(rec["gain_vs_calibrated_acaps_lower90"], 0)
        self.assertFalse(rec["super_estimator"])

    def test_sharp_experts_still_earn_it(self):
        sharp = {r["display_name"] for r in self.summary["experts"] if r["archetype"] == "sharp"}
        badges = {e["display_name"] for e in self.board["entries"] if e["super_estimator"]}
        self.assertEqual(badges, sharp)


class NoLeakageTest(unittest.TestCase):
    def test_own_outcome_never_sets_own_baseline(self):
        qs = [(f"Q{i}", "Low", i % 2) for i in range(6)]
        con = make_db(qs, [("psd_EXP-1", q, 0.4) for q, _, _ in qs])
        con.execute("UPDATE risks SET status = CASE (SELECT outcome FROM questions q WHERE q.risk_id = risks.risk_id)"
                    " WHEN 1 THEN 'Materialised' ELSE 'Not materialised' END")
        base = {h["question_id"]: h["calibrated_acaps_prob"] for h in track_record(con, "psd_EXP-1")["history"]}

        # Flip Q0's own risk outcome: Q0's baseline must not move, every other question's must.
        con.execute("UPDATE risks SET status = 'Materialised' WHERE risk_id = 'R-Q0'")
        con.execute("UPDATE questions SET outcome = 1 WHERE question_id = 'Q0'")
        after = {h["question_id"]: h["calibrated_acaps_prob"] for h in track_record(con, "psd_EXP-1")["history"]}
        self.assertEqual(after["Q0"], base["Q0"])
        self.assertTrue(all(after[q] != base[q] for q in base if q != "Q0"))

    def test_calibrated_acaps_leave_one_out_and_shrinkage(self):
        counts = {"Low": [10, 4]}
        # (k − own + prior·midpoint) / (n − 1 + prior)
        self.assertAlmostEqual(calibrated_acaps("Low", counts, exclude_outcome=1), (3 + 5 * 0.22) / (9 + 5))
        self.assertAlmostEqual(calibrated_acaps("Low", {"Low": [0, 0]}), 0.22)  # no data → midpoint

    def test_wilson(self):
        lo, hi = wilson(25, 30)
        self.assertTrue(lo < 25 / 30 < hi)
        self.assertEqual(wilson(0, 0), (0.0, 1.0))

    def test_improvement_lower_bound(self):
        self.assertGreater(improvement_lower90([0.05] * 10)[1], 0)
        self.assertLess(improvement_lower90([0.3, -0.3] * 5)[1], 0)


class NoSecretsInOutputsTest(unittest.TestCase):
    def test_backtest_outputs(self):
        vault = json.loads((Path(__file__).parent / "synthetic" / "vault.json").read_text())
        secrets = {v["device_secret"] for v in vault if v["device_secret"]}
        invites = {v["invite_token"] for v in vault}
        with tempfile.TemporaryDirectory() as tmp:
            summary, board, records = run(Path(tmp) / "bt.db")
        for name, obj in [("summary", summary), ("leaderboard", board), ("track records", records)]:
            text = json.dumps(obj)
            self.assertNotIn("inv_", text, name)
            for s in secrets | invites:
                self.assertNotIn(s, text, name)
        # Summary and leaderboard are shared with the team/peers: no tokens, no pseudonym for anonymous.
        for obj in (summary, board):
            self.assertNotIn("anon_", json.dumps(obj))
            self.assertNotIn("Sparrow", json.dumps(obj))


if __name__ == "__main__":
    unittest.main()
