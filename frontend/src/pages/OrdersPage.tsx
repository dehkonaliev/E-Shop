import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState, ErrorNote, PageLoader, StatusPill } from '../components/ui'
import { useAuth } from '../context/auth-context'
import { api } from '../lib/api'
import { formatDateTime, formatPrice, pluralize } from '../lib/format'
import type { Order, OrderStatus } from '../types'

const filters: { value: OrderStatus | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'shipping', label: 'On its way' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

export function OrdersPage() {
  const { user } = useAuth()
  const [orders, setOrders] = useState<Order[] | null>(null)
  const [status, setStatus] = useState<OrderStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async (nextStatus: OrderStatus | '') => {
    try {
      const result = await api.orders.list({ status: nextStatus || undefined })
      setOrders(result.results)
    } catch {
      setError('We could not load your orders.')
      setOrders([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load(status)
  }, [status])

  const retry = () => {
    setError(null)
    setLoading(true)
    void load(status)
  }

  const isAdmin = user?.role === 'admin'

  return (
    <div className="container page">
      <header className="page-head">
        <p className="eyebrow">{isAdmin ? 'All orders' : 'Your orders'}</p>
        <h1 className="headline">Order history</h1>
        <p className="lead lead-small">
          {isAdmin
            ? 'Every order across the store, newest first.'
            : 'Track shipments and revisit past purchases.'}
        </p>
      </header>

      <div className="chip-row">
        {filters.map((filter) => (
          <button
            key={filter.value}
            type="button"
            className={`chip ${status === filter.value ? 'active' : ''}`}
            onClick={() => {
              setError(null)
              setLoading(true)
              setStatus(filter.value)
            }}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {error ? <ErrorNote message={error} onRetry={retry} /> : null}
      {loading ? (
        <PageLoader label="Loading orders" />
      ) : orders && orders.length > 0 ? (
        <div className="orders">
          {orders.map((order) => (
            <article className="order panel" key={order.id}>
              <header className="order-head">
                <div>
                  <p className="order-id">Order #{order.id}</p>
                  <p className="muted">{formatDateTime(order.created_at)}</p>
                </div>
                <div className="order-head-right">
                  <StatusPill status={order.status} display={order.status_display} />
                  <p className="order-total">{formatPrice(order.total_price)}</p>
                </div>
              </header>
              <div className="order-items">
                {order.items.map((item) => (
                  <div className="order-line" key={item.id}>
                    <Link className="order-line-name" to={`/product/${item.product}`}>
                      {item.product_name}
                    </Link>
                    <span className="muted">
                      {item.quantity} × {formatPrice(item.price_at_that_time)}
                    </span>
                    <span>{formatPrice(item.line_total)}</span>
                  </div>
                ))}
              </div>
              <footer className="order-foot">
                <p className="muted address">
                  <span className="eyebrow">Ships to</span>
                  {order.shipping_address}
                </p>
                <p className="muted">
                  {order.items.reduce((total, item) => total + item.quantity, 0)}{' '}
                  {pluralize(
                    order.items.reduce((total, item) => total + item.quantity, 0),
                    'item',
                  )}
                </p>
              </footer>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No orders here"
          description="When you place an order it will appear here with live status updates."
          action={
            <Link className="btn btn-dark btn-sm" to="/shop">
              Browse the catalogue
            </Link>
          }
        />
      )}
    </div>
  )
}
