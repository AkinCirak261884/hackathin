import React, { useState } from 'react'
import { api, MOCK, hasAnySubmission, resetDemoAnswers, revisionOf } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { Head, Chip, Loading, LoadError } from '../components/ui.jsx'

// What the round's button does: start, update after the reveal (in the window that answered), or see the group.
// No button, a note instead: answered elsewhere (anonymous, other window/device), or first answers already closed.
function roundAction(r, t) {
  if (r.elsewhere) return { href: `#/reveal/${r.round_id}`, label: t('see_group'), cls: 'answered', note: 'answered_elsewhere' }
  if (!r.answered && !MOCK && r.stage === 'reveal') return { note: 'submit_closed' }
  if (!r.answered) return { href: `#/pulse/${r.round_id}`, label: t('start'), cls: '' }
  const decided = r.decided || !!revisionOf(r.round_id)?.decision
  if (!r.practice && !decided && (MOCK || r.stage === 'reveal')) return { href: `#/reveal/${r.round_id}`, label: t('update_answers'), cls: '' }
  return { href: `#/reveal/${r.round_id}`, label: t('answered'), cls: 'answered' }
}

export default function Home() {
  const { t, date } = useT()
  const [version, setVersion] = useState(0)
  const [rounds, roundsErr] = useLoad(() => api.openRounds('TCD'), [version])
  const [acaps] = useLoad(() => api.acapsRisks('TCD'), [])
  if (roundsErr) return <LoadError error={roundsErr} />
  if (!rounds) return <Loading />
  const reset = () => { resetDemoAnswers(); setVersion((v) => v + 1) }
  return (
    <section className="page">
      <Head level={1} title={t('openRounds')} sub={t('openRounds_sub')} />
      <div className="grid">
        {rounds.map((r) => (
          <article key={r.round_id} className="card round-card">
            <div className="chips">
              {r.practice && <Chip tone="practice">{t('practice_tag')}</Chip>}
              {r.demo && <Chip tone="hot">{t('demo_off_tag')}</Chip>}
              <Chip>{r.risk_id}</Chip>{r.country && <Chip>{r.country}</Chip>}<Chip>{t('minutes', r.est_minutes)}</Chip>
              {r.closes_at && <Chip>{t('closes', date(r.closes_at))}</Chip>}
            </div>
            <h2 className="q-title">{r.title}</h2>
            {r.practice && <p className="q-sub">{t('practice_card')}</p>}
            {r.demo && <p className="q-sub">{t('demo_off_card')}</p>}
            {(() => {
              const act = roundAction(r, t)
              return <>
                {act.note && <p className="note round-note">{t(act.note)}</p>}
                {act.href && <a className={`btn block ${act.cls}`} href={act.href}>{act.label}</a>}
              </>
            })()}
          </article>
        ))}
      </div>
      {/* TEMPORARY: demo-only reset, remove before the pilot */}
      {MOCK && hasAnySubmission() && (
        <div className="demo-reset">
          <button className="btn ghost small-btn" onClick={reset}>{t('reset_demo')}</button>
          <span className="muted small">{t('reset_demo_d')}</span>
        </div>
      )}
      {acaps?.risks?.length > 0 && <AcapsRisks data={acaps} rounds={rounds} />}
      <p className="center"><a href="#/signpost" className="muted small">{t('signpost')}</a></p>
    </section>
  )
}

// Latest ACAPS risks for this panel (ACAPS API via Lane B). Risks in one of your check-ins open that check-in
// (whole row + a Start / "see the group" button); the rest are read-only context, so no hover.
function AcapsRisks({ data, rounds }) {
  const { t, date } = useT()
  const live = data.source === 'live'
  const roundOf = Object.fromEntries([...rounds].reverse().map((r) => [r.risk_id, r]))  // first round per risk wins
  return (
    <section className="acaps-risks">
      <Head eyebrow={live ? t('acaps_live') : t('acaps_snapshot')} title={t('acaps_title')} sub={t('acaps_sub')} />
      <div className="card risk-list">
        {data.risks.map((r) => {
          const round = roundOf[r.risk_id]
          const act = round && roundAction(round, t)
          const body = (
            <>
              <div className="risk-line-main">
                <div className="chips">
                  {r.risk_level && <span className={`level ${r.risk_level.toLowerCase()}`}>{t(`lvl_${r.risk_level.toLowerCase()}`)}</span>}
                  <Chip>{r.risk_id}</Chip><Chip>{r.country}</Chip>
                  {round && <Chip tone="new">{t('acaps_in_round')}</Chip>}
                </div>
                <p className="risk-line-title">{r.title}</p>
                {act?.href && <span className={`btn small-btn risk-line-cta ${act.cls}`}>{act.label} →</span>}
              </div>
              <dl className="risk-line-facts">
                <div><dt>{t('probability')}</dt><dd>{r.probability ?? '—'}</dd></div>
                <div><dt>{t('impact')}</dt><dd>{r.impact != null ? `${r.impact}/5` : '—'}</dd></div>
                <div><dt>{t('acaps_trend')}</dt><dd>{r.trend ? t(`tr_${r.trend.toLowerCase()}`) : '—'}</dd></div>
              </dl>
            </>
          )
          return act?.href
            ? <a key={r.risk_id} className="risk-line in-round" href={act.href}>{body}</a>
            : <div key={r.risk_id} className="risk-line">{body}</div>
        })}
      </div>
      <p className="muted small">{live && data.updated_at ? t('acaps_updated', date(data.updated_at)) : t('acaps_snapshot_d')}</p>
    </section>
  )
}
