import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '@/api/client'
import { updateEmail } from '@/api/users'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/components/ui/PasswordInput'
import { Modal } from '@/components/ui/Modal'

export function ChangeEmailModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void
  onSuccess: () => void
}) {
  const { t } = useTranslation('account')
  const { t: tc } = useTranslation('common')
  const [newEmail, setNewEmail] = useState('')
  const [password, setPassword] = useState('')

  const mutation = useMutation({
    mutationFn: () => updateEmail(password, newEmail),
    onSuccess,
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Modal
      title={t('changeEmail')}
      minHeightClassName="min-h-[19rem]"
      showCloseButton={false}
      onClose={onClose}
    >
      <form className="flex flex-1 flex-col gap-4" onSubmit={handleSubmit} autoComplete="off">
        <Input
          label={t('newEmail')}
          type="email"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
          required
          autoComplete="off"
        />
        <PasswordInput
          label={t('currentPassword')}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
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
            {t('updateEmail')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
