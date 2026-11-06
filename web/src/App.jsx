import React, { useEffect, useState } from 'react'
import { LangProvider, useT } from './i18n.jsx'
import { MOCK } from './api.js'
import Home from './screens/Home.jsx'
import Pulse from './screens/Pulse.jsx'
import Reveal from './screens/Reveal.jsx'
import Forecasts from './screens/Forecasts.jsx'
import Profile from './screens/Profile.jsx'
import PublicPage from './screens/Public.jsx'
import Signpost from './screens/Signpost.jsx'

// Tiny hash router.
//   Ground truth: #/ (check-ins) · #/pulse/RD-R1043-1 · #/reveal/RD-R1043-1 · #/signpost
//   Forecasts:    #/forecasts (open questions) · #/me (my record + leaderboard)
//   Public:       #/public
function useRoute() {
  const get = () => window.location.hash.replace(/^#\/?/, '').split('?')[0].split('/')
  const [route, setRoute] = useState(get)
  useEffect(() => {
    const on = () => { setRoute(get()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

const SECTION = { '': 'ground', pulse: 'ground', reveal: 'ground', signpost: 'ground', forecasts: 'forecast', me: 'forecast', public: 'public' }

const Icon = {
  ground: <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h16M6 20V10l6-5 6 5v10" /><path d="M10 20v-5h4v5" /></svg>,
  forecast: <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19l5-6 4 3 7-9" /><circle cx="20" cy="7" r="1.5" /></svg>,
  public: <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" /></svg>,
}

function Shell() {
  const { t, lang, setLang } = useT()
  const [page, id] = useRoute()
  const section = SECTION[page] ?? 'ground'
  const focus = page === 'pulse' // hide tab bar during the survey so the action bar owns the thumb zone
  const modes = [
    { key: 'ground', href: '#/', label: t('mode_ground'), hint: t('mode_ground_d') },
    { key: 'forecast', href: '#/forecasts', label: t('mode_forecast'), hint: t('mode_forecast_d') },
  ]
  const tabs = [...modes, { key: 'public', href: '#/public', label: t('nav_public') }]
  const screens = {
    '': <Home />,
    pulse: <Pulse roundId={id} />,
    reveal: <Reveal roundId={id} />,
    forecasts: <Forecasts />,
    me: <Profile />,
    public: <PublicPage />,
    signpost: <Signpost />,
  }
  return (
    <div className={`app ${focus ? 'focus' : ''} mode-${section}`}>
      <header className="top">
        <a href="#/" className="brand"><span className="logo" aria-hidden="true" />{t('app')}</a>
        <nav className="modeswitch" aria-label="Sections">
          {modes.map((m) => (
            <a key={m.key} href={m.href} title={m.hint} className={section === m.key ? 'on' : ''}
              aria-current={section === m.key ? 'page' : undefined}>{Icon[m.key]}{m.label}</a>
          ))}
        </nav>
        <a href="#/public" className={`top-link ${section === 'public' ? 'on' : ''}`}>{t('nav_public')}</a>
        {MOCK && <span className="pill demo-pill">{t('mock')}</span>}
        <button className="lang" onClick={() => setLang(lang === 'en' ? 'fr' : 'en')} aria-label="Language">
          {lang === 'en' ? 'FR' : 'EN'}
        </button>
      </header>
      <main>{screens[page] ?? screens['']}</main>
      {!focus && (
        <nav className="tabbar" aria-label="Sections">
          {tabs.map((x) => (
            <a key={x.key} href={x.href} className={section === x.key ? 'on' : ''} aria-current={section === x.key ? 'page' : undefined}>
              {Icon[x.key]}<span>{x.label}</span>
            </a>
          ))}
        </nav>
      )}
    </div>
  )
}

export default function App() {
  return <LangProvider><Shell /></LangProvider>
}
