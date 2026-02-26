import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { HomeIcon, DumbbellIcon, UtensilsIcon, PencilIcon, ChartBarIcon } from './Icons'

const tabs = [
  { path: '/', Icon: HomeIcon, key: 'nav.home' },
  { path: '/exercises', Icon: DumbbellIcon, key: 'nav.exercises' },
  { path: '/meals', Icon: UtensilsIcon, key: 'nav.meals' },
  { path: '/calories', Icon: PencilIcon, key: 'nav.calories' },
  { path: '/progress', Icon: ChartBarIcon, key: 'nav.progress' },
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
            <tab.Icon className="w-5 h-5" />
            <span>{t(tab.key)}</span>
          </button>
        )
      })}
    </nav>
  )
}
