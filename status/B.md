# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [x] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [x] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [x] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [x] **Requests from A + C.** `/me/track-record` + `/leaderboard` via `analysis/leaderboard.py`, opt-out, `reasoning_text`/`reasoning_basis` (moderator-only), peer-safe `/rounds/{id}/thread`. *Done when:* tests cover auth, no tokens in leaderboard, no free text to peers.
- [ ] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [ ] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #4 — 19:18
Done: requests from A+C: /me/track-record + /leaderboard (via analysis/leaderboard.py, history/pending), POST /me/leaderboard-opt-out, reasoning_text/basis stored (moderator view `free_text` only), peer-safe GET /rounds/{id}/thread (aggregate + basis shares + approved themes, same 403/n≥3 gate); uvicorn IP access log disabled; startup seeding idempotent (revoked invites stay revoked); 86 tests incl. Lane A's synthetic round
Pushed: lane-b @ HASH | PR: not opened yet (no gh CLI) → https://github.com/AkinCirak261884/hackathin/pull/new/lane-b
How to see it: `uv run --with-requirements api/requirements.txt uvicorn api.main:app` → localhost:8000/docs (invites inv_demo_01..08)
Requests to other lanes: →C: track-record/leaderboard/thread/aggregate auth = headers X-Invite-Token (+ X-Device-Secret), no ?token= (web/src/api.js lines 80–88) · →A: thanks for adopting psd_/inv_demo_ IDs; my token request in #3 is resolved
Contract change proposed: field names decided (as contracts owner): `history` (resolved) + `pending`, `acaps_brier_same_questions` (alias `acaps_baseline_brier` until web/ switches) — will write into contracts/ once PR #1 merges · to agree on voice: ACAPS midpoints 0.05/0.22/0.50/0.78/0.95 (API already uses them via Lane A) and B↔C option (c), not implemented yet
Next: round lifecycle (blind → reveal → closed)
Blockers: contracts/ not on main yet (PR #1)
