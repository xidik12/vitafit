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

  const steps = recipe.instructions_json
    || (Array.isArray(instructions) ? instructions : [])

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-end">
      <div className="bg-white w-full rounded-t-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        {/* Hero image */}
        {recipe.image_url ? (
          <img src={recipe.image_url} alt={title} className="w-full h-48 object-cover" />
        ) : (
          <div className="w-full h-48 bg-gradient-to-br from-accent-green/20 to-accent-orange/20 flex items-center justify-center">
            <UtensilsIcon className="w-12 h-12 text-text-secondary" />
          </div>
        )}

        <div className="p-4">
          <div className="flex justify-between items-start mb-2">
            <h2 className="text-lg font-bold text-text-primary flex-1 pr-2">{title}</h2>
            <button onClick={onClose} className="text-text-secondary text-xl">✕</button>
          </div>

          {description && (
            <p className="text-text-secondary text-sm mb-3">{description}</p>
          )}

          {/* Macro chips */}
          <div className="flex gap-2 mb-4 flex-wrap">
            {recipe.calories != null && (
              <span className="px-2.5 py-1 bg-accent-orange/10 text-accent-orange rounded-full text-xs font-medium">
                {Math.round(recipe.calories)} kcal
              </span>
            )}
            {recipe.protein != null && (
              <span className="px-2.5 py-1 bg-accent-blue/10 text-accent-blue rounded-full text-xs font-medium">
                P: {Math.round(recipe.protein)}g
              </span>
            )}
            {recipe.carbs != null && (
              <span className="px-2.5 py-1 bg-accent-green/10 text-accent-green rounded-full text-xs font-medium">
                C: {Math.round(recipe.carbs)}g
              </span>
            )}
            {recipe.fat != null && (
              <span className="px-2.5 py-1 bg-accent-red/10 text-accent-red rounded-full text-xs font-medium">
                F: {Math.round(recipe.fat)}g
              </span>
            )}
            {recipe.cook_time_mins && (
              <span className="px-2.5 py-1 bg-gray-100 text-text-secondary rounded-full text-xs font-medium">
                {recipe.cook_time_mins} min
              </span>
            )}
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

          {steps.length > 0 && (
            <>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Instructions</h3>
              <ol className="space-y-2">
                {steps.map((step, i) => (
                  <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                    <span className="text-accent-green font-bold min-w-[20px]">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </>
          )}

          {/* YouTube button */}
          {recipe.youtube_url && (
            <a
              href={recipe.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full bg-red-500 text-white py-2.5 rounded-xl text-sm font-semibold mt-4"
            >
              Watch Video
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
      setPlan(data.plan)
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
          <UtensilsIcon className="w-10 h-10 text-text-secondary mx-auto mb-3" />
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
          <ClipboardIcon className="w-10 h-10 text-text-secondary mx-auto mb-3" />
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
                const meal = day.meals?.[type]
                return acc + (Array.isArray(meal) ? meal.length : meal ? 1 : 0)
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
                        const meal = day.meals?.[mealType]
                        const recipes = Array.isArray(meal)
                          ? meal
                          : meal
                          ? [meal]
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
