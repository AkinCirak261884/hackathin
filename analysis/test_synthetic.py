"""Run: python3 -m unittest discover analysis"""

import random
import statistics
import tempfile
import unittest
from pathlib import Path

from ingest import build_db
from synthetic import ARCHETYPES, forecast, save, simulate


class SyntheticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.con = build_db(Path(cls.tmp.name) / "test.db")
        cls.out = simulate(cls.con)
        save(cls.con, cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.tmp.cleanup()

    def test_panel(self):
        experts = self.out["experts"]
        self.assertEqual(len(experts), 8)
        self.assertEqual({e["default_tier"] for e in experts}, {"known", "pseudonymous", "anonymous"})

    def test_deterministic(self):
        con = build_db(Path(self.tmp.name) / "again.db")
        self.assertEqual(simulate(con)["responses"], self.out["responses"])
        con.close()

    def test_every_expert_answers_round_1(self):
        v1 = [r for r in self.out["responses"] if r["version"] == 1]
        self.assertEqual(len(v1), 8)
        for r in v1:
            self.assertEqual(len(r["answers"]), 4)
            for a in r["answers"]:
                if "prob" in a:
                    self.assertTrue(0.05 <= a["prob"] <= 0.95)

    def test_revisions_follow_a_round_1_answer(self):
        v1 = {r["invite_token"] for r in self.out["responses"] if r["version"] == 1}
        v2 = {r["invite_token"] for r in self.out["responses"] if r["version"] == 2}
        self.assertTrue(v2)
        self.assertLessEqual(v2, v1)

    def test_biases_point_the_right_way(self):
        rng = random.Random(0)
        mean = lambda arch: statistics.mean(forecast(arch, 0.7, 0.4, rng) for _ in range(300))
        self.assertGreater(mean("alarmist"), mean("well_calibrated"))
        self.assertLess(mean("complacent"), mean("well_calibrated"))
        self.assertGreater(mean("anchored"), mean("sharp"))  # anchored stays near ACAPS's 0.7
        self.assertLessEqual({e["archetype"] for e in self.out["experts"]}, set(ARCHETYPES))

    def test_no_identities_in_main_db(self):
        names = {v["name"] for v in self.out["vault"]} | {v["email"] for v in self.out["vault"]}
        for table in ("experts", "contributions"):
            for row in self.con.execute(f"SELECT * FROM {table}"):
                self.assertFalse(names & {str(c) for c in row}, table)

    def test_anonymous_token_is_unlinkable(self):
        anon = next(v for v in self.out["vault"] if v["device_secret"])
        self.assertTrue(anon["author_token"].startswith("anon_"))
        self.assertNotIn(anon["expert_id"].lower().replace("-", "_"), anon["author_token"])
        tokens = {t for (t,) in self.con.execute("SELECT DISTINCT author_token FROM contributions")}
        self.assertIn(anon["author_token"], tokens)
        self.assertNotIn(anon["device_secret"], tokens)


if __name__ == "__main__":
    unittest.main()
