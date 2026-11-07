"""Run: python3 -m unittest discover analysis"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from ingest import build_db
from questions import add_months, generate_questions, save_questions

OPENED = date(2026, 11, 6)


class QuestionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.con = build_db(Path(cls.tmp.name) / "test.db")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.tmp.cleanup()

    def test_r1043_yields_agree_plus_three_triggers(self):
        qs = generate_questions(self.con, OPENED, ["R1043"])

        self.assertEqual(
            [q["question_id"] for q in qs],
            ["Q-R1043-AGREE", "Q-R1043-T0618", "Q-R1043-T0619", "Q-R1043-T0620"],
        )
        self.assertTrue(all(q["closes_at"] == "2027-05-06" for q in qs))
        self.assertEqual(
            qs[0]["text"],
            "Do you agree with ACAPS's rating for this risk (Probability: High, Impact: 4, Risk level: High)?",
        )
        self.assertTrue(qs[1]["text"].startswith("Will cross-border attacks become sustained and recurrent"))
        self.assertTrue(qs[1]["text"].endswith(", by 6 May 2027?"))
        self.assertEqual(qs[1]["trigger_id"], "T0618")

    def test_fallback_without_objective(self):
        # R1066/T0669 has an objective that isn't in the "100% completion" form.
        q = next(q for q in generate_questions(self.con, OPENED, ["R1066"]) if q["trigger_id"] == "T0669")
        self.assertTrue(q["text"].startswith("Will this trigger fully materialise in Chad"))
        self.assertTrue(q["resolves_yes_if"])

    def test_default_is_active_risks(self):
        qs = generate_questions(self.con, OPENED)
        self.assertEqual(sum(q["kind"] == "agree" for q in qs), 28)

    def test_save(self):
        save_questions(self.con, generate_questions(self.con, OPENED, ["R1043"]))
        n = self.con.execute("SELECT COUNT(*) FROM questions WHERE risk_id = 'R1043'").fetchone()[0]
        self.assertEqual(n, 4)

    def test_add_months_clamps_day(self):
        self.assertEqual(add_months(date(2026, 8, 31), 6), date(2027, 2, 28))
        self.assertEqual(add_months(OPENED, 6), date(2027, 5, 6))


if __name__ == "__main__":
    unittest.main()
