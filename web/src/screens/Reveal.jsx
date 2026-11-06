import React from 'react'
import { api, DEMO_TOKEN } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, r05, recordSummary } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { RatingBar, RatingLegend, ForecastDots, ForecastLegend, RankingBars } from '../components/charts.jsx'

export default function Reveal({ roundId = 'RD-R1043-1' }) {
  const { t, tx, date } = useT()
  const just = window.location.hash.includes('just=1')
  const [agg] = useLoad(() => api.aggregate(roundId, DEMO_TOKEN), [roundId])
  const [round] = useLoad(() => api.round(roundId), [roundId])
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  if (!agg || !round) return <Loading />
  if (agg.suppressed) return <section className="page"><Head level={1} title={t('reveal')} sub={t('suppressed')} /></section>

  const qById = Object.fromEntries(round.questions.map((q) => [q.question_id, q]))
  const ranking = round.questions.find((q) => q.kind === 'ranking')
  const n = agg.n_responses
  const rec = tr ? recordSummary(tr.resolved) : null

  const forecastTakeaway = (f) => {
    const others = [...f.values]
    const i = others.indexOf(r05(f.you)); if (i >= 0) others.splice(i, 1)
    const higher = others.filter((v) => v > r05(f.you)).length
    const lower = others.filter((v) => v < r05(f.you)).length
    if (higher > others.length / 2) return t('t_forecast_higher', higher, others.length)
    if (lower > others.length / 2) return t('t_forecast_lower', lower, others.length)
    return t('t_forecast_same')
  }
  const pr = agg.rating.probability

  return (
    <section className="page">
      {just && (
        <div className="banner">
          <div><b>✓ {t('thanks')}</b>{rec && <div className="small">{t('record_banner', rec.correct, rec.total)}</div>}</div>
          <a className="btn small-btn" href="#/me">{t('see_profile')}</a>
        </div>
      )}
      <Head level={1} title={t('reveal')} sub={t('reveal_sub', n)} />

      <div className="grid">
        <article className="card chart-card">
          <Head eyebrow={round.risk.risk_id} title={t('r_rating')} sub={t('r_rating_sub')} />
          <p className="takeaway">{t('t_rating', pr.agree, n, pr.too_low, pr.too_high)}</p>
          <RatingBar label={`${t('probability')} · ${round.risk.probability}`} counts={agg.rating.probability} you={agg.rating.you.probability} />
          <RatingBar label={`${t('impact')} · ${round.risk.impact}/5`} counts={agg.rating.impact} you={agg.rating.you.impact} />
          <RatingLegend />
        </article>

        {agg.forecasts.map((f) => {
          const q = qById[f.question_id]
          return (
            <article key={f.question_id} className="card chart-card">
              <Head eyebrow={<><Chip>{q.trigger_id}</Chip> <Chip>{t('deadline', date(q.closes_at))}</Chip></>}
                title={tx(q, 'title')} sub={tx(q)} />
              <div className="kpis">
                <div><span className="kpi-num">{asPct(f.median)}</span><span className="kpi-label">{t('group_median')}</span></div>
                <div><span className="kpi-num you-ink">{asPct(f.you)}</span><span className="kpi-label">{t('you')}</span></div>
              </div>
              <p className="takeaway">{forecastTakeaway(f)}</p>
              <ForecastDots {...f} />
              <ForecastLegend />
            </article>
          )
        })}

        <article className="card chart-card">
          <Head title={t('r_ranking')} sub={t('r_ranking_sub')} />
          <RankingBars ranking={agg.ranking} options={ranking.options} yours={agg.rating.you.ranking || []} />
        </article>
      </div>

      {agg.can_revise && (
        <div className="card revise">
          <Head title={t('revise')} sub={t('revise_sub')} />
          <button className="btn ghost" onClick={() => alert('TODO: revise (version 2)')}>{t('revise')}</button>
        </div>
      )}
    </section>
  )
}
