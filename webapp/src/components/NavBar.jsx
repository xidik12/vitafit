import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { HomeIcon, DumbbellIcon, UtensilsIcon, PencilIcon, ChartBarIcon } from './Icons'

const tabs = [
  { path: '/', Icon: HomeIcon, key: 'nav.home', color: 'accent-green' },
  { path: '/exercises', Icon: DumbbellIcon, key: 'nav.exercises', color: 'accent-blue' },
  { path: '/meals', Icon: UtensilsIcon, key: 'nav.meals', color: 'accent-orange' },
  { path: '/calories', Icon: PencilIcon, key: 'nav.calories', color: 'accent-teal' },
  { path: '/progress', Icon: ChartBarIcon, key: 'nav.progress', color: 'accent-purple' },
]

const colorMap = {
  'accent-green': { bg: 'bg-accent-green/15', text: 'text-accent-green', iconBg: 'bg-accent-green' },
  'accent-blue': { bg: 'bg-accent-blue/15', text: 'text-accent-blue', iconBg: 'bg-accent-blue' },
  'accent-orange': { bg: 'bg-accent-orange/15', text: 'text-accent-orange', iconBg: 'bg-accent-orange' },
  'accent-teal': { bg: 'bg-accent-teal/15', text: 'text-accent-teal', iconBg: 'bg-accent-teal' },
  'accent-purple': { bg: 'bg-accent-purple/15', text: 'text-accent-purple', iconBg: 'bg-accent-purple' },
}

export default function NavBar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { t } = useTranslation()

  return (
    <nav className="fixed bottom-3 left-3 right-3 bg-white/95 backdrop-blur-lg border border-border/60 rounded-2xl flex justify-around py-2 px-1 z-50 shadow-lg shadow-black/8">
      {tabs.map(tab => {
        const active = pathname === tab.path
        const colors = colorMap[tab.color]
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`flex flex-col items-center gap-0.5 px-3 py-2.5 rounded-xl transition-all duration-200 min-h-[44px] min-w-[44px] ${
              active ? `${colors.bg}` : 'hover:bg-gray-50'
            }`}
          >
            <tab.Icon className={`w-6 h-6 transition-colors ${active ? colors.text : 'text-text-secondary'}`} />
            <span className={`text-xs font-medium transition-colors ${active ? colors.text : 'text-text-secondary'}`}>
              {t(tab.key)}
            </span>
          </button>
        )
      })}
    </nav>
  )
}
