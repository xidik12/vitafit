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
  { id: 'first_log', Icon: PencilIcon, labelKey: 'ach_first_log', color: 'accent-teal' },
  { id: 'streak_3', Icon: BoltIcon, labelKey: 'ach_streak_3', color: 'accent-orange' },
  { id: 'streak_7', Icon: FireIcon, labelKey: 'ach_streak_7', color: 'accent-orange' },
  { id: 'streak_14', Icon: SparklesIcon, labelKey: 'ach_streak_14', color: 'accent-amber' },
  { id: 'streak_30', Icon: GemIcon, labelKey: 'ach_streak_30', color: 'accent-indigo' },
  { id: 'streak_60', Icon: CrownIcon, labelKey: 'ach_streak_60', color: 'accent-purple' },
  { id: 'streak_100', Icon: TrophyIcon, labelKey: 'ach_streak_100', color: 'accent-pink' },
  { id: 'workout_10', Icon: DumbbellIcon, labelKey: 'ach_workout_10', color: 'accent-blue' },
  { id: 'hydration', Icon: DropletIcon, labelKey: 'ach_hydration', color: 'accent-cyan' },
  { id: 'level_5', Icon: StarIcon, labelKey: 'ach_level_5', color: 'accent-green' },
  { id: 'level_10', Icon: StarIcon, labelKey: 'ach_level_10', color: 'accent-emerald' },
  { id: 'goal_reached', Icon: TargetIcon, labelKey: 'ach_goal_reached', color: 'accent-red' },
]

const achievementColorMap = {
  'accent-teal': { bg: 'bg-accent-teal/10', border: 'border-accent-teal/30', text: 'text-accent-teal' },
  'accent-orange': { bg: 'bg-accent-orange/10', border: 'border-accent-orange/30', text: 'text-accent-orange' },
  'accent-amber': { bg: 'bg-accent-amber/10', border: 'border-accent-amber/30', text: 'text-accent-amber' },
  'accent-indigo': { bg: 'bg-accent-indigo/10', border: 'border-accent-indigo/30', text: 'text-accent-indigo' },
  'accent-purple': { bg: 'bg-accent-purple/10', border: 'border-accent-purple/30', text: 'text-accent-purple' },
  'accent-pink': { bg: 'bg-accent-pink/10', border: 'border-accent-pink/30', text: 'text-accent-pink' },
  'accent-blue': { bg: 'bg-accent-blue/10', border: 'border-accent-blue/30', text: 'text-accent-blue' },
  'accent-cyan': { bg: 'bg-accent-cyan/10', border: 'border-accent-cyan/30', text: 'text-accent-cyan' },
  'accent-green': { bg: 'bg-accent-green/10', border: 'border-accent-green/30', text: 'text-accent-green' },
  'accent-emerald': { bg: 'bg-accent-emerald/10', border: 'border-accent-emerald/30', text: 'text-accent-emerald' },
  'accent-red': { bg: 'bg-accent-red/10', border: 'border-accent-red/30', text: 'text-accent-red' },
}

function AchievementBadge({ achievement, unlocked }) {
  const { t } = useTranslation('progress')
  const colors = unlocked ? achievementColorMap[achievement.color] : null
  return (
    <div className={`flex flex-col items-center p-3 rounded-xl border transition-all ${
      unlocked
        ? `${colors.bg} ${colors.border} shadow-sm`
        : 'bg-gray-50 border-border opacity-40'
    }`}>
      <achievement.Icon className={`w-7 h-7 ${unlocked ? colors.text : 'text-text-secondary'}`} />
      <span className={`text-xs mt-1 text-center leading-tight font-medium ${unlocked ? colors.text : 'text-text-secondary'}`}>
        {t(achievement.labelKey)}
      </span>
    </div>
  )
}

function CustomTooltip({ active, payload, label, lang }) {
  const { t } = useTranslation()
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-border rounded-lg px-3 py-2 text-xs shadow-sm">
      <p className="text-text-secondary">{formatDate(label, lang)}</p>
      <p className="text-accent-green font-semibold">{payload[0].value} {t('common.kg')}</p>
    </div>
  )
}

function MeasurementInput({ label, value, onChange }) {
  return (
    <div>
      <label className="text-xs text-text-secondary font-medium">{label}</label>
      <input
        type="number"
        step="0.1"
        value={value || ''}
        onChange={e => onChange(e.target.value ? Number(e.target.value) : null)}
        className="w-full bg-bg-secondary rounded-lg px-2 py-1.5 text-sm text-text-primary outline-none border border-border focus:border-accent-purple transition-colors"
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
        <div className="w-6 h-6 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
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
    <div className="p-4 pb-24">
      {/* Header */}
      <div className="bg-gradient-to-br from-accent-purple/10 via-accent-indigo/5 to-transparent rounded-2xl p-4 mb-4">
        <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
        <p className="text-accent-purple text-xs font-medium mt-1">{t('subtitle')}</p>
      </div>

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
              <h2 className="text-sm font-semibold text-text-primary">{t('measurements')}</h2>
              <button
                onClick={() => setShowMeasurements(!showMeasurements)}
                className="text-xs text-accent-purple font-semibold bg-accent-purple/10 px-3 py-1 rounded-lg"
              >
                {showMeasurements ? t('hide_measurements') : t('add_measurements')}
              </button>
            </div>
            {showMeasurements && (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <MeasurementInput
                    label={t('waist')}
                    value={measurements.waist_cm}
                    onChange={v => setMeasurements(m => ({ ...m, waist_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('hips')}
                    value={measurements.hips_cm}
                    onChange={v => setMeasurements(m => ({ ...m, hips_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('chest')}
                    value={measurements.chest_cm}
                    onChange={v => setMeasurements(m => ({ ...m, chest_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('neck')}
                    value={measurements.neck_cm}
                    onChange={v => setMeasurements(m => ({ ...m, neck_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('left_arm')}
                    value={measurements.left_arm_cm}
                    onChange={v => setMeasurements(m => ({ ...m, left_arm_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('right_arm')}
                    value={measurements.right_arm_cm}
                    onChange={v => setMeasurements(m => ({ ...m, right_arm_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('left_thigh')}
                    value={measurements.left_thigh_cm}
                    onChange={v => setMeasurements(m => ({ ...m, left_thigh_cm: v }))}
                  />
                  <MeasurementInput
                    label={t('right_thigh')}
                    value={measurements.right_thigh_cm}
                    onChange={v => setMeasurements(m => ({ ...m, right_thigh_cm: v }))}
                  />
                </div>
                <button
                  onClick={saveMeasurements}
                  className="w-full bg-gradient-to-r from-accent-purple to-accent-indigo text-white py-2 rounded-xl text-sm font-semibold mt-2 shadow-md shadow-accent-purple/20"
                >
                  {t('save_measurements')}
                </button>
              </div>
            )}
          </div>

          {/* Measurement trend chart */}
          {measChartData.length > 0 && (
            <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
              <h2 className="text-sm font-semibold text-text-primary mb-3">{t('measurement_trend')}</h2>
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
                    name={t('waist_cm')}
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={{ fill: '#f97316', r: 3 }}
                    activeDot={{ r: 5 }}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="body_fat"
                    name={t('body_fat_pct')}
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
              <div className="flex-1 bg-gradient-to-br from-accent-orange/10 to-accent-amber/5 rounded-xl p-3 text-center border border-accent-orange/15">
                <FireIcon className="w-8 h-8 text-accent-orange mx-auto" />
                <p className="text-2xl font-bold text-accent-orange">{streak}</p>
                <p className="text-xs text-text-secondary font-medium">{t('current_streak')}</p>
              </div>
              <div className="flex-1 bg-gradient-to-br from-accent-blue/10 to-accent-indigo/5 rounded-xl p-3 text-center border border-accent-blue/15">
                <MedalIcon className="w-8 h-8 text-accent-blue mx-auto" />
                <p className="text-2xl font-bold text-accent-blue">{longestStreak}</p>
                <p className="text-xs text-text-secondary font-medium">{t('longest_streak')}</p>
              </div>
            </div>

            {/* Level & XP */}
            <div className="bg-gradient-to-br from-accent-purple/5 to-accent-indigo/5 rounded-xl p-3 border border-accent-purple/10">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-text-primary">
                  {t('level', { n: level })}
                </span>
                <span className="text-xs text-text-secondary font-medium">
                  {t('xp', { xp })} / {xpToNext}
                </span>
              </div>
              <div className="w-full h-2.5 bg-white/60 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-accent-purple to-accent-indigo transition-all duration-500"
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
              <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-accent-green to-accent-emerald transition-all duration-500"
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
