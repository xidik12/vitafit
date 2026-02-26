import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import ProgressRing from '../components/ProgressRing'
import api from '../utils/api'

export default function Dashboard() {
  const { t } = useTranslation()
  const { profile, token, loading, tgUser } = useUser()
  const navigate = useNavigate()
  const [todaySummary, setTodaySummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(true)

  const isOnboarded = profile?.onboarded

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
  const calGoal = profile?.calorie_goal || 2000
  const calConsumed = todaySummary?.calories_consumed || 0
  const calLeft = Math.max(0, calGoal - calConsumed)
  const calPercent = Math.min(100, (calConsumed / calGoal) * 100)

  const waterGoal = profile?.water_goal_ml || 2000
  const waterConsumed = todaySummary?.water_ml || 0
  const waterPercent = Math.min(100, (waterConsumed / waterGoal) * 100)

  const streak = todaySummary?.streak || profile?.streak || 0

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">
            {t('dashboard.welcome')}
          </h1>
          {firstName && (
            <p className="text-text-secondary text-sm mt-0.5">{firstName}</p>
          )}
        </div>
        <button
          onClick={() => navigate('/settings')}
          className="text-text-secondary text-xl p-1"
          aria-label={t('common.settings')}
        >
          ⚙️
        </button>
      </div>

      {/* Onboarding CTA */}
      {!isOnboarded && (
        <div className="bg-accent-light border border-accent-green/30 rounded-2xl p-4 mb-4">
          <h2 className="text-accent-dark font-semibold text-base mb-1">
            {t('dashboard.start_questionnaire')}
          </h2>
          <p className="text-text-secondary text-sm mb-3">
            {t('dashboard.complete_setup')}
          </p>
          <button
            onClick={() => navigate('/questionnaire')}
            className="w-full bg-accent-green text-white font-semibold py-3 rounded-xl text-sm"
          >
            {t('dashboard.start_questionnaire')} →
          </button>
        </div>
      )}

      {/* Today's summary */}
      {isOnboarded && (
        <>
          <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
            <h2 className="text-text-secondary text-xs uppercase tracking-wide mb-3">
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
                  <ProgressRing
                    percent={calPercent}
                    size={72}
                    strokeWidth={5}
                    color="#22c55e"
                    label={t('dashboard.calories_left')}
                  />
                  <span className="text-sm font-bold text-text-primary mt-1">{calLeft}</span>
                  <span className="text-xs text-text-secondary">{t('common.kcal')}</span>
                </div>

                {/* Water */}
                <div className="flex flex-col items-center">
                  <ProgressRing
                    percent={waterPercent}
                    size={72}
                    strokeWidth={5}
                    color="#3b82f6"
                    label={t('dashboard.water')}
                  />
                  <span className="text-sm font-bold text-text-primary mt-1">{waterConsumed}</span>
                  <span className="text-xs text-text-secondary">{t('common.water_ml')}</span>
                </div>

                {/* Streak */}
                <div className="flex flex-col items-center justify-center">
                  <span className="text-3xl">🔥</span>
                  <span className="text-xl font-bold text-accent-orange">{streak}</span>
                  <span className="text-xs text-text-secondary">{t('dashboard.days')}</span>
                  <span className="text-xs text-text-secondary mt-0.5">{t('dashboard.streak')}</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick actions */}
          <h2 className="text-text-secondary text-xs uppercase tracking-wide mb-2">
            {t('dashboard.your_plan')}
          </h2>
          <div className="grid grid-cols-3 gap-2 mb-4">
            <button
              onClick={() => navigate('/calories')}
              className="bg-white rounded-xl p-3 flex flex-col items-center gap-1 border border-border shadow-sm"
            >
              <span className="text-2xl">📝</span>
              <span className="text-xs text-text-secondary text-center leading-tight">
                {t('nav.calories')}
              </span>
            </button>
            <button
              onClick={() => navigate('/exercises')}
              className="bg-white rounded-xl p-3 flex flex-col items-center gap-1 border border-border shadow-sm"
            >
              <span className="text-2xl">💪</span>
              <span className="text-xs text-text-secondary text-center leading-tight">
                {t('nav.exercises')}
              </span>
            </button>
            <button
              onClick={() => navigate('/meals')}
              className="bg-white rounded-xl p-3 flex flex-col items-center gap-1 border border-border shadow-sm"
            >
              <span className="text-2xl">🍽️</span>
              <span className="text-xs text-text-secondary text-center leading-tight">
                {t('nav.meals')}
              </span>
            </button>
          </div>
        </>
      )}
    </div>
  )
}
