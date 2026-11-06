"""Ground Truth core API (Lane B). Real data for rounds, responses, aggregates, track record and
leaderboard. Still mock: AI clusters (moderator), publish flow and /public/summaries.

Run:  uvicorn api.main:app --reload     (from the repo root)
"""
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api import db, records, rounds, seed, trust
from api.db import init_db

MOCKS = Path(__file__).parent / "mocks"


def mock(name: str) -> dict:
    return json.loads((MOCKS / f"{name}.json").read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(_app):
    # No IP logging (BOARD.md): uvicorn's access log prints client IP:port, so switch it off here
    # rather than trusting everyone to pass --no-access-log.
    logging.getLogger("uvicorn.access").disabled = True
    init_db()
    seed.seed()  # idempotent: R1043 round + panel (Lane A's if present, else inv_demo_01..08)
    yield


app = FastAPI(title="Ground Truth API", version="0.2.0", lifespan=lifespan)
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
    missing_text: Optional[str] = Field(None, max_length=2000)
    reasoning_text: Optional[str] = Field(None, max_length=2000)   # moderator-only
    reasoning_basis: list[str] = []   # field_observation | local_contacts | media_osint | reports_data | experience


class PublishIn(BaseModel):
    approved_text: str


class RoundIn(BaseModel):
    risk_id: str
    question_set: Literal["core", "short_horizon"] = "core"
    question_ids: Optional[list[str]] = None   # overrides question_set
    panel: str = "TCD"


class AdvanceIn(BaseModel):
    to: Optional[Literal["reveal", "closed"]] = None   # optional safety check


class InviteIn(BaseModel):
    expert_id: str
    country_panel: str = "TCD"


# ---------- expert / public ----------

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/rounds/open")
def rounds_open(panel: str = "TCD", x_invite_token: Optional[str] = Header(None),
                x_device_secret: Optional[str] = Header(None)):
    """Open (blind/reveal) rounds for a panel. With headers, `you_submitted` is filled in."""
    return rounds.list_open(panel, x_invite_token, x_device_secret)


@app.get("/rounds/{round_id}")
def get_round(round_id: str):
    return rounds.round_detail(round_id)


@app.post("/rounds/{round_id}/responses", status_code=201)
def post_response(round_id: str, body: ResponseIn):
    return rounds.submit(round_id, body.invite_token, body.tier, body.device_secret, body.version,
                         [a.model_dump() for a in body.answers], body.triggers_observed, body.missing_text,
                         body.reasoning_text, body.reasoning_basis)


@app.get("/rounds/{round_id}/aggregate")
def aggregate(round_id: str,
              x_invite_token: str = Header(..., description="your invite token"),
              x_device_secret: Optional[str] = Header(None, description="anonymous tier only")):
    """Secrets go in headers, never in the URL (URLs end up in logs and browser history)."""
    return rounds.aggregate(round_id, x_invite_token, x_device_secret)


@app.get("/rounds/{round_id}/thread")
def round_thread(round_id: str,
                 x_invite_token: str = Header(...), x_device_secret: Optional[str] = Header(None)):
    """Peer-safe thread: aggregate + reasoning-basis shares + approved themes. No authors."""
    return rounds.thread(round_id, x_invite_token, x_device_secret)


@app.get("/me/track-record")
def track_record(x_invite_token: str = Header(...), x_device_secret: Optional[str] = Header(None)):
    """Your own record only. Send X-Device-Secret for your anonymous-tier record."""
    return records.track_record(x_invite_token, x_device_secret)


@app.get("/leaderboard")
def leaderboard(panel: str = "TCD", x_invite_token: Optional[str] = Header(None),
                x_device_secret: Optional[str] = Header(None)):
    """Peer leaderboard: display names only, no tokens. Headers optional (marks is_you)."""
    return records.leaderboard(panel, x_invite_token, x_device_secret)


@app.post("/me/leaderboard-opt-out")
def leaderboard_opt_out(x_invite_token: str = Header(...), x_device_secret: Optional[str] = Header(None)):
    return records.opt_out(x_invite_token, x_device_secret)


@app.get("/public/summaries")
def public_summaries():
    return mock("public_summaries")


# ---------- moderator ----------

@app.post("/moderator/rounds", status_code=201)
def create_round(body: RoundIn):
    """Launch a round in one click: core questions, Lane A's short-horizon pilot set, or explicit ids."""
    return rounds.create_round(body.risk_id, body.question_set, body.question_ids, body.panel)


@app.get("/moderator/rounds/{round_id}")
def moderator_round(round_id: str):
    out = rounds.moderator_view(round_id)
    m = mock("moderator_round")  # AI synthesis = task 5
    out["missing_clusters"], out["synthesis_source"] = m["missing_clusters"], m["synthesis_source"]
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
def advance(round_id: str, body: Optional[AdvanceIn] = None):
    """blind -> reveal (needs n >= 3) -> closed. Never backwards."""
    return rounds.advance(round_id, body.to if body else None)


@app.post("/moderator/rounds/{round_id}/publish")
def publish(round_id: str, body: PublishIn):
    rounds.get_round(round_id)
    return mock("publish")
