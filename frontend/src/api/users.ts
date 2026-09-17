import { apiFetch } from '@/api/client'
import type {
  ResendCooldown,
  Session,
  TimeFormatPreference,
  TokenPair,
  User,
} from '@/api/types'
import type { Locale } from '@/i18n/config'

export function getMe(): Promise<User> {
  return apiFetch<User>('/users/me')
}

export function activateAccount(code: string): Promise<void> {
  return apiFetch<void>('/users/me/activate', {
    method: 'POST',
    body: { code },
  })
}

export function resendActivationCode(): Promise<void> {
  return apiFetch<void>('/users/me/activate/resend', { method: 'POST' })
}

export function getResendCooldown(): Promise<ResendCooldown> {
  return apiFetch<ResendCooldown>('/users/me/activate/resend-cooldown')
}

export function updatePassword(
  currentPassword: string,
  newPassword: string,
): Promise<TokenPair> {
  return apiFetch<TokenPair>('/users/me/password', {
    method: 'PATCH',
    body: { current_password: currentPassword, new_password: newPassword },
  })
}

export function updateEmail(
  password: string,
  newEmail: string,
): Promise<User> {
  return apiFetch<User>('/users/me/email', {
    method: 'PATCH',
    body: { password, new_email: newEmail },
  })
}

export function deleteMe(): Promise<void> {
  return apiFetch<void>('/users/me', { method: 'DELETE' })
}

export function updateTimeFormat(
  timeFormat: TimeFormatPreference,
): Promise<User> {
  return apiFetch<User>('/users/me/time-format', {
    method: 'PATCH',
    body: { time_format: timeFormat },
  })
}

export function updateLocale(locale: Locale): Promise<User> {
  return apiFetch<User>('/users/me/locale', {
    method: 'PATCH',
    body: { locale },
  })
}

export function getSessions(): Promise<Session[]> {
  return apiFetch<Session[]>('/users/me/sessions')
}

export function revokeSession(id: number): Promise<void> {
  return apiFetch<void>(`/users/me/sessions/${id}`, { method: 'DELETE' })
}

export function revokeAllSessions(): Promise<void> {
  return apiFetch<void>('/users/me/sessions', { method: 'DELETE' })
}
