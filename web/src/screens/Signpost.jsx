import React from 'react'
import { useT } from '../i18n.jsx'

// Out of scope on purpose: we don't take in evidence. Point witnesses to channels built for it.
export default function Signpost() {
  const { t } = useT()
  return (
    <section>
      <h1>{t('signpost')}</h1>
      <p>This tool is for invited expert panels. It is not a safe place to submit evidence of crimes.
        If you witnessed serious violations, these organisations can protect you and your evidence:</p>
      <ul>
        <li><a href="https://otplink.icc-cpi.int" rel="noreferrer" target="_blank">ICC Office of the Prosecutor: OTPLink</a></li>
        <li><a href="https://www.eyewitness.global" rel="noreferrer" target="_blank">eyeWitness to Atrocities (app)</a></li>
        <li><a href="https://www.ohchr.org" rel="noreferrer" target="_blank">UN Human Rights (OHCHR)</a></li>
      </ul>
      <p className="muted small">Think about your safety first: delete this page from your history if your phone may be checked.</p>
    </section>
  )
}
