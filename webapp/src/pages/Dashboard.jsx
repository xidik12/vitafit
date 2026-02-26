import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import ProgressRing from '../components/ProgressRing'
import api from '../utils/api'
import { CogIcon, FireIcon, PencilIcon, DumbbellIcon, UtensilsIcon } from '../components/Icons'

export default function Dashboard() {
  const { t } = useTranslation()
  const { profile, token, loading, tgUser } = useUser()
  const navigate = useNavigate()
  const [todaySummary, setTodaySummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(true)

  const isOnboarded = profile?.onboarding_complete

  useEffect(() => {
    if (!token || !isOnboarded) {
      setSummaryLoading(false)
      return
    }
    async function fetchSummary() {
      try {
        const data = await api.get('/api/progress/today', token)
        setTodaySummary(data)
      } catch {
        // Non-critical — summary may not exist yet
      }
      setSummaryLoading(false)
    }
    fetchSummary()
  }, [token, isOnboarded])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const firstName = tgUser?.first_name || profile?.first_name || ''
  const calGoal = profile?.calorie_goal || profile?.target_calories || 2000
  const calConsumed = todaySummary?.calories_consumed || 0
  const calLeft = Math.max(0, calGoal - calConsumed)
  const calPercent = Math.min(100, (calConsumed / calGoal) * 100)

  const waterGoal = profile?.target_water_ml || 2000
  const waterConsumed = todaySummary?.water_ml || 0
  const waterPercent = Math.min(100, (waterConsumed / waterGoal) * 100)

  const streak = todaySummary?.streak || profile?.current_streak || 0

  return (
    <div className="p-4 pb-24">
      {/* Header */}
      <div className="bg-gradient-to-br from-accent-green/10 via-accent-teal/5 to-transparent rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">
              {t('dashboard.welcome')}
            </h1>
            {firstName && (
              <p className="text-text-secondary text-sm mt-0.5">{firstName}</p>
            )}
            <p className="text-accent-green text-xs font-medium mt-1">{t('dashboard.subtitle')}</p>
          </div>
          <button
            onClick={() => navigate('/settings')}
            className="text-text-secondary p-2 rounded-xl hover:bg-white/60 transition-colors"
            aria-label={t('common.settings')}
          >
            <CogIcon className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Onboarding CTA */}
      {!isOnboarded && (
        <div className="bg-gradient-to-br from-accent-light to-accent-green/5 border border-accent-green/30 rounded-2xl p-4 mb-4">
          <h2 className="text-accent-dark font-semibold text-base mb-1">
            {t('dashboard.start_questionnaire')}
          </h2>
          <p className="text-text-secondary text-sm mb-3">
            {t('dashboard.complete_setup')}
          </p>
          <button
            onClick={() => navigate('/questionnaire')}
            className="w-full bg-gradient-to-r from-accent-green to-accent-emerald text-white font-semibold py-3 rounded-xl text-sm shadow-md shadow-accent-green/20"
          >
            {t('dashboard.start_questionnaire')} →
          </button>
        </div>
      )}

      {/* Today's summary */}
      {isOnboarded && (
        <>
          <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
            <h2 className="text-text-secondary text-xs uppercase tracking-wide mb-3 font-semibold">
              {t('dashboard.today')}
            </h2>
            {summaryLoading ? (
              <div className="flex justify-center py-4">
                <div className="w-5 h-5 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <div className="flex justify-around">
                {/* Calories */}
                <div className="flex flex-col items-center">
                  <div className="rounded-full bg-accent-green/5 p-1">
                    <ProgressRing
                      percent={calPercent}
                      size={72}
                      strokeWidth={5}
                      color="#22c55e"
                      label={t('dashboard.calories_left')}
                    />
                  </div>
                  <span className="text-lg font-bold text-text-primary mt-1">{calLeft}</span>
                  <span className="text-xs text-text-secondary">{t('common.kcal')}</span>
                </div>

                {/* Water */}
                <div className="flex flex-col items-center">
                  <div className="rounded-full bg-accent-blue/5 p-1">
                    <ProgressRing
                      percent={waterPercent}
                      size={72}
                      strokeWidth={5}
                      color="#3b82f6"
                      label={t('dashboard.water')}
                    />
                  </div>
                  <span className="text-lg font-bold text-text-primary mt-1">{waterConsumed}</span>
                  <span className="text-xs text-text-secondary">{t('common.water_ml')}</span>
                </div>

                {/* Streak */}
                <div className="flex flex-col items-center justify-center">
                  <div className="rounded-full bg-accent-orange/10 p-2">
                    <FireIcon className="w-8 h-8 text-accent-orange" />
                  </div>
                  <span className="text-2xl font-bold text-accent-orange">{streak}</span>
                  <span className="text-xs text-text-secondary">{t('dashboard.days')}</span>
                  <span className="text-xs text-text-secondary mt-0.5">{t('dashboard.streak')}</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick actions */}
          <h2 className="text-text-secondary text-xs uppercase tracking-wide mb-2 font-semibold">
            {t('dashboard.your_plan')}
          </h2>
          <div className="grid grid-cols-3 gap-2 mb-4">
            <button
              onClick={() => navigate('/calories')}
              className="bg-gradient-to-br from-accent-teal/10 to-accent-cyan/5 rounded-xl p-3 flex flex-col items-center gap-1.5 border border-accent-teal/20 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-full bg-accent-teal/15 flex items-center justify-center">
                <PencilIcon className="w-5 h-5 text-accent-teal" />
              </div>
              <span className="text-sm text-text-primary text-center leading-tight font-medium">
                {t('nav.calories')}
              </span>
            </button>
            <button
              onClick={() => navigate('/exercises')}
              className="bg-gradient-to-br from-accent-blue/10 to-accent-indigo/5 rounded-xl p-3 flex flex-col items-center gap-1.5 border border-accent-blue/20 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-full bg-accent-blue/15 flex items-center justify-center">
                <DumbbellIcon className="w-5 h-5 text-accent-blue" />
              </div>
              <span className="text-sm text-text-primary text-center leading-tight font-medium">
                {t('nav.exercises')}
              </span>
            </button>
            <button
              onClick={() => navigate('/meals')}
              className="bg-gradient-to-br from-accent-orange/10 to-accent-amber/5 rounded-xl p-3 flex flex-col items-center gap-1.5 border border-accent-orange/20 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-full bg-accent-orange/15 flex items-center justify-center">
                <UtensilsIcon className="w-5 h-5 text-accent-orange" />
              </div>
              <span className="text-sm text-text-primary text-center leading-tight font-medium">
                {t('nav.meals')}
              </span>
            </button>
          </div>
        </>
      )}
    </div>
  )
}
