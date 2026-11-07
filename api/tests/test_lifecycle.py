"""Lane B task 4: round lifecycle blind -> reveal -> closed, round creation, moderator view."""
import pytest
from fastapi.testclient import TestClient

from api import db, seed
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
Q = "Q-R1043-T0618"


def post(i, prob=0.5, version=1, rid=RID, qid=Q, tier="pseudonymous", **extra):
    return client.post(f"/rounds/{rid}/responses", json={
        "invite_token": f"inv_demo_{i:02d}", "tier": tier, "version": version,
        "answers": [{"question_id": qid, "prob": prob}], **extra})


def agg(i, rid=RID):
    return client.get(f"/rounds/{rid}/aggregate", headers={"X-Invite-Token": f"inv_demo_{i:02d}"})


def advance(rid=RID, **body):
    return client.post(f"/moderator/rounds/{rid}/advance", json=body or None)


def dots(i, rid=RID, qid=Q):
    return next(q for q in agg(i, rid).json()["questions"] if q["question_id"] == qid).get("dots")


def test_full_walk_blind_reveal_closed():
    # blind: answers in, results locked, no revisions
    for i, p in ((1, 0.2), (2, 0.5), (3, 0.8)):
        assert post(i, p).status_code == 201
    a = agg(1).json()
    assert a["stage"] == "blind" and a["locked"] is True and a["view"] == "locked"
    assert all(q["suppressed"] and "dots" not in q for q in a["questions"])
    assert "your_answers" not in a and a["can_revise"] is False
    assert post(1, 0.3, version=2).status_code == 409

    # reveal: frozen round-1 picture, one revision each, no late first answers
    r = advance(to="reveal").json()
    assert r == {"round_id": RID, "from_stage": "blind", "to_stage": "reveal", "n_responses": 3}
    assert dots(1) == [0.2, 0.5, 0.8] and agg(1).json()["can_revise"] is True
    assert post(4, 0.9).status_code == 409
    assert post(1, 0.45, version=2).status_code == 201
    assert dots(2) == [0.2, 0.5, 0.8]          # unchanged while revisions arrive: no timing leak
    assert agg(1).json()["can_revise"] is False

    # closed: final answers, nothing accepted
    assert advance().json()["to_stage"] == "closed"
    a = agg(2).json()
    assert a["view"] == "final" and dots(2) == [0.45, 0.5, 0.8]
    assert post(2, 0.6, version=2).status_code == 409
    assert advance().status_code == 409
    with db.main_db() as m:
        assert m.execute("SELECT closed_at FROM rounds WHERE round_id = ?", (RID,)).fetchone()[0]


def test_reveal_needs_three_answers():
    post(1)
    post(2)
    r = advance()
    assert r.status_code == 409 and "at least 3" in r.json()["detail"]


def test_advance_cannot_skip_stages():
    assert advance(to="closed").status_code == 409


def test_advance_unknown_round_404():
    assert advance(rid="NOPE").status_code == 404


def test_closed_round_leaves_open_list():
    for i in (1, 2, 3):
        post(i)
    assert [r["round_id"] for r in client.get("/rounds/open?panel=TCD").json()["rounds"]] == [RID]
    advance()
    advance()
    assert client.get("/rounds/open?panel=TCD").json()["rounds"] == []


def test_open_list_marks_you_submitted_with_header():
    post(1)
    mine = client.get("/rounds/open?panel=TCD", headers={"X-Invite-Token": "inv_demo_01"}).json()["rounds"][0]
    other = client.get("/rounds/open?panel=TCD", headers={"X-Invite-Token": "inv_demo_02"}).json()["rounds"][0]
    anon = client.get("/rounds/open?panel=TCD").json()["rounds"][0]
    assert (mine["you_submitted"], other["you_submitted"], anon["you_submitted"]) == (True, False, None)
    assert client.get("/rounds/open?panel=FRA").json()["rounds"] == []


# ---- round creation (moderator, one click) + Lane A's pilot questions ----

def test_round_detail_from_db():
    d = client.get(f"/rounds/{RID}").json()
    assert d["risk"]["probability"] == "High" and d["risk_title"].startswith("Escalating")
    assert [t["trigger_id"] for t in d["triggers"]] == ["T0618", "T0619", "T0620"]
    assert all(0 <= t["completion_rate"] <= 1 for t in d["triggers"])  # fraction, per contracts/
    assert d["triggers"][0]["completion_rate"] == 0.4
    assert [q["question_id"] for q in d["questions"]][0] == "Q-R1043-AGREE"
    assert len(d["questions"]) == 4 and all("outcome" not in q for q in d["questions"])


@pytest.mark.skipif(not seed.SHORT_HORIZON.exists(), reason="Lane A short_horizon.json not present")
def test_pilot_round_from_short_horizon_questions():
    r = client.post("/moderator/rounds", json={"risk_id": "R1043", "question_set": "short_horizon"})
    assert r.status_code == 201, r.text
    pilot = r.json()
    assert pilot["round_id"] == "RND-R1043-P2" and pilot["stage"] == "blind"
    assert pilot["question_ids"] and all("-SH" in q for q in pilot["question_ids"])
    d = client.get(f"/rounds/{pilot['round_id']}").json()
    assert all(q["question_set"] == "short_horizon" and q["title"] for q in d["questions"])
    # questions belong to their round: a core question is rejected in the pilot round, and vice versa
    assert post(1, rid=pilot["round_id"], qid=Q).status_code == 422
    assert post(1, rid=pilot["round_id"], qid=pilot["question_ids"][0]).status_code == 201
    assert post(1, qid=pilot["question_ids"][0]).status_code == 422
    assert len(client.get("/rounds/open?panel=TCD").json()["rounds"]) == 2


@pytest.mark.skipif(not seed.SHORT_HORIZON.exists(), reason="Lane A short_horizon.json not present")
def test_other_risk_pilot_round_lake_chad():
    r = client.post("/moderator/rounds", json={"risk_id": "R1066", "question_set": "short_horizon"})
    assert r.status_code == 201, r.text
    assert client.get(f"/rounds/{r.json()['round_id']}").json()["triggers"]


def test_create_round_with_explicit_ids_and_errors():
    r = client.post("/moderator/rounds", json={"risk_id": "R1043", "question_ids": [Q]})
    assert r.status_code == 201 and r.json()["question_ids"] == [Q]
    assert client.post("/moderator/rounds", json={"risk_id": "R9999"}).status_code == 404
    assert client.post("/moderator/rounds", json={"risk_id": "R1043", "question_ids": ["Q-NOPE"]}).status_code == 422
    assert client.post("/moderator/rounds", json={"risk_id": "R0353"}).status_code == 422  # no questions


# ---- moderator view ----

def test_moderator_view_real_numbers_and_shifts():
    post(1, 0.2, tier="known")
    post(2, 0.5)
    post(3, 0.8, tier="anonymous", device_secret="device-secret-0123456789")
    advance()
    post(1, 0.4, version=2, tier="known")
    v = client.get(f"/moderator/rounds/{RID}").json()
    assert v["stage"] == "reveal" and v["n_responses"] == 3 and v["n_revised"] == 1
    assert v["can_advance_to"] == "closed"
    assert v["revision_shifts"] == [{"question_id": Q, "n_revised": 1, "mean_shift": 0.2, "mean_abs_shift": 0.2}]
    final = next(q for q in v["questions"]["final"] if q["question_id"] == Q)
    assert final["dots"] == [0.4, 0.5, 0.8]
    ids = {c["tier"]: c["identity"] for c in v["contributors"]}
    assert ids["known"] == {"name": "Synthetic Expert 01"}
    assert ids["pseudonymous"] is None and ids["anonymous"] is None


def test_moderator_view_most_protective_tier_wins():
    post(1, 0.2, tier="known")
    post(2)
    post(3)
    advance()
    post(1, 0.3, version=2, tier="pseudonymous")  # same psd_ token, now asks not to be named
    c = next(c for c in client.get(f"/moderator/rounds/{RID}").json()["contributors"]
             if c["author_token"] == "psd_EXP-TCD-01")
    assert c["tier"] == "pseudonymous" and c["identity"] is None
