import React, { useState } from 'react'
import { api, DEMO_TOKEN, lastSubmission } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, r05, recordSummary } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { RatingBar, RatingLegend, ForecastDots, ForecastLegend, RankingBars, ProbMeter } from '../components/charts.jsx'

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

      <MyAnswers round={round} agg={agg} />
    </section>
  )
}

// Read-only view of what this expert submitted. Uses the locally kept submission; falls back to the
// "you" values the aggregate endpoint returns (enough for rating, forecasts and ranking).
function MyAnswers({ round, agg }) {
  const { t, tx } = useT()
  const [open, setOpen] = useState(false)
  const sub = lastSubmission()
  const mine = sub?.round_id === round.round_id ? sub : null
  const byQ = Object.fromEntries((mine?.answers || []).map((x) => [x.question_id, x]))
  const rating = round.questions.find((q) => q.kind === 'rating')
  const ranking = round.questions.find((q) => q.kind === 'ranking')
  const forecasts = round.questions.filter((q) => q.kind === 'forecast')
  const you = agg.rating.you
  const r = byQ[rating.question_id] || { rating_probability: you.probability, rating_impact: you.impact }
  const picks = byQ[ranking.question_id]?.ranking || you.ranking || []
  const label = (id) => tx(ranking.options.find((o) => o.option_id === id), 'label')

  return (
    <div className="card check-answers">
      <Head title={t('check')} sub={t('check_sub')} />
      <button className="btn ghost" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? t('check_hide') : t('check')}</button>
      {open && (
        <div className="recap answers">
          <div className="recap-row">
            <span>{tx(rating, 'title')}</span>
            <b>{t('probability')}: {t(r.rating_probability)} · {t('impact')}: {t(r.rating_impact)}</b>
          </div>
          {forecasts.map((q) => {
            const p = byQ[q.question_id]?.prob ?? agg.forecasts.find((f) => f.question_id === q.question_id)?.you
            return (
              <div key={q.question_id} className="recap-row">
                <span>{tx(q, 'title')}{byQ[q.question_id]?.seeing ? ` · ✓ ${t('a_seeing')}` : ''}</span>
                {p != null && <div className="recap-prob"><ProbMeter p={p} /><b>{asPct(p)}</b></div>}
              </div>
            )
          })}
          <div className="recap-row">
            <span>{tx(ranking, 'title')}</span>
            <ol className="answer-list">{picks.length ? picks.map((id) => <li key={id}>{label(id)}</li>) : <li>{t('a_none')}</li>}</ol>
          </div>
          {mine && (
            <>
              <div className="recap-row"><span>{t('a_missing')}</span><b className="answer-text">{mine.missing_text || t('a_none')}</b></div>
              <div className="recap-row"><span>{t('a_why')}</span><b className="answer-text">{mine.reasoning_text || t('a_none')}</b></div>
              <div className="recap-row">
                <span>{t('a_basis')}</span>
                <div className="chips">{(mine.reasoning_basis || []).length ? mine.reasoning_basis.map((b) => <span key={b} className="chip">{t(`b_${b}`)}</span>) : <b>{t('a_none')}</b>}</div>
              </div>
              <div className="recap-row"><span>{t('a_tier')}</span><b>{t(`tier_${mine.tier}`)}</b></div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
