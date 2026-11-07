"""Lane B task 3: stored v1/v2 responses, min-3 rule, own-submit gate."""
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import db, seed, trust
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
SECRET = "device-secret-0123456789"
Q = "Q-R1043-T0618"


def post(i=1, prob=0.5, version=1, tier="pseudonymous", secret=None, **extra):
    body = {"invite_token": f"inv_demo_{i:02d}", "tier": tier, "version": version,
            "answers": [{"question_id": Q, "prob": prob},
                        {"question_id": "Q-R1043-AGREE", "agree": True}], **extra}
    if secret:
        body["device_secret"] = secret
    return client.post(f"/rounds/{RID}/responses", json=body)


def agg(i=1, secret=None):
    h = {"X-Invite-Token": f"inv_demo_{i:02d}"}
    if secret:
        h["X-Device-Secret"] = secret
    return client.get(f"/rounds/{RID}/aggregate", headers=h)


def stage(s):
    """Set the stage directly (unit tests); the advance endpoint is tested in test_lifecycle.py."""
    with db.main_db() as m:
        m.execute("UPDATE rounds SET stage = ? WHERE round_id = ?", (s, RID))


def q_of(aggregate, qid=Q):
    return next(q for q in aggregate["questions"] if q["question_id"] == qid)


# ---- storing ----

def test_response_is_stored_without_identity():
    assert post(1, 0.6, missing_text="Rainy season access").status_code == 201
    with db.main_db() as m:
        rows = m.execute("SELECT * FROM contributions WHERE round_id = ?", (RID,)).fetchall()
    assert len(rows) == 2 and {r["author_token"] for r in rows} == {"psd_EXP-TCD-01"}
    assert {r["version"] for r in rows} == {1}


def test_v1_only_once_per_invite():
    assert post(1).status_code == 201
    assert post(1).status_code == 409
    assert post(1, tier="anonymous", secret=SECRET).status_code == 409  # tier switch can't double-vote


def test_v2_needs_v1_and_only_once():
    assert post(1).status_code == 201
    stage("reveal")
    assert post(2, version=2).status_code == 409   # no v1 from this invite
    assert post(1, 0.8, version=2).status_code == 201
    assert post(1, 0.9, version=2).status_code == 409


def test_v2_must_keep_same_tier():
    assert post(1, tier="anonymous", secret=SECRET).status_code == 201
    stage("reveal")
    assert post(1, version=2, tier="pseudonymous").status_code == 409
    assert post(1, version=2, tier="anonymous", secret=SECRET).status_code == 201


def test_participation_record_does_not_link_anonymous_token():
    post(1, tier="anonymous", secret=SECRET)
    with db.vault_db() as v:
        cols = {c[1] for c in v.execute("PRAGMA table_info(round_participation)")}
        dump = json.dumps([dict(r) for r in v.execute("SELECT * FROM round_participation")])
    assert "author_token" not in cols and "anon_" not in dump


def test_same_device_secret_on_two_invites_is_409_not_500():
    assert post(1, tier="anonymous", secret=SECRET).status_code == 201
    assert post(2, tier="anonymous", secret=SECRET).status_code == 409


@pytest.mark.parametrize("bad", [
    {"answers": [{"question_id": "Q-NOPE", "prob": 0.5}]},
    {"answers": [{"question_id": Q, "prob": 0.5}, {"question_id": Q, "prob": 0.6}]},
    {"answers": []},
    {"answers": [{"question_id": Q, "prob": 1.5}]},
    {"triggers_observed": ["T9999"]},
])
def test_invalid_bodies_are_422(bad):
    body = {"invite_token": "inv_demo_01", "tier": "pseudonymous",
            "answers": [{"question_id": Q, "prob": 0.5}], **bad}
    assert client.post(f"/rounds/{RID}/responses", json=body).status_code == 422


def test_closed_round_rejects_answers():
    with db.main_db() as m:
        m.execute("UPDATE rounds SET stage = 'closed' WHERE round_id = ?", (RID,))
    assert post(1).status_code == 409


def test_unknown_round_404():
    assert client.post("/rounds/NOPE/responses", json={"invite_token": "inv_demo_01", "answers": []}).status_code == 404


# ---- aggregate ----

def test_aggregate_locked_before_own_submit():
    for i in (2, 3, 4):
        post(i)
    assert agg(1).status_code == 403
    assert agg(99).status_code == 401  # unknown invite


def test_n2_is_suppressed():
    post(1, 0.4)
    post(2, 0.6)
    stage("reveal")  # forced: advance itself refuses n < 3
    a = agg(1).json()
    assert a["suppressed"] is True
    q = q_of(a)
    assert q["suppressed"] is True and "median" not in q and "dots" not in q and q["n"] == "<3"
    assert a["triggers_observed"] == []


def test_n3_is_shown_with_sorted_dots():
    post(1, 0.7)
    post(2, 0.2)
    post(3, 0.5)
    stage("reveal")
    q = q_of(agg(2).json())
    assert q["suppressed"] is False and q["n"] == 3
    assert q["dots"] == [0.2, 0.5, 0.7] and q["median"] == 0.5
    assert q_of(agg(2).json(), "Q-R1043-AGREE")["agree_share"] == 1.0


def test_revision_counts_once_and_uses_latest():
    post(1, 0.1)
    post(2, 0.5)
    post(3, 0.9)
    stage("reveal")
    post(1, 0.6, version=2)
    a = agg(1).json()
    assert q_of(a)["dots"] == [0.1, 0.5, 0.9]          # reveal shows the frozen round-1 picture
    assert "your_answers" not in a and a["can_revise"] is False
    stage("closed")
    q = q_of(agg(1).json())
    assert q["n"] == 3 and q["dots"] == [0.5, 0.6, 0.9]  # final view: latest version, counted once


def test_anonymous_caller_needs_device_secret_to_unlock():
    post(1, tier="anonymous", secret=SECRET)
    post(2)
    post(3)
    stage("reveal")
    assert agg(1).status_code == 403
    assert agg(1, secret=SECRET).status_code == 200


def test_triggers_observed_share():
    post(1, triggers_observed=["T0618"])
    post(2, triggers_observed=["R1043 - T0618", "T0619"])  # long form accepted
    post(3)
    stage("reveal")
    t = {x["trigger_id"]: x["share"] for x in agg(1).json()["triggers_observed"]}
    assert t == {"T0618": 0.67, "T0619": 0.33}


def test_aggregate_never_contains_free_text():
    post(1, missing_text="SECRET-FIELD-NOTE")
    post(2)
    post(3)
    stage("closed")
    assert "SECRET-FIELD-NOTE" not in agg(1).text


# ---- integration with Lane A's synthetic round ----

SYNTH = Path(os.environ.get("GT_SYNTH_DIR", seed.SYNTH_DIR))


@pytest.mark.skipif(not (SYNTH / "responses_R1043.json").exists(), reason="Lane A synthetic data not present")
def test_lane_a_synthetic_round_posts_cleanly(tmp_path):
    seed.seed(SYNTH)
    bodies = json.loads((SYNTH / "responses_R1043.json").read_text(encoding="utf-8"))
    for version in (1, 2):
        for b in [b for b in bodies if b["version"] == version]:
            b = {k: v for k, v in b.items() if not k.startswith("_")}
            r = client.post(f"/rounds/{RID}/responses", json=b)
            assert r.status_code == 201, r.text
        if version == 1:
            assert client.post(f"/moderator/rounds/{RID}/advance").json()["to_stage"] == "reveal"
    first = next(b for b in bodies if b["version"] == 1)
    a = client.get(f"/rounds/{RID}/aggregate", headers={
        "X-Invite-Token": first["invite_token"], **({"X-Device-Secret": first["device_secret"]}
                                                     if first.get("device_secret") else {})}).json()
    assert a["suppressed"] is False and q_of(a)["n"] == len({b["invite_token"] for b in bodies})


# ---- collective view only (team decision 7 Nov: experts don't see their own answers back) ----

def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


@pytest.mark.parametrize("s", ["blind", "reveal", "closed"])
def test_group_views_never_return_your_own_answers(s):
    for i, p in ((1, 0.15), (2, 0.5), (3, 0.85)):
        post(i, p, tier="anonymous" if i == 1 else "pseudonymous", secret=SECRET if i == 1 else None)
    stage(s)
    h = {"X-Invite-Token": "inv_demo_01", "X-Device-Secret": SECRET}
    for path in ("aggregate", "thread"):
        body = client.get(f"/rounds/{RID}/{path}", headers=h).json()
        keys = set(_keys(body))
        assert not keys & {"your_answers", "you", "your_prob", "mine", "author_token"}, (path, keys)
    if s != "blind":   # the group numbers are still there, and include everyone once n >= 3
        assert q_of(agg(1, SECRET).json())["dots"] == [0.15, 0.5, 0.85]
