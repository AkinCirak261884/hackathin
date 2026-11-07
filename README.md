# Ground Truth

**A short monthly check-in that lets ACAPS's trusted field experts test ACAPS risk analyses, forecast what happens next, and see how their judgement holds up, without exposing who said what.**

**Live demo: [groundtruth-acaps.vercel.app](https://groundtruth-acaps.vercel.app)** (demo data, works on a phone; use "Reset my answers (demo)" to start again)

Built at Hackathon for Good #8 (The Hague, 6–8 November 2026) for the [ACAPS Ground Truth challenge](docs/challenge-brief.md). All people in the demo are synthetic; the risks are real ACAPS Risk Radar data.

---

## Why

The people closest to a crisis often sense it shifting first, but that knowledge stays in informal chats and never reaches the analysis. ACAPS needs a way to tap a small, trusted panel (5–10 experts per country) that:

- takes minutes, not hours, so busy field staff actually answer;
- protects experts who cannot be seen sharing views;
- stops one loud voice or the group average from drowning out independent judgement;
- shows, over time, whose forecasts are worth listening to.

## What it does

**For experts (mobile-first web app, English and French)**

1. **Blind check-in (about 3 minutes).** On a live ACAPS risk (demo: R1043, cross-border insecurity in eastern Chad) the expert rates ACAPS's probability and impact as too low / about right / too high, flags triggers they are seeing, gives a probability for each trigger by the deadline, ranks priorities and notes what ACAPS is missing.
2. **Choose how you are shown.** Anonymous (default), pseudonymous or known to ACAPS, per answer.
3. **Reasons before numbers (Delphi step 2).** After submitting, the expert reads the panel's reasons *without* their numbers, then keeps their answers or updates once, saying what changed their mind. Only then do the group's numbers unlock. The blind answer is always kept and is the one that is scored, so copying the group cannot improve anyone's record.
4. **Group view.** Distribution of answers (one dot per expert, yours highlighted), agreement with ACAPS's rating, and peer comments with each commenter's track record.
5. **Track record.** "x of y correct", an accuracy score (Brier) compared with ACAPS's own rating or the panel's middle answer, a page per forecast, and a "super estimator" badge for experts who beat ACAPS. A practice round on a real, already-resolved risk lets new experts see scoring work on day one.
6. **Impact.** "How ACAPS used your input" shows when a point an expert made changed an analysis.

**For ACAPS and the public**

- Moderator side (API, in progress): answers before and after revision, "what's missing" themes with AI-assisted clustering; the publish flow is still mocked.
- Public page: aggregates only, never who said what, hidden below 3 responses.

## Does it work?

Lane A backtested on the Risk Radar export: across **99 resolved ACAPS risks**, ACAPS's own ratings turned into probabilities score a **Brier score of 0.213** (61% of risks materialised). That is the baseline the panel has to beat, and every expert's record is measured against it on the same questions. Details: `analysis/README.md`.

## Trust and anonymity

- **Invite-only.** Each expert gets a personal invite; rate-limited and revocable.
- **Identities kept apart.** Names live in a separate vault database; contributions only carry a token. Anonymous answers are linked only to a one-way hash of a secret generated on the expert's phone.
- **Secrets never in URLs.** Tokens travel in request headers; the server does not log IP addresses.
- **Minimum of 3.** No group view or public number is shown for fewer than 3 responses; no free text is published verbatim.
- **Witnesses are signposted, not collected.** People who have seen abuses are pointed to the ICC and eyeWitness rather than asked to report in the app.

## Run it

**Expert app (works on its own with demo data):**

```bash
cd web
npm install
npm run dev          # http://localhost:5173, also reachable from a phone on the same wifi
```

Use "Reset my answers (demo)" on the home page to take the check-in again.

**Personal invite links (live API):** each expert opens `https://groundtruth-acaps-live.vercel.app/#/?invite=<their invite>`, for example `inv_demo_02` … `inv_demo_08` for the synthetic panel. The invite sits after `#`, so it is never sent to the server; the app removes it from the address bar and remembers it in that browser.

**With the API (Lane B):**

```bash
uv run --with-requirements api/requirements.txt uvicorn api.main:app --reload   # http://localhost:8000/docs
cd web && VITE_API_URL=http://localhost:8000 npm run dev
```

**Data and scoring (Lane A, standard library only):**

```bash
python3 analysis/ingest.py
python3 -m unittest discover analysis
```

## How it is built

| Folder | What | Stack |
|---|---|---|
| `web/` | Expert app | React 18 + Vite, no UI framework, no third-party fonts or trackers |
| `api/` | Rounds, responses, aggregates, track record, trust layer | FastAPI + SQLite (separate vault DB) |
| `analysis/` | Ingest, question generation, synthetic panel, scoring, backtest | Python standard library |
| `contracts/` | JSON schemas shared by all three | JSON Schema |
| `fixtures/` | Demo data for every endpoint | generated by `fixtures/generate_fixtures.py` |
| `pitch/` | Pitch outline and demo script | |

## Status and next steps

Working: the full expert flow on demo data, track record, public page, EN/FR, API for rounds, responses and records, scoring and backtest. In progress: wiring the app to the API end to end, and publishing to the public page.
Next for a pilot: live risk list from the ACAPS API, Arabic (covers about a third of ACAPS risks, including the rest of the Chad panel), agreement by region, and comparing the panel against other sources where the questions line up.

## Challenge material

- [Challenge brief](docs/challenge-brief.md) · [Evaluation criteria](docs/evaluation-criteria.md) · [Data dictionary](docs/data-dictionary.md) · [Resources](docs/resources.md)
- [ACAPS Risk List](https://www.acaps.org/en/thematics/all-topics/risk-list) · [ACAPS API](https://api.acaps.org)

## License

MIT, see [LICENSE](LICENSE). ACAPS data is used under [ACAPS' terms of use](https://www.acaps.org/en/about/terms-of-use).
