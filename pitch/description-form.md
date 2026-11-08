**Ground Truth** is a three-minute monthly check-in that lets ACAPS's trusted field experts **test ACAPS's risk analyses, forecast what happens next and build a track record**, without exposing who said what.

## The problem
The people closest to a crisis often sense it shifting first, but that knowledge stays in informal chats and never reaches ACAPS's analysis. ACAPS wants a small, trusted panel of 5–10 experts per country that:
- takes **minutes, not hours**, so busy field staff actually answer;
- **protects people** who can't be seen sharing views;
- keeps one loud voice or the group average from **drowning out independent judgement**;
- shows, over time, **whose forecasts are worth listening to**.

## What we built

### For experts: a mobile web app in English and French
1. **Blind check-in, about 3 minutes.** On a live ACAPS risk (demo: R1043, eastern Chad) the expert rates ACAPS's probability and impact as too low, about right or too high, ticks the triggers they see on the ground, forecasts each one by a deadline, ranks the country's top 3 risks and notes what ACAPS is missing.
2. **Anonymity chosen per answer:** fully anonymous (the default), pseudonymous, or known to ACAPS.
3. **Reasons before numbers.** After submitting, they read the panel's reasons without any numbers, then keep their answers or update once. Only then do the group's numbers appear. The blind first answer is the one scored, so *copying the group never helps*.
4. **Group view:** one dot per expert, agreement with ACAPS's rating and the panel's combined top 3 risks.
5. **Track record:** forecasts validated, a Brier accuracy score against ACAPS's own rating, a super estimator badge, and a practice round on a real resolved risk so scoring works from day one.
6. **Reasons to come back:** "Your input at work" shows when their input changed ACAPS's analysis; "What's next" shows the next check-in and when their forecasts resolve. No streaks or points.

### For ACAPS: a moderator page
Answers before and after the reasons step, agreement with the rating, field-based vs remote experts, "what's missing" **grouped by AI (Claude, moderator side only) and checked by a person**, flags for copy-pasted or coordinated answers, and a switch for peer comments.

### For the public
Aggregates only: **nothing below 3 responses**, no free text published word for word.

## Does it work? Backtest on the Risk Radar
Each trigger's "objective to meet 100%" becomes a yes/no forecast question that resolves in six months. We scored ACAPS's own ratings, turned into probabilities, on the **99 resolved risks** in the export:

| Forecaster | Brier score (lower is better) |
|---|---|
| ACAPS's ratings | **0.213** |
| Always guessing the 61% base rate | 0.239 |

ACAPS beats guessing, with room to improve: **risks rated Low happened 6 times in 14**, about twice what the rating implies. That is the baseline every expert is scored against, on the same questions. The super estimator badge needs 5+ resolved forecasts and a clear win over both raw and calibrated ACAPS ratings, so hedging can't earn it.

## Trust and anonymity
- **Invite-only:** rate-limited and revocable; invites travel in request headers, never in URLs.
- **Identities kept apart:** names sit in a separate vault; anonymous answers carry only a one-way hash of a secret made on the expert's phone. No IP logging.
- **Reasons, not records:** other experts see reasons, never anyone's track record.
- **Peer comments only where safe:** they switch off for small areas (a named town, up to 100,000 people affected, or fewer than 30 organisations according to OCHA 3W/HDX), so one voice can't mislead the panel or be traced. Copy-pasted answers are never shown to peers.
- **Witnesses signposted:** people who saw abuses are pointed to the ICC and eyeWitness, not asked to report in the app.

## Technology
| Part | Stack |
|---|---|
| Expert app | React 18 + Vite, mobile-first, no UI framework, no third-party fonts or trackers |
| API | FastAPI; SQLite locally, Supabase Postgres hosted; separate identity vault |
| Analysis | Python standard library: ingest, question generator, synthetic panel, Brier scoring, backtest |
| Shared | JSON Schema contracts and fixtures; hosted on Vercel (demo site + live site with personal invites) |

All experts in the demo are synthetic; the risks are real ACAPS data. Still mocked: publishing moderator summaries to the public page.

## What's next
- **More languages:** Arabic and Spanish
- **Sign-in page** that keeps anonymous answers unlinkable
- **Settings** so each expert can set the app to their taste
- **Fully automatic check-ins** from the ACAPS API
- **Richer data** for ACAPS to analyse and export
- **Stronger protection** against attacks and false information
- **More reasons to return:** results when forecasts resolve, and a monthly note on how ACAPS used the panel's input

**Ready to pilot with the Chad panel in December.**
