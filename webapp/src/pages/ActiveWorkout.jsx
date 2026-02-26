import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import api from '../utils/api'
import { CheckCircleIcon, ClockIcon, DumbbellIcon } from '../components/Icons'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function getDefaultRest(exercise) {
  const type = (exercise?.type || '').toLowerCase()
  if (type.includes('strength')) return 90
  if (type.includes('bodyweight')) return 60
  return 30
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Animated confetti dots — pure CSS, no libraries */
function Confetti() {
  const colors = [
    '#22c55e', '#f59e0b', '#3b82f6', '#a78bfa',
    '#f87171', '#34d399', '#fbbf24', '#60a5fa',
  ]
  const dots = Array.from({ length: 40 }, (_, i) => ({
    id: i,
    color: colors[i % colors.length],
    left: `${Math.random() * 100}%`,
    delay: `${(Math.random() * 1.2).toFixed(2)}s`,
    size: `${6 + Math.floor(Math.random() * 8)}px`,
    duration: `${(1.8 + Math.random() * 1.4).toFixed(2)}s`,
  }))

  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden z-50">
      <style>{`
        @keyframes confetti-fall {
          0%   { transform: translateY(-20px) rotate(0deg); opacity: 1; }
          100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
        }
      `}</style>
      {dots.map(d => (
        <div
          key={d.id}
          style={{
            position: 'absolute',
            top: '-20px',
            left: d.left,
            width: d.size,
            height: d.size,
            borderRadius: Math.random() > 0.5 ? '50%' : '2px',
            backgroundColor: d.color,
            animation: `confetti-fall ${d.duration} ${d.delay} ease-in forwards`,
          }}
        />
      ))}
    </div>
  )
}

/** Circular countdown timer */
function RestCircle({ seconds, total }) {
  const radius = 52
  const circ = 2 * Math.PI * radius
  const progress = total > 0 ? seconds / total : 0
  const offset = circ * (1 - progress)

  return (
    <svg width="140" height="140" className="-rotate-90">
      <circle
        cx="70" cy="70" r={radius}
        fill="none"
        stroke="#e5e7eb"
        strokeWidth="8"
      />
      <circle
        cx="70" cy="70" r={radius}
        fill="none"
        stroke="#22c55e"
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 1s linear' }}
      />
    </svg>
  )
}

/** Single set row inside the exercise view */
function SetRow({ setNum, exercise, isCompleted, onComplete }) {
  const [weight, setWeight] = useState('')
  const [reps, setReps] = useState('')

  function handleComplete() {
    onComplete(setNum, {
      weight: parseFloat(weight) || 0,
      reps: parseInt(reps, 10) || exercise.reps || 0,
    })
  }

  return (
    <div
      className={`flex items-center gap-3 py-2.5 px-3 rounded-xl mb-2 transition-colors ${
        isCompleted
          ? 'bg-accent-green/10 border border-accent-green/30'
          : 'bg-bg-secondary border border-border'
      }`}
    >
      {/* Set badge */}
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
          isCompleted
            ? 'bg-accent-green text-white'
            : 'bg-white text-text-secondary border border-border'
        }`}
      >
        {isCompleted ? (
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M2.5 7.5L5.5 10.5L11.5 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ) : setNum}
      </div>

      {/* Weight input */}
      <div className="flex-1">
        <input
          type="number"
          min="0"
          step="0.5"
          placeholder="kg"
          value={weight}
          onChange={e => setWeight(e.target.value)}
          disabled={isCompleted}
          className={`w-full text-center text-sm font-medium rounded-lg py-1.5 border outline-none transition ${
            isCompleted
              ? 'bg-transparent border-transparent text-text-secondary'
              : 'bg-white border-border text-text-primary focus:border-accent-green'
          }`}
        />
        <p className="text-center text-[10px] text-text-secondary mt-0.5">weight</p>
      </div>

      {/* Reps input */}
      <div className="flex-1">
        <input
          type="number"
          min="0"
          placeholder={exercise.reps ? String(exercise.reps) : 'reps'}
          value={reps}
          onChange={e => setReps(e.target.value)}
          disabled={isCompleted}
          className={`w-full text-center text-sm font-medium rounded-lg py-1.5 border outline-none transition ${
            isCompleted
              ? 'bg-transparent border-transparent text-text-secondary'
              : 'bg-white border-border text-text-primary focus:border-accent-green'
          }`}
        />
        <p className="text-center text-[10px] text-text-secondary mt-0.5">reps</p>
      </div>

      {/* Complete button */}
      <button
        onClick={handleComplete}
        disabled={isCompleted}
        className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 transition-all active:scale-95 ${
          isCompleted
            ? 'bg-accent-green text-white cursor-default'
            : 'bg-accent-green text-white shadow-sm shadow-accent-green/40 hover:bg-accent-dark'
        }`}
      >
        {isCompleted ? (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 8.5L6.5 12L13 5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3.5 8H12.5M12.5 8L8.5 4M12.5 8L8.5 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ActiveWorkout() {
  const { dayIndex: dayIndexParam } = useParams()
  const dayIndex = parseInt(dayIndexParam, 10)
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const { token } = useUser()

  // -- Core state -----------------------------------------------------------
  const [exercises, setExercises] = useState([])
  const [currentExIdx, setCurrentExIdx] = useState(0)
  const [currentSet, setCurrentSet] = useState(1)
  const [completedSets, setCompletedSets] = useState({}) // { exIdx: Set<setNum> }
  const [setLogs, setSetLogs] = useState([])

  // Rest timer
  const [resting, setResting] = useState(false)
  const [restTotal, setRestTotal] = useState(60)
  const [restTime, setRestTime] = useState(60)

  // Session
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [finished, setFinished] = useState(false)
  const [finishData, setFinishData] = useState(null)
  const [error, setError] = useState(null)

  // Elapsed timer
  const [elapsed, setElapsed] = useState(0)

  // Refs to hold interval IDs
  const elapsedRef = useRef(null)
  const restRef = useRef(null)

  // -- On mount: fetch plan + start session --------------------------------
  useEffect(() => {
    if (!token) return
    let cancelled = false

    async function init() {
      setLoading(true)
      try {
        const plan = await api.get('/api/exercises/plan', token)
        if (cancelled) return

        const day = plan?.days?.[dayIndex]
        const exs = day?.exercises || []
        setExercises(exs)

        const session = await api.post('/api/workouts/start', { plan_day_index: dayIndex }, token)
        if (cancelled) return
        setSessionId(session?.session_id || session?.id || null)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load workout')
      }
      if (!cancelled) setLoading(false)
    }

    init()
    return () => { cancelled = true }
  }, [token, dayIndex])

  // -- Elapsed timer --------------------------------------------------------
  useEffect(() => {
    if (loading || finished) return
    elapsedRef.current = setInterval(() => {
      setElapsed(prev => prev + 1)
    }, 1000)
    return () => clearInterval(elapsedRef.current)
  }, [loading, finished])

  // -- Rest countdown -------------------------------------------------------
  useEffect(() => {
    if (!resting) return
    restRef.current = setInterval(() => {
      setRestTime(prev => {
        if (prev <= 1) {
          clearInterval(restRef.current)
          handleRestEnd()
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(restRef.current)
  }, [resting]) // eslint-disable-line react-hooks/exhaustive-deps

  // -- Derived --------------------------------------------------------------
  const currentExercise = exercises[currentExIdx] || null
  const exName =
    i18n.language === 'ru' && currentExercise?.name_ru
      ? currentExercise.name_ru
      : currentExercise?.name_en || currentExercise?.name || 'Exercise'

  const totalSets = currentExercise?.sets || 3
  const completedSetsForCurrent = completedSets[currentExIdx] || new Set()

  // -- Handlers -------------------------------------------------------------

  function handleRestEnd() {
    clearInterval(restRef.current)
    setResting(false)
    if (currentExIdx + 1 < exercises.length) {
      setCurrentExIdx(prev => prev + 1)
      setCurrentSet(1)
    } else {
      finishWorkout()
    }
  }

  function startRest(exercise) {
    clearInterval(restRef.current)
    const duration = getDefaultRest(exercise)
    setRestTotal(duration)
    setRestTime(duration)
    setResting(true)
  }

  function changeRestPreset(secs) {
    clearInterval(restRef.current)
    setRestTotal(secs)
    setRestTime(secs)
    // Restart the countdown with new value
    restRef.current = setInterval(() => {
      setRestTime(prev => {
        if (prev <= 1) {
          clearInterval(restRef.current)
          handleRestEnd()
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const handleCompleteSet = useCallback(async (setNum, { weight, reps: repsLogged }) => {
    // Update local completed sets
    setCompletedSets(prev => {
      const next = { ...prev }
      const existing = next[currentExIdx] ? new Set(next[currentExIdx]) : new Set()
      existing.add(setNum)
      next[currentExIdx] = existing
      return next
    })

    const logEntry = {
      exercise_name: currentExercise?.name_en || currentExercise?.name,
      exercise_index: currentExIdx,
      set_number: setNum,
      weight_kg: weight,
      reps: repsLogged,
    }
    setSetLogs(prev => [...prev, logEntry])

    // Fire API call (best effort)
    if (sessionId) {
      try {
        await api.post(`/api/workouts/${sessionId}/log-set`, logEntry, token)
      } catch {
        // Non-critical — keep going
      }
    }

    // Check if all sets for this exercise are done
    const newDone = (completedSets[currentExIdx]?.size || 0) + 1
    if (newDone >= totalSets) {
      // All sets complete — rest then next exercise
      startRest(currentExercise)
    } else {
      setCurrentSet(setNum + 1)
    }
  }, [currentExIdx, currentExercise, completedSets, totalSets, sessionId, token]) // eslint-disable-line react-hooks/exhaustive-deps

  async function finishWorkout() {
    clearInterval(elapsedRef.current)
    clearInterval(restRef.current)
    setResting(false)

    let result = null
    if (sessionId) {
      try {
        result = await api.post(`/api/workouts/${sessionId}/finish`, { duration_seconds: elapsed }, token)
      } catch {
        // Use fallback data
      }
    }

    setFinishData(result)
    setFinished(true)
  }

  async function handleEarlyExit() {
    const confirmed = window.confirm('End workout early? Your progress so far will be saved.')
    if (!confirmed) return
    await finishWorkout()
  }

  // -- Loading --------------------------------------------------------------
  if (loading) {
    return (
      <div className="fixed inset-0 bg-bg-primary flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
        <p className="text-text-secondary text-sm">Loading workout...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-bg-primary flex flex-col items-center justify-center gap-4 p-6">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="text-accent-red">
          <path d="M24 6L44 42H4L24 6Z" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" fill="none"/>
          <path d="M24 20V30" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
          <circle cx="24" cy="36" r="1.5" fill="currentColor"/>
        </svg>
        <p className="text-accent-red text-sm text-center">{error}</p>
        <button
          onClick={() => navigate('/exercises')}
          className="mt-2 bg-accent-green text-white px-6 py-2.5 rounded-xl text-sm font-semibold"
        >
          Back to Plan
        </button>
      </div>
    )
  }

  // -- Completion screen ----------------------------------------------------
  if (finished) {
    const totalSetsCompleted = setLogs.length
    const xp = finishData?.xp_earned ?? finishData?.xp ?? 0
    const calories = finishData?.calories_burned ?? finishData?.calories ?? 0
    const duration = finishData?.duration_seconds ?? elapsed

    return (
      <>
        <Confetti />
        <div className="fixed inset-0 bg-bg-primary flex flex-col items-center justify-center p-6 z-40">
          {/* Big checkmark */}
          <div className="w-24 h-24 rounded-full bg-accent-green/15 border-4 border-accent-green flex items-center justify-center mb-6 shadow-lg shadow-accent-green/20">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <path
                d="M10 26L20 36L38 14"
                stroke="#22c55e"
                strokeWidth="4.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-text-primary mb-1">Workout Complete!</h1>
          <p className="text-text-secondary text-sm mb-8">Great job — you crushed it today!</p>

          {/* Stats grid */}
          <div className="w-full max-w-xs grid grid-cols-2 gap-3 mb-8">
            <div className="bg-white rounded-2xl p-4 border border-border shadow-sm text-center">
              <p className="text-2xl font-bold text-text-primary">{formatTime(duration)}</p>
              <p className="text-xs text-text-secondary mt-1">Duration</p>
            </div>
            <div className="bg-white rounded-2xl p-4 border border-border shadow-sm text-center">
              <p className="text-2xl font-bold text-text-primary">{totalSetsCompleted}</p>
              <p className="text-xs text-text-secondary mt-1">Sets done</p>
            </div>
            {xp > 0 && (
              <div className="bg-accent-purple/10 rounded-2xl p-4 border border-accent-purple/30 shadow-sm text-center">
                <p className="text-2xl font-bold text-accent-purple">+{xp}</p>
                <p className="text-xs text-text-secondary mt-1">XP earned</p>
              </div>
            )}
            {calories > 0 && (
              <div className="bg-accent-orange/10 rounded-2xl p-4 border border-accent-orange/30 shadow-sm text-center">
                <p className="text-2xl font-bold text-accent-orange">{calories}</p>
                <p className="text-xs text-text-secondary mt-1">kcal burned</p>
              </div>
            )}
          </div>

          <button
            onClick={() => navigate('/exercises')}
            className="w-full max-w-xs bg-accent-green text-white font-bold py-3.5 rounded-2xl text-base shadow-md shadow-accent-green/30 active:scale-95 transition-transform"
          >
            Back to Plan
          </button>
        </div>
      </>
    )
  }

  // -- Rest overlay ---------------------------------------------------------
  if (resting) {
    const presets = [30, 60, 90, 120]

    return (
      <div className="fixed inset-0 bg-bg-primary flex flex-col items-center justify-center p-6 z-40">
        <p className="text-text-secondary text-sm uppercase tracking-widest font-semibold mb-2">Rest</p>
        <h2 className="text-text-primary text-lg font-bold mb-6">
          Next: {exercises[currentExIdx + 1]
            ? (i18n.language === 'ru' && exercises[currentExIdx + 1].name_ru
              ? exercises[currentExIdx + 1].name_ru
              : exercises[currentExIdx + 1].name_en || exercises[currentExIdx + 1].name)
            : 'Finish'}
        </h2>

        {/* Circular timer */}
        <div className="relative flex items-center justify-center mb-6">
          <RestCircle seconds={restTime} total={restTotal} />
          <div className="absolute flex flex-col items-center">
            <span className="text-4xl font-bold text-text-primary">{restTime}</span>
            <span className="text-xs text-text-secondary">sec</span>
          </div>
        </div>

        {/* Preset buttons */}
        <div className="flex gap-2 mb-8">
          {presets.map(p => (
            <button
              key={p}
              onClick={() => changeRestPreset(p)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                restTotal === p
                  ? 'bg-accent-green text-white border-accent-green'
                  : 'bg-white text-text-secondary border-border hover:border-accent-green/50'
              }`}
            >
              {p}s
            </button>
          ))}
        </div>

        {/* Skip */}
        <button
          onClick={handleRestEnd}
          className="text-accent-green font-semibold text-sm border border-accent-green/40 px-6 py-2.5 rounded-xl hover:bg-accent-green/10 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            Skip Rest
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2.5 7H11.5M11.5 7L7.5 3M11.5 7L7.5 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
        </button>
      </div>
    )
  }

  // -- No exercises guard ----------------------------------------------------
  if (exercises.length === 0) {
    return (
      <div className="fixed inset-0 bg-bg-primary flex flex-col items-center justify-center gap-4 p-6">
        <DumbbellIcon className="w-12 h-12 text-text-secondary" />
        <p className="text-text-secondary text-sm text-center">This is a rest day — no exercises scheduled.</p>
        <button
          onClick={() => navigate('/exercises')}
          className="bg-accent-green text-white px-6 py-2.5 rounded-xl text-sm font-semibold"
        >
          Back to Plan
        </button>
      </div>
    )
  }

  // -- Main workout UI ------------------------------------------------------
  return (
    <div className="fixed inset-0 bg-bg-primary flex flex-col overflow-hidden">

      {/* -- Top bar ------------------------------------------------------- */}
      <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-border bg-white flex-shrink-0">
        {/* Back / quit */}
        <button
          onClick={handleEarlyExit}
          className="w-9 h-9 flex items-center justify-center text-text-secondary rounded-xl hover:bg-bg-secondary transition-colors"
          aria-label="End workout"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M12 4L6 10L12 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        {/* Exercise counter */}
        <div className="flex items-center gap-1.5">
          {exercises.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all ${
                i < currentExIdx
                  ? 'w-4 bg-accent-green'
                  : i === currentExIdx
                  ? 'w-5 bg-accent-green'
                  : 'w-4 bg-border'
              }`}
            />
          ))}
        </div>

        {/* Elapsed time */}
        <div className="flex items-center gap-1 text-text-secondary text-sm font-mono">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-accent-green">
            <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M7 4.5V7L8.5 8.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          {formatTime(elapsed)}
        </div>
      </div>

      {/* -- Scrollable body ------------------------------------------------ */}
      <div className="flex-1 overflow-y-auto p-4 pb-6">

        {/* Exercise header */}
        <div className="flex gap-3 mb-4">
          {/* Optional image thumbnail */}
          {currentExercise?.images?.[0] && (
            <div className="w-16 h-16 rounded-xl overflow-hidden border border-border flex-shrink-0 bg-bg-secondary">
              <img
                src={currentExercise.images[0]}
                alt={exName}
                className="w-full h-full object-cover"
                onError={e => { e.currentTarget.style.display = 'none' }}
              />
            </div>
          )}

          <div className="flex-1 min-w-0">
            {/* Counter label */}
            <p className="text-xs font-semibold text-accent-green uppercase tracking-wide mb-0.5">
              Exercise {currentExIdx + 1} of {exercises.length}
            </p>
            {/* Exercise name */}
            <h1 className="text-xl font-bold text-text-primary leading-tight truncate">
              {exName}
            </h1>
            {/* Details row */}
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {currentExercise?.sets && (
                <span className="text-xs bg-accent-green/10 text-accent-green border border-accent-green/20 px-2 py-0.5 rounded-md font-medium">
                  {currentExercise.sets} sets
                </span>
              )}
              {currentExercise?.reps && (
                <span className="text-xs bg-bg-secondary text-text-secondary border border-border px-2 py-0.5 rounded-md font-medium">
                  {currentExercise.reps} reps
                </span>
              )}
              {currentExercise?.duration_mins && (
                <span className="text-xs bg-accent-blue/10 text-accent-blue border border-accent-blue/20 px-2 py-0.5 rounded-md font-medium">
                  {currentExercise.duration_mins} min
                </span>
              )}
              {currentExercise?.type && (
                <span className="text-xs bg-bg-secondary text-text-secondary border border-border px-2 py-0.5 rounded-md capitalize">
                  {currentExercise.type}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Instructions (collapsible hint) */}
        {currentExercise?.instructions && (
          <details className="mb-4 bg-bg-secondary rounded-xl border border-border">
            <summary className="px-3 py-2.5 text-xs text-text-secondary cursor-pointer font-medium select-none">
              Instructions
            </summary>
            <p className="px-3 pb-3 text-sm text-text-secondary leading-relaxed">
              {currentExercise.instructions}
            </p>
          </details>
        )}

        {/* Divider */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-text-secondary font-semibold uppercase tracking-wide">Sets</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Sets checklist */}
        <div>
          {Array.from({ length: totalSets }, (_, i) => {
            const setNum = i + 1
            const isDone = completedSetsForCurrent.has(setNum)
            return (
              <SetRow
                key={`${currentExIdx}-${setNum}`}
                setNum={setNum}
                exercise={currentExercise}
                isCompleted={isDone}
                onComplete={handleCompleteSet}
              />
            )
          })}
        </div>

        {/* Skip exercise button */}
        <button
          onClick={() => startRest(currentExercise)}
          className="mt-4 w-full text-text-secondary text-xs border border-dashed border-border py-2.5 rounded-xl hover:border-accent-green/40 hover:text-accent-green transition-colors"
        >
          <span className="flex items-center justify-center gap-1.5">
            Skip this exercise
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2.5 7H11.5M11.5 7L7.5 3M11.5 7L7.5 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
        </button>

        {/* Upcoming exercises preview */}
        {currentExIdx + 1 < exercises.length && (
          <div className="mt-6">
            <p className="text-xs text-text-secondary uppercase tracking-wide font-semibold mb-2">Up next</p>
            <div className="space-y-1.5">
              {exercises.slice(currentExIdx + 1, currentExIdx + 4).map((ex, i) => {
                const name = i18n.language === 'ru' && ex.name_ru ? ex.name_ru : (ex.name_en || ex.name || 'Exercise')
                return (
                  <div key={i} className="flex items-center gap-3 p-2.5 bg-white rounded-xl border border-border">
                    <div className="w-6 h-6 rounded-full bg-border flex items-center justify-center text-xs text-text-secondary font-bold flex-shrink-0">
                      {currentExIdx + i + 2}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-text-primary truncate">{name}</p>
                      <p className="text-xs text-text-secondary">
                        {ex.sets && ex.reps ? `${ex.sets}×${ex.reps}` : ex.duration_mins ? `${ex.duration_mins} min` : ''}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* -- Bottom action bar ---------------------------------------------- */}
      <div className="flex-shrink-0 px-4 py-3 border-t border-border bg-white">
        <button
          onClick={() => startRest(currentExercise)}
          className="w-full bg-accent-green text-white font-bold py-3.5 rounded-2xl text-base shadow-md shadow-accent-green/25 active:scale-95 transition-transform"
        >
          {currentExIdx + 1 < exercises.length ? (
            <span className="flex items-center justify-center gap-2">
              Next Exercise
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M3.5 9H14.5M14.5 9L9.5 4M14.5 9L9.5 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              Finish Workout
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M3.5 9.5L7 13L14.5 5.5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
          )}
        </button>
      </div>
    </div>
  )
}
