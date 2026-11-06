# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [x] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [x] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [x] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [ ] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [ ] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #3 — 17:25
Done: real responses stored (v1 once per invite, v2 once + same tier, closed → 409); /aggregate gated on own submit (403), per-question suppression n<3, sorted dots, trigger shares, no free text; Lane A's responses_R1043.json posts cleanly end-to-end; 65 tests
Pushed: lane-b @ HASH | PR: not opened yet (no gh CLI) → https://github.com/AkinCirak261884/hackathin/pull/new/lane-b
How to see it: `uv run --with-requirements api/requirements.txt python -m pytest api/tests -q` · server: POST with `inv_demo_01..03`, then GET /rounds/RND-R1043-1/aggregate with header X-Invite-Token
Requests to other lanes: →A: tokens are derived server-side (`api.trust.author_token`: psd_<expert_id> / anon_+sha256("groundtruth-anon-v1:"+secret)[:32]) — for scoring, read author_token from `contributions` instead of your tok_exp_* / [:24] hash; seed auto-imports your vault.json/experts.json · →C: aggregate auth = headers X-Invite-Token (+ X-Device-Secret), not ?token=; see api/mocks/aggregate.json (per-question "suppressed", "n": "<3")
Contract change proposed: adopt Lane A's short trigger_id `T####` (API accepts both); /aggregate auth via headers; internal tables observed_triggers, round_participation
Next: round lifecycle (blind → reveal → closed)
Blockers: none
