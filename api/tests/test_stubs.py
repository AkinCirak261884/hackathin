import json
import re

import pytest
from fastapi.testclient import TestClient

from api import db
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"

ANSWER = {"invite_token": "inv_demo", "tier": "anonymous", "device_secret": "s3cret",
          "answers": [{"question_id": "Q-R1043-T0618", "prob": 0.6}]}

EXPERT_AND_PUBLIC = [
    ("get", "/rounds/open?panel=TCD", None),
    ("get", f"/rounds/{RID}", None),
    ("post", f"/rounds/{RID}/responses", ANSWER),
    ("get", f"/rounds/{RID}/aggregate?token=tok_demo_pseud_07", None),
    ("get", "/me/track-record?token=tok_demo_pseud_07", None),
    ("get", "/public/summaries", None),
]
MODERATOR = [
    ("get", f"/moderator/rounds/{RID}", None),
    ("post", f"/moderator/rounds/{RID}/advance", None),
    ("post", f"/moderator/rounds/{RID}/publish", {"approved_text": "ok"}),
]


def call(method, url, body):
    return client.post(url, json=body) if method == "post" else client.get(url)


@pytest.mark.parametrize("method,url,body", EXPERT_AND_PUBLIC + MODERATOR)
def test_every_endpoint_serves(method, url, body):
    r = call(method, url, body)
    assert r.status_code in (200, 201), r.text


@pytest.mark.parametrize("method,url,body", EXPERT_AND_PUBLIC)
def test_non_moderator_endpoints_never_leak_identity(method, url, body):
    payload = json.dumps(call(method, url, body).json()).lower()
    assert '"name"' not in payload and '"email"' not in payload
    assert not re.search(r"[\w.]+@[\w-]+\.\w+", payload), "email-like string leaked"
    assert "synthetic expert" not in payload


def test_public_aggregates_respect_min_n():
    for s in client.get("/public/summaries").json()["summaries"]:
        assert s["n"] >= 3


def test_unknown_round_is_404():
    assert client.get("/rounds/NOPE").status_code == 404


def test_schema_builds_with_vault_separated(tmp_path):
    main, vault = tmp_path / "m.db", tmp_path / "v.db"
    db.init_db(main, vault)
    main_tables = {r[0] for r in db.connect(main).execute("select name from sqlite_master where type='table'")}
    vault_tables = {r[0] for r in db.connect(vault).execute("select name from sqlite_master where type='table'")}
    assert {"risks", "triggers", "questions", "rounds", "experts", "contributions", "scores"} <= main_tables
    assert "identity_vault" not in main_tables
    assert {"identity_vault", "invites"} <= vault_tables
