"""Run: python3 -m unittest discover analysis"""

import json
import sqlite3
import unittest

from demo_history import seed_history
from leaderboard import leaderboard, track_record
from synthetic import EXPERTS

# The parts of Lane B's api/db.py schema that seed_history touches (NOT NULL columns included).
B_SCHEMA = """
CREATE TABLE risks (risk_id TEXT PRIMARY KEY, title TEXT NOT NULL, country TEXT NOT NULL,
                    probability TEXT, impact REAL, level TEXT, status TEXT);
CREATE TABLE rounds (round_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL, stage TEXT NOT NULL, opened_at TEXT NOT NULL);
CREATE TABLE questions (question_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL, trigger_id TEXT, text TEXT NOT NULL,
                        closes_at TEXT NOT NULL, outcome INTEGER);
CREATE TABLE experts (expert_id TEXT PRIMARY KEY, pseudonym TEXT NOT NULL, country_panel TEXT NOT NULL,
                      lang TEXT NOT NULL, default_tier TEXT NOT NULL);
CREATE TABLE contributions (id INTEGER PRIMARY KEY AUTOINCREMENT, round_id TEXT NOT NULL, question_id TEXT NOT NULL,
                            author_token TEXT NOT NULL, tier TEXT NOT NULL, prob REAL, agree INTEGER,
                            missing_text TEXT, reasoning_text TEXT, reasoning_basis TEXT,
                            version INTEGER NOT NULL, created_at TEXT NOT NULL,
                            UNIQUE (round_id, question_id, author_token, version));
INSERT INTO risks VALUES ('R1043', 'kept as is', 'Chad', 'High', 4, 'High', 'Active');
INSERT INTO rounds VALUES ('RND-R1043-1', 'R1043', 'blind', '2026-11-06');
"""


class DemoHistoryTest(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.executescript(B_SCHEMA)
        self.con.executemany("INSERT INTO experts VALUES (?, ?, 'TCD', ?, ?)",
                             [(e[0], e[1], e[5], e[4]) for e in EXPERTS])

    def tearDown(self):
        self.con.close()

    def test_seeds_once_and_fills_profile_and_leaderboard(self):
        self.assertEqual(seed_history(self.con), 99)
        self.assertEqual(seed_history(self.con), 0)  # idempotent
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM risks").fetchone()[0], 139)
        self.assertEqual(self.con.execute("SELECT title FROM risks WHERE risk_id='R1043'").fetchone()[0], "kept as is")
        self.assertEqual(self.con.execute("SELECT stage FROM rounds WHERE round_id='RND-R1043-1'").fetchone()[0], "blind")

        board = leaderboard(self.con)
        self.assertEqual(len(board["entries"]), 8)
        self.assertIn("Anonymous expert", [e["display_name"] for e in board["entries"]])
        self.assertNotIn("Sparrow", json.dumps(board))
        self.assertGreater(track_record(self.con, "psd_EXP-TCD-04")["n_resolved"], 5)


if __name__ == "__main__":
    unittest.main()
