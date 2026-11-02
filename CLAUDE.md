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
