import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import ProgressRing from '../components/ProgressRing'
import api from '../utils/api'
import { CogIcon, FireIcon, PencilIcon, DumbbellIcon, UtensilsIcon, DropletIcon } from '../components/Icons'

export default function Dashboard() {
  const { t, i18n } = useTranslation()
  const { profile, token, loading, tgUser } = useUser()
  const navigate = useNavigate()
  const [todaySummary, setTodaySummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(true)

  const isOnboarded = profile?.onboarding_complete
  const lang = i18n.language

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
        <div className="w-8 h-8 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const firstName = tgUser?.first_name || profile?.first_name || ''
  const calGoal = profile?.calorie_goal || profile?.target_calories || 2000
  const calConsumed = todaySummary?.calories_consumed || 0
  const calPercent = Math.min(100, (calConsumed / calGoal) * 100)

  // Calorie ring color: green <80%, amber 80-100%, red >100%
  const calColor = calPercent > 100 ? '#f87171' : calPercent >= 80 ? '#f59e0b' : '#22c55e'

  const waterGoal = profile?.target_water_ml || 2000
  const waterConsumed = todaySummary?.water_ml || 0
  const waterPercent = Math.min(100, (waterConsumed / waterGoal) * 100)
  const WATER_STEP_ML = 250

  const streak = todaySummary?.streak || profile?.current_streak || 0

  // Time-based greeting
  const hour = new Date().getHours()
  const greetingKey = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'
  const greetings = {
    morning: lang === 'ru' ? 'Доброе утро' : 'Good morning',
    afternoon: lang === 'ru' ? 'Добрый день' : 'Good afternoon',
    evening: lang === 'ru' ? 'Добрый вечер' : 'Good evening',
  }
  const greeting = firstName
    ? `${greetings[greetingKey]}, ${firstName}!`
    : `${greetings[greetingKey]}!`

  // Today's main task placeholder
  const todayTask = todaySummary?.today_task
    || (lang === 'ru' ? 'Сегодня: 20 мин лёгкая йога' : "Today's workout: 20 min gentle yoga")

  async function logWater() {
    if (!token) return
    try {
      await api.post('/api/calories/water', { amount_ml: WATER_STEP_ML }, token)
      setTodaySummary(prev => ({ ...prev, water_ml: (prev?.water_ml || 0) + WATER_STEP_ML }))
    } catch (err) {
      console.error(err)
    }
  }

  // Streak encouragement
  const streakMsg = streak === 0
    ? (lang === 'ru' ? 'Начните серию сегодня!' : 'Start your streak today!')
    : streak < 7
    ? (lang === 'ru' ? 'Отличное начало! Продолжайте!' : 'Great start! Keep going!')
    : (lang === 'ru' ? 'Потрясающая серия!' : 'Amazing streak!')

  return (
    <div className="p-4 pb-24">
      {/* Warm greeting */}
      <div className="bg-gradient-to-br from-accent-green/10 via-accent-teal/5 to-transparent rounded-2xl p-5 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary leading-snug">
              {greeting}
            </h1>
            {isOnboarded && (
              <p className="text-base text-accent-green font-medium mt-2">{todayTask}</p>
            )}
          </div>
          <button
            onClick={() => navigate('/settings')}
            className="text-text-secondary p-3 rounded-xl hover:bg-white/60 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label={t('common.settings')}
          >
            <CogIcon className="w-7 h-7" />
          </button>
        </div>
      </div>

      {/* Onboarding CTA */}
      {!isOnboarded && (
        <div className="bg-gradient-to-br from-accent-light to-accent-green/5 border border-accent-green/30 rounded-2xl p-5 mb-4">
          <h2 className="text-accent-dark font-semibold text-lg mb-2">
            {t('dashboard.start_questionnaire')}
          </h2>
          <p className="text-text-secondary text-base mb-4">
            {t('dashboard.complete_setup')}
          </p>
          <button
            onClick={() => navigate('/questionnaire')}
            className="w-full bg-gradient-to-r from-accent-green to-accent-emerald text-white font-semibold py-4 rounded-xl text-base shadow-md shadow-accent-green/20 min-h-[48px]"
          >
            {t('dashboard.start_questionnaire')} →
          </button>
        </div>
      )}

      {/* Main content for onboarded users */}
      {isOnboarded && (
        <>
          {/* Calorie progress ring — simple visual */}
          <div className="bg-white rounded-2xl p-5 mb-4 border border-border shadow-sm">
            {summaryLoading ? (
              <div className="flex justify-center py-6">
                <div className="w-8 h-8 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <div className="flex items-center gap-5">
                <div className="rounded-full bg-accent-green/5 p-1 flex-shrink-0">
                  <ProgressRing
                    percent={calPercent}
                    size={100}
                    strokeWidth={8}
                    color={calColor}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-base font-semibold text-text-primary">
                    {t('dashboard.calories_left')}
                  </p>
                  <p className="text-3xl font-bold text-text-primary mt-1">
                    {Math.max(0, calGoal - calConsumed)} <span className="text-base font-medium text-text-secondary">{t('common.kcal')}</span>
                  </p>
                  <p className="text-sm text-text-secondary mt-1">
                    {Math.round(calConsumed)} / {calGoal} {t('common.kcal')}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Water intake — simple + button */}
          <div className="bg-gradient-to-br from-accent-blue/5 to-accent-cyan/5 rounded-2xl p-5 mb-4 border border-accent-blue/15 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-accent-blue/15 flex items-center justify-center">
                  <DropletIcon className="w-6 h-6 text-accent-blue" />
                </div>
                <div>
                  <p className="text-base font-semibold text-text-primary">{t('dashboard.water')}</p>
                  <p className="text-sm text-text-secondary">{waterConsumed} / {waterGoal} {t('common.water_ml')}</p>
                </div>
              </div>
              <button
                onClick={logWater}
                className="bg-accent-blue text-white px-5 py-3 rounded-xl text-base font-bold shadow-sm hover:bg-accent-blue/90 transition-colors min-h-[48px] active:scale-95"
              >
                + {WATER_STEP_ML}{t('common.water_ml')}
              </button>
            </div>
            <div className="w-full h-3 bg-white/60 rounded-full overflow-hidden mt-3">
              <div
                className="h-full rounded-full transition-all duration-300 bg-gradient-to-r from-accent-blue to-accent-cyan"
                style={{ width: `${waterPercent}%` }}
              />
            </div>
          </div>

          {/* Streak with encouragement */}
          <div className="bg-gradient-to-br from-accent-orange/10 to-accent-amber/5 rounded-2xl p-5 mb-4 border border-accent-orange/15 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-accent-orange/15 p-3 flex-shrink-0">
                <FireIcon className="w-10 h-10 text-accent-orange" />
              </div>
              <div>
                <p className="text-3xl font-bold text-accent-orange">
                  {streak} <span className="text-base font-medium">{t('dashboard.days')}</span>
                </p>
                <p className="text-base text-text-secondary font-medium mt-0.5">{streakMsg}</p>
              </div>
            </div>
          </div>

          {/* Quick action buttons — large touch targets */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <button
              onClick={() => navigate('/calories')}
              className="bg-gradient-to-br from-accent-teal/10 to-accent-cyan/5 rounded-xl p-4 flex flex-col items-center gap-2 border border-accent-teal/20 shadow-sm hover:shadow-md transition-shadow min-h-[100px]"
            >
              <div className="w-12 h-12 rounded-full bg-accent-teal/15 flex items-center justify-center">
                <PencilIcon className="w-6 h-6 text-accent-teal" />
              </div>
              <span className="text-sm text-text-primary text-center leading-tight font-semibold">
                {lang === 'ru' ? 'Записать еду' : 'Log Meal'}
              </span>
            </button>
            <button
              onClick={() => navigate('/exercises')}
              className="bg-gradient-to-br from-accent-blue/10 to-accent-indigo/5 rounded-xl p-4 flex flex-col items-center gap-2 border border-accent-blue/20 shadow-sm hover:shadow-md transition-shadow min-h-[100px]"
            >
              <div className="w-12 h-12 rounded-full bg-accent-blue/15 flex items-center justify-center">
                <DumbbellIcon className="w-6 h-6 text-accent-blue" />
              </div>
              <span className="text-sm text-text-primary text-center leading-tight font-semibold">
                {lang === 'ru' ? 'Тренировка' : 'Start Workout'}
              </span>
            </button>
            <button
              onClick={() => navigate('/meals')}
              className="bg-gradient-to-br from-accent-orange/10 to-accent-amber/5 rounded-xl p-4 flex flex-col items-center gap-2 border border-accent-orange/20 shadow-sm hover:shadow-md transition-shadow min-h-[100px]"
            >
              <div className="w-12 h-12 rounded-full bg-accent-orange/15 flex items-center justify-center">
                <UtensilsIcon className="w-6 h-6 text-accent-orange" />
              </div>
              <span className="text-sm text-text-primary text-center leading-tight font-semibold">
                {lang === 'ru' ? 'Питание' : 'Meal Plan'}
              </span>
            </button>
          </div>
        </>
      )}
    </div>
  )
}
