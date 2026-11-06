# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [x] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [ ] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [ ] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [ ] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [ ] **Leaderboard.** Super-estimator ranking by Brier. *Done when:* a table/chart is generated from the DB.
- [ ] **Moderator dashboard (Streamlit).** Spread vs. ACAPS rating, disagreement, revision shifts, triggers observed. *Done when:* `streamlit run moderator/app.py` shows R1043.

## Latest update

### Lane A — update #1 — 17:17
Done: Risk Radar ingest — `analysis/ingest.py` parses triggers, builds SQLite `risks` + `triggers` (139 risks, 266 triggers; R1043 → T0618/T0619/T0620). 5 unittests pass.
Pushed: lane-a @ 2837150 | PR: not opened yet (no gh CLI) — https://github.com/AkinCirak261884/hackathin/compare/main...lane-a
How to see it: `python3 analysis/ingest.py` then `python3 -m unittest discover analysis`
Requests to other lanes: →B: ingest uses the BOARD.md schema exactly; if `api/` owns the DB, reuse `analysis/ingest.py` or tell me where the DB should live
Contract change proposed: none (note: only 35/266 triggers have an "objective"; questions fall back to title/description)
Next: question generator (R1043 → 3 trigger questions + 1 agree item)
Blockers: none
