import React, { useId, useRef, useState } from 'react'
import { api, anonToken, inviteToken, MOCK } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, likelihoodKey } from '../stats.js'
import TierPicker from '../components/TierPicker.jsx'
import { Head, Chip, Loading, Icon, LoadError, CommentsPolicyLine } from '../components/ui.jsx'
import { ProbMeter } from '../components/charts.jsx'

const PRESETS = [0.1, 0.3, 0.5, 0.7, 0.9]
const BASIS = ['field_observation', 'local_contacts', 'media_osint', 'reports_data', 'experience']

// ACAPS rationale: one paragraph per line; "[label](https://…)" source links become real links (no raw HTML).
function RationaleText({ text }) {
  return text.split('\n').map((line, i) => {
    const parts = []
    let last = 0
    for (const m of line.matchAll(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\s*\)/g)) {
      if (m.index > last) parts.push(line.slice(last, m.index))
      parts.push(<a key={m.index} href={m[2]} target="_blank" rel="noopener noreferrer">{m[1]}</a>)
      last = m.index + m[0].length
    }
    parts.push(line.slice(last))
    return <p key={i}>{parts}</p>
  })
}

// "Read more": the card shows ACAPS's short rationale; the full text opens in a dialog over the screen.
function RationaleDialog({ risk }) {
  const { t } = useT()
  const ref = useRef(null)
  const titleId = useId()
  const close = () => ref.current?.close()
  return (
    <>
      <button type="button" className="link read-more" onClick={() => ref.current?.showModal()}>{t('read_more')}</button>
      <dialog ref={ref} className="sheet" aria-labelledby={titleId} onClick={(e) => { if (e.target === ref.current) close() }}>
        <div className="sheet-body">
          <div className="sheet-head">
            <div>
              <div className="eyebrow">{t('acaps_rationale')} · {risk.risk_id}</div>
              <h2 id={titleId}>{risk.title}</h2>
            </div>
            <button type="button" className="btn ghost small-btn" onClick={close}>{t('close')}</button>
          </div>
          <div className="sheet-text"><RationaleText text={risk.rationale} /></div>
          <p className="muted small">{t('acaps_rationale_src')}</p>
        </div>
      </dialog>
    </>
  )
}

function RiskSummary({ risk }) {
  const { t } = useT()
  const more = risk.rationale && risk.rationale.length > (risk.rationale_short || '').length + 20
  return (
    <div className="risk">
      <div className="chips">
        <Chip>{risk.risk_id}</Chip><Chip>{risk.country}</Chip>
        {risk.level && <Chip tone="hot">{risk.level}</Chip>}{risk.trend && <Chip>{risk.trend}</Chip>}
      </div>
      <h3>{risk.title}</h3>
      {risk.rationale_short && <p className="small muted">{risk.rationale_short}</p>}
      {more && <RationaleDialog risk={risk} />}
      <dl className="facts">
        <div><dt>{t('probability')}</dt><dd>{risk.probability}</dd></div>
        <div><dt>{t('impact')}</dt><dd>{risk.impact}/5</dd></div>
        {risk.expected_exposure && <div><dt>Exposure</dt><dd>{risk.expected_exposure}</dd></div>}
      </dl>
    </div>
  )
}

const OTHER = 'OTHER'

// Slider + quick presets + reading, shared by ACAPS's trigger questions and the expert's own additions.
function ProbPicker({ p, touched, label, onChange }) {
  const { t } = useT()
  const v = p ?? 0.5
  return (
    <>
      <div className={`prob-read ${touched ? '' : 'untouched'}`}>
        <span className="big">{asPct(v)}</span>
        <span className="muted">{t(likelihoodKey(v))}</span>
      </div>
      <input type="range" min="0" max="100" step="5" value={Math.round(v * 100)} aria-label={label}
        onChange={(e) => onChange(e.target.value / 100)} />
      <div className="presets">
        {PRESETS.map((x) => (
          <button key={x} type="button" className={touched && v === x ? 'on' : ''} onClick={() => onChange(x)}>{asPct(x)}</button>
        ))}
      </div>
    </>
  )
}

// "Something else is happening": developments the expert sees that ACAPS hasn't listed, optionally flagged as
// possibly bigger than the risk itself. Goes to the ACAPS moderator only (never shown word for word to peers).
function SignalAdder({ signals, policy, onChange }) {
  const { t } = useT()
  const [text, setText] = useState('')
  const [bigger, setBigger] = useState(false)
  const add = (e) => {
    e.preventDefault()
    if (!text.trim()) return
    onChange([...signals, { text: text.trim(), bigger }])
    setText(''); setBigger(false)
  }
  return (
    <div className="card add-own">
      <b className="q-title">{t('sig_title')}</b>
      <span className="q-sub">{t('sig_sub')}</span>
      {signals.map((s, i) => (
        <div key={i} className="own-item">
          <span className="own-text">{s.text}</span>
          {s.bigger && <span className="chip hot">{t('sig_bigger_tag')}</span>}
          <button type="button" className="link" onClick={() => onChange(signals.filter((_, j) => j !== i))}>{t('remove')}</button>
        </div>
      ))}
      {signals.length < 3 && (
        <form className="own-form" onSubmit={add}>
          <input type="text" maxLength={200} value={text} placeholder={t('sig_ph')} aria-label={t('sig_title')} onChange={(e) => setText(e.target.value)} />
          <label className="own-flag"><input type="checkbox" checked={bigger} onChange={(e) => setBigger(e.target.checked)} /> {t('sig_bigger')}</label>
          <button type="submit" className="btn ghost small-btn" disabled={!text.trim()}>{t('add')}</button>
        </form>
      )}
      <p className="muted small own-note">{policy?.enabled === false ? t('own_private_off') : t('own_private')}</p>
    </div>
  )
}

// "A bigger risk isn't on the list?": the expert's own option, ranked like the others.
function OtherRisk({ value, rank, full, policy, prob, onProb, onToggle, onChange }) {
  const { t } = useT()
  const [draft, setDraft] = useState('')
  if (value) return (
    <>
      <button type="button" disabled={full && rank < 0} className={`row ${rank >= 0 ? 'on' : ''}`} onClick={onToggle}>
        <span className="rank">{rank >= 0 ? rank + 1 : ''}</span>
        <span className="row-text">{value}</span>
        <span className="pill">{t('own_tag')}</span>
      </button>
      <div className="card qcard own-q own-risk-prob">
        <p className="q-sub">{t('own_risk_prob_q')}</p>
        <ProbPicker p={prob} touched={prob != null} label={value} onChange={onProb} />
      </div>
      <button type="button" className="link own-remove" onClick={() => onChange('')}>{t('remove')} · {t('own_tag')}</button>
    </>
  )
  return (
    <form className="card add-own own-form" onSubmit={(e) => { e.preventDefault(); if (draft.trim()) { onChange(draft.trim()); setDraft('') } }}>
      <b className="q-title">{t('other_title')}</b>
      <span className="q-sub">{t('other_sub')}</span>
      <input type="text" maxLength={120} value={draft} placeholder={t('other_ph')} aria-label={t('other_title')} onChange={(e) => setDraft(e.target.value)} />
      <button type="submit" className="btn ghost small-btn" disabled={!draft.trim()}>{t('add')}</button>
      <p className="muted small own-note">{policy?.enabled === false ? t('own_private_off') : t('own_private')}</p>
    </form>
  )
}

export default function Pulse({ roundId = 'RD-R1043-1' }) {
  const { t, tx, date } = useT()
  const [round, roundErr] = useLoad(() => api.round(roundId), [roundId])
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const [a, setA] = useState({
    rating_probability: null, rating_impact: null, seeing: {}, prob: {}, ranking: [],
    missing: '', why: '', basis: [], tier: 'anonymous',
    signals: [],     // things the expert sees that ACAPS hasn't listed: [{ text, bigger }]
    other_risk: '',  // a risk missing from the top-3 list (contract: ranking_other, ranked as 'OTHER')
    source_other: '', // "Based on: other": the expert's own source, in their words (moderator-only)
    other_risk_prob: null, // likelihood the expert gives their own top-3 risk
  })
  const set = (patch) => setA((s) => ({ ...s, ...patch }))
  if (roundErr) return <LoadError error={roundErr} />
  if (!round) return <Loading />

  const { risk, questions } = round
  const policy = round.comments_policy
  const rating = questions.find((q) => q.kind === 'rating')
  const forecasts = questions.filter((q) => q.kind === 'forecast')
  const ranking = questions.find((q) => q.kind === 'ranking')
  const trig = Object.fromEntries(risk.triggers.map((x) => [x.trigger_id, x]))
  const optLabel = (id) => (id === OTHER ? a.other_risk : tx(ranking?.options.find((o) => o.option_id === id), 'label'))

  async function submit() {
    setBusy(true)
    const body = {
      invite_token: inviteToken(),
      tier: a.tier,
      version: 1,
      missing_text: a.missing.trim() || null,
      reasoning_text: a.why.trim() || null,
      reasoning_basis: a.basis.filter((b) => b !== 'other').length ? a.basis.filter((b) => b !== 'other') : null,
      source_other: a.basis.includes('other') && a.source_other.trim() ? a.source_other.trim() : null,
      answers: [
        { question_id: rating.question_id, rating_probability: a.rating_probability || 'agree', rating_impact: a.rating_impact || 'agree' },
        ...forecasts.map((q) => ({ question_id: q.question_id, prob: a.prob[q.question_id] ?? 0.5, seeing: !!a.seeing[q.trigger_id] })),
        ...(ranking ? [{ question_id: ranking.question_id, ranking: a.ranking, ranking_other: a.other_risk.trim() || null }] : []),
      ],
      seeing_other: a.signals.length ? a.signals.map((s) => ({ ...s, prob: s.prob ?? 0.5 })) : null,
      other_risk_prob: a.other_risk.trim() ? (a.other_risk_prob ?? 0.5) : null,
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
      body: <>{risk.triggers.map((x) => (
        <label key={x.trigger_id} className={`card check ${a.seeing[x.trigger_id] ? 'on' : ''}`}>
          <input type="checkbox" checked={!!a.seeing[x.trigger_id]}
            onChange={(e) => set({ seeing: { ...a.seeing, [x.trigger_id]: e.target.checked } })} />
          <span className="check-body">
            <span className="chips"><Chip>{x.trigger_id}</Chip><Chip>{t('acaps_progress', asPct(x.completion_rate))}</Chip></span>
            <b className="q-title">{x.title}</b>
            <span className="q-sub">{x.description}</span>
          </span>
        </label>
      ))}
      <SignalAdder signals={a.signals} policy={policy} onChange={(signals) => set({ signals })} />
      </>,
    },
    {
      key: 'forecast', title: t('s_forecast'), sub: t('s_forecast_sub'),
      body: <>{forecasts.map((q, i) => {
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
            <ProbPicker p={p} touched={touched} label={tx(q, 'title')}
              onChange={(v) => set({ prob: { ...a.prob, [q.question_id]: v } })} />
          </div>
        )
      })}
      {/* the expert's own "something else is happening" items get a likelihood too */}
      {a.signals.map((s, i) => (
        <div key={'sig' + i} className="card qcard own-q">
          <div className="chips">
            <span className="pill">{t('own_tag')}</span>
            {s.bigger && <span className="chip hot">{t('sig_bigger_tag')}</span>}
            <Chip>{t('deadline', date(forecasts[0]?.closes_at || round.closes_at))}</Chip>
          </div>
          <h3 className="q-title">{s.text}</h3>
          <p className="q-sub">{t('own_prob_q')}</p>
          <ProbPicker p={s.prob} touched={s.prob != null} label={s.text}
            onChange={(v) => set({ signals: a.signals.map((x, j) => (j === i ? { ...x, prob: v } : x)) })} />
        </div>
      ))}
      </>,
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
          <OtherRisk value={a.other_risk} rank={a.ranking.indexOf(OTHER)} full={a.ranking.length >= 3} policy={policy}
            prob={a.other_risk_prob} onProb={(v) => set({ other_risk_prob: v })}
            onToggle={() => set({ ranking: a.ranking.includes(OTHER) ? a.ranking.filter((x) => x !== OTHER) : [...a.ranking, OTHER] })}
            onChange={(text) => set({
              other_risk: text,
              ranking: !text ? a.ranking.filter((x) => x !== OTHER)
                : a.ranking.includes(OTHER) || a.ranking.length >= 3 ? a.ranking : [...a.ranking, OTHER],
            })} />
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
            {a.signals.length > 0 && (
              <div className="recap-row">
                <span>{t('sig_title')}</span>
                <b>{a.signals.map((s) => `${s.text} · ${asPct(s.prob ?? 0.5)}` + (s.bigger ? ` (${t('sig_bigger_tag')})` : '')).join('  ·  ')}</b>
                <button type="button" className="link" onClick={() => goTo('triggers')}>{t('edit')}</button>
              </div>
            )}
            {ranking && (
              <div className="recap-row">
                <span>{t('s_ranking')}</span>
                <b>{a.ranking.length ? a.ranking.map((id, i) => `${i + 1}. ${optLabel(id)}${id === OTHER ? ` · ${asPct(a.other_risk_prob ?? 0.5)}` : ''}`).join('  ') : '—'}</b>
                <button type="button" className="link" onClick={() => goTo('ranking')}>{t('edit')}</button>
              </div>
            )}
          </div>
          <label className="field-label" htmlFor="why">{t('why_label')}</label>
          <textarea id="why" rows="5" maxLength="1000" placeholder={t('why_ph')} value={a.why} onChange={(e) => set({ why: e.target.value })} />
          <div className="field-label">{t('basis_label')}</div>
          <div className="toggles">
            {[...BASIS, 'other'].map((b) => {
              const on = a.basis.includes(b)
              return (
                <button key={b} type="button" aria-pressed={on} className={on ? 'on' : ''}
                  onClick={() => set({ basis: on ? a.basis.filter((x) => x !== b) : [...a.basis, b] })}>{t(`b_${b}`)}</button>
              )
            })}
          </div>
          {a.basis.includes('other') && (
            <div className="own-form own-source">
              <input type="text" maxLength={120} value={a.source_other} placeholder={t('b_other_ph')} aria-label={t('b_other_label')}
                onChange={(e) => set({ source_other: e.target.value })} />
              <span className="muted small">{t('b_other_note')}</span>
            </div>
          )}
          {/* demo data shows peer comments word for word; Lane B's API keeps reasoning for the moderator and shares approved themes */}
          <p className="note">{policy?.enabled === false ? t('why_private_off') : MOCK ? t('why_private') : t('why_private_api')}</p>
          <CommentsPolicyLine policy={policy} />
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
