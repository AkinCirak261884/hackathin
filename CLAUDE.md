# CLAUDE.md — Context for AI Coding Assistants

This is the challenge repository for the **ACAPS Ground Truth** challenge at **Hackathon for Good #8** (6-8 November 2026, The Hague).

## What This Repo Is

A hackathon challenge repository — not a software project. It contains:
- Challenge documentation (the problem to solve)
- A dataset (ACAPS Risk Radar export: 139 humanitarian risks across 57 countries)
- Reference materials (methodology docs)
- A starter notebook for data exploration

Participants fork this repo and build their solutions on top of it.

## The Challenge

Build a system for ACAPS to engage a trusted network of humanitarian experts to:
1. **Ground truth** ACAPS risk analyses (Delphi-style expert validation)
2. **Forecast** risk outcomes within a six-month horizon (with scoring and "super estimator" tracking)

Key constraints: expert anonymity, minimal time commitment, retention over time, small trusted groups (5-10 per country).

## Repo Structure

```
docs/           → Challenge brief, methodology, data dictionary, evaluation criteria, resources
data/           → Risk Radar export (CSV + XLSX), data README
references/     → ACAPS methodology PDF and infographic
notebooks/      → Starter data exploration notebook
```

## Data

- `data/risk-radar-export.csv` — clean CSV, 139 rows, 25 columns
- Key fields: Risk ID, Risk Title, Country, Probability, Impact, Risk Level, Status
- Demo risk: **R1043** (Chad/Sudan cross-border insecurity)
- Text fields may contain multi-line content; triggers field has structured `Trigger ID: / Title: / Description:` format

## Important Notes

- Do not use personal data of real experts — use synthetic users
- The data is a working export with some quality issues (see `docs/data-dictionary.md`)
- ACAPS data is used under ACAPS' terms of use

## Team Rules (hackhaag, 3 lanes)

- Read `BOARD.md` first: plan, decisions, data model, endpoints, cut order. Your tasks and latest update are in `status/{A|B|C}.md`.
- Lanes: **A** = data & scoring (`analysis/`, `moderator/`) · **B** = backend & trust (`api/`) · **C** = expert app & pitch (`web/`, `pitch/`).
- Work only in your lane's folders and your own `status/` file. Never edit `contracts/`, `fixtures/` or other lanes' folders. If you need something from another lane, use mocks from `fixtures/` and add a request to `BOARD.md` → "Requests between lanes".
- Contract changes: agree on voice first, then change `contracts/`, then everyone pulls.
- Branches `lane-a` / `lane-b` / `lane-c`; commit messages prefixed `[A]` / `[B]` / `[C]`; small PRs to `main` every 2–3 hours.
- Synthetic users only. Public outputs: aggregates only, n ≥ 3, no verbatim free text, no IP/device logging.

### Session prompt (paste into your Claude Code, fill in the lane)

> You are Claude Code for Lane {A|B|C} on our hackathon team. Do this, in order:
> 1. `git pull --rebase` on your lane branch and merge latest `main`. Read `CLAUDE.md`, `BOARD.md`, `contracts/` and `status/{A|B|C}.md`.
> 2. List briefly what from the other two lanes affects you: contract changes, requests addressed to you, things ready to integrate, blockers.
> 3. Handle a small request addressed to your lane first; otherwise take the next unchecked task in your status file. Write a short plan before coding.
> 4. Work only in your lane's folders (see Team Rules).
> 5. Run it / run the tests. Commit in small steps, push your branch, open or update a PR to `main` if tests pass.
> 6. Stop after one task (~30–45 min). Don't start a second large task.
> 7. Tick the task in `status/{A|B|C}.md` and replace the "Latest update" block (under 15 lines, format already in the file).
