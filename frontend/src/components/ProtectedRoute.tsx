import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { CustomerRoute } from './admin/AdminRoute'
import { useAuth } from '../context/auth-context'
import { PageLoader } from './ui'

export { CustomerRoute }

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const location = useLocation()

  if (!ready) return <PageLoader label="Checking your session" />
  if (!user) {
    return <Navigate to="/signin" replace state={{ from: `${location.pathname}${location.search}` }} />
  }
  return <>{children}</>
}
