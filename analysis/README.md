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
