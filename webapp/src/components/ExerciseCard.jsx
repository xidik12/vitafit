import { useState } from 'react'
import { useTranslation } from 'react-i18next'

// SVG fallback icons for when images fail to load
const EXERCISE_TYPE_ICONS = {
  strength: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <path d="M6.5 6.5h11M6.5 17.5h11M2 12h4M18 12h4M6 6.5v11M18 6.5v11"/>
    </svg>
  ),
  cardio: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/>
    </svg>
  ),
  flexibility: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <circle cx="12" cy="5" r="3"/><path d="M12 8v4l3 5M12 12l-3 5"/>
    </svg>
  ),
  tai_chi: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 0 20 5 5 0 0 1 0-10 5 5 0 0 0 0-10z"/>
    </svg>
  ),
  yoga: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <circle cx="12" cy="4" r="2.5"/><path d="M12 6.5v5M8 20l4-8.5 4 8.5M6 14h12"/>
    </svg>
  ),
  warm_up: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <path d="M12 2v10l4.5 4.5M12 12L7.5 16.5"/><circle cx="12" cy="12" r="10"/>
    </svg>
  ),
  cool_down: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
      <path d="M12 2L12 22M12 2L8 6M12 2L16 6M5 12H19"/><path d="M8 16l4 4 4-4"/>
    </svg>
  ),
}

const DEFAULT_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
    <circle cx="12" cy="5" r="3"/><path d="M12 8v4l3 5M12 12l-3 5"/>
  </svg>
)

// Fallback background colors per exercise type
const FALLBACK_BG = {
  strength: 'bg-blue-100 text-blue-500',
  cardio: 'bg-orange-100 text-orange-500',
  flexibility: 'bg-purple-100 text-purple-500',
  tai_chi: 'bg-green-100 text-green-500',
  yoga: 'bg-teal-100 text-teal-500',
  warm_up: 'bg-amber-100 text-amber-500',
  cool_down: 'bg-sky-100 text-sky-500',
}

export default function ExerciseCard({ exercise }) {
  const { i18n, t } = useTranslation('exercises')
  const lang = i18n.language
  const name = lang === 'ru' ? (exercise.name_ru || exercise.name_en) : exercise.name_en

  const [expanded, setExpanded] = useState(false)
  const [imgError, setImgError] = useState(false)

  const typeColors = {
    strength: 'bg-accent-blue/15 text-accent-blue border border-accent-blue/25',
    cardio: 'bg-accent-orange/15 text-accent-orange border border-accent-orange/25',
    flexibility: 'bg-accent-purple/15 text-accent-purple border border-accent-purple/25',
    tai_chi: 'bg-accent-green/15 text-accent-green border border-accent-green/25',
    yoga: 'bg-accent-teal/15 text-accent-teal border border-accent-teal/25',
    warm_up: 'bg-amber-100/60 text-amber-600 border border-amber-200',
    cool_down: 'bg-sky-100/60 text-sky-600 border border-sky-200',
  }

  // Difficulty styling
  const difficultyConfig = {
    beginner: { label: lang === 'ru' ? 'Легко' : 'Easy', color: 'bg-green-100 text-green-700 border border-green-200' },
    intermediate: { label: lang === 'ru' ? 'Средне' : 'Moderate', color: 'bg-yellow-100 text-yellow-700 border border-yellow-200' },
    advanced: { label: lang === 'ru' ? 'Сложно' : 'Hard', color: 'bg-red-100 text-red-700 border border-red-200' },
  }

  const difficulty = exercise.difficulty ? difficultyConfig[exercise.difficulty] : null

  // Estimate duration: use duration_mins if available, else estimate from sets*reps
  const durationMins = exercise.duration_mins
    || (exercise.sets && exercise.reps ? Math.max(5, Math.ceil(exercise.sets * exercise.reps * 0.08 * exercise.sets)) : null)

  const hasImage = exercise.images && exercise.images.length > 0 && !imgError
  const hasTips = exercise.form_tips && (
    exercise.form_tips.setup ||
    exercise.form_tips.execution ||
    exercise.form_tips.mistakes ||
    exercise.form_tips.breathing
  )
  const hasExpandable = (exercise.images && exercise.images.length > 0) || hasTips || exercise.video_url

  const fallbackColorClass = FALLBACK_BG[exercise.type] || 'bg-gray-100 text-gray-500'
  const typeIcon = EXERCISE_TYPE_ICONS[exercise.type] || DEFAULT_ICON

  // Image fallback component
  function ImageFallback({ className = '' }) {
    return (
      <div className={`${fallbackColorClass} flex items-center justify-center ${className}`}>
        {typeIcon}
      </div>
    )
  }

  return (
    <div className="bg-bg-card rounded-xl p-3 mb-2 border border-border shadow-sm">
      {/* Card header -- clickable to toggle expanded */}
      <div
        className={`flex items-center justify-between min-h-[48px] ${hasExpandable ? 'cursor-pointer select-none' : ''}`}
        onClick={() => hasExpandable && setExpanded(prev => !prev)}
      >
        <div className="flex-1 min-w-0">
          {/* Exercise name - large and prominent */}
          <h4 className="text-base font-bold text-text-primary leading-snug">{name}</h4>

          {/* Description preview (first sentence, clear and simple) */}
          {exercise.instructions && (
            <p className="text-sm text-text-secondary mt-1 line-clamp-2 leading-relaxed">
              {exercise.instructions.split('.').slice(0, 2).join('.').trim()}{exercise.instructions.includes('.') ? '.' : ''}
            </p>
          )}

          {/* Tags row: type, difficulty, duration, sets x reps */}
          <div className="flex gap-1.5 mt-2 flex-wrap items-center">
            {exercise.type && (
              <span className={`text-sm px-2.5 py-0.5 rounded-full font-semibold ${typeColors[exercise.type] || 'bg-gray-100 text-text-secondary border border-border'}`}>
                {t(`types.${exercise.type}`, exercise.type)}
              </span>
            )}
            {difficulty && (
              <span className={`text-sm px-2.5 py-0.5 rounded-full font-semibold ${difficulty.color}`}>
                {difficulty.label}
              </span>
            )}
            {durationMins && (
              <span className="text-sm font-bold text-accent-blue bg-accent-blue/10 px-2.5 py-0.5 rounded-full">
                {durationMins} {lang === 'ru' ? 'мин' : 'min'}
              </span>
            )}
            {exercise.sets && exercise.reps && (
              <span className="text-sm text-text-primary font-bold bg-bg-secondary px-2.5 py-0.5 rounded-full">
                {exercise.sets}x{exercise.reps}
              </span>
            )}
          </div>
        </div>

        {/* Thumbnail + expand indicator */}
        <div className="flex items-center gap-2 ml-3 flex-shrink-0">
          {exercise.images && exercise.images.length > 0 && (
            hasImage ? (
              <img
                src={exercise.images[0]}
                alt={name}
                className="w-14 h-14 rounded-lg object-cover border border-border"
                onError={() => setImgError(true)}
              />
            ) : (
              <ImageFallback className="w-14 h-14 rounded-lg" />
            )
          )}
          {hasExpandable && (
            <span className="text-text-secondary text-sm">{expanded ? '▲' : '▼'}</span>
          )}
        </div>
      </div>

      {/* Expandable How-to section */}
      {expanded && hasExpandable && (
        <div className="mt-3 border-t border-border pt-3 space-y-3">
          {/* Full-width image or fallback */}
          {exercise.images && exercise.images.length > 0 && (
            hasImage ? (
              <img
                src={exercise.images[0]}
                alt={name}
                className="w-full max-h-40 object-cover rounded-lg border border-border"
                onError={() => setImgError(true)}
              />
            ) : (
              <ImageFallback className="w-full h-32 rounded-lg" />
            )
          )}

          {/* Full instructions */}
          {exercise.instructions && (
            <div className="bg-bg-secondary rounded-lg p-3">
              <p className="text-sm font-semibold text-text-primary mb-1">{t('instructions_label', 'Instructions')}</p>
              <p className="text-base text-text-secondary leading-relaxed">{exercise.instructions}</p>
            </div>
          )}

          {/* Form tips */}
          {hasTips && (
            <div className="space-y-2">
              <p className="text-sm font-semibold text-text-primary">{t('how_to')}</p>
              {exercise.form_tips.setup && (
                <div className="border-l-3 border-l-accent-blue pl-3 py-1.5">
                  <span className="text-sm font-semibold text-accent-blue">{t('setup') + ': '}</span>
                  <span className="text-sm text-text-secondary">{exercise.form_tips.setup}</span>
                </div>
              )}
              {exercise.form_tips.execution && (
                <div className="border-l-3 border-l-accent-green pl-3 py-1.5">
                  <span className="text-sm font-semibold text-accent-green">{t('execution') + ': '}</span>
                  <span className="text-sm text-text-secondary">{exercise.form_tips.execution}</span>
                </div>
              )}
              {exercise.form_tips.mistakes && (
                <div className="border-l-3 border-l-accent-orange pl-3 py-1.5">
                  <span className="text-sm font-semibold text-accent-orange">{t('mistakes') + ': '}</span>
                  <span className="text-sm text-text-secondary">{exercise.form_tips.mistakes}</span>
                </div>
              )}
              {exercise.form_tips.breathing && (
                <div className="border-l-3 border-l-accent-purple pl-3 py-1.5">
                  <span className="text-sm font-semibold text-accent-purple">{t('breathing') + ': '}</span>
                  <span className="text-sm text-text-secondary">{exercise.form_tips.breathing}</span>
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
              className="flex items-center gap-1.5 text-sm text-accent-blue font-semibold bg-accent-blue/10 rounded-lg px-4 py-3 w-fit min-h-[44px]"
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
