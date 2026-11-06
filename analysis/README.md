# analysis/ — Lane A (data & scoring)

Standard library only (Python 3.10+), no extra installs.

```bash
python3 analysis/ingest.py               # builds analysis/out/groundtruth.db (git-ignored)
python3 -m unittest discover analysis    # tests
```

## ingest.py

Loads `data/risk-radar-export.csv` into SQLite with the `risks` and `triggers` tables from `BOARD.md`: all 139 risks and 266 triggers.

- `trigger_id` is the short ID (`T0618`); `risk_id` links back to `risks`.
- `completion_rate` is an integer percent, or NULL when not set.
- `objective` is the "Quantitative objective to meet 100%" text with the leading "Yes." removed. **Only 35 of 266 triggers have one** (222 are empty, 9 say "No"), so the question generator must fall back to the trigger title/description.
- Chad: R1043 (3 triggers) and R1066 are Active; R0233 has no status.

## questions.py

Builds the `questions` table: per risk, one agree item `Q-{risk}-AGREE` plus one yes/no forecast per trigger `Q-{risk}-{T####}`, closing 6 months after the round opens.

```bash
python3 analysis/questions.py --opened 2026-11-06                    # all 28 Active risks → 104 questions
python3 analysis/questions.py --risk R1043 --opened 2026-11-06 --json analysis/out/questions_R1043.json
```

- Objectives in the form "100% completion would be reached if X" become "Will X, by 6 May 2027?" (R1043, R1042).
- Everything else falls back to `Will this trigger fully materialise in {country} by {date}: "{title}"?`, with the objective or description as `resolves_yes_if` (JSON export only; not a DB column).
- The JSON export matches the shape of `api/mocks/_questions.json` (`question_id, trigger_id, kind, text, closes_at`) plus `risk_id` and `resolves_yes_if`.

## synthetic.py

Invented Chad (TCD) panel of 8 experts and a simulated round on R1043. **All people are synthetic.**

```bash
python3 analysis/synthetic.py --out analysis/synthetic
```

- Each expert has an archetype: `sharp`, `well_calibrated`, `anchored` (on ACAPS), `alarmist`, `complacent`, `noisy`, `hedger`. Only `sharp` sees more than ACAPS. Forecast logit = `anchor·logit(ACAPS) + skill·logit(truth) + bias + noise`, rounded to 5 points.
- Round 1: everyone answers the 4 R1043 questions; 6 write a "what's missing" text (written to form clusters: wet-season access, overcrowded sites, drones, mediation). Round 2: less stubborn experts move towards the group median (4 revisions).
- Writes `experts`, `rounds`, `contributions` to the DB, and committed JSON in `analysis/synthetic/`:
  - `experts.json`: public profiles + archetype (no names)
  - `vault.json`: synthetic names/emails, invite tokens, device secret for the anonymous expert, expected author token
  - `responses_R1043.json`: Lane B's `POST /rounds/{id}/responses` bodies; `_author_token` is what the API should derive (not sent)
- IDs, invites (`inv_demo_01`…) and tokens match Lane B's `api/seed.py` / `api/trust.py`: `psd_{expert_id}`, anonymous `anon_` + sha256("groundtruth-anon-v1:" + secret)[:32].

## scoring.py + backtest.py

```bash
python3 analysis/backtest.py   # rebuilds analysis/backtest.db (git-ignored), writes analysis/charts/*
```

- `scoring.py`: Brier score `(p − outcome)²`, using each author's **final** answer (v2 if revised). `score_db()` fills the `scores` table; `calibration()` bins forecasts into 5 equal bins.
- `backtest.py`: for the 99 resolved risks that have a probability rating (104 resolved, 5 unrated), adds a closed round `RND-{risk}-BT` with one question `Q-{risk}-MAT` ("Will this risk materialise?", real outcome) and simulated answers from the 8 synthetic experts (~75% participation).
- **It only ever writes `analysis/backtest.db`** and refuses a path inside `api/var/`.
- Outputs in `analysis/charts/`: `calibration.svg`, `backtest_summary.json`, `leaderboard.json`, `track_record_example.json`. None of them contain invite codes, device secrets or author tokens, except the track-record example, which contains only its owner's own token, as `/me/track-record` would.

### ACAPS probability → number

ACAPS's 2019 risk methodology ([technical brief, p. 11](https://www.acaps.org/fileadmin/Dataset/Methodology_files/acaps_technical_brief_introduction_to_risk_analysis_methodology_may_2019.pdf)) puts probability on a five-point scale using "Medow and Lucey's unequal ranges": Very low < 10%, Low 10–33%, Moderate 34–66%, High 67–90%, Very high > 90%. (The table itself is a graphic in the PDF; the bands are Medow & Lucey's published ranges. The export says "Medium" for Moderate.)

| Label | **Midpoint (app uses this)** | Edge (old, from BOARD.md) |
|---|---|---|
| Very Low | 5% | 10% |
| Low | 22% | 30% |
| Medium | 50% | 50% |
| High | 78% | 70% |
| Very High | 95% | 90% |
| **ACAPS Brier, 99 resolved risks** | **0.2133** | 0.2128 |

`scoring.APP_MAPPING = "midpoint"` drives the app's ACAPS baseline, the leaderboard, the badge and the synthetic experts' anchor. Both give almost the same Brier score: midpoint fits High-rated risks better (says 78%, 83% materialised) and Low-rated ones worse (says 22%, 43% materialised).

### Results (seeded, reproducible)

| Forecaster | Brier ↓ |
|---|---|
| Anonymous expert / Birch (sharp) ★ | 0.143 / 0.149 |
| **ACAPS rating (real outcomes)** | **0.213** |
| Kestrel (calibrated, no info beyond ACAPS) | 0.217 |
| Osprey (alarmist) | 0.220 |
| Alder (noisy, often misreads signals) | 0.229 |
| Linden (anchored on ACAPS) | 0.235 |
| Wren (hedger) / Heron (complacent) | 0.246 / 0.260 |
| Always the 61% base rate | 0.239 |

★ = super-estimator badge. Only the two "sharp" archetypes are given more information than ACAPS, so only they earn it (2 of 8).

**Real finding:** ACAPS's own ratings beat the base rate and are well calibrated in the middle: risks rated Medium materialised 48% of the time, High 83%, Very High 88%. Low-rated risks materialised more often than rated (43%, n=14).

**Also real:** ACAPS's extreme ratings are overconfident. Very Low risks materialised 33% of the time (rated 5%) and Very High ones 88% (rated 95%), so any forecaster who pulls those towards 50% scores better than ACAPS, even with no extra knowledge. While tuning the synthetic panel, random noise around ACAPS's rating alone was enough to "beat" it. Worth raising with Alex: it may argue for the edge mapping at the extremes, or for ACAPS hedging Very Low/Very High.

**Not a finding:** the experts' scores. Their "knowledge" is simulated, so the table only shows the pipeline can tell a sharp forecaster from a biased one. Say this on the slide.

## leaderboard.py

Per-question track record and the super-estimator leaderboard. Works on any DB with the BOARD.md tables (Lane B's or `analysis/backtest.db`).

```python
from leaderboard import track_record, leaderboard
track_record(con, author_token)          # → GET /me/track-record (served only to its owner): resolved "history" + unresolved "pending"
leaderboard(con, viewer_token=None)      # → peer-visible board: display names, no tokens
```

- **`pending`:** the author's final answers on unresolved questions, soonest deadline first, in Lane C's fixture shape (`question_id, title, title_fr, text, text_fr, your_prob, closes_at, submitted_at`; French fields are `null` until questions carry translations).
- **Ranked only after 5 resolved forecasts** (`MIN_RESOLVED`); below that, `forecasts_until_counted` says how many more are needed.
- **Rank by shrunk mean Brier:** `(n·mean + 5·group_mean) / (n + 5)` (`SHRINK_K = 5`), so a few lucky calls can't top the board.
- **Super estimator** = ≥ 5 resolved forecasts **and** mean Brier lower than ACAPS's mean Brier on exactly the same questions (paired). ACAPS's forecast for a question is its rating of that question's risk.
- **Names:** `psd_*` tokens show the pseudonym from `experts`; `anon_*` tokens show "Anonymous expert". Tokens listed in an optional `leaderboard_opt_out(author_token)` table are left off the board but still get their own track record.
- **Backtest:** 2 of 8 synthetic experts earn the badge (the two "sharp" ones, the only ones given information beyond ACAPS).
