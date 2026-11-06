# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [x] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [x] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [x] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [x] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [ ] **Leaderboard.** Super-estimator ranking by mean Brier, **only experts with ≥ N resolved forecasts qualify** (N = 10 for the backtest), shown against ACAPS's 0.213. *Done when:* a table/chart is generated from the DB.
- [ ] **Short-horizon questions.** Question generator also emits 1–3-month trigger questions (e.g. "…before 31 January 2027?") so a track record builds during the ~2-month December pilot. *Done when:* R1043 has at least one question closing within the pilot.
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

**Lane C answer:**
> (write here)

## Latest update

### Lane A — update #4 — 17:27
Done: Brier scoring (`scoring.py`, final version counts) + backtest on 99 resolved risks (`backtest.py`) + calibration chart `analysis/charts/calibration.svg`. Real: ACAPS Brier 0.213 vs 0.239 base rate; High (70%) → 83% materialised. Synthetic experts 0.144–0.234 (simulated, pipeline demo only). Also aligned synthetic IDs/invites/tokens with B's seed.py + trust.py. 23 unittests pass.
Pushed: lane-a @ f9f35c0 | PR: not opened yet (no gh CLI) — https://github.com/AkinCirak261884/hackathin/compare/main...lane-a
How to see it: `python3 analysis/backtest.py` then open `analysis/charts/calibration.svg`
Requests to other lanes: →B: `scores` table + backtest rounds `RND-{risk}-BT` / questions `Q-{risk}-MAT` with outcomes can feed real `/me/track-record` (tokens = your psd_/anon_ format) · →C: chart + numbers for the data slide in `analysis/charts/`
Contract change proposed: none (still pending: short `trigger_id` `T####`, from #2)
Next: leaderboard (super estimators by Brier)
Blockers: none
