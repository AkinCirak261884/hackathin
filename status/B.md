# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [x] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [x] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [x] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [x] **Requests from A + C.** `/me/track-record` + `/leaderboard` via `analysis/leaderboard.py`, opt-out, `reasoning_text`/`reasoning_basis` (moderator-only), peer-safe `/rounds/{id}/thread`. *Done when:* tests cover auth, no tokens in leaderboard, no free text to peers.
- [x] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [ ] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #5 — 19:33
Done: round lifecycle blind → reveal → closed (moderator advance, reveal needs n≥3, never backwards). blind = v1 only + locked view; reveal = v2 only vs frozen round-1 distribution (no real-time/timing leak); closed = final view. POST /moderator/rounds launches a round (core / short_horizon / ids) with its own question list. /rounds/open, /rounds/{id}, moderator view now real DB data (n, round-1 vs final, revision shifts, most-protective tier wins). All 139 risks seeded via Lane A's ingest; completion_rate as 0–1. 97 tests incl. a full stage walk
Pushed: lane-b @ HASH | PR: not opened yet (no gh CLI) → https://github.com/AkinCirak261884/hackathin/pull/new/lane-b
How to see it: `uv run --with-requirements api/requirements.txt uvicorn api.main:app` → localhost:8000/docs · 3× POST answers (inv_demo_01..03) → POST /moderator/rounds/RND-R1043-1/advance → GET aggregate
Requests to other lanes: →C: after submitting, aggregate/thread return `locked: true` until the moderator reveals; show "results unlock at reveal". v2 only in `reveal`. Use `view` ("locked"/"round_1"/"final"). Demo script needs an "advance" click · →A: your short_horizon.json is loaded; `POST /moderator/rounds {"risk_id":"R1043","question_set":"short_horizon"}` → pilot round RND-R1043-P2 (R1066 works too) · →A: your ingest stores completion_rate as 40.0; I convert to 0.4 (contract) when seeding
Contract change proposed: rounds gets `panel`, `closed_at`; new `round_questions`; aggregate gets `locked` + `view`; questions get `question_set`, `title`, `title_fr`, `text_fr`, `opens_at`, `resolution_criterion`; still open: ACAPS midpoints + B↔C option (c)
Next: AI synthesis (moderator only, Claude API, fallback without key)
Blockers: contracts/ not on main yet (PR #1)
