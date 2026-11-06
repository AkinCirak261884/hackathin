import React from 'react'
import { api, DEMO_TOKEN, demoPseudonym } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, recordSummary, verdict } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { RecordHero, BrierCompare, ProbMeter, VerdictBadge, Leaderboard } from '../components/charts.jsx'

// Track record + leaderboard follow Lane A's analysis/leaderboard.py output (contracts/schemas/track-record, leaderboard).
export default function Profile() {
  const { t, tx, date } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  const [lb] = useLoad(() => api.leaderboard('TCD', DEMO_TOKEN), [])
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
            {tr.super_estimator && <span className="badge-star" title={t('super_est_d')}>★ {t('super_est')}</span>}
            {tr.rank && <Chip>{t('rank_of', tr.rank, tr.n_ranked)} {t('rank_label')}</Chip>}
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
        <article className="card"><RecordHero {...rec} /></article>
        <article className="card">
          <Head title={t('brier_title')} sub={t('brier_sub')} />
          <BrierCompare you={tr.mean_brier} acaps={tr.acaps_baseline_brier} />
          <p className="takeaway">{t('beat_acaps_n', tr.n_beat_acaps, tr.n_resolved)}</p>
        </article>
        {lb && (
          <article className="card lb-card">
            <Head title={t('lb_title')} sub={t('lb_sub')} />
            <Leaderboard data={lb} />
          </article>
        )}
      </div>

      <Head title={t('latest')} sub={t('latest_sub')} />
      <div className="list">
        {tr.pending.map((p) => (
          <article key={p.question_id} className="card item">
            <div className="chips">
              <Chip>{t('deadline', date(p.closes_at))}</Chip>
              {p.submitted_at && <Chip tone="new">{t('submitted', date(p.submitted_at))}</Chip>}
            </div>
            <h3 className="q-title">{tx(p, 'title')}</h3>
            <p className="q-sub">{tx(p)}</p>
            <div className="item-prob"><ProbMeter p={p.your_prob} /><b>{asPct(p.your_prob)}</b></div>
          </article>
        ))}
      </div>

      <Head title={t('past')} sub={t('past_sub')} />
      <div className="list">
        {tr.history.map((r) => (
          <article key={r.question_id} className="card item">
            <div className="item-top">
              <span className="chips">
                <VerdictBadge verdict={verdict(r.your_prob, r.outcome)} />
                <span className={`beat ${r.beat_acaps ? 'yes' : 'no'}`}>{r.beat_acaps ? `▲ ${t('beat_acaps')}` : t('acaps_closer')}</span>
              </span>
              <span className="muted small">{r.outcome ? t('happened') : t('not_happened')}</span>
            </div>
            <p className="q-sub">{r.text}</p>
            <div className="item-prob">
              <ProbMeter p={r.your_prob} marker={r.acaps_prob} />
              <b>{t('you_said', asPct(r.your_prob))}</b>
            </div>
            <div className="muted small">{t('acaps_said', asPct(r.acaps_prob))} · Brier {r.brier.toFixed(2)} vs {r.acaps_brier.toFixed(2)}</div>
          </article>
        ))}
      </div>

      {tr.impact?.length > 0 && (
        <>
          <Head title={t('impact_title')} />
          {tr.impact.map((i) => <p key={i.date} className="card small">★ {i.note}</p>)}
        </>
      )}
    </section>
  )
}
