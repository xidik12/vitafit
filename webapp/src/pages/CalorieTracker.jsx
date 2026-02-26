import { useEffect, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import MacroBar from '../components/MacroBar'
import FoodSearchModal from '../components/FoodSearchModal'
import api from '../utils/api'

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

const WATER_STEP_ML = 250

function MealSection({ mealType, entries, onAddFood }) {
  const { t } = useTranslation('calories')
  const [expanded, setExpanded] = useState(true)

  const totalCal = entries.reduce((sum, e) => sum + (e.calories || 0), 0)

  return (
    <div className="bg-bg-card rounded-xl mb-3 overflow-hidden">
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center justify-between p-3"
      >
        <div className="flex items-center gap-2">
          <span className="text-base">
            {mealType === 'breakfast' ? '🌅' : mealType === 'lunch' ? '☀️' : mealType === 'dinner' ? '🌙' : '🍎'}
          </span>
          <span className="text-sm font-medium text-text-primary capitalize">
            {t(`meal_types.${mealType}`)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-secondary">{Math.round(totalCal)} kcal</span>
          <span className="text-text-secondary text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3">
          {entries.length === 0 ? (
            <p className="text-xs text-text-secondary py-2 text-center">No food logged</p>
          ) : (
            <div className="space-y-1 mb-2">
              {entries.map((entry, i) => (
                <div key={i} className="flex justify-between items-center py-1 border-b border-gray-800 last:border-0">
                  <div>
                    <p className="text-xs text-text-primary">{entry.food_name}</p>
                    <p className="text-xs text-text-secondary">{entry.amount_g}g</p>
                  </div>
                  <span className="text-xs text-text-secondary">{Math.round(entry.calories)} kcal</span>
                </div>
              ))}
            </div>
          )}
          <button
            onClick={() => onAddFood(mealType)}
            className="w-full flex items-center justify-center gap-1 py-2 text-accent-green text-xs border border-accent-green/30 rounded-lg"
          >
            <span>+</span>
            <span>{t('add_food')}</span>
          </button>
        </div>
      )}
    </div>
  )
}

export default function CalorieTracker() {
  const { t } = useTranslation('calories')
  const { t: tc } = useTranslation()
  const { token, profile } = useUser()

  const [dailyData, setDailyData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [addingMeal, setAddingMeal] = useState(null)
  const [addingWater, setAddingWater] = useState(false)

  const calGoal = profile?.calorie_goal || 2000
  const proteinGoal = profile?.protein_goal || 150
  const carbsGoal = profile?.carbs_goal || 250
  const fatGoal = profile?.fat_goal || 65
  const waterGoal = profile?.water_goal_ml || 2000

  useEffect(() => {
    if (!token) return
    fetchDaily()
  }, [token])

  async function fetchDaily() {
    setLoading(true)
    try {
      const data = await api.get('/api/calories/daily', token)
      setDailyData(data)
    } catch {
      setDailyData({ logs: [], water_ml: 0 })
    }
    setLoading(false)
  }

  const logsByMeal = useCallback(() => {
    const map = {}
    MEAL_TYPES.forEach(mt => { map[mt] = [] })
    if (!dailyData?.logs) return map
    dailyData.logs.forEach(entry => {
      const mt = entry.meal_type || 'snack'
      if (!map[mt]) map[mt] = []
      map[mt].push(entry)
    })
    return map
  }, [dailyData])

  const totals = useCallback(() => {
    if (!dailyData?.logs) return { calories: 0, protein: 0, carbs: 0, fat: 0 }
    return dailyData.logs.reduce(
      (acc, e) => ({
        calories: acc.calories + (e.calories || 0),
        protein: acc.protein + (e.protein || 0),
        carbs: acc.carbs + (e.carbs || 0),
        fat: acc.fat + (e.fat || 0),
      }),
      { calories: 0, protein: 0, carbs: 0, fat: 0 }
    )
  }, [dailyData])

  async function logWater(amount) {
    if (!token) return
    try {
      await api.post('/api/calories/water', { amount_ml: amount }, token)
      setDailyData(prev => ({ ...prev, water_ml: (prev?.water_ml || 0) + amount }))
    } catch (err) {
      console.error(err)
    }
  }

  function handleFoodAdded(logData) {
    setDailyData(prev => ({
      ...prev,
      logs: [...(prev?.logs || []), logData],
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const t2 = totals()
  const meals = logsByMeal()
  const calRemaining = Math.max(0, calGoal - t2.calories)
  const calOver = t2.calories > calGoal ? t2.calories - calGoal : 0
  const waterMl = dailyData?.water_ml || 0
  const waterPercent = Math.min(100, (waterMl / waterGoal) * 100)

  return (
    <div className="p-4">
      {/* Header */}
      <h1 className="text-xl font-bold text-text-primary mb-4">{t('title')}</h1>

      {/* Calorie summary */}
      <div className="bg-bg-secondary rounded-2xl p-4 mb-4">
        <div className="flex justify-between items-center mb-3">
          <div className="text-center">
            <p className="text-2xl font-bold text-accent-green">{Math.round(t2.calories)}</p>
            <p className="text-xs text-text-secondary">{t('daily_total')}</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-text-primary">{calGoal}</p>
            <p className="text-xs text-text-secondary">Goal</p>
          </div>
          <div className="text-center">
            {calOver > 0 ? (
              <>
                <p className="text-lg font-bold text-accent-red">{Math.round(calOver)}</p>
                <p className="text-xs text-text-secondary">{t('over')}</p>
              </>
            ) : (
              <>
                <p className="text-lg font-bold text-accent-green">{Math.round(calRemaining)}</p>
                <p className="text-xs text-text-secondary">{t('remaining')}</p>
              </>
            )}
          </div>
        </div>

        {/* Macro bars */}
        <div className="mt-2">
          <MacroBar
            label={tc('common.protein')}
            current={t2.protein}
            target={proteinGoal}
            color="#60a5fa"
          />
          <MacroBar
            label={tc('common.carbs')}
            current={t2.carbs}
            target={carbsGoal}
            color="#fbbf24"
          />
          <MacroBar
            label={tc('common.fat')}
            current={t2.fat}
            target={fatGoal}
            color="#f87171"
          />
        </div>
      </div>

      {/* Water tracker */}
      <div className="bg-bg-secondary rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">💧</span>
            <div>
              <p className="text-sm font-medium text-text-primary">{t('water_goal')}</p>
              <p className="text-xs text-text-secondary">{waterMl}/{waterGoal} {tc('common.water_ml')}</p>
            </div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => logWater(WATER_STEP_ML)}
              className="bg-accent-blue/20 text-accent-blue px-3 py-1.5 rounded-lg text-xs font-medium"
            >
              +{WATER_STEP_ML}{tc('common.water_ml')}
            </button>
          </div>
        </div>
        <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300 bg-accent-blue"
            style={{ width: `${waterPercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-text-secondary">{Math.round(waterPercent)}%</span>
          <span className="text-xs text-text-secondary">{waterGoal}{tc('common.water_ml')} goal</span>
        </div>
      </div>

      {/* Meal sections */}
      {MEAL_TYPES.map(mealType => (
        <MealSection
          key={mealType}
          mealType={mealType}
          entries={meals[mealType] || []}
          onAddFood={mt => setAddingMeal(mt)}
        />
      ))}

      {/* Food search modal */}
      {addingMeal && (
        <FoodSearchModal
          mealType={addingMeal}
          onAdd={handleFoodAdded}
          onClose={() => setAddingMeal(null)}
        />
      )}
    </div>
  )
}
