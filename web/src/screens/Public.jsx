import React from 'react'
import { api } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'

// Aggregates only. Never render authors or verbatim free text here.
export default function PublicPage() {
  const { t } = useT()
  const [list] = useLoad(() => api.publicSummaries(), [])
  if (!list) return <p className="muted">…</p>
  return (
    <section>
      <h1>{t('public')}</h1>
      {list.map((s) => (
        <article key={s.round_id} className="card">
          <div className="meta">{s.risk_id} · n = {s.n_responses} · {s.published_at.slice(0, 10)}</div>
          <h2>{s.headline}</h2>
          <p>{s.summary_text}</p>
          {s.forecasts.map((f) => (
            <p key={f.question_id} className="small"><b>{Math.round(f.median * 100)}%</b>: {f.text}</p>
          ))}
        </article>
      ))}
    </section>
  )
}
