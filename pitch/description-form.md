**Ground Truth** is a three-minute monthly check-in that lets ACAPS's trusted field experts test ACAPS's risk analyses, forecast what happens next and build a track record, without exposing who said what.

Live demo: https://groundtruth-acaps.vercel.app (works on a phone)

## The problem
The people closest to a crisis often sense it shifting first, but that knowledge stays in informal chats and never reaches ACAPS's analysis. ACAPS wants a small, trusted panel (5–10 experts per country) that takes minutes, not hours; protects people who can't be seen sharing views; keeps one loud voice or the group average from drowning out independent judgement; and shows over time whose forecasts are worth listening to.

## What we built
**For experts (mobile web app, English and French)**
1. **Blind check-in, ~3 minutes.** On a live ACAPS risk (demo: R1043, eastern Chad) the expert rates ACAPS's probability and impact (too low / about right / too high), ticks the triggers they see, forecasts each one by a deadline, ranks the country's top 3 risks and notes what ACAPS is missing.
2. **Anonymity chosen per answer:** fully anonymous (default), pseudonymous, or known to ACAPS.
3. **Reasons before numbers.** After submitting they read the panel's reasons with no numbers, then keep their answers or update once. Only then do the group's numbers appear. The blind first answer is the one scored, so copying the group never helps.
4. **Group view:** one dot per expert, agreement with ACAPS's rating, the panel's combined top 3 risks.
5. **Track record:** forecasts validated, a Brier accuracy score against ACAPS's own rating, a super estimator badge, and a practice round on a real resolved risk so scoring works on day one.
6. **Reasons to come back:** "Your input at work" shows when their input changed ACAPS's analysis; "What's next" shows the next check-in and when forecasts resolve. No streaks or points.

**For ACAPS:** a moderator page with answers before and after the reasons step, agreement with the rating, field-based vs remote experts, "what's missing" grouped by AI (Claude, moderator side only) and checked by a person, flags for copy-pasted or coordinated answers, and a switch for peer comments.

**For the public:** aggregates only, nothing below 3 responses, no free text word for word.

## How we use the Risk Radar data
- Each trigger's "objective to meet 100%" becomes a yes/no forecast question resolving in six months.
- **Backtest on 99 resolved risks:** ACAPS's ratings as probabilities score a Brier of **0.213**, against 0.239 for always guessing the 61% base rate. Risks rated Low happened 6 times in 14, about twice what the rating implies. That's the baseline every expert is scored against.
- The badge needs 5+ resolved forecasts and a clear win (90% interval) over both raw and calibrated ACAPS ratings, so hedging can't earn it.

## Trust and anonymity
- Invite-only, rate-limited, revocable; invites travel in headers, never in URLs.
- Names in a separate vault; anonymous answers carry only a one-way hash of a secret made on the expert's phone. No IP logging.
- Peers see reasons, never anyone's track record.
- Peer comments switch off for small areas (a named town, ≤100,000 people affected, or <30 organisations per OCHA 3W/HDX), so one voice can't mislead or be traced. Copy-pasted answers are never shown to peers.
- Witnesses of abuses are signposted to the ICC and eyeWitness, not asked to report in the app.

## Technology
- **Expert app:** React 18 + Vite, mobile-first, no UI framework, no third-party fonts or trackers
- **API:** FastAPI; SQLite locally, Supabase Postgres hosted; separate identity vault
- **Analysis:** Python standard library (ingest, question generator, synthetic panel, Brier scoring, backtest)
- **Shared:** JSON Schema contracts and fixtures; hosted on Vercel (demo site + live site with personal invite links)

All experts in the demo are synthetic; the risks are real ACAPS data. Still mocked: publishing moderator summaries to the public page.

## What's next
Arabic and Spanish, a sign-in page that keeps anonymity, user settings, fully automatic check-ins from the ACAPS API, richer data for ACAPS, stronger protection against attacks and false information, and more reasons to return. Ready to pilot with the Chad panel in December.
