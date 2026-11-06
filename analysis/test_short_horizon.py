"""Run: python3 -m unittest discover analysis"""

import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from ingest import load_rows, parse_triggers

FILE = Path(__file__).parent / "questions" / "short_horizon.json"
# Required by contracts/schemas/common.schema.json#/$defs/question
REQUIRED = {"question_id", "risk_id", "kind", "title", "title_fr", "text", "text_fr", "closes_at"}
PILOT_START = datetime(2026, 12, 1)


class ShortHorizonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text())
        cls.qs = cls.data["questions"]
        cls.risks = {r["Risk ID"]: r for r in load_rows()}

    def test_contract_fields(self):
        for q in self.qs:
            self.assertLessEqual(REQUIRED, set(q), q["question_id"])
            self.assertEqual(q["kind"], "forecast")
            for f in ("title", "title_fr", "text", "text_fr", "resolution_criterion"):
                self.assertTrue(q[f].strip(), (q["question_id"], f))
            self.assertTrue(q["resolution_source"]["type"])
        self.assertEqual(len({q["question_id"] for q in self.qs}), len(self.qs))

    def test_close_dates_within_one_to_three_months_of_pilot_start(self):
        for q in self.qs:
            closes = datetime.fromisoformat(q["closes_at"].replace("Z", ""))
            self.assertGreaterEqual(closes, PILOT_START + timedelta(days=28), q["question_id"])
            self.assertLessEqual(closes, datetime(2027, 3, 1, 23, 59, 59), q["question_id"])

    def test_three_to_five_per_active_chad_risk_from_its_own_triggers(self):
        active_chad = {rid for rid, r in self.risks.items() if "TCD" in r["ISO"] and r["Status"] == "Active"}
        by_risk = {}
        for q in self.qs:
            by_risk.setdefault(q["risk_id"], []).append(q)
            triggers = {t["trigger_id"] for t in parse_triggers(self.risks[q["risk_id"]]["Triggers"])}
            self.assertIn(q["trigger_id"], triggers, q["question_id"])
        self.assertEqual(set(by_risk), active_chad)
        for rid, qs in by_risk.items():
            self.assertTrue(3 <= len(qs) <= 5, rid)


if __name__ == "__main__":
    unittest.main()
