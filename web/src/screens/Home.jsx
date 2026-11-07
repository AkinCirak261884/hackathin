import React, { useState } from 'react'
import { api, MOCK, hasAnySubmission, resetDemoAnswers } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { Head, Chip, Loading, LoadError } from '../components/ui.jsx'

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
              <Chip>{r.risk_id}</Chip>{r.country && <Chip>{r.country}</Chip>}<Chip>{t('minutes', r.est_minutes)}</Chip>
              {r.closes_at && <Chip>{t('closes', date(r.closes_at))}</Chip>}
            </div>
            <h2 className="q-title">{r.title}</h2>
            {r.practice && <p className="q-sub">{t('practice_card')}</p>}
            <a className={`btn block ${r.answered ? 'answered' : ''}`} href={`#/${r.answered ? 'reveal' : 'pulse'}/${r.round_id}`}>
              {r.answered ? t('answered') : t('start')}
            </a>
          </article>
        ))}
      </div>
      {acaps?.risks?.length > 0 && <AcapsRisks data={acaps} openIds={rounds.map((r) => r.risk_id)} />}
      {/* TEMPORARY: demo-only reset, remove before the pilot */}
      {MOCK && hasAnySubmission() && (
        <div className="demo-reset">
          <button className="btn ghost small-btn" onClick={reset}>{t('reset_demo')}</button>
          <span className="muted small">{t('reset_demo_d')}</span>
        </div>
      )}
      <p className="center"><a href="#/signpost" className="muted small">{t('signpost')}</a></p>
    </section>
  )
}

// Latest ACAPS risks for this panel (ACAPS API via Lane B). Read-only context: not clickable, so no hover.
function AcapsRisks({ data, openIds }) {
  const { t, date } = useT()
  const live = data.source === 'live'
  return (
    <section className="acaps-risks">
      <Head eyebrow={live ? t('acaps_live') : t('acaps_snapshot')} title={t('acaps_title')} sub={t('acaps_sub')} />
      <div className="card risk-list">
        {data.risks.map((r) => (
          <div key={r.risk_id} className="risk-line">
            <div className="risk-line-main">
              <div className="chips">
                {r.risk_level && <span className={`level ${r.risk_level.toLowerCase()}`}>{t(`lvl_${r.risk_level.toLowerCase()}`)}</span>}
                <Chip>{r.risk_id}</Chip><Chip>{r.country}</Chip>
                {openIds.includes(r.risk_id) && <Chip tone="new">{t('acaps_in_round')}</Chip>}
              </div>
              <p className="risk-line-title">{r.title}</p>
            </div>
            <dl className="risk-line-facts">
              <div><dt>{t('probability')}</dt><dd>{r.probability ?? '—'}</dd></div>
              <div><dt>{t('impact')}</dt><dd>{r.impact != null ? `${r.impact}/5` : '—'}</dd></div>
              <div><dt>{t('acaps_trend')}</dt><dd>{r.trend ? t(`tr_${r.trend.toLowerCase()}`) : '—'}</dd></div>
            </dl>
          </div>
        ))}
      </div>
      <p className="muted small">{live && data.updated_at ? t('acaps_updated', date(data.updated_at)) : t('acaps_snapshot_d')}</p>
    </section>
  )
}
