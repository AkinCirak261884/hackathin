"""Ground Truth core API (Lane B). Stub stage: every endpoint serves mock JSON
from api/mocks/ so Lane C can build against the real URLs today.

Run:  uvicorn api.main:app --reload     (from the repo root)
"""
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.db import init_db

MOCKS = Path(__file__).parent / "mocks"


def mock(name: str) -> dict:
    return json.loads((MOCKS / f"{name}.json").read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(title="Ground Truth API", version="0.1.0-stub", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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
    out = mock("response_created")
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
    return mock("moderator_round")


@app.post("/moderator/rounds/{round_id}/advance")
def advance(round_id: str):
    _round_or_404(round_id)
    return mock("advance")


@app.post("/moderator/rounds/{round_id}/publish")
def publish(round_id: str, body: PublishIn):
    _round_or_404(round_id)
    return mock("publish")
