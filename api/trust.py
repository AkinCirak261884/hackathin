"""Trust layer (Lane B): invites, author tokens per anonymity tier, rate limits,
and the single place where an identity can be resolved (moderator, "known" tier only).

Tiers (BOARD.md):
- known         token = pseudonym ID; moderator may resolve it to the vault identity.
- pseudonymous  token = pseudonym ID; never resolved, peers see only the pseudonym.
- anonymous     token = one-way hash of a device-held secret; scorable, never linked.

Honest limit: the server checks the invite when an anonymous answer arrives, so in
that moment it *could* see who sent it. We never store or log that link. Full
cryptographic unlinkability (blind-signed tokens) is a roadmap item, not built.
"""
import hashlib
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Literal, Optional

from api import db

Tier = Literal["known", "pseudonymous", "anonymous"]
TIERS = ("known", "pseudonymous", "anonymous")

MIN_DEVICE_SECRET_LEN = 16
RATE_LIMIT = 30           # requests ...
RATE_WINDOW_S = 600       # ... per 10 minutes, per invite


class TrustError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


# ---------- invites ----------

def create_invite(expert_id: str, country_panel: str, token: Optional[str] = None) -> str:
    token = token or "inv_" + secrets.token_urlsafe(18)
    with db.vault_db() as v:
        v.execute(
            "INSERT INTO invites (invite_token, expert_id, country_panel, created_at) VALUES (?,?,?,?)",
            (token, expert_id, country_panel, datetime.now(timezone.utc).isoformat()),
        )
    return token


def revoke_invite(token: str) -> bool:
    with db.vault_db() as v:
        return v.execute("UPDATE invites SET revoked = 1 WHERE invite_token = ?", (token,)).rowcount == 1


def check_invite(token: str) -> dict:
    """Returns {expert_id, country_panel} for a valid invite. Kept in memory only."""
    with db.vault_db() as v:
        row = v.execute(
            "SELECT expert_id, country_panel, revoked FROM invites WHERE invite_token = ?", (token,)
        ).fetchone()
    if row is None:
        raise TrustError(401, "unknown invite")
    if row["revoked"]:
        raise TrustError(401, "invite revoked")
    return {"expert_id": row["expert_id"], "country_panel": row["country_panel"]}


# ---------- rate limit (in memory, per invite) ----------

_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(token: str, now: Optional[float] = None) -> None:
    now = time.monotonic() if now is None else now
    q = _hits[token]
    while q and now - q[0] > RATE_WINDOW_S:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise TrustError(429, "too many requests for this invite")
    q.append(now)


def reset_rate_limits() -> None:
    _hits.clear()


# ---------- author tokens ----------

def pseudonym_token(expert_id: str) -> str:
    return "psd_" + expert_id


def anonymous_token(device_secret: str) -> str:
    if not device_secret or len(device_secret) < MIN_DEVICE_SECRET_LEN:
        raise TrustError(422, f"anonymous tier needs a device_secret of at least {MIN_DEVICE_SECRET_LEN} chars")
    return "anon_" + hashlib.sha256(("groundtruth-anon-v1:" + device_secret).encode()).hexdigest()[:32]


def author_token(tier: Tier, expert_id: str, device_secret: Optional[str] = None) -> str:
    if tier not in TIERS:
        raise TrustError(422, "unknown tier")
    if tier == "anonymous":
        return anonymous_token(device_secret or "")
    return pseudonym_token(expert_id)


def authenticate(invite_token: str, tier: Tier, device_secret: Optional[str] = None) -> str:
    """Invite check + rate limit + token derivation. Returns only the author token."""
    rate_limit(invite_token)
    expert_id = check_invite(invite_token)["expert_id"]
    return author_token(tier, expert_id, device_secret)


# ---------- moderator-only identity resolution ----------

def resolve_identity(author_token_: str, tier: Tier) -> Optional[dict]:
    """The only function that reads names. Returns None unless tier == 'known'."""
    if tier != "known" or not author_token_.startswith("psd_"):
        return None
    expert_id = author_token_[len("psd_"):]
    with db.vault_db() as v:
        row = v.execute("SELECT name FROM identity_vault WHERE expert_id = ?", (expert_id,)).fetchone()
    return {"name": row["name"]} if row else None
