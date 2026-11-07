# api/ — Lane B (backend & trust)

```
uv run --with-requirements api/requirements.txt uvicorn api.main:app --reload   # http://localhost:8000/docs
uv run --with-requirements api/requirements.txt python -m pytest api/tests -q
```

Stub stage: all endpoints from BOARD.md serve `api/mocks/*.json`. Identities and invites live in a
separate SQLite file (`api/var/vault.db`), so the contributions DB holds no names or emails.

## Trust layer (`api/trust.py`)

- Demo panel seeds automatically on first start (or `python -m api.seed`): invites `inv_demo_01` … `inv_demo_08`.
- `POST /rounds/{id}/responses` needs a valid invite (401 if unknown/revoked, 429 over 30 req / 10 min).
- Author token: `psd_<expert_id>` for known/pseudonymous, `anon_<sha256(device_secret)>` for anonymous
  (device_secret ≥ 16 chars, generated and kept on the phone).
- Only `trust.resolve_identity` reads names, and only for the "known" tier (moderator view).
- Moderator: `POST /moderator/invites {expert_id}` · `POST /moderator/invites/{token}/revoke`.
- DB paths: `GT_DB`, `GT_VAULT_DB` env vars (default `api/var/`).

## Responses & aggregate (`api/rounds.py`)

- v1 once per invite per round; v2 once, after v1, same tier. Closed round → 409.
- `GET /rounds/{id}/aggregate` with headers `X-Invite-Token` (+ `X-Device-Secret` for anonymous).
  403 until you submitted; each question `suppressed` until n ≥ 3 distinct authors (latest version
  counts); dots sorted; free text never included. Collective view only: the caller never gets
  their own answers back (no `your_answers`), only group numbers (team decision 7 Nov).
- Lane A data: if `analysis/synthetic/` exists, the seed uses that panel (invites `inv_tcd_01…`), and
  `responses_R1043.json` posts cleanly (test `test_lane_a_synthetic_round_posts_cleanly`).

## Track record, leaderboard, thread (requests from A and C)

- `GET /me/track-record` — headers `X-Invite-Token` (+ `X-Device-Secret` for your anonymous record;
  the two records are never merged). Computed by `analysis/leaderboard.py` (Lane A). Fields:
  `history` = resolved, `pending` = open; ACAPS comparison `acaps_brier_same_questions`
  (`acaps_baseline_brier` alias, to be removed).
- `GET /leaderboard?panel=TCD` — display names only, no tokens; headers optional (marks `is_you`).
  `POST /me/leaderboard-opt-out`.
- `GET /rounds/{id}/thread` — peer view: aggregate + reasoning-basis shares + approved themes.
  Same 403 / n ≥ 3 gate. Never individual replies or verbatim text.
- `reasoning_text` / `reasoning_basis` stored on responses, visible only in `GET /moderator/rounds/{id}` → `free_text`.
- No `?token=` anywhere: tokens and secrets go in headers. Uvicorn's access log (client IPs) is disabled at startup.

## Round lifecycle (`api/rounds.py`)

| stage | accepts | `/aggregate` + `/thread` (after your own v1) |
|---|---|---|
| `blind` | v1 only | `locked: true`, no numbers (so nothing changes in real time) |
| `reveal` | v2 only (one revision) | `view: "round_1"`, frozen v1 distribution |
| `closed` | nothing | `view: "final"`, each author's latest answer |

- `POST /moderator/rounds/{id}/advance` (optional body `{"to": "reveal"|"closed"}`): blind → reveal needs ≥ 3 answers; never backwards.
- `POST /moderator/rounds {"risk_id", "question_set": "core"|"short_horizon", "question_ids"?}` launches a round
  (Lane A's `analysis/questions/short_horizon.json` is loaded as `short_horizon`, e.g. pilot `RND-R1043-P2`).
- Each round has its own question list (`round_questions`); answers to other questions → 422.
- `GET /rounds/open?panel=TCD` and `GET /rounds/{id}` now come from the DB (all 139 Risk Radar risks are seeded
  via Lane A's `ingest.py`; `completion_rate` is a 0–1 fraction).
- `GET /moderator/rounds/{id}`: real n, round-1 vs final distributions (from n = 1), revision shifts, contributors
  (identity only if every answer of that token was "known"), free text. AI clusters still mock (task 5).

## AI synthesis (`api/synthesis.py`, moderator only)

- `POST /moderator/rounds/{id}/synthesis[?force=true]` clusters the "what's missing" answers with Claude
  (`claude-opus-5-5`, effort `low`, JSON-schema output, server-side `fallbacks: "default"` on a refusal).
  Result cached per round + input hash; `GET /moderator/rounds/{id}` only reads the cache (never a paid call)
  and shows `missing_clusters` (with `response_ids` → `free_text`), `identifying_details`, `coordination_flags`,
  `synthesis_source` (`claude` / `fallback` / `none`) and `fallback_reason`.
- Credentials: `ANTHROPIC_API_KEY` (or an `ant auth login` profile). Without them, on API errors or a refusal,
  it falls back to keyword grouping labelled "no AI". `GT_AI=off` never calls the API.
- Safety: only response id + text are sent (no tokens/tiers/identities; synthetic data only); answers are wrapped
  as data and instructions inside them are ignored; output validated (unknown ids dropped, one cluster per answer);
  summaries must not contain identifying details; copy-paste/coordinated answers are flagged locally. Nothing is
  published from here — the moderator approves text in the publish flow.

## Comments on/off from OCHA 3W presence (`api/comments_policy.py`)

Team decision (7 Nov): with few organisations in the affected area, a comment is easy to trace
back and easy to steer, so comments are off there.

- `GET /rounds/{id}`, `/rounds/{id}/thread` and `GET /moderator/rounds/{id}` carry
  `comments: {enabled, n_orgs, min_orgs, areas, area_basis, reason, source}`.
- Affected area = provinces/states/oblasts named in the risk title, or a region ("eastern Chad",
  "Darfur"), else the whole country. `n_orgs` = distinct organisations there (one org in two areas counts once).
- `enabled` when `n_orgs >= COMMENTS_MIN_ORGS` (env, default 30). No 3W data for the country → off.
- Data: `api/data/presence_3w.json`, built from OCHA 3W/5W on HDX (CC BY; Chad Sep 2026, Sudan Jan–Jul
  2026, Ukraine Jan–Sep 2026). Rebuild: `uv run --with openpyxl python -m api.build_presence_3w <dir>`.
- Examples: R1043 eastern Chad 146 orgs → on · R1051 West Kordofan 17 → off · R0248 East Darfur 19 → off.
