import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import api from '../utils/api'
import i18n from '../i18n'

const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English' },
  { code: 'ru', label: 'Русский' },
]

const DIET_OPTIONS = [
  { value: 'no_restriction', label: 'No restriction' },
  { value: 'halal', label: 'Halal' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'gluten_free', label: 'Gluten Free' },
  { value: 'dairy_free', label: 'Dairy Free' },
]

export default function Settings() {
  const { t } = useTranslation()
  const { token, profile, setProfile } = useUser()
  const navigate = useNavigate()

  const [lang, setLang] = useState(i18n.language || 'ru')
  const [weight, setWeight] = useState(profile?.weight_kg?.toString() || '')
  const [diet, setDiet] = useState(profile?.dietary_pref || 'no_restriction')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  function handleLangChange(code) {
    setLang(code)
    i18n.changeLanguage(code)
    localStorage.setItem('vitafit-lang', code)
  }

  async function handleSave() {
    if (!token) return
    setSaving(true)
    setError(null)
    setSaved(false)

    const updates = {}
    if (weight && !isNaN(Number(weight))) updates.weight_kg = Number(weight)
    if (diet) updates.dietary_pref = diet
    updates.language = lang

    try {
      const updated = await api.put('/api/profile', updates, token)
      if (updated?.status === 'ok') {
        setProfile(prev => ({ ...prev, ...updates }))
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err.message)
    }
    setSaving(false)
  }

  function handleLogout() {
    localStorage.removeItem('vitafit-token')
    window.location.reload()
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold text-text-primary mb-6">{t('common.settings')}</h1>

      {/* Language */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Language</h2>
        <div className="flex gap-2">
          {LANGUAGE_OPTIONS.map(opt => (
            <button
              key={opt.code}
              onClick={() => handleLangChange(opt.code)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border text-sm font-medium transition-colors ${
                lang === opt.code
                  ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                  : 'bg-bg-secondary border-border text-text-secondary'
              }`}
            >
              <span className="text-xs font-bold uppercase text-text-secondary">{opt.code}</span>
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Weight update */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Update Weight</h2>
        <div className="flex gap-2">
          <input
            type="number"
            step="0.1"
            value={weight}
            onChange={e => setWeight(e.target.value)}
            placeholder={profile?.weight_kg ? `${profile.weight_kg} kg` : 'Your weight (kg)'}
            className="flex-1 bg-bg-secondary rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
          />
          <span className="text-text-secondary text-sm flex items-center px-2">kg</span>
        </div>
      </div>

      {/* Dietary preference */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Dietary Preference</h2>
        <div className="grid grid-cols-2 gap-2">
          {DIET_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setDiet(opt.value)}
              className={`py-2.5 rounded-xl border text-sm transition-colors ${
                diet === opt.value
                  ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                  : 'bg-bg-secondary border-border text-text-secondary'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error / Success */}
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-3 mb-4">
          <p className="text-accent-red text-sm">{error}</p>
        </div>
      )}
      {saved && (
        <div className="bg-accent-green/10 border border-accent-green/30 rounded-xl p-3 mb-4">
          <p className="text-accent-green text-sm">Saved successfully!</p>
        </div>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full bg-accent-green text-white py-3 rounded-xl text-sm font-semibold mb-3 disabled:opacity-50"
      >
        {saving ? t('common.loading') : t('common.save')}
      </button>

      {/* Navigation links */}
      <div className="bg-white rounded-2xl overflow-hidden mb-4 border border-border shadow-sm">
        <button
          onClick={() => navigate('/about')}
          className="w-full flex items-center justify-between px-4 py-3 border-b border-border"
        >
          <span className="text-sm text-text-primary">{t('common.about')}</span>
          <span className="text-text-secondary">›</span>
        </button>
        <button
          onClick={() => navigate('/questionnaire')}
          className="w-full flex items-center justify-between px-4 py-3"
        >
          <span className="text-sm text-text-primary">Redo Questionnaire</span>
          <span className="text-text-secondary">›</span>
        </button>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-3 rounded-xl text-sm font-medium text-accent-red border border-accent-red/30 bg-accent-red/5"
      >
        Log Out
      </button>
    </div>
  )
}
