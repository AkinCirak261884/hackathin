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
  counts); dots sorted; free text never included.
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
