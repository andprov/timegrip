import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { resetPassword } from '@/api/auth'
import { ApiError } from '@/api/client'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/components/ui/PasswordInput'

export function ResetPasswordPage() {
  const { t } = useTranslation('auth')
  const { t: tc } = useTranslation('common')
  const navigate = useNavigate()
  // The link from the reset email carries both values, leaving only the new
  // password to type.
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState(searchParams.get('email') ?? '')
  const [code, setCode] = useState(searchParams.get('code') ?? '')
  const isPrefilled = searchParams.has('email') && searchParams.has('code')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await resetPassword(email, code, newPassword)
      navigate('/signin', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : tc('somethingWentWrong'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout title={t('resetPassword')}>
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <Input
          label={t('email')}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus={!isPrefilled}
        />
        <Input
          label={t('resetCode')}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="123456"
          required
        />
        <PasswordInput
          label={t('newPassword')}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={5}
          autoFocus={isPrefilled}
        />
        {error && <Alert>{error}</Alert>}
        <Button type="submit" disabled={isSubmitting}>
          {t('resetPassword')}
        </Button>
      </form>
      <div className="mt-4 text-center text-sm">
        <Link to="/signin" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
          {t('backToSignIn')}
        </Link>
      </div>
    </AuthLayout>
  )
}
