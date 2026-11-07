"""Track record + peer leaderboard: thin wrappers over Lane A's analysis/leaderboard.py
(single source of truth for scoring), plus Lane B's auth and privacy rules.

Field names (Lane B decision, as contracts owner): `history` = resolved forecasts,
`pending` = unresolved; ACAPS comparison = `acaps_brier_same_questions`
(`acaps_baseline_brier` kept as an alias until web/ switches).
"""
import sys
from pathlib import Path
from typing import Optional

from api import db, trust

_ANALYSIS = Path(__file__).resolve().parent.parent / "analysis"
if str(_ANALYSIS) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS))  # leaderboard.py does `from scoring import ...`

import leaderboard as lb  # noqa: E402


def caller_token(invite_token: str, device_secret: Optional[str]) -> str:
    """Anonymous record if the phone sends its secret, otherwise the pseudonym record.
    The two are never merged, so the response can't link them."""
    trust.rate_limit(invite_token)
    expert_id = trust.check_invite(invite_token)["expert_id"]
    if device_secret:
        return trust.anonymous_token(device_secret)
    return trust.pseudonym_token(expert_id)


def track_record(invite_token: str, device_secret: Optional[str]) -> dict:
    token = caller_token(invite_token, device_secret)
    with db.main_db() as m:
        out = lb.track_record(m, token)
    out["impact"] = []  # filled by the publish flow (moderator cites your input)
    return out


def leaderboard(panel: str, invite_token: Optional[str], device_secret: Optional[str]) -> dict:
    viewer = caller_token(invite_token, device_secret) if invite_token else None
    with db.main_db() as m:
        out = lb.leaderboard(m, viewer)
    out["panel"] = panel.upper()
    return out


def opt_out(invite_token: str, device_secret: Optional[str]) -> dict:
    token = caller_token(invite_token, device_secret)
    with db.main_db() as m:
        m.execute("INSERT OR IGNORE INTO leaderboard_opt_out VALUES (?)", (token,))
    return {"opted_out": True}
