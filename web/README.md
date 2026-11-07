# web/: expert app (Lane C)

React 18 + Vite, mobile-first. Reads mocks from `../fixtures` until Lane B's API is up.

```bash
cd web
npm install
npm run dev          # http://localhost:5173 (and your LAN IP for testing on a phone)
npm run build
```

Use the real API: `cp .env.example .env` and set `VITE_API_URL=http://localhost:8000`. All data access goes through `src/api.js`.

Routes: `#/` open rounds · `#/pulse/RD-R1043-1` pulse flow · `#/reveal/RD-R1043-1` group view · `#/me` track record · `#/public` public summary · `#/signpost` witness signposting.

Notes:
- The anonymous tier uses `crypto.subtle` for the token hash, which needs `localhost` or HTTPS. On a phone over a plain-HTTP LAN IP it won't work yet; use a tunnel or test it on desktop.
- Strings live in `src/i18n.jsx` (EN/FR). Fixture text uses `text` / `text_fr`.
