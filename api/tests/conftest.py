import pytest

from api import db, seed, trust


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Every test gets its own seeded main + vault DB (never touches api/var)."""
    monkeypatch.setattr(db, "MAIN_DB", tmp_path / "main.db")
    monkeypatch.setattr(db, "VAULT_DB", tmp_path / "vault.db")
    if db.DATABASE_URL:  # Postgres run (GT_DATABASE_URL set): start every test from empty schemas
        import psycopg
        with psycopg.connect(db.DATABASE_URL) as c:
            c.execute("DROP SCHEMA IF EXISTS gt CASCADE; DROP SCHEMA IF EXISTS gt_vault CASCADE")
    trust.reset_rate_limits()
    seed.seed(tmp_path / "no-synth")  # built-in panel: inv_demo_01..08
    yield
    trust.reset_rate_limits()
