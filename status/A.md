# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [x] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [x] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [x] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [x] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [ ] **Leaderboard.** Super-estimator ranking by Brier. *Done when:* a table/chart is generated from the DB.
- [ ] **Moderator dashboard (Streamlit).** Spread vs. ACAPS rating, disagreement, revision shifts, triggers observed. *Done when:* `streamlit run moderator/app.py` shows R1043.

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
