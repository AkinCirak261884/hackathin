import React from 'react'
import { api, DEMO_TOKEN, MAIN_ROUND_ID, lastSubmission } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'
import { asPct, verdict } from '../stats.js'
import { Head, Chip, Loading } from '../components/ui.jsx'
import { BrierCompare, VerdictBadge } from '../components/charts.jsx'

// One forecast in detail, opened from the profile's "Latest" / "Past predictions" lists: #/guess/<question_id>
export default function Guess({ questionId }) {
  const { t, tx, date } = useT()
  const [tr] = useLoad(() => api.trackRecord(DEMO_TOKEN), [])
  if (!tr) return <Loading />

  const past = tr.history.find((r) => r.question_id === questionId)
  const open = !past && tr.pending.find((p) => p.question_id === questionId)
  const back = <a className="link back-link" href="#/me">{t('g_back')}</a>
  if (!past && !open) return <section className="page">{back}<Head level={1} title={t('g_notfound')} /></section>

  const item = past || open
  const roundId = item.round_id || (open ? MAIN_ROUND_ID : null)
  const mine = roundId ? lastSubmission(roundId) : null

  // previous / next through the same list the user came from
  const list = past ? tr.history : tr.pending
  const i = list.indexOf(item)
  const prev = list[i - 1], next = list[i + 1]

  return (
    <section className="page guess">
      {back}
      <div className="eyebrow">{item.risk_id || item.question_id.split('-')[1]} · {past ? t('g_resolved') : t('g_open')}</div>
      <Head level={1} title={open ? tx(open, 'title') : (past.text.split('? ')[1] || past.text)}
        sub={open ? tx(open) : past.text.split('? ')[1] ? past.text.split('? ')[0] + '?' : null} />
      <div className="chips guess-chips">
        {past && <VerdictBadge verdict={verdict(past.your_prob, past.outcome)} />}
        {past && <span className={`beat ${past.beat_acaps ? 'yes' : 'no'}`}>{past.beat_acaps ? `▲ ${t('beat_acaps')}` : t('acaps_closer')}</span>}
        {past?.practice && <Chip tone="practice">{t('practice_tag')}</Chip>}
        {open?.submitted_at && <Chip tone="new">{t('submitted', date(open.submitted_at))}</Chip>}
        {open?.revised_prob != null && <Chip>{t('rv_revised_to', asPct(open.revised_prob))}</Chip>}
      </div>

      <div className="grid two">
        <article className="card">
          <Head title={past ? t('g_vs') : t('g_vs_open')} sub={past ? t('g_vs_sub') : t('g_vs_open_sub')} />
          <GuessScale you={item.your_prob} acaps={past?.acaps_prob} outcome={past?.outcome} />
          <dl className="facts">
            <div><dt>{t('you')}</dt><dd>{asPct(item.your_prob)}</dd></div>
            {past
              ? <div><dt>{t('g_acaps')}</dt><dd>{asPct(past.acaps_prob)}</dd></div>
              : <div><dt>{t('g_submitted')}</dt><dd>{open.submitted_at ? date(open.submitted_at) : '—'}</dd></div>}
            {past
              ? <div><dt>{t('g_outcome')}</dt><dd>{past.outcome ? t('happened') : t('not_happened')}</dd></div>
              : <div><dt>{t('g_closes')}</dt><dd>{date(open.closes_at)}</dd></div>}
          </dl>
        </article>

        {past && (
          <article className="card">
            <Head title={t('g_score_title')} sub={t('g_score_sub')} />
            <BrierCompare you={past.brier} acaps={past.acaps_brier} />
            <p className="muted small calc">
              {t('g_calc', t('you'), past.your_prob.toFixed(2), past.outcome, past.brier.toFixed(3))}<br />
              {t('g_calc', t('g_acaps'), past.acaps_prob.toFixed(2), past.outcome, past.acaps_brier.toFixed(3))}
            </p>
          </article>
        )}

        {mine?.reasoning_text && (
          <article className="card">
            <Head title={t('g_reason')} />
            <p className="answer-text">{mine.reasoning_text}</p>
          </article>
        )}
      </div>

      {roundId && mine && <p><a className="btn ghost small-btn" href={`#/reveal/${roundId}`}>{t('g_round')}</a></p>}

      <nav className="guess-nav">
        {prev ? <a className="btn ghost small-btn" href={`#/guess/${prev.question_id}`}>{t('g_prev')}</a> : <span />}
        {next ? <a className="btn ghost small-btn" href={`#/guess/${next.question_id}`}>{t('g_next')}</a> : <span />}
      </nav>
    </section>
  )
}

// 0–100% line: your forecast (dot, label above), ACAPS (tick, label below), and the outcome end highlighted.
function GuessScale({ you, acaps, outcome }) {
  const { t } = useT()
  const pos = (p) => ({ left: `${p * 100}%` })
  const shift = (p) => ({ transform: `translateX(-${p * 100}%)` }) // keeps labels inside the track at the ends
  return (
    <div className="gscale" role="img"
      aria-label={`${t('you')} ${asPct(you)}${acaps != null ? ` · ACAPS ${asPct(acaps)}` : ''}${outcome != null ? ` · ${outcome ? t('happened') : t('not_happened')}` : ''}`}>
      <div className="gscale-plot">
        <div className="gscale-track" />
        {outcome != null && <span className={`gscale-out ${outcome ? 'end' : 'start'}`} />}
        <span className="gmark you" style={pos(you)}><i /><em style={shift(you)}>{t('you')} {asPct(you)}</em></span>
        {acaps != null && <span className="gmark acaps" style={pos(acaps)}><i /><em style={shift(acaps)}>ACAPS {asPct(acaps)}</em></span>}
      </div>
      <div className="fdots-ends">
        <span>0%{outcome === 0 ? ` · ${t('not_happened')}` : ''}</span>
        <span>50%</span>
        <span>{outcome === 1 ? `${t('happened')} · ` : ''}100%</span>
      </div>
    </div>
  )
}
