// One place for all data access. Mock mode (default) reads ../fixtures; set VITE_API_URL to use Lane B's API.
import roundsOpen from '@fixtures/rounds_open_TCD.json'
import round from '@fixtures/round_RD-R1043-1.json'
import aggregate from '@fixtures/aggregate_RD-R1043-1.json'
import postReply from '@fixtures/post_response_201.json'
import trackRecord from '@fixtures/me_track_record.json'
import publicSummaries from '@fixtures/public_summaries.json'
import { pct, r05 } from './stats.js'

const BASE = import.meta.env.VITE_API_URL
export const MOCK = !BASE

const clone = (v) => JSON.parse(JSON.stringify(v))
const delay = (v) => new Promise((r) => setTimeout(() => r(clone(v)), 120))

async function http(path, opts) {
  const res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...opts })
  if (!res.ok) throw Object.assign(new Error(`${res.status} ${path}`), { status: res.status })
  return res.json()
}

// ---- mock-only: remember the demo user's last submission so reveal + profile reflect it
const KEY = 'gt_submission'
export function lastSubmission() {
  try { return JSON.parse(localStorage.getItem(KEY)) } catch { return null }
}
function saveSubmission(roundId, body) {
  try { localStorage.setItem(KEY, JSON.stringify({ round_id: roundId, submitted_at: new Date().toISOString(), ...body })) } catch {}
}

// The demo user is Kestrel (E01). Swap Kestrel's fixture answers for what the user actually entered.
function personalise(agg, sub) {
  if (!sub) return agg
  const a = clone(agg)
  const byQ = Object.fromEntries(sub.answers.map((x) => [x.question_id, x]))
  for (const f of a.forecasts) {
    const mine = byQ[f.question_id]?.prob
    if (mine == null) continue
    const i = f.values.indexOf(r05(f.you))
    if (i >= 0) f.values.splice(i, 1, r05(mine))
    f.values.sort((x, y) => x - y)
    Object.assign(f, { you: mine, median: pct(f.values, 0.5), p25: pct(f.values, 0.25), p75: pct(f.values, 0.75) })
  }
  const rating = Object.values(byQ).find((x) => x.rating_probability)
  if (rating) {
    for (const dim of ['probability', 'impact']) {
      a.rating[dim][a.rating.you[dim]] -= 1
      a.rating.you[dim] = rating[`rating_${dim}`]
      a.rating[dim][a.rating.you[dim]] += 1
    }
  }
  const rank = Object.values(byQ).find((x) => x.ranking)
  if (rank) {
    const pts = Object.fromEntries(a.ranking.map((r) => [r.option_id, r]))
    a.rating.you.ranking.forEach((id, i) => { pts[id].points -= 3 - i; if (i === 0) pts[id].first_choice -= 1 })
    rank.ranking.forEach((id, i) => { pts[id].points += 3 - i; if (i === 0) pts[id].first_choice += 1 })
    a.rating.you.ranking = rank.ranking
    a.ranking.sort((x, y) => y.points - x.points)
  }
  return a
}

function personalTrackRecord(tr, sub) {
  if (!sub) return tr
  const t = clone(tr)
  const byQ = Object.fromEntries(sub.answers.map((x) => [x.question_id, x]))
  t.pending = t.pending.map((p) => ({ ...p, your_prob: byQ[p.question_id]?.prob ?? p.your_prob, submitted_at: sub.submitted_at }))
  return t
}

export const api = {
  openRounds: (panel = 'TCD') =>
    MOCK ? delay(roundsOpen.map((r) => ({ ...r, answered: lastSubmission()?.round_id === r.round_id }))) : http(`/rounds/open?panel=${panel}`),
  round: (id) => (MOCK ? delay(round) : http(`/rounds/${id}`)),
  submit: (id, body) =>
    MOCK ? (saveSubmission(id, body), delay({ ...postReply, version: body.version }))
      : http(`/rounds/${id}/responses`, { method: 'POST', body: JSON.stringify(body) }),
  aggregate: (id, token) =>
    MOCK ? delay(personalise(aggregate, lastSubmission())) : http(`/rounds/${id}/aggregate?token=${encodeURIComponent(token)}`),
  trackRecord: (token) =>
    MOCK ? delay(personalTrackRecord(trackRecord, lastSubmission())) : http(`/me/track-record?token=${encodeURIComponent(token)}`),
  publicSummaries: () => (MOCK ? delay(publicSummaries) : http('/public/summaries')),
}

// Demo identity: in the real app this comes from the invite link (?invite=…).
export const DEMO_INVITE = 'inv_demo'
export const DEMO_TOKEN = 'E01'
export const DEMO_PSEUDONYM = 'Kestrel'

const randomHex = () => [...crypto.getRandomValues(new Uint8Array(32))].map((b) => b.toString(16).padStart(2, '0')).join('')

// Anonymous tier: device-held secret, server only ever sees sha256(secret).
export async function anonToken() {
  let secret
  try {
    secret = localStorage.getItem('gt_device_secret')
    if (!secret) { secret = randomHex(); localStorage.setItem('gt_device_secret', secret) }
  } catch { secret = randomHex() }
  if (!crypto.subtle) return 'anon_insecure_context_demo' // plain-HTTP LAN testing; real deploy is HTTPS
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(secret))
  return 'anon_' + [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
