import { apiFetch } from '@/api/client'
import type { TokenPair, User } from '@/api/types'
import type { Locale } from '@/i18n/config'

export function signUp(
  email: string,
  password: string,
  locale?: Locale,
): Promise<User> {
  return apiFetch<User>('/auth/signup', {
    method: 'POST',
    body: { email, password, locale },
  })
}

export function signIn(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>('/auth/signin', {
    method: 'POST',
    body: { email, password },
  })
}

export function signOut(refreshToken: string): Promise<void> {
  return apiFetch<void>('/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  })
}

export function forgotPassword(email: string): Promise<void> {
  return apiFetch<void>('/auth/password/forgot', {
    method: 'POST',
    body: { email },
  })
}

export function resetPassword(
  email: string,
  code: string,
  newPassword: string,
): Promise<void> {
  return apiFetch<void>('/auth/password/reset', {
    method: 'POST',
    body: { email, code, new_password: newPassword },
  })
}
