"""Lane A/C requests to B: track record + leaderboard (via analysis/leaderboard.py),
reasoning fields (moderator-only), peer-safe thread."""
import json

from fastapi.testclient import TestClient

from api import db
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
SECRET = "device-secret-0123456789"
Q = "Q-R1043-T0618"


def post(i, prob=0.5, tier="pseudonymous", secret=None, **extra):
    body = {"invite_token": f"inv_demo_{i:02d}", "tier": tier,
            "answers": [{"question_id": Q, "prob": prob}], **extra}
    if secret:
        body["device_secret"] = secret
    r = client.post(f"/rounds/{RID}/responses", json=body)
    assert r.status_code == 201, r.text
    return r


def hdr(i, secret=None):
    h = {"X-Invite-Token": f"inv_demo_{i:02d}"}
    if secret:
        h["X-Device-Secret"] = secret
    return h


def resolve(qid=Q, outcome=1):
    with db.main_db() as m:
        m.execute("UPDATE questions SET outcome = ? WHERE question_id = ?", (outcome, qid))


# ---- track record ----

def test_track_record_pending_then_resolved():
    post(1, 0.8)
    rec = client.get("/me/track-record", headers=hdr(1)).json()
    assert rec["n_resolved"] == 0 and [p["question_id"] for p in rec["pending"]] == [Q]
    resolve(outcome=1)
    rec = client.get("/me/track-record", headers=hdr(1)).json()
    h = rec["history"][0]
    assert h["question_id"] == Q and h["your_prob"] == 0.8 and abs(h["brier"] - 0.04) < 1e-9
    assert h["acaps_prob"] == 0.78  # R1043 is High -> band midpoint
    assert "acaps_brier_same_questions" in rec and "acaps_baseline_brier" in rec


def test_track_record_requires_invite_header():
    assert client.get("/me/track-record").status_code == 422
    assert client.get("/me/track-record?token=psd_EXP-TCD-01").status_code == 422  # no ?token= access
    assert client.get("/me/track-record", headers={"X-Invite-Token": "inv_forged"}).status_code == 401


def test_anonymous_and_pseudonymous_records_are_separate():
    post(1, 0.9, tier="anonymous", secret=SECRET)
    resolve()
    assert client.get("/me/track-record", headers=hdr(1)).json()["n_resolved"] == 0
    anon = client.get("/me/track-record", headers=hdr(1, SECRET)).json()
    assert anon["n_resolved"] == 1 and anon["author_token"].startswith("anon_")


# ---- leaderboard ----

def test_leaderboard_has_no_tokens_and_marks_you():
    for i in range(1, 4):
        post(i, 0.3 * i)
    resolve()
    lb = client.get("/leaderboard?panel=TCD", headers=hdr(1)).json()
    dump = json.dumps(lb)
    assert "psd_" not in dump and "anon_" not in dump and "inv_" not in dump
    assert lb["panel"] == "TCD" and "entries" in lb
    assert client.get("/leaderboard").status_code == 200  # headers optional


def test_opt_out_is_stored():
    post(1)
    assert client.post("/me/leaderboard-opt-out", headers=hdr(1)).json() == {"opted_out": True}
    with db.main_db() as m:
        assert m.execute("SELECT author_token FROM leaderboard_opt_out").fetchall()[0][0] == "psd_EXP-TCD-01"


# ---- reasoning (Lane C request) ----

def test_reasoning_stored_and_moderator_only():
    post(1, reasoning_text="I saw convoys near Adre", reasoning_basis=["field_observation", "local_contacts"],
         missing_text="Rainy season")
    post(2)
    post(3)
    mod = client.get(f"/moderator/rounds/{RID}").json()["free_text"]
    assert mod == [{"response_id": mod[0]["response_id"], "version": 1, "tier": "pseudonymous",
                    "missing_text": "Rainy season", "reasoning_text": "I saw convoys near Adre",
                    "reasoning_basis": ["field_observation", "local_contacts"]}]
    for url in (f"/rounds/{RID}/aggregate", f"/rounds/{RID}/thread"):
        body = client.get(url, headers=hdr(2)).text
        assert "convoys" not in body and "Rainy season" not in body


def test_unknown_reasoning_basis_is_422():
    r = client.post(f"/rounds/{RID}/responses", json={
        "invite_token": "inv_demo_01", "answers": [{"question_id": Q, "prob": 0.5}],
        "reasoning_basis": ["gossip"]})
    assert r.status_code == 422


# ---- thread (Lane C request) ----

def test_thread_gated_and_suppressed():
    post(2)
    assert client.get(f"/rounds/{RID}/thread", headers=hdr(1)).status_code == 403
    post(1, reasoning_basis=["media_osint"])
    t = client.get(f"/rounds/{RID}/thread", headers=hdr(1)).json()
    assert t["suppressed"] is True and t["reasoning_basis"] == [] and t["themes"] == []


def test_thread_shows_shares_and_approved_themes_only():
    post(1, reasoning_basis=["media_osint"])
    post(2, reasoning_basis=["media_osint", "experience"])
    post(3)
    with db.main_db() as m:
        m.execute("INSERT INTO summaries VALUES (?,?,?)", (RID, "Access constraints under-rated.", "2026-11-07"))
        m.execute("UPDATE rounds SET stage = 'reveal' WHERE round_id = ?", (RID,))
    t = client.get(f"/rounds/{RID}/thread", headers=hdr(3)).json()
    assert t["suppressed"] is False
    assert t["reasoning_basis"] == [{"basis": "experience", "share": 0.33}, {"basis": "media_osint", "share": 0.67}]
    assert t["themes"][0]["text"] == "Access constraints under-rated."
    assert "author_token" not in json.dumps(t)
