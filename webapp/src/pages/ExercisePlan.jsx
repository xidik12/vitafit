import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import ExerciseCard from '../components/ExerciseCard'
import { DumbbellIcon, ClipboardIcon } from '../components/Icons'
import api from '../utils/api'

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_NAMES_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

export default function ExercisePlan() {
  const { t, i18n } = useTranslation('exercises')
  const { t: tc } = useTranslation()
  const { token, profile } = useUser()
  const navigate = useNavigate()

  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [expandedDay, setExpandedDay] = useState(null)
  const [error, setError] = useState(null)

  const dayNames = i18n.language === 'ru' ? DAY_NAMES_RU : DAY_NAMES

  useEffect(() => {
    if (!token) return
    fetchPlan()
  }, [token])

  async function fetchPlan() {
    setLoading(true)
    try {
      const data = await api.get('/api/exercises/plan', token)
      const fetched = data.plan
      // Auto-regenerate if stored plan lacks exercise images (legacy plan)
      if (fetched && fetched.days) {
        const firstDay = fetched.days.find(d => d.exercises && d.exercises.length > 0)
        const firstEx = firstDay?.exercises?.[0]
        if (firstEx && !firstEx.images) {
          try {
            const fresh = await api.post('/api/exercises/plan/generate', {}, token)
            setPlan(fresh.plan)
          } catch {
            setPlan(fetched)
          }
          setLoading(false)
          return
        }
      }
      setPlan(fetched)
    } catch (err) {
      if (!err.message?.includes('Not Found') && !err.message?.includes('404')) setError(err.message)
    }
    setLoading(false)
  }

  async function generatePlan() {
    if (!token) return
    setGenerating(true)
    setError(null)
    try {
      const data = await api.post('/api/exercises/plan/generate', {}, token)
      setPlan(data.plan)
    } catch (err) {
      setError(err.message)
    }
    setGenerating(false)
  }

  const isOnboarded = profile?.onboarding_complete

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-4 pb-24">
      {/* Header */}
      <div className="bg-gradient-to-br from-accent-blue/10 via-accent-indigo/5 to-transparent rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
            <p className="text-accent-blue text-xs font-medium mt-1">{t('subtitle')}</p>
          </div>
          {isOnboarded && (
            <button
              onClick={generatePlan}
              disabled={generating}
              className="text-xs bg-gradient-to-r from-accent-blue to-accent-indigo text-white px-4 py-2 rounded-xl font-semibold shadow-md shadow-accent-blue/20 disabled:opacity-50"
            >
              {generating ? '...' : t('generate')}
            </button>
          )}
        </div>
      </div>

      {!isOnboarded ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <DumbbellIcon className="w-10 h-10 text-text-secondary mx-auto mb-3" />
          <p className="text-text-secondary text-sm mb-4">{t('empty')}</p>
          <button
            onClick={() => navigate('/questionnaire')}
            className="bg-gradient-to-r from-accent-green to-accent-emerald text-white px-6 py-2.5 rounded-xl text-sm font-semibold shadow-md shadow-accent-green/20"
          >
            {tc('dashboard.start_questionnaire')}
          </button>
        </div>
      ) : !plan ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <ClipboardIcon className="w-10 h-10 text-text-secondary mx-auto mb-3" />
          <p className="text-text-secondary text-sm mb-4">{t('empty')}</p>
          <button
            onClick={generatePlan}
            disabled={generating}
            className="bg-gradient-to-r from-accent-blue to-accent-indigo text-white px-6 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50 shadow-md shadow-accent-blue/20"
          >
            {generating ? tc('common.loading') : t('generate')}
          </button>
        </div>
      ) : (
        <>
          {/* Week label */}
          <p className="text-text-secondary text-xs mb-3 font-semibold uppercase tracking-wide">{t('this_week')}</p>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-3 mb-3">
              <p className="text-accent-red text-sm">{error}</p>
            </div>
          )}

          {/* Days */}
          <div className="space-y-2">
            {(plan.days || []).map((day, index) => {
              const isExpanded = expandedDay === index
              const isRestDay = !day.exercises || day.exercises.length === 0

              return (
                <div key={index} className={`bg-white rounded-xl overflow-hidden border shadow-sm border-l-4 ${
                  isRestDay ? 'border-l-gray-300 border-border' : 'border-l-accent-green border-border'
                }`}>
                  <button
                    onClick={() => setExpandedDay(isExpanded ? null : index)}
                    className="w-full flex items-center justify-between p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                        isRestDay ? 'bg-gray-100 text-text-secondary' : 'bg-accent-green/15 text-accent-green'
                      }`}>
                        {dayNames[index] || `D${index + 1}`}
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-semibold text-text-primary">
                          {t('day', { n: index + 1 })}
                        </p>
                        <p className="text-xs text-text-secondary">
                          {isRestDay ? t('rest') : t('exercises_count', { count: day.exercises.length })}
                        </p>
                      </div>
                    </div>
                    {!isRestDay && (
                      <span className="text-text-secondary text-xs">
                        {isExpanded ? '▲' : '▼'}
                      </span>
                    )}
                  </button>

                  {isExpanded && !isRestDay && (
                    <div className="px-3 pb-3">
                      {day.exercises.map((ex, i) => (
                        <ExerciseCard key={i} exercise={ex} />
                      ))}
                      <button
                        onClick={(e) => { e.stopPropagation(); navigate(`/workout/${index}`) }}
                        className="w-full mt-2 bg-gradient-to-r from-accent-green to-accent-emerald text-white py-2.5 rounded-xl text-sm font-semibold shadow-md shadow-accent-green/20"
                      >
                        {t('start_workout', 'Start Workout')}
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
