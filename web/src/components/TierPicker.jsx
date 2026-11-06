import React from 'react'
import { useT } from '../i18n.jsx'

// Most protective tier first and default. Changeable per answer.
export const TIERS = ['anonymous', 'pseudonymous', 'known']
const ICON = { anonymous: '🕶️', pseudonymous: '🏷️', known: '🤝' }

export default function TierPicker({ value, onChange }) {
  const { t } = useT()
  return (
    <div className="tiers" role="radiogroup">
      {TIERS.map((tier) => (
        <label key={tier} className={`card tier ${value === tier ? 'on' : ''}`}>
          <input type="radio" name="tier" checked={value === tier} onChange={() => onChange(tier)} />
          <span className="tier-icon" aria-hidden="true">{ICON[tier]}</span>
          <span><b>{t(`tier_${tier}`)}</b><br /><span className="muted small">{t(`tier_${tier}_d`)}</span></span>
        </label>
      ))}
    </div>
  )
}
