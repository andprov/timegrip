import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/useAuth'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/components/ui/PasswordInput'

export function SignUpPage() {
  const { t } = useTranslation('auth')
  const { t: tc } = useTranslation('common')
  const { signUp } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  // Mismatch is reported only once the user leaves the confirm field or
  // submits, so it doesn't flash while they are still typing.
  const [isMismatchShown, setIsMismatchShown] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const passwordsMatch = password === confirmPassword

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!passwordsMatch) {
      setIsMismatchShown(true)
      return
    }
    setIsSubmitting(true)
    try {
      await signUp(email, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : tc('somethingWentWrong'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout title={t('createAccount')}>
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <Input
          label={t('email')}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus
        />
        <PasswordInput
          label={t('password')}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          required
          minLength={5}
        />
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t('passwordHint')}
        </p>
        <PasswordInput
          label={t('confirmPassword')}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          onBlur={() => setIsMismatchShown(confirmPassword !== '')}
          autoComplete="new-password"
          required
          error={
            isMismatchShown && !passwordsMatch
              ? t('passwordsDoNotMatch')
              : undefined
          }
        />
        {error && <Alert>{error}</Alert>}
        <Button type="submit" disabled={isSubmitting}>
          {t('signUp')}
        </Button>
      </form>
      <div className="mt-4 text-center text-sm">
        <Link to="/signin" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
          {t('alreadyHaveAccount')}
        </Link>
      </div>
    </AuthLayout>
  )
}
