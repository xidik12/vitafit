import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import RecipeCard from '../components/RecipeCard'
import api from '../utils/api'

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_NAMES_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snacks']

function RecipeDetail({ recipe, onClose }) {
  const { i18n, t } = useTranslation('meals')
  const lang = i18n.language
  const title = lang === 'ru' ? (recipe.title_ru || recipe.title_en) : recipe.title_en
  const description = lang === 'ru' ? (recipe.description_ru || recipe.description_en) : recipe.description_en
  const ingredients = lang === 'ru'
    ? (recipe.ingredients_ru || recipe.ingredients_en || [])
    : (recipe.ingredients_en || [])
  const instructions = lang === 'ru'
    ? (recipe.instructions_ru || recipe.instructions_en || [])
    : (recipe.instructions_en || [])

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-end">
      <div className="bg-white w-full rounded-t-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        {recipe.image_url && (
          <img src={recipe.image_url} alt={title} className="w-full h-40 object-cover" />
        )}
        <div className="p-4">
          <div className="flex justify-between items-start mb-2">
            <h2 className="text-lg font-bold text-text-primary flex-1 pr-2">{title}</h2>
            <button onClick={onClose} className="text-text-secondary text-xl">✕</button>
          </div>

          {description && (
            <p className="text-text-secondary text-sm mb-3">{description}</p>
          )}

          <div className="flex gap-3 mb-4 text-xs text-text-secondary">
            {recipe.calories != null && <span>🔥 {Math.round(recipe.calories)} kcal</span>}
            {recipe.cook_time_mins && <span>⏱ {t('cook_time', { mins: recipe.cook_time_mins })}</span>}
          </div>

          {ingredients.length > 0 && (
            <>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Ingredients</h3>
              <ul className="space-y-1 mb-4">
                {ingredients.map((ing, i) => (
                  <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                    <span className="text-accent-green mt-0.5">•</span>
                    <span>{ing}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {instructions.length > 0 && (
            <>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Instructions</h3>
              <ol className="space-y-2">
                {instructions.map((step, i) => (
                  <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                    <span className="text-accent-green font-bold min-w-[20px]">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function MealPlan() {
  const { t, i18n } = useTranslation('meals')
  const { t: tc } = useTranslation()
  const { token, profile } = useUser()
  const navigate = useNavigate()

  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [expandedDay, setExpandedDay] = useState(null)
  const [selectedRecipe, setSelectedRecipe] = useState(null)
  const [error, setError] = useState(null)

  const dayNames = i18n.language === 'ru' ? DAY_NAMES_RU : DAY_NAMES
  const isOnboarded = profile?.onboarding_complete

  useEffect(() => {
    if (!token) return
    fetchPlan()
  }, [token])

  async function fetchPlan() {
    setLoading(true)
    try {
      const data = await api.get('/api/recipes/plan', token)
      setPlan(data)
    } catch {
      // Plan might not exist
    }
    setLoading(false)
  }

  async function generatePlan() {
    if (!token) return
    setGenerating(true)
    setError(null)
    try {
      const data = await api.post('/api/recipes/plan/generate', {}, token)
      setPlan(data)
    } catch (err) {
      setError(err.message)
    }
    setGenerating(false)
  }

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
          <span className="text-4xl block mb-3">🍽️</span>
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
          <p className="text-text-secondary text-xs mb-3">{t('this_week')}</p>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-3 mb-3">
              <p className="text-accent-red text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-2">
            {(plan.days || []).map((day, index) => {
              const isExpanded = expandedDay === index
              const mealCount = MEAL_TYPES.reduce((acc, type) => {
                return acc + (day[type]?.length || (day[type] ? 1 : 0))
              }, 0)

              return (
                <div key={index} className="bg-white rounded-xl overflow-hidden border border-border shadow-sm">
                  <button
                    onClick={() => setExpandedDay(isExpanded ? null : index)}
                    className="w-full flex items-center justify-between p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-accent-orange/20 text-accent-orange flex items-center justify-center text-xs font-bold">
                        {dayNames[index] || `D${index + 1}`}
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-medium text-text-primary">
                          Day {index + 1}
                        </p>
                        <p className="text-xs text-text-secondary">
                          {mealCount} meals
                        </p>
                      </div>
                    </div>
                    <span className="text-text-secondary text-xs">{isExpanded ? '▲' : '▼'}</span>
                  </button>

                  {isExpanded && (
                    <div className="px-3 pb-3">
                      {MEAL_TYPES.map(mealType => {
                        const recipes = Array.isArray(day[mealType])
                          ? day[mealType]
                          : day[mealType]
                          ? [day[mealType]]
                          : []
                        if (recipes.length === 0) return null

                        return (
                          <div key={mealType} className="mb-3">
                            <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">
                              {t(mealType)}
                            </h4>
                            {recipes.map((recipe, ri) => (
                              <RecipeCard
                                key={ri}
                                recipe={recipe}
                                onClick={() => setSelectedRecipe(recipe)}
                              />
                            ))}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      {selectedRecipe && (
        <RecipeDetail recipe={selectedRecipe} onClose={() => setSelectedRecipe(null)} />
      )}
    </div>
  )
}
