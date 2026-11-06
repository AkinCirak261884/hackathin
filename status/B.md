# Lane B — backend & trust

Folders: `api/`. Don't edit `contracts/`, `analysis/`, `moderator/`, `web/`.

## Tasks

- [x] **Schema + stubs.** SQLite schema from BOARD.md; every endpoint stubbed, returning the mock JSON from `fixtures/`. *Done when:* `uvicorn api.main:app` serves all endpoints.
- [x] **Tokens + identity vault.** Invite tokens, author tokens per tier, anonymous-tier hashing; vault kept separate from contributions. *Done when:* tests prove no public endpoint ever returns a name or email.
- [ ] **Real responses + min-3 rule.** `POST /rounds/{id}/responses` stores v1/v2; `/aggregate` returns nothing until n ≥ 3 and only after the caller's own submit. *Done when:* tests cover n = 2 and n = 3.
- [ ] **Round lifecycle.** blind → reveal → closed via `/moderator/rounds/{id}/advance`. *Done when:* a test walks a round through all stages.
- [ ] **AI synthesis (moderator only).** Cluster "what's missing" answers via the Claude API, linked back to responses. *Done when:* the moderator endpoint returns clusters; falls back to a prepared summary if no API key.
- [ ] **Publish flow.** Moderator-approved summary → `/public/summaries`. *Done when:* the public endpoint shows only aggregates and approved text.

## Latest update

### Lane B — update #2 — 17:25
Done: trust layer (api/trust.py): invite check/revoke + rate limit, tier tokens (psd_<id> / anon_<sha256(device secret)>), moderator-only identity resolve (known tier); 8 synthetic TCD experts auto-seeded; 47 tests incl. "no non-moderator endpoint returns any vault name/email, for all 3 tiers"
Pushed: lane-b @ d786e93 | PR: not opened yet (no gh CLI) → https://github.com/AkinCirak261884/hackathin/pull/new/lane-b
How to see it: `uv run --with-requirements api/requirements.txt uvicorn api.main:app` → localhost:8000/docs, POST a response with invite `inv_demo_01`
Requests to other lanes: →A: DB lives at api/var/groundtruth.db (env GT_DB); run `ingest.py --db api/var/groundtruth.db` only before real responses exist (it recreates the file) · →C: send invite_token + tier on every response; anonymous tier = generate a ≥16-char device_secret once, keep it in localStorage
Contract change proposed: (from #1, still open) POST /responses body; new moderator endpoints POST /moderator/invites, POST /moderator/invites/{token}/revoke
Next: real responses + min-3 rule
Blockers: none
