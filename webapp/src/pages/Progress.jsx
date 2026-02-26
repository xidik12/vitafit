import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import api from '../utils/api'
import { formatDate } from '../utils/format'
import { ChartBarIcon, FireIcon, MedalIcon, PencilIcon, BoltIcon, SparklesIcon, GemIcon, CrownIcon, TrophyIcon, DumbbellIcon, DropletIcon, StarIcon, TargetIcon } from '../components/Icons'

const ACHIEVEMENTS = [
  { id: 'first_log', Icon: PencilIcon, label: 'First Log' },
  { id: 'streak_3', Icon: BoltIcon, label: '3-Day Streak' },
  { id: 'streak_7', Icon: FireIcon, label: '7-Day Streak' },
  { id: 'streak_14', Icon: SparklesIcon, label: '14-Day Streak' },
  { id: 'streak_30', Icon: GemIcon, label: '30-Day Streak' },
  { id: 'streak_60', Icon: CrownIcon, label: '60-Day Streak' },
  { id: 'streak_100', Icon: TrophyIcon, label: '100-Day Streak' },
  { id: 'workout_10', Icon: DumbbellIcon, label: '10 Workouts' },
  { id: 'hydration', Icon: DropletIcon, label: 'Hydration Pro' },
  { id: 'level_5', Icon: StarIcon, label: 'Level 5' },
  { id: 'level_10', Icon: StarIcon, label: 'Level 10' },
  { id: 'goal_reached', Icon: TargetIcon, label: 'Goal Reached' },
]

function AchievementBadge({ achievement, unlocked }) {
  return (
    <div className={`flex flex-col items-center p-3 rounded-xl ${unlocked ? 'bg-accent-green/10 border border-accent-green/30' : 'bg-gray-50 border border-border opacity-40'}`}>
      <achievement.Icon className={`w-7 h-7 ${unlocked ? 'text-accent-green' : 'text-text-secondary'}`} />
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

function MeasurementInput({ label, value, onChange }) {
  return (
    <div>
      <label className="text-xs text-text-secondary">{label}</label>
      <input
        type="number"
        step="0.1"
        value={value || ''}
        onChange={e => onChange(e.target.value ? Number(e.target.value) : null)}
        className="w-full bg-bg-secondary rounded-lg px-2 py-1.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
      />
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
  const [showMeasurements, setShowMeasurements] = useState(false)
  const [measurements, setMeasurements] = useState({})
  const [measurementHistory, setMeasurementHistory] = useState([])

  useEffect(() => {
    if (!token) return
    fetchProgress()
  }, [token])

  async function fetchProgress() {
    setLoading(true)
    try {
      const [prog, weights, measHistory] = await Promise.all([
        api.get('/api/progress/streak', token).catch(() => null),
        api.get('/api/progress/weight', token).catch(() => []),
        api.get('/api/progress/measurements', token).catch(() => []),
      ])
      setProgressData(prog)
      setWeightData(Array.isArray(weights) ? weights : weights?.entries || [])
      setMeasurementHistory(Array.isArray(measHistory) ? measHistory : [])
    } catch {
      // Non-critical
    }
    setLoading(false)
  }

  async function saveMeasurements() {
    try {
      await api.post('/api/progress/measurements', measurements, token)
      setMeasurements({})
      setShowMeasurements(false)
      fetchProgress()
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const streak = progressData?.current_streak || profile?.current_streak || 0
  const longestStreak = progressData?.longest_streak || 0
  const level = progressData?.level || 1
  const xp = progressData?.xp_total || 0
  const xpToNext = (level) * 100  // simple XP threshold formula
  const xpPercent = Math.min(100, (xp / xpToNext) * 100)
  const weeklyCompliance = progressData?.weekly_compliance || 0
  const unlockedAchievements = new Set(progressData?.achievements || [])

  const hasData = weightData.length > 0 || streak > 0

  const chartData = weightData.map(w => ({
    date: w.date,
    weight: w.weight_kg,
  }))

  const measChartData = measurementHistory.map(m => ({
    date: m.date,
    waist: m.waist_cm ?? null,
    body_fat: m.body_fat_pct ?? null,
  })).filter(m => m.waist !== null || m.body_fat !== null)

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold text-text-primary mb-4">{t('title')}</h1>

      {!hasData ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <ChartBarIcon className="w-10 h-10 text-text-secondary mx-auto mb-3" />
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

          {/* Body Measurements form */}
          <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-semibold text-text-primary">Body Measurements</h2>
              <button
                onClick={() => setShowMeasurements(!showMeasurements)}
                className="text-xs text-accent-green"
              >
                {showMeasurements ? 'Hide' : 'Add'}
              </button>
            </div>
            {showMeasurements && (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <MeasurementInput
                    label="Waist (cm)"
                    value={measurements.waist_cm}
                    onChange={v => setMeasurements(m => ({ ...m, waist_cm: v }))}
                  />
                  <MeasurementInput
                    label="Hips (cm)"
                    value={measurements.hips_cm}
                    onChange={v => setMeasurements(m => ({ ...m, hips_cm: v }))}
                  />
                  <MeasurementInput
                    label="Chest (cm)"
                    value={measurements.chest_cm}
                    onChange={v => setMeasurements(m => ({ ...m, chest_cm: v }))}
                  />
                  <MeasurementInput
                    label="Neck (cm)"
                    value={measurements.neck_cm}
                    onChange={v => setMeasurements(m => ({ ...m, neck_cm: v }))}
                  />
                  <MeasurementInput
                    label="L Arm (cm)"
                    value={measurements.left_arm_cm}
                    onChange={v => setMeasurements(m => ({ ...m, left_arm_cm: v }))}
                  />
                  <MeasurementInput
                    label="R Arm (cm)"
                    value={measurements.right_arm_cm}
                    onChange={v => setMeasurements(m => ({ ...m, right_arm_cm: v }))}
                  />
                  <MeasurementInput
                    label="L Thigh (cm)"
                    value={measurements.left_thigh_cm}
                    onChange={v => setMeasurements(m => ({ ...m, left_thigh_cm: v }))}
                  />
                  <MeasurementInput
                    label="R Thigh (cm)"
                    value={measurements.right_thigh_cm}
                    onChange={v => setMeasurements(m => ({ ...m, right_thigh_cm: v }))}
                  />
                </div>
                <button
                  onClick={saveMeasurements}
                  className="w-full bg-accent-green text-white py-2 rounded-xl text-sm font-medium mt-2"
                >
                  Save Measurements
                </button>
              </div>
            )}
          </div>

          {/* Measurement trend chart */}
          {measChartData.length > 0 && (
            <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
              <h2 className="text-sm font-semibold text-text-primary mb-3">Measurement Trends</h2>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={measChartData}>
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
                  <YAxis tick={{ fill: '#6b7b6b', fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
                    labelFormatter={d => formatDate(d, lang)}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line
                    type="monotone"
                    dataKey="waist"
                    name="Waist (cm)"
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={{ fill: '#f97316', r: 3 }}
                    activeDot={{ r: 5 }}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="body_fat"
                    name="Body Fat (%)"
                    stroke="#a855f7"
                    strokeWidth={2}
                    dot={{ fill: '#a855f7', r: 3 }}
                    activeDot={{ r: 5 }}
                    connectNulls
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
                <FireIcon className="w-8 h-8 text-accent-orange mx-auto" />
                <p className="text-xl font-bold text-accent-orange">{streak}</p>
                <p className="text-xs text-text-secondary">{t('current_streak')}</p>
              </div>
              <div className="flex-1 bg-bg-secondary rounded-xl p-3 text-center">
                <MedalIcon className="w-8 h-8 text-accent-blue mx-auto" />
                <p className="text-xl font-bold text-accent-blue">{longestStreak}</p>
                <p className="text-xs text-text-secondary">{t('longest_streak')}</p>
              </div>
            </div>

            {/* Level & XP */}
            <div className="bg-bg-secondary rounded-xl p-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-text-primary">
                  {t('level', { n: level })}
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
