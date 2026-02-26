import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export default function ExerciseCard({ exercise }) {
  const { i18n, t } = useTranslation('exercises')
  const lang = i18n.language
  const name = lang === 'ru' ? (exercise.name_ru || exercise.name_en) : exercise.name_en

  const [expanded, setExpanded] = useState(false)

  const typeColors = {
    strength: 'bg-accent-blue/15 text-accent-blue border border-accent-blue/25',
    cardio: 'bg-accent-orange/15 text-accent-orange border border-accent-orange/25',
    flexibility: 'bg-accent-purple/15 text-accent-purple border border-accent-purple/25',
    tai_chi: 'bg-accent-green/15 text-accent-green border border-accent-green/25',
    yoga: 'bg-accent-teal/15 text-accent-teal border border-accent-teal/25',
  }

  const hasImage = exercise.images && exercise.images.length > 0
  const hasTips = exercise.form_tips && (
    exercise.form_tips.setup ||
    exercise.form_tips.execution ||
    exercise.form_tips.mistakes ||
    exercise.form_tips.breathing
  )
  const hasExpandable = hasImage || hasTips || exercise.video_url

  return (
    <div className="bg-bg-card rounded-xl p-3 mb-2 border border-border shadow-sm">
      {/* Card header — clickable to toggle expanded */}
      <div
        className={`flex items-center justify-between ${hasExpandable ? 'cursor-pointer select-none' : ''}`}
        onClick={() => hasExpandable && setExpanded(prev => !prev)}
      >
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-text-primary">{name}</h4>
          <div className="flex gap-2 mt-1.5 flex-wrap">
            {exercise.type && (
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${typeColors[exercise.type] || 'bg-gray-100 text-text-secondary border border-border'}`}>
                {t(`types.${exercise.type}`, exercise.type)}
              </span>
            )}
            {exercise.sets && exercise.reps && (
              <span className="text-xs text-text-primary font-bold bg-bg-secondary px-2 py-0.5 rounded-full">{exercise.sets}x{exercise.reps}</span>
            )}
            {exercise.duration_mins && (
              <span className="text-xs text-text-secondary bg-bg-secondary px-2 py-0.5 rounded-full">{exercise.duration_mins} {t('duration')}</span>
            )}
          </div>
        </div>

        {/* Thumbnail + expand indicator */}
        <div className="flex items-center gap-2 ml-2 flex-shrink-0">
          {hasImage && (
            <img
              src={exercise.images[0]}
              alt={name}
              className="w-12 h-12 rounded-lg object-cover border border-border"
            />
          )}
          {hasExpandable && (
            <span className="text-text-secondary text-xs">{expanded ? '▲' : '▼'}</span>
          )}
        </div>
      </div>

      {/* Static instructions */}
      {exercise.instructions && (
        <p className="text-xs text-text-secondary mt-2 leading-relaxed">{exercise.instructions}</p>
      )}

      {/* Expandable How-to section */}
      {expanded && hasExpandable && (
        <div className="mt-3 border-t border-border pt-3 space-y-3">
          {/* Full-width image */}
          {hasImage && (
            <img
              src={exercise.images[0]}
              alt={name}
              className="w-full max-h-32 object-cover rounded-lg border border-border"
            />
          )}

          {/* Form tips */}
          {hasTips && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-text-primary">{t('how_to')}</p>
              {exercise.form_tips.setup && (
                <div className="border-l-3 border-l-accent-blue pl-3 py-1">
                  <span className="text-xs font-semibold text-accent-blue">{t('setup') + ': '}</span>
                  <span className="text-xs text-text-secondary">{exercise.form_tips.setup}</span>
                </div>
              )}
              {exercise.form_tips.execution && (
                <div className="border-l-3 border-l-accent-green pl-3 py-1">
                  <span className="text-xs font-semibold text-accent-green">{t('execution') + ': '}</span>
                  <span className="text-xs text-text-secondary">{exercise.form_tips.execution}</span>
                </div>
              )}
              {exercise.form_tips.mistakes && (
                <div className="border-l-3 border-l-accent-orange pl-3 py-1">
                  <span className="text-xs font-semibold text-accent-orange">{t('mistakes') + ': '}</span>
                  <span className="text-xs text-text-secondary">{exercise.form_tips.mistakes}</span>
                </div>
              )}
              {exercise.form_tips.breathing && (
                <div className="border-l-3 border-l-accent-purple pl-3 py-1">
                  <span className="text-xs font-semibold text-accent-purple">{t('breathing') + ': '}</span>
                  <span className="text-xs text-text-secondary">{exercise.form_tips.breathing}</span>
                </div>
              )}
            </div>
          )}

          {/* Video link */}
          {exercise.video_url && (
            <a
              href={exercise.video_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              className="flex items-center gap-1.5 text-xs text-accent-blue font-semibold bg-accent-blue/10 rounded-lg px-3 py-2 w-fit"
            >
              <span>▶</span>
              <span>{t('watch_video')}</span>
            </a>
          )}
        </div>
      )}
    </div>
  )
}
