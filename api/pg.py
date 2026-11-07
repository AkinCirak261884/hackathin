"""Postgres (Supabase) backend with the sqlite3 surface the API and analysis/ code already use.

Switched on by GT_DATABASE_URL (see db.py); without it everything stays on SQLite.
Callers keep writing SQLite-flavoured SQL ("?" placeholders, INSERT OR IGNORE / OR REPLACE,
datetime('now'), sqlite_master, PRAGMA table_info). This module translates those few idioms, so
api/*.py and analysis/*.py run unchanged on both databases.

Trust design is kept: answers live in schema `gt`, identities and invites in schema `gt_vault`.
Neither schema is exposed through Supabase's public REST API, and row-level security is on with
no policies, so only this server (holding the connection string) can read them.
"""
import re
from decimal import Decimal

import psycopg

MAIN_SCHEMA_NAME = "gt"
VAULT_SCHEMA_NAME = "gt_vault"

# Primary keys of tables written with INSERT OR REPLACE (needed for ON CONFLICT ... DO UPDATE).
PRIMARY_KEYS = {"syntheses": ["round_id"], "experts": ["expert_id"], "identity_vault": ["expert_id"]}
# Column order for INSERT OR REPLACE statements that omit the column list.
TABLE_COLUMNS = {"syntheses": ["round_id", "input_hash", "result_json", "created_at"]}


class Row:
    """sqlite3.Row look-alike: row["col"], row[0], dict(row), tuple unpacking."""
    __slots__ = ("_keys", "_values", "_index")

    def __init__(self, keys, values):
        self._keys = keys
        self._values = tuple(float(v) if isinstance(v, Decimal) else v for v in values)
        self._index = {k: i for i, k in enumerate(keys)}

    def keys(self):
        return list(self._keys)

    def __getitem__(self, key):
        return self._values[key] if isinstance(key, (int, slice)) else self._values[self._index[key]]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __repr__(self):
        return f"Row({dict(zip(self._keys, self._values))})"


def _row_factory(cursor):
    keys = [d.name for d in (cursor.description or [])]
    return lambda values: Row(keys, values)


_INSERT_OR = re.compile(r"^\s*INSERT\s+OR\s+(IGNORE|REPLACE)\s+INTO\s+(\w+)\s*(\(([^)]*)\))?", re.I)
# sqlite_master (table list) → the current schema's tables, same column names
_SQLITE_MASTER = re.compile(r"\bsqlite_master\b", re.I)
_SQLITE_MASTER_PG = ("(SELECT table_name AS name, 'table' AS type FROM information_schema.tables"
                     " WHERE table_schema = current_schema()) AS sqlite_master")
_PRAGMA_TABLE_INFO = re.compile(r"^\s*PRAGMA\s+table_info\((\w+)\)\s*$", re.I)


def translate(sql: str) -> str:
    """SQLite idioms → Postgres. Kept deliberately small: only what this codebase uses."""
    m = _PRAGMA_TABLE_INFO.match(sql)
    if m:  # callers read row[1] == column name
        return ("SELECT ordinal_position - 1 AS cid, column_name AS name FROM information_schema.columns"
                f" WHERE table_schema = current_schema() AND table_name = '{m.group(1)}' ORDER BY ordinal_position")
    sql = _SQLITE_MASTER.sub(_SQLITE_MASTER_PG, sql)
    sql = re.sub(r"datetime\('now'\)", "to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD HH24:MI:SS')", sql, flags=re.I)
    m = _INSERT_OR.match(sql)
    if m:
        mode, table, cols = m.group(1).upper(), m.group(2), m.group(4)
        sql = _INSERT_OR.sub(lambda mm: f"INSERT INTO {table}" + (f" ({cols}) " if cols else " "), sql, count=1).rstrip().rstrip(";")
        if mode == "IGNORE":
            sql += " ON CONFLICT DO NOTHING"
        else:
            pk = PRIMARY_KEYS[table]
            names = [c.strip() for c in cols.split(",")] if cols else TABLE_COLUMNS[table]
            sets = ", ".join(f"{c} = EXCLUDED.{c}" for c in names if c not in pk)
            sql += f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {sets}"
    # placeholders: "?" → "%s", ":name" → "%(name)s" (escape literal % first, e.g. LIKE 'RND-%')
    sql = sql.replace("%", "%%").replace("?", "%s")
    return re.sub(r"(?<![:\w]):([A-Za-z_]\w*)", r"%(\1)s", sql)


def _params(params):
    if params is None:
        return None
    fix = lambda p: int(p) if isinstance(p, bool) else p
    if isinstance(params, dict):
        return {k: fix(v) for k, v in params.items()}
    return tuple(fix(p) for p in params)


class Cursor:
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        return self._cur.fetchone() if self._cur.description else None

    def fetchall(self):
        return self._cur.fetchall() if self._cur.description else []

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def rowcount(self):
        return self._cur.rowcount


class Connection:
    """Enough of sqlite3.Connection: execute/executemany/executescript/commit, and `with` = commit + close."""

    def __init__(self, url: str, schema: str):
        # prepare_threshold=None: Supabase's transaction pooler (PgBouncer) doesn't support prepared statements
        self._conn = psycopg.connect(url, prepare_threshold=None, autocommit=False)
        self._conn.execute(f"SET search_path TO {schema}")

    def execute(self, sql, params=None):
        cur = self._conn.cursor(row_factory=_row_factory)
        cur.execute(translate(sql), _params(params))
        return Cursor(cur)

    def executemany(self, sql, seq):
        cur = self._conn.cursor()
        cur.executemany(translate(sql), [_params(p) for p in seq])
        return Cursor(cur)

    def executescript(self, script):
        self._conn.execute(script)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self._conn.rollback() if exc_type else self._conn.commit()
        finally:
            self._conn.close()
        return False


def to_postgres_ddl(sqlite_ddl: str) -> str:
    ddl = re.sub(r"INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", sqlite_ddl)
    return re.sub(r"\bREAL\b", "DOUBLE PRECISION", ddl)  # REAL is 4-byte in Postgres: 0.35 would come back as 0.3499…


def _lock_down(conn, schema: str) -> None:
    """RLS on, no policies: Supabase's anon/authenticated roles can't read anything even if exposed."""
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,)).fetchall()
    for (t,) in tables:
        conn.execute(f"ALTER TABLE {schema}.{t} ENABLE ROW LEVEL SECURITY")
    conn.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
    for role in ("anon", "authenticated"):  # Supabase API roles; absent on plain Postgres
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone():
            conn.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM {role}")
            conn.execute(f"REVOKE ALL ON SCHEMA {schema} FROM {role}")


def init(url: str, main_ddl: str, vault_ddl: str, migrations) -> None:
    with psycopg.connect(url, prepare_threshold=None) as conn:
        for schema, ddl in ((MAIN_SCHEMA_NAME, main_ddl), (VAULT_SCHEMA_NAME, vault_ddl)):
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            conn.execute(f"SET search_path TO {schema}")
            conn.execute(to_postgres_ddl(ddl))
            if schema == MAIN_SCHEMA_NAME:
                for table, col, typ in migrations:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {to_postgres_ddl(typ)}")
            _lock_down(conn, schema)
        conn.commit()
