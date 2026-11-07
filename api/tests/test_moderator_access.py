"""Moderator-only access (Lane C request 7 Nov): key on /moderator/*, leaderboard moved there, page."""
import pytest
from fastapi.testclient import TestClient

import api.main as main
from api import db
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
MOD_GETS = [f"/moderator/rounds/{RID}", "/moderator/rounds", "/moderator/leaderboard?panel=TCD"]


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setattr(main, "MODERATOR_KEY", "s3cret-key")


@pytest.mark.parametrize("url", MOD_GETS)
def test_moderator_needs_key_when_set(keyed, url):
    with client:
        assert client.get(url).status_code == 401
        assert client.get(url, headers={"X-Moderator-Key": "wrong"}).status_code == 401
        assert client.get(url, headers={"X-Moderator-Key": "s3cret-key"}).status_code == 200


def test_moderator_posts_need_key(keyed):
    with client:
        assert client.post(f"/moderator/rounds/{RID}/advance").status_code == 401
        assert client.post("/moderator/invites", json={"expert_id": "EXP-TCD-01"}).status_code == 401


def test_expert_endpoints_do_not_need_the_key(keyed):
    with client:
        assert client.get(f"/rounds/{RID}").status_code == 200


def test_old_leaderboard_is_gone_for_everyone():
    with client:
        assert client.get("/leaderboard?panel=TCD").status_code == 410


def test_moderator_rounds_lists_all_stages():
    with client:
        rounds = client.get("/moderator/rounds").json()["rounds"]
    r = next(x for x in rounds if x["round_id"] == RID)
    assert {"stage", "n_responses", "risk_title", "country"} <= set(r)


def test_page_is_served_without_key_and_holds_no_data(keyed):
    with client:
        r = client.get("/ui/moderator")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert r.headers["cache-control"] == "no-store" and r.headers["x-frame-options"] == "DENY"
    html = r.text
    assert "X-Moderator-Key" in html
    for leak in ("psd_", "inv_demo", "Synthetic expert", "EXP-TCD"):
        assert leak not in html
    assert ".innerHTML" not in html   # free text is only ever inserted as text


def test_keyless_routes_never_contain_a_vault_identity():
    with client:
        client.get("/health")   # startup seeds the vault
        with db.vault_db() as v:
            names = [r["name"].lower() for r in v.execute("SELECT name FROM identity_vault")]
        bodies = [client.get("/ui/moderator").text, client.get("/leaderboard?panel=TCD").text]
    assert names and not [n for n in names for b in bodies if n in b.lower()]
