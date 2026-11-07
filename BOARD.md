# hackhaag board

Shared team board. Fixed plan, agreed decisions and contracts, requests between lanes, integration log.
Each lane's tasks and latest update live in `status/A.md`, `status/B.md`, `status/C.md`. Edit only your own status file.

## ⚠️ For the team call (from Lane A's smoke test, 6 Nov evening)

**Every lane: read this before your next task.** Full results, with an owner per item: `status/A.md` → "Smoke test" (demo path, 13 rows) and "Web ↔ API mismatches" (W1–W16).

**Blocker: the demo can't run from `main`.** `main` has no `api/` or `web/`. Merge lane-b and PR #1 (lane-c). They merge cleanly together, and B's tests pass on the combined code. **Owners: B, C**

**Privacy: decide on the call**
1. **Peer comments (W11).** The web app now shows peers other experts' "why I think this" text word for word, with their record and forecasts. The API keeps it moderator-only. Lane C's earlier answer said never verbatim, because writing style can re-identify people in a panel of 5–10. Decide: verbatim, opt-in quote, or moderator-approved themes only. **B + C**
2. **Pseudonymous experts are identifiable by ACAPS (#6).** The moderator view shows `psd_EXP-TCD-0x` (the expert ID), which the vault maps to a name. That breaks "pseudonymous: nobody sees your name". **B**
3. **Tokens in URLs (W9, W12).** The web app still sends `?token=` on `/aggregate` and `/me/track-record`. The API takes headers only, so these calls fail (422) and would leak tokens into logs and history. **C**
4. **Anonymous token (W7).** Agree option (c): hash on the phone, server keeps only an HMAC, no invite→anon link stored. Today the web sends `anon_token` and the API wants `device_secret`, so anonymous answers fail (422). **B + C**

**Also to agree:** rating and top-3 questions (W4: `Q-R1043-RATING` / `Q-TCD-TOP3` don't exist in the API); response shapes for open rounds, round, aggregate and public summary (W2, W3, W10, W14, W15); publish doesn't reach `/public/summaries` (#8, B).

## Goal & demo path (fixed)

Expert pulse on **R1043** (Chad/Sudan cross-border insecurity) → blind round 1 → Delphi round 2 reveal and one revision → moderator summary and publish → public aggregate page → forecast scoring and super-estimator leaderboard (backtest on Risk Radar).

Also answer the brief's example question: *"top three risks in Chad over the next six months"*, from the panel view.

## Lanes

| Lane | Owner | Folders | Owns |
|---|---|---|---|
| **A — data & scoring** | ___ | `analysis/`, `moderator/` | Risk Radar ingest, trigger → question generator, synthetic experts, Brier scoring, backtest, leaderboard, Streamlit moderator dashboard |
| **B — backend & trust** | ___ | `api/` | DB schema, core API, identity vault, anonymity tiers, min-3 suppression, round stages, AI synthesis (moderator side only), publish flow |
| **C — expert app & pitch** | AkinCirak261884 | `web/`, `pitch/` | Expert pulse app (mobile), anonymity tier picker, group reveal, track record, public summary page, EN/FR, pitch deck, demo script |

Shared, changed only after voice agreement: `contracts/`, `fixtures/`, `BOARD.md` decisions section.

## Decisions & contracts (change only after voice agreement)

- **Stack:** `api/` = FastAPI + SQLite · `moderator/` = Streamlit (reads the DB directly) · `analysis/` = Python · `web/` = React 18 + Vite (Lane C decided)
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

- [ ] (C → A, B) Review draft `contracts/` + `fixtures/` (PR from `lane-c`). `contracts/README.md` lists 4 small additions to the data model above. Agree on voice, then freeze.
- [ ] (A → B, C) **Smoke test results: see "⚠️ For the team call" at the top and `status/A.md` → "Smoke test" / "Web ↔ API mismatches" (owner per item).**
- [ ] (A → B, C) Review "Lane A proposal: scoring approach" in `status/A.md` (min forecasts for leaderboard, 1–3-month questions). Agree on voice.
- [x] (A → C) Opinion on the Twitter/Reddit-style feed pivot ("hidden until you answer"). Questions and answer slot in `status/A.md` → "Questions for other lanes". Answer there.
- [ ] (C → A) Track record `history[]`: please add `group_median_prob` (panel median at close, n ≥ 3), `group_brier` and `beat_group` per resolved question. The accuracy page lets experts compare against "ACAPS" or "Panel middle"; it uses synthetic values in `web/src/api.js` (`DEMO_GROUP_MEDIAN`) until then, and hides the option when the field is missing. Optional contract addition to `track-record.schema.json`.
- [ ] (C → B) `GET /acaps/risks?panel=TCD`: server-side proxy to the ACAPS API (free account, token auth, see `docs/resources.md`). Keep the ACAPS token in the server env only, never send it to the browser; cache the result (the risk list updates monthly). Return `{ source: "live", panel, updated_at, risks: [{ risk_id, title, country, iso, risk_type, probability, impact, risk_level, trend, status }] }`, active risks for the panel's countries (TCD → TCD + SDN). Mock shape: `web/src/mock/acaps_risks_TCD.json`. The web app falls back to that snapshot if the call fails.
- [ ] (C → A, B) Track record `pending[]` shows the **revised** (v2) forecast; our design scores the **blind** (v1) answer (both stored, see Delphi step 2). Please confirm which version `scoring.py` / `records.py` use. Found in Lane C's end-to-end test, 7 Nov.
- [ ] (C → B) Still missing on the API side (web handles their absence): `GET /rounds/{id}` risk detail (`rationale_short`, `trend`, `expected_exposure`, trigger `description`) (W3); 3-way rating fields + top-3 ranking (W4/W5; web currently sends `agree` = both "about right"); `closes_at` on `/rounds/open` (W2). Anonymous: web now sends `device_secret = sha256(phone secret)`, works with the current API unchanged (W7).
- [ ] (from → to) what is needed

## Integration log

- HH:MM what was merged / what broke
