# fixtures/: mock data (synthetic panel, real R1043)

Mock responses for every endpoint in `../contracts/README.md`, so every lane can build without waiting for the others.

**Regenerate:** `python3 fixtures/generate_fixtures.py` (from repo root, stdlib only). Edit the panel or answers in that script, not the JSON.

| File | What |
|---|---|
| `rounds_open_TCD.json` | `GET /rounds/open?panel=TCD` |
| `round_RD-R1043-1.json` | `GET /rounds/RD-R1043-1`: real R1043 risk and triggers T0618–T0620, 1 rating, 3 forecasts, 1 top-3 ranking |
| `post_response_request.json` / `post_response_201.json` | example POST body (Kestrel, version 1) and reply |
| `aggregate_RD-R1043-1.json` | group view as seen by Kestrel after submitting (n=7) |
| `aggregate_suppressed.json` | same endpoint when n<3 |
| `me_track_record.json` | Kestrel's track record in Lane A's shape: 8 **real resolved risks** from the CSV with synthetic forecasts, Brier vs ACAPS (midpoint mapping), rank 3 of 7, super estimator |
| `me_track_record_new.json` | a new expert with 2 resolved forecasts: not ranked yet, "3 more until counted" |
| `leaderboard.json` | peer leaderboard in Lane A's shape (7 ranked, 1 not yet) |
| `moderator_round_RD-R1043-1.json` | moderator view: v1/v2 spread, revision shifts, region split (n<3 dropped), "what's missing" with tier-aware names, mock AI clusters |
| `public_summaries.json` | public page: aggregates only (the generator asserts no tokens, pseudonyms or verbatim text) |
| `experts.json` / `identity_vault.json` / `contributions_RD-R1043-1.json` | seed tables for Lane B's DB and Lane A's analysis |

## Synthetic Chad panel (8 invited, 7 answered)

| id | pseudonym | profile | region | tier | bias (Lane A only) |
|---|---|---|---|---|---|
| E01 | Kestrel | Local NGO director | East | known | well_calibrated |
| E02 | Linden | Anticipatory-action officer | N'Djamena | known | anchored_on_acaps |
| E03 | Osprey | Conflict analyst, social media | Abroad | pseudonymous | alarmist |
| E04 | Birch | University researcher | Abroad | pseudonymous | underconfident |
| E05 | Heron | UN regional office | Abroad | pseudonymous | well_calibrated |
| E06 | Wren | MEAL officer | East | pseudonymous | noisy |
| E07 | — | Community responder | East | anonymous | alarmist |
| E08 | Alder | Donor-agency methodologist | Abroad | known | (not answered yet) |

E03, E04 and E06 revised after the reveal (version 2). Ranking options `SYN-TCD-*` are synthetic and flagged `synthetic: true`. Show that in the UI.
