import { ArrowRight, ShieldAlert } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/auth-context'
import { hasAdminAccess } from '../../lib/access'
import { PageLoader } from '../ui'

export function AdminRoute({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const location = useLocation()

  if (!ready) return <PageLoader label="Checking your session" />
  if (!user) {
    return <Navigate to="/signin" replace state={{ from: `${location.pathname}${location.search}` }} />
  }
  if (!hasAdminAccess(user)) {
    return (
      <div className="admin-denied">
        <ShieldAlert size={28} strokeWidth={1.5} aria-hidden="true" />
        <h1>Administrator access only</h1>
        <p className="muted">
          This area manages products, categories and sales. Sign in with an administrator
          account to continue.
        </p>
        <Link className="btn btn-dark btn-sm" to="/">
          Back to the store
          <ArrowRight size={15} strokeWidth={1.8} />
        </Link>
      </div>
    )
  }
  return <>{children}</>
}

export function CustomerRoute({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const location = useLocation()

  if (!ready) return <PageLoader label="Checking your session" />
  if (!user) {
    return <Navigate to="/signin" replace state={{ from: `${location.pathname}${location.search}` }} />
  }
  if (hasAdminAccess(user)) return <Navigate to="/admin" replace />
  return <>{children}</>
}
