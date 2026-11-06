# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [x] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [ ] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [ ] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [ ] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [ ] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #1 — 23:00
Done: SQLite schema (vault + invites in separate vault.db), all 9 BOARD endpoints stubbed from api/mocks/*.json (real R1043 triggers), 18 tests incl. "non-moderator endpoints never leak name/email"
Pushed: lane-b @ 36c61a0 | PR: not opened yet (no gh CLI) → https://github.com/AkinCirak261884/hackathin/pull/new/lane-b
How to see it: `uv run --with-requirements api/requirements.txt uvicorn api.main:app` → localhost:8000/docs
Requests to other lanes: →C: build against localhost:8000 or api/mocks/*.json · →A: question_id format `Q-{risk}-{T####|AGREE}`, OK?
Contract change proposed: copy api/mocks/ into fixtures/ at freeze; add internal tables `invites`, `summaries`; `/aggregate` and `/me/track-record` take `?token=`; POST /responses body = {invite_token, tier, device_secret?, version, answers[{question_id, prob?, agree?}], triggers_observed[], missing_text?}
Next: tokens + identity vault (anonymous-tier hashing, invite check)
Blockers: none
