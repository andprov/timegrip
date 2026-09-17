import { useContext } from 'react'

import { LocaleContext } from '@/i18n/LocaleContext'
import type { LocaleContextValue } from '@/i18n/LocaleContext'

export function useLocale(): LocaleContextValue {
  const context = useContext(LocaleContext)
  if (!context) throw new Error('useLocale must be used within LocaleProvider')
  return context
}
