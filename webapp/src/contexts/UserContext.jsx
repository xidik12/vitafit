import { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useTelegram } from '../hooks/useTelegram'
import api from '../utils/api'
import i18n from '../i18n'

const UserContext = createContext(null)

export function UserProvider({ children }) {
  const { token, user: tgUser, loading: authLoading } = useAuth()
  const { tg, ready, expand } = useTelegram()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ready?.()
    expand?.()
  }, [ready, expand])

  useEffect(() => {
    if (authLoading || !token) {
      setLoading(false)
      return
    }
    async function fetchProfile() {
      try {
        const data = await api.get('/api/profile', token)
        setProfile(data)
      } catch (err) {
        console.error('Profile fetch failed:', err)
      }
      setLoading(false)
    }
    fetchProfile()
  }, [token, authLoading])

  useEffect(() => {
    if (profile?.language) {
      i18n.changeLanguage(profile.language)
      localStorage.setItem('vitafit-lang', profile.language)
    }
  }, [profile?.language])

  return (
    <UserContext.Provider value={{ tgUser, profile, setProfile, token, loading: loading || authLoading }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  return useContext(UserContext)
}
