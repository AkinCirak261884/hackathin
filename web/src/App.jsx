import React, { useEffect, useState } from 'react'
import { LangProvider, useT } from './i18n.jsx'
import { MOCK } from './api.js'
import Home from './screens/Home.jsx'
import Pulse from './screens/Pulse.jsx'
import Reveal from './screens/Reveal.jsx'
import Profile from './screens/Profile.jsx'
import PublicPage from './screens/Public.jsx'
import Signpost from './screens/Signpost.jsx'
import Guess from './screens/Guess.jsx'
import { RecordPage, AccuracyPage } from './screens/Record.jsx'

// Tiny hash router: #/pulse/RD-R1043-1, #/reveal/RD-R1043-1, #/me, #/guess/Q-R1014-MAT, #/public, #/signpost
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

const Icon = {
  rounds: <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16M4 12h16M4 19h10" /></svg>,
  me: <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></svg>,
  public: <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" /></svg>,
}

function Shell() {
  const { t, lang, setLang } = useT()
  const [page, id] = useRoute()
  const focus = page === 'pulse' // hide tab bar during the survey so the action bar owns the thumb zone
  const tabs = [
    { href: '#/', key: '', label: t('nav_rounds'), icon: Icon.rounds },
    { href: '#/me', key: 'me', label: t('nav_me'), icon: Icon.me },
    { href: '#/public', key: 'public', label: t('nav_public'), icon: Icon.public },
  ]
  const current = page === 'reveal' || page === 'pulse' ? '' : ['guess', 'record', 'accuracy'].includes(page) ? 'me' : page
  const screens = {
    '': <Home />,
    pulse: <Pulse roundId={id} />,
    reveal: <Reveal roundId={id} />,
    me: <Profile />,
    guess: <Guess questionId={id} />,
    record: <RecordPage />,
    accuracy: <AccuracyPage />,
    public: <PublicPage />,
    signpost: <Signpost />,
  }
  return (
    <div className={`app ${focus ? 'focus' : ''}`}>
      <header className="top">
        <a href="#/" className="brand"><span className="logo" aria-hidden="true" />{t('app')}</a>
        <nav className="top-nav">
          {tabs.map((x) => <a key={x.key} href={x.href} className={current === x.key ? 'on' : ''}>{x.label}</a>)}
        </nav>
        {MOCK && <span className="pill">{t('mock')}</span>}
        <button className="lang" onClick={() => setLang(lang === 'en' ? 'fr' : 'en')} aria-label="Language">
          {lang === 'en' ? 'FR' : 'EN'}
        </button>
      </header>
      <main>{screens[page] ?? screens['']}</main>
      {!focus && (
        <nav className="tabbar">
          {tabs.map((x) => (
            <a key={x.key} href={x.href} className={current === x.key ? 'on' : ''}>{x.icon}<span>{x.label}</span></a>
          ))}
        </nav>
      )}
    </div>
  )
}

export default function App() {
  return <LangProvider><Shell /></LangProvider>
}
