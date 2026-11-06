# api/ — Lane B (backend & trust)

```
uv run --with-requirements api/requirements.txt uvicorn api.main:app --reload   # http://localhost:8000/docs
uv run --with-requirements api/requirements.txt python -m pytest api/tests -q
```

Stub stage: all endpoints from BOARD.md serve `api/mocks/*.json`. Identities and invites live in a
separate SQLite file (`api/var/vault.db`), so the contributions DB holds no names or emails.
