# pitch/ (Lane C)

Everything for the 3-minute pitch on Sunday 8 November.

| What | Where |
|---|---|
| Slide deck (7 slides + 3 backup slides for questions) | https://claude.ai/artifact/LUYp9dww5VgcuRADFiZ6V2 (private until shared from its Share menu; download PDF/PPTX there) |
| Backup demo video (75 s, no sound) | [`backup-demo.mp4`](backup-demo.mp4) |
| Demo taps, fallbacks, likely jury questions | [`demo-script.md`](demo-script.md) |
| Project description for the submission form (under 5,000 characters, markdown) | [`description-form.md`](description-form.md) |
| Full project description (longer, for the repo) | [`submission.md`](submission.md) |

## Links

- Pitch site (demo data, no login): https://groundtruth-acaps.vercel.app
- Live site on the API (personal invites): https://groundtruth-acaps-live.vercel.app/#/?invite=inv_demo_02
- Moderator page (needs the moderator key): https://ground-truth-api.vercel.app/ui/moderator
- Repo: https://github.com/AkinCirak261884/hackathin

## Deck order

1. Cover · 2. Live demo (the 6 steps + QR code to the pitch site) · 3. What the moderator sees · 4. Does it work? (backtest) · 5. Trust and anonymity · 6. Roadmap · 7. Ready to pilot (QR code)
Backup: who sees what per anonymity level · when peer comments switch off · retention and scoring

## Before going on stage

- Download the deck as PDF onto the presenting laptop (works without wifi).
- Phone: open the pitch site, **Reset my answers (demo)**, EN, brightness up, Do Not Disturb on, auto-lock off.
- If possible, mirror the phone onto the same laptop that shows the slides (QuickTime → New Movie Recording → pick the iPhone, or iPhone Mirroring), so there's no switching between inputs.
- Keep `backup-demo.mp4` open in a player, ready to play if the phone or wifi fails.

## Screen sketches (built as stubs in `web/`)

```
 1. ROUND CARD / PULSE          2. GROUP REVEAL                 3. MY TRACK RECORD
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ Ground Truth     FR  │    │ The group view  n=7  │    │ My track record      │
│ Step 3 of 6  ▓▓▓░░░  │    │                      │    │  0.131               │
│ How likely before    │    │ Sustained attacks…   │    │  Brier · ACAPS 0.202 │
│ 6 May 2027?          │    │ |··[·●·]···  ·|      │    │                      │
│ ┌──────────────────┐ │    │  median 65% you 65%  │    │ Mali blockade unrest │
│ │Sustained cross-  │ │    │ Strategic infra…     │    │  you 80% · happened  │
│ │border attacks…   │ │    │ |·[··●]·  ·   |      │    │ Cameroon IDP attacks │
│ │ ○────────●──  65%│ │    │ Proxy mobilisation…  │    │  you 30% · didn't    │
│ └──────────────────┘ │    │ |  ·[·●··]· · |      │    │                      │
│ [Back]       [Next]  │    │ [Revise once]        │    │ ★ Your water-point   │
│ Rounds · Me · Public │    │ Rounds · Me · Public │    │   note was added     │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
 steps: rating → triggers → forecasts → top-3 → missing → anonymity tier (anon default)
