import { useTranslation } from 'react-i18next'

export default function ExerciseCard({ exercise }) {
  const { i18n, t } = useTranslation('exercises')
  const lang = i18n.language
  const name = lang === 'ru' ? (exercise.name_ru || exercise.name_en) : exercise.name_en

  const typeColors = {
    strength: 'bg-accent-blue/20 text-accent-blue',
    cardio: 'bg-accent-orange/20 text-accent-orange',
    flexibility: 'bg-accent-purple/20 text-accent-purple',
    tai_chi: 'bg-accent-green/20 text-accent-green',
    yoga: 'bg-accent-green/20 text-accent-green',
  }

  return (
    <div className="bg-bg-card rounded-xl p-3 mb-2 border border-border shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-text-primary">{name}</h4>
          <div className="flex gap-2 mt-1 flex-wrap">
            {exercise.type && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${typeColors[exercise.type] || 'bg-gray-100 text-text-secondary'}`}>
                {t(`types.${exercise.type}`, exercise.type)}
              </span>
            )}
            {exercise.sets && exercise.reps && (
              <span className="text-xs text-text-secondary">{exercise.sets}x{exercise.reps}</span>
            )}
            {exercise.duration_mins && (
              <span className="text-xs text-text-secondary">{exercise.duration_mins} {t('duration')}</span>
            )}
          </div>
        </div>
      </div>
      {exercise.instructions && (
        <p className="text-xs text-text-secondary mt-2 leading-relaxed">{exercise.instructions}</p>
      )}
    </div>
  )
}
