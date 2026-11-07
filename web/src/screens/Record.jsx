import React from 'react'
import { api, DEMO_TOKEN } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, recordSummary, verdict } from '../stats.js'
import { Head, Loading } from '../components/ui.jsx'
import { RecordHero, BrierCompare, ProbMeter, VerdictBadge } from '../components/charts.jsx'

const short = (text) => text.split('? ')[1] || text

// One resolved forecast as a clickable card. Shared by the profile and the record page.
export function PastCard({ r }) {
  const { t } = useT()
  return (
    <a className="card item" href={`#/guess/${r.question_id}`}>
      <div className="item-top">
        <span className="chips">
          <VerdictBadge verdict={verdict(r.your_prob, r.outcome)} />
          <span className={`beat ${r.beat_acaps ? 'yes' : 'no'}`}>{r.beat_acaps ? t('beat_acaps') : t('acaps_closer')}</span>
        </span>
        <span className="muted small">{r.outcome ? t('happened') : t('not_happened')}</span>
      </div>
      <p className="q-sub">{r.text}</p>
      <div className="item-prob">
        <ProbMeter p={r.your_prob} marker={r.acaps_prob} />
        <b>{t('you_said', asPct(r.your_prob))}</b>
      </div>
      <div className="muted small">{t('acaps_said', asPct(r.acaps_prob))} · Brier {r.brier.toFixed(2)} vs {r.acaps_brier.toFixed(2)}</div>
      <span className="item-more">{t('g_details')}</span>
    </a>
  )
}

// #/record: every resolved forecast behind the "x of y correct" card
export function RecordPage() {
  const { t } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  if (!tr) return <Loading />
  const rec = recordSummary(tr.history)
  const nocall = rec.verdicts.filter((v) => v === 'nocall').length
  return (
    <section className="page">
      <a className="link back-link" href="#/me">{t('g_back')}</a>
      <Head level={1} title={t('rec_title')} sub={t('rec_sub')} />
      <div className="grid two">
        <article className="card"><RecordHero {...rec} /></article>
        <article className="card">
          <Head title={t('rec_how')} />
          <ul className="explain">
            <li>{t('rec_how_1')}</li>
            <li>{t('rec_how_2')}</li>
            <li>{t('rec_how_3')}</li>
          </ul>
          <dl className="facts">
            <div><dt>{t('v_correct')}</dt><dd>{rec.correct}</dd></div>
            <div><dt>{t('v_wrong')}</dt><dd>{rec.total - rec.correct}</dd></div>
            <div><dt>{t('v_nocall')}</dt><dd>{nocall}</dd></div>
          </dl>
        </article>
      </div>
      <Head title={t('past')} sub={t('past_sub')} />
      <div className="list">{tr.history.map((r) => <PastCard key={r.question_id} r={r} />)}</div>
    </section>
  )
}

// Comparison baselines. Each one is offered only when every resolved question has its number.
const BASELINES = {
  acaps: { prob: 'acaps_prob', brier: 'acaps_brier', beat: 'beat_acaps', label: 'vs_acaps', win: 'beat_acaps', lose: 'acaps_closer' },
  group: { prob: 'group_median_prob', brier: 'group_brier', beat: 'beat_group', label: 'vs_group', win: 'beat_group', lose: 'group_closer' },
}
const VS_KEY = 'gt_accuracy_vs' // per-viewer convenience only
function useBaseline(available) {
  const [vs, setVs] = React.useState(() => { try { return localStorage.getItem(VS_KEY) || 'acaps' } catch { return 'acaps' } })
  const pick = (k) => { setVs(k); try { localStorage.setItem(VS_KEY, k) } catch {} }
  return [available.includes(vs) ? vs : 'acaps', pick]
}

// #/accuracy: the Brier score card broken down question by question, against a baseline the expert picks
export function AccuracyPage() {
  const { t } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  const available = tr ? Object.keys(BASELINES).filter((k) => tr.history.length && tr.history.every((r) => r[BASELINES[k].brier] != null)) : ['acaps']
  const [vs, setVs] = useBaseline(available)
  if (!tr) return <Loading />
  const b = BASELINES[vs]
  const h = tr.history, n = h.length
  const counted = tr.forecasts_until_counted === 0
  const baseMean = vs === 'acaps' ? tr.acaps_baseline_brier : n ? +(h.reduce((s, r) => s + r[b.brier], 0) / n).toFixed(4) : null
  const nBeat = h.filter((r) => r[b.beat]).length
  return (
    <section className="page">
      <a className="link back-link" href="#/me">{t('g_back')}</a>
      <Head level={1} title={t('brier_title')} sub={t('acc_sub')} />

      {available.length > 1 && (
        <div className="vs-picker" role="radiogroup" aria-label={t('vs_label')}>
          <span className="vs-label">{t('vs_label')}</span>
          <div className="toggles">
            {available.map((k) => (
              <button key={k} role="radio" aria-checked={vs === k} className={vs === k ? 'on' : ''} onClick={() => setVs(k)}>
                {t(BASELINES[k].label)}
              </button>
            ))}
          </div>
          <p className="muted small">{t(`vs_${vs}_d`)}</p>
        </div>
      )}

      <div className="grid two">
        <article className="card">
          <Head title={t('acc_overall')} sub={t('acc_overall_sub', n)} />
          {n > 0 && tr.mean_brier != null ? <BrierCompare you={tr.mean_brier} acaps={baseMean} vs={vs} /> : <p className="muted small">{t('brier_none')}</p>}
          <p className="takeaway">{t(vs === 'group' ? 'beat_group_n' : 'beat_acaps_n', nBeat, n)}</p>
          <p className="muted small">
            {!counted ? t('not_ranked', tr.forecasts_until_counted)
              : tr.super_estimator ? t('acc_super_yes') : t('acc_super_no')}
          </p>
        </article>
        <article className="card">
          <Head title={t('acc_how')} />
          <ul className="explain">
            <li>{t('acc_how_1')}</li>
            <li>{t('acc_how_2')}</li>
            <li>{t('acc_how_3')}</li>
            <li>{t('acc_how_4', tr.min_resolved)}</li>
          </ul>
        </article>
      </div>

      <Head title={t('acc_per_q')} sub={t('acc_per_q_sub', t(b.label))} />
      <div className="list">
        {h.map((r) => (
          <a key={r.question_id} className="card item" href={`#/guess/${r.question_id}`}>
            <div className="item-top">
              <span className={`beat ${r[b.beat] ? 'yes' : 'no'}`}>{r[b.beat] ? t(b.win) : t(b.lose)}</span>
              <span className="muted small">
                {t('you_said', asPct(r.your_prob))} · {t(b.label)} {asPct(r[b.prob])} · {r.outcome ? t('happened') : t('not_happened')}
              </span>
            </div>
            <p className="q-sub">{short(r.text)}</p>
            <BrierCompare you={r.brier} acaps={r[b.brier]} vs={vs} />
            <span className="item-more">{t('g_details')}</span>
          </a>
        ))}
      </div>
    </section>
  )
}
