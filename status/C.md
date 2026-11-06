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

### Lane C — update #4 — 19:37
Done: Peer comments on the results page ("why I think this"), each with the commenter's record ("7 of 8 correct · 88%") and their guesses; anonymous comments show no record/guesses. Leaderboard + rank removed from the app (team decision). Step 6 privacy note updated. Temporary "Reset my answers (demo)" button on Home.
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm run dev → answer the R1043 check-in → results page, "Comments from the panel"
Requests to other lanes: →B: add `comments[]` to /aggregate (contracts/schemas/aggregate.schema.json, invariant 1b): reasoning_text to peers only after own submit and n≥3, pseudonym or "Anonymous expert", no record/forecasts for anonymous. →A: per-expert correct/resolved count for the comment record (or I compute it from history[])
Contract change proposed: aggregate.comments + invariant 1b; /leaderboard removed (contracts/README.md)
Next: switch web/src/api.js to B's real API once IDs/auth are agreed
Blockers: contract freeze needs A+B OK
