import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const APP_VERSION = '1.0.0'

export default function About() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const features = [
    { icon: '\uD83D\uDCAA', labelKey: 'about_page.feature_exercises' },
    { icon: '\uD83C\uDF7D\uFE0F', labelKey: 'about_page.feature_meals' },
    { icon: '\uD83D\uDCDD', labelKey: 'about_page.feature_calories' },
    { icon: '\uD83D\uDCCA', labelKey: 'about_page.feature_progress' },
    { icon: '\uD83C\uDF0D', labelKey: 'about_page.feature_languages' },
    { icon: '\uD83D\uDD25', labelKey: 'about_page.feature_streaks' },
  ]

  return (
    <div className="p-4 pb-24">
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => navigate(-1)}
          className="text-text-secondary text-2xl p-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label={t('common.back')}
        >
          ←
        </button>
        <h1 className="text-xl font-bold text-text-primary">{t('common.about')}</h1>
      </div>

      {/* App identity */}
      <div className="flex flex-col items-center py-8 mb-6">
        <div className="w-20 h-20 bg-accent-light border border-accent-green/30 rounded-2xl flex items-center justify-center mb-4">
          <span className="text-4xl">{'\uD83C\uDF3F'}</span>
        </div>
        <h2 className="text-2xl font-bold text-text-primary">VitaFit</h2>
        <p className="text-text-secondary text-sm mt-1">Version {APP_VERSION}</p>
      </div>

      {/* Description */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h3 className="text-sm font-semibold text-text-primary mb-2">{t('about_page.title')}</h3>
        <p className="text-text-secondary text-sm leading-relaxed">
          {t('about_page.description')}
        </p>
      </div>

      {/* Features */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <h3 className="text-sm font-semibold text-text-primary mb-3">{t('about_page.features_title')}</h3>
        <div className="space-y-2">
          {features.map(({ icon, labelKey }) => (
            <div key={labelKey} className="flex items-center gap-3">
              <span className="text-lg">{icon}</span>
              <span className="text-sm text-text-secondary">{t(labelKey)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-accent-orange/10 border border-accent-orange/20 rounded-2xl p-4 mb-4">
        <h3 className="text-sm font-semibold text-accent-orange mb-2">{'\u26A0\uFE0F'} {t('about_page.disclaimer_title')}</h3>
        <p className="text-text-secondary text-sm leading-relaxed">
          {t('about_page.disclaimer_text')}
        </p>
      </div>

      {/* Links */}
      <div className="bg-white rounded-2xl overflow-hidden mb-4 border border-border shadow-sm">
        <a
          href="https://t.me/vitafit_support"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-between px-4 py-4 border-b border-border min-h-[48px]"
        >
          <div className="flex items-center gap-2">
            <span>{'\uD83D\uDCE9'}</span>
            <span className="text-base text-text-primary">{t('about_page.support')}</span>
          </div>
          <span className="text-text-secondary text-sm">@vitafit_support</span>
        </a>
        <a
          href="https://t.me/vitafit_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-between px-4 py-4 min-h-[48px]"
        >
          <div className="flex items-center gap-2">
            <span>{'\uD83E\uDD16'}</span>
            <span className="text-base text-text-primary">{t('about_page.telegram_bot')}</span>
          </div>
          <span className="text-text-secondary text-sm">@vitafit_bot</span>
        </a>
      </div>

      {/* Footer */}
      <p className="text-center text-sm text-text-secondary pb-2">
        Made with {'\u2764\uFE0F'} · VitaFit {APP_VERSION}
      </p>
    </div>
  )
}
