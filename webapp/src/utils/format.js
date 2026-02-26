export function formatCalories(n) {
  return Math.round(n).toLocaleString()
}

export function formatWeight(kg, lang = 'en') {
  return `${kg.toFixed(1)} ${lang === 'ru' ? 'кг' : 'kg'}`
}

export function formatDate(dateStr, lang = 'en') {
  const d = new Date(dateStr)
  if (lang === 'ru') {
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function macroPercent(current, target) {
  if (!target) return 0
  return Math.min(100, Math.round((current / target) * 100))
}
