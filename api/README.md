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
