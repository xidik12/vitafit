import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useUser } from '../contexts/UserContext'
import api from '../utils/api'

const TOTAL_STEPS = 7

// Step indices
const STEP_CONSENT = 0
const STEP_PARQ = 1
const STEP_GOALS = 2
const STEP_METRICS = 3
const STEP_DIET = 4
const STEP_SLEEP = 5
const STEP_LIFESTYLE = 6

const PARQ_QUESTIONS = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7']

const GOAL_OPTIONS = ['weight_loss', 'muscle', 'flexibility', 'health', 'stress_relief']

const DIET_OPTIONS = ['no_restriction', 'halal', 'vegetarian', 'vegan', 'gluten_free', 'dairy_free']

const ACTIVITY_LEVELS = ['sedentary', 'light', 'moderate', 'active', 'very_active']

function StepProgress({ step }) {
  return (
    <div className="flex gap-1 mb-6">
      {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
        <div
          key={i}
          className={`flex-1 h-1 rounded-full transition-all duration-300 ${i <= step ? 'bg-accent-green' : 'bg-gray-200'}`}
        />
      ))}
    </div>
  )
}

export default function Questionnaire() {
  const { t } = useTranslation('questionnaire')
  const { t: tc } = useTranslation()
  const { token, setProfile } = useUser()
  const navigate = useNavigate()

  const [step, setStep] = useState(STEP_CONSENT)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // Form state
  const [consent, setConsent] = useState(false)
  const [parq, setParq] = useState({})
  const [goal, setGoal] = useState('')
  const [metrics, setMetrics] = useState({ age: '', gender: '', height_cm: '', weight_kg: '', target_weight_kg: '' })
  const [diet, setDiet] = useState('no_restriction')
  const [sleep, setSleep] = useState({ sleep_hours: 7, sleep_quality: 'good' })
  const [lifestyle, setLifestyle] = useState({ activity_level: 'moderate', stress_level: 'moderate', work_type: 'sedentary' })

  const parqWarning = Object.values(parq).some(v => v === 'yes')

  function next() {
    setError(null)
    if (step === STEP_CONSENT && !consent) {
      setError(t('consent'))
      return
    }
    if (step === STEP_GOALS && !goal) {
      setError(t('errors.select_goal'))
      return
    }
    if (step === STEP_METRICS) {
      const { age, height_cm, weight_kg } = metrics
      if (!age || !height_cm || !weight_kg) {
        setError(t('errors.fill_required'))
        return
      }
    }
    if (step < TOTAL_STEPS - 1) {
      setStep(s => s + 1)
    } else {
      handleSubmit()
    }
  }

  function back() {
    if (step > 0) setStep(s => s - 1)
  }

  async function handleSubmit() {
    if (!token) return
    setSubmitting(true)
    setError(null)
    const payload = {
      consent: consent,
      parq: parq,
      goal,
      age: Number(metrics.age),
      gender: metrics.gender,
      height_cm: Number(metrics.height_cm),
      weight_kg: Number(metrics.weight_kg),
      target_weight_kg: metrics.target_weight_kg ? Number(metrics.target_weight_kg) : null,
      diet_preference: diet,
      sleep_hours: sleep.sleep_hours,
      sleep_quality: sleep.sleep_quality,
      activity_level: lifestyle.activity_level,
      stress_level: lifestyle.stress_level,
      work_type: lifestyle.work_type,
    }
    try {
      const res = await api.post('/api/questionnaire/answers', payload, token)
      if (res?.profile) {
        setProfile(prev => ({ ...prev, ...res.profile }))
      }
      navigate('/')
    } catch (err) {
      setError(err.message || 'Submission failed')
    }
    setSubmitting(false)
  }

  return (
    <div className="p-4 min-h-screen">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-xl font-bold text-text-primary">{t('title')}</h1>
          <p className="text-text-secondary text-sm">{t('subtitle')}</p>
        </div>

        <StepProgress step={step} />

        {/* Step 0: Consent */}
        {step === STEP_CONSENT && (
          <div>
            {/* Privacy statement */}
            <div className="bg-accent-green/10 border border-accent-green/20 rounded-xl p-3 mb-4 flex items-start gap-2">
              <span className="text-accent-green text-lg mt-0.5">🔒</span>
              <p className="text-sm text-accent-dark leading-relaxed">
                {t('privacy')}
              </p>
            </div>

            <h2 className="text-lg font-semibold text-text-primary mb-4">
              ⚕️ {t('modules.parq')}
            </h2>
            <p className="text-text-secondary text-sm leading-relaxed mb-6">
              {t('consent')}
            </p>
            <label className="flex items-start gap-3 bg-white rounded-xl p-4 cursor-pointer border border-border shadow-sm">
              <input
                type="checkbox"
                checked={consent}
                onChange={e => setConsent(e.target.checked)}
                className="mt-0.5 w-5 h-5 accent-accent-green"
              />
              <span className="text-sm text-text-primary">{t('consent')}</span>
            </label>
          </div>
        )}

        {/* Step 1: PAR-Q */}
        {step === STEP_PARQ && (
          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-1">
              {t('parq.title')}
            </h2>
            <p className="text-sm text-text-secondary mb-4">
              {t('subtitle')}
            </p>
            {parqWarning && (
              <div className="bg-accent-orange/10 border border-accent-orange/30 rounded-xl p-3 mb-4">
                <p className="text-accent-orange text-sm">{t('parq.warning')}</p>
              </div>
            )}
            <div className="space-y-3">
              {PARQ_QUESTIONS.map(qKey => (
                <div key={qKey} className="bg-white rounded-xl p-3 border border-border shadow-sm">
                  <p className="text-sm text-text-primary mb-2">{t(`parq.${qKey}`)}</p>
                  <div className="flex gap-2">
                    {['yes', 'no'].map(val => (
                      <button
                        key={val}
                        onClick={() => setParq(prev => ({ ...prev, [qKey]: val }))}
                        className={`flex-1 py-2.5 rounded-lg text-base font-medium border transition-colors min-h-[44px] ${
                          parq[qKey] === val
                            ? val === 'yes'
                              ? 'bg-accent-orange/20 border-accent-orange text-accent-orange'
                              : 'bg-accent-green/20 border-accent-green text-accent-green'
                            : 'bg-transparent border-border text-text-secondary'
                        }`}
                      >
                        {tc(`common.${val}`)}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Goals */}
        {step === STEP_GOALS && (
          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-4">
              🎯 {t('goals.title')}
            </h2>
            <div className="space-y-2">
              {GOAL_OPTIONS.map(g => (
                <button
                  key={g}
                  onClick={() => setGoal(g)}
                  className={`w-full text-left px-4 py-3 rounded-xl border text-sm font-medium transition-colors ${
                    goal === g
                      ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                      : 'bg-white border-border text-text-primary shadow-sm'
                  }`}
                >
                  {t(`goals.${g}`)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Body Metrics */}
        {step === STEP_METRICS && (
          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-4">
              📏 {t('modules.fitness')}
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-text-secondary mb-1 block">{t('body.age')} *</label>
                <input
                  type="number"
                  value={metrics.age}
                  onChange={e => setMetrics(m => ({ ...m, age: e.target.value }))}
                  placeholder="50"
                  className="w-full bg-white rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
                />
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-1 block">{t('body.gender')}</label>
                <div className="flex gap-2">
                  {['male', 'female', 'other'].map(g => (
                    <button
                      key={g}
                      onClick={() => setMetrics(m => ({ ...m, gender: g }))}
                      className={`flex-1 py-2.5 rounded-xl text-sm border transition-colors min-h-[44px] ${
                        metrics.gender === g
                          ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                          : 'bg-white border-border text-text-secondary'
                      }`}
                    >
                      {t(`body.${g}`)}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-1 block">{t('body.height')} *</label>
                <input
                  type="number"
                  value={metrics.height_cm}
                  onChange={e => setMetrics(m => ({ ...m, height_cm: e.target.value }))}
                  placeholder="170"
                  className="w-full bg-white rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
                />
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-1 block">{t('body.weight')} *</label>
                <input
                  type="number"
                  step="0.1"
                  value={metrics.weight_kg}
                  onChange={e => setMetrics(m => ({ ...m, weight_kg: e.target.value }))}
                  placeholder="70"
                  className="w-full bg-white rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
                />
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-1 block">{t('body.target_weight')}</label>
                <input
                  type="number"
                  step="0.1"
                  value={metrics.target_weight_kg}
                  onChange={e => setMetrics(m => ({ ...m, target_weight_kg: e.target.value }))}
                  placeholder="65 (optional)"
                  className="w-full bg-white rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none border border-border focus:border-accent-green"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Diet */}
        {step === STEP_DIET && (
          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-4">
              🥗 {t('modules.diet')}
            </h2>
            <div className="space-y-2">
              {DIET_OPTIONS.map(d => (
                <button
                  key={d}
                  onClick={() => setDiet(d)}
                  className={`w-full text-left px-4 py-3 rounded-xl border text-sm font-medium transition-colors ${
                    diet === d
                      ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                      : 'bg-white border-border text-text-primary shadow-sm'
                  }`}
                >
                  {t(`diet_options.${d}`, d.replace(/_/g, ' '))}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 5: Sleep */}
        {step === STEP_SLEEP && (
          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-4">
              😴 {t('modules.sleep')}
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-text-secondary mb-2 block">
                  {t('sleep_labels.hours')}: <span className="text-accent-green font-semibold">{sleep.sleep_hours}h</span>
                </label>
                <input
                  type="range"
                  min="4"
                  max="12"
                  step="0.5"
                  value={sleep.sleep_hours}
                  onChange={e => setSleep(s => ({ ...s, sleep_hours: Number(e.target.value) }))}
                  className="w-full accent-accent-green"
                />
                <div className="flex justify-between text-sm text-text-secondary mt-1">
                  <span>4h</span>
                  <span>12h</span>
                </div>
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-2 block">{t('sleep_labels.quality')}</label>
                <div className="flex gap-2">
                  {['poor', 'fair', 'good', 'excellent'].map(q => (
                    <button
                      key={q}
                      onClick={() => setSleep(s => ({ ...s, sleep_quality: q }))}
                      className={`flex-1 py-2.5 rounded-xl text-sm border transition-colors min-h-[44px] ${
                        sleep.sleep_quality === q
                          ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                          : 'bg-white border-border text-text-secondary'
                      }`}
                    >
                      {t(`sleep_labels.${q}`, q)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 6: Lifestyle */}
        {step === STEP_LIFESTYLE && (
          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-4">
              🏃 {t('modules.lifestyle')}
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-text-secondary mb-2 block">{t('lifestyle_labels.activity')}</label>
                <div className="space-y-2">
                  {ACTIVITY_LEVELS.map(level => (
                    <button
                      key={level}
                      onClick={() => setLifestyle(l => ({ ...l, activity_level: level }))}
                      className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-colors min-h-[44px] ${
                        lifestyle.activity_level === level
                          ? 'bg-accent-green/20 border-accent-green text-accent-dark'
                          : 'bg-white border-border text-text-primary'
                      }`}
                    >
                      {t(`lifestyle_labels.${level}`, level.replace(/_/g, ' '))}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-2 block">{t('lifestyle_labels.stress')}</label>
                <div className="flex gap-2">
                  {['low', 'moderate', 'high'].map(lvl => (
                    <button
                      key={lvl}
                      onClick={() => setLifestyle(l => ({ ...l, stress_level: lvl }))}
                      className={`flex-1 py-2.5 rounded-xl text-sm border transition-colors min-h-[44px] ${
                        lifestyle.stress_level === lvl
                          ? 'bg-accent-orange/20 border-accent-orange text-accent-orange'
                          : 'bg-white border-border text-text-secondary'
                      }`}
                    >
                      {t(`lifestyle_labels.${lvl}`, lvl)}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-2 block">{t('lifestyle_labels.work_type')}</label>
                <div className="flex gap-2">
                  {['sedentary', 'standing', 'physical'].map(wt => (
                    <button
                      key={wt}
                      onClick={() => setLifestyle(l => ({ ...l, work_type: wt }))}
                      className={`flex-1 py-2.5 rounded-xl text-sm border transition-colors min-h-[44px] ${
                        lifestyle.work_type === wt
                          ? 'bg-accent-blue/20 border-accent-blue text-accent-blue'
                          : 'bg-white border-border text-text-secondary'
                      }`}
                    >
                      {t(`lifestyle_labels.${wt}`, wt)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 bg-accent-red/10 border border-accent-red/30 rounded-xl p-3">
            <p className="text-accent-red text-sm">{error}</p>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex gap-2 mt-6">
          {step > 0 && (
            <button
              onClick={back}
              className="flex-1 bg-gray-100 py-3.5 rounded-xl text-base font-medium text-text-primary border border-border min-h-[48px]"
            >
              {tc('common.back')}
            </button>
          )}
          <button
            onClick={next}
            disabled={submitting}
            className="flex-1 bg-accent-green text-white py-3.5 rounded-xl text-base font-semibold disabled:opacity-50 min-h-[48px]"
          >
            {submitting
              ? tc('common.loading')
              : step === TOTAL_STEPS - 1
              ? tc('common.done')
              : tc('common.next')}
          </button>
        </div>
      </div>
    </div>
  )
}
