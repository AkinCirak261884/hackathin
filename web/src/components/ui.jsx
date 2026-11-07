import React from 'react'
import { useT } from '../i18n.jsx'

// Section heading with a subtitle, used everywhere so nothing reads as plain text.
export function Head({ eyebrow, title, sub, level = 2 }) {
  const H = `h${level}`
  return (
    <header className="head">
      {eyebrow && <div className="eyebrow">{eyebrow}</div>}
      <H>{title}</H>
      {sub && <p className="sub">{sub}</p>}
    </header>
  )
}

export function Chip({ children, tone }) {
  return <span className={`chip ${tone || ''}`}>{children}</span>
}

// Simple line icons (no emoji): check, cross, dash, up, down. Decorative; pair with text or aria-label.
const PATHS = { check: 'M5 12.5l4.5 4.5L19 7.5', cross: 'M6.5 6.5l11 11M17.5 6.5l-11 11', dash: 'M6 12h12',
  up: 'M12 19V5M6 11l6-6 6 6', down: 'M12 5v14M6 13l6 6 6-6' }
export function Icon({ name, size = 16 }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d={PATHS[name]} /></svg>
  )
}

// Shown instead of endless loading dots when a request fails (offline, server down, refused).
export function LoadError({ error }) {
  const { t } = useT()
  const offline = !error?.status
  return (
    <section className="page">
      <Head level={1} title={t('err_title')} sub={offline ? t('err_offline') : t('err_server', error.status)} />
      <button className="btn ghost" onClick={() => window.location.reload()}>{t('err_retry')}</button>
    </section>
  )
}

// Peer comments on/off for this round (OCHA 3W operational presence via HDX). On: one quiet line with the source.
// Off: a card explaining that with few organisations in the area, comments can't be cross-checked and are easier
// to trace back, so what experts write goes to the ACAPS moderator only.
export function CommentsPolicyLine({ policy }) {
  const { t, date } = useT()
  if (!policy) return null
  const where = policy.areas?.length ? policy.areas.join(', ') : t('cp_country')
  const sources = (policy.sources || (policy.source ? [policy.source] : [])).filter((s) => s.url)
  const src = sources.length > 0 && (
    <> · {sources.map((s, i) => (
      <React.Fragment key={s.url}>{i > 0 && ', '}<a href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a>{s.as_of ? ` (${date(s.as_of)})` : ''}</React.Fragment>
    ))}</>
  )
  if (policy.enabled) return <p className="muted small cp-line">{t('cp_on', policy.n_orgs, where, policy.people)}{src}</p>
  const why = {
    small_place: () => t('cp_off_place', policy.place?.type, policy.place?.name),
    few_people: () => t('cp_off_people', policy.people, policy.min_people),
    few_orgs: () => t('cp_off', policy.n_orgs, where, policy.min_orgs),
    moderator: () => t('cp_off_moderator'),
  }[policy.basis] || (() => (policy.n_orgs == null ? t('cp_off_nodata') : t('cp_off', policy.n_orgs, where, policy.min_orgs)))
  return (
    <div className="card cp-off" role="note">
      <b>{t('cp_off_title')}</b>
      <p className="small">{why()}</p>
      <p className="muted small">{policy.basis === 'moderator' ? t('cp_off_why_mod') : <>{t('cp_off_why')}{src}</>}</p>
    </div>
  )
}

export function Loading() {
  return <div className="loading" aria-busy="true"><span /><span /><span /></div>
}
