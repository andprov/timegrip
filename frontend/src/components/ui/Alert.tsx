import type { ReactNode } from 'react'

const VARIANT_CLASSES = {
  error:
    'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200 dark:bg-red-950/40 dark:text-red-300 dark:ring-red-900',
  success:
    'bg-green-50 text-green-700 ring-1 ring-inset ring-green-200 dark:bg-green-950/40 dark:text-green-300 dark:ring-green-900',
  info: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:ring-blue-900',
} as const

export function Alert({
  variant = 'error',
  children,
}: {
  variant?: keyof typeof VARIANT_CLASSES
  children: ReactNode
}) {
  return (
    <div className={`rounded-md px-3 py-2 text-sm ${VARIANT_CLASSES[variant]}`}>
      {children}
    </div>
  )
}
