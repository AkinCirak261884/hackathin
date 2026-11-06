"""SQLite schema for Lane B (from BOARD.md "Data model").

Trust design: identities are kept in a *separate database file* (vault.db),
so the contributions DB physically contains no names or emails. Only the
moderator layer ever opens the vault.
"""
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent / "var"
MAIN_DB = DATA_DIR / "groundtruth.db"
VAULT_DB = DATA_DIR / "vault.db"

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
    outcome INTEGER CHECK (outcome IN (0, 1))           -- NULL until resolved
);
CREATE TABLE IF NOT EXISTS rounds (
    round_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL REFERENCES risks(risk_id),
    stage TEXT NOT NULL CHECK (stage IN ('blind', 'reveal', 'closed')),
    opened_at TEXT NOT NULL
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
    missing_text TEXT,
    version INTEGER NOT NULL CHECK (version IN (1, 2)),
    created_at TEXT NOT NULL,
    UNIQUE (round_id, question_id, author_token, version)
);
CREATE TABLE IF NOT EXISTS scores (
    author_token TEXT NOT NULL, question_id TEXT NOT NULL REFERENCES questions(question_id),
    brier REAL NOT NULL, PRIMARY KEY (author_token, question_id)
);
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
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(main_path: Path = MAIN_DB, vault_path: Path = VAULT_DB) -> None:
    with connect(main_path) as c:
        c.executescript(MAIN_SCHEMA)
    with connect(vault_path) as c:
        c.executescript(VAULT_SCHEMA)


if __name__ == "__main__":
    init_db()
    print(f"Initialised {MAIN_DB} and {VAULT_DB}")
