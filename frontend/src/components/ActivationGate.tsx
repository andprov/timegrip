import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Trans, useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'

import { ApiError } from '@/api/client'
import {
  activateAccount,
  getResendCooldown,
  resendActivationCode,
} from '@/api/users'
import { useAuth } from '@/auth/useAuth'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { useCountdown } from '@/hooks/useCountdown'
import { formatCountdown } from '@/lib/format'

export function ActivationGate() {
  const { t } = useTranslation('activation')
  const { t: tc } = useTranslation('common')
  const { user, refreshUser } = useAuth()
  // The link from the activation email carries the code.
  const [searchParams] = useSearchParams()
  const [code, setCode] = useState(searchParams.get('code') ?? '')
  const queryClient = useQueryClient()

  // The server knows when the last code went out, so the countdown survives
  // a page reload and is already running right after sign-up.
  const cooldownQuery = useQuery({
    queryKey: ['resendCooldown'],
    queryFn: getResendCooldown,
    gcTime: 0,
  })
  const resendSecondsLeft = useCountdown(
    cooldownQuery.data?.retry_after_seconds ?? 0,
    cooldownQuery.dataUpdatedAt,
  )

  const activateMutation = useMutation({
    mutationFn: () => activateAccount(code),
    onSuccess: () => refreshUser(),
  })

  const resendMutation = useMutation({
    mutationFn: resendActivationCode,
    // Awaiting the fresh cooldown keeps the button disabled until the
    // countdown has taken over, whether the code was sent or rejected.
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ['resendCooldown'] }),
  })
  // A rejection while the countdown runs is already explained by it.
  const resendError = resendSecondsLeft > 0 ? null : resendMutation.error

  return (
    <div className="mx-auto max-w-sm">
      <Card>
        <h2 className="mb-2 text-lg font-medium text-gray-900 dark:text-gray-100">
          {t('title')}
        </h2>
        <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
          <Trans
            t={t}
            i18nKey="description"
            values={{ email: user?.email }}
            components={{
              email: (
                <span className="inline-block max-w-full font-medium wrap-anywhere text-gray-900 dark:text-gray-100" />
              ),
            }}
          />
        </p>
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            activateMutation.mutate()
          }}
        >
          <Input
            label={t('codeLabel')}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            required
          />
          {activateMutation.isError && (
            <Alert>
              {activateMutation.error instanceof ApiError
                ? activateMutation.error.message
                : tc('somethingWentWrong')}
            </Alert>
          )}
          <Button type="submit" disabled={activateMutation.isPending}>
            {t('activate')}
          </Button>
        </form>
        <div className="mt-4 border-t border-gray-100 pt-4 dark:border-gray-800">
          <div className="flex flex-col gap-3">
            {resendMutation.isSuccess && (
              <Alert variant="success">{t('codeResent')}</Alert>
            )}
            {resendError && (
              <Alert>
                {resendError instanceof ApiError
                  ? resendError.message
                  : tc('somethingWentWrong')}
              </Alert>
            )}
            <Button
              variant="ghost"
              onClick={() => resendMutation.mutate()}
              disabled={
                cooldownQuery.isPending ||
                resendMutation.isPending ||
                resendSecondsLeft > 0
              }
            >
              {resendSecondsLeft > 0
                ? t('resendCodeIn', { time: formatCountdown(resendSecondsLeft) })
                : t('resendCode')}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
