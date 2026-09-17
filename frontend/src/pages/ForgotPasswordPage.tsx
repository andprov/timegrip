import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { forgotPassword } from '@/api/auth'
import { ApiError } from '@/api/client'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function ForgotPasswordPage() {
  const { t } = useTranslation('auth')
  const { t: tc } = useTranslation('common')
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // The backend already answers 204 for any well-formed email, known or not,
  // so surfacing errors here (validation, server down) leaks nothing.
  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await forgotPassword(email)
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : tc('somethingWentWrong'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout title={t('forgotPasswordTitle')}>
      {submitted ? (
        <Alert variant="success">
          {t('resetCodeSentMessage', { email })}
        </Alert>
      ) : (
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <Input
            label={t('email')}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          {error && <Alert>{error}</Alert>}
          <Button type="submit" disabled={isSubmitting}>
            {t('sendResetCode')}
          </Button>
        </form>
      )}
      <div className="mt-4 flex justify-between text-sm">
        <Link to="/signin" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
          {t('backToSignIn')}
        </Link>
        <Link to="/reset-password" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
          {t('haveACode')}
        </Link>
      </div>
    </AuthLayout>
  )
}
