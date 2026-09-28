import { useQueryClient } from '@tanstack/react-query'
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
  // Endpoints that change the user answer with the updated one; storing it
  // saves a follow-up GET /users/me.
  setUser: (user: User) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<User | null>(null)
  const { locale, setLocale } = useLocale()
  const queryClient = useQueryClient()

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

  // Sign-up already returns the new user, so only the tokens are missing.
  const signUp = useCallback(async (email: string, password: string) => {
    const newUser = await apiSignUp(email, password, locale)
    setTokens(await apiSignIn(email, password))
    setUser(newUser)
    setLocale(newUser.locale)
    setStatus('authenticated')
  }, [locale, setLocale])

  const signOut = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      await apiSignOut(refreshToken).catch(() => undefined)
    }
    clearTokens()
    setUser(null)
    setStatus('unauthenticated')
    // Cached projects and timers belong to this account; the next one to
    // sign in in this tab must not see them.
    queryClient.clear()
  }, [queryClient])

  const value = useMemo(
    () => ({ status, user, signIn, signUp, signOut, setUser }),
    [status, user, signIn, signUp, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
