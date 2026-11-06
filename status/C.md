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

### Lane C — update #2 — 17:57
Done: Pulse flow polished (headings + subtitles on every step, presets for forecasts, "your answers and why" recap step with reasoning + source tags). Results page: one chart per answer type (rating bar, forecast dot plot, ranking bars) with a one-line takeaway. Profile: "4 of 5 correct", Brier vs ACAPS, latest + past predictions. Phone (thumb action bar, tab bar) + desktop (top nav, 2–3 columns) layouts.
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm install && npm run dev → http://localhost:5173
Requests to other lanes: →B: store reasoning_text / reasoning_basis (moderator-only, like missing_text). →A: optional: use reasoning_basis in the moderator view
Contract change proposed: questions.title/title_fr; responses.reasoning_text/reasoning_basis (see contracts/README.md)
Next: offline queue; decide with team whether to keep a one-time revise (Delphi round 2)
Blockers: contract freeze needs A+B OK
