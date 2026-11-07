import React from 'react'
import { api, DEMO_TOKEN, demoPseudonym } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, recordSummary } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { RecordHero, BrierCompare, ProbMeter } from '../components/charts.jsx'
import { PastCard } from './Record.jsx'

// Track record follows Lane A's analysis/leaderboard.py track_record() output (contracts/schemas/track-record).
export default function Profile() {
  const { t, tx, date } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  if (!tr) return <Loading />
  const rec = recordSummary(tr.history)
  const counted = tr.forecasts_until_counted === 0

  return (
    <section className="page">
      <div className="profile-head">
        <div className="avatar" aria-hidden="true">{demoPseudonym()[0]}</div>
        <div>
          <Head level={1} title={`${t('profile')} · ${demoPseudonym()}`} sub={t('profile_sub')} />
          <div className="chips">
            {tr.super_estimator && <span className="badge-star" title={t('super_est_d')}>{t('super_est')}</span>}
          </div>
        </div>
      </div>

      {!counted && (
        <article className="card progress-card">
          <Head title={t('not_ranked', tr.forecasts_until_counted)} sub={t('not_ranked_d', tr.n_resolved, tr.min_resolved)} />
          <div className="steps-meter" aria-hidden="true">
            {Array.from({ length: tr.min_resolved }, (_, i) => <span key={i} className={i < tr.n_resolved ? 'done' : ''} />)}
          </div>
        </article>
      )}

      <div className="grid two">
        <a className="card" href="#/record">
          <RecordHero {...rec} />
          <span className="item-more center">{t('g_details')}</span>
        </a>
        <a className="card" href="#/accuracy">
          <Head title={t('brier_title')} sub={t('brier_sub')} />
          <BrierCompare you={tr.mean_brier} acaps={tr.acaps_baseline_brier} />
          <p className="takeaway">{t('beat_acaps_n', tr.n_beat_acaps, tr.n_resolved)}</p>
          <span className="item-more">{t('g_details')}</span>
        </a>
      </div>

      <Head title={t('latest')} sub={t('latest_sub')} />
      <div className="list">
        {tr.pending.map((p) => (
          <a key={p.question_id} className="card item" href={`#/guess/${p.question_id}`}>
            <div className="chips">
              <Chip>{t('deadline', date(p.closes_at))}</Chip>
              {p.submitted_at && <Chip tone="new">{t('submitted', date(p.submitted_at))}</Chip>}
            </div>
            <h3 className="q-title">{tx(p, 'title')}</h3>
            <p className="q-sub">{tx(p)}</p>
            <div className="item-prob"><ProbMeter p={p.your_prob} /><b>{asPct(p.your_prob)}</b></div>
            <span className="item-more">{t('g_details')}</span>
          </a>
        ))}
      </div>

      <Head title={t('past')} sub={t('past_sub')} />
      <div className="list">
        {tr.history.map((r) => <PastCard key={r.question_id} r={r} />)}
      </div>

      {tr.impact?.length > 0 && (
        <>
          <Head title={t('impact_title')} sub={t('impact_sub')} />
          {tr.impact.map((i) => (
            <article key={i.date + i.risk_id} className="card impact">
              <div className="chips"><Chip>{i.risk_id}</Chip><span className="muted small">{date(i.date)}</span></div>
              <p className="small">{i.note}</p>
            </article>
          ))}
        </>
      )}
    </section>
  )
}
