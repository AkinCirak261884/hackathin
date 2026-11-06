import React from 'react'
import { api, DEMO_TOKEN } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'

export default function TrackRecord() {
  const { t } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  if (!tr) return <p className="muted">…</p>
  return (
    <section>
      <h1>{t('trackRecord')}</h1>
      <article className="card">
        <div className="big">{tr.mean_brier.toFixed(3)}</div>
        <div className="meta">your Brier score (lower is better) · ACAPS baseline {tr.acaps_mean_brier.toFixed(3)}</div>
      </article>
      {tr.resolved.map((r) => (
        <article key={r.question_id} className="card">
          <p className="small">{r.text}</p>
          <div className="meta">
            you said {Math.round(r.your_prob * 100)}% · {r.outcome ? 'it happened' : 'it did not happen'} · Brier {r.brier}
          </div>
        </article>
      ))}
      {tr.impact.map((i) => <p key={i.date} className="muted small">★ {i.note}</p>)}
    </section>
  )
}
