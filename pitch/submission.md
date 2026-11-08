# Ground Truth

**A three-minute monthly check-in that lets ACAPS's trusted field experts test ACAPS's risk analyses, forecast what happens next and build a track record, without exposing who said what.**

- **Live demo:** https://groundtruth-acaps.vercel.app (demo data, works on a phone)
- **Repo:** https://github.com/AkinCirak261884/hackathin
- Built at Hackathon for Good #8 (The Hague, 6–8 November 2026) for the ACAPS Ground Truth challenge. All experts in the demo are synthetic; the risks are real ACAPS Risk Radar data.

## The problem

ACAPS publishes risk analyses for crises around the world, such as the cross-border insecurity spilling from Sudan into eastern Chad (R1043). The people closest to a crisis (local staff, NGO workers, community contacts) often sense it shifting first, but that knowledge stays in informal chats and never reaches the analysis.

ACAPS wants a small, trusted panel of 5–10 experts per country to check its analyses and forecast outcomes over six months. That only works if it takes minutes rather than hours, protects people who cannot be seen sharing views, stops one loud voice or the group average from drowning out independent judgement, and shows over time whose forecasts are worth listening to.

## What we built

### For experts: a mobile web app in English and French

1. **Blind check-in, about 3 minutes.** On a live ACAPS risk, the expert says whether ACAPS's probability and impact are too low, about right or too high; ticks the ACAPS triggers they can see on the ground; gives a probability for each trigger by a fixed deadline; ranks the top three risks for the country; and notes what ACAPS is missing, including developments ACAPS hasn't listed. They also say what their answer is based on: what they see themselves, local contacts, media or reports.
2. **Anonymity, chosen per answer.** Fully anonymous (the default: not even ACAPS can link the answer to them), pseudonymous to other experts, or known to ACAPS.
3. **Reasons before numbers.** After submitting, the expert reads the panel's reasons without any numbers, then keeps their answers or updates once, saying what changed their mind. Only then do the group's numbers appear. Their blind first answer is kept and is the one that is scored, so copying the group can never improve a record. This is a Delphi round compressed into one sitting.
4. **Group view.** One dot per expert with the middle half shaded, agreement with ACAPS's rating, the panel's combined top three risks for the country, and what the panel added, without names.
5. **Track record.** How many past forecasts were validated, a Brier accuracy score compared with ACAPS's own rating, a page per forecast, and a super estimator badge. A practice round on a real, already-resolved ACAPS risk (Ukraine, April 2025) shows the scoring working on day one.
6. **Reasons to come back.** The profile opens with "Your input at work" (each time a point the expert made changed ACAPS's analysis) and "What's next" (the next check-in and the date their forecasts resolve). No streaks, no points, no public leaderboard.

The home page also lists ACAPS's current risks for the expert's area, and a signpost page sends witnesses of serious abuses to the ICC and eyeWitness instead of collecting that evidence in the app.

### For ACAPS: a moderator page

For each round the moderator sees answers before and after the reasons step (how far the panel moved), agreement with ACAPS's rating, field-based versus remote experts (from their own "based on" ticks), "what's missing" grouped by AI (Claude, on the moderator side only) and checked by a person, flags for copy-pasted or coordinated answers, and contributors by anonymity level. The moderator can turn peer comments off and move the round from open to reveal to closed. Late first answers are still accepted after the reveal and counted when the round closes. Track records are visible to the moderator only, to weigh views.

### For the public

A public page with aggregates only: nothing below 3 responses, and no free text published word for word.

## How it uses the Risk Radar data

- **Questions from triggers.** Each ACAPS trigger's "objective to meet 100%" becomes a yes/no forecast question that resolves six months after the round opens. R1043 gives three trigger questions plus the rating question.
- **Real risk context.** Check-ins show ACAPS's rationale, trend, expected exposure and trigger progress, with links to ACAPS's sources.
- **Backtest.** We turned ACAPS's ratings into probabilities and scored them on the 99 resolved risks in the export: a Brier score of 0.213, against 0.239 for always saying the 61% base rate. ACAPS is better than guessing, with room to improve: risks rated Low happened 6 times in 14 (43%), about twice what the rating implies. That is the baseline every expert is measured against, on the same questions.
- **A badge that can't be gamed.** The super estimator badge needs at least 5 resolved forecasts and a clear win over both ACAPS's raw ratings and a calibrated version of them (the paired 90% interval must lie above zero). Hedging towards 50% doesn't earn it: in the backtest, only the 2 of 8 synthetic experts who were given real extra information do.
- **Comments policy from open data.** Expected exposure from the Risk Radar, OCHA 3W presence data and HDX Populated Places decide, per round, whether peer comments are safe (see below).

## Trust and anonymity

- **Invite-only.** Each expert gets a personal invite from ACAPS, rate-limited and revocable. The invite sits after the `#` in the link, so it is never sent to the server as part of a URL; after that it travels only in request headers.
- **Identities kept apart.** Names and invites live in a separate vault (a separate database locally, a separate schema on Postgres); answers carry only a token. Anonymous answers are linked only to a one-way hash of a secret generated on the expert's phone, so a track record still builds up without anyone being able to link it to a person.
- **No IP or device logging.**
- **Minimum of 3.** No group view, breakdown or public number is shown for fewer than 3 responses.
- **Peers see reasons, never records.** Comments show reasons only; no expert's track record is shown to other experts.
- **Peer comments only where they are safe.** Per round, comments switch off if the risk names a town or village, if few people are affected (up to 100,000) or if fewer than 30 organisations work there. In a small area one comment can't be cross-checked, can spread misinformation and is easy to trace back. Experts still answer; their text goes only to the moderator. Copy-pasted or coordinated answers are never shown to other experts.

## How it is built

| Part | What | Stack |
|---|---|---|
| `web/` | Expert app, mobile-first, English and French | React 18 + Vite, no UI framework, no third-party fonts or trackers (no expert's IP goes to a third party) |
| `api/` | Rounds, responses, aggregates, track records, trust layer, moderator page | FastAPI; SQLite locally, Supabase Postgres when hosted |
| `analysis/` | Risk Radar ingest, trigger-to-question generator, synthetic panel, Brier scoring, backtest, leaderboard | Python standard library |
| `contracts/`, `fixtures/` | JSON schemas shared by all parts, demo data for every endpoint | JSON Schema |

Hosted on Vercel: a demo site with demo data, and a live site wired to the API with personal invite links. Built by a team working in three lanes: data and scoring, backend and trust, expert app and pitch.

## Status

Working: the full expert flow, both on demo data and live against the API; track record; moderator page; public page; English and French; scoring and backtest. Still mocked: publishing moderator summaries to the public page.

## What's next

- **More languages:** Arabic and Spanish next to English and French. Arabic alone covers about a third of ACAPS risks.
- **Sign-in page:** sign in again on a new phone without a new invite, while anonymous answers stay unlinkable.
- **Settings:** language, reminders, text size, low-data mode and a default anonymity level.
- **More reasons to come back:** results when forecasts resolve, and a monthly note on how ACAPS used the panel's input.
- **Fully automatic check-ins:** new risks and triggers from the ACAPS API become check-ins on their own.
- **Richer data for ACAPS:** more variables per answer and per round, ready to analyse and export.
- **Protection against attacks and false information:** stronger defences for the site, and checks that flag false or coordinated input before other experts see it.

Ready to pilot with the Chad panel in December: one link per expert, no account.
