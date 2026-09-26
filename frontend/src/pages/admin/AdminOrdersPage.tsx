import { useCallback, useEffect, useState } from 'react'
import {
  AdminPageHeader,
  AdminTable,
  EmptyRow,
  Notice,
  Pager,
  Panel,
} from '../../components/admin/AdminUI'
import { ErrorNote, PageLoader } from '../../components/ui'
import { api, ApiError } from '../../lib/api'
import { formatDateTime, formatPrice, pluralize } from '../../lib/format'
import type { Order, OrderStatus, Paginated } from '../../types'

const PAGE_SIZE = 15

const filters: { value: OrderStatus | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'shipping', label: 'On its way' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

const transitions: Record<OrderStatus, OrderStatus[]> = {
  pending: ['shipping', 'cancelled'],
  shipping: ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
}

export function AdminOrdersPage() {
  const [data, setData] = useState<Paginated<Order> | null>(null)
  const [status, setStatus] = useState<OrderStatus | ''>('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [flash, setFlash] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await api.orders.list({ status: status || undefined, page, page_size: PAGE_SIZE }))
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Orders could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [status, page])

  useEffect(() => {
    void load()
  }, [load])

  const changeStatus = async (order: Order, next: OrderStatus) => {
    setBusyId(order.id)
    setError(null)
    try {
      await api.admin.setOrderStatus(order.id, next)
      setFlash(`Order #${order.id} is now ${next}.`)
      await load()    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Status could not be changed.')
    } finally {
      setBusyId(null)
    }
  }

  const count = data?.count ?? 0

  return (
    <div className="admin-stack">
      <AdminPageHeader
        eyebrow="Fulfilment"
        title="Orders"
        description="Every order from every customer. Move them through fulfilment."
        actions={
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => void load()}>
            Refresh
          </button>
        }
      />

      {flash ? <Notice tone="success" onClose={() => setFlash(null)}>{flash}</Notice> : null}
      {error ? <ErrorNote message={error} onRetry={() => void load()} /> : null}

      <Panel
        title="All orders"
        description={`${count} ${pluralize(count, 'order')}`}
        action={
          <div className="segmented" role="group" aria-label="Filter by status">
            {filters.map((filter) => (
              <button
                key={filter.value || 'all'}
                type="button"
                className={status === filter.value ? 'active' : ''}
                onClick={() => {
                  setPage(1)
                  setStatus(filter.value)
                }}
              >
                {filter.label}
              </button>
            ))}
          </div>
        }
      >
        {loading && !data ? <PageLoader label="Loading orders" /> : null}
        {data ? (
          <>
            <AdminTable>
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Items</th>
                  <th>Status</th>
                  <th>Move to</th>
                  <th className="num">Total</th>
                  <th className="num">Placed</th>
                </tr>
              </thead>
              <tbody>
                {data.results.length === 0 ? (
                  <EmptyRow colSpan={7}>No orders with this status.</EmptyRow>
                ) : (
                  data.results.map((order) => {
                    const options = transitions[order.status]
                    return (
                      <tr key={order.id}>
                        <td>
                          <span className="cell-strong">#{order.id}</span>
                          <span className="cell-sub muted">{order.uuid.slice(0, 8)}</span>
                        </td>
                        <td>
                          <span className="cell-strong">{order.user_username}</span>
                          <span className="cell-sub muted">{order.user_email || '—'}</span>
                        </td>
                        <td>
                          {order.items.length === 0 ? (
                            <span className="muted">{order.item_count}</span>
                          ) : (
                            <span className="cell-lines">
                              {order.items.slice(0, 2).map((item) => (
                                <span key={item.id} className="muted">
                                  {item.quantity} × {item.product_name}
                                </span>
                              ))}
                              {order.items.length > 2 ? (
                                <span className="muted">+{order.items.length - 2} more</span>
                              ) : null}
                            </span>
                          )}
                        </td>
                        <td>
                          <span className={`status-pill ${order.status}`}>{order.status_display}</span>
                        </td>
                        <td>
                          {options.length === 0 ? (
                            <span className="muted">Final</span>
                          ) : (
                            <div className="status-actions">
                              {options.map((option) => (
                                <button
                                  key={option}
                                  type="button"
                                  className="btn btn-ghost btn-sm"
                                  disabled={busyId === order.id}
                                  onClick={() => void changeStatus(order, option)}
                                >
                                  {option === 'shipping'
                                    ? 'Ship'
                                    : option === 'completed'
                                      ? 'Complete'
                                      : 'Cancel'}
                                </button>
                              ))}
                            </div>
                          )}
                        </td>
                        <td className="num">{formatPrice(order.total_price)}</td>
                        <td className="num muted">{formatDateTime(order.created_at)}</td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </AdminTable>
            <Pager page={page} count={count} pageSize={PAGE_SIZE} onChange={setPage} />
          </>
        ) : null}
      </Panel>
    </div>
  )
}
