import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import api from '../utils/api'
import { formatDate } from '../utils/format'

const ACHIEVEMENTS = [
  { id: 'first_log', icon: '📝', label: 'First Log' },
  { id: 'streak_7', icon: '🔥', label: '7-Day Streak' },
  { id: 'streak_30', icon: '💎', label: '30-Day Streak' },
  { id: 'goal_reached', icon: '🏆', label: 'Goal Reached' },
  { id: 'hydration', icon: '💧', label: 'Hydration Pro' },
  { id: 'workout_10', icon: '💪', label: '10 Workouts' },
]

function AchievementBadge({ achievement, unlocked }) {
  return (
    <div className={`flex flex-col items-center p-3 rounded-xl ${unlocked ? 'bg-accent-green/10 border border-accent-green/30' : 'bg-gray-50 border border-border opacity-40'}`}>
      <span className="text-2xl">{achievement.icon}</span>
      <span className="text-xs text-text-secondary mt-1 text-center leading-tight">{achievement.label}</span>
    </div>
  )
}

function CustomTooltip({ active, payload, label, lang }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-border rounded-lg px-3 py-2 text-xs shadow-sm">
      <p className="text-text-secondary">{formatDate(label, lang)}</p>
      <p className="text-accent-green font-semibold">{payload[0].value} kg</p>
    </div>
  )
}

export default function Progress() {
  const { t, i18n } = useTranslation('progress')
  const { token, profile } = useUser()
  const lang = i18n.language

  const [weightData, setWeightData] = useState([])
  const [progressData, setProgressData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    fetchProgress()
  }, [token])

  async function fetchProgress() {
    setLoading(true)
    try {
      const [prog, weights] = await Promise.all([
        api.get('/api/progress/summary', token).catch(() => null),
        api.get('/api/progress/weights', token).catch(() => []),
      ])
      setProgressData(prog)
      setWeightData(Array.isArray(weights) ? weights : weights?.entries || [])
    } catch {
      // Non-critical
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const streak = progressData?.streak || profile?.streak || 0
  const longestStreak = progressData?.longest_streak || 0
  const level = progressData?.level || 1
  const xp = progressData?.xp || 0
  const xpToNext = progressData?.xp_to_next || 100
  const xpPercent = Math.min(100, (xp / xpToNext) * 100)
  const weeklyCompliance = progressData?.weekly_compliance || 0
  const unlockedAchievements = new Set(progressData?.achievements || [])

  const hasData = weightData.length > 0 || streak > 0

  const chartData = weightData.map(w => ({
    date: w.date,
    weight: w.weight_kg,
  }))

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold text-text-primary mb-4">{t('title')}</h1>

      {!hasData ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <span className="text-4xl block mb-3">📊</span>
          <p className="text-text-secondary text-sm">{t('no_data')}</p>
        </div>
      ) : (
        <>
          {/* Weight trend chart */}
          {chartData.length > 0 && (
            <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
              <h2 className="text-sm font-semibold text-text-primary mb-3">{t('weight_trend')}</h2>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#6b7b6b', fontSize: 10 }}
                    tickFormatter={d => {
                      const date = new Date(d)
                      return `${date.getMonth() + 1}/${date.getDate()}`
                    }}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fill: '#6b7b6b', fontSize: 10 }}
                    domain={['dataMin - 1', 'dataMax + 1']}
                    tickFormatter={v => `${v}`}
                  />
                  <Tooltip content={<CustomTooltip lang={lang} />} />
                  <Line
                    type="monotone"
                    dataKey="weight"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ fill: '#22c55e', r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Streak & XP */}
          <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
            <h2 className="text-sm font-semibold text-text-primary mb-3">{t('streak_info')}</h2>
            <div className="flex gap-3 mb-4">
              <div className="flex-1 bg-bg-secondary rounded-xl p-3 text-center">
                <span className="text-3xl block">🔥</span>
                <p className="text-xl font-bold text-accent-orange">{streak}</p>
                <p className="text-xs text-text-secondary">{t('current_streak')}</p>
              </div>
              <div className="flex-1 bg-bg-secondary rounded-xl p-3 text-center">
                <span className="text-3xl block">🏅</span>
                <p className="text-xl font-bold text-accent-blue">{longestStreak}</p>
                <p className="text-xs text-text-secondary">{t('longest_streak')}</p>
              </div>
            </div>

            {/* Level & XP */}
            <div className="bg-bg-secondary rounded-xl p-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-text-primary">
                  {t('level', { n: level })} 🌟
                </span>
                <span className="text-xs text-text-secondary">
                  {t('xp', { xp })} / {xpToNext}
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent-purple transition-all duration-500"
                  style={{ width: `${xpPercent}%` }}
                />
              </div>
            </div>
          </div>

          {/* Weekly compliance */}
          {weeklyCompliance > 0 && (
            <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-sm font-semibold text-text-primary">{t('weekly_compliance')}</h2>
                <span className="text-sm font-bold text-accent-green">{Math.round(weeklyCompliance)}%</span>
              </div>
              <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent-green transition-all duration-500"
                  style={{ width: `${weeklyCompliance}%` }}
                />
              </div>
            </div>
          )}

          {/* Achievements */}
          <div className="bg-white rounded-2xl p-4 border border-border shadow-sm">
            <h2 className="text-sm font-semibold text-text-primary mb-3">{t('achievements')}</h2>
            <div className="grid grid-cols-3 gap-2">
              {ACHIEVEMENTS.map(achievement => (
                <AchievementBadge
                  key={achievement.id}
                  achievement={achievement}
                  unlocked={unlockedAchievements.has(achievement.id)}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
