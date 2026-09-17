import type { ReactNode } from 'react'

import { AppLogo } from '@/components/AppLogo'

export function AuthLayout({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-950">
      <div className="w-full max-w-sm">
        <h1 className="mb-6 flex items-center justify-center gap-1.5 text-2xl font-semibold text-gray-900 dark:text-gray-100">
          <AppLogo className="size-7" />
          TimeGrip
        </h1>
        <div className="rounded-lg bg-white p-6 shadow-sm ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-800">
          <h2 className="mb-4 text-lg font-medium text-gray-900 dark:text-gray-100">{title}</h2>
          {children}
        </div>
      </div>
    </div>
  )
}
