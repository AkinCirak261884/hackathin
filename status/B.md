# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [x] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [x] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [x] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [x] **Requests from A + C.** `/me/track-record` + `/leaderboard` via `analysis/leaderboard.py`, opt-out, `reasoning_text`/`reasoning_basis` (moderator-only), peer-safe `/rounds/{id}/thread`. *Done when:* tests cover auth, no tokens in leaderboard, no free text to peers.
- [x] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [x] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #6 — 19:39
Done: AI synthesis (api/synthesis.py): POST /moderator/rounds/{id}/synthesis clusters "what's missing" with Claude (claude-opus-5-5, JSON schema, fallbacks "default"), cached per input hash; GET moderator view never calls the API. Output validated (unknown ids dropped, 1 cluster/answer), identifying-detail flags, prompt-injection-safe wrapping, local copy-paste/coordination flags. No key / error / refusal → keyword grouping labelled "no AI". On Lane A's R1043 round: 6 answers → 4 clusters. 111 tests (fake client, no network)
Pushed: lane-b @ HASH | PR: not opened yet (no gh CLI) → https://github.com/AkinCirak261884/hackathin/pull/new/lane-b
How to see it: server → post answers with missing_text → POST /moderator/rounds/RND-R1043-1/synthesis → GET /moderator/rounds/RND-R1043-1 (`missing_clusters`). Real AI needs ANTHROPIC_API_KEY in the server env
Requests to other lanes: →A: moderator dashboard can show `missing_clusters` (+ `response_ids` → `free_text`), `identifying_details`, `coordination_flags`, `synthesis_source`; add a "Run AI synthesis" button = POST …/synthesis · →A: your `aggregate.aggregate()` / `disagreement()` request (#9) is next on my list · →C: nothing new for the expert app (synthesis is moderator-only)
Contract change proposed: moderator round gets `identifying_details`, `coordination_flags`, `fallback_reason`, `model`, `synthesis_generated_at`; new endpoint POST /moderator/rounds/{id}/synthesis; still open: ACAPS midpoints + B↔C option (c)
Next: publish flow (moderator-approved summary → /public/summaries), then Lane A's aggregate/disagreement request
Blockers: need an Anthropic API key for the live demo (otherwise fallback); contracts/ not on main (PR #1)
