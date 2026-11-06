import React, { useState } from 'react'
import { api, MOCK, hasAnySubmission, resetDemoAnswers } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { Head, Chip, Loading } from '../components/ui.jsx'

export default function Home() {
  const { t, date } = useT()
  const [version, setVersion] = useState(0)
  const [rounds] = useLoad(() => api.openRounds('TCD'), [version])
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
              <Chip>{r.risk_id}</Chip>{r.country && <Chip>{r.country}</Chip>}<Chip>{t('minutes', r.est_minutes)}</Chip>
              {r.closes_at && <Chip>{t('closes', date(r.closes_at))}</Chip>}
            </div>
            <h2 className="q-title">{r.title}</h2>
            {r.practice && <p className="q-sub">{t('practice_card')}</p>}
            <a className={`btn block ${r.answered ? 'answered' : ''}`} href={`#/${r.answered ? 'reveal' : 'pulse'}/${r.round_id}`}>
              {r.answered ? `✓ ${t('answered')}` : t('start')}
            </a>
          </article>
        ))}
      </div>
      {/* TEMPORARY: demo-only reset, remove before the pilot */}
      {MOCK && hasAnySubmission() && (
        <div className="demo-reset">
          <button className="btn ghost small-btn" onClick={reset}>↺ {t('reset_demo')}</button>
          <span className="muted small">{t('reset_demo_d')}</span>
        </div>
      )}
      <p className="center"><a href="#/signpost" className="muted small">{t('signpost')}</a></p>
    </section>
  )
}
