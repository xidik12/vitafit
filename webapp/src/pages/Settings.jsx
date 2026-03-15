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
  { value: 'no_restriction', labelKey: 'settings.diet.no_restriction' },
  { value: 'halal', labelKey: 'settings.diet.halal' },
  { value: 'vegetarian', labelKey: 'settings.diet.vegetarian' },
  { value: 'vegan', labelKey: 'settings.diet.vegan' },
  { value: 'gluten_free', labelKey: 'settings.diet.gluten_free' },
  { value: 'dairy_free', labelKey: 'settings.diet.dairy_free' },
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
    <div className="p-4 pb-24">
      <div className="bg-gradient-to-br from-accent-green/10 via-accent-teal/5 to-transparent rounded-2xl p-4 mb-4">
        <h1 className="text-2xl font-bold text-text-primary">{t('common.settings')}</h1>
        <p className="text-accent-green text-sm font-medium mt-1">{t('settings.subtitle')}</p>
      </div>

      {/* Language */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">{t('settings.language')}</h2>
        <div className="flex gap-2">
          {LANGUAGE_OPTIONS.map(opt => (
            <button
              key={opt.code}
              onClick={() => handleLangChange(opt.code)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border text-base font-medium transition-colors min-h-[48px] ${
                lang === opt.code
                  ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                  : 'bg-bg-secondary border-border text-text-secondary'
              }`}
            >
              <span className="text-sm font-bold uppercase text-text-secondary">{opt.code}</span>
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Weight update */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">{t('settings.update_weight')}</h2>
        <div className="flex gap-2">
          <input
            type="number"
            step="0.1"
            value={weight}
            onChange={e => setWeight(e.target.value)}
            placeholder={profile?.weight_kg ? `${profile.weight_kg} ${t('common.kg')}` : t('settings.weight_placeholder')}
            className="flex-1 bg-bg-secondary rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
          />
          <span className="text-text-secondary text-sm flex items-center px-2">{t('common.kg')}</span>
        </div>
      </div>

      {/* Dietary preference */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">{t('settings.dietary_pref')}</h2>
        <div className="grid grid-cols-2 gap-2">
          {DIET_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setDiet(opt.value)}
              className={`py-3 rounded-xl border text-base transition-colors min-h-[48px] ${
                diet === opt.value
                  ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                  : 'bg-bg-secondary border-border text-text-secondary'
              }`}
            >
              {t(opt.labelKey)}
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
          <p className="text-accent-green text-sm">{t('settings.saved')}</p>
        </div>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full bg-accent-green text-white py-3.5 rounded-xl text-base font-semibold mb-3 disabled:opacity-50 min-h-[48px]"
      >
        {saving ? t('common.loading') : t('common.save')}
      </button>

      {/* Navigation links */}
      <div className="bg-white rounded-2xl overflow-hidden mb-4 border border-border shadow-sm">
        <button
          onClick={() => navigate('/about')}
          className="w-full flex items-center justify-between px-4 py-4 border-b border-border min-h-[48px]"
        >
          <span className="text-base text-text-primary">{t('common.about')}</span>
          <span className="text-text-secondary text-lg">›</span>
        </button>
        <button
          onClick={() => navigate('/questionnaire')}
          className="w-full flex items-center justify-between px-4 py-4 min-h-[48px]"
        >
          <span className="text-base text-text-primary">{t('settings.redo_questionnaire')}</span>
          <span className="text-text-secondary text-lg">›</span>
        </button>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-3.5 rounded-xl text-base font-medium text-accent-red border border-accent-red/30 bg-accent-red/5 min-h-[48px]"
      >
        {t('settings.logout')}
      </button>
    </div>
  )
}
