import React, { useState } from 'react'
import { api, DEMO_TOKEN, lastSubmission, revisionOf } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, r05, recordSummary, verdict, likelihoodKey } from '../stats.js'
import { Head, Chip, Loading, LoadError } from '../components/ui.jsx'
import { RatingBar, RatingLegend, ForecastDots, ForecastLegend, RankingBars, ProbMeter, VerdictBadge } from '../components/charts.jsx'
import acapsUKR from '../mock/acaps_country_UKR.json' // public ACAPS snapshot, see _note in the file

const ACAPS_COUNTRY = { UKR: acapsUKR }

export default function Reveal({ roundId = 'RD-R1043-1' }) {
  const { t, tx, date } = useT()
  const just = window.location.hash.includes('just=1')
  const [agg, aggErr] = useLoad(() => api.aggregate(roundId, DEMO_TOKEN), [roundId])
  const [round, roundErr] = useLoad(() => api.round(roundId), [roundId])
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  const [decision, setDecision] = useState(() => revisionOf(roundId)?.decision || null)
  const [aggKey, setAggKey] = useState(0)
  const [fresh] = useLoad(() => (aggKey ? api.aggregate(roundId, DEMO_TOKEN) : Promise.resolve(null)), [aggKey])
  if (aggErr || roundErr) return <LoadError error={aggErr || roundErr} />
  if (!agg || !round) return <Loading />
  // Lane B API refuses the group view to anyone who hasn't answered yet (blind first)
  if (agg.mustAnswer) return (
    <section className="page">
      <Head level={1} title={t('reveal')} sub={t('must_answer')} />
      <a className="btn" href={`#/pulse/${roundId}`}>{t('start')}</a>
    </section>
  )
  if (agg.suppressed) return <section className="page"><Head level={1} title={t('reveal')} sub={t('suppressed')} /></section>
  // Lane B API: the group view opens when the moderator moves the round to "reveal", not on your own submit
  if (agg.locked) return (
    <section className="page">
      {just && <div className="banner"><div><b>{t('thanks')}</b></div></div>}
      <Head level={1} title={t('reveal')} sub={t('locked_wait')} />
      <a className="btn ghost" href="#/">{t('back')}</a>
    </section>
  )

  // Option B: experts read peer reasons first and decide keep/revise; the numbers unlock after that.
  // Practice rounds skip this (the outcome is shown, so revising would be hindsight).
  const needsDecision = !round.practice && !!lastSubmission(roundId) && !decision && agg.can_revise !== false
  const decide = (d) => { setDecision(d); setAggKey((k) => k + 1); window.scrollTo(0, 0) }
  if (needsDecision) return <ReasonsFirst round={round} agg={agg} just={just} rec={tr ? recordSummary(tr.history) : null} onDecided={decide} />
  if (aggKey && !fresh) return <Loading />
  return <FullReveal round={round} agg={fresh || agg} tr={tr} just={just && decision == null} roundId={roundId} />
}

function FullReveal({ round, agg, tr, just, roundId }) {
  const { t, tx, date } = useT()

  const qById = Object.fromEntries(round.questions.map((q) => [q.question_id, q]))
  const ranking = round.questions.find((q) => q.kind === 'ranking')
  const n = agg.n_responses
  const rec = tr ? recordSummary(tr.history) : null

  const forecastTakeaway = (f) => {
    const others = [...f.values]
    const i = others.indexOf(r05(f.you)); if (i >= 0) others.splice(i, 1)
    const higher = others.filter((v) => v > r05(f.you)).length
    const lower = others.filter((v) => v < r05(f.you)).length
    if (higher > others.length / 2) return t('t_forecast_higher', higher, others.length)
    if (lower > others.length / 2) return t('t_forecast_lower', lower, others.length)
    return t('t_forecast_same')
  }
  const pr = agg.rating?.probability

  return (
    <section className="page">
      {just && (
        <div className="banner">
          <div><b>{t('thanks')}</b>{rec && <div className="small">{t('record_banner', rec.correct, rec.total)}</div>}</div>
          <a className="btn small-btn" href="#/me">{t('see_profile')}</a>
        </div>
      )}
      <Head level={1} title={t('reveal')} sub={t('reveal_sub', n)} />
      {round.practice && round.outcome && <PracticeOutcome round={round} agg={agg} />}
      {ACAPS_COUNTRY[round.risk.iso] && <CountryNow c={ACAPS_COUNTRY[round.risk.iso]} />}
      <RevisionNote round={round} roundId={roundId} />

      <div className="grid">
        {agg.rating ? (
          <article className="card chart-card">
            <Head eyebrow={round.risk.risk_id} title={t('r_rating')} sub={t('r_rating_sub')} />
            <p className="takeaway">{t('t_rating', pr.agree, n, pr.too_low, pr.too_high)}</p>
            <RatingBar label={`${t('probability')} · ${round.risk.probability}`} counts={agg.rating.probability} you={agg.rating.you.probability} />
            <RatingBar label={`${t('impact')} · ${round.risk.impact}/5`} counts={agg.rating.impact} you={agg.rating.you.impact} />
            <RatingLegend />
          </article>
        ) : agg.agree && (
          // Lane B API reports one yes/no "agree with ACAPS's rating" share instead of the 3-way split
          <article className="card chart-card">
            <Head eyebrow={round.risk.risk_id} title={t('r_rating')} sub={t('r_agree_sub')} />
            <p className="takeaway">{t('t_agree', Math.round(agg.agree.share * agg.agree.n), agg.agree.n)}</p>
            <div className="item-prob"><ProbMeter p={agg.agree.share} /><b>{asPct(agg.agree.share)}</b></div>
            {agg.agree.you != null && <p className="muted small">{agg.agree.you ? t('you_agreed') : t('you_disagreed')}</p>}
          </article>
        )}

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

        {ranking && (
          <article className="card chart-card">
            <Head title={t('r_ranking')} sub={t('r_ranking_sub')} />
            <RankingBars ranking={agg.ranking} options={ranking.options} yours={agg.rating.you.ranking || []} />
          </article>
        )}
      </div>

      <Comments comments={agg.comments || []} round={round} />
      <MyAnswers round={round} agg={agg} />
    </section>
  )
}

// Read-only view of what this expert submitted. Uses the locally kept submission; falls back to the
// "you" values the aggregate endpoint returns (enough for rating, forecasts and ranking).
function MyAnswers({ round, agg }) {
  const { t, tx } = useT()
  const [open, setOpen] = useState(false)
  const mine = lastSubmission(round.round_id)
  const byQ = Object.fromEntries((mine?.answers || []).map((x) => [x.question_id, x]))
  const rating = round.questions.find((q) => q.kind === 'rating')
  const ranking = round.questions.find((q) => q.kind === 'ranking')
  const forecasts = round.questions.filter((q) => q.kind === 'forecast')
  const you = agg.rating?.you || {}
  const r = byQ[rating.question_id] || { rating_probability: you.probability, rating_impact: you.impact }
  const picks = (ranking && byQ[ranking.question_id]?.ranking) || you.ranking || []
  const label = (id) => tx(ranking?.options.find((o) => o.option_id === id), 'label')
  const rev = revisionOf(round.round_id)
  const revised = rev?.decision === 'revised' ? Object.fromEntries(rev.answers.map((x) => [x.question_id, x.prob])) : {}

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
            const p2 = revised[q.question_id]
            return (
              <div key={q.question_id} className="recap-row">
                <span>{tx(q, 'title')}{byQ[q.question_id]?.seeing ? ` · ${t('a_seeing')}` : ''}</span>
                {p != null && <div className="recap-prob"><ProbMeter p={p2 ?? p} /><b>{p2 != null ? `${asPct(p)} → ${asPct(p2)}` : asPct(p)}</b></div>}
              </div>
            )
          })}
          {ranking && (
            <div className="recap-row">
              <span>{tx(ranking, 'title')}</span>
              <ol className="answer-list">{picks.length ? picks.map((id) => <li key={id}>{label(id)}</li>) : <li>{t('a_none')}</li>}</ol>
            </div>
          )}
          {mine && (
            <>
              <div className="recap-row"><span>{t('a_missing')}</span><b className="answer-text">{mine.missing_text || t('a_none')}</b></div>
              <div className="recap-row"><span>{t('a_why')}</span><b className="answer-text">{mine.reasoning_text || t('a_none')}</b></div>
              <div className="recap-row">
                <span>{t('a_basis')}</span>
                <div className="chips">{(mine.reasoning_basis || []).length ? mine.reasoning_basis.map((b) => <span key={b} className="chip">{t(`b_${b}`)}</span>) : <b>{t('a_none')}</b>}</div>
              </div>
              <div className="recap-row"><span>{t('a_tier')}</span><b>{t(`tier_${mine.tier}`)}</b></div>
              {rev?.reason && <div className="recap-row"><span>{t('rv_reason')}</span><b className="answer-text">{rev.reason}</b></div>}
            </>
          )}
        </div>
      )}
    </div>
  )
}

// Peer comments: what each expert wrote under "why do you think this?", with their record and guesses.
// Anonymous comments show neither (a stable record would link them across rounds).
function Comments({ comments, round, hideNumbers = false }) {
  const { t, tx } = useT()
  const forecastQs = round.questions.filter((q) => q.kind === 'forecast')
  return (
    <section className="comments">
      <Head title={t('c_title')} sub={t('c_sub')} />
      {comments.length === 0 && <p className="muted">{t('c_none')}</p>}
      <div className="list">
        {comments.map((c) => {
          const anon = c.tier === 'anonymous'
          return (
            <article key={c.comment_id} className={`card comment ${c.is_you ? 'you' : ''}`}>
              <div className="c-head">
                <div className={`c-avatar ${anon ? 'anon' : ''}`} aria-hidden="true">{c.is_theme ? '·' : anon ? '?' : c.display_name[0]}</div>
                <div className="c-who">
                  <span className="c-name">{c.is_theme ? t('theme_label') : anon ? t('anon_expert') : c.display_name}
                    {c.is_you && <span className="you-tag">{t('you')}</span>}
                  </span>
                  <span className="c-record">
                    {/* Records are never shown to peers (people would follow the high scorer, and a stable record
                        helps re-identify someone). You see your own; the moderator sees all. */}
                    {c.is_theme ? t('theme_note') : anon ? t('c_anon_note')
                      : c.is_you ? (c.record?.resolved > 0 ? t('c_record_you', c.record.correct, c.record.resolved) : t('c_new'))
                      : t('c_record_private')}
                  </span>
                </div>
              </div>
              <p className="c-text">{c.text}</p>
              {c.basis?.length > 0 && (
                <div className="chips">{c.basis.map((b) => <span key={b} className="chip">{t(`b_${b}`)}</span>)}</div>
              )}
              {c.forecasts && !hideNumbers && (
                <div className="c-guesses">
                  {forecastQs.filter((q) => c.forecasts[q.question_id] != null).map((q) => (
                    <span key={q.question_id} className="c-guess" title={tx(q, 'title')}>
                      {t('c_guess')} {q.trigger_id}: <b>{asPct(c.forecasts[q.question_id])}</b>
                    </span>
                  ))}
                </div>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}

// Practice round: after answering, show what actually happened and how your forecast scored vs ACAPS.
function PracticeOutcome({ round, agg }) {
  const { t } = useT()
  const o = round.outcome
  const f = agg.forecasts[0]
  const out = o.materialised ? 1 : 0
  const you = f?.you
  const b = you != null ? (you - out) ** 2 : null
  const ab = (o.acaps_prob - out) ** 2
  return (
    <article className={`card outcome ${o.materialised ? 'yes' : 'no'}`}>
      <div className="eyebrow">{t('practice_tag')} · {round.risk.country}</div>
      <h2 className="q-title">{t('what_happened')}: {o.materialised ? t('happened') : t('not_happened')}</h2>
      <p className="q-sub">{o.summary}</p>
      {you != null && (
        <div className="outcome-score">
          <VerdictBadge verdict={verdict(you, out)} />
          <span>{t('you_said', asPct(you))} · {t('acaps_said', asPct(o.acaps_prob))}</span>
          <span className={`beat ${b < ab ? 'yes' : 'no'}`}>{b < ab ? t('beat_acaps') : t('acaps_closer')}</span>
        </div>
      )}
      <p className="muted small">{t('practice_scored')}</p>
    </article>
  )
}

// Country context from ACAPS, shown only after answering (on the reveal screen), so later events
// can't give away a practice question's outcome. Energy-related events are tagged.
function CountryNow({ c }) {
  const { t, date } = useT()
  const k = c.crisis
  return (
    <article className="card country-now">
      <Head eyebrow={<><Chip>{c.country}</Chip><Chip>{k.crisis_id}</Chip></>} title={t('cn_title', c.country)} sub={t('cn_sub')} />
      <dl className="facts">
        <div><dt>{t('cn_severity')}</dt><dd>{k.severity.toFixed(1)} · {k.severity_label}</dd></div>
        <div><dt>{t('cn_access')}</dt><dd>{k.access_constraints.toFixed(1)}</dd></div>
        <div><dt>{t('cn_updated')}</dt><dd>{date(k.updated_at)}</dd></div>
      </dl>
      <dl className="facts">
        {c.key_figures.map((f) => <div key={f.label}><dt>{f.label}</dt><dd>{f.value}</dd><span className="muted small">{f.source}, {date(f.date)}</span></div>)}
      </dl>
      <h3 className="q-title">{t('cn_events')}</h3>
      <ul className="cn-events">
        {c.events.map((e) => (
          <li key={e.date + e.text.slice(0, 12)}>
            <span className="muted small">{date(e.date)}</span>{e.energy && <> <Chip tone="hot">{t('cn_energy')}</Chip></>}
            <div className="small">{e.text}</div>
          </li>
        ))}
      </ul>
      <h3 className="q-title">{t('cn_reports')}</h3>
      <ul className="cn-events">
        {c.reports.map((x) => <li key={x.url}><a href={x.url} target="_blank" rel="noopener noreferrer">{x.title}</a> <span className="muted small">· {date(x.date)}</span></li>)}
      </ul>
      <p className="muted small">{t('cn_needs')}: {c.priority_needs.join(', ')}</p>
      <p className="note">{t('cn_source')} <a href={c.source_url} target="_blank" rel="noopener noreferrer">acaps.org</a> · {date(c.fetched_at)}</p>
    </article>
  )
}

// Step 2, option B: peer reasons without numbers, then keep or revise once. First answer stays the scored one.
function ReasonsFirst({ round, agg, just, rec, onDecided }) {
  const { t } = useT()
  const [revising, setRevising] = useState(false)
  const [busy, setBusy] = useState(false)
  const keep = async () => { setBusy(true); await api.keepAnswers(round.round_id); onDecided('kept') }
  return (
    <section className="page">
      {just && (
        <div className="banner">
          <div><b>{t('thanks')}</b>{rec && <div className="small">{t('record_banner', rec.correct, rec.total)}</div>}</div>
        </div>
      )}
      <Head level={1} eyebrow={t('rv_step')} title={t('rv_title')} sub={t('rv_sub')} />
      <Comments comments={agg.comments || []} round={round} hideNumbers />
      <article className="card decide-card">
        {!revising ? (
          <>
            <Head title={t('rv_q')} sub={t('rv_q_sub')} />
            <div className="decide-actions">
              <button className="btn ghost" disabled={busy} onClick={keep}>{t('rv_keep')}</button>
              <button className="btn" disabled={busy} onClick={() => setRevising(true)}>{t('rv_update')}</button>
            </div>
          </>
        ) : (
          <RevisePanel round={round} onCancel={() => setRevising(false)} onSaved={() => onDecided('revised')} />
        )}
      </article>
    </section>
  )
}

function RevisePanel({ round, onCancel, onSaved }) {
  const { t, tx } = useT()
  const first = lastSubmission(round.round_id)
  const qs = round.questions.filter((q) => q.kind === 'forecast')
  const start = Object.fromEntries(qs.map((q) => [q.question_id, first?.answers.find((x) => x.question_id === q.question_id)?.prob ?? 0.5]))
  const [prob, setProb] = useState(start)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const changed = qs.filter((q) => prob[q.question_id] !== start[q.question_id])
  const save = async () => {
    setBusy(true)
    await api.revise(round.round_id, { answers: changed.map((q) => ({ question_id: q.question_id, prob: prob[q.question_id] })), reason: reason.trim() })
    onSaved()
  }
  return (
    <div className="revise">
      <Head title={t('rv_update')} sub={t('rv_once')} />
      {qs.map((q) => {
        const p = prob[q.question_id]
        return (
          <div key={q.question_id} className="revise-q">
            <span className="q-title">{tx(q, 'title')}</span>
            <div className="prob-read">
              <span className="big">{asPct(p)}</span>
              <span className="muted">{t(likelihoodKey(p))}</span>
              <span className="muted small revise-first">{t('rv_first', asPct(start[q.question_id]))}</span>
            </div>
            <input type="range" min="0" max="100" step="5" value={Math.round(p * 100)} aria-label={tx(q, 'title')}
              onChange={(e) => setProb({ ...prob, [q.question_id]: e.target.value / 100 })} />
          </div>
        )
      })}
      <label className="field-label" htmlFor="rv-reason">{t('rv_reason')} <span className="muted">· {t('optional')}</span></label>
      <textarea id="rv-reason" rows="2" maxLength={1000} value={reason} placeholder={t('rv_reason_ph')} onChange={(e) => setReason(e.target.value)} />
      <div className="decide-actions">
        <button className="btn ghost" disabled={busy} onClick={onCancel}>{t('back')}</button>
        <button className="btn" disabled={busy || changed.length === 0} onClick={save}>{t('rv_save')}</button>
      </div>
      {changed.length === 0 && <p className="muted small">{t('rv_nochange')}</p>}
    </div>
  )
}

// Shown above the charts after a revision: what moved, and that the first answer is the scored one.
function RevisionNote({ round, roundId }) {
  const { t, tx } = useT()
  const rev = revisionOf(roundId)
  if (rev?.decision !== 'revised') return null
  const first = lastSubmission(roundId)
  const qById = Object.fromEntries(round.questions.map((q) => [q.question_id, q]))
  return (
    <div className="note revision-note">
      <b>{t('rv_done')}</b>
      <ul>
        {rev.answers.map((a) => {
          const p1 = first?.answers.find((x) => x.question_id === a.question_id)?.prob
          return <li key={a.question_id}>{tx(qById[a.question_id], 'title')}: {p1 != null ? `${asPct(p1)} → ` : ''}<b>{asPct(a.prob)}</b></li>
        })}
      </ul>
      <span className="muted">{t('rv_scored')}</span>
    </div>
  )
}
