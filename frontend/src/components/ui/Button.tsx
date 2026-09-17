import type { ButtonHTMLAttributes } from 'react'
import { Link } from 'react-router-dom'
import type { LinkProps } from 'react-router-dom'

const VARIANT_CLASSES = {
  primary:
    'bg-indigo-600 text-white hover:bg-indigo-500 disabled:bg-indigo-300 dark:disabled:bg-indigo-900',
  secondary:
    'bg-white text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:text-gray-400 dark:bg-gray-900 dark:text-gray-100 dark:ring-gray-700 dark:hover:bg-gray-800 dark:disabled:text-gray-600',
  danger:
    'bg-white text-red-600 ring-1 ring-inset ring-red-300 hover:bg-red-50 disabled:text-red-300 dark:bg-gray-900 dark:text-red-400 dark:ring-red-900 dark:hover:bg-red-950/40 dark:disabled:text-red-900',
  ghost:
    'text-gray-600 hover:bg-gray-100 disabled:text-gray-300 dark:text-gray-400 dark:hover:bg-gray-800 dark:disabled:text-gray-600',
} as const

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANT_CLASSES
}

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex min-w-28 items-center justify-center gap-2 rounded-md px-4 py-3 text-base font-medium transition-colors disabled:cursor-not-allowed sm:px-3 sm:py-2 sm:text-sm ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  )
}

interface LinkButtonProps extends LinkProps {
  variant?: keyof typeof VARIANT_CLASSES
}

export function LinkButton({
  variant = 'primary',
  className = '',
  ...props
}: LinkButtonProps) {
  return (
    <Link
      className={`inline-flex min-w-28 items-center justify-center gap-2 rounded-md px-4 py-3 text-base font-medium transition-colors sm:px-3 sm:py-2 sm:text-sm ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  )
}
