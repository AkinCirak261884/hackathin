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

## Smoke test: R1043 demo path (rerun 19:41, 6 Nov, on lane-b @ 366e6b6 + lane-c @ 3cc33b0)

**Setup:** `main` still has no `api/` or `web/`, so I merged `main` + `origin/lane-b` + `origin/lane-c` **locally only** (clean merge, nothing pushed, no files outside `analysis/` changed). Lane B's 97 tests pass on the combined code. API on a fresh scratch DB (`GT_DB` / `GT_VAULT_DB`, never Lane B's live one); demo history added with `python3 analysis/demo_history.py --demo` (refuses without `--demo`). Driven with the 8 synthetic experts. Chrome extension was disconnected, so web screens were checked by replaying `web/src/api.js`'s real-API requests and diffing Lane C's fixtures (what the screens read) against the API's real responses.

### Demo path

| # | Step | Result | Detail | Owner |
|---|---|---|---|---|
| 0 | Run from `main` | broken | `main` has no `api/` or `web/`: lane-b and lane-c (PR #1) not merged | B, C |
| 1 | Invite | works | unknown invite → 401; `inv_demo_01..08` accepted | — |
| 2 | Choose tier | works | tier per answer; anonymous token derived server-side from `device_secret` | — |
| 3 | Round 1 (8 experts) | works | v1 → 201, `next: "wait for the moderator to reveal"` | — |
| 4 | Group view after own answer | works | 403 before own answer; `locked` in blind; after moderator `advance` → `view: "round_1"`, n=8, median/p25/p75/sorted dots; no tokens. **Missing:** weighted `aggregate` from `analysis/aggregate.py` | B |
| 5 | Revise once | works | v2 in reveal → 201; second v2 → 409 `already revised once` | — |
| 6 | Moderator view | partly | Real now (n, round-1 vs final, revision shifts, free text). **Missing:** `disagreement()` not integrated; `missing_clusters` still the mock (AI synthesis is B's next task). **Privacy:** pseudonymous contributors appear as `psd_EXP-TCD-0x`, i.e. the expert ID, which the vault maps to a name, so ACAPS could identify "pseudonymous" experts | B |
| 7 | Profile: track record + leaderboard | works | Empty on a fresh DB → **fixed (A)**: `analysis/demo_history.py` (demo-only guards; also fixed a positional INSERT that broke on B's new 6-column `rounds`). Via the live API: Birch 73 resolved, badge, `record` 56/70; leaderboard 8 entries | A (fixed); B decides whether to call it |
| 8 | Publish public summary | broken | `POST …/publish` → `published: true`, but `/public/summaries` still only shows mock `RND-R1043-0` | B |
| 9 | No token in any URL | API OK, web broken | API: headers only. Web: `?token=` in `/rounds/{id}/aggregate` and `/me/track-record` (`web/src/api.js` l.96, l.100) | C |
| 10 | Public summary: no tokens, pseudonyms, exact quotes | OK on the mock | none found; recheck once publish writes real summaries | B |
| 11 | Anonymous never by pseudonym | OK | "Sparrow" appears nowhere (peer, public, moderator, leaderboard: "Anonymous expert") | — |
| 12 | Docs | minor | `api/README.md` says synthetic invites `inv_tcd_01…`; seeded are `inv_demo_01…` | B |

### Web ↔ API mismatches (web = what `web/src` and `fixtures/` expect; API = Lane B's real response)

| # | Endpoint | Mismatch | Owner |
|---|---|---|---|
| W1 | all | Demo IDs: web uses round `RD-R1043-1`, token `E01`, invite `inv_demo`; API has `RND-R1043-1`, `psd_EXP-TCD-01`, `inv_demo_01..08` → 404 / 401 | C |
| W2 | `GET /rounds/open` | web expects a top-level array of `{round_id, risk_id, title, stage, closes_at, est_minutes, n_questions, answered}`; API returns `{panel, rounds: [{…, risk_title, opened_at, you_submitted}]}`: `title`↔`risk_title`, `answered`↔`you_submitted`, no `closes_at` / `est_minutes` | C (adapt), B (`closes_at`) |
| W3 | `GET /rounds/{id}` | web reads `risk.triggers[]` (+ `description`, `objective`), `risk.title`, `rationale_short`, `iso`, `trend`, `expected_exposure`, `priority_needs`, round `closes_at`; API has top-level `triggers` (`trigger_id, title, completion_rate` only), `risk_title`, and `risk` = `{risk_id, country, probability, impact, level, status}` | B (risk detail), C (top-level `triggers`) |
| W4 | `GET /rounds/{id}` questions | web expects `kind: "rating"` `Q-R1043-RATING` and `kind: "ranking"` `Q-TCD-TOP3` (with `options`), plus `acaps_baseline`; API has `kind: "agree"` `Q-R1043-AGREE`, no ranking question, no `acaps_baseline` → POST 422 `questions not in this round` | B + C (decide) |
| W5 | `POST /rounds/{id}/responses` | answer fields `rating_probability`, `rating_impact`, `seeing`, `ranking`, `ranking_other` are dropped (API `Answer` = `prob`, `agree` only; no DB columns) | B |
| W6 | `POST …/responses` | `reasoning_basis: null` → 422 `Input should be a valid list` (send `[]`) | C |
| W7 | `POST …/responses` | anonymous: web sends `anon_token`, no `device_secret` → 422 `needs a device_secret of at least 16 chars`. Option (c) (hash on phone, server HMAC, no invite→anon link) not implemented either side | B + C |
| W8 | `POST …/responses` reply | web fixture has `contribution_ids`; API returns `stored, author_token, can_revise, aggregate_unlocked, next` | C |
| W9 | `GET /rounds/{id}/aggregate` | auth: web `?token=` → 422 `missing header x-invite-token` | C |
| W10 | `GET /rounds/{id}/aggregate` | shape: web expects `{n_responses, rating: {probability/impact: {too_low, agree, too_high}, you}, forecasts: [{question_id, values, median, p25, p75, you, n, acaps_baseline, seeing_count}], ranking, comments}`; API gives `{locked, view, questions: [{median, p25, p75, dots, agree_share, suppressed, n}], triggers_observed: [{trigger_id, share}], your_answers}`; web doesn't handle `locked` / `view` | C (adapt), B (3-way rating shares) |
| W11 | `GET /rounds/{id}/aggregate` | **Policy conflict:** web shows peers `comments[]` = other experts' `reasoning_text` verbatim under pseudonym / "Anonymous expert" with their record and forecasts; API keeps reasoning moderator-only. Contradicts Lane C's own earlier answer here ("never verbatim, style can re-identify in 5–10") | B + C (team decision) |
| W12 | `GET /me/track-record` | auth: web `?token=` → 422 missing header | C |
| W13 | `GET /me/track-record` | web reads `history[].risk_id` and the correct/resolved record: **fixed (A)**, `history[].risk_id`, `history[].verdict`, `record: {correct, resolved, no_call}` (same 50% rule as `web/src/stats.js`). `impact[] {risk_id, date, note}` still missing | A (fixed), B (`impact`) |
| W14 | `GET /public/summaries` | web expects an array of `{round_id, risk_id, risk_title, published_at, headline, summary_text, n_responses, rating_agreement, forecasts: [{question_id, text, median, n}]}`; API returns `{summaries: [{…, n, agree_share, questions: [{median, p25, p75}], approved_text}]}` | B + C |
| W15 | `POST /moderator/rounds/{id}/publish` | contract body `{summary_text, headline}`; API `PublishIn` = `{approved_text}` | B + C |
| W16 | `GET /leaderboard` | none: web removed the leaderboard (team decision); API and `analysis/leaderboard.py` still provide it | — |

## Latest update

### Lane A — update #11 — 19:41
Done: reran the smoke test on lane-b @ 366e6b6 + lane-c @ 3cc33b0 and listed every web↔API mismatch with an owner (tables above). Lane A fixes only: `demo_history.py` is demo-only (refuses without `--demo` / `demo=True`, refuses DBs with any non-synthetic expert or author token, all-or-nothing) and uses named columns (Lane B's `rounds` now has 6); `track_record()` adds `record {correct, resolved, no_call}`, `history[].verdict`, `history[].risk_id` (Lane C's request). Nothing outside `analysis/` changed. 60 unittests pass.
Pushed: lane-a (code not merged into main)
How to see it: tables above · `python3 analysis/demo_history.py --demo --db <demo db>`
Requests to other lanes: →B: #0 merge lane-b; #4 add `aggregate.aggregate()["aggregate"]`; #6 integrate `aggregate.disagreement()`, real themes, and don't show pseudonymous experts' `psd_<expert_id>` to the moderator; #8 publish must write `/public/summaries`; W3 risk detail + round `closes_at`; W5 store `rating_probability` / `rating_impact` / `seeing` / `ranking`; W13 `impact[]`; W14/W15 public summary + publish shape; #12 README; optional: call `demo_history.seed_history(con, demo=True)` in the demo seed (your call) · →C: #0 merge PR #1; W1 use `RND-R1043-1` / real invite / API tokens; W2, W3, W8, W10 adapt to the API shapes; W6 `reasoning_basis: []`; W9/W12 headers, no `?token=`; W13 `record` is now in the track record · →B+C: W4 rating/ranking questions, W7 anonymous token (option c), W11 peer comments: decide on voice
Contract change proposed: track record `record`, `history[].verdict`, `history[].risk_id`
Next: stop, as asked
Blockers: demo from main blocked on #0
