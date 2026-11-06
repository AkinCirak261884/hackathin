import React from 'react'
import { api } from '../api.js'
import { useLoad } from '../useLoad.js'
import { useT } from '../i18n.jsx'

export default function Home() {
  const { t } = useT()
  const [rounds] = useLoad(() => api.openRounds('TCD'), [])
  if (!rounds) return <p className="muted">…</p>
  return (
    <section>
      <h1>{t('openRounds')}</h1>
      {rounds.map((r) => (
        <article key={r.round_id} className="card">
          <div className="meta">{r.risk_id} · {t('minutes', r.est_minutes)}</div>
          <h2>{r.title}</h2>
          <a className="btn" href={`#/${r.answered ? 'reveal' : 'pulse'}/${r.round_id}`}>
            {r.answered ? t('answered') : t('start')}
          </a>
        </article>
      ))}
      <p><a href="#/signpost" className="muted">{t('signpost')}</a></p>
    </section>
  )
}
