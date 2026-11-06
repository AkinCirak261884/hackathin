"""Seed a demo database with resolved history, so the profile, badge and leaderboard aren't empty.

A fresh Lane B database only holds the open R1043 round, so every track record is empty and the
leaderboard has no entries. This adds, into any DB with the BOARD.md tables (e.g. Lane B's
api/var/groundtruth.db right after its own seed):

- every Risk Radar risk (INSERT OR IGNORE, existing rows untouched);
- the backtest: one closed round RND-{risk}-BT and question Q-{risk}-MAT per resolved, rated risk,
  with the real outcome and the synthetic panel's answers (same tokens Lane B's API derives:
  psd_{expert_id} / anon_ + sha256("groundtruth-anon-v1:" + secret)[:32], from analysis/synthetic/vault.json).

Demo-only, with two guards:
- it refuses to run unless explicitly asked (`demo=True` / `--demo`);
- it refuses any database that already holds a non-synthetic expert: an `experts` row outside the
  synthetic panel, or a contribution whose author token isn't one of the panel's tokens (a real
  anonymous expert only ever exists as an `anon_` token).
Idempotent: does nothing if backtest rounds already exist. Lives in analysis/; Lane B decides
whether api/seed.py calls it.

    python3 analysis/demo_history.py --demo --db path/to/demo.db
"""

import argparse
import json
import sqlite3
from pathlib import Path

from backtest import add_backtest
from ingest import load_rows

VAULT = Path(__file__).resolve().parent / "synthetic" / "vault.json"


class NotADemoDatabase(Exception):
    pass


def non_synthetic(con, vault):
    """Experts or author tokens in `con` that don't belong to the synthetic panel."""
    ids = {v["expert_id"] for v in vault}
    tokens = {v["author_token"] for v in vault}
    found = [f"expert {e}" for (e,) in con.execute("SELECT expert_id FROM experts") if e not in ids]
    found += [f"author token {t[:12]}…" for (t,) in con.execute("SELECT DISTINCT author_token FROM contributions")
              if t not in tokens]
    return found


def seed_history(con, vault_path=VAULT, demo=False):
    """Add all risks and the synthetic backtest history to a *demo* DB. Returns the number of questions added.
    Raises NotADemoDatabase unless demo=True and every expert in the DB is synthetic."""
    if not demo:
        raise NotADemoDatabase("seed_history is demo-only: pass demo=True (CLI: --demo)")
    vault = json.loads(Path(vault_path).read_text())
    others = non_synthetic(con, vault)
    if others:
        raise NotADemoDatabase(f"refusing: database has non-synthetic experts ({', '.join(others[:3])})")
    if con.execute("SELECT 1 FROM rounds WHERE round_id LIKE 'RND-%-BT' LIMIT 1").fetchone():
        return 0
    try:
        n = _write(con, vault)
    except Exception:
        con.rollback()  # all or nothing
        raise
    con.commit()
    return n


def _write(con, vault):
    for row in load_rows():
        impact = row["Impact"].strip()
        con.execute(
            "INSERT OR IGNORE INTO risks (risk_id, title, country, probability, impact, level, status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (row["Risk ID"].strip(), row["Risk Title"].strip(), row["Country"].strip(),
             row["Probability"].strip() or None, int(impact) if impact.isdigit() else None,
             row["Risk Level"].strip() or None, row["Status"].strip() or None),
        )
    _, risks = add_backtest(con, vault)
    return len(risks)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--demo", action="store_true", help="required: confirms this is a demo database")
    args = parser.parse_args()
    if not args.demo:
        parser.error("demo-only: add --demo to confirm this is a demo database")
    if not Path(args.db).exists():
        parser.error(f"{args.db} does not exist")
    con = sqlite3.connect(args.db)
    try:
        n = seed_history(con, demo=True)
    except NotADemoDatabase as e:
        con.close()
        parser.error(str(e))
    print(f"Added {n} resolved backtest questions to {args.db}" if n else "History already present, nothing added")
    con.close()


if __name__ == "__main__":
    main()
