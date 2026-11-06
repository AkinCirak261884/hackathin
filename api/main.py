"""Ground Truth core API (Lane B). Responses are invite-checked and
get a tier-based author token (api/trust.py); other data is still mock JSON
from api/mocks/ so Lane C can build against the real URLs today.

Run:  uvicorn api.main:app --reload     (from the repo root)
"""
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api import db, seed, trust
from api.db import init_db

MOCKS = Path(__file__).parent / "mocks"


def mock(name: str) -> dict:
    return json.loads((MOCKS / f"{name}.json").read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(_app):
    init_db()
    with db.main_db() as m:
        if m.execute("SELECT COUNT(*) FROM experts").fetchone()[0] == 0:
            seed.seed()  # demo invites inv_demo_01..08 work out of the box
    yield


app = FastAPI(title="Ground Truth API", version="0.1.0-stub", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(trust.TrustError)
def _trust_error(_req: Request, exc: trust.TrustError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.detail})


# ---------- request models ----------

class Answer(BaseModel):
    question_id: str
    prob: Optional[float] = Field(None, ge=0, le=1)
    agree: Optional[bool] = None


class ResponseIn(BaseModel):
    invite_token: str
    tier: Literal["known", "pseudonymous", "anonymous"] = "anonymous"
    device_secret: Optional[str] = None  # anonymous tier only; hashed, never stored raw
    version: Literal[1, 2] = 1
    answers: list[Answer]
    triggers_observed: list[str] = []
    missing_text: Optional[str] = None


class PublishIn(BaseModel):
    approved_text: str


class InviteIn(BaseModel):
    expert_id: str
    country_panel: str = "TCD"


# ---------- expert / public ----------

def _round_or_404(round_id: str) -> dict:
    for r in mock("rounds_open")["rounds"]:
        if r["round_id"] == round_id:
            return r
    raise HTTPException(404, "round not found")


@app.get("/health")
def health():
    return {"ok": True, "stage": "stub"}


@app.get("/rounds/open")
def rounds_open(panel: str = "TCD"):
    data = mock("rounds_open")
    if panel.upper() != data["panel"]:
        return {"panel": panel.upper(), "rounds": []}
    return data


@app.get("/rounds/{round_id}")
def get_round(round_id: str):
    r = _round_or_404(round_id)
    return {
        **r,
        "risk": {"risk_id": "R1043", "country": "Chad", "probability": "High",
                 "impact": 4, "level": "High", "status": "Active"},
        "triggers": [
            {"trigger_id": "R1043 - T0618", "title": "Expansion of cross-border attacks and insecurity", "completion_rate": 0.4},
            {"trigger_id": "R1043 - T0619", "title": "Attacks on strategic infrastructure in Chad", "completion_rate": 0.1},
            {"trigger_id": "R1043 - T0620", "title": "Renewed proxy mobilisation and cross-border armed group activity", "completion_rate": 0.2},
        ],
        "questions": mock("_questions"),
    }


@app.post("/rounds/{round_id}/responses", status_code=201)
def post_response(round_id: str, body: ResponseIn):
    _round_or_404(round_id)
    token = trust.authenticate(body.invite_token, body.tier, body.device_secret)
    out = mock("response_created")
    out["author_token"] = token
    out["version"] = body.version
    out["stored"] = len(body.answers)
    out["can_revise"] = body.version == 1
    return out


@app.get("/rounds/{round_id}/aggregate")
def aggregate(round_id: str, token: Optional[str] = None):
    _round_or_404(round_id)
    return mock("aggregate")


@app.get("/me/track-record")
def track_record(token: str):
    return mock("track_record")


@app.get("/public/summaries")
def public_summaries():
    return mock("public_summaries")


# ---------- moderator ----------

@app.get("/moderator/rounds/{round_id}")
def moderator_round(round_id: str):
    _round_or_404(round_id)
    out = mock("moderator_round")
    for c in out["contributors"]:
        c["identity"] = trust.resolve_identity(c["author_token"], c["tier"])
    return out


@app.post("/moderator/invites", status_code=201)
def create_invite(body: InviteIn):
    return {"invite_token": trust.create_invite(body.expert_id, body.country_panel),
            "expert_id": body.expert_id, "country_panel": body.country_panel}


@app.post("/moderator/invites/{invite_token}/revoke")
def revoke_invite(invite_token: str):
    if not trust.revoke_invite(invite_token):
        raise HTTPException(404, "invite not found")
    return {"invite_token": invite_token, "revoked": True}


@app.post("/moderator/rounds/{round_id}/advance")
def advance(round_id: str):
    _round_or_404(round_id)
    return mock("advance")


@app.post("/moderator/rounds/{round_id}/publish")
def publish(round_id: str, body: PublishIn):
    _round_or_404(round_id)
    return mock("publish")
