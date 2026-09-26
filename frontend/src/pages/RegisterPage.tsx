import { ArrowLeft, ArrowRight, Check, Mail } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Field } from '../components/ui'
import { useAuth } from '../context/auth-context'
import { api, fieldError } from '../lib/api'

type Step = 'email' | 'code' | 'activate'

const stepOrder: Step[] = ['email', 'code', 'activate']

export function RegisterPage() {
  const { applySession, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/shop'

  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [activationToken, setActivationToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user && step !== 'activate') return <Navigate to={from} replace />

  const sendCode = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.auth.register(email)
      setStep('code')
    } catch (caught) {
      setError(fieldError(caught, 'email') ?? 'We could not send the code.')
    } finally {
      setBusy(false)
    }
  }

  const confirmCode = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const result = await api.auth.confirmCode(email, code)
      setActivationToken(result.activation_token)
      setStep('activate')
    } catch (caught) {
      setError(fieldError(caught, 'code') ?? 'That code is not valid.')
    } finally {
      setBusy(false)
    }
  }

  const activate = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const response = await api.auth.activate({
        token: activationToken,
        username,
        password,
      })
      applySession(response)
      navigate(from, { replace: true })
    } catch (caught) {
      setError(fieldError(caught, 'token') ?? 'We could not finish your account.')
    } finally {
      setBusy(false)
    }
  }

  const activeIndex = stepOrder.indexOf(step)

  return (
    <div className="container page narrow">
      <div className="auth-card panel">
        <p className="eyebrow">Create an account</p>
        <h1 className="headline">Join E-Shop</h1>

        <ol className="steps" aria-label="Registration progress">
          {stepOrder.map((item, index) => (
            <li
              key={item}
              className={index < activeIndex ? 'done' : index === activeIndex ? 'active' : ''}
            >
              <span className="step-dot">
                {index < activeIndex ? <Check size={12} /> : index + 1}
              </span>
              {item === 'email' ? 'Email' : item === 'code' ? 'Verify' : 'Details'}
            </li>
          ))}
        </ol>

        {error ? <p className="error-note">{error}</p> : null}

        {step === 'email' ? (
          <form onSubmit={(event) => void sendCode(event)}>
            <Field label="Email address" htmlFor="email" hint="We send a 6-digit code">
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
            <button type="submit" className="btn btn-dark full" disabled={busy}>
              {busy ? 'Sending…' : 'Send verification code'}
              <Mail size={16} />
            </button>
          </form>
        ) : null}

        {step === 'code' ? (
          <form onSubmit={(event) => void confirmCode(event)}>
            <p className="muted">
              We sent a 6-digit code to <strong>{email}</strong>. Enter it below to continue.
            </p>
            <Field label="Verification code" htmlFor="code">
              <input
                id="code"
                className="input code-input"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                inputMode="numeric"
                maxLength={6}
                required
              />
            </Field>
            <button type="submit" className="btn btn-dark full" disabled={busy}>
              {busy ? 'Verifying…' : 'Verify code'}
              <ArrowRight size={16} />
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm full"
              onClick={() => setStep('email')}
            >
              <ArrowLeft size={14} />
              Use a different email
            </button>
          </form>
        ) : null}

        {step === 'activate' ? (
          <form onSubmit={(event) => void activate(event)}>
            <Field label="Username" htmlFor="username">
              <input
                id="username"
                className="input"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
                autoComplete="username"
              />
            </Field>
            <Field label="Password" htmlFor="password" hint="At least 8 characters">
              <input
                id="password"
                className="input"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                autoComplete="new-password"
              />
            </Field>
            <button type="submit" className="btn btn-dark full" disabled={busy}>
              {busy ? 'Creating account…' : 'Create account'}
              <ArrowRight size={16} />
            </button>
          </form>
        ) : null}

        <p className="muted center">
          Already have an account? <Link className="link-underline" to="/signin">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
