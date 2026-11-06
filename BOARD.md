# hackhaag board

Shared team board. Fixed plan, agreed decisions and contracts, requests between lanes, integration log.
Each lane's tasks and latest update live in `status/A.md`, `status/B.md`, `status/C.md`. Edit only your own status file.

## Goal & demo path (fixed)

Expert pulse on **R1043** (Chad/Sudan cross-border insecurity) → blind round 1 → Delphi round 2 reveal and one revision → moderator summary and publish → public aggregate page → forecast scoring and super-estimator leaderboard (backtest on Risk Radar).

Also answer the brief's example question: *"top three risks in Chad over the next six months"*, from the panel view.

## Lanes

| Lane | Owner | Folders | Owns |
|---|---|---|---|
| **A — data & scoring** | ___ | `analysis/`, `moderator/` | Risk Radar ingest, trigger → question generator, synthetic experts, Brier scoring, backtest, leaderboard, Streamlit moderator dashboard |
| **B — backend & trust** | ___ | `api/` | DB schema, core API, identity vault, anonymity tiers, min-3 suppression, round stages, AI synthesis (moderator side only), publish flow |
| **C — expert app & pitch** | ___ | `web/`, `pitch/` | Expert pulse app (mobile), anonymity tier picker, group reveal, track record, public summary page, EN/FR, pitch deck, demo script |

Shared, changed only after voice agreement: `contracts/`, `fixtures/`, `BOARD.md` decisions section.

## Decisions & contracts (change only after voice agreement)

- **Stack:** `api/` = FastAPI + SQLite · `moderator/` = Streamlit (reads the DB directly) · `analysis/` = Python · `web/` = ___ (plain HTML/JS or React, Lane C decides)
- **Branches:** `lane-a`, `lane-b`, `lane-c` → merge to `main` via small PRs, at least every 2–3 hours
- **Commit prefix:** `[A]`, `[B]`, `[C]`
- **Triggers → questions:** each trigger's "objective to meet 100%" becomes a yes/no question resolving 6 months after the round opens. R1043 = 3 trigger questions + 1 "do you agree with ACAPS's rating?" item.
- **Anonymity:**
  - Identities live only in `identity_vault` (synthetic data only). Contributions store an `author_token`, never a name.
  - Known / pseudonymous tiers: token = pseudonym ID. Only the moderator view resolves it, and only for the "known" tier.
  - Fully anonymous tier: token = one-way hash of a device-held secret. Scorable, never linkable.
  - No aggregate until **n ≥ 3** responses. Drop any geography breakdown with n < 3.
  - Free text is never published verbatim. Public page shows only moderator-approved summaries.
  - No IP or device logging.
- **Access:** invite-only. Each expert gets a personal invite token from the moderator. Rate-limit and revoke per token. The invite is the anti-spam and anti-misinformation layer, not metadata about the person. Possible extension: referral invites (an expert vouches, the moderator approves).
- **Out of scope (on purpose):** open public reporting and war-crime evidence intake. Witness knowledge reaches ACAPS through panel experts ("what's missing" field). Add a static signpost screen that links to dedicated secure channels (e.g. OHCHR, ICC OTP, eyeWitness to Atrocities). Explain on one slide.
- **Groupthink:** round 1 is blind. Group view (median, spread, one dot per answer) unlocks only after your own submit. One revision allowed; both versions stored.
- **Scoring:** Brier per answer. Moderator aggregate = median, later a track-record-weighted mean. Backtest baseline = ACAPS ratings mapped to Very Low 10% / Low 30% / Medium 50% / High 70% / Very High 90%, scored on resolved risks.

### Data model

```
risks(risk_id, title, country, probability, impact, level, status)
triggers(trigger_id, risk_id, title, description, completion_rate, objective)
questions(question_id, risk_id, trigger_id, text, closes_at, outcome)
rounds(round_id, risk_id, stage[blind|reveal|closed], opened_at)
experts(expert_id, pseudonym, country_panel, lang, default_tier)
identity_vault(expert_id, name, email)          -- separate, synthetic only
contributions(id, round_id, question_id, author_token, tier, prob,
              agree, missing_text, version[1|2], created_at)
scores(author_token, question_id, brier)
```

### Endpoints

```
GET  /rounds/open?panel=TCD          GET  /rounds/{id}
POST /rounds/{id}/responses          GET  /rounds/{id}/aggregate  (n≥3, after own submit)
GET  /me/track-record?token=…        GET  /public/summaries
GET  /moderator/rounds/{id}          POST /moderator/rounds/{id}/advance | /publish
```

Each endpoint gets a mock JSON file in `fixtures/` so Lane C can build before the API exists.

## Checkpoints

1. **Fri ~23:00: contract frozen.** `contracts/` and mock JSON in `fixtures/` committed. No field renames after this without telling the other two.
2. **Sat ~13:00: first integration.** Expert app submits a real response to the real API for R1043.
3. **Sat ~20:00: full loop.** 5 synthetic experts answer → reveal works → moderator publishes → public page shows the summary. "Top 3 risks in Chad" works from the panel view.
4. **Sun mid-morning: feature freeze.** After this, only fixes, README, backup demo video, pitch rehearsal.

## If you fall behind, cut in this order

1. AI synthesis (mock it with a prepared summary)
2. Geography breakdown
3. French
4. Anonymous-tier hashing (explain it on a slide instead)

**Never cut:** blind-then-reveal, the min-3 rule, the backtest. They answer the jury's hardest questions: groupthink, anonymity, "does it work?"

## Open questions for Alex (ACAPS)

- [ ] Does the anonymity model (3 tiers, min-3, no verbatim free text) match how ACAPS would actually run it?
- [ ] How would a moderator actually use the summary? What's the one button they need?
- [ ] Are referral invites acceptable, or must ACAPS hand-pick every expert?
- [ ] Should the app include a signpost screen for witnesses of serious violations?
- [ ] Sanity-check the R1043 forecast questions and thresholds.
- [ ] The pilot is ~2 months but questions run 6 months. OK to add 1–3-month trigger questions so scores exist during the pilot? (Lane A proposal in `status/A.md`)
- [ ] Is "others' answers hidden until you've answered" (feed idea) OK for ACAPS?

## Requests between lanes

- [ ] (A → B, C) Review "Lane A proposal: scoring approach" in `status/A.md` (min forecasts for leaderboard, 1–3-month questions). Agree on voice.
- [x] (A → C) Opinion on the Twitter/Reddit-style feed pivot ("hidden until you answer"). Questions and answer slot in `status/A.md` → "Questions for other lanes". Answer there.
- [ ] (from → to) what is needed

## Integration log

- HH:MM what was merged / what broke
