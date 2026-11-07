"""Late first answers (decided 8 Nov): accepted during the reveal, kept out of the frozen reveal view, counted in
the final view and on the moderator page."""
from fastapi.testclient import TestClient

from api import db
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
Q = "Q-R1043-T0618"
TEXT = {1: "armed men recruiting near the camps", 2: "fuel prices doubled in the market",
        3: "new checkpoints on the road to the border", 4: "cholera cases reported in the late answer camp",
        5: "a second late answer about grain prices"}


def post(i, prob, version=1, basis=("media_osint",), seeing=("T0618",)):
    body = {"invite_token": f"inv_demo_{i:02d}", "tier": "pseudonymous", "version": version,
            "answers": [{"question_id": Q, "prob": prob}], "triggers_observed": list(seeing),
            "reasoning_basis": list(basis), "missing_text": "Seeing, not on ACAPS's list: " + TEXT[i]}
    return client.post(f"/rounds/{RID}/responses", json=body)


def thread(i):
    return client.get(f"/rounds/{RID}/thread", headers={"X-Invite-Token": f"inv_demo_{i:02d}"}).json()


def q_of(view, qid=Q):
    return next(q for q in view["questions"] if q["question_id"] == qid)


def on_time_round():
    for i, p in ((1, 0.2), (2, 0.5), (3, 0.8)):
        assert post(i, p).status_code == 201
    assert client.post(f"/moderator/rounds/{RID}/advance").status_code == 200


def test_late_answer_is_accepted_but_the_reveal_view_stays_frozen():
    on_time_round()
    before = thread(1)
    r = post(4, 0.95, basis=("field_observation",), seeing=("T0619",))
    assert r.status_code == 201 and r.json()["late"] is True
    after = thread(1)
    for k in ("questions", "triggers_observed", "reasoning_basis"):
        assert after[k] == before[k], k                        # nothing peers see moved
    assert [a["text"] for a in after["additions"]] == [a["text"] for a in before["additions"]]
    assert not any("cholera" in a["text"] for a in after["additions"])
    late = thread(4)                                           # the late expert sees the same frozen picture
    assert late["late"] is True and late["can_revise"] is True and q_of(late)["dots"] == q_of(before)["dots"]
    assert post(4, 0.7, version=2).status_code == 201          # and may update once, like everyone


def test_moderator_sees_late_answers_and_final_view_counts_them():
    on_time_round()
    assert post(4, 0.95).status_code == 201
    m = client.get(f"/moderator/rounds/{RID}").json()
    assert m["n_responses"] == 4 and m["n_late"] == 1 and m["revealed_at"]
    assert [c["late"] for c in m["contributors"]] == [False, False, False, True]
    assert client.post(f"/moderator/rounds/{RID}/advance").status_code == 200   # close
    assert q_of(thread(1))["dots"] == [0.2, 0.5, 0.8, 0.95]
    assert post(5, 0.4).status_code == 409                     # closed: nothing accepted


def test_round_revealed_before_this_change_counts_earlier_answers_as_on_time():
    on_time_round()
    with db.main_db() as m:                                    # like the live round: no reveal time recorded
        m.execute("DELETE FROM round_reveals WHERE round_id = ?", (RID,))
    assert q_of(thread(1))["dots"] == [0.2, 0.5, 0.8]          # records 'now' on first use
    assert client.get(f"/moderator/rounds/{RID}").json()["n_late"] == 0
    assert post(4, 0.95).status_code == 201
    assert q_of(thread(1))["dots"] == [0.2, 0.5, 0.8]
    assert client.get(f"/moderator/rounds/{RID}").json()["n_late"] == 1


def test_demo_reset_forgets_the_reveal(monkeypatch):
    monkeypatch.setenv("GT_DEMO_RESET", "1")
    on_time_round()
    assert client.post(f"/moderator/rounds/{RID}/demo-reset").status_code == 200
    m = client.get(f"/moderator/rounds/{RID}").json()
    assert m["stage"] == "blind" and m["revealed_at"] is None and m["n_late"] == 0
