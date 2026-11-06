"""SQLite schema for Lane B (from BOARD.md "Data model").

Trust design: identities are kept in a *separate database file* (vault.db),
so the contributions DB physically contains no names or emails. Only the
moderator layer ever opens the vault.
"""
import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent / "var"
# Lane A can build content tables first:  python analysis/ingest.py --db api/var/groundtruth.db
# (ingest recreates the file, so only run it before real responses exist).
MAIN_DB = Path(os.environ.get("GT_DB", DATA_DIR / "groundtruth.db"))
VAULT_DB = Path(os.environ.get("GT_VAULT_DB", DATA_DIR / "vault.db"))

MAIN_SCHEMA = """
CREATE TABLE IF NOT EXISTS risks (
    risk_id TEXT PRIMARY KEY, title TEXT NOT NULL, country TEXT NOT NULL,
    probability TEXT, impact REAL, level TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS triggers (
    trigger_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL REFERENCES risks(risk_id),
    title TEXT, description TEXT, completion_rate REAL, objective TEXT
);
CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL REFERENCES risks(risk_id),
    trigger_id TEXT REFERENCES triggers(trigger_id),   -- NULL for the "agree with rating" item
    text TEXT NOT NULL, closes_at TEXT NOT NULL,
    question_set TEXT NOT NULL DEFAULT 'core',          -- core (6-month) | short_horizon (pilot)
    title TEXT, title_fr TEXT, text_fr TEXT, opens_at TEXT, resolution_criterion TEXT,
    outcome INTEGER CHECK (outcome IN (0, 1))           -- NULL until resolved
);
CREATE TABLE IF NOT EXISTS rounds (
    round_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL REFERENCES risks(risk_id),
    stage TEXT NOT NULL CHECK (stage IN ('blind', 'reveal', 'closed')),
    opened_at TEXT NOT NULL,
    panel TEXT NOT NULL DEFAULT 'TCD', closed_at TEXT
);
CREATE TABLE IF NOT EXISTS round_questions (
    round_id TEXT NOT NULL REFERENCES rounds(round_id),
    question_id TEXT NOT NULL REFERENCES questions(question_id),
    PRIMARY KEY (round_id, question_id)
);
-- Pseudonymous profile only. No names, no emails, no IPs.
CREATE TABLE IF NOT EXISTS experts (
    expert_id TEXT PRIMARY KEY, pseudonym TEXT NOT NULL, country_panel TEXT NOT NULL,
    lang TEXT NOT NULL DEFAULT 'en',
    default_tier TEXT NOT NULL DEFAULT 'anonymous'
        CHECK (default_tier IN ('known', 'pseudonymous', 'anonymous'))
);
CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id TEXT NOT NULL REFERENCES rounds(round_id),
    question_id TEXT NOT NULL REFERENCES questions(question_id),
    author_token TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('known', 'pseudonymous', 'anonymous')),
    prob REAL CHECK (prob BETWEEN 0 AND 1),
    agree INTEGER CHECK (agree IN (0, 1)),
    missing_text TEXT,                      -- moderator-only, never published verbatim
    reasoning_text TEXT,                    -- moderator-only, like missing_text
    reasoning_basis TEXT,
    version INTEGER NOT NULL CHECK (version IN (1, 2)),
    created_at TEXT NOT NULL,
    UNIQUE (round_id, question_id, author_token, version)
);
CREATE TABLE IF NOT EXISTS scores (
    author_token TEXT NOT NULL, question_id TEXT NOT NULL REFERENCES questions(question_id),
    brier REAL NOT NULL, PRIMARY KEY (author_token, question_id)
);
CREATE TABLE IF NOT EXISTS observed_triggers (
    round_id TEXT NOT NULL REFERENCES rounds(round_id), author_token TEXT NOT NULL,
    trigger_id TEXT NOT NULL, version INTEGER NOT NULL CHECK (version IN (1, 2)),
    PRIMARY KEY (round_id, author_token, trigger_id, version)
);
CREATE TABLE IF NOT EXISTS leaderboard_opt_out (author_token TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS summaries (
    round_id TEXT PRIMARY KEY REFERENCES rounds(round_id),
    approved_text TEXT NOT NULL, published_at TEXT NOT NULL
);
"""

VAULT_SCHEMA = """
-- Synthetic identities only. Never joined into public queries.
CREATE TABLE IF NOT EXISTS identity_vault (
    expert_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL
);
-- Invite-only access: the anti-spam / anti-misinformation layer.
CREATE TABLE IF NOT EXISTS invites (
    invite_token TEXT PRIMARY KEY, expert_id TEXT NOT NULL,
    country_panel TEXT NOT NULL, created_at TEXT NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
-- "This invite already answered round R (version v)". Deliberately has NO author_token,
-- so it stops double submissions without linking an invite to an anonymous answer.
CREATE TABLE IF NOT EXISTS round_participation (
    round_id TEXT NOT NULL, invite_token TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version IN (1, 2)),
    PRIMARY KEY (round_id, invite_token, version)
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def main_db() -> sqlite3.Connection:
    return connect(MAIN_DB)


def vault_db() -> sqlite3.Connection:
    """Only trust.py and the moderator layer may call this."""
    return connect(VAULT_DB)


# Columns added after the first schema; ALTERed into existing DBs on startup.
MIGRATIONS = [
    ("contributions", "reasoning_text", "TEXT"), ("contributions", "reasoning_basis", "TEXT"),
    ("rounds", "panel", "TEXT NOT NULL DEFAULT 'TCD'"), ("rounds", "closed_at", "TEXT"),
    ("questions", "question_set", "TEXT NOT NULL DEFAULT 'core'"), ("questions", "title", "TEXT"),
    ("questions", "title_fr", "TEXT"), ("questions", "text_fr", "TEXT"), ("questions", "opens_at", "TEXT"),
    ("questions", "resolution_criterion", "TEXT"),
]


def init_db(main_path: Path | None = None, vault_path: Path | None = None) -> None:
    with connect(main_path or MAIN_DB) as c:
        c.executescript(MAIN_SCHEMA)
        for table, col, typ in MIGRATIONS:
            if col not in {r[1] for r in c.execute(f"PRAGMA table_info({table})")}:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
    with connect(vault_path or VAULT_DB) as c:
        c.executescript(VAULT_SCHEMA)


if __name__ == "__main__":
    init_db()
    print(f"Initialised {MAIN_DB} and {VAULT_DB}")
