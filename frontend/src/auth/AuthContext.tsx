import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import {
  signIn as apiSignIn,
  signOut as apiSignOut,
  signUp as apiSignUp,
} from '@/api/auth'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/api/client'
import { getMe } from '@/api/users'
import type { User } from '@/api/types'
import { useLocale } from '@/i18n/useLocale'

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

export interface AuthContextValue {
  status: AuthStatus
  user: User | null
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<User | null>(null)
  const { locale, setLocale } = useLocale()

  const loadUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null)
      setStatus('unauthenticated')
      return
    }
    try {
      const currentUser = await getMe()
      setUser(currentUser)
      setLocale(currentUser.locale)
      setStatus('authenticated')
    } catch {
      clearTokens()
      setUser(null)
      setStatus('unauthenticated')
    }
  }, [setLocale])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const signIn = useCallback(async (email: string, password: string) => {
    const tokens = await apiSignIn(email, password)
    setTokens(tokens)
    await loadUser()
  }, [loadUser])

  const signUp = useCallback(async (email: string, password: string) => {
    await apiSignUp(email, password, locale)
    await signIn(email, password)
  }, [signIn, locale])

  const signOut = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      await apiSignOut(refreshToken).catch(() => undefined)
    }
    clearTokens()
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  const value = useMemo(
    () => ({ status, user, signIn, signUp, signOut, refreshUser: loadUser }),
    [status, user, signIn, signUp, signOut, loadUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
