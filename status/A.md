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

## Latest update

### Lane A — update #9 — 19:29
Done: `analysis/aggregate.py`. Lane B keeps owning the group view gate/auth (`api/rounds.py::aggregate`), so these are plain functions to call. Weighted group forecast (log-odds, track-record weights shrunk to group average, new experts = average, ×1.5 extremizing), out-of-sample only. Backtest (synthetic, Risk ID order): median 0.181 → weighted 0.171 → weighted+extremized 0.157 (ACAPS 0.215). Moderator `disagreement()`: IQR/spread, split flag, distance from ACAPS, rating shares. 54 unittests pass (n<3 → None, no tokens/names, own outcome never moves own aggregate).
Pushed: lane-a + main @ fc555e6
How to see it: `python3 analysis/backtest.py` (aggregate table) · `backtest_summary.json` → `aggregate_backtest`
Requests to other lanes: →B: call `aggregate.aggregate(con, question_id)` → `None` if n<3, else `{question_id, n, min_n, median, weighted, weighted_extremized, extremize_factor, aggregate, n_weighted_by_track_record, values: [shuffled probs]}`; add `aggregate` (the value to show) next to your median in `/rounds/{id}/aggregate` and `/thread`. Call `aggregate.disagreement(con, question_id)` for `/moderator/rounds/{id}` → `None` if n<3, else `{question_id, min_n, rating_shares, n, iqr: [q1, q3], spread, split, split_at, aggregate, acaps_prob, aggregate_minus_acaps, vs_acaps: "close"|"higher"|"lower"}`; `rating_shares` = `{probability: {too_low, agree, too_high}, impact: {…}}` if you store `rating_probability` / `rating_impact`, else `{overall: {agree, disagree}}` · →C: show `aggregate` as the group's forecast (median stays available); `values` are unnamed and shuffled, so sort them for the dot plot
Contract change proposed: group forecast shown = `aggregate` (weighted, ×1.5 extremized) instead of median; store Lane C's `rating_probability` / `rating_impact` so moderator shares are 3-way
Next: (open) moderator dashboard (Streamlit) or GJP-calibrated synthetic experts
Blockers: none
