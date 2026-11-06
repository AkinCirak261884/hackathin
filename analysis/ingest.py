"""Load the Risk Radar export into SQLite: `risks` and `triggers` tables (schema in BOARD.md).

Usage:
    python3 analysis/ingest.py                 # writes analysis/out/groundtruth.db
    python3 analysis/ingest.py --db path.db
"""

import argparse
import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "risk-radar-export.csv"
DEFAULT_DB = Path(__file__).resolve().parent / "out" / "groundtruth.db"

# Labels in each trigger block, in the order they appear in the export.
LABELS = [
    "Trigger ID",
    "Title",
    "Description",
    "Sources",
    "Completion rate",
    "Completion rate history",
    "Quantitative objective to meet 100%",
    "Trend",
    "Trend history",
    "Date entered",
    "Last update",
]
LABEL_RE = re.compile(r"^(" + "|".join(re.escape(l) for l in LABELS) + r"):[ \t]*", re.M)

SCHEMA = """
CREATE TABLE risks (
    risk_id     TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    country     TEXT,
    probability TEXT,
    impact      INTEGER,
    level       TEXT,
    status      TEXT
);
CREATE TABLE triggers (
    trigger_id      TEXT PRIMARY KEY,
    risk_id         TEXT NOT NULL REFERENCES risks(risk_id),
    title           TEXT,
    description     TEXT,
    completion_rate INTEGER,
    objective       TEXT
);
"""


def _clean(text):
    # Some descriptions start with a stray ":" line in the export.
    return text.strip().lstrip(":").strip() or None


def parse_triggers(text):
    """Parse a Triggers field into a list of dicts (trigger_id, risk_id, title, description,
    completion_rate, objective). Returns [] for empty fields."""
    triggers = []
    for block in re.split(r"(?=^Trigger ID:)", text or "", flags=re.M):
        if not block.startswith("Trigger ID:"):
            continue
        parts = LABEL_RE.split(block)
        # split() with one group gives ['', label, value, label, value, ...]
        fields = {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}

        risk_id, _, trigger_id = fields["Trigger ID"].strip().partition(" - ")
        rate = re.match(r"(\d+)\s*%", fields.get("Completion rate", "").strip())
        objective = _clean(fields.get("Quantitative objective to meet 100%", ""))
        # Most triggers have no objective; "No" also means none was set.
        if objective and objective != "No":
            objective = re.sub(r"^Yes\.\s*", "", objective)
        else:
            objective = None

        triggers.append({
            "trigger_id": trigger_id.strip(),
            "risk_id": risk_id.strip(),
            "title": _clean(fields.get("Title", "")),
            "description": _clean(fields.get("Description", "")),
            "completion_rate": int(rate.group(1)) if rate else None,
            "objective": objective,
        })
    return triggers


def load_rows(csv_path=CSV_PATH):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_db(db_path=DEFAULT_DB, csv_path=CSV_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    for row in load_rows(csv_path):
        impact = row["Impact"].strip()
        con.execute(
            "INSERT INTO risks VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                row["Risk ID"].strip(),
                row["Risk Title"].strip(),
                row["Country"].strip() or None,
                row["Probability"].strip() or None,
                int(impact) if impact.isdigit() else None,
                row["Risk Level"].strip() or None,
                row["Status"].strip() or None,
            ),
        )
        con.executemany(
            "INSERT INTO triggers VALUES (:trigger_id, :risk_id, :title, :description,"
            " :completion_rate, :objective)",
            parse_triggers(row["Triggers"]),
        )
    con.commit()
    return con


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    con = build_db(args.db)
    n_risks = con.execute("SELECT COUNT(*) FROM risks").fetchone()[0]
    n_triggers = con.execute("SELECT COUNT(*) FROM triggers").fetchone()[0]
    print(f"Wrote {args.db}: {n_risks} risks, {n_triggers} triggers")

    print("\nChad risks:")
    for risk_id, title, status in con.execute(
        "SELECT risk_id, title, status FROM risks WHERE country LIKE '%Chad%'"
    ):
        print(f"  {risk_id} [{status or '?'}] {title[:80]}")

    print("\nR1043 triggers:")
    for trigger_id, title, rate in con.execute(
        "SELECT trigger_id, title, completion_rate FROM triggers WHERE risk_id = 'R1043'"
    ):
        print(f"  {trigger_id} ({rate}%) {title}")


if __name__ == "__main__":
    main()
