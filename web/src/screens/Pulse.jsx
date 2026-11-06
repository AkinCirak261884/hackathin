import React, { useState } from 'react'
import { api, anonToken, DEMO_INVITE } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import TierPicker from '../components/TierPicker.jsx'

// TODO(Lane C task 2): polish each step, offline queue, revise flow (version 2).
export default function Pulse({ roundId = 'RD-R1043-1' }) {
  const { t, tx } = useT()
  const [round] = useLoad(() => api.round(roundId), [roundId])
  const [step, setStep] = useState(0)
  const [a, setA] = useState({ rating_probability: 'agree', rating_impact: 'agree', seeing: {}, prob: {}, ranking: [], missing: '', tier: 'anonymous' })
  const set = (patch) => setA((s) => ({ ...s, ...patch }))
  if (!round) return <p className="muted">…</p>

  const { risk, questions } = round
  const forecasts = questions.filter((q) => q.kind === 'forecast')
  const ranking = questions.find((q) => q.kind === 'ranking')
  const rating = questions.find((q) => q.kind === 'rating')

  async function submit() {
    const body = {
      invite_token: DEMO_INVITE,
      tier: a.tier,
      version: 1,
      missing_text: a.missing || null,
      answers: [
        { question_id: rating.question_id, rating_probability: a.rating_probability, rating_impact: a.rating_impact },
        ...forecasts.map((q) => ({ question_id: q.question_id, prob: a.prob[q.question_id] ?? 0.5, seeing: !!a.seeing[q.trigger_id] })),
        { question_id: ranking.question_id, ranking: a.ranking, ranking_other: null },
      ],
    }
    if (a.tier === 'anonymous') body.anon_token = await anonToken()
    await api.submit(roundId, body)
    window.location.hash = `#/reveal/${roundId}`
  }

  const View = ({ field }) => (
    <div className="seg">
      {['too_low', 'agree', 'too_high'].map((v) => (
        <button key={v} className={a[field] === v ? 'on' : ''} onClick={() => set({ [field]: v })}>
          {{ too_low: '↓', agree: '=', too_high: '↑' }[v]}
        </button>
      ))}
    </div>
  )

  const steps = [
    <>
      <h2>{t('rating')}</h2>
      <article className="card">
        <div className="meta">{risk.risk_id} · {risk.country} · {risk.level}</div>
        <p>{risk.title}</p>
        <p className="muted small">{risk.rationale_short}</p>
      </article>
      <p>{tx(rating)}</p>
      <label>Probability: {risk.probability}</label><View field="rating_probability" />
      <label>Impact: {risk.impact}/5</label><View field="rating_impact" />
    </>,
    <>
      <h2>{t('triggers')}</h2>
      {risk.triggers.map((tr) => (
        <label key={tr.trigger_id} className="check card">
          <input type="checkbox" checked={!!a.seeing[tr.trigger_id]}
            onChange={(e) => set({ seeing: { ...a.seeing, [tr.trigger_id]: e.target.checked } })} />
          <span><b>{tr.title}</b><br /><span className="muted small">ACAPS: {Math.round(tr.completion_rate * 100)}%</span></span>
        </label>
      ))}
    </>,
    <>
      <h2>{t('forecast')}</h2>
      {forecasts.map((q) => {
        const p = a.prob[q.question_id] ?? 0.5
        return (
          <div key={q.question_id} className="card">
            <p className="small">{tx(q)}</p>
            <input type="range" min="0" max="100" step="5" value={Math.round(p * 100)}
              onChange={(e) => set({ prob: { ...a.prob, [q.question_id]: e.target.value / 100 } })} />
            <div className="big">{Math.round(p * 100)}%</div>
          </div>
        )
      })}
    </>,
    <>
      <h2>{t('ranking')}</h2>
      {ranking.options.map((o) => {
        const i = a.ranking.indexOf(o.option_id)
        return (
          <button key={o.option_id} className={`row ${i >= 0 ? 'on' : ''}`}
            onClick={() => set({ ranking: i >= 0 ? a.ranking.filter((x) => x !== o.option_id) : a.ranking.length < 3 ? [...a.ranking, o.option_id] : a.ranking })}>
            <span className="rank">{i >= 0 ? i + 1 : ''}</span>
            {tx(o, 'label')} {o.synthetic && <span className="pill">{t('synthetic')}</span>}
          </button>
        )
      })}
    </>,
    <>
      <h2>{t('missing')}</h2>
      <textarea rows="5" maxLength="1000" value={a.missing} onChange={(e) => set({ missing: e.target.value })} />
    </>,
    <>
      <h2>{t('tier')}</h2>
      <TierPicker value={a.tier} onChange={(tier) => set({ tier })} />
    </>,
  ]

  const last = step === steps.length - 1
  return (
    <section>
      <div className="meta">{t('step', step + 1, steps.length)}</div>
      <div className="progress"><div style={{ width: `${((step + 1) / steps.length) * 100}%` }} /></div>
      {steps[step]}
      <div className="actions">
        {step > 0 && <button className="btn ghost" onClick={() => setStep(step - 1)}>{t('back')}</button>}
        <button className="btn" onClick={() => (last ? submit() : setStep(step + 1))}>{last ? t('submit') : t('next')}</button>
      </div>
    </section>
  )
}
