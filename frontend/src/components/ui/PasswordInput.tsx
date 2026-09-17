import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Input } from '@/components/ui/Input'
import type { InputProps } from '@/components/ui/Input'

type PasswordInputProps = Omit<InputProps, 'type' | 'endAdornment'>

/** Password field with an eye button that toggles the value's visibility. */
export function PasswordInput({ className = '', ...props }: PasswordInputProps) {
  const { t } = useTranslation('common')
  const [isVisible, setIsVisible] = useState(false)

  return (
    <Input
      {...props}
      type={isVisible ? 'text' : 'password'}
      // Hide Edge's built-in reveal button so it doesn't duplicate ours.
      className={`[&::-ms-reveal]:hidden ${className}`}
      endAdornment={
        <button
          type="button"
          // Keep focus (and the caret) in the field when toggling with a click.
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => setIsVisible((v) => !v)}
          aria-label={isVisible ? t('hidePassword') : t('showPassword')}
          aria-pressed={isVisible}
          className="flex size-8 items-center justify-center rounded-md text-gray-400 hover:text-gray-600 focus-visible:outline-2 focus-visible:outline-indigo-600 dark:text-gray-500 dark:hover:text-gray-300"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="size-5"
            aria-hidden="true"
          >
            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
            <circle cx="12" cy="12" r="3" />
            {isVisible && <path d="M3 3l18 18" />}
          </svg>
        </button>
      }
    />
  )
}
