import { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import api from '../utils/api'

export default function FoodSearchModal({ mealType, onAdd, onClose }) {
  const { t, i18n } = useTranslation('calories')
  const { t: tc } = useTranslation()
  const { token } = useUser()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedFood, setSelectedFood] = useState(null)
  const [amount, setAmount] = useState(100)
  const [recentFoods, setRecentFoods] = useState([])

  useEffect(() => {
    if (!token) return
    api.get('/api/foods/recent', token)
      .then(data => setRecentFoods(data.foods || data || []))
      .catch(() => {})
  }, [token])

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
    <div className="fixed inset-0 bg-black/40 z-[60] flex items-end">
      <div className="bg-white w-full rounded-t-2xl p-4 max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-bold text-text-primary">{t('add_food')}</h3>
          <button onClick={onClose} className="text-text-secondary text-2xl hover:text-text-primary transition-colors p-2 min-w-[44px] min-h-[44px] flex items-center justify-center">✕</button>
        </div>

        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder={t('search')}
            className="flex-1 bg-bg-secondary rounded-lg px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green transition-colors"
            autoFocus
          />
          <button
            onClick={search}
            className="bg-gradient-to-r from-accent-green to-accent-emerald text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm hover:shadow-md transition-shadow"
          >
            {loading ? '...' : t('search_btn', 'Search')}
          </button>
        </div>

        {selectedFood ? (
          <div className="bg-bg-secondary rounded-xl p-3 border-t-4 border-t-accent-green border border-border">
            {selectedFood.isCustom ? (
              <>
                <h4 className="font-semibold text-text-primary mb-1">
                  {lang === 'ru' ? (selectedFood.name_ru || selectedFood.name_en) : selectedFood.name_en}
                </h4>
                <p className="text-sm text-accent-green font-medium mb-3">{t('custom_food')}</p>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-sm text-text-secondary font-medium">{t('amount')}</label>
                    <input
                      type="number"
                      value={amount}
                      onChange={e => setAmount(Number(e.target.value))}
                      className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-green transition-colors"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-accent-orange font-medium">{t('kcal_per_100g')}</label>
                    <input
                      type="number"
                      value={selectedFood.calories_per_100g || ''}
                      onChange={e => setSelectedFood(prev => ({ ...prev, calories_per_100g: Number(e.target.value) }))}
                      placeholder="0"
                      className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-orange transition-colors"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-accent-blue font-medium">{t('protein_label')}</label>
                    <input
                      type="number"
                      value={selectedFood.protein_per_100g || ''}
                      onChange={e => setSelectedFood(prev => ({ ...prev, protein_per_100g: Number(e.target.value) }))}
                      placeholder="0"
                      className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-blue transition-colors"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-accent-green font-medium">{t('carbs_label')}</label>
                    <input
                      type="number"
                      value={selectedFood.carbs_per_100g || ''}
                      onChange={e => setSelectedFood(prev => ({ ...prev, carbs_per_100g: Number(e.target.value) }))}
                      placeholder="0"
                      className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-green transition-colors"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-accent-red font-medium">{t('fat_label')}</label>
                    <input
                      type="number"
                      value={selectedFood.fat_per_100g || ''}
                      onChange={e => setSelectedFood(prev => ({ ...prev, fat_per_100g: Number(e.target.value) }))}
                      placeholder="0"
                      className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-green transition-colors"
                    />
                  </div>
                </div>
                <div className="flex gap-2 mt-3 flex-wrap">
                  <span className="px-2 py-1 bg-accent-orange/10 text-accent-orange rounded-full text-sm font-semibold">
                    {Math.round((selectedFood.calories_per_100g || 0) * amount / 100)} {tc('common.kcal')}
                  </span>
                  <span className="px-2 py-1 bg-accent-blue/10 text-accent-blue rounded-full text-sm font-semibold">
                    {t('macro_p')} {Math.round((selectedFood.protein_per_100g || 0) * amount / 100)}{tc('common.g')}
                  </span>
                  <span className="px-2 py-1 bg-accent-green/10 text-accent-green rounded-full text-sm font-semibold">
                    {t('macro_c')} {Math.round((selectedFood.carbs_per_100g || 0) * amount / 100)}{tc('common.g')}
                  </span>
                  <span className="px-2 py-1 bg-accent-red/10 text-accent-red rounded-full text-sm font-semibold">
                    {t('macro_f')} {Math.round((selectedFood.fat_per_100g || 0) * amount / 100)}{tc('common.g')}
                  </span>
                </div>
              </>
            ) : (
              <>
                <h4 className="font-semibold text-text-primary">
                  {lang === 'ru' ? (selectedFood.name_ru || selectedFood.name_en) : selectedFood.name_en}
                </h4>
                <p className="text-sm text-text-secondary mt-1">
                  {selectedFood.calories_per_100g} {t('kcal_per_100g')}
                </p>
                <div className="mt-3">
                  <label className="text-sm text-text-secondary font-medium">{t('amount')}</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={e => setAmount(Number(e.target.value))}
                    className="w-full bg-bg-primary rounded-lg px-3 py-2 text-sm text-text-primary outline-none mt-1 border border-border focus:border-accent-green transition-colors"
                  />
                </div>
                <div className="flex gap-2 mt-3 flex-wrap">
                  <span className="px-2 py-1 bg-accent-orange/10 text-accent-orange rounded-full text-sm font-semibold">
                    {Math.round((selectedFood.calories_per_100g || 0) * amount / 100)} {tc('common.kcal')}
                  </span>
                  <span className="px-2 py-1 bg-accent-blue/10 text-accent-blue rounded-full text-sm font-semibold">
                    {t('macro_p')} {Math.round((selectedFood.protein_per_100g || 0) * amount / 100)}{tc('common.g')}
                  </span>
                  <span className="px-2 py-1 bg-accent-green/10 text-accent-green rounded-full text-sm font-semibold">
                    {t('macro_c')} {Math.round((selectedFood.carbs_per_100g || 0) * amount / 100)}{tc('common.g')}
                  </span>
                  <span className="px-2 py-1 bg-accent-red/10 text-accent-red rounded-full text-sm font-semibold">
                    {t('macro_f')} {Math.round((selectedFood.fat_per_100g || 0) * amount / 100)}{tc('common.g')}
                  </span>
                </div>
              </>
            )}
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setSelectedFood(null)}
                className="flex-1 bg-gray-100 py-3 rounded-lg text-base text-text-primary border border-border font-medium min-h-[44px]"
              >
                ←
              </button>
              <button
                onClick={handleAdd}
                className="flex-1 bg-gradient-to-r from-accent-green to-accent-emerald text-white py-3 rounded-lg text-base font-semibold shadow-sm min-h-[44px]"
              >
                {t('add_food')}
              </button>
            </div>
          </div>
        ) : (
          <>
            {!query && recentFoods.length > 0 && (
              <div className="mb-3">
                <h4 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">{t('recent_foods')}</h4>
                <div className="space-y-1">
                  {recentFoods.map((food, i) => {
                    const dotColors = ['bg-accent-green', 'bg-accent-blue', 'bg-accent-orange', 'bg-accent-teal', 'bg-accent-purple']
                    return (
                      <button
                        key={i}
                        onClick={() => setSelectedFood({
                          name_en: food.name,
                          name_ru: food.name,
                          image_url: food.image_url,
                          calories_per_100g: food.calories ? Math.round(food.calories * 100 / (food.amount_g || 100)) : 0,
                          protein_per_100g: food.protein ? Math.round(food.protein * 100 / (food.amount_g || 100)) : 0,
                          carbs_per_100g: food.carbs ? Math.round(food.carbs * 100 / (food.amount_g || 100)) : 0,
                          fat_per_100g: food.fat ? Math.round(food.fat * 100 / (food.amount_g || 100)) : 0,
                        })}
                        className="w-full text-left bg-accent-green/5 rounded-lg p-3 border border-accent-green/20 hover:border-accent-green transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {food.image_url ? (
                            <img src={food.image_url} alt="" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                          ) : (
                            <div className="w-10 h-10 rounded-lg bg-accent-green/10 flex items-center justify-center flex-shrink-0">
                              <span className="text-accent-green text-sm font-bold">
                                {(food.name || '?')[0].toUpperCase()}
                              </span>
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-text-primary">{food.name}</div>
                          </div>
                          <span className="text-sm text-text-secondary flex-shrink-0">{food.count}x</span>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
            <div className="space-y-1">
              {results.map((food, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedFood(food)}
                  className="w-full text-left bg-bg-secondary rounded-lg p-3 border border-border hover:border-accent-green transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {food.image_url ? (
                      <img src={food.image_url} alt="" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-accent-green/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-accent-green text-sm font-bold">
                          {(food.name_en || '?')[0].toUpperCase()}
                        </span>
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-text-primary">
                        {lang === 'ru' ? (food.name_ru || food.name_en) : food.name_en}
                      </div>
                      <div className="text-sm text-text-secondary mt-0.5">
                        {food.calories_per_100g} {tc('common.kcal')} · {t('macro_p')}{food.protein_per_100g}{tc('common.g')} · {t('macro_c')}{food.carbs_per_100g}{tc('common.g')} · {t('macro_f')}{food.fat_per_100g}{tc('common.g')}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
              {results.length === 0 && !loading && query && (
                <p className="text-center text-text-secondary text-sm py-4">{t('empty')}</p>
              )}
            </div>
            <button
              onClick={() => setSelectedFood({
                name_en: query || 'Custom Food',
                name_ru: query || '',
                calories_per_100g: 0,
                protein_per_100g: 0,
                carbs_per_100g: 0,
                fat_per_100g: 0,
                isCustom: true,
              })}
              className="w-full mt-3 border-2 border-dashed border-border rounded-lg p-3 text-sm text-text-secondary hover:border-accent-green hover:text-accent-green transition-colors"
            >
              {'+ ' + t('custom_food')}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
