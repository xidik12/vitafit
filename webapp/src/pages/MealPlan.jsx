import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import RecipeCard from '../components/RecipeCard'
import { UtensilsIcon, ClipboardIcon } from '../components/Icons'
import api from '../utils/api'

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_NAMES_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snacks']

const mealDotColors = {
  breakfast: 'bg-accent-orange',
  lunch: 'bg-accent-amber',
  dinner: 'bg-accent-blue',
  snacks: 'bg-accent-green',
}

function RecipeDetail({ recipe, onClose }) {
  const { i18n, t } = useTranslation('meals')
  const { t: tc } = useTranslation()
  const { token } = useUser()
  const lang = i18n.language

  const [fullRecipe, setFullRecipe] = useState(null)
  const [fetchLoading, setFetchLoading] = useState(false)

  // Fetch full recipe details from API when recipe_id exists
  useEffect(() => {
    if (!recipe.recipe_id || !token) return
    setFetchLoading(true)
    api.get(`/api/recipes/${recipe.recipe_id}`, token)
      .then(data => setFullRecipe(data.recipe || data))
      .catch(() => {})
      .finally(() => setFetchLoading(false))
  }, [recipe.recipe_id, token])

  // Merge fetched data with embedded plan data
  const r = fullRecipe || recipe

  const title = lang === 'ru' ? (r.title_ru || r.title_en) : r.title_en
  const description = lang === 'ru' ? (r.description_ru || r.description_en) : r.description_en

  // Build ingredients list
  // API returns `ingredients` as [{name, amount, unit}], plan_json has no ingredients
  const ingredients = (() => {
    if (r.ingredients && Array.isArray(r.ingredients) && r.ingredients.length > 0) {
      return r.ingredients.map(ing =>
        typeof ing === 'string'
          ? ing
          : [ing.amount, ing.unit, ing.name].filter(Boolean).join(' ')
      )
    }
    // Fallback to legacy fields if present
    const legacy = lang === 'ru'
      ? (r.ingredients_ru || r.ingredients_en || [])
      : (r.ingredients_en || [])
    return Array.isArray(legacy) ? legacy : []
  })()

  // Build instructions steps
  const steps = (() => {
    if (r.instructions_json && Array.isArray(r.instructions_json) && r.instructions_json.length > 0) {
      return r.instructions_json
    }
    // For RU, prefer instructions_ru text
    const textBlob = lang === 'ru'
      ? (r.instructions_ru || r.instructions || '')
      : (r.instructions || '')
    if (textBlob && typeof textBlob === 'string') {
      return textBlob.split('\n').map(s => s.trim()).filter(Boolean)
    }
    return []
  })()

  return (
    <div className="fixed inset-0 bg-black/40 z-[60] flex items-end">
      <div className="bg-white w-full rounded-t-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        {/* Hero image */}
        {r.image_url ? (
          <img src={r.image_url} alt={title} className="w-full h-48 object-cover" />
        ) : (
          <div className="w-full h-48 bg-gradient-to-br from-accent-orange/20 via-accent-amber/10 to-accent-green/20 flex items-center justify-center">
            <UtensilsIcon className="w-12 h-12 text-text-secondary" />
          </div>
        )}

        <div className="p-4">
          <div className="flex justify-between items-start mb-2">
            <h2 className="text-lg font-bold text-text-primary flex-1 pr-2">{title}</h2>
            <button onClick={onClose} className="text-text-secondary text-2xl hover:text-text-primary transition-colors p-2 min-w-[44px] min-h-[44px] flex items-center justify-center">✕</button>
          </div>

          {description && (
            <p className="text-text-secondary text-base mb-3">{description}</p>
          )}

          {/* Macro chips */}
          <div className="flex gap-2 mb-4 flex-wrap">
            {(r.calories ?? recipe.calories) != null && (
              <span className="px-3 py-1.5 bg-accent-orange/10 text-accent-orange rounded-full text-sm font-semibold">
                {Math.round(r.calories ?? recipe.calories)} {tc('common.kcal')}
              </span>
            )}
            {(r.protein ?? recipe.protein) != null && (
              <span className="px-3 py-1.5 bg-accent-blue/10 text-accent-blue rounded-full text-sm font-semibold">
                {t('macro_p')} {Math.round(r.protein ?? recipe.protein)}{tc('common.g')}
              </span>
            )}
            {(r.carbs ?? recipe.carbs) != null && (
              <span className="px-3 py-1.5 bg-accent-green/10 text-accent-green rounded-full text-sm font-semibold">
                {t('macro_c')} {Math.round(r.carbs ?? recipe.carbs)}{tc('common.g')}
              </span>
            )}
            {(r.fat ?? recipe.fat) != null && (
              <span className="px-3 py-1.5 bg-accent-red/10 text-accent-red rounded-full text-sm font-semibold">
                {t('macro_f')} {Math.round(r.fat ?? recipe.fat)}{tc('common.g')}
              </span>
            )}
            {(r.cook_time_mins || recipe.cook_time_mins) && (
              <span className="px-3 py-1.5 bg-gray-100 text-text-secondary rounded-full text-sm font-medium">
                {r.cook_time_mins || recipe.cook_time_mins} {tc('common.min')}
              </span>
            )}
          </div>

          {/* Loading spinner while fetching full recipe */}
          {fetchLoading && (
            <div className="flex justify-center py-4">
              <div className="w-5 h-5 border-2 border-accent-orange border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {!fetchLoading && ingredients.length > 0 && (
            <>
              <h3 className="text-base font-semibold text-text-primary mb-2">{t('ingredients')}</h3>
              <ul className="space-y-1.5 mb-4">
                {ingredients.map((ing, i) => (
                  <li key={i} className="text-base text-text-secondary flex items-start gap-2">
                    <span className="text-accent-green mt-0.5">•</span>
                    <span>{ing}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {!fetchLoading && steps.length > 0 && (
            <>
              <h3 className="text-base font-semibold text-text-primary mb-2">{t('instructions')}</h3>
              <ol className="space-y-2">
                {steps.map((step, i) => (
                  <li key={i} className="text-base text-text-secondary flex items-start gap-2">
                    <span className="text-accent-green font-bold min-w-[20px]">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </>
          )}

          {/* YouTube button */}
          {(r.youtube_url || recipe.youtube_url) && (
            <a
              href={r.youtube_url || recipe.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full bg-red-500 text-white py-3 rounded-xl text-base font-semibold mt-4 min-h-[48px]"
            >
              {t('watch_video')}
            </a>
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
      const fetched = data.plan
      // Auto-regenerate if stored plan lacks images (legacy plan from before image support)
      if (fetched && fetched.days) {
        const firstMeal = fetched.days[0]?.meals?.breakfast || fetched.days[0]?.meals?.lunch
        const meal = Array.isArray(firstMeal) ? firstMeal[0] : firstMeal
        if (meal && !meal.image_url && !localStorage.getItem('vitafit-meal-plan-upgraded')) {
          // Old plan without images — regenerate silently (only once)
          localStorage.setItem('vitafit-meal-plan-upgraded', '1')
          try {
            const fresh = await api.post('/api/recipes/plan/generate', {}, token)
            setPlan(fresh.plan)
          } catch {
            setPlan(fetched) // fallback to old plan if regeneration fails
          }
          setLoading(false)
          return
        }
      }
      setPlan(fetched)
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
      setPlan(data.plan)
    } catch (err) {
      setError(err.message)
    }
    setGenerating(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 border-2 border-accent-orange border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-4 pb-24">
      {/* Header */}
      <div className="bg-gradient-to-br from-accent-orange/10 via-accent-amber/5 to-transparent rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
            <p className="text-accent-orange text-sm font-medium mt-1">{t('subtitle')}</p>
          </div>
          {isOnboarded && (
            <button
              onClick={generatePlan}
              disabled={generating}
              className="text-sm bg-gradient-to-r from-accent-orange to-accent-amber text-white px-5 py-3 rounded-xl font-semibold shadow-md shadow-accent-orange/20 disabled:opacity-50 min-h-[44px]"
            >
              {generating ? '...' : t('generate')}
            </button>
          )}
        </div>
      </div>

      {!isOnboarded ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <UtensilsIcon className="w-10 h-10 text-text-secondary mx-auto mb-3" />
          <p className="text-text-secondary text-base mb-4">{t('empty')}</p>
          <button
            onClick={() => navigate('/questionnaire')}
            className="bg-gradient-to-r from-accent-green to-accent-emerald text-white px-6 py-3 rounded-xl text-base font-semibold shadow-md shadow-accent-green/20 min-h-[48px]"
          >
            {tc('dashboard.start_questionnaire')}
          </button>
        </div>
      ) : !plan ? (
        <div className="bg-white rounded-2xl p-6 text-center border border-border shadow-sm">
          <ClipboardIcon className="w-12 h-12 text-text-secondary mx-auto mb-3" />
          <p className="text-text-secondary text-base mb-4">{t('empty')}</p>
          <button
            onClick={generatePlan}
            disabled={generating}
            className="bg-gradient-to-r from-accent-orange to-accent-amber text-white px-6 py-3 rounded-xl text-base font-semibold disabled:opacity-50 shadow-md shadow-accent-orange/20 min-h-[48px]"
          >
            {generating ? tc('common.loading') : t('generate')}
          </button>
        </div>
      ) : (
        <>
          <p className="text-text-secondary text-sm mb-3 font-semibold uppercase tracking-wide">{t('this_week')}</p>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-3 mb-3">
              <p className="text-accent-red text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-2">
            {(plan.days || []).map((day, index) => {
              const isExpanded = expandedDay === index
              const mealCount = MEAL_TYPES.reduce((acc, type) => {
                const meal = day.meals?.[type]
                return acc + (Array.isArray(meal) ? meal.length : meal ? 1 : 0)
              }, 0)

              return (
                <div key={index} className="bg-white rounded-xl overflow-hidden border border-border shadow-sm border-l-4 border-l-accent-orange">
                  <button
                    onClick={() => setExpandedDay(isExpanded ? null : index)}
                    className="w-full flex items-center justify-between p-3 min-h-[52px]"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-accent-orange/15 text-accent-orange flex items-center justify-center text-sm font-bold">
                        {dayNames[index] || `D${index + 1}`}
                      </div>
                      <div className="text-left">
                        <p className="text-base font-semibold text-text-primary">
                          {t('day', { n: index + 1 })}
                        </p>
                        <p className="text-sm text-text-secondary">
                          {t('meals_count', { count: mealCount })}
                        </p>
                      </div>
                    </div>
                    <span className="text-text-secondary text-sm">{isExpanded ? '▲' : '▼'}</span>
                  </button>

                  {isExpanded && (
                    <div className="px-3 pb-3">
                      {MEAL_TYPES.map(mealType => {
                        const meal = day.meals?.[mealType]
                        const recipes = Array.isArray(meal)
                          ? meal
                          : meal
                          ? [meal]
                          : []
                        if (recipes.length === 0) return null

                        return (
                          <div key={mealType} className="mb-3">
                            <h4 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2 flex items-center gap-2">
                              <span className={`w-2.5 h-2.5 rounded-full ${mealDotColors[mealType] || 'bg-gray-400'}`}></span>
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
