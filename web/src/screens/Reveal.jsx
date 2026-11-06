import React from 'react'
import { api, DEMO_TOKEN } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'

// TODO(Lane C task 4): revise flow (POST version 2), nicer distribution chart.
export default function Reveal({ roundId = 'RD-R1043-1' }) {
  const { t, tx } = useT()
  const [agg] = useLoad(() => api.aggregate(roundId, DEMO_TOKEN), [roundId])
  const [round] = useLoad(() => api.round(roundId), [roundId])
  if (!agg || !round) return <p className="muted">…</p>
  if (agg.suppressed) return <section><h1>{t('reveal')}</h1><p>{agg.reason}</p></section>
  const qById = Object.fromEntries(round.questions.map((q) => [q.question_id, q]))
  return (
    <section>
      <h1>{t('reveal')}</h1>
      <p className="muted">n = {agg.n_responses}</p>
      {agg.forecasts.map((f) => (
        <article key={f.question_id} className="card">
          <p className="small">{tx(qById[f.question_id])}</p>
          <div className="strip">
            <div className="iqr" style={{ left: `${f.p25 * 100}%`, width: `${(f.p75 - f.p25) * 100}%` }} />
            {f.values.map((v, i) => <span key={i} className="dot" style={{ left: `${v * 100}%` }} />)}
            {f.you != null && <span className="dot you" style={{ left: `${f.you * 100}%` }} />}
          </div>
          <div className="meta">median {Math.round(f.median * 100)}% · you {Math.round(f.you * 100)}%</div>
        </article>
      ))}
      {agg.can_revise && <button className="btn" onClick={() => alert('TODO: revise (version 2)')}>{t('revise')}</button>}
    </section>
  )
}
