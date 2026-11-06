"""Run: python3 -m unittest discover analysis"""

import tempfile
import unittest
from pathlib import Path

from ingest import build_db, load_rows, parse_triggers


class ParseTriggersTest(unittest.TestCase):
    def test_r1043_has_three_triggers(self):
        row = next(r for r in load_rows() if r["Risk ID"] == "R1043")
        triggers = parse_triggers(row["Triggers"])

        self.assertEqual([t["trigger_id"] for t in triggers], ["T0618", "T0619", "T0620"])
        self.assertEqual([t["completion_rate"] for t in triggers], [40, 10, 20])
        first = triggers[0]
        self.assertEqual(first["risk_id"], "R1043")
        self.assertEqual(first["title"], "Expansion of cross-border attacks and insecurity")
        self.assertTrue(first["description"].startswith("Additional drone strikes"))
        self.assertTrue(first["objective"].startswith("100% completion would be reached"))

    def test_empty_field(self):
        self.assertEqual(parse_triggers(""), [])

    def test_missing_completion_rate(self):
        text = "Trigger ID: R1 - T1\nTitle: X\nDescription: d\nCompletion rate: \nCompletion rate history: \n"
        self.assertIsNone(parse_triggers(text)[0]["completion_rate"])

    def test_objective_no_means_none(self):
        text = "Trigger ID: R1 - T1\nTitle: X\nQuantitative objective to meet 100%: \nNo\nTrend: \n"
        self.assertIsNone(parse_triggers(text)[0]["objective"])


class BuildDbTest(unittest.TestCase):
    def test_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            con = build_db(Path(tmp) / "test.db")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM risks").fetchone()[0], 139)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM triggers").fetchone()[0], 266)
            row = con.execute(
                "SELECT country, probability, impact, level, status FROM risks WHERE risk_id='R1043'"
            ).fetchone()
            self.assertEqual(row, ("Chad", "High", 4, "High", "Active"))
            con.close()


if __name__ == "__main__":
    unittest.main()
