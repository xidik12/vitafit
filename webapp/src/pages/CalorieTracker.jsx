import { useEffect, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import MacroBar from '../components/MacroBar'
import FoodSearchModal from '../components/FoodSearchModal'
import api from '../utils/api'
import { SunriseIcon, SunIcon, MoonIcon, AppleIcon, DropletIcon } from '../components/Icons'

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

const WATER_STEP_ML = 250

const mealBorderColors = {
  breakfast: 'border-l-accent-orange',
  lunch: 'border-l-accent-amber',
  dinner: 'border-l-accent-blue',
  snack: 'border-l-accent-green',
}

function MealSection({ mealType, entries, onAddFood }) {
  const { t } = useTranslation('calories')
  const [expanded, setExpanded] = useState(true)

  const totalCal = entries.reduce((sum, e) => sum + (e.calories || 0), 0)

  return (
    <div className={`bg-white rounded-xl mb-3 overflow-hidden border border-border shadow-sm border-l-4 ${mealBorderColors[mealType] || 'border-l-accent-green'}`}>
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center justify-between p-3"
      >
        <div className="flex items-center gap-2">
          {mealType === 'breakfast' ? <SunriseIcon className="w-5 h-5 text-accent-orange" /> :
           mealType === 'lunch' ? <SunIcon className="w-5 h-5 text-accent-amber" /> :
           mealType === 'dinner' ? <MoonIcon className="w-5 h-5 text-accent-blue" /> :
           <AppleIcon className="w-5 h-5 text-accent-green" />}
          <span className="text-sm font-semibold text-text-primary capitalize">
            {t(`meal_types.${mealType}`)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-text-secondary bg-gray-50 px-2 py-0.5 rounded-full">{Math.round(totalCal)} kcal</span>
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
                <div key={i} className="flex justify-between items-center py-1.5 border-b border-border/50 last:border-0">
                  <div>
                    <p className="text-sm text-text-primary">{entry.food_name}</p>
                    <p className="text-xs text-text-secondary">{entry.amount_g}g</p>
                  </div>
                  <span className="text-xs font-medium text-text-secondary">{Math.round(entry.calories)} kcal</span>
                </div>
              ))}
            </div>
          )}
          <button
            onClick={() => onAddFood(mealType)}
            className="w-full flex items-center justify-center gap-1 py-2 text-accent-green text-xs font-medium border border-accent-green/30 rounded-lg hover:bg-accent-green/5 transition-colors"
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

  const calGoal = dailyData?.targets?.calories || profile?.target_calories || 2000
  const proteinGoal = dailyData?.targets?.protein || profile?.target_protein || 150
  const carbsGoal = dailyData?.targets?.carbs || profile?.target_carbs || 250
  const fatGoal = dailyData?.targets?.fat || profile?.target_fat || 65
  const waterGoal = dailyData?.targets?.water_ml || profile?.target_water_ml || 2000

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
      setDailyData({ meals: {}, totals: { calories: 0, protein: 0, carbs: 0, fat: 0 }, water_ml: 0 })
    }
    setLoading(false)
  }

  const logsByMeal = useCallback(() => {
    const map = {}
    MEAL_TYPES.forEach(mt => { map[mt] = [] })
    if (!dailyData?.meals) return map
    MEAL_TYPES.forEach(mt => {
      if (dailyData.meals[mt]) {
        map[mt] = dailyData.meals[mt]
      }
    })
    return map
  }, [dailyData])

  const totals = useCallback(() => {
    if (dailyData?.totals) return dailyData.totals
    return { calories: 0, protein: 0, carbs: 0, fat: 0 }
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
    setDailyData(prev => {
      const mt = logData.meal_type || 'snack'
      const meals = { ...(prev?.meals || {}) }
      meals[mt] = [...(meals[mt] || []), logData]
      // Recalculate totals
      const totals = { calories: 0, protein: 0, carbs: 0, fat: 0 }
      Object.values(meals).forEach(entries => {
        entries.forEach(e => {
          totals.calories += e.calories || 0
          totals.protein += e.protein || 0
          totals.carbs += e.carbs || 0
          totals.fat += e.fat || 0
        })
      })
      return { ...prev, meals, totals }
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-teal border-t-transparent rounded-full animate-spin" />
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
    <div className="p-4 pb-24">
      {/* Header */}
      <div className="bg-gradient-to-br from-accent-teal/10 via-accent-cyan/5 to-transparent rounded-2xl p-4 mb-4">
        <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
        <p className="text-accent-teal text-xs font-medium mt-1">Track your daily nutrition</p>
      </div>

      {/* Calorie summary */}
      <div className="bg-white rounded-2xl p-4 mb-4 border border-border shadow-sm">
        <div className="flex justify-between items-center mb-3">
          <div className="text-center flex-1">
            <div className="bg-gradient-to-br from-accent-green/10 to-accent-emerald/5 rounded-xl py-2 px-3">
              <p className="text-2xl font-bold text-accent-green">{Math.round(t2.calories)}</p>
              <p className="text-xs text-text-secondary font-medium">{t('daily_total')}</p>
            </div>
          </div>
          <div className="text-center flex-1 mx-2">
            <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl py-2 px-3">
              <p className="text-xl font-bold text-text-primary">{calGoal}</p>
              <p className="text-xs text-text-secondary font-medium">Goal</p>
            </div>
          </div>
          <div className="text-center flex-1">
            {calOver > 0 ? (
              <div className="bg-gradient-to-br from-accent-red/10 to-accent-red/5 rounded-xl py-2 px-3">
                <p className="text-xl font-bold text-accent-red">{Math.round(calOver)}</p>
                <p className="text-xs text-text-secondary font-medium">{t('over')}</p>
              </div>
            ) : (
              <div className="bg-gradient-to-br from-accent-teal/10 to-accent-cyan/5 rounded-xl py-2 px-3">
                <p className="text-xl font-bold text-accent-teal">{Math.round(calRemaining)}</p>
                <p className="text-xs text-text-secondary font-medium">{t('remaining')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Macro bars */}
        <div className="mt-3">
          <MacroBar
            label={tc('common.protein')}
            current={t2.protein}
            target={proteinGoal}
            color="#3b82f6"
          />
          <MacroBar
            label={tc('common.carbs')}
            current={t2.carbs}
            target={carbsGoal}
            color="#f59e0b"
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
      <div className="bg-gradient-to-br from-accent-blue/5 to-accent-cyan/5 rounded-2xl p-4 mb-4 border border-accent-blue/15 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-full bg-accent-blue/15 flex items-center justify-center">
              <DropletIcon className="w-5 h-5 text-accent-blue" />
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary">{t('water_goal')}</p>
              <p className="text-xs text-text-secondary">{waterMl}/{waterGoal} {tc('common.water_ml')}</p>
            </div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => logWater(WATER_STEP_ML)}
              className="bg-accent-blue/20 text-accent-blue px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-accent-blue/30 transition-colors"
            >
              +{WATER_STEP_ML}{tc('common.water_ml')}
            </button>
          </div>
        </div>
        <div className="w-full h-3 bg-white/60 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300 bg-gradient-to-r from-accent-blue to-accent-cyan"
            style={{ width: `${waterPercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-text-secondary font-medium">{Math.round(waterPercent)}%</span>
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
