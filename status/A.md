# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [x] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [x] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [x] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [ ] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [ ] **Leaderboard.** Super-estimator ranking by Brier. *Done when:* a table/chart is generated from the DB.
- [ ] **Moderator dashboard (Streamlit).** Spread vs. ACAPS rating, disagreement, revision shifts, triggers observed. *Done when:* `streamlit run moderator/app.py` shows R1043.

## Latest update

### Lane A — update #3 — 17:21
Done: synthetic TCD panel — `analysis/synthetic.py`: 8 experts (all 3 tiers) with biases (sharp, calibrated, anchored, alarmist, complacent, noisy, hedger); simulated R1043 round: 8 v1 + 4 v2 revisions, 6 "what's missing" texts. Written to DB + committed JSON in `analysis/synthetic/`. 17 unittests pass.
Pushed: lane-a @ 1cdfed0 | PR: not opened yet (no gh CLI) — https://github.com/AkinCirak261884/hackathin/compare/main...lane-a
How to see it: `python3 analysis/ingest.py && python3 analysis/synthetic.py --out analysis/synthetic`
Requests to other lanes: →B: `analysis/synthetic/responses_R1043.json` = ready POST bodies for integration tests; `vault.json` = synthetic vault + invite tokens; tell me if your anon hash differs from `"anon_"+sha256(secret)[:24]` · →B: "what's missing" texts form 4 clusters for AI synthesis · →C: use these responses for the reveal screen dots
Contract change proposed: none (still pending: short `trigger_id` `T####`, from update #2)
Next: Brier scoring + backtest vs ACAPS baseline on resolved risks
Blockers: none
