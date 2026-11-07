"""Moderator switch: peer comments off for one round (only ever stricter than the automatic rule)."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"   # R1043: eastern Chad, large area, automatic rule says comments ON
# different texts: near-identical answers are withheld from peers as possible coordination
TEXTS = {1: "armed men recruiting near the camps", 2: "fuel prices doubled in the market",
         3: "new checkpoints on the road to the border"}


def post(i):
    body = {"invite_token": f"inv_demo_{i:02d}", "tier": "pseudonymous", "version": 1,
            "answers": [{"question_id": "Q-R1043-T0618", "prob": 0.6}],
            "missing_text": "Seeing, not on ACAPS's list · 70% likely: " + TEXTS[i]}
    assert client.post(f"/rounds/{RID}/responses", json=body).status_code == 201


def comments_everywhere(i=1):
    h = {"X-Invite-Token": f"inv_demo_{i:02d}"}
    return (client.get(f"/rounds/{RID}").json()["comments"],
            client.get(f"/moderator/rounds/{RID}").json()["comments"],
            client.get(f"/rounds/{RID}/thread", headers=h).json())


def test_on_by_rule_then_off_by_moderator_then_back():
    for i in (1, 2, 3):
        post(i)
    assert client.post(f"/moderator/rounds/{RID}/advance").status_code == 200
    card, mod, thread = comments_everywhere()
    assert card["enabled"] and mod["enabled"] and thread["comments"]["enabled"] and card["moderator_off"] is False
    assert thread["additions"]                                   # peers see the additions while comments are on

    r = client.post(f"/moderator/rounds/{RID}/comments", json={"off": True})
    assert r.status_code == 200 and r.json()["enabled"] is False and r.json()["basis"] == "moderator"
    card, mod, thread = comments_everywhere()
    for c in (card, mod, thread["comments"]):
        assert c["enabled"] is False and c["moderator_off"] is True and c["auto_enabled"] is True
    assert "additions" not in thread                             # peer text withheld

    r = client.post(f"/moderator/rounds/{RID}/comments", json={"off": False})
    assert r.json()["enabled"] is True and r.json()["moderator_off"] is False
    assert comments_everywhere()[2]["additions"]


def test_cannot_force_on_where_the_rule_says_off(monkeypatch):
    monkeypatch.setenv("COMMENTS_MIN_ORGS", "100000")           # rule now says off for R1043
    r = client.post(f"/moderator/rounds/{RID}/comments", json={"off": False})
    assert r.status_code == 200 and r.json()["enabled"] is False and r.json()["basis"] == "few_orgs"


def test_demo_reset_puts_comments_back_to_automatic(monkeypatch):
    monkeypatch.setenv("GT_DEMO_RESET", "1")
    client.post(f"/moderator/rounds/{RID}/comments", json={"off": True})
    assert client.post(f"/moderator/rounds/{RID}/demo-reset").status_code == 200
    assert client.get(f"/rounds/{RID}").json()["comments"]["enabled"] is True


def test_unknown_round_and_bad_body():
    assert client.post("/moderator/rounds/NOPE/comments", json={"off": True}).status_code == 404
    assert client.post(f"/moderator/rounds/{RID}/comments", json={}).status_code == 422
