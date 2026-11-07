"""Moderator view: field-based vs remote split from the experts' own "Based on" ticks."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
Q = "Q-R1043-T0618"


def post(i, prob, basis, agree=True, version=1):
    body = {"invite_token": f"inv_demo_{i:02d}", "tier": "pseudonymous", "version": version,
            "answers": [{"question_id": Q, "prob": prob}, {"question_id": "Q-R1043-AGREE", "agree": agree}],
            "reasoning_basis": basis}
    r = client.post(f"/rounds/{RID}/responses", json=body)
    assert r.status_code == 201, r.text


def split():
    return client.get(f"/moderator/rounds/{RID}").json()["basis_split"]


def q_item(s, qid=Q):
    return next(q for q in s["questions"] if q["question_id"] == qid)


def test_split_groups_and_gap():
    post(1, 0.8, ["field_observation"])
    post(2, 0.7, ["local_contacts", "media_osint"])   # any field source counts as field
    post(3, 0.9, ["field_observation"], agree=False)
    post(4, 0.3, ["media_osint"])
    post(5, 0.4, ["reports_data", "experience"])
    post(6, 0.5, ["reports_data"])
    post(7, 0.2, [])                                   # nothing ticked: in neither side
    s = split()
    assert s["groups"] == {"field": 3, "remote": 3, "not_stated": 1}
    item = q_item(s)
    assert item["field"]["n"] == 3 and item["field"]["median"] == 0.8
    assert item["remote"]["n"] == 3 and item["remote"]["median"] == 0.4
    assert item["median_gap"] == 0.4
    agree = q_item(s, "Q-R1043-AGREE")
    assert agree["field"]["agree_share"] == 0.67 and agree["remote"]["agree_share"] == 1.0
    assert agree["agree_gap"] == -0.33


def test_small_side_is_hidden():
    post(1, 0.8, ["field_observation"])
    post(2, 0.7, ["field_observation"])
    post(4, 0.3, ["media_osint"])
    post(5, 0.4, ["reports_data"])
    post(6, 0.5, ["reports_data"])
    item = q_item(split())
    assert item["field"]["suppressed"] is True and "median" not in item["field"]
    assert item["remote"]["suppressed"] is False
    assert "median_gap" not in item


def test_revision_keeps_the_first_answers_basis():
    for i, p in ((1, 0.8), (2, 0.7), (3, 0.9)):
        post(i, p, ["field_observation"])
    for i, p in ((4, 0.3), (5, 0.4), (6, 0.5)):
        post(i, p, ["media_osint"])
    assert client.post(f"/moderator/rounds/{RID}/advance").status_code == 200
    post(1, 0.2, [], version=2)                         # the web app sends no basis with a revision
    s = split()
    assert s["groups"] == {"field": 3, "remote": 3, "not_stated": 0}
    assert q_item(s)["field"]["median"] == 0.7          # latest answers: 0.2, 0.7, 0.9


def test_empty_round():
    s = split()
    assert s["groups"] == {"field": 0, "remote": 0, "not_stated": 0}
    assert all(q["field"]["suppressed"] and q["remote"]["suppressed"] for q in s["questions"])
