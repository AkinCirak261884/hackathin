"""Seed a demo database with resolved history, so the profile, badge and leaderboard aren't empty.

A fresh Lane B database only holds the open R1043 round, so every track record is empty and the
leaderboard has no entries. This adds, into any DB with the BOARD.md tables (e.g. Lane B's
api/var/groundtruth.db right after its own seed):

- every Risk Radar risk (INSERT OR IGNORE, existing rows untouched);
- the backtest: one closed round RND-{risk}-BT and question Q-{risk}-MAT per resolved, rated risk,
  with the real outcome and the synthetic panel's answers (same tokens Lane B's API derives:
  psd_{expert_id} / anon_ + sha256("groundtruth-anon-v1:" + secret)[:32], from analysis/synthetic/vault.json).

Idempotent: does nothing if backtest rounds already exist. Synthetic experts only.

    python3 analysis/demo_history.py --db path/to/groundtruth.db
"""

import argparse
import json
import sqlite3
from pathlib import Path

from backtest import add_backtest
from ingest import load_rows

VAULT = Path(__file__).resolve().parent / "synthetic" / "vault.json"


def seed_history(con, vault_path=VAULT):
    """Add all risks and the synthetic backtest history to `con`. Returns the number of questions added."""
    if con.execute("SELECT 1 FROM rounds WHERE round_id LIKE 'RND-%-BT' LIMIT 1").fetchone():
        return 0
    for row in load_rows():
        impact = row["Impact"].strip()
        con.execute(
            "INSERT OR IGNORE INTO risks (risk_id, title, country, probability, impact, level, status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (row["Risk ID"].strip(), row["Risk Title"].strip(), row["Country"].strip(),
             row["Probability"].strip() or None, int(impact) if impact.isdigit() else None,
             row["Risk Level"].strip() or None, row["Status"].strip() or None),
        )
    vault = json.loads(Path(vault_path).read_text())
    _, risks = add_backtest(con, vault)
    con.commit()
    return len(risks)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    n = seed_history(con)
    print(f"Added {n} resolved backtest questions to {args.db}" if n else "History already present, nothing added")
    con.close()


if __name__ == "__main__":
    main()
