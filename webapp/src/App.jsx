import { Component, lazy, Suspense, useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { useTelegram } from './hooks/useTelegram'
import { UserProvider } from './contexts/UserContext'
import NavBar from './components/NavBar'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Questionnaire = lazy(() => import('./pages/Questionnaire'))
const ExercisePlan = lazy(() => import('./pages/ExercisePlan'))
const MealPlan = lazy(() => import('./pages/MealPlan'))
const CalorieTracker = lazy(() => import('./pages/CalorieTracker'))
const Progress = lazy(() => import('./pages/Progress'))
const Settings = lazy(() => import('./pages/Settings'))
const About = lazy(() => import('./pages/About'))

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, color: 'white', fontFamily: 'monospace' }}>
          <h2 style={{ color: '#f87171' }}>Something went wrong</h2>
          <pre style={{ fontSize: 12, color: '#aaa', whiteSpace: 'pre-wrap' }}>
            {this.state.error?.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{ marginTop: 16, padding: '8px 16px', background: '#60a5fa', border: 'none', borderRadius: 6, color: 'white', cursor: 'pointer' }}
          >
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

export default function App() {
  const location = useLocation()
  return (
    <ErrorBoundary>
      <UserProvider>
        <ScrollToTop />
        <div className="min-h-screen bg-bg-primary text-text-primary pb-20">
          <div key={location.pathname} className="page-enter">
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/questionnaire" element={<Questionnaire />} />
                <Route path="/exercises" element={<ExercisePlan />} />
                <Route path="/meals" element={<MealPlan />} />
                <Route path="/calories" element={<CalorieTracker />} />
                <Route path="/progress" element={<Progress />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/about" element={<About />} />
              </Routes>
            </Suspense>
          </div>
          <NavBar />
        </div>
      </UserProvider>
    </ErrorBoundary>
  )
}
