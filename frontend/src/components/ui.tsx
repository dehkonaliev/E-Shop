import { Star } from 'lucide-react'
import type { ChangeEvent, ReactNode } from 'react'
import type { OrderStatus } from '../types'

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="spinner" role="status" aria-live="polite">
      <span className="spinner-ring" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  )
}

export function PageLoader({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="page-loader">
      <Spinner label={label} />
      <p className="muted">{label}</p>
    </div>
  )
}

export function ProductSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid-products">
      {Array.from({ length: count }, (_, index) => (
        <div className="skeleton-card" key={index}>
          <div className="skeleton skeleton-media" />
          <div className="skeleton skeleton-line" />
          <div className="skeleton skeleton-line short" />
        </div>
      ))}
    </div>
  )
}

export function Stars({ value, size = 14 }: { value: number; size?: number }) {
  return (
    <span className="stars" aria-label={`Rated ${value.toFixed(1)} out of 5`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          size={size}
          strokeWidth={1.6}
          className={star <= Math.round(value) ? 'star filled' : 'star'}
        />
      ))}
    </span>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <p className="muted">{description}</p>
      {action}
    </div>
  )
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-note" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="btn btn-ghost btn-sm" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  )
}

export function Field({
  label,
  hint,
  error,
  children,
  htmlFor,
}: {
  label: string
  hint?: string
  error?: string | null
  children: ReactNode
  htmlFor?: string
}) {
  return (
    <div className="field">
      <div className="field-head">
        <label className="label" htmlFor={htmlFor}>
          {label}
        </label>
        {hint ? <span className="hint">{hint}</span> : null}
      </div>
      {children}
      {error ? <p className="field-error">{error}</p> : null}
    </div>
  )
}

export function QuantityStepper({
  value,
  min = 1,
  max = 99,
  onChange,
}: {
  value: number
  min?: number
  max?: number
  onChange: (next: number) => void
}) {
  const handle = (event: ChangeEvent<HTMLInputElement>) => {
    const next = Number.parseInt(event.target.value, 10)
    if (Number.isNaN(next)) return
    onChange(Math.min(max, Math.max(min, next)))
  }

  return (
    <div className="qty">
      <button
        type="button"
        aria-label="Decrease quantity"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
      >
        −
      </button>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={handle}
        aria-label="Quantity"
      />
      <button
        type="button"
        aria-label="Increase quantity"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
      >
        +
      </button>
    </div>
  )
}

const statusLabels: Record<OrderStatus, string> = {
  pending: 'Pending',
  shipping: 'On its way',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export function StatusPill({ status, display }: { status: OrderStatus; display?: string }) {
  return <span className={`status-pill ${status}`}>{display ?? statusLabels[status]}</span>
}
