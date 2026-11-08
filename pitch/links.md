# Ground Truth: links

Everything for trying and reviewing Ground Truth (Hackathon for Good #8, ACAPS Ground Truth challenge). All experts in the demo are synthetic; the risks are real ACAPS Risk Radar data.

| What | Link | Notes |
|---|---|---|
| **Try the expert app** | https://groundtruth-acaps.vercel.app | Demo data, no login, works on a phone. "Reset my answers (demo)" on the home page lets you start again. |
| **Live version on the real API** | https://groundtruth-acaps-live.vercel.app/#/?invite=inv_demo_01 | One expert invite, for one person: the first to open it can answer the check-in; anyone after that sees the group view. Answers show up on the moderator page. |
| **Moderator page for ACAPS** | https://ground-truth-api.vercel.app/ui/moderator | Needs the moderator key, which the team gives to the jury directly (it is not in this public repo). Paste it at the top right and press Connect. Please don't press "Reset round (demo)": it wipes the live answers. |
| **Demo video** (76 s, no sound) | [backup-demo.mp4](backup-demo.mp4) | A phone screen recording of the full check-in. |
| **Source code** | https://github.com/AkinCirak261884/hackathin | Expert app (`web/`), API (`api/`), scoring and backtest (`analysis/`). |
| **Hosted API code** | https://github.com/AkinCirak261884/hackathin/tree/supabase-api | The Supabase/Postgres version behind the live site, deployed separately until it is merged into `main`. |
| **Backtest and scoring** | [analysis/README.md](../analysis/README.md) | ACAPS's ratings on 99 resolved risks: Brier 0.213 against 0.239 for guessing; how the super estimator badge works. |
