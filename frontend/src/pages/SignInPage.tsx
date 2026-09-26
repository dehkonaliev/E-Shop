import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Field } from '../components/ui'
import { useAuth } from '../context/auth-context'
import { fieldError } from '../lib/api'

export function SignInPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const from = (location.state as { from?: string } | null)?.from ?? '/account'
  if (user) return <Navigate to={from} replace />

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (caught) {
      setError(fieldError(caught, 'detail') ?? 'We could not sign you in.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page narrow">
      <div className="auth-card panel">
        <p className="eyebrow">Welcome back</p>
        <h1 className="headline">Sign in</h1>
        <p className="muted">Access your cart, orders and saved items.</p>
        <form onSubmit={(event) => void submit(event)}>
          {error ? <p className="error-note">{error}</p> : null}
          <Field label="Email" htmlFor="email">
            <input
              id="email"
              className="input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
            />
          </Field>
          <Field label="Password" htmlFor="password">
            <input
              id="password"
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
            />
          </Field>
          <button type="submit" className="btn btn-dark full" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="muted center">
          New here? <Link className="link-underline" to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
