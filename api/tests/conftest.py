import pytest

from api import db, seed, trust


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Every test gets its own seeded main + vault DB (never touches api/var)."""
    monkeypatch.setattr(db, "MAIN_DB", tmp_path / "main.db")
    monkeypatch.setattr(db, "VAULT_DB", tmp_path / "vault.db")
    trust.reset_rate_limits()
    seed.seed(tmp_path / "no-synth")  # built-in panel: inv_demo_01..08
    yield
    trust.reset_rate_limits()
