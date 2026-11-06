# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [x] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [x] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [ ] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [ ] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [ ] **Leaderboard.** Super-estimator ranking by Brier. *Done when:* a table/chart is generated from the DB.
- [ ] **Moderator dashboard (Streamlit).** Spread vs. ACAPS rating, disagreement, revision shifts, triggers observed. *Done when:* `streamlit run moderator/app.py` shows R1043.

## Latest update

### Lane A — update #2 — 17:19
Done: question generator — `analysis/questions.py` writes `questions` (R1043 → Q-R1043-AGREE + T0618/T0619/T0620, closes 2027-05-06; all 28 Active risks → 104 questions) + JSON export in B's mock shape. 10 unittests pass.
Pushed: lane-a @ b96b323 | PR: not opened yet (no gh CLI) — https://github.com/AkinCirak261884/hackathin/compare/main...lane-a
How to see it: `python3 analysis/ingest.py && python3 analysis/questions.py --risk R1043 --opened 2026-11-06 --json analysis/out/questions_R1043.json`
Requests to other lanes: →B: yes to `Q-{risk}-{T####|AGREE}`. My `trigger_id` is short `T0618` (globally unique), your mocks use `R1043 - T0618` — can we agree on short? →B/C: `analysis/out/questions_R1043.json` can replace `_questions.json` at freeze
Contract change proposed: `trigger_id` = short form `T####`; optional `resolves_yes_if` field on questions (JSON only, not a DB column)
Next: synthetic experts (8, with biases) + simulated answers
Blockers: none
