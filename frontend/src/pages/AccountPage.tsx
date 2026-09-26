import { useState } from 'react'
import { Field } from '../components/ui'
import { useAuth } from '../context/auth-context'
import { fieldError } from '../lib/api'
import { initials } from '../lib/format'
import type { User } from '../types'

interface ProfileForm {
  username: string
  first_name: string
  last_name: string
  phone_number: string
  age: string
}

function toForm(user: User | null): ProfileForm {
  return {
    username: user?.username ?? '',
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
    phone_number: user?.phone_number ?? '',
    age: user?.age === null || user?.age === undefined ? '' : String(user.age),
  }
}

export function AccountPage() {
  const { user, updateProfile } = useAuth()
  const [form, setForm] = useState<ProfileForm>(() => toForm(user))
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!user) return null

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    setStatus(null)
    try {
      await updateProfile({
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        phone_number: form.phone_number,
        age: form.age === '' ? null : Number.parseInt(form.age, 10),
      })
      setStatus('Your profile has been updated.')
    } catch (caught) {
      setError(fieldError(caught, 'username') ?? 'We could not save your profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="container page">
      <header className="page-head">
        <p className="eyebrow">Account</p>
        <h1 className="headline">Your details</h1>
        <p className="lead lead-small">Keep your contact information up to date for deliveries.</p>
      </header>

      <div className="account-grid">
        <aside className="panel account-card">
          <span className="avatar avatar-lg">{initials(user.first_name || user.username)}</span>
          <h3>{user.username}</h3>
          <p className="muted">{user.email}</p>
          <p className="eyebrow">{user.role === 'admin' ? 'Administrator' : 'Customer'}</p>
          <p className="muted small">
            Signed in with a JSON Web Token. Sessions last 15 minutes and refresh automatically.
          </p>
        </aside>

        <form className="panel account-form" onSubmit={(event) => void submit(event)}>
          {error ? <p className="error-note">{error}</p> : null}
          {status ? <p className="success-note">{status}</p> : null}
          <Field label="Username" htmlFor="username" error={fieldError(error, 'username')}>
            <input
              id="username"
              className="input"
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              required
            />
          </Field>
          <div className="form-row">
            <Field label="First name" htmlFor="first_name">
              <input
                id="first_name"
                className="input"
                value={form.first_name}
                onChange={(event) => setForm({ ...form, first_name: event.target.value })}
              />
            </Field>
            <Field label="Last name" htmlFor="last_name">
              <input
                id="last_name"
                className="input"
                value={form.last_name}
                onChange={(event) => setForm({ ...form, last_name: event.target.value })}
              />
            </Field>
          </div>
          <div className="form-row">
            <Field label="Phone" htmlFor="phone_number">
              <input
                id="phone_number"
                className="input"
                value={form.phone_number}
                onChange={(event) => setForm({ ...form, phone_number: event.target.value })}
              />
            </Field>
            <Field label="Age" htmlFor="age">
              <input
                id="age"
                className="input"
                type="number"
                min="0"
                max="120"
                value={form.age}
                onChange={(event) => setForm({ ...form, age: event.target.value })}
              />
            </Field>
          </div>
          <button type="submit" className="btn btn-dark" disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </div>
    </div>
  )
}
