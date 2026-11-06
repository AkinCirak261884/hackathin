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

- Each expert has an archetype: `sharp`, `well_calibrated`, `anchored` (on ACAPS), `alarmist`, `complacent`, `noisy`, `hedger`. Forecast logit = `anchor·logit(ACAPS) + skill·logit(truth) + bias + noise`, rounded to 5 points.
- Round 1: everyone answers the 4 R1043 questions; 6 write a "what's missing" text (written to form clusters: wet-season access, overcrowded sites, drones, mediation). Round 2: less stubborn experts move towards the group median (4 revisions).
- Writes `experts`, `rounds`, `contributions` to the DB, and committed JSON in `analysis/synthetic/`:
  - `experts.json`: public profiles + archetype (no names)
  - `vault.json`: synthetic names/emails, invite tokens, device secret for the anonymous expert, expected author token
  - `responses_R1043.json`: Lane B's `POST /rounds/{id}/responses` bodies; `_author_token` is what the API should derive (not sent)
- Anonymous tier: `author_token = "anon_" + sha256(device_secret)[:24]`.
