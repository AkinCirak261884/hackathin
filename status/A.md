# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [x] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [x] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [x] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [x] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [x] **Leaderboard.** Super-estimator ranking by mean Brier, **only experts with ≥ N resolved forecasts qualify** (N = 10 for the backtest), shown against ACAPS's 0.213. *Done when:* a table/chart is generated from the DB.
- [x] **Short-horizon questions.** Question generator also emits 1–3-month trigger questions (e.g. "…before 31 January 2027?") so a track record builds during the ~2-month December pilot. *Done when:* R1043 has at least one question closing within the pilot.
- [ ] *(optional)* **Ground synthetic experts in real forecasters.** Tune archetype noise/bias to the Good Judgment Project data (Harvard Dataverse). *Done when:* README states the source and the fitted parameters.
- [ ] **Moderator dashboard (Streamlit).** Spread vs. ACAPS rating, disagreement, revision shifts, triggers observed. *Done when:* `streamlit run moderator/app.py` shows R1043.

## Lane A proposal: scoring approach (for voice OK)

**What's real and what's synthetic**
- **Real:** the Risk Radar export, 139 ACAPS risks with ratings and outcomes. That's exactly what the brief says to test scoring on "before any expert joins". ACAPS's live Risk List is also public (HDX + ACAPS API), so the demo can show current risks, not only the archive.
- **Not available, by design:** real expert forecasts. The brief says synthetic users only; real answers arrive with the December pilot.

**Approach**
1. **Test the algorithm on real outcomes, with ACAPS as the forecaster.** Ratings → % (Very Low 10 · Low 30 · Medium 50 · High 70 · Very High 90), Brier = (forecast − outcome)², outcome 1 = materialised. Expert score = mean Brier over their resolved questions; **leaderboard only after a minimum number of resolved forecasts**. Done: ACAPS 0.213 vs 0.239 for always guessing the 61% base rate (`analysis/charts/`).
2. **Synthetic experts forecast the same real risks.** Their answers are generated from the real outcome plus noise and bias (bold, cautious, anchored on ACAPS…). This tests whether scoring can tell a skilled forecaster from a poor one. It is **not** evidence that experts beat ACAPS; say so on the slide.
3. **Make the synthetic panel more plausible** by tuning its noise to real human forecasters: the Good Judgment Project data (2011–2015 ACE tournament, millions of forecasts) is public on Harvard Dataverse, dataverse.harvard.edu/dataverse/gjp. Pitch line if we do it: "our synthetic experts are calibrated on how real forecasters behave".

**Problem to fix now: the pilot is shorter than the horizon.** The pilot is ~2 months and questions are 6 months, so nothing resolves during the pilot and ACAPS sees no scores. Fix: add **1–3-month trigger questions** ("Will there be an attack on X before 31 January 2027?") that resolve inside the pilot, so a track record starts building immediately. Good pitch point; check with Alex.

## Questions for other lanes

### A → C: Twitter/Reddit-style feed pivot? — asked 2026-11-06 evening
**Please answer below in this file (under "Lane C answer"), commit with prefix `[C]` and push to `main`.** Only edit the answer block.

**Proposal** (from team discussion): replace the survey-style pulse with a social feed, own brand "Ground Truth" (no Twitter name/logo/bird), dark "lights out" theme, single column, bottom tabs: Feed · Forecasts · Notifications · Profile.
- ACAPS posts a risk (R1043: probability, impact, triggers) as a thread.
- Expert replies through one composer: probability slider + "too high / agree / too low" on the ACAPS rating + optional ≤280-char "what's missing".
- **Hidden until you answer** (BeReal / Metaculus style): others' replies and the distribution unlock only after your own submit. Then replies show as pseudonym or "Anonymous expert", with "I see it the same way / differently" reactions.
- Forecasts look like polls with a slider; on resolution the post shows ✓ / ✗ and your Brier score.
- Profile: track record + "super estimator" badge. Moderator pins summaries ("how your input shaped our analysis").
- Access: invite link → pick pseudonym + tier → in the feed. No password.

**What we'd like your opinion on:**
1. Is this worth the pivot tonight, given your 6 screens already exist? How much of `web/` survives (TierPicker, Reveal, TrackRecord)?
2. Showing *individual* replies to peers after reveal: OK with the anonymity rules? With 5–10 experts, writing style or timing could identify an "Anonymous expert". Should the min-3 rule also apply to showing individual replies, and should free text be shown to peers verbatim or only moderator-approved?
3. Brief says "should not focus on time spent in the app". How do we keep a feed from feeling like engagement bait (no infinite scroll, no likes count, no streaks)?
4. What do you need from A and B? Lane A's guess: B adds "same / differently" reactions + the reveal-after-submit gate (already exists for `/aggregate`); A adds the ✓/✗ + Brier per post (already in `scores`) and the badge rule.
5. Should we check "hidden until answered" with Alex first?
6. Also see "Lane A proposal: scoring approach" above. Anything there that changes your screens (✓/✗ + Brier per resolved post, badge only after N resolved forecasts, short 1–3-month questions)?

**Lane C answer:** (2026-11-06, Lane C)
> **TL;DR: no full pivot tonight. Do a "feed skin" over what exists, and keep peers seeing aggregates, not individual replies.**
>
> 1. **Pivot?** Not a rewrite. ~80% of `web/` already maps onto the feed: Home = feed of ACAPS risk posts, Pulse = composer, Reveal = the thread after you answer, Profile = track record (✓/✗ + Brier + "4 of 5 correct" already built), TierPicker/charts/i18n/api.js unchanged. I can restyle Home + Reveal as posts/threads in ~1–2h. Dark mode already follows the phone setting. One caution: keep our own look, not a Twitter/X clone (brief + jury).
> 2. **Individual replies to peers: no.** With 5–10 experts, style and timing re-identify people, and one leaked quote can endanger someone in eastern Chad. Proposal: peers see (a) the distribution (dots, no names), (b) moderator-approved or AI-clustered *themes* of the free text, never verbatim, and (c) only once n ≥ 3. Unlock everything for everyone at round close or at n ≥ 3, never per reply in real time, and shuffle and drop timestamps so timing can't leak. Pseudonymous experts may opt in to showing a short quote under their pseudonym; anonymous never.
> 3. **Not engagement bait:** a finite feed (1–3 open rounds, then "You're all caught up"), no like counts, no streaks, no infinite scroll. Notifications only for: new round, results unlocked, your forecast resolved. Retention comes from impact ("your input changed the R1043 rationale") and the track record, both already on Profile.
> 4. **From B:** a peer-safe thread endpoint, e.g. `GET /rounds/{id}/thread` = aggregate + approved themes (no authors, n ≥ 3). Skip "same/differently" reactions unless it's just aggregate counts. **Alignment needed:** B uses `RND-R1043-1`, header auth (`X-Invite-Token`) and server-side anon hashing, while `contracts/` (PR #1) uses `RD-R1043-1`, `?token=` and a client-side hash. Let's pick one on voice; I'll switch `web/src/api.js` to B's version. Note: sending `X-Device-Secret` to the server weakens "server can never link anonymous answers"; the client-side hash keeps that promise. **From A:** badge rule (e.g. ≥5 resolved and Brier better than the ACAPS baseline), and per-question ✓/✗ + Brier in `/me/track-record` (my Profile already renders that shape).
> 5. **Alex:** yes, but frame it right. "Hidden until you answer" *is* Delphi round 1, so he'll likely say yes. The real questions for him: may peers ever see each other's free text, and is a feed look OK for ACAPS's brand?
> 6. **Scoring proposal:** 👍 to all three. 1–3-month questions are great for the pilot; Profile already shows deadlines, so I'll show short-horizon questions first. "Badge only after N resolved" fits the "4 of 5 correct" hero; below N I'll show "3 more forecasts until your score counts". Please say the synthetic-expert caveat on the data slide, as you wrote.

## Smoke test: R1043 demo path (19:35, 6 Nov)

**Setup:** `main` has no `api/` or `web/` yet, so I merged `main` + `origin/lane-b` (70317cd) + `origin/lane-c` (965ecc9) **locally only** (clean merge, nothing pushed). Lane B's 86 tests pass on the combined code. API on a fresh scratch DB (`GT_DB` / `GT_VAULT_DB`, never Lane B's live one), web app with `VITE_API_URL=http://localhost:8000`. Driven with the 8 synthetic experts' `responses_R1043.json`. Chrome extension was disconnected, so web screens were checked by replaying `web/src/api.js`'s real-API requests, not by clicking.

| # | Step | API (Lane B) | Web app (Lane C) | Exact error / mismatch | Owner |
|---|---|---|---|---|---|
| 0 | Run demo from `main` | broken | broken | `main` has no `api/` or `web/`: lane-b and lane-c (PR #1) not merged | B, C |
| 1 | Invite | works | broken | API: unknown invite → 401, `inv_demo_01..08` OK. Web sends `invite_token: "inv_demo"` → 401 `unknown invite` | C |
| 2 | Choose tier | works | broken | Web anonymous sends `anon_token`, no `device_secret` → 422 `anonymous tier needs a device_secret of at least 16 chars`. Option (c) (hash on phone, server HMAC) not implemented on either side | B + C |
| 3 | Round 1 (8 experts) | works | broken | Web: `GET /rounds/RD-R1043-1` → 404 (API uses `RND-R1043-1`); `Q-R1043-RATING`, `Q-TCD-TOP3` → 422 `questions not in this round`; `reasoning_basis: null` → 422 `Input should be a valid list`; round has top-level `triggers` but web reads `risk.triggers`; API questions have `kind: "agree"` (web expects `rating`), no `title`/`title_fr`/`text_fr`; `rating_probability`, `rating_impact`, `seeing`, `ranking` have no DB columns | C (IDs, body), B (store rating/ranking) |
| 4 | Group view after own answer | works | broken | API: 403 before own answer, per-question `suppressed` at n=2, n=8 gives median/p25/p75/sorted dots, no tokens. **Missing:** weighted `aggregate` from `analysis/aggregate.py` not added. Web: `/rounds/{id}/aggregate?token=` → 422 `missing header x-invite-token` | B (aggregate), C (headers) |
| 5 | Revise once | works | not tested | v2 → 201, second v2 → 409 `already revised once` | — |
| 6 | Moderator view | broken | — | `GET /moderator/rounds/RND-R1043-1` returns the **mock** (`n_responses: 6`, `anon_3f9a…`, fake `response_ids`, `synthesis_source: "mock"`), not the real round. `disagreement()` not integrated; themes are mock | B |
| 7 | Profile: track record + leaderboard | works (headers) | broken | Fresh DB has only R1043 → empty history, empty leaderboard: **fixed (A)**, `analysis/demo_history.py::seed_history(con)`, verified on the live API (Birch 73 resolved + badge, 8-entry leaderboard). Web: `/me/track-record?token=` → 422 missing header; `/leaderboard?...&token=` ignored, so `is_you` never set | A (fixed), B (call it in seed), C (headers) |
| 8 | Publish public summary | broken | — | `POST /moderator/rounds/{id}/publish` → `published: true`, but `/public/summaries` still only shows mock `RND-R1043-0` | B |
| 9 | No token in any URL | OK | broken | API takes tokens only in headers. Web puts tokens in 3 URLs: aggregate, track-record, leaderboard (`?token=`) | C |
| 10 | Public summary: no tokens, pseudonyms, exact quotes | OK (on the mock) | — | None found; no "what's missing" text appears verbatim. Recheck once publish works | B |
| 11 | Anonymous never by pseudonym | OK | — | "Sparrow" appears nowhere; leaderboard says "Anonymous expert"; peer outputs carry no tokens. Moderator mock lists `anon_…` tokens (no name); recheck when real | B |
| 12 | Docs | minor | — | `api/README.md` says synthetic invites are `inv_tcd_01…`; seeded ones are `inv_demo_01…` | B |

## Latest update

### Lane A — update #10 — 19:35
Done: end-to-end smoke test of the R1043 demo path (table above). API path works for invite → round 1 → group view (403 / n≥3) → revise; moderator view and publish are still mocks; web app can't talk to the real API yet (IDs, body, `?token=`). Fixed the Lane A item: `analysis/demo_history.py::seed_history(con)` fills a fresh DB with all risks + resolved synthetic history, so profile/badge/leaderboard work in the demo. 55 unittests pass.
Pushed: lane-a @ d46ed71 (code not yet merged into main)
How to see it: table above · `python3 analysis/demo_history.py --db <db>`
Requests to other lanes: →B: (0) merge lane-b into main; (6) real `/moderator/rounds/{id}` with `aggregate.disagreement()` + real themes; (8) publish must write to `/public/summaries`; (4) add `aggregate.aggregate()["aggregate"]` to `/aggregate` + `/thread`; (7) call `demo_history.seed_history(con)` at the end of `api/seed.py`; (3) store `rating_probability`, `rating_impact`, `ranking` (+ add `Q-R1043-RATING`/`Q-TCD-TOP3` or agree with C to drop them); (2) option (c) device-hashed anon token; (12) README invites · →C: (0) merge PR #1; (1) real invite from the link, not `inv_demo`; (3) use `RND-R1043-1`, read top-level `triggers`, send `reasoning_basis: []` not `null`, `kind: "agree"`; (4)(7)(9) send `X-Invite-Token` / `X-Device-Secret` headers, drop all `?token=`; (2) anonymous: send `device_secret` until (c) is agreed
Contract change proposed: none new
Next: stop, as asked
Blockers: none for A; demo from main blocked on (0)
