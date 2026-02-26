import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import ExerciseCard from '../components/ExerciseCard'
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
      setPlan(data)
    } catch (err) {
      if (err.message !== '404') setError(err.message)
    }
    setLoading(false)
  }

  async function generatePlan() {
    if (!token) return
    setGenerating(true)
    setError(null)
    try {
      const data = await api.post('/api/exercises/plan/generate', {}, token)
      setPlan(data)
    } catch (err) {
      setError(err.message)
    }
    setGenerating(false)
  }

  const isOnboarded = profile?.onboarded

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-text-primary">{t('title')}</h1>
        {isOnboarded && (
          <button
            onClick={generatePlan}
            disabled={generating}
            className="text-xs bg-accent-green/10 text-accent-green border border-accent-green/30 px-3 py-1.5 rounded-lg"
          >
            {generating ? '...' : t('generate')}
          </button>
        )}
      </div>

      {!isOnboarded ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <span className="text-4xl block mb-3">💪</span>
          <p className="text-text-secondary text-sm mb-4">{t('empty')}</p>
          <button
            onClick={() => navigate('/questionnaire')}
            className="bg-accent-green text-white px-6 py-2.5 rounded-xl text-sm font-semibold"
          >
            {tc('dashboard.start_questionnaire')}
          </button>
        </div>
      ) : !plan ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <span className="text-4xl block mb-3">📋</span>
          <p className="text-text-secondary text-sm mb-4">{t('empty')}</p>
          <button
            onClick={generatePlan}
            disabled={generating}
            className="bg-accent-green text-white px-6 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50"
          >
            {generating ? tc('common.loading') : t('generate')}
          </button>
        </div>
      ) : (
        <>
          {/* Week label */}
          <p className="text-text-secondary text-xs mb-3">{t('this_week')}</p>

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
                <div key={index} className="bg-white rounded-xl overflow-hidden border border-border shadow-sm">
                  <button
                    onClick={() => setExpandedDay(isExpanded ? null : index)}
                    className="w-full flex items-center justify-between p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                        isRestDay ? 'bg-gray-100 text-text-secondary' : 'bg-accent-green/20 text-accent-green'
                      }`}>
                        {dayNames[index] || `D${index + 1}`}
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-medium text-text-primary">
                          {t('day', { n: index + 1 })}
                        </p>
                        <p className="text-xs text-text-secondary">
                          {isRestDay ? t('rest') : `${day.exercises.length} exercises`}
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
