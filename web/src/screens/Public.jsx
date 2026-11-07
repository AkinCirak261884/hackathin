import React from 'react'
import { api } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct } from '../stats.js'
import { Head, Chip, Loading, LoadError } from '../components/ui.jsx'
import { RatingBar, RatingLegend, ProbMeter } from '../components/charts.jsx'

// Aggregates only. Never render authors or verbatim free text here.
export default function PublicPage() {
  const { t, date } = useT()
  const [list, listErr] = useLoad(() => api.publicSummaries(), [])
  if (listErr) return <LoadError error={listErr} />
  if (!list) return <Loading />
  return (
    <section className="page">
      <Head level={1} title={t('public')} sub={t('public_sub')} />
      {list.map((s) => (
        <article key={s.round_id} className="card">
          <div className="chips"><Chip>{s.risk_id}</Chip><Chip>n = {s.n_responses}</Chip><Chip>{date(s.published_at)}</Chip></div>
          {s.headline && <h2 className="q-title">{s.headline}</h2>}
          <p className="q-sub">{s.summary_text}</p>
          {s.rating_agreement ? (
            <>
              <RatingBar label={t('probability')} counts={s.rating_agreement.probability} />
              <RatingBar label={t('impact')} counts={s.rating_agreement.impact} />
              <RatingLegend />
            </>
          ) : s.agree_share != null && (
            <div className="item-prob"><span className="small">{t('public_agree')}</span><ProbMeter p={s.agree_share} /><b>{asPct(s.agree_share)}</b></div>
          )}
          <div className="list">
            {s.forecasts.map((f) => (
              <div key={f.question_id} className="item-prob public-f">
                <span className="small">{f.text || f.question_id}</span>
                <div className="item-prob"><ProbMeter p={f.median} /><b>{asPct(f.median)}</b></div>
              </div>
            ))}
          </div>
        </article>
      ))}
    </section>
  )
}
