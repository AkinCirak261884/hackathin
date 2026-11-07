import React, { useState } from 'react'
import { api, anonToken, DEMO_INVITE } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, likelihoodKey } from '../stats.js'
import TierPicker from '../components/TierPicker.jsx'
import { Head, Chip, Loading, Icon } from '../components/ui.jsx'
import { ProbMeter } from '../components/charts.jsx'

const PRESETS = [0.1, 0.3, 0.5, 0.7, 0.9]
const BASIS = ['field_observation', 'local_contacts', 'media_osint', 'reports_data', 'experience']

function RiskSummary({ risk }) {
  const { t } = useT()
  return (
    <div className="risk">
      <div className="chips">
        <Chip>{risk.risk_id}</Chip><Chip>{risk.country}</Chip>
        <Chip tone="hot">{risk.level}</Chip><Chip>{risk.trend}</Chip>
      </div>
      <h3>{risk.title}</h3>
      <p className="small muted">{risk.rationale_short}</p>
      <dl className="facts">
        <div><dt>{t('probability')}</dt><dd>{risk.probability}</dd></div>
        <div><dt>{t('impact')}</dt><dd>{risk.impact}/5</dd></div>
        <div><dt>Exposure</dt><dd>{risk.expected_exposure}</dd></div>
      </dl>
    </div>
  )
}

export default function Pulse({ roundId = 'RD-R1043-1' }) {
  const { t, tx, date } = useT()
  const [round] = useLoad(() => api.round(roundId), [roundId])
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const [a, setA] = useState({
    rating_probability: null, rating_impact: null, seeing: {}, prob: {}, ranking: [],
    missing: '', why: '', basis: [], tier: 'anonymous',
  })
  const set = (patch) => setA((s) => ({ ...s, ...patch }))
  if (!round) return <Loading />

  const { risk, questions } = round
  const rating = questions.find((q) => q.kind === 'rating')
  const forecasts = questions.filter((q) => q.kind === 'forecast')
  const ranking = questions.find((q) => q.kind === 'ranking')
  const trig = Object.fromEntries(risk.triggers.map((x) => [x.trigger_id, x]))
  const optLabel = (id) => tx(ranking?.options.find((o) => o.option_id === id), 'label')

  async function submit() {
    setBusy(true)
    const body = {
      invite_token: DEMO_INVITE,
      tier: a.tier,
      version: 1,
      missing_text: a.missing.trim() || null,
      reasoning_text: a.why.trim() || null,
      reasoning_basis: a.basis.length ? a.basis : null,
      answers: [
        { question_id: rating.question_id, rating_probability: a.rating_probability || 'agree', rating_impact: a.rating_impact || 'agree' },
        ...forecasts.map((q) => ({ question_id: q.question_id, prob: a.prob[q.question_id] ?? 0.5, seeing: !!a.seeing[q.trigger_id] })),
        ...(ranking ? [{ question_id: ranking.question_id, ranking: a.ranking, ranking_other: null }] : []),
      ],
    }
    if (a.tier === 'anonymous') body.anon_token = await anonToken()
    await api.submit(roundId, body)
    window.location.hash = `#/reveal/${roundId}?just=1`
  }

  const ViewPicker = ({ field, label, current }) => (
    <fieldset className="field">
      <legend>{label} <span className="muted">· ACAPS: {current}</span></legend>
      <div className="seg3">
        {['too_low', 'agree', 'too_high'].map((v) => (
          <button key={v} type="button" className={`${v} ${a[field] === v ? 'on' : ''}`} aria-pressed={a[field] === v}
            onClick={() => set({ [field]: v })}>
            <b><Icon name={{ too_low: 'down', agree: 'check', too_high: 'up' }[v]} size={20} /></b>{t(v)}
          </button>
        ))}
      </div>
    </fieldset>
  )

  const steps = [
    {
      key: 'rating', title: t('s_rating'), sub: t('s_rating_sub'),
      body: (
        <>
          <div className="phone-only card"><RiskSummary risk={risk} /></div>
          <ViewPicker field="rating_probability" label={t('probability')} current={risk.probability} />
          <ViewPicker field="rating_impact" label={t('impact')} current={`${risk.impact}/5`} />
        </>
      ),
    },
    {
      key: 'triggers', title: t('s_triggers'), sub: t('s_triggers_sub'),
      body: risk.triggers.map((x) => (
        <label key={x.trigger_id} className={`card check ${a.seeing[x.trigger_id] ? 'on' : ''}`}>
          <input type="checkbox" checked={!!a.seeing[x.trigger_id]}
            onChange={(e) => set({ seeing: { ...a.seeing, [x.trigger_id]: e.target.checked } })} />
          <span className="check-body">
            <span className="chips"><Chip>{x.trigger_id}</Chip><Chip>{t('acaps_progress', asPct(x.completion_rate))}</Chip></span>
            <b className="q-title">{x.title}</b>
            <span className="q-sub">{x.description}</span>
          </span>
        </label>
      )),
    },
    {
      key: 'forecast', title: t('s_forecast'), sub: t('s_forecast_sub'),
      body: forecasts.map((q, i) => {
        const p = a.prob[q.question_id] ?? 0.5
        const touched = a.prob[q.question_id] != null
        return (
          <div key={q.question_id} className="card qcard">
            <div className="chips">
              <Chip>{i + 1} / {forecasts.length}</Chip>
              <Chip>{t('deadline', date(q.closes_at))}</Chip>
              <Chip>{t('acaps_progress', asPct(trig[q.trigger_id].completion_rate))}</Chip>
            </div>
            <h3 className="q-title">{tx(q, 'title')}</h3>
            <p className="q-sub">{tx(q)}</p>
            <div className={`prob-read ${touched ? '' : 'untouched'}`}>
              <span className="big">{asPct(p)}</span>
              <span className="muted">{t(likelihoodKey(p))}</span>
            </div>
            <input type="range" min="0" max="100" step="5" value={Math.round(p * 100)}
              aria-label={tx(q, 'title')}
              onChange={(e) => set({ prob: { ...a.prob, [q.question_id]: e.target.value / 100 } })} />
            <div className="presets">
              {PRESETS.map((v) => (
                <button key={v} type="button" className={touched && p === v ? 'on' : ''}
                  onClick={() => set({ prob: { ...a.prob, [q.question_id]: v } })}>{asPct(v)}</button>
              ))}
            </div>
          </div>
        )
      }),
    },
    ranking && {
      key: 'ranking', title: t('s_ranking'), sub: t('s_ranking_sub'),
      body: (
        <>
          <div className="eyebrow">{t('picked', a.ranking.length)}</div>
          {ranking.options.map((o) => {
            const i = a.ranking.indexOf(o.option_id)
            const full = a.ranking.length >= 3 && i < 0
            return (
              <button key={o.option_id} type="button" disabled={full} className={`row ${i >= 0 ? 'on' : ''}`}
                onClick={() => set({ ranking: i >= 0 ? a.ranking.filter((x) => x !== o.option_id) : [...a.ranking, o.option_id] })}>
                <span className="rank">{i >= 0 ? i + 1 : ''}</span>
                <span className="row-text">{tx(o, 'label')}</span>
                {o.synthetic && <span className="pill">{t('synthetic')}</span>}
              </button>
            )
          })}
        </>
      ),
    },
    {
      key: 'missing', title: t('s_missing'), sub: t('s_missing_sub'),
      body: <textarea rows="6" maxLength="1000" placeholder={t('missing_ph')} value={a.missing} onChange={(e) => set({ missing: e.target.value })} />,
    },
    {
      key: 'why', title: t('s_why'), sub: t('s_why_sub'),
      body: (
        <>
          <div className="card recap">
            <div className="recap-row">
              <span>{t('s_rating')}</span>
              <b>{t('probability')}: {t(a.rating_probability || 'agree')} · {t('impact')}: {t(a.rating_impact || 'agree')}</b>
              <button type="button" className="link" onClick={() => goTo('rating')}>{t('edit')}</button>
            </div>
            {forecasts.map((q) => {
              const p = a.prob[q.question_id] ?? 0.5
              return (
                <div key={q.question_id} className="recap-row">
                  <span>{tx(q, 'title')}</span>
                  <div className="recap-prob"><ProbMeter p={p} /><b>{asPct(p)}</b></div>
                  <button type="button" className="link" onClick={() => goTo('forecast')}>{t('edit')}</button>
                </div>
              )
            })}
            {ranking && (
              <div className="recap-row">
                <span>{t('s_ranking')}</span>
                <b>{a.ranking.length ? a.ranking.map((id, i) => `${i + 1}. ${optLabel(id)}`).join('  ') : '—'}</b>
                <button type="button" className="link" onClick={() => goTo('ranking')}>{t('edit')}</button>
              </div>
            )}
          </div>
          <label className="field-label" htmlFor="why">{t('why_label')}</label>
          <textarea id="why" rows="5" maxLength="1000" placeholder={t('why_ph')} value={a.why} onChange={(e) => set({ why: e.target.value })} />
          <div className="field-label">{t('basis_label')}</div>
          <div className="toggles">
            {BASIS.map((b) => {
              const on = a.basis.includes(b)
              return (
                <button key={b} type="button" aria-pressed={on} className={on ? 'on' : ''}
                  onClick={() => set({ basis: on ? a.basis.filter((x) => x !== b) : [...a.basis, b] })}>{t(`b_${b}`)}</button>
              )
            })}
          </div>
          <p className="note">{t('why_private')}</p>
        </>
      ),
    },
    {
      key: 'tier', title: t('s_tier'), sub: t('s_tier_sub'),
      body: <TierPicker value={a.tier} onChange={(tier) => set({ tier })} />,
    },
  ].filter(Boolean)

  const goTo = (key) => setStep(steps.findIndex((x) => x.key === key))
  const s = steps[step]
  const last = step === steps.length - 1
  const go = (d) => { setStep(step + d); window.scrollTo({ top: 0, behavior: 'smooth' }) }

  return (
    <div className="pulse">
      <aside className="desktop-only pulse-aside card"><RiskSummary risk={risk} /></aside>
      <section className="pulse-main">
        <div className="progress" aria-hidden="true"><div style={{ width: `${((step + 1) / steps.length) * 100}%` }} /></div>
        {round.practice && <p className="practice-note">{t('practice_note', date(round.as_of))}</p>}
        <Head level={1} eyebrow={t('step', step + 1, steps.length)} title={s.title} sub={s.sub} />
        <div className="step-body" key={s.key}>{s.body}</div>
        <div className="actionbar">
          {step > 0 ? <button className="btn ghost" onClick={() => go(-1)}>{t('back')}</button> : <a className="btn ghost" href="#/">{t('back')}</a>}
          <button className="btn" disabled={busy} onClick={() => (last ? submit() : go(1))}>{last ? t('submit') : t('next')}</button>
        </div>
      </section>
    </div>
  )
}
