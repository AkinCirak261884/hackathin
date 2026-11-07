# Lane C — expert app & pitch

Folders: `web/`, `pitch/`. Don't edit `contracts/`, `api/`, `analysis/`, `moderator/`.

## Tasks

- [x] **Pick the web stack + sketch 3 screens.** Round card, group reveal, my track record. *Done when:* stack is written in BOARD.md decisions (after voice agreement) and sketches are in `pitch/`.
- [x] **Pulse flow against mocks.** Rating agree/disagree, triggers "I'm seeing this", what's missing, forecast slider; one screen per step, mobile-first. *Done when:* the full flow runs on a phone against `fixtures/`.
- [x] **Anonymity tier picker.** 3 tiers, most protective by default, changeable per answer. *Done when:* the chosen tier is sent with each response.
- [ ] **Group reveal + revise.** Unlocks only after own submit; distribution, not just an average; one revision. *Done when:* works against mock `/aggregate`.
- [x] **Track record + public page + signpost screen.** *Done when:* all three pages render from mocks.
- [ ] **EN/FR toggle + pitch.** *Done when:* strings switch language; pitch draft and demo script in `pitch/` by Sat evening.

## Latest update

### Lane C — update #6 — 14:09
Done: flat CLO-style theme (no gradients, small radii, hover only on clickable items). Profile record + accuracy cards open #/record and #/accuracy; every forecast opens #/guess/<id> with you vs ACAPS vs outcome and the Brier maths. Accuracy page: compare with ACAPS or panel middle. Home: "Latest ACAPS risks" for Chad/Sudan via api.acapsRisks() (CSV snapshot for now). "How ACAPS used your input" explained. All EN/FR.
Pushed: lane-c | PR: https://github.com/AkinCirak261884/hackathin/pull/1
How to see it: cd web && npm run dev → My profile → click a card; Check-ins → scroll to ACAPS risks
Requests to other lanes: →A: group_median_prob / group_brier / beat_group per track-record history item. →B: GET /acaps/risks?panel=TCD proxy, token server-side only (both in BOARD.md)
Contract change proposed: optional history.group_median_prob in track-record.schema.json
Next: pitch draft + demo script in pitch/
Blockers: ACAPS API account/token needed for B's proxy
