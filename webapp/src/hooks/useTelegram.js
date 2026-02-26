import { useMemo } from 'react'

export function useTelegram() {
  const tg = useMemo(() => window.Telegram?.WebApp, [])
  const user = tg?.initDataUnsafe?.user
  const initData = tg?.initData

  return {
    tg,
    user,
    initData,
    colorScheme: tg?.colorScheme || 'dark',
    isExpanded: tg?.isExpanded,
    ready: () => tg?.ready(),
    expand: () => tg?.expand(),
    close: () => tg?.close(),
    haptic: tg?.HapticFeedback,
  }
}
