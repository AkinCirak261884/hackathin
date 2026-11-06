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

### Lane C — update #3 — 19:09
Done: Lane A's 3 requests. Profile now uses A's track-record shape (super-estimator badge, rank "#3 of 7", "N more forecasts until your score counts", beat-ACAPS per question with ACAPS marker), new panel leaderboard (A's shape), ACAPS midpoint mapping (5/22/50/78/95) in fixtures + contracts. "Check my answers" replaces revise.
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm run dev → #/me (and #/me?new=1 for a not-yet-ranked expert)
Requests to other lanes: →B: serve GET /leaderboard (contracts/schemas/leaderboard.schema.json) and /me/track-record in A's shape + pending + impact. →A+B: align IDs/tokens (RD- vs RND-, E01 vs psd_EXP-TCD-01) on voice
Contract change proposed: midpoint mapping; /leaderboard; track-record = A's shape (history[]). See contracts/README.md
Next: switch web/src/api.js to B's real API once IDs/auth are agreed
Blockers: contract freeze needs A+B OK
