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

export function Loading() {
  return <div className="loading" aria-busy="true"><span /><span /><span /></div>
}
