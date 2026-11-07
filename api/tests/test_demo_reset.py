"""TEMPORARY demo-only reset: off unless GT_DEMO_RESET=1; puts one round back to blind with no answers."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"


def post(i, version=1, prob=0.6):
    body = {"invite_token": f"inv_demo_{i:02d}", "tier": "pseudonymous", "version": version,
            "answers": [{"question_id": "Q-R1043-T0618", "prob": prob}, {"question_id": "Q-R1043-AGREE", "agree": True}],
            "reasoning_basis": ["field_observation"]}
    return client.post(f"/rounds/{RID}/responses", json=body).status_code


def submitted(i):
    r = client.get("/rounds/open?panel=TCD", headers={"X-Invite-Token": f"inv_demo_{i:02d}"}).json()
    return next(x for x in r["rounds"] if x["round_id"] == RID)["you_submitted"]


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("GT_DEMO_RESET", raising=False)
    assert post(1) == 201
    assert client.get(f"/moderator/rounds/{RID}").json()["demo_reset"] is False
    assert client.post(f"/moderator/rounds/{RID}/demo-reset").status_code == 404
    assert submitted(1) is True                         # nothing deleted


def test_reset_puts_round_back_to_start(monkeypatch):
    monkeypatch.setenv("GT_DEMO_RESET", "1")
    summaries_before = client.get("/public/summaries").json()
    assert [post(i) for i in (1, 2, 3)] == [201, 201, 201]
    assert client.post(f"/moderator/rounds/{RID}/advance").status_code == 200
    assert post(1, version=2, prob=0.3) == 201
    view = client.get(f"/moderator/rounds/{RID}").json()
    assert view["demo_reset"] is True and view["stage"] == "reveal" and view["n_responses"] == 3

    r = client.post(f"/moderator/rounds/{RID}/demo-reset")
    assert r.status_code == 200 and r.json() == {"round_id": RID, "stage": "blind", "removed_responses": 3}

    view = client.get(f"/moderator/rounds/{RID}").json()
    assert view["stage"] == "blind" and view["n_responses"] == 0 and view["free_text"] == []
    assert [submitted(i) for i in (1, 2, 3)] == [False, False, False]
    assert post(1) == 201                               # the same invite can answer again
    assert client.get("/public/summaries").json() == summaries_before


def test_unknown_round(monkeypatch):
    monkeypatch.setenv("GT_DEMO_RESET", "1")
    assert client.post("/moderator/rounds/NOPE/demo-reset").status_code == 404
