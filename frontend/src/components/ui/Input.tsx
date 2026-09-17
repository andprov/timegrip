import { useId } from 'react'
import type {
  ChangeEvent,
  FormEvent,
  InputHTMLAttributes,
  ReactNode,
} from 'react'
import { useTranslation } from 'react-i18next'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  /** Rendered inside the field on the right, e.g. a visibility toggle. */
  endAdornment?: ReactNode
}

type Translate = (key: string, options?: Record<string, unknown>) => string

// An empty message clears the custom validity, so the browser falls back to
// its own wording for states we have no translation for.
function validationMessage(input: HTMLInputElement, t: Translate): string {
  const { validity } = input

  if (validity.valueMissing) return t('validation.required')
  if (validity.typeMismatch && input.type === 'email') {
    return t('validation.email')
  }
  if (validity.tooShort) {
    return t('validation.tooShort', { min: input.minLength })
  }
  if (validity.badInput) return t('validation.number')
  if (validity.rangeUnderflow) return t('validation.min', { min: input.min })
  if (validity.rangeOverflow) return t('validation.max', { max: input.max })
  if (validity.stepMismatch) return t('validation.step', { step: input.step })

  return ''
}

export function Input({
  label,
  error,
  endAdornment,
  id,
  className = '',
  onChange,
  onInvalid,
  ...props
}: InputProps) {
  const { t } = useTranslation('common')
  const generatedId = useId()
  const inputId = id ?? generatedId

  const handleInvalid = (event: FormEvent<HTMLInputElement>) => {
    event.currentTarget.setCustomValidity(
      validationMessage(event.currentTarget, t),
    )
    onInvalid?.(event)
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    event.currentTarget.setCustomValidity('')
    onChange?.(event)
  }

  const renderInput = (extraClassName: string) => (
    <input
      id={inputId}
      className={`rounded-md border-0 px-3 py-2 text-base text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm dark:text-gray-100 dark:ring-gray-700 dark:placeholder:text-gray-500 ${extraClassName} ${className}`}
      onChange={handleChange}
      onInvalid={handleInvalid}
      {...props}
    />
  )

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      {endAdornment ? (
        <div className="relative">
          {renderInput('w-full pr-11')}
          <div className="absolute inset-y-0 right-0 flex items-center pr-1.5">
            {endAdornment}
          </div>
        </div>
      ) : (
        renderInput('')
      )}
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  )
}
