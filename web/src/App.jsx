import React, { useEffect, useState } from 'react'
import { LangProvider, useT } from './i18n.jsx'
import { MOCK } from './api.js'
import Home from './screens/Home.jsx'
import Pulse from './screens/Pulse.jsx'
import Reveal from './screens/Reveal.jsx'
import TrackRecord from './screens/TrackRecord.jsx'
import PublicPage from './screens/Public.jsx'
import Signpost from './screens/Signpost.jsx'

// Tiny hash router: #/pulse/RD-R1043-1, #/reveal/RD-R1043-1, #/me, #/public, #/signpost
function useRoute() {
  const get = () => window.location.hash.replace(/^#\/?/, '').split('/')
  const [route, setRoute] = useState(get)
  useEffect(() => {
    const on = () => { setRoute(get()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

function Shell() {
  const { t, lang, setLang } = useT()
  const [page, id] = useRoute()
  const screens = {
    '': <Home />,
    pulse: <Pulse roundId={id} />,
    reveal: <Reveal roundId={id} />,
    me: <TrackRecord />,
    public: <PublicPage />,
    signpost: <Signpost />,
  }
  return (
    <div className="app">
      <header className="top">
        <a href="#/" className="brand">{t('app')}</a>
        {MOCK && <span className="pill">{t('mock')}</span>}
        <button className="lang" onClick={() => setLang(lang === 'en' ? 'fr' : 'en')}>
          {lang === 'en' ? 'FR' : 'EN'}
        </button>
      </header>
      <main>{screens[page] ?? screens['']}</main>
      <nav className="bottom">
        <a href="#/">{t('openRounds')}</a>
        <a href="#/me">{t('trackRecord')}</a>
        <a href="#/public">{t('public')}</a>
      </nav>
    </div>
  )
}

export default function App() {
  return (
    <LangProvider>
      <Shell />
    </LangProvider>
  )
}
