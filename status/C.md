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

### Lane C — update #8 — 15:02
Done: web ↔ API mismatches owned by C (status/A.md W1, W2, W3, W6, W8, W9, W10, W12, W14): adapters in web/src/api.js map Lane B's responses onto the contract shapes, so screens are unchanged. Tested end to end against lane-b @ 1e6a58d with a fresh DB: open rounds → round → anonymous submit → locked → moderator reveal → group view → one revision → track record → public. Anonymous: phone sends sha256(secret) as device_secret, raw secret never leaves the phone (closes W7 on our side, no API change). Reveal shows "waiting for the moderator" while locked; agree share instead of 3-way bars; moderator-approved themes instead of verbatim peer comments when on the API (W11).
Pushed: lane-c | PR: see BOARD.md integration log
How to see it: VITE_API_URL=http://localhost:8000 npm run dev (with B's API running); demo mode unchanged
Requests to other lanes: →A/B: track record lists the revised forecast as pending; we score the blind (v1) answer, please confirm. →B: rationale/trend/exposure on GET /rounds/{id} (W3), 3-way rating + ranking fields (W4/W5), closes_at on open rounds (W2)
Contract change proposed: none
Next: backup demo video; moderator slide with A/B
Blockers: none for C
