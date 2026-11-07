import React from 'react'
import { api, DEMO_TOKEN, demoPseudonym } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, recordSummary } from '../stats.js'
import { Head, Chip, Loading, LoadError } from '../components/ui.jsx'
import { RecordHero, BrierCompare, ProbMeter } from '../components/charts.jsx'
import { PastCard } from './Record.jsx'

// Track record follows Lane A's analysis/leaderboard.py track_record() output (contracts/schemas/track-record).
export default function Profile() {
  const { t, tx, date } = useT()
  const [tr, trErr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  const [rounds] = useLoad(() => api.openRounds('TCD'), [])
  if (trErr) return <LoadError error={trErr} />
  if (!tr) return <Loading />
  const rec = recordSummary(tr.history)
  const counted = tr.forecasts_until_counted === 0

  return (
    <section className="page">
      <div className="profile-head">
        {demoPseudonym() && <div className="avatar" aria-hidden="true">{demoPseudonym()[0]}</div>}
        <div>
          <Head level={1} title={demoPseudonym() ? `${t('profile')} · ${demoPseudonym()}` : t('profile')} sub={t('profile_sub')} />
          <div className="chips">
            {tr.super_estimator && <span className="badge-star" title={t('super_est_d')}>{t('super_est')}</span>}
          </div>
        </div>
      </div>

      <ImpactCard impact={tr.impact || []} />
      <NextCard rounds={rounds} pending={tr.pending || []} />

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
          {tr.n_resolved > 0 ? <BrierCompare you={tr.mean_brier} acaps={tr.acaps_baseline_brier} /> : <p className="muted small">{t('brier_none')}</p>}
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
    </section>
  )
}

// Why come back, part 1: proof that what you said changed ACAPS's analysis (the strongest motivator for experts).
function ImpactCard({ impact }) {
  const { t, date } = useT()
  const n = impact.length
  return (
    <article className="card impact-hero">
      <div className="eyebrow">{t('impact_eyebrow')}</div>
      {n > 0 ? (
        <>
          <h2 className="impact-headline"><span className="impact-num">{n}</span>{t('impact_count', n)}</h2>
          <p className="muted small">{t('impact_sub')}</p>
          <ul className="impact-list">
            {impact.map((i) => (
              <li key={i.date + i.risk_id}>
                <div className="chips"><Chip>{i.risk_id}</Chip><span className="muted small">{date(i.date)}</span></div>
                <p>{i.note}</p>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <>
          <h2 className="impact-headline">{t('impact_empty_title')}</h2>
          <p className="muted small">{t('impact_empty')}</p>
        </>
      )}
    </article>
  )
}

// Why come back, part 2: something waiting now, and a date when you'll find out how your forecasts did.
// Deliberately no streaks or points: the brief asks for quality of information, not engagement metrics.
function NextCard({ rounds, pending }) {
  const { t, date } = useT()
  const open = (rounds || []).filter((r) => !r.answered)
  const next = open[0]
  const first = pending.map((p) => p.closes_at).filter(Boolean).sort()[0]
  const nFirst = first ? pending.filter((p) => p.closes_at && p.closes_at.slice(0, 10) === first.slice(0, 10)).length : 0
  return (
    <article className="card next-card">
      <Head title={t('next_title')} />
      <div className="next-row">
        <div>
          <b>{open.length ? t('next_waiting', open.length) : t('next_none')}</b>
          <span className="muted small">{next ? `${next.title} · ${t('minutes', next.est_minutes)}` : t('next_none_d')}</span>
        </div>
        {next && <a className="btn small-btn" href={`#/pulse/${next.round_id}`}>{t('start')}</a>}
      </div>
      {first && (
        <div className="next-row">
          <div>
            <b>{t('next_results', nFirst, date(first))}</b>
            <span className="muted small">{t('next_results_d')}</span>
          </div>
        </div>
      )}
    </article>
  )
}
