// Small helpers shared by charts and screens. Must match fixtures/generate_fixtures.py.
export function pct(values, q) {
  const v = [...values].sort((a, b) => a - b)
  if (!v.length) return null
  const k = (v.length - 1) * q
  const lo = Math.floor(k), hi = Math.min(lo + 1, v.length - 1)
  return +(v[lo] + (v[hi] - v[lo]) * (k - lo)).toFixed(3)
}
export const r05 = (x) => Math.round(Math.round(x * 20) / 20 * 100) / 100
export const asPct = (x) => `${Math.round(x * 100)}%`

// A forecast "counts as correct" when it was on the right side of 50%. 50% is no call.
export function verdict(prob, outcome) {
  if (prob === 0.5) return 'nocall'
  return (prob > 0.5) === outcome ? 'correct' : 'wrong'
}
export function recordSummary(resolved) {
  const v = resolved.map((r) => verdict(r.your_prob, r.outcome))
  return { correct: v.filter((x) => x === 'correct').length, total: v.filter((x) => x !== 'nocall').length, verdicts: v }
}

// Verbal scale for probabilities (shown under sliders)
export function likelihoodKey(p) {
  if (p < 0.15) return 'l_very_unlikely'
  if (p < 0.4) return 'l_unlikely'
  if (p <= 0.6) return 'l_even'
  if (p <= 0.85) return 'l_likely'
  return 'l_very_likely'
}
