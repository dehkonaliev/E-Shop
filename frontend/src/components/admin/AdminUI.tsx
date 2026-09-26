import { Check, Info, TriangleAlert, X } from 'lucide-react'
import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { createPortal } from 'react-dom'

export function AdminPageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <header className="admin-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p className="muted">{description}</p> : null}
      </div>
      {actions ? <div className="admin-header-actions">{actions}</div> : null}
    </header>
  )
}

export function StatCard({
  label,
  value,
  hint,
  tone = 'neutral',
}: {
  label: string
  value: string
  hint?: string
  tone?: 'neutral' | 'positive' | 'warning' | 'danger'
}) {
  return (
    <div className={`stat-card ${tone}`}>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {hint ? <p className="stat-hint">{hint}</p> : null}
    </div>
  )
}

export function Panel({
  title,
  description,
  action,
  children,
  className = '',
}: {
  title: string
  description?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {description ? <p className="muted">{description}</p> : null}
        </div>
        {action ? <div className="panel-action">{action}</div> : null}
      </div>
      {children}
    </section>
  )
}

export function Notice({
  tone,
  children,
  onClose,
}: {
  tone: 'success' | 'error' | 'info'
  children: ReactNode
  onClose?: () => void
}) {
  const Icon = tone === 'success' ? Check : tone === 'error' ? TriangleAlert : Info
  return (
    <div className={`notice ${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
      <p>{children}</p>
      {onClose ? (
        <button type="button" onClick={onClose} aria-label="Dismiss message">
          <X size={15} strokeWidth={1.8} />
        </button>
      ) : null}
    </div>
  )
}

export function AdminTable({ children }: { children: ReactNode }) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">{children}</table>
    </div>
  )
}

export function Modal({
  open,
  title,
  description,
  onClose,
  children,
  footer,
  wide = false,
}: {
  open: boolean
  title: string
  description?: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  wide?: boolean
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = previous
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className={`modal ${wide ? 'wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-head">
          <div>
            <h2>{title}</h2>
            {description ? <p className="muted">{description}</p> : null}
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={18} strokeWidth={1.8} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer ? <div className="modal-foot">{footer}</div> : null}
      </div>
    </div>,
    document.body,
  )
}

export function Pager({
  page,
  count,
  pageSize,
  onChange,
}: {
  page: number
  count: number
  pageSize: number
  onChange: (next: number) => void
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  if (count <= pageSize) return null
  return (
    <div className="pager">
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>
      <span className="muted">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </button>
    </div>
  )
}

export function EmptyRow({ colSpan, children }: { colSpan: number; children: ReactNode }) {
  return (
    <tr>
      <td colSpan={colSpan} className="admin-empty">
        {children}
      </td>
    </tr>
  )
}
