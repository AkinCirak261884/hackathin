import React from 'react'
import { useT } from '../i18n.jsx'

// Second-level switch inside the Forecasts tab: open questions | my record
export default function SubTabs({ current }) {
  const { t } = useT()
  return (
    <nav className="subtabs" aria-label={t('mode_forecast')}>
      <a href="#/forecasts" className={current === 'open' ? 'on' : ''} aria-current={current === 'open' ? 'page' : undefined}>{t('sub_open')}</a>
      <a href="#/me" className={current === 'record' ? 'on' : ''} aria-current={current === 'record' ? 'page' : undefined}>{t('sub_record')}</a>
    </nav>
  )
}
