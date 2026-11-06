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

### Lane C — update #5 — 19:49
Done: Ukraine practice round in check-ins: real resolved risk R0993 (energy attacks after the April 2025 pause) replayed as of 17 Apr 2025: answer → group view + "What actually happened" + scored vs ACAPS → added to your record. Answered check-ins now show a grey "✓ Answered" button. App handles rounds without the top-3 question.
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm run dev → Check-ins → "Practice · resolved risk" card
Requests to other lanes: →B: rounds can be `practice: true` with `as_of` + `outcome` (contracts/schemas/round.schema.json). →A: practice forecasts are scored like resolved ones (Brier vs ACAPS midpoint)
Contract change proposed: round.practice / as_of / outcome; open-rounds.country / practice (contracts/README.md)
Next: switch web/src/api.js to B's real API once IDs/auth are agreed
Blockers: contract freeze needs A+B OK
