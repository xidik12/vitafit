import { useTranslation } from 'react-i18next'

export default function RecipeCard({ recipe, onClick }) {
  const { i18n, t } = useTranslation('meals')
  const lang = i18n.language
  const title = lang === 'ru' ? (recipe.title_ru || recipe.title_en) : recipe.title_en

  return (
    <div className="bg-bg-card rounded-xl overflow-hidden mb-3 cursor-pointer border border-border shadow-sm" onClick={onClick}>
      {recipe.image_url && (
        <img src={recipe.image_url} alt={title} className="w-full h-32 object-cover" loading="lazy" />
      )}
      <div className="p-3">
        <h4 className="text-sm font-medium text-text-primary">{title}</h4>
        <div className="flex gap-3 mt-2 text-xs text-text-secondary">
          {recipe.calories != null && <span>{Math.round(recipe.calories)} {t('common:common.kcal')}</span>}
          {recipe.cook_time_mins && <span>{t('cook_time', { mins: recipe.cook_time_mins })}</span>}
        </div>
        {(recipe.protein != null || recipe.carbs != null || recipe.fat != null) && (
          <div className="flex gap-3 mt-1 text-xs">
            {recipe.protein != null && (
              <span className="text-accent-blue">{t('common:common.protein')}: {Math.round(recipe.protein)}g</span>
            )}
            {recipe.carbs != null && (
              <span className="text-accent-orange">{t('common:common.carbs')}: {Math.round(recipe.carbs)}g</span>
            )}
            {recipe.fat != null && (
              <span className="text-accent-red">{t('common:common.fat')}: {Math.round(recipe.fat)}g</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
