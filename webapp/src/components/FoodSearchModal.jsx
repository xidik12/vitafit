import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import api from '../utils/api'

export default function FoodSearchModal({ mealType, onAdd, onClose }) {
  const { t, i18n } = useTranslation('calories')
  const { token } = useUser()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedFood, setSelectedFood] = useState(null)
  const [amount, setAmount] = useState(100)

  const search = useCallback(async () => {
    if (!query.trim() || !token) return
    setLoading(true)
    try {
      const data = await api.get(`/api/calories/search?q=${encodeURIComponent(query)}&lang=${i18n.language}`, token)
      setResults(data.results || [])
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }, [query, token, i18n.language])

  const handleAdd = async () => {
    if (!selectedFood || !token) return
    const multiplier = amount / 100
    const logData = {
      meal_type: mealType,
      food_id: selectedFood.id || null,
      food_name: selectedFood.name_ru || selectedFood.name_en,
      amount_g: amount,
      calories: (selectedFood.calories_per_100g || 0) * multiplier,
      protein: (selectedFood.protein_per_100g || 0) * multiplier,
      carbs: (selectedFood.carbs_per_100g || 0) * multiplier,
      fat: (selectedFood.fat_per_100g || 0) * multiplier,
    }
    try {
      await api.post('/api/calories/log', logData, token)
      onAdd?.(logData)
      onClose()
    } catch (err) {
      console.error(err)
    }
  }

  const lang = i18n.language

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-end">
      <div className="bg-white w-full rounded-t-2xl p-4 max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold text-text-primary">{t('add_food')}</h3>
          <button onClick={onClose} className="text-text-secondary text-xl">✕</button>
        </div>

        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder={t('search')}
            className="flex-1 bg-bg-secondary rounded-lg px-3 py-2 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
            autoFocus
          />
          <button
            onClick={search}
            className="bg-accent-green text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
            {loading ? '...' : '🔍'}
          </button>
        </div>

        {selectedFood ? (
          <div className="bg-bg-secondary rounded-xl p-3 border border-border">
            <h4 className="font-medium text-text-primary">
              {lang === 'ru' ? (selectedFood.name_ru || selectedFood.name_en) : selectedFood.name_en}
            </h4>
            <p className="text-xs text-text-secondary mt-1">
              {selectedFood.calories_per_100g} kcal / 100g
            </p>
            <div className="mt-3">
              <label className="text-xs text-text-secondary">{t('amount')}</label>
              <input
                type="number"
                value={amount}
                onChange={e => setAmount(Number(e.target.value))}
                className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-green"
              />
            </div>
            <div className="flex gap-3 mt-2 text-xs text-text-secondary">
              <span>{Math.round((selectedFood.calories_per_100g || 0) * amount / 100)} kcal</span>
              <span>P: {Math.round((selectedFood.protein_per_100g || 0) * amount / 100)}g</span>
              <span>C: {Math.round((selectedFood.carbs_per_100g || 0) * amount / 100)}g</span>
              <span>F: {Math.round((selectedFood.fat_per_100g || 0) * amount / 100)}g</span>
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setSelectedFood(null)}
                className="flex-1 bg-gray-100 py-2 rounded-lg text-sm text-text-primary border border-border"
              >
                {t('common:common.back')}
              </button>
              <button
                onClick={handleAdd}
                className="flex-1 bg-accent-green text-white py-2 rounded-lg text-sm font-medium"
              >
                {t('add_food')}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {results.map((food, i) => (
              <button
                key={i}
                onClick={() => setSelectedFood(food)}
                className="w-full text-left bg-bg-secondary rounded-lg p-3 border border-border hover:border-accent-green transition-colors"
              >
                <div className="text-sm font-medium text-text-primary">
                  {lang === 'ru' ? (food.name_ru || food.name_en) : food.name_en}
                </div>
                <div className="text-xs text-text-secondary mt-0.5">
                  {food.calories_per_100g} kcal · P:{food.protein_per_100g}g · C:{food.carbs_per_100g}g · F:{food.fat_per_100g}g
                </div>
              </button>
            ))}
            {results.length === 0 && !loading && query && (
              <p className="text-center text-text-secondary text-sm py-4">{t('empty')}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
