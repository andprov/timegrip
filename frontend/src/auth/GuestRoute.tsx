import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '@/auth/useAuth'
import { Spinner } from '@/components/ui/Spinner'

export function GuestRoute() {
  const { status } = useAuth()

  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }

  if (status === 'authenticated') {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
