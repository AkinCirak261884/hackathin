# Lane A — data & scoring

Folders: `analysis/`, `moderator/`. Don't edit `contracts/`, `api/`, `web/`.

## Tasks

- [ ] **Trigger parser + ingest.** Parse the `triggers` field of `data/risk-radar-export.csv`; load `risks` and `triggers` for R1043 and all of Chad. *Done when:* a script builds the SQLite DB and R1043 shows its 3 triggers.
- [ ] **Question generator.** Turn each trigger's objective into a yes/no question that closes 6 months after the round opens. *Done when:* R1043 yields 3 trigger questions + 1 agree item, written to `questions`.
- [ ] **Synthetic experts.** Generate 8 experts with different biases (well calibrated, alarmist, anchored on ACAPS, noisy). *Done when:* experts and their simulated answers are in the DB and in `fixtures/`.
- [ ] **Scoring + backtest.** Brier scoring; backtest synthetic experts vs. the ACAPS baseline on resolved risks. *Done when:* tests pass and a calibration chart is saved.
- [ ] **Leaderboard.** Super-estimator ranking by Brier. *Done when:* a table/chart is generated from the DB.
- [ ] **Moderator dashboard (Streamlit).** Spread vs. ACAPS rating, disagreement, revision shifts, triggers observed. *Done when:* `streamlit run moderator/app.py` shows R1043.

## Latest update

### Lane A — update #0 — --:--
Done: nothing yet
Pushed: none | PR: none
How to see it: —
Requests to other lanes: none
Contract change proposed: none
Next: trigger parser + ingest
Blockers: none
