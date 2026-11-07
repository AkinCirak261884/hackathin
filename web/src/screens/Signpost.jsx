import React from 'react'
import { useT } from '../i18n.jsx'
import { Head } from '../components/ui.jsx'

// Out of scope on purpose: we don't take in evidence. Point witnesses to channels built for it.
export default function Signpost() {
  const { t } = useT()
  return (
    <section className="page">
      <Head level={1} title={t('signpost')}
        sub="This tool is for invited expert panels. It is not a safe place to submit evidence of crimes." />
      <div className="card">
        <p className="q-sub">If you witnessed serious violations, these organisations can protect you and your evidence:</p>
        <ul>
          <li><a href="https://otplink.icc-cpi.int" rel="noreferrer" target="_blank">ICC Office of the Prosecutor: OTPLink</a></li>
          <li><a href="https://www.eyewitness.global" rel="noreferrer" target="_blank">eyeWitness to Atrocities (app)</a></li>
          <li><a href="https://www.ohchr.org" rel="noreferrer" target="_blank">UN Human Rights (OHCHR)</a></li>
        </ul>
        <p className="note">Think about your safety first: delete this page from your history if your phone may be checked.</p>
      </div>
    </section>
  )
}
