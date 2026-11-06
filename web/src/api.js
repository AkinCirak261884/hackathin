// One place for all data access. Mock mode (default) reads ../fixtures; set VITE_API_URL to use Lane B's API.
import roundsOpen from '@fixtures/rounds_open_TCD.json'
import round from '@fixtures/round_RD-R1043-1.json'
import aggregate from '@fixtures/aggregate_RD-R1043-1.json'
import postReply from '@fixtures/post_response_201.json'
import trackRecord from '@fixtures/me_track_record.json'
import publicSummaries from '@fixtures/public_summaries.json'

const BASE = import.meta.env.VITE_API_URL
export const MOCK = !BASE

const delay = (v) => new Promise((r) => setTimeout(() => r(structuredClone(v)), 150))

async function http(path, opts) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) throw Object.assign(new Error(`${res.status} ${path}`), { status: res.status })
  return res.json()
}

export const api = {
  openRounds: (panel = 'TCD') => (MOCK ? delay(roundsOpen) : http(`/rounds/open?panel=${panel}`)),
  round: (id) => (MOCK ? delay(round) : http(`/rounds/${id}`)),
  submit: (id, body) =>
    MOCK
      ? (console.info('[mock] POST response', body), delay({ ...postReply, version: body.version }))
      : http(`/rounds/${id}/responses`, { method: 'POST', body: JSON.stringify(body) }),
  aggregate: (id, token) => (MOCK ? delay(aggregate) : http(`/rounds/${id}/aggregate?token=${encodeURIComponent(token)}`)),
  trackRecord: (token) => (MOCK ? delay(trackRecord) : http(`/me/track-record?token=${encodeURIComponent(token)}`)),
  publicSummaries: () => (MOCK ? delay(publicSummaries) : http('/public/summaries')),
}

// Demo identity: in the real app this comes from the invite link (?invite=…).
export const DEMO_INVITE = 'inv_' // filled from fixtures/experts.json by Lane B; mock ignores it
export const DEMO_TOKEN = 'E01'

// Anonymous tier: device-held secret, server only ever sees sha256(secret).
export async function anonToken() {
  let secret
  try {
    secret = localStorage.getItem('gt_device_secret')
    if (!secret) {
      secret = crypto.randomUUID()
      localStorage.setItem('gt_device_secret', secret)
    }
  } catch {
    secret = crypto.randomUUID()
  }
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(secret))
  return 'anon_' + [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
