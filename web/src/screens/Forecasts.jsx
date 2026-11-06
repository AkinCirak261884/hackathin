import React, { useState } from 'react'
import { api, anonToken, DEMO_INVITE, DEMO_TOKEN } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, likelihoodKey } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { ProbMeter } from '../components/charts.jsx'
import SubTabs from '../components/SubTabs.jsx'

const PRESETS = [0.1, 0.3, 0.5, 0.7, 0.9]
const daysUntil = (iso) => Math.ceil((new Date(iso) - new Date()) / 86400000)

function ForecastCard({ f, onSaved }) {
  const { t, tx, date } = useT()
  const answered = f.your_prob != null
  const [editing, setEditing] = useState(!answered)
  const [p, setP] = useState(f.your_prob ?? 0.5)
  const [touched, setTouched] = useState(answered)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const set = (v) => { setP(v); setTouched(true) }

  async function save() {
    setBusy(true)
    const body = { invite_token: DEMO_INVITE, tier: 'anonymous', prob: p, anon_token: await anonToken() }
    const updated = await api.updateForecast(f.question_id, body)
    setBusy(false); setEditing(false); setSaved(true)
    onSaved(updated)
  }

  return (
    <article className={`card fcard ${answered ? '' : 'todo'}`}>
      <div className="chips">
        <Chip tone={f.horizon === 'short' ? 'new' : ''}>{f.horizon === 'short' ? t('short_term') : t('six_months')}</Chip>
        <Chip>{t('deadline', date(f.closes_at))}</Chip>
        <Chip>{t('in_days', daysUntil(f.closes_at))}</Chip>
        {f.synthetic && <span className="pill">{t('synthetic')}</span>}
      </div>
      <h3 className="q-title">{tx(f, 'title')}</h3>
      <p className="q-sub">{tx(f)}</p>

      {answered && !editing && (
        <div className="fc-now">
          <div className="kpis">
            <div><span className="kpi-num you-ink">{asPct(f.your_prob)}</span><span className="kpi-label">{t('your_forecast')}</span></div>
            {f.group && <div><span className="kpi-num">{asPct(f.group.median)}</span><span className="kpi-label">{t('group_median')} · n={f.group.n}</span></div>}
          </div>
          <ProbMeter p={f.your_prob} marker={f.group?.median} />
          <div className="fc-foot">
            <span className="muted small">{t('updated', date(f.your_updated_at), f.n_updates)} · {t('marker_median')}</span>
            <button className="btn ghost small-btn" onClick={() => { setEditing(true); setSaved(false) }}>{t('update')}</button>
          </div>
          {saved && <p className="saved">✓ {t('saved')}</p>}
        </div>
      )}

      {!answered && <p className="lock">🔒 {t('hidden_group')}</p>}

      {editing && (
        <div className="fc-edit">
          <div className={`prob-read ${touched ? '' : 'untouched'}`}>
            <span className="big">{asPct(p)}</span><span className="muted">{t(likelihoodKey(p))}</span>
          </div>
          <input type="range" min="0" max="100" step="5" value={Math.round(p * 100)} aria-label={tx(f, 'title')}
            onChange={(e) => set(e.target.value / 100)} />
          <div className="presets">
            {PRESETS.map((v) => <button key={v} type="button" className={touched && p === v ? 'on' : ''} onClick={() => set(v)}>{asPct(v)}</button>)}
          </div>
          <div className="fc-actions">
            {answered && <button className="btn ghost" onClick={() => { setEditing(false); setP(f.your_prob) }}>{t('cancel')}</button>}
            <button className="btn" disabled={busy || !touched} onClick={save}>{t('save_forecast')}</button>
          </div>
        </div>
      )}
    </article>
  )
}

export default function Forecasts() {
  const { t, date } = useT()
  const [list, setList] = useState(null)
  const [loaded] = useLoad(() => api.forecastsOpen('TCD', DEMO_TOKEN), [])
  const items = list || loaded
  if (!items || !loaded) return <Loading />
  const replace = (u) => setList(items.map((x) => (x.question_id === u.question_id ? u : x)))
  // group by status at load time, so a card doesn't jump sections right after you save it
  const todoIds = new Set(loaded.filter((f) => f.your_prob == null).map((f) => f.question_id))
  const todo = items.filter((f) => todoIds.has(f.question_id))
  const mine = items.filter((f) => !todoIds.has(f.question_id))
  const next = [...items].sort((a, b) => a.closes_at.localeCompare(b.closes_at))[0]

  return (
    <section className="page">
      <SubTabs current="open" />
      <Head level={1} eyebrow={t('mode_forecast')} title={t('fc_title')} sub={t('fc_sub')} />
      <div className="kpi-strip">
        <div><b>{items.length}</b><span>{t('fc_kpi_open')}</span></div>
        <div><b>{items.filter((f) => f.your_prob == null).length}</b><span>{t('fc_kpi_todo')}</span></div>
        <div><b>{next ? date(next.closes_at) : '—'}</b><span>{t('fc_kpi_next')}</span></div>
      </div>
      {todo.length > 0 && (
        <>
          <Head title={t('fc_todo')} sub={t('fc_todo_sub')} />
          <div className="list">{todo.map((f) => <ForecastCard key={f.question_id} f={f} onSaved={replace} />)}</div>
        </>
      )}
      <Head title={t('fc_mine')} sub={t('fc_mine_sub')} />
      <div className="list">{mine.map((f) => <ForecastCard key={f.question_id} f={f} onSaved={replace} />)}</div>
    </section>
  )
}
