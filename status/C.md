# Lane C — expert app & pitch

Folders: `web/`, `pitch/`. Don't edit `contracts/`, `api/`, `analysis/`, `moderator/`.

## Tasks

- [x] **Pick the web stack + sketch 3 screens.** Round card, group reveal, my track record. *Done when:* stack is written in BOARD.md decisions (after voice agreement) and sketches are in `pitch/`.
- [x] **Pulse flow against mocks.** Rating agree/disagree, triggers "I'm seeing this", what's missing, forecast slider; one screen per step, mobile-first. *Done when:* the full flow runs on a phone against `fixtures/`.
- [x] **Anonymity tier picker.** 3 tiers, most protective by default, changeable per answer. *Done when:* the chosen tier is sent with each response.
- [ ] **Group reveal + revise.** Unlocks only after own submit; distribution, not just an average; one revision. *Done when:* works against mock `/aggregate`.
- [ ] **Track record + public page + signpost screen.** *Done when:* all three pages render from mocks.
- [ ] **EN/FR toggle + pitch.** *Done when:* strings switch language; pitch draft and demo script in `pitch/` by Sat evening.

## Latest update

### Lane C — update #4 — 19:18
Done: Split the app into tabs: Ground truth (check-ins → survey → results) · Forecasts (Open forecasts: every open question, update any time, group median hidden until you answer; My record: profile + leaderboard) · Public. Desktop header has a Ground truth | Forecasts switch; phone has 3 bottom tabs. Survey steps are tagged Ground truth / Forecasts. 2 synthetic short-term (1–3 month) questions added.
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm run dev → #/ and #/forecasts
Requests to other lanes: →B: GET /forecasts/open + POST /forecasts/{question_id} (contracts/schemas/forecasts.schema.json); store every update, group null until caller answered and n≥3. →A: score the last forecast before closes_at (not only v1/v2); real short-horizon questions can replace Q-R1043-S01/S02
Contract change proposed: forecasts endpoints + invariant 7 + version 3+ = forecast updates (contracts/README.md)
Next: switch web/src/api.js to B's real API once IDs/auth are agreed
Blockers: contract freeze needs A+B OK
