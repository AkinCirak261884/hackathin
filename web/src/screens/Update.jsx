import React, { useState } from 'react'
import { api, DEMO_TOKEN, lastSubmission, revisionOf } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, likelihoodKey } from '../stats.js'
import { Head, Chip, Loading, LoadError } from '../components/ui.jsx'
import { RiskSummary, ProbPicker } from './Pulse.jsx'

// Delphi step 2, "Update my forecast", on its own page: by the time the group view opens the expert may have
// forgotten the round, so everything needed to decide is shown again: the risk (with Read more), each full
// question, their first answer and what they wrote. The group's numbers stay hidden until they save.
export default function Update({ roundId }) {
  const { t, tx, date } = useT()
  const [round, roundErr] = useLoad(() => api.round(roundId), [roundId])
  const [agg, aggErr] = useLoad(() => api.aggregate(roundId, DEMO_TOKEN), [roundId])
  const [prob, setProb] = useState({})
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  if (roundErr || aggErr) return <LoadError error={roundErr || aggErr} />
  if (!round || !agg) return <Loading />

  const first = lastSubmission(roundId)
  if (!first || agg.mustAnswer) return (
    <section className="page">
      <Head level={1} title={t('rv_update')} sub={t('must_answer')} />
      <a className="btn" href={`#/pulse/${roundId}`}>{t('start')}</a>
    </section>
  )
  if (round.practice || revisionOf(roundId)?.decision || agg.locked || agg.can_revise === false) return (
    <section className="page">
      <Head level={1} title={t('rv_update')} sub={t('up_closed')} />
      <a className="btn" href={`#/reveal/${roundId}`}>{t('reveal')}</a>
    </section>
  )

  const byQ = Object.fromEntries(first.answers.map((x) => [x.question_id, x]))
  const rating = first.answers.find((x) => x.rating_probability !== undefined)
  const forecasts = round.questions.filter((q) => q.kind === 'forecast')
  const trig = Object.fromEntries((round.risk.triggers || []).map((x) => [x.trigger_id, x]))
  const start = Object.fromEntries(forecasts.map((q) => [q.question_id, byQ[q.question_id]?.prob ?? 0.5]))
  const now = (qid) => prob[qid] ?? start[qid]
  const changed = forecasts.filter((q) => now(q.question_id) !== start[q.question_id])
  const save = async () => {
    setBusy(true)
    await api.revise(roundId, { answers: changed.map((q) => ({ question_id: q.question_id, prob: now(q.question_id) })), reason: reason.trim() })
    window.location.hash = `#/reveal/${roundId}`
  }

  return (
    <section className="page update-page">
      <Head level={1} eyebrow={t('up_eyebrow')} title={t('rv_update')} sub={t('up_sub', date(first.submitted_at || new Date().toISOString()))} />
      <div className="card"><RiskSummary risk={round.risk} /></div>

      <article className="card">
        <Head title={t('up_recap')} />
        <div className="recap answers">
          {rating && (
            <div className="recap-row"><span>{t('s_rating')}</span>
              <b>{t('probability')}: {t(rating.rating_probability || 'agree')} · {t('impact')}: {t(rating.rating_impact || 'agree')}</b></div>
          )}
          <div className="recap-row"><span>{t('a_why')}</span><b className="answer-text">{first.reasoning_text || t('a_none')}</b></div>
          <div className="recap-row">
            <span>{t('a_basis')}</span>
            <div className="chips">{(first.reasoning_basis || []).length
              ? first.reasoning_basis.map((b) => <span key={b} className="chip">{t(`b_${b}`)}</span>)
              : <b>{t('a_none')}</b>}</div>
          </div>
          {first.missing_text && <div className="recap-row"><span>{t('a_missing')}</span><b className="answer-text">{first.missing_text}</b></div>}
        </div>
      </article>

      <Head title={t('up_forecasts')} sub={t('rv_q_sub')} />
      {forecasts.map((q, i) => {
        const p0 = start[q.question_id]
        const tr = trig[q.trigger_id]
        return (
          <div key={q.question_id} className="card qcard">
            <div className="chips">
              <Chip>{i + 1} / {forecasts.length}</Chip>
              {q.closes_at && <Chip>{t('deadline', date(q.closes_at))}</Chip>}
              {tr?.completion_rate != null && <Chip>{t('acaps_progress', asPct(tr.completion_rate))}</Chip>}
              {byQ[q.question_id]?.seeing && <Chip tone="new">{t('a_seeing')}</Chip>}
            </div>
            <h3 className="q-title">{tx(q, 'title')}</h3>
            <p className="q-sub">{tx(q)}</p>
            <p className="up-first">{t('up_first', asPct(p0), t(likelihoodKey(p0)))}</p>
            <ProbPicker p={now(q.question_id)} touched label={tx(q, 'title')}
              onChange={(v) => setProb({ ...prob, [q.question_id]: v })} />
          </div>
        )
      })}

      <label className="field-label" htmlFor="up-reason">{t('rv_reason')} <span className="muted">· {t('optional')}</span></label>
      <textarea id="up-reason" rows="3" maxLength={1000} value={reason} placeholder={t('rv_reason_ph')} onChange={(e) => setReason(e.target.value)} />
      <div className="decide-actions">
        <a className="btn ghost" href={`#/reveal/${roundId}`}>{t('back')}</a>
        <button className="btn" disabled={busy || changed.length === 0} onClick={save}>{t('rv_save')}</button>
      </div>
      {changed.length === 0 && <p className="muted small">{t('rv_nochange')}</p>}
    </section>
  )
}
