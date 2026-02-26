import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const APP_VERSION = '1.0.0'

export default function About() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => navigate(-1)}
          className="text-text-secondary text-lg"
          aria-label={t('common.back')}
        >
          ←
        </button>
        <h1 className="text-xl font-bold text-text-primary">{t('common.about')}</h1>
      </div>

      {/* App identity */}
      <div className="flex flex-col items-center py-8 mb-6">
        <div className="w-20 h-20 bg-accent-green/10 border border-accent-green/30 rounded-2xl flex items-center justify-center mb-4">
          <span className="text-4xl">🌿</span>
        </div>
        <h2 className="text-2xl font-bold text-text-primary">VitaFit</h2>
        <p className="text-text-secondary text-sm mt-1">Version {APP_VERSION}</p>
      </div>

      {/* Description */}
      <div className="bg-bg-card rounded-2xl p-4 mb-4">
        <h3 className="text-sm font-semibold text-text-primary mb-2">About VitaFit</h3>
        <p className="text-text-secondary text-sm leading-relaxed">
          VitaFit is your personal AI-powered health and fitness companion. Get personalized
          exercise plans, meal recommendations, and track your daily nutrition to achieve
          your health goals.
        </p>
      </div>

      {/* Features */}
      <div className="bg-bg-card rounded-2xl p-4 mb-4">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Features</h3>
        <div className="space-y-2">
          {[
            { icon: '💪', label: 'Personalized exercise plans' },
            { icon: '🍽️', label: 'AI-generated meal plans' },
            { icon: '📝', label: 'Daily calorie & macro tracking' },
            { icon: '📊', label: 'Progress visualization' },
            { icon: '🌍', label: 'Multi-language support (EN/RU)' },
            { icon: '🔥', label: 'Streak & achievement system' },
          ].map(({ icon, label }) => (
            <div key={label} className="flex items-center gap-3">
              <span className="text-lg">{icon}</span>
              <span className="text-sm text-text-secondary">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-accent-orange/10 border border-accent-orange/20 rounded-2xl p-4 mb-4">
        <h3 className="text-sm font-semibold text-accent-orange mb-2">⚠️ Medical Disclaimer</h3>
        <p className="text-text-secondary text-xs leading-relaxed">
          VitaFit is intended for informational and educational purposes only. The content
          provided — including exercise plans, meal recommendations, and nutritional information —
          does not constitute medical advice. Always consult a qualified healthcare professional
          before starting any new fitness or nutrition program, especially if you have any
          existing medical conditions.
        </p>
      </div>

      {/* Links */}
      <div className="bg-bg-card rounded-2xl overflow-hidden mb-4">
        <a
          href="https://t.me/vitafit_support"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-between px-4 py-3 border-b border-gray-800"
        >
          <div className="flex items-center gap-2">
            <span>📩</span>
            <span className="text-sm text-text-primary">Support</span>
          </div>
          <span className="text-text-secondary text-xs">@vitafit_support</span>
        </a>
        <a
          href="https://t.me/vitafit_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-between px-4 py-3"
        >
          <div className="flex items-center gap-2">
            <span>🤖</span>
            <span className="text-sm text-text-primary">Telegram Bot</span>
          </div>
          <span className="text-text-secondary text-xs">@vitafit_bot</span>
        </a>
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-text-secondary pb-2">
        Made with ❤️ · VitaFit {APP_VERSION}
      </p>
    </div>
  )
}
