# Lane C — expert app & pitch

Folders: `web/`, `pitch/`. Don't edit `contracts/`, `api/`, `analysis/`, `moderator/`.

## Tasks

- [x] **Pick the web stack + sketch 3 screens.** Round card, group reveal, my track record. *Done when:* stack is written in BOARD.md decisions (after voice agreement) and sketches are in `pitch/`.
- [x] **Pulse flow against mocks.** Rating agree/disagree, triggers "I'm seeing this", what's missing, forecast slider; one screen per step, mobile-first. *Done when:* the full flow runs on a phone against `fixtures/`.
- [x] **Anonymity tier picker.** 3 tiers, most protective by default, changeable per answer. *Done when:* the chosen tier is sent with each response.
- [x] **Group reveal + revise.** Unlocks only after own submit; distribution, not just an average; one revision. *Done when:* works against mock `/aggregate`.
- [x] **Track record + public page + signpost screen.** *Done when:* all three pages render from mocks.
- [ ] **EN/FR toggle + pitch.** *Done when:* strings switch language; pitch draft and demo script in `pitch/` by Sat evening.

## Latest update

### Lane C — update #7 — 14:22
Done: Delphi step 2 (option B, reasons first). After submitting, experts read peer reasons without numbers, then keep or update once (sliders start at the first answer, optional "what changed your mind?"). Numbers unlock after the decision. First answer stays the scored one; detail page and "Check my answers" show first → updated. Practice round skips the step (outcome is shown).
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm run dev → Check-ins → reset demo → answer Chad check-in → step 2
Requests to other lanes: →B: revision arrives as POST version 2 with only changed forecasts + reasoning_text (no contract change). →A: score version 1; v1→v2 shift per question is available for the moderator view
Contract change proposed: none
Next: pitch draft + demo script in pitch/
Blockers: in real-API mode step 2 needs the first answer kept locally (only done in mock today), to agree with B
