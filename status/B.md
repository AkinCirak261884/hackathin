# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [ ] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [ ] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [ ] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [ ] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [ ] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #0 — --:--
Done: nothing yet
Pushed: none | PR: none
How to see it: —
Requests to other lanes: none
Contract change proposed: none
Next: schema + stubs
Blockers: none
