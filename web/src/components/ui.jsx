import React from 'react'

// Section heading with a subtitle, used everywhere so nothing reads as plain text.
export function Head({ eyebrow, title, sub, level = 2 }) {
  const H = `h${level}`
  return (
    <header className="head">
      {eyebrow && <div className="eyebrow">{eyebrow}</div>}
      <H>{title}</H>
      {sub && <p className="sub">{sub}</p>}
    </header>
  )
}

export function Chip({ children, tone }) {
  return <span className={`chip ${tone || ''}`}>{children}</span>
}

// Simple line icons (no emoji): check, cross, dash, up, down. Decorative; pair with text or aria-label.
const PATHS = { check: 'M5 12.5l4.5 4.5L19 7.5', cross: 'M6.5 6.5l11 11M17.5 6.5l-11 11', dash: 'M6 12h12',
  up: 'M12 19V5M6 11l6-6 6 6', down: 'M12 5v14M6 13l6 6 6-6' }
export function Icon({ name, size = 16 }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d={PATHS[name]} /></svg>
  )
}

export function Loading() {
  return <div className="loading" aria-busy="true"><span /><span /><span /></div>
}
