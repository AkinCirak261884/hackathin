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

### Lane B — update #7 — 7 Nov afternoon
Done: (1) Collective view only: `/aggregate` + `/thread` no longer return `your_answers` (team decision). (2) Comments on/off per round from OCHA 3W operational presence (HDX): ≥ 30 organisations in the risk's affected area → on; fewer, or no 3W data → off (`api/comments_policy.py`, snapshot `api/data/presence_3w.json`, CC BY). R1043 eastern Chad 146 → on; West Kordofan 17 → off. (3) On request: Ukraine "now, according to ACAPS" card committed on lane-c (2918647). 123 tests.
Pushed: lane-b merged into main (f4e6816) → blocker #0 (api/ on main) fixed
How to see it: GET /rounds/RND-R1043-1 → `comments` block · `api/README.md` → "Comments on/off"
Requests to other lanes: →C: hide comment UI when `comments.enabled` is false; drop "you" markers on reveal (both on BOARD)
Contract change proposed: round, thread and moderator round get `comments {enabled, n_orgs, min_orgs, areas, area_basis, reason, source}`; aggregate drops `your_answers`
Next: C's request: `/leaderboard` behind the moderator key; then publish flow
Blockers: none
