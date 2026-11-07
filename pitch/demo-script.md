# Demo script: 3 minutes

**Story:** one field expert in eastern Chad does this month's check-in on R1043 (cross-border insecurity from the Sudan conflict), learns from the panel without being swayed by it, and sees whether their judgement holds up.

**Link:** https://groundtruth-acaps.vercel.app (demo data, no login, works offline once loaded)

## Roles

| Who | Does |
|---|---|
| **Presenter** | Talks. Never touches the phone. |
| **Driver** | Holds the phone (mirrored to the screen) and taps exactly the steps below. Says nothing. |
| **Backup** | Laptop with the same link open and the backup video ready. Takes over if the phone fails. |

## Before going on stage (5 min)

1. Phone: open the link, **Check-ins** tab, tap **Reset my answers (demo)** if it shows. Language **EN**. Screen brightness up, Do Not Disturb on, auto-lock off.
2. Mirror the phone (cable or AirPlay) and check it on the projector. Zoom the browser so text is readable from the back.
3. Laptop: same link in a second tab, already on **My profile**; backup video at `pitch/backup-demo.mp4` (record it Saturday night, see the end of this file).
4. Do one dry run, then reset again.

## Script

Spoken lines are in quotes. Taps are for the Driver. Timings are cumulative.

### 0:00–0:20 · Hook (no phone)

> "When a crisis is about to shift, the first people to notice are local staff, NGO workers, community contacts. Today that knowledge stays in WhatsApp groups and never reaches the analysis. ACAPS asked us: how do you tap a small, trusted panel, safely, in a few minutes a month, and know whose judgement to trust?"

### 0:20–1:35 · Live demo (phone)

| Time | Driver taps | Presenter says |
|---|---|---|
| 0:20 | **Check-ins** is on screen. Scroll a little to show **Latest ACAPS risks** under the cards, then back up. Tap **Start** on the Chad card. | "This is the expert's view. One check-in a month on a real ACAPS risk: R1043, eastern Chad. Below it, what ACAPS currently flags in the area." |
| 0:30 | **Is ACAPS's rating right?** Probability: **About right**. Impact: **Too low**. **Next**. | "First: is ACAPS's own rating right? One tap each." |
| 0:37 | **What are you seeing on the ground?** Tick **Expansion of cross-border attacks**. **Next**. | "Which of ACAPS's warning signs are they actually seeing?" |
| 0:42 | **How likely is each of these?** Tap presets **70%**, **10%**, **50%**. **Next**. | "Then a probability for each trigger, before a deadline, so we can score it later." |
| 0:50 | **Top 3 risks for Chad**: tap the first three options. **Next**. **What is ACAPS missing?**: **Next** (leave empty). | |
| 0:55 | **Your answers, and why**: tick **What I see myself**. **Next**. | "What is it based on: seeing it themselves, contacts, media." |
| 1:00 | **Who can see this answer?**: leave **Fully anonymous** selected. Tap **Submit answers**. | "And who can see it. Fully anonymous is the default: not even ACAPS can link this answer to them. That's the only way some of these people can take part." |
| 1:07 | **Step 2: Why others answered the way they did.** Scroll slowly through 2–3 comments (Adré water points, drones in French). | "Here's our key idea. Before seeing anyone's numbers, they read the panel's *reasons*. No averages, no majority to follow. Just arguments: water-point incidents in Adré, drones near the border every night." |
| 1:17 | Tap **Update my forecast**. Drag **Attacks on strategic infrastructure** from 10% to **35%**. Tap **Save update and see the group**. | "The drone report changes this expert's mind, so they update once. Their blind answer is still the one that's scored, so copying the group can't help anyone's record." |
| 1:25 | Group view: point at the dots chart for the first trigger. | "Only now do the numbers unlock: every answer as a dot, theirs in orange, the middle half shaded." |
| 1:30 | Tap **My profile**. Show the record card (x of y correct) and the accuracy card. | "Over time every expert builds a track record against ACAPS's own rating. That's how ACAPS learns whose judgement to trust." |

### 1:35–2:00 · What ACAPS gets (slide)

> "On ACAPS's side, a moderator sees how far each answer moved after the reasons step, where the panel disagrees with the rating, and what experts say is missing, clustered by AI and checked by a person before anything is published. The public page only ever shows group results, and nothing at all below 3 responses."

Slide: moderator view (screenshot from Lane A/B, or the `fixtures/moderator_round_RD-R1043-1.json` numbers as a chart).

### 2:00–2:25 · Does it work? (slide, Lane A numbers)

> "Does it work? We scored ACAPS's own ratings on 99 risks that have already resolved. Turned into probabilities, they score a Brier of 0.213. Simply saying 61%, the base rate, every time scores 0.239. So ACAPS's ratings are better than guessing, but there's a lot of room. That gap is what a panel of people on the ground can close, and our scoring measures it per expert, on the same questions."

Slide: calibration chart (`analysis/charts/calibration.svg`) + the two numbers. Say clearly that the expert panel in the demo is synthetic.

### 2:25–2:45 · Trust (slide)

> "Trust is built in: invite-only, three anonymity levels chosen per answer, names kept in a separate vault, no IP addresses logged, nothing published below 3 responses and no quotes. And people who have witnessed abuses aren't asked to report here: we point them to the ICC and eyeWitness."

### 2:45–3:00 · Close (no phone)

> "Three minutes a month, in English or French, on their phone. Experts see their record grow and see when ACAPS used their input. ACAPS gets ground truth it can weigh. It's live now at groundtruth-acaps.vercel.app, and it's ready to pilot with the Chad panel."

## If something breaks

| Problem | Do |
|---|---|
| Phone mirroring fails | Backup switches to the laptop tab and drives the same steps. |
| No internet | The page works once loaded. If it never loaded, play the backup video. |
| Reveal opens without step 2 | Answers from the dry run are still saved: go to **Check-ins**, **Reset my answers (demo)**, start again from the Chad card. If short on time, skip to **My profile**. |
| Running long at 1:30 | Skip **My profile**; the presenter says the track-record line over the group view. |

## Likely judge questions

- **"Won't people just copy the group?"** They read reasons before numbers, can change their answer only once, and the blind answer is the one that's scored. Both answers are stored, so ACAPS can see if the group herded.
- **"How anonymous is anonymous?"** The anonymous level uses a one-way hash of a secret on the expert's phone; names live in a separate database that only the moderator side can open, and only for experts who chose to be known.
- **"Why would busy experts come back?"** It takes about 3 minutes, they get a track record and a super estimator badge, and they see when their input changed ACAPS's analysis.
- **"Doesn't scoring put pressure on experts?"** Each expert sees only their own record, privately; peers never see anyone's record, and there's no public leaderboard. ACAPS's moderator sees all records to weigh views. Scores only count after 5 resolved forecasts.
- **"Is the accuracy real?"** ACAPS's baseline (0.213 on 99 resolved risks) is real data. The expert panel in the demo is synthetic; the pilot is what measures real experts.
- **"What about Arabic?"** Next language: it covers about a third of ACAPS risks, including the rest of the Chad panel. Adding a language is one more set of texts.

## Backup video (record Saturday night)

1. Reset the demo, start a screen recording on the phone.
2. Do the 0:20–1:35 taps exactly as above, at a calm pace (about 75 seconds).
3. Save as `pitch/backup-demo.mp4` (or a shared drive link if it's over 50 MB) and copy it to the Backup's laptop.
