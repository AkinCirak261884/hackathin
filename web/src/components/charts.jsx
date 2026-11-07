import React, { useState } from 'react'
import { useT } from '../i18n.jsx'
import { asPct, r05 } from '../stats.js'

// Each answer type has its own chart, so it reads at a glance:
//   rating   -> 3-part diverging bar (too low | about right | too high)
//   forecast -> dot plot on 0-100% with your dot, median line and middle-half band
//   ranking  -> ranked horizontal bars (one hue)
//   profile  -> hero "4 of 5" + verdict chips, Brier you-vs-ACAPS bars, mini meters
// Colors come from CSS tokens in styles.css (validated: group blue vs you orange, light + dark).

export function RatingBar({ label, counts, you }) {
  const { t } = useT()
  const order = ['too_low', 'agree', 'too_high']
  const n = order.reduce((s, k) => s + (counts[k] || 0), 0) || 1
  return (
    <div className="rating-row">
      <div className="rating-label">{label}</div>
      <div className="seg-bar" role="img"
        aria-label={order.map((k) => `${t(k)}: ${counts[k] || 0}`).join(', ')}>
        {order.map((k) => {
          const c = counts[k] || 0
          if (!c) return null
          const w = (c / n) * 100
          return (
            <div key={k} className={`seg-part ${k}`} style={{ width: `${w}%` }} title={`${t(k)}: ${c}`}>
              {w >= 12 && <span>{c}</span>}
              {you === k && <i className="you-caret" aria-label={t('you')} />}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function RatingLegend() {
  const { t } = useT()
  return (
    <div className="legend">
      <span><i className="sw too_low" />{t('too_low')}</span>
      <span><i className="sw agree" />{t('agree')}</span>
      <span><i className="sw too_high" />{t('too_high')}</span>
      <span><i className="sw-caret" />{t('you')}</span>
    </div>
  )
}

export function ForecastDots({ values, you, median, p25, p75 }) {
  const { t } = useT()
  const [active, setActive] = useState(null)
  // others = all answers minus one copy of yours
  const others = [...values]
  if (you != null) {
    const i = others.indexOf(r05(you))
    if (i >= 0) others.splice(i, 1)
  }
  // stack equal values upwards so every dot stays visible
  const seen = {}
  const dots = others.map((v, i) => {
    const level = (seen[v] = (seen[v] ?? -1) + 1)
    return { key: `o${i}`, v, level, you: false }
  })
  if (you != null) dots.push({ key: 'you', v: r05(you), level: (seen[r05(you)] ?? -1) + 1, you: true, exact: you })
  const maxLevel = Math.max(0, ...dots.map((d) => d.level))
  const plotH = 40 + maxLevel * 14

  return (
    <div className="fdots" onMouseLeave={() => setActive(null)}>
      <div className="fdots-plot" style={{ height: plotH }}>
        <div className="fdots-band" style={{ left: `${p25 * 100}%`, width: `${Math.max(0.5, (p75 - p25) * 100)}%` }} />
        <div className="fdots-median" style={{ left: `${median * 100}%` }} title={`${t('group_median')} ${asPct(median)}`} />
        {dots.map((d) => (
          <button key={d.key} type="button"
            className={`fdot ${d.you ? 'you' : ''} ${active === d.key ? 'active' : ''}`}
            style={{ left: `${d.v * 100}%`, bottom: 6 + d.level * 14 }}
            aria-label={`${d.you ? t('you') : ''} ${asPct(d.exact ?? d.v)}`}
            onMouseEnter={() => setActive(d.key)} onFocus={() => setActive(d.key)}
            onClick={() => setActive(active === d.key ? null : d.key)}>
            <i />
            {(active === d.key || d.you) && (
              <span className={`tip ${d.you && active !== d.key ? 'tip-you' : ''}`}>
                {d.you ? `${t('you')} ${asPct(d.exact)}` : asPct(d.v)}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="fdots-axis">
        {[0, 25, 50, 75, 100].map((x) => <span key={x} style={{ left: `${x}%` }}>{x}%</span>)}
      </div>
      <div className="fdots-ends"><span>{t('l_very_unlikely')}</span><span>{t('l_very_likely')}</span></div>
    </div>
  )
}

export function ForecastLegend() {
  const { t } = useT()
  return (
    <div className="legend">
      <span><i className="sw dot-group" />Experts</span>
      <span><i className="sw dot-you" />{t('you')}</span>
      <span><i className="sw band" />{t('middle_half')}</span>
      <span><i className="sw median" />{t('group_median')}</span>
    </div>
  )
}

export function RankingBars({ ranking, options, yours = [] }) {
  const { t, tx } = useT()
  const byId = Object.fromEntries(options.map((o) => [o.option_id, o]))
  const max = Math.max(1, ...ranking.map((r) => r.points))
  return (
    <ol className="rank-bars">
      {ranking.map((r) => {
        const o = byId[r.option_id]
        const mine = yours.indexOf(r.option_id)
        return (
          <li key={r.option_id} title={`${r.points} pts · ${r.first_choice}× #1`}>
            <div className="rank-label">
              <span>{tx(o, 'label')}</span>
              {o.synthetic && <span className="pill">{t('synthetic')}</span>}
              {mine >= 0 && <span className="your-pick">{t('your_pick', mine + 1)}</span>}
            </div>
            <div className="rank-track">
              <div className="rank-fill" style={{ width: `${(r.points / max) * 100}%` }} />
              <span className="rank-val">{r.points}</span>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

const ICON = { correct: '✓', wrong: '✗', nocall: '–' }

export function RecordHero({ correct, total, verdicts }) {
  const { t } = useT()
  return (
    <div className="record-hero">
      <div className="hero-num">{t('correct_of', correct, total)}</div>
      <div className="hero-label">{t('correct_label')}</div>
      <div className="verdict-row" aria-hidden="true">
        {verdicts.map((v, i) => <span key={i} className={`vchip ${v}`}>{ICON[v]}</span>)}
      </div>
      <div className="muted small">{t('correct_hint')}</div>
    </div>
  )
}

export function VerdictBadge({ verdict }) {
  const { t } = useT()
  return <span className={`vbadge ${verdict}`}>{ICON[verdict]} {t(`v_${verdict}`)}</span>
}

// `vs` picks the baseline row: 'acaps' (default) or 'group' (panel middle answer)
export function BrierCompare({ you, acaps, vs = 'acaps' }) {
  const { t } = useT()
  const max = Math.max(0.25, you, acaps)
  const rows = [
    { k: 'you', label: t('you'), v: you },
    { k: vs, label: vs === 'group' ? t('vs_group') : t('acaps_baseline'), v: acaps },
  ]
  return (
    <div className="brier">
      {rows.map((r) => (
        <div key={r.k} className="brier-row">
          <span className="brier-label">{r.label}</span>
          <div className="brier-track">
            <div className={`brier-fill ${r.k}`} style={{ width: `${(r.v / max) * 100}%` }} />
          </div>
          <span className="brier-val">{r.v.toFixed(3)}</span>
        </div>
      ))}
    </div>
  )
}

export function ProbMeter({ p, marker }) {
  return (
    <div className="meter" role="img" aria-label={marker != null ? `${asPct(p)} · ACAPS ${asPct(marker)}` : asPct(p)}>
      <div className="meter-fill" style={{ width: `${p * 100}%` }} />
      <span className="meter-mid" />
      {marker != null && <span className="meter-marker" style={{ left: `${marker * 100}%` }} />}
    </div>
  )
}
