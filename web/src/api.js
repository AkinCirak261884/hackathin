// One place for all data access. Mock mode (default) reads ../fixtures; set VITE_API_URL to use Lane B's API.
import roundsOpen from '@fixtures/rounds_open_TCD.json'
import round from '@fixtures/round_RD-R1043-1.json'
import aggregate from '@fixtures/aggregate_RD-R1043-1.json'
import practiceRound from '@fixtures/round_RD-R0993-P.json'
import practiceAggregate from '@fixtures/aggregate_RD-R0993-P.json'
import postReply from '@fixtures/post_response_201.json'
import trackRecord from '@fixtures/me_track_record.json'
import trackRecordNew from '@fixtures/me_track_record_new.json'
import publicSummaries from '@fixtures/public_summaries.json'
import acapsRisksTCD from './mock/acaps_risks_TCD.json' // snapshot from the CSV until Lane B's /acaps/risks exists
import { pct, r05, recordSummary } from './stats.js'

const BASE = import.meta.env.VITE_API_URL
export const MOCK = !BASE

const clone = (v) => JSON.parse(JSON.stringify(v))
const ROUNDS = { [round.round_id]: round, [practiceRound.round_id]: practiceRound }
const AGGS = { [aggregate.round_id]: aggregate, [practiceAggregate.round_id]: practiceAggregate }
const MAIN_ROUND = round.round_id
export const MAIN_ROUND_ID = MAIN_ROUND
export const PRACTICE_ROUND_ID = practiceRound.round_id
const delay = (v) => new Promise((r) => setTimeout(() => r(clone(v)), 120))
// Secrets travel in headers, never in the URL (URLs end up in server logs and browser history). Matches Lane B's API.
// X-Device-Secret carries the phone-side hash (see deviceKey), only once this device has answered anonymously.
const auth = async () => {
  const headers = { 'X-Invite-Token': inviteToken() }
  if (hasDeviceSecret()) headers['X-Device-Secret'] = await deviceKey()
  return { headers }
}
const get = (path) => auth().then((o) => http(path, o))

async function http(path, opts = {}) {
  const res = await fetch(BASE + path, { ...opts, headers: { 'Content-Type': 'application/json', ...opts.headers } })
  if (!res.ok) throw Object.assign(new Error(`${res.status} ${path}`), { status: res.status })
  return res.json()
}

// ---- mock-only: remember the demo user's submissions, one per round, so reveal + profile reflect them
const KEY = 'gt_submissions'
function allSubmissions() {
  try { return JSON.parse(localStorage.getItem(KEY)) || {} } catch { return {} }
}
export function lastSubmission(roundId = MAIN_ROUND) {
  return allSubmissions()[roundId] || null
}
export const hasAnySubmission = () => Object.keys(allSubmissions()).length > 0
// TEMPORARY demo helper: forget this browser's answers so the survey can be taken again
export function resetDemoAnswers() {
  try { ['gt_submissions', 'gt_submission', 'gt_forecast_updates', 'gt_revisions'].forEach((k) => localStorage.removeItem(k)) } catch {}
}
// Delphi step 2 (option B): after reading peer reasons the expert either keeps their answers or revises once.
// Kept in this browser in both modes so the reveal knows whether to show the numbers yet.
const REV_KEY = 'gt_revisions'
function allRevisions() {
  try { return JSON.parse(localStorage.getItem(REV_KEY)) || {} } catch { return {} }
}
export const revisionOf = (roundId) => allRevisions()[roundId] || null
function saveRevision(roundId, rev) {
  const all = allRevisions()
  all[roundId] = { round_id: roundId, decided_at: new Date().toISOString(), ...rev }
  try { localStorage.setItem(REV_KEY, JSON.stringify(all)) } catch {}
}
// blind answers with the revised probabilities laid over them: what the group view should show as "you"
function latestSubmission(roundId) {
  const sub = lastSubmission(roundId), rev = revisionOf(roundId)
  if (!sub || rev?.decision !== 'revised') return sub
  const p = Object.fromEntries(rev.answers.map((x) => [x.question_id, x.prob]))
  return { ...sub, answers: sub.answers.map((x) => (p[x.question_id] != null ? { ...x, prob: p[x.question_id] } : x)) }
}

function saveSubmission(roundId, body) {
  const all = allSubmissions()
  all[roundId] = { round_id: roundId, submitted_at: new Date().toISOString(), ...body }
  try { localStorage.setItem(KEY, JSON.stringify(all)) } catch {}
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
  if (rank && a.ranking.length) {
    const pts = Object.fromEntries(a.ranking.map((r) => [r.option_id, r]))
    a.rating.you.ranking.forEach((id, i) => { pts[id].points -= 3 - i; if (i === 0) pts[id].first_choice -= 1 })
    rank.ranking.forEach((id, i) => { pts[id].points += 3 - i; if (i === 0) pts[id].first_choice += 1 })
    a.rating.you.ranking = rank.ranking
    a.ranking.sort((x, y) => y.points - x.points)
  }
  // your own comment: swap Kestrel's fixture comment for what you wrote (or drop it if you wrote nothing)
  // your record next to your comment = the same live record as the profile (includes practice results)
  const live = recordSummary(personalTrackRecord(trackRecord, lastSubmission()).history)
  a.comments = (a.comments || []).filter((c) => !c.is_you)
  if (sub.reasoning_text) {
    const anon = sub.tier === 'anonymous'
    a.comments.unshift({
      comment_id: 'CM-YOU', display_name: anon ? 'Anonymous expert' : DEMO_PSEUDONYM, tier: sub.tier,
      text: sub.reasoning_text, basis: sub.reasoning_basis, is_you: true,
      record: anon ? null : { correct: live.correct, resolved: live.total },
      forecasts: anon ? null : Object.fromEntries(sub.answers.filter((x) => x.prob != null).map((x) => [x.question_id, x.prob])),
    })
  }
  return a
}

// MOCK ONLY: panel middle answer per resolved question, until Lane A adds group_median_prob to history
// (requested in BOARD.md). Synthetic, like all fixture data. The practice question uses its real aggregate.
const DEMO_GROUP_MEDIAN = { R1014: 0.7, R0094: 0.4, R0248: 0.7, R1028: 0.3, R0073: 0.4, R0301: 0.75, R0089: 0.45, R0002: 0.7,
  R0120: 0.55, R0242: 0.45 }
function withGroup(h) {
  if (h.group_median_prob != null) return h
  const g = h.practice ? practiceAggregate.forecasts.find((f) => f.question_id === h.question_id)?.median : DEMO_GROUP_MEDIAN[h.risk_id]
  if (g == null) return h
  const gb = +((g - h.outcome) ** 2).toFixed(4)
  return { ...h, group_median_prob: g, group_brier: gb, beat_group: h.brier < gb }
}

function personalTrackRecord(tr, sub) {
  const practice = lastSubmission(practiceRound.round_id)
  if (!sub && !practice) return tr
  const t = clone(tr)
  if (sub) {
    const byQ = Object.fromEntries(sub.answers.map((x) => [x.question_id, x]))
    const rev = revisionOf(MAIN_ROUND)
    const revP = rev?.decision === 'revised' ? Object.fromEntries(rev.answers.map((x) => [x.question_id, x.prob])) : {}
    t.pending = t.pending.map((p) => ({ ...p, your_prob: byQ[p.question_id]?.prob ?? p.your_prob, submitted_at: sub.submitted_at,
      revised_prob: revP[p.question_id] ?? null }))
  }
  // practice round answered: score it like any resolved forecast and add it to the record
  if (practice) {
    for (const q of practiceRound.questions.filter((x) => x.kind === 'forecast')) {
      const p = practice.answers.find((x) => x.question_id === q.question_id)?.prob
      if (p == null) continue
      const o = q.outcome ? 1 : 0
      const b = +((p - o) ** 2).toFixed(4), ab = +((q.acaps_baseline - o) ** 2).toFixed(4)
      t.history.unshift({ question_id: q.question_id, risk_id: q.risk_id, text: `${q.text} (Ukraine, practice)`, closes_at: q.closes_at,
        outcome: o, outcome_label: o ? 'happened' : "didn't happen", your_prob: p, brier: b,
        acaps_prob: q.acaps_baseline, acaps_brier: ab, beat_acaps: b < ab, practice: true, round_id: practiceRound.round_id })
    }
    const h = t.history, n = h.length
    t.n_resolved = n
    t.mean_brier = +(h.reduce((s, x) => s + x.brier, 0) / n).toFixed(4)
    t.acaps_baseline_brier = t.acaps_brier_same_questions = +(h.reduce((s, x) => s + x.acaps_brier, 0) / n).toFixed(4)
    t.n_beat_acaps = h.filter((x) => x.beat_acaps).length
    t.super_estimator = n >= t.min_resolved && t.mean_brier < t.acaps_baseline_brier
    t.forecasts_until_counted = Math.max(0, t.min_resolved - n)
  }
  return t
}

// ---------------------------------------------------------------- Lane B API adapters (real mode only)
// The screens keep the fixture shapes (contracts/); these map Lane B's responses onto them.
// See status/A.md "Web ↔ API mismatches" W1–W16 for the list this closes.
const fromApi = {
  // W2: { panel, rounds: [{ risk_title, you_submitted, n_questions }] } → array of round cards
  openRounds: (r) => (r.rounds || []).map((x) => ({
    round_id: x.round_id, risk_id: x.risk_id, title: x.risk_title, stage: x.stage, closes_at: x.closes_at || null,
    est_minutes: Math.max(2, x.n_questions || 3), answered: !!x.you_submitted || !!lastSubmission(x.round_id),
  })),
  // W3/W4: top-level triggers + risk_title; the API's yes/no "agree" item is shown as the rating step
  round: (r) => {
    const trig = Object.fromEntries((r.triggers || []).map((t) => [t.trigger_id, t]))
    return {
      ...r,
      risk: { ...r.risk, title: r.risk_title, triggers: r.triggers || [] },
      questions: r.questions.map((q) => (q.kind === 'agree'
        ? { ...q, kind: 'rating', api_kind: 'agree', title: q.title || 'ACAPS rating', title_fr: q.title_fr || 'Évaluation ACAPS' }
        : { ...q, title: q.title || trig[q.trigger_id]?.title || null })),
    }
  },
  // W10/W11: /thread → group view. Locked until the moderator opens the reveal; peers see approved themes, not replies.
  aggregate: (a) => {
    if (a.locked) return { locked: true, stage: a.stage, round_id: a.round_id }
    if (a.suppressed) return { suppressed: true }
    const qs = a.questions || [], mine = a.your_answers || {}
    const agreeQ = qs.find((q) => q.agree_share != null)
    return {
      round_id: a.round_id, n_responses: Math.max(0, ...qs.map((q) => q.n || 0)), can_revise: a.can_revise,
      rating: null,
      agree: agreeQ ? { share: agreeQ.agree_share, n: agreeQ.n, you: mine[agreeQ.question_id] } : null,
      forecasts: qs.filter((q) => q.dots).map((q) => ({
        question_id: q.question_id, values: [...q.dots].sort((x, y) => x - y), median: q.median, p25: q.p25, p75: q.p75, n: q.n,
        you: mine[q.question_id] ?? null,
      })),
      ranking: [],
      comments: (a.themes || []).map((th, i) => ({ comment_id: `theme-${i}`, is_theme: true, tier: 'anonymous', text: th.text })),
    }
  },
  trackRecord: (tr) => ({ ...tr, history: tr.history || [], pending: tr.pending || [], impact: tr.impact || [] }),
  // W14: { summaries: [{ n, agree_share, questions, approved_text }] } → public cards
  publicSummaries: (r) => (r.summaries || []).map((x) => ({
    round_id: x.round_id, risk_id: x.risk_id, published_at: x.published_at, n_responses: x.n,
    headline: x.headline || null, summary_text: x.approved_text, agree_share: x.agree_share,
    forecasts: (x.questions || []).map((q) => ({ question_id: q.question_id, text: q.text || null, median: q.median, n: q.n })),
  })),
}

// Web response body → Lane B's ResponseIn. W5: 3-way rating collapses to agree = both "about right";
// top-3 ranking isn't stored by the API yet. W6: lists, never null. W7: device_secret = the phone-side hash.
async function toApiResponse(body) {
  const answers = [], triggers = []
  for (const x of body.answers) {
    if (x.rating_probability !== undefined) answers.push({ question_id: x.question_id, agree: x.rating_probability === 'agree' && x.rating_impact === 'agree' })
    else if (x.prob != null) answers.push({ question_id: x.question_id, prob: x.prob })
    if (x.seeing) { const m = /-(T\d+)$/.exec(x.question_id); if (m) triggers.push(m[1]) }
  }
  const out = {
    invite_token: body.invite_token, tier: body.tier, version: body.version, answers, triggers_observed: triggers,
    missing_text: body.missing_text ?? null, reasoning_text: body.reasoning_text ?? null, reasoning_basis: body.reasoning_basis || [],
  }
  if (body.tier === 'anonymous') out.device_secret = await deviceKey()
  return out
}
const postResponse = async (id, body) => http(`/rounds/${id}/responses`, { method: 'POST', body: JSON.stringify(await toApiResponse(body)) })

export const api = {
  openRounds: (panel = 'TCD') =>
    MOCK ? delay(roundsOpen.map((r) => ({ ...r, answered: !!lastSubmission(r.round_id) }))) : get(`/rounds/open?panel=${panel}`).then(fromApi.openRounds),
  round: (id) => (MOCK ? delay(ROUNDS[id] || round) : http(`/rounds/${id}`).then(fromApi.round)),
  // the first answer is also kept in this browser (both modes): step 2 and "Check my answers" read it
  submit: async (id, body) => {
    const reply = MOCK ? await delay({ ...postReply, version: body.version }) : await postResponse(id, body)
    saveSubmission(id, body)
    return reply
  },
  aggregate: (id, token) =>
    MOCK ? delay(personalise(AGGS[id] || aggregate, latestSubmission(id))) : get(`/rounds/${id}/thread`).then(fromApi.aggregate)
        .catch((e) => (e.status === 403 ? { mustAnswer: true } : Promise.reject(e))),
  // keep = no second version; revise = POST version 2 with only the changed forecasts + "what changed your mind?"
  keepAnswers: async (id) => { saveRevision(id, { decision: 'kept' }) },
  revise: async (id, { answers, reason }) => {
    const first = lastSubmission(id)
    const body = { invite_token: inviteToken(), tier: first?.tier || 'pseudonymous', version: 2, reasoning_text: reason || null, reasoning_basis: [], answers }
    if (MOCK) { if (body.tier === 'anonymous') body.anon_token = await anonToken() } else await postResponse(id, body)
    saveRevision(id, { decision: 'revised', answers, reason: reason || null })
  },
  // mock: add ?new=1 to the URL hash to see a new expert who is not ranked yet
  trackRecord: (token) =>
    MOCK ? delay(withGroups(personalTrackRecord(isNewcomerDemo() ? trackRecordNew : trackRecord, lastSubmission())))
      : get('/me/track-record').then(fromApi.trackRecord),
  publicSummaries: () => (MOCK ? delay(publicSummaries) : http('/public/summaries').then(fromApi.publicSummaries)),
  // Latest published ACAPS risks for a panel. Lane B proxies the ACAPS API server-side (token never reaches the browser).
  // Shape: { source: 'live' | 'snapshot', panel, updated_at?, risks: [{ risk_id, title, country, probability, impact, risk_level, trend, ... }] }
  acapsRisks: (panel = 'TCD') =>
    MOCK ? delay(acapsRisksTCD) : http(`/acaps/risks?panel=${panel}`).catch(() => clone(acapsRisksTCD)),
}

const withGroups = (tr) => ({ ...tr, history: tr.history.map(withGroup) })
const isNewcomerDemo = () => window.location.hash.includes('new=1')

// Demo identity: in the real app this comes from the invite link (?invite=…).
export const DEMO_INVITE = 'inv_demo_01' // Lane B seeds inv_demo_01 … inv_demo_08

// Personal invite links: https://…/#/?invite=inv_demo_02 (preferred: the part after # is never sent to the
// server, so the token stays out of hosting logs) or ?invite=… (removed from the address bar on load).
// The invite is remembered in this browser; opening a link with a different invite starts fresh.
const INVITE_KEY = 'gt_invite'
const INVITE_RE = /^[A-Za-z0-9_-]{4,64}$/
function readInviteFromUrl() {
  try {
    const url = new URL(window.location.href)
    const hashQuery = new URLSearchParams(url.hash.split('?')[1] || '')
    const invite = url.searchParams.get('invite') || hashQuery.get('invite')
    if (!invite || !INVITE_RE.test(invite)) return
    const previous = localStorage.getItem(INVITE_KEY)
    if (previous && previous !== invite) { // another expert on this browser: don't mix answers or anonymous identity
      resetDemoAnswers()
      localStorage.removeItem('gt_device_secret')
    }
    localStorage.setItem(INVITE_KEY, invite)
    url.searchParams.delete('invite')
    hashQuery.delete('invite')
    const rest = hashQuery.toString()
    url.hash = url.hash.split('?')[0] + (rest ? `?${rest}` : '')
    window.history.replaceState(null, '', url.toString())
  } catch { /* no window (tests) or storage blocked: fall back to the demo invite */ }
}
readInviteFromUrl()
export function inviteToken() {
  try { return localStorage.getItem(INVITE_KEY) || DEMO_INVITE } catch { return DEMO_INVITE }
}
export const DEMO_TOKEN = 'E01'
export const DEMO_PSEUDONYM = 'Kestrel'
// Demo mode only: on the API the profile doesn't know the expert's pseudonym, so it shows none
export const demoPseudonym = () => (!MOCK ? null : isNewcomerDemo() ? 'Alder' : DEMO_PSEUDONYM)

const randomHex = () => [...crypto.getRandomValues(new Uint8Array(32))].map((b) => b.toString(16).padStart(2, '0')).join('')

// Anonymous tier: device-held secret, server only ever sees sha256(secret).
// The raw secret never leaves the phone: only sha256(secret) is sent (as the API's device_secret / X-Device-Secret),
// and the server derives its anon token from that. Same value every time on this device, so the record is stable.
const hasDeviceSecret = () => { try { return !!localStorage.getItem('gt_device_secret') } catch { return false } }
export async function deviceKey() {
  let secret
  try {
    secret = localStorage.getItem('gt_device_secret')
    if (!secret) { secret = randomHex(); localStorage.setItem('gt_device_secret', secret) }
  } catch { secret = randomHex() }
  if (!crypto.subtle) return 'insecure_context_demo_key' // plain-HTTP LAN testing; real deploy is HTTPS
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(secret))
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
export async function anonToken() {
  return 'anon_' + (await deviceKey())
}
