import React, { createContext, useContext, useState } from 'react'

const STRINGS = {
  en: {
    app: 'Ground Truth',
    openRounds: 'Your open check-ins',
    minutes: (n) => `about ${n} min`,
    start: 'Start',
    answered: 'Answered, see the group',
    step: (i, n) => `Step ${i} of ${n}`,
    next: 'Next',
    back: 'Back',
    submit: 'Submit',
    rating: 'Do you agree with the ACAPS rating?',
    triggers: 'Which triggers are you seeing now?',
    forecast: 'How likely is this before the deadline?',
    missing: 'What is ACAPS missing? (optional)',
    ranking: 'Top 3 risks for Chad, next 6 months',
    tier: 'How should this answer be attributed?',
    tier_known: 'Known to ACAPS',
    tier_known_d: 'ACAPS moderators know it is you. Never public.',
    tier_pseudonymous: 'Pseudonym to peers',
    tier_pseudonymous_d: 'Peers see your pseudonym. Nobody sees your name.',
    tier_anonymous: 'Fully anonymous',
    tier_anonymous_d: 'Nobody can link this answer to you, not even ACAPS.',
    reveal: 'The group view',
    revise: 'Revise my answer (once)',
    trackRecord: 'My track record',
    public: 'Public summary',
    signpost: 'Witnessed abuses?',
    synthetic: 'synthetic',
    mock: 'Demo data',
  },
  fr: {
    app: 'Ground Truth',
    openRounds: 'Vos consultations ouvertes',
    minutes: (n) => `environ ${n} min`,
    start: 'Commencer',
    answered: 'Répondu, voir le groupe',
    step: (i, n) => `Étape ${i} sur ${n}`,
    next: 'Suivant',
    back: 'Retour',
    submit: 'Envoyer',
    rating: "Êtes-vous d'accord avec l'évaluation d'ACAPS ?",
    triggers: 'Quels déclencheurs observez-vous en ce moment ?',
    forecast: "Quelle est la probabilité avant l'échéance ?",
    missing: "Qu'est-ce qui manque à l'analyse d'ACAPS ? (facultatif)",
    ranking: 'Les 3 principaux risques au Tchad, 6 prochains mois',
    tier: 'Comment attribuer cette réponse ?',
    tier_known: 'Connu d’ACAPS',
    tier_known_d: 'Les modérateurs ACAPS savent que c’est vous. Jamais public.',
    tier_pseudonymous: 'Pseudonyme pour les pairs',
    tier_pseudonymous_d: 'Vos pairs voient votre pseudonyme. Personne ne voit votre nom.',
    tier_anonymous: 'Totalement anonyme',
    tier_anonymous_d: 'Personne ne peut relier cette réponse à vous, pas même ACAPS.',
    reveal: 'La vue du groupe',
    revise: 'Réviser ma réponse (une fois)',
    trackRecord: 'Mon historique',
    public: 'Synthèse publique',
    signpost: 'Témoin de violations ?',
    synthetic: 'synthétique',
    mock: 'Données de démo',
  },
}

const LangCtx = createContext(null)

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => {
    try { return localStorage.getItem('gt_lang') || 'en' } catch { return 'en' }
  })
  const change = (l) => {
    setLang(l)
    try { localStorage.setItem('gt_lang', l) } catch {}
  }
  return <LangCtx.Provider value={{ lang, setLang: change }}>{children}</LangCtx.Provider>
}

export function useT() {
  const { lang, setLang } = useContext(LangCtx)
  const t = (key, ...args) => {
    const v = STRINGS[lang][key] ?? STRINGS.en[key] ?? key
    return typeof v === 'function' ? v(...args) : v
  }
  // pick the right language field from fixture objects: text / text_fr, label / label_fr
  const tx = (obj, field = 'text') => (lang === 'fr' && obj[`${field}_fr`]) || obj[field]
  return { t, tx, lang, setLang }
}
