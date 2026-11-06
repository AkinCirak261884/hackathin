import React from 'react'
import { api, DEMO_TOKEN, DEMO_PSEUDONYM } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, recordSummary, verdict } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { RecordHero, BrierCompare, ProbMeter, VerdictBadge } from '../components/charts.jsx'

export default function Profile() {
  const { t, tx, date } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  if (!tr) return <Loading />
  const rec = recordSummary(tr.resolved)

  return (
    <section className="page">
      <div className="profile-head">
        <div className="avatar" aria-hidden="true">{DEMO_PSEUDONYM[0]}</div>
        <Head level={1} title={`${t('profile')} · ${DEMO_PSEUDONYM}`} sub={t('profile_sub')} />
      </div>

      <div className="grid">
        <article className="card"><RecordHero {...rec} /></article>
        <article className="card">
          <Head title={t('brier_title')} sub={t('brier_sub')} />
          <BrierCompare you={tr.mean_brier} acaps={tr.acaps_mean_brier} />
        </article>
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
        {tr.resolved.map((r) => (
          <article key={r.question_id} className="card item">
            <div className="item-top">
              <VerdictBadge verdict={verdict(r.your_prob, r.outcome)} />
              <span className="muted small">{r.outcome ? t('happened') : t('not_happened')} · Brier {r.brier.toFixed(2)}</span>
            </div>
            <p className="q-sub">{r.text}</p>
            <div className="item-prob"><ProbMeter p={r.your_prob} /><b>{t('you_said', asPct(r.your_prob))}</b></div>
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
