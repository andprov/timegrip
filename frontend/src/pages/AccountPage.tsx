import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '@/api/client'
import type { TimeFormatPreference } from '@/api/types'
import {
  deleteMe,
  getSessions,
  revokeAllSessions,
  revokeSession,
  updateTimeFormat,
} from '@/api/users'
import { useAuth } from '@/auth/useAuth'
import { ChangeEmailModal } from '@/components/ChangeEmailModal'
import { ChangePasswordModal } from '@/components/ChangePasswordModal'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import type { Locale } from '@/i18n/config'
import { useLocaleSetting } from '@/i18n/useLocaleSetting'
import { useTheme } from '@/theme/useTheme'
import type { ThemePreference } from '@/theme/ThemeContext'

type ActiveModal = 'email' | 'password' | null

export function AccountPage() {
  const { t } = useTranslation('account')
  const { t: tc } = useTranslation('common')
  const THEME_LABELS: Record<ThemePreference, string> = {
    light: t('themeOptions.light'),
    dark: t('themeOptions.dark'),
    system: t('themeOptions.system'),
  }
  const LOCALE_LABELS: Record<Locale, string> = {
    en: 'English',
    ru: 'Русский',
  }
  const TIME_FORMAT_LABELS: Record<TimeFormatPreference, string> = {
    '12h': t('timeFormatOptions.12h'),
    '24h': t('timeFormatOptions.24h'),
  }
  const { user, refreshUser, signOut } = useAuth()
  const { theme, setTheme } = useTheme()
  const {
    locale,
    changeLocale,
    isError: isLocaleError,
    error: localeError,
  } = useLocaleSetting()
  const queryClient = useQueryClient()
  const [activeModal, setActiveModal] = useState<ActiveModal>(null)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [confirmingLogoutEverywhere, setConfirmingLogoutEverywhere] =
    useState(false)

  const deleteMutation = useMutation({
    mutationFn: deleteMe,
    onSuccess: signOut,
  })

  const timeFormatMutation = useMutation({
    mutationFn: updateTimeFormat,
    onSuccess: refreshUser,
  })

  const sessionsQuery = useQuery({
    queryKey: ['sessions'],
    queryFn: getSessions,
  })

  const revokeSessionMutation = useMutation({
    mutationFn: revokeSession,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sessions'] }),
  })

  const revokeAllSessionsMutation = useMutation({
    mutationFn: revokeAllSessions,
    onSuccess: signOut,
  })

  return (
    <div>
      <div className="mb-6 flex min-h-9 items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{t('title')}</h1>
      </div>

      <Card className="divide-y divide-gray-100 p-0 dark:divide-gray-800">
        <div className="flex flex-col gap-3 p-6 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
          <div className="min-w-0 break-words">
            <p className="font-medium text-gray-900 dark:text-gray-100">{t('signedInAs')}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email}</p>
          </div>
          <Button
            className="w-full sm:w-40"
            variant="secondary"
            onClick={() => setActiveModal('email')}
          >
            {t('changeEmail')}
          </Button>
        </div>

        <div className="p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">{t('theme')}</p>
            </div>
            <Select
              className="w-full sm:w-40"
              value={theme}
              onChange={(v) => setTheme(v as ThemePreference)}
              options={(
                Object.keys(THEME_LABELS) as ThemePreference[]
              ).map((option) => ({
                value: option,
                label: THEME_LABELS[option],
              }))}
            />
          </div>
        </div>

        <div className="p-6">
          {timeFormatMutation.isError && (
            <div className="mb-3">
              <Alert>
                {timeFormatMutation.error instanceof ApiError
                  ? timeFormatMutation.error.message
                  : tc('somethingWentWrong')}
              </Alert>
            </div>
          )}
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">{t('timeFormat')}</p>
            </div>
            <Select
              className="w-full sm:w-40"
              value={user?.time_format ?? '24h'}
              onChange={(v) =>
                timeFormatMutation.mutate(v as TimeFormatPreference)
              }
              options={(
                Object.keys(TIME_FORMAT_LABELS) as TimeFormatPreference[]
              ).map((option) => ({
                value: option,
                label: TIME_FORMAT_LABELS[option],
              }))}
            />
          </div>
        </div>

        <div className="p-6">
          {isLocaleError && (
            <div className="mb-3">
              <Alert>
                {localeError instanceof ApiError
                  ? localeError.message
                  : tc('somethingWentWrong')}
              </Alert>
            </div>
          )}
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">{t('language')}</p>
            </div>
            <Select
              className="w-full sm:w-40"
              value={locale}
              onChange={(v) => changeLocale(v as Locale)}
              options={(Object.keys(LOCALE_LABELS) as Locale[]).map(
                (option) => ({
                  value: option,
                  label: LOCALE_LABELS[option],
                }),
              )}
            />
          </div>
        </div>

        <div className="p-6">
          <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">{t('activeSessions')}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('activeSessionsDesc')}
              </p>
            </div>
            <Button
              className="w-full sm:w-40"
              variant="secondary"
              disabled={
                revokeAllSessionsMutation.isPending ||
                !sessionsQuery.data?.length
              }
              onClick={() => setConfirmingLogoutEverywhere(true)}
            >
              {t('logOutEverywhere')}
            </Button>
          </div>
          {sessionsQuery.isLoading && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{tc('loading')}</p>
          )}
          {sessionsQuery.data && sessionsQuery.data.length > 0 && (
            <details className="group">
              <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-medium text-gray-700 [&::-webkit-details-marker]:hidden dark:text-gray-300">
                <svg
                  className="h-4 w-4 shrink-0 text-gray-400 transition-transform group-open:rotate-90 dark:text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                {t('session', { count: sessionsQuery.data.length })}
              </summary>
              <ul className="mt-2 divide-y divide-gray-100 dark:divide-gray-800">
                {sessionsQuery.data.map((session) => (
                  <li
                    key={session.id}
                    className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm text-gray-900 dark:text-gray-100">
                        {session.user_agent ?? t('unknownDevice')}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {session.ip_address ?? t('unknownIp')} ·{' '}
                        {new Date(session.created_at).toLocaleString()}
                      </p>
                    </div>
                    <Button
                      className="w-full sm:w-auto"
                      variant="secondary"
                      disabled={revokeSessionMutation.isPending}
                      onClick={() => revokeSessionMutation.mutate(session.id)}
                    >
                      {t('revoke')}
                    </Button>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>

        <div className="flex flex-col gap-3 p-6 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
          <div>
            <p className="font-medium text-gray-900 dark:text-gray-100">{t('password')}</p>
          </div>
          <Button
            className="w-full sm:w-40"
            variant="secondary"
            onClick={() => setActiveModal('password')}
          >
            {t('changePassword')}
          </Button>
        </div>

        <div className="p-6">
          {deleteMutation.isError && (
            <div className="mb-3">
              <Alert>
                {deleteMutation.error instanceof ApiError
                  ? deleteMutation.error.message
                  : tc('somethingWentWrong')}
              </Alert>
            </div>
          )}
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium text-red-600 dark:text-red-400">{t('deleteAccountTitle')}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('deleteAccountDesc')}
              </p>
            </div>
            <Button
              className="w-full sm:w-40"
              variant="danger"
              disabled={deleteMutation.isPending}
              onClick={() => setConfirmingDelete(true)}
            >
              {t('deleteAccountTitle')}
            </Button>
          </div>
        </div>
      </Card>

      {confirmingDelete && (
        <Modal
          title={t('deleteAccountTitle')}
          titleClassName="text-red-600 dark:text-red-400"
          minHeightClassName="min-h-[19rem]"
          showCloseButton={false}
          onClose={() => setConfirmingDelete(false)}
        >
          <div className="rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/40">
            <p className="text-sm font-semibold text-red-800 dark:text-red-300">{t('dangerZone')}</p>
            <p className="mt-1 text-sm text-red-700 dark:text-red-400">
              {t('deleteAccountConfirm')}
            </p>
          </div>
          <div className="mt-auto flex flex-col gap-3">
            <Button
              type="button"
              variant="secondary"
              className="w-full"
              onClick={() => setConfirmingDelete(false)}
            >
              {tc('cancel')}
            </Button>
            <Button
              type="button"
              variant="danger"
              className="w-full"
              disabled={deleteMutation.isPending}
              onClick={() => deleteMutation.mutate()}
            >
              {t('deleteAccountTitle')}
            </Button>
          </div>
        </Modal>
      )}

      {confirmingLogoutEverywhere && (
        <Modal
          title={t('logOutEverywhere')}
          minHeightClassName="min-h-[19rem]"
          showCloseButton={false}
          onClose={() => setConfirmingLogoutEverywhere(false)}
        >
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('logoutEverywhereConfirm')}
          </p>
          <div className="mt-auto flex flex-col gap-3">
            <Button
              type="button"
              variant="secondary"
              className="w-full"
              onClick={() => setConfirmingLogoutEverywhere(false)}
            >
              {tc('cancel')}
            </Button>
            <Button
              type="button"
              variant="danger"
              className="w-full"
              disabled={revokeAllSessionsMutation.isPending}
              onClick={() => revokeAllSessionsMutation.mutate()}
            >
              {t('logOutEverywhere')}
            </Button>
          </div>
        </Modal>
      )}

      {activeModal === 'email' && (
        <ChangeEmailModal
          onClose={() => setActiveModal(null)}
          onSuccess={() => {
            refreshUser()
            setActiveModal(null)
          }}
        />
      )}

      {activeModal === 'password' && (
        <ChangePasswordModal onClose={() => setActiveModal(null)} />
      )}
    </div>
  )
}
