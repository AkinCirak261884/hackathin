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

### Lane C — update #9 — 16:58
Done: hosted the stack (see BOARD integration log): live site on the API + Supabase with personal invite links; Supabase/Postgres port of the API (PR #3 for B, 111/111 tests on Postgres, moderator key on /moderator/*). Peers no longer see track records (agreed with B). Clear error pages instead of endless loading. Checked every page of both sites in headless Chrome.
Pushed: lane-c, merged to main (PRs #4, #5) | PR #3 open for B
How to see it: https://groundtruth-acaps.vercel.app (pitch) · https://groundtruth-acaps-live.vercel.app/#/?invite=inv_demo_02 (live)
Requests to other lanes: →B: review PR #3; remove or lock GET /leaderboard. →A/B: confirm v1 (blind) is the scored version
Contract change proposed: none
Next: backup demo video; moderator slide
Blockers: none
