import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const tabs = [
  { path: '/', icon: '🏠', key: 'nav.home' },
  { path: '/exercises', icon: '💪', key: 'nav.exercises' },
  { path: '/meals', icon: '🍽️', key: 'nav.meals' },
  { path: '/calories', icon: '📝', key: 'nav.calories' },
  { path: '/progress', icon: '📊', key: 'nav.progress' },
]

export default function NavBar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { t } = useTranslation()

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-border flex justify-around py-2 z-50">
      {tabs.map(tab => {
        const active = pathname === tab.path
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`flex flex-col items-center gap-0.5 px-3 py-1 text-xs ${active ? 'text-accent-green font-semibold' : 'text-text-secondary'}`}
          >
            <span className="text-lg">{tab.icon}</span>
            <span>{t(tab.key)}</span>
          </button>
        )
      })}
    </nav>
  )
}
