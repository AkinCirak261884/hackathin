"""Run: python3 -m unittest discover analysis"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from backtest import calibration_svg, run
from scoring import brier, calibration, mean_brier, score_db


class BrierTest(unittest.TestCase):
    def test_values(self):
        self.assertEqual(brier(1.0, 1), 0)
        self.assertEqual(brier(0.5, 0), 0.25)
        self.assertAlmostEqual(brier(0.7, 0), 0.49)
        self.assertAlmostEqual(mean_brier([(0.7, 1), (0.7, 0)]), (0.09 + 0.49) / 2)

    def test_calibration_bins(self):
        pairs = [(0.1, 0)] * 4 + [(0.9, 1)] * 3 + [(0.9, 0)] + [(0.5, 1)] * 2
        bins = calibration(pairs)  # the 0.5 bin has n=2 < min_n and is skipped
        self.assertEqual([(round(b["mean_prob"], 2), b["observed"], b["n"]) for b in bins],
                         [(0.1, 0, 4), (0.9, 0.75, 4)])

    def test_score_db_uses_final_version(self):
        con = sqlite3.connect(":memory:")
        con.executescript("""
            CREATE TABLE questions (question_id TEXT, outcome INTEGER);
            CREATE TABLE contributions (author_token TEXT, question_id TEXT, prob REAL, version INTEGER);
            INSERT INTO questions VALUES ('Q1', 1), ('Q2', NULL);
            INSERT INTO contributions VALUES ('a', 'Q1', 0.2, 1), ('a', 'Q1', 0.8, 2),
                                             ('b', 'Q1', 0.5, 1), ('a', 'Q2', 0.9, 1);
        """)
        self.assertEqual(score_db(con), 2)  # Q2 unresolved, a's v1 superseded
        scores = dict(con.execute("SELECT author_token, brier FROM scores"))
        self.assertAlmostEqual(scores["a"], 0.04)
        self.assertAlmostEqual(scores["b"], 0.25)
        con.close()


class BacktestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.summary, _, _ = run(Path(cls.tmp.name) / "bt.db")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_acaps_baseline_on_real_outcomes(self):
        s = self.summary
        self.assertEqual(s["n_resolved"], 99)  # 104 resolved, 5 without a probability rating
        self.assertAlmostEqual(s["base_rate"], 0.606, places=3)
        self.assertLess(s["acaps"]["brier"], s["climatology_brier"])  # ACAPS beats always-base-rate
        self.assertEqual(s["acaps_mapping_used"], "midpoint")
        by_mapping = s["acaps_brier_by_mapping"]
        self.assertEqual(by_mapping["midpoint"]["brier"], s["acaps"]["brier"])
        self.assertAlmostEqual(by_mapping["edge"]["brier"], 0.2128, places=4)

    def test_archetypes_rank_sensibly(self):
        ranked = [r["archetype"] for r in self.summary["experts"]]
        self.assertEqual(ranked[0], "sharp")
        self.assertLess(ranked.index("well_calibrated"), ranked.index("anchored"))
        self.assertIn(ranked[-1], {"complacent", "hedger", "noisy", "alarmist"})

    def test_chart_renders(self):
        svg = calibration_svg(self.summary)
        self.assertTrue(svg.startswith("<svg") and svg.rstrip().endswith("</svg>"))
        self.assertIn("ACAPS rating", svg)
        self.assertIn("prefers-color-scheme: dark", svg)


if __name__ == "__main__":
    unittest.main()
