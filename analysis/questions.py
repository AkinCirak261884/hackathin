"""Turn risks and their triggers into resolvable questions (`questions` table, schema in BOARD.md).

Each risk gets one "do you agree with ACAPS's rating?" item (Q-{risk}-AGREE) and one yes/no
forecast per trigger (Q-{risk}-{T####}) that closes six months after the round opens.

Usage:
    python3 analysis/questions.py                       # all Active risks, opened today
    python3 analysis/questions.py --risk R1043 --opened 2026-11-06 --json analysis/out/questions_R1043.json
"""

import argparse
import calendar
import json
import re
import sqlite3
from datetime import date
from pathlib import Path

from ingest import DEFAULT_DB, build_db

HORIZON_MONTHS = 6

QUESTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    risk_id     TEXT NOT NULL REFERENCES risks(risk_id),
    trigger_id  TEXT REFERENCES triggers(trigger_id),  -- NULL for the agree item
    text        TEXT NOT NULL,
    closes_at   TEXT NOT NULL,
    outcome     INTEGER CHECK (outcome IN (0, 1))      -- NULL until resolved
);
"""

# Only the recent risks phrase objectives this way; older ones are free text.
OBJECTIVE_RE = re.compile(r"^100% completion would be reached if (.+?)\.?$", re.S)


def add_months(d, months):
    month = d.month - 1 + months
    year, month = d.year + month // 12, month % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _human(d):
    return f"{d.day} {d.strftime('%B %Y')}"


def agree_question(risk, closes):
    return {
        "question_id": f"Q-{risk['risk_id']}-AGREE",
        "risk_id": risk["risk_id"],
        "trigger_id": None,
        "kind": "agree",
        "text": (
            "Do you agree with ACAPS's rating for this risk (Probability: "
            f"{risk['probability'] or '?'}, Impact: {risk['impact'] or '?'}, "
            f"Risk level: {risk['level'] or '?'})?"
        ),
        "resolves_yes_if": None,
        "closes_at": closes.isoformat(),
    }


def trigger_question(risk, trigger, closes):
    objective = trigger["objective"] or ""
    match = OBJECTIVE_RE.match(objective.strip())
    if match:
        clause = " ".join(match.group(1).split())
        text = f"Will {clause}, by {_human(closes)}?"
        resolves = objective
    else:
        title = (trigger["title"] or "this trigger").rstrip(".")
        text = f'Will this trigger fully materialise in {risk["country"]} by {_human(closes)}: "{title}"?'
        resolves = objective or trigger["description"]

    return {
        "question_id": f"Q-{risk['risk_id']}-{trigger['trigger_id']}",
        "risk_id": risk["risk_id"],
        "trigger_id": trigger["trigger_id"],
        "kind": "forecast",
        "text": text,
        "resolves_yes_if": resolves,
        "closes_at": closes.isoformat(),
    }


def generate_questions(con, opened_at, risk_ids=None):
    """Return question dicts for the given risks (default: all Active risks)."""
    con.row_factory = sqlite3.Row
    closes = add_months(opened_at, HORIZON_MONTHS)
    if risk_ids:
        marks = ",".join("?" * len(risk_ids))
        risks = con.execute(f"SELECT * FROM risks WHERE risk_id IN ({marks})", risk_ids).fetchall()
    else:
        risks = con.execute("SELECT * FROM risks WHERE status = 'Active'").fetchall()

    questions = []
    for risk in risks:
        questions.append(agree_question(risk, closes))
        for trigger in con.execute(
            "SELECT * FROM triggers WHERE risk_id = ? ORDER BY trigger_id", (risk["risk_id"],)
        ):
            questions.append(trigger_question(risk, trigger, closes))
    return questions


def save_questions(con, questions):
    con.executescript(QUESTIONS_SCHEMA)
    con.executemany(
        "INSERT OR REPLACE INTO questions (question_id, risk_id, trigger_id, text, closes_at)"
        " VALUES (:question_id, :risk_id, :trigger_id, :text, :closes_at)",
        questions,
    )
    con.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--risk", action="append", help="risk ID (repeatable); default all Active")
    parser.add_argument("--opened", type=date.fromisoformat, default=date.today())
    parser.add_argument("--json", help="also write the questions to this JSON file")
    args = parser.parse_args()

    if not Path(args.db).exists():
        build_db(args.db).close()
    con = sqlite3.connect(args.db)
    questions = generate_questions(con, args.opened, args.risk)
    save_questions(con, questions)
    print(f"Wrote {len(questions)} questions to {args.db}")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {args.json}")

    for q in questions[:8]:
        print(f"  {q['question_id']}: {q['text'][:110]}")


if __name__ == "__main__":
    main()
