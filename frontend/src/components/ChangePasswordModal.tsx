import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError, setTokens } from '@/api/client'
import { updatePassword } from '@/api/users'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { PasswordInput } from '@/components/ui/PasswordInput'

export function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation('account')
  const { t: tc } = useTranslation('common')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')

  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => updatePassword(currentPassword, newPassword),
    onSuccess: (tokens) => {
      setTokens(tokens)
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      onClose()
    },
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Modal
      title={t('changePassword')}
      minHeightClassName="min-h-[19rem]"
      showCloseButton={false}
      onClose={onClose}
    >
      <form className="flex flex-1 flex-col gap-4" onSubmit={handleSubmit}>
        <PasswordInput
          label={t('currentPassword')}
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
        <PasswordInput
          label={t('newPassword')}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={5}
        />
        {mutation.isError && (
          <Alert>
            {mutation.error instanceof ApiError
              ? mutation.error.message
              : tc('somethingWentWrong')}
          </Alert>
        )}
        <div className="mt-auto flex flex-col gap-3">
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            onClick={onClose}
          >
            {tc('cancel')}
          </Button>
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {t('updatePassword')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
