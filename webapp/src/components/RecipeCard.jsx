import { useTranslation } from 'react-i18next'
import { UtensilsIcon } from './Icons'

export default function RecipeCard({ recipe, onClick }) {
  const { i18n, t } = useTranslation('meals')
  const lang = i18n.language
  const title = lang === 'ru' ? (recipe.title_ru || recipe.title_en) : recipe.title_en

  return (
    <div className="bg-bg-card rounded-xl overflow-hidden mb-3 cursor-pointer border border-border shadow-sm hover:shadow-md transition-shadow" onClick={onClick}>
      <div className="relative">
        {recipe.image_url ? (
          <>
            <img src={recipe.image_url} alt={title} className="w-full h-32 object-cover" loading="lazy" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
          </>
        ) : (
          <div className="w-full h-32 bg-gradient-to-br from-accent-orange/20 via-accent-amber/10 to-accent-green/20 flex items-center justify-center">
            <UtensilsIcon className="w-10 h-10 text-text-secondary" />
          </div>
        )}
      </div>
      <div className="p-3">
        <h4 className="text-sm font-semibold text-text-primary">{title}</h4>
        <div className="flex gap-3 mt-2 text-xs text-text-secondary">
          {recipe.calories != null && <span className="font-medium">{Math.round(recipe.calories)} {t('common:common.kcal')}</span>}
          {recipe.cook_time_mins && <span>{t('cook_time', { mins: recipe.cook_time_mins })}</span>}
        </div>
        {(recipe.protein != null || recipe.carbs != null || recipe.fat != null) && (
          <div className="flex gap-2 mt-2">
            {recipe.protein != null && (
              <span className="px-2 py-0.5 bg-accent-blue/10 text-accent-blue rounded-full text-xs font-semibold">
                P: {Math.round(recipe.protein)}g
              </span>
            )}
            {recipe.carbs != null && (
              <span className="px-2 py-0.5 bg-accent-green/10 text-accent-green rounded-full text-xs font-semibold">
                C: {Math.round(recipe.carbs)}g
              </span>
            )}
            {recipe.fat != null && (
              <span className="px-2 py-0.5 bg-accent-red/10 text-accent-red rounded-full text-xs font-semibold">
                F: {Math.round(recipe.fat)}g
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
