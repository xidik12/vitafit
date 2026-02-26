import { useState, useEffect } from 'react'
import { useTelegram } from './useTelegram'
import api from '../utils/api'

export function useAuth() {
  const { initData, user } = useTelegram()
  const [token, setToken] = useState(() => localStorage.getItem('vitafit-token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function authenticate() {
      if (token) {
        setLoading(false)
        return
      }
      if (!initData) {
        setLoading(false)
        return
      }
      try {
        const res = await api.post('/api/auth/telegram', { init_data: initData })
        const newToken = res.token
        localStorage.setItem('vitafit-token', newToken)
        setToken(newToken)
      } catch (err) {
        console.error('Auth failed:', err)
      }
      setLoading(false)
    }
    authenticate()
  }, [initData, token])

  return { token, user, loading }
}
