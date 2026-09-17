import { useMutation } from '@tanstack/react-query'

import { updateLocale } from '@/api/users'
import { useAuth } from '@/auth/useAuth'
import type { Locale } from '@/i18n/config'
import { useLocale } from '@/i18n/useLocale'

export function useLocaleSetting() {
  const { locale, setLocale } = useLocale()
  const { status } = useAuth()

  const mutation = useMutation({ mutationFn: updateLocale })

  function changeLocale(next: Locale) {
    setLocale(next)
    if (status === 'authenticated') {
      mutation.mutate(next)
    }
  }

  return {
    locale,
    changeLocale,
    isError: mutation.isError,
    error: mutation.error,
  }
}
