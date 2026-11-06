# Lane C — expert app & pitch

Folders: `web/`, `pitch/`. Don't edit `contracts/`, `api/`, `analysis/`, `moderator/`.

## Tasks

- [x] **Pick the web stack + sketch 3 screens.** Round card, group reveal, my track record. *Done when:* stack is written in BOARD.md decisions (after voice agreement) and sketches are in `pitch/`.
- [ ] **Pulse flow against mocks.** Rating agree/disagree, triggers "I'm seeing this", what's missing, forecast slider; one screen per step, mobile-first. *Done when:* the full flow runs on a phone against `fixtures/`.
- [ ] **Anonymity tier picker.** 3 tiers, most protective by default, changeable per answer. *Done when:* the chosen tier is sent with each response.
- [ ] **Group reveal + revise.** Unlocks only after own submit; distribution, not just an average; one revision. *Done when:* works against mock `/aggregate`.
- [ ] **Track record + public page + signpost screen.** *Done when:* all three pages render from mocks.
- [ ] **EN/FR toggle + pitch.** *Done when:* strings switch language; pitch draft and demo script in `pitch/` by Sat evening.

## Latest update

### Lane C — update #1 — 17:22
Done: React+Vite skeleton in web/ (all 6 screens routed, reading fixtures; basic pulse flow, tier picker, reveal strip, track record, public, signpost). Draft contracts/ (JSON Schemas) + fixtures/ generated from real R1043. Screen sketches + pitch outline in pitch/.
Pushed: not yet (local branch lane-c)
How to see it: cd web && npm install && npm run dev → http://localhost:5173
Requests to other lanes: →A, →B: review contracts/README.md "Differences from BOARD.md" and agree on voice
Contract change proposed: rating_probability/rating_impact, seeing, ranking on contributions; kind/text_fr/options on questions (see contracts/README.md)
Next: pulse flow polish + revise (version 2) against mocks
Blockers: contract freeze needs A+B OK
