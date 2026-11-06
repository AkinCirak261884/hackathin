"""Lane B task 2: invites, tier tokens, vault separation, no identity leaks."""
import json

import pytest
from fastapi.testclient import TestClient

from api import db, seed, trust
from api.main import app

client = TestClient(app)
RID = "RND-R1043-1"
SECRET = "device-secret-0123456789"


def respond(invite="inv_demo_01", tier="pseudonymous", secret=None):
    body = {"invite_token": invite, "tier": tier,
            "answers": [{"question_id": "Q-R1043-T0618", "prob": 0.6}]}
    if secret:
        body["device_secret"] = secret
    return client.post(f"/rounds/{RID}/responses", json=body)


def vault_identities():
    with db.vault_db() as v:
        rows = v.execute("SELECT name, email FROM identity_vault").fetchall()
    return [x.lower() for r in rows for x in (r["name"], r["email"])]


# ---- invites ----

def test_valid_invite_is_accepted():
    assert respond().status_code == 201


def test_unknown_invite_is_rejected():
    assert respond(invite="inv_forged").status_code == 401


def test_revoked_invite_is_rejected():
    r = client.post("/moderator/invites/inv_demo_02/revoke")
    assert r.status_code == 200
    assert respond(invite="inv_demo_02").status_code == 401


def test_moderator_can_issue_new_invite():
    tok = client.post("/moderator/invites", json={"expert_id": "EXP-TCD-03"}).json()["invite_token"]
    assert tok.startswith("inv_") and respond(invite=tok).status_code == 201


def test_rate_limit_per_invite():
    for _ in range(trust.RATE_LIMIT):
        assert respond().status_code == 201
    assert respond().status_code == 429
    assert respond(invite="inv_demo_03").status_code == 201  # other invites unaffected


# ---- tier tokens ----

def test_pseudonymous_token_is_pseudonym_id_not_name():
    tok = respond(tier="pseudonymous").json()["author_token"]
    assert tok == "psd_EXP-TCD-01"


def test_anonymous_token_is_stable_and_unlinkable():
    a = respond(tier="anonymous", secret=SECRET).json()["author_token"]
    b = respond(invite="inv_demo_05", tier="anonymous", secret=SECRET).json()["author_token"]
    assert a == b                       # depends only on the device secret, not on the invite
    assert a.startswith("anon_") and "EXP-TCD" not in a and SECRET not in a
    other = respond(tier="anonymous", secret=SECRET + "x").json()["author_token"]
    assert other != a


def test_anonymous_tier_requires_strong_secret():
    assert respond(tier="anonymous").status_code == 422
    assert respond(tier="anonymous", secret="short").status_code == 422


# ---- identity separation ----

def test_main_db_has_no_identity_columns():
    with db.main_db() as m:
        tables = [r[0] for r in m.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        cols = {c[1] for t in tables for c in m.execute(f"PRAGMA table_info({t})")}
    assert not {"name", "email", "ip", "user_agent", "device_id"} & cols
    assert "identity_vault" not in tables and "invites" not in tables


def test_moderator_resolves_only_known_tier():
    assert trust.resolve_identity("psd_EXP-TCD-01", "known") == {"name": "Synthetic Expert 01"}
    assert trust.resolve_identity("psd_EXP-TCD-01", "pseudonymous") is None
    assert trust.resolve_identity(trust.anonymous_token(SECRET), "anonymous") is None
    contributors = client.get(f"/moderator/rounds/{RID}").json()["contributors"]
    for c in contributors:
        assert (c["identity"] is not None) == (c["tier"] == "known")


NON_MODERATOR = [
    ("get", "/rounds/open?panel=TCD"),
    ("get", f"/rounds/{RID}"),
    ("post", f"/rounds/{RID}/responses"),
    ("get", f"/rounds/{RID}/aggregate?token=psd_EXP-TCD-01"),
    ("get", "/me/track-record?token=psd_EXP-TCD-01"),
    ("get", "/public/summaries"),
]


@pytest.mark.parametrize("method,url", NON_MODERATOR)
@pytest.mark.parametrize("tier", trust.TIERS)
def test_no_non_moderator_endpoint_returns_a_vault_identity(method, url, tier):
    if method == "post":
        r = respond(tier=tier, secret=SECRET)
    else:
        r = client.get(url)
    assert r.status_code in (200, 201), r.text
    payload = json.dumps(r.json()).lower()
    leaked = [x for x in vault_identities() if x in payload]
    assert not leaked, f"{url} leaked {leaked}"


def test_every_route_is_covered_by_leak_test():
    """Fails if someone adds a non-moderator route without adding it above."""
    covered = {u.split("?")[0].replace(RID, "{round_id}") for _, u in NON_MODERATOR}
    routes = {r.path for r in app.routes if hasattr(r, "methods")}
    expert_routes = {p for p in routes if not p.startswith(("/moderator", "/docs", "/redoc", "/openapi"))}
    assert expert_routes - {"/health"} <= covered, expert_routes - covered
