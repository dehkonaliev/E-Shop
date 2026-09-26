import { useCallback, useEffect, useState } from 'react'
import { Search } from 'lucide-react'
import {
  AdminPageHeader,
  AdminTable,
  EmptyRow,
  Modal,
  Notice,
  Pager,
  Panel,
  StatCard,
} from '../../components/admin/AdminUI'
import { ErrorNote, PageLoader } from '../../components/ui'
import { api, ApiError } from '../../lib/api'
import { formatDate, formatDateTime, formatPrice, pluralize } from '../../lib/format'
import type {
  CustomerOrder,
  CustomerProfile,
  CustomerReport,
  Paginated,
} from '../../types'

const PAGE_SIZE = 12
const ORDER_PAGE_SIZE = 8

const orderingOptions = [
  { value: '-order_count', label: 'Most orders' },
  { value: '-spent', label: 'Highest spend' },
  { value: '-date_joined', label: 'Newest customers' },
  { value: 'date_joined', label: 'Oldest customers' },
  { value: 'username', label: 'Name A–Z' },
]

export function AdminCustomersPage() {
  const [data, setData] = useState<Paginated<CustomerReport> | null>(null)
  const [search, setSearch] = useState('')
  const [term, setTerm] = useState('')
  const [ordering, setOrdering] = useState('-order_count')
  const [withOrders, setWithOrders] = useState(false)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<CustomerReport | null>(null)
  const [profile, setProfile] = useState<CustomerProfile | null>(null)
  const [orders, setOrders] = useState<Paginated<CustomerOrder> | null>(null)
  const [orderPage, setOrderPage] = useState(1)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(
        await api.admin.customers({
          page,
          page_size: PAGE_SIZE,
          search: term,
          ordering,
          has_orders: withOrders ? 'true' : undefined,
        }),
      )
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Customers could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [page, term, ordering, withOrders])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPage(1)
      setTerm(search.trim())
    }, 300)
    return () => window.clearTimeout(timer)
  }, [search])

  const loadOrders = useCallback(async (id: number, nextPage: number) => {
    setDetailLoading(true)
    setDetailError(null)
    try {
      const [detail, list] = await Promise.all([
        api.admin.customer(id),
        api.admin.customerOrders(id, { page: nextPage, page_size: ORDER_PAGE_SIZE }),
      ])
      setProfile(detail)
      setOrders(list)
    } catch (caught) {
      setDetailError(
        caught instanceof ApiError ? caught.message : 'This customer could not be loaded.',
      )
      setProfile(null)
      setOrders(null)
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const openCustomer = (row: CustomerReport) => {
    setSelected(row)
    setOrderPage(1)
    void loadOrders(row.id, 1)
  }

  const closeCustomer = () => {
    setSelected(null)
    setProfile(null)
    setOrders(null)
    setDetailError(null)
  }

  const rows = data?.results ?? []
  const totals = rows.reduce(
    (accumulator, row) => {
      accumulator.spent += Number(row.total_spent)
      accumulator.orders += row.order_count
      if (row.order_count > 0) accumulator.buyers += 1
      return accumulator
    },
    { spent: 0, orders: 0, buyers: 0 },
  )

  return (
    <div className="admin-stack">
      <AdminPageHeader
        eyebrow="People"
        title="Customers"
        description="Who shops with you, how often, and what they spend."
        actions={
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => void load()}>
            Refresh
          </button>
        }
      />

      {error ? <ErrorNote message={error} onRetry={() => void load()} /> : null}

      <div className="stat-grid compact">
        <StatCard label="Shown" value={String(data?.count ?? 0)} hint="Customer accounts" />
        <StatCard label="Buyers" value={String(totals.buyers)} hint="With at least one order" />
        <StatCard label="Orders" value={String(totals.orders)} hint="Across this page" />
        <StatCard
          label="Spend"
          value={formatPrice(totals.spent)}
          hint="Excludes cancelled orders"
          tone="positive"
        />
      </div>

      <Panel
        title="Customer accounts"
        description={data ? `${data.count} ${pluralize(data.count, 'customer')}` : undefined}
        action={
          <div className="toolbar">
            <div className="search">
              <Search size={15} strokeWidth={1.8} aria-hidden="true" />
              <input
                type="search"
                value={search}
                placeholder="Search name or email"
                aria-label="Search customers"
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={withOrders}
                onChange={(event) => {
                  setPage(1)
                  setWithOrders(event.target.checked)
                }}
              />
              Buyers only
            </label>
            <select
              className="select"
              value={ordering}
              aria-label="Sort customers"
              onChange={(event) => {
                setPage(1)
                setOrdering(event.target.value)
              }}
            >
              {orderingOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        }
      >
        {loading && !data ? <PageLoader label="Loading customers" /> : null}
        {data ? (
          <>
            <AdminTable>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Joined</th>
                  <th className="num">Orders</th>
                  <th>Status mix</th>
                  <th className="num">Spent</th>
                  <th className="num">Last order</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <EmptyRow colSpan={7}>No customers match these filters.</EmptyRow>
                ) : (
                  rows.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <span className="cell-strong">
                          {row.first_name || row.last_name
                            ? `${row.first_name} ${row.last_name}`.trim()
                            : row.username}
                        </span>
                        <span className="cell-sub muted">
                          {row.username} · {row.email || 'no email'}
                        </span>
                      </td>
                      <td className="muted">{formatDate(row.date_joined)}</td>
                      <td className="num">{row.order_count}</td>
                      <td>
                        <div className="status-mix">
                          {row.pending_orders > 0 ? (
                            <span className="badge warning">{row.pending_orders} pending</span>
                          ) : null}
                          {row.shipping_orders > 0 ? (
                            <span className="badge info">{row.shipping_orders} shipping</span>
                          ) : null}
                          {row.completed_orders > 0 ? (
                            <span className="badge positive">
                              {row.completed_orders} done
                            </span>
                          ) : null}
                          {row.cancelled_orders > 0 ? (
                            <span className="badge danger">{row.cancelled_orders} cancelled</span>
                          ) : null}
                          {row.order_count === 0 ? <span className="muted">No orders yet</span> : null}
                        </div>
                      </td>
                      <td className="num">{formatPrice(row.total_spent)}</td>
                      <td className="num muted">
                        {row.last_order_at ? formatDateTime(row.last_order_at) : '—'}
                      </td>
                      <td className="actions">
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => openCustomer(row)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </AdminTable>
            <Pager
              page={page}
              count={data.count}
              pageSize={PAGE_SIZE}
              onChange={(next) => {
                setPage(next)
                setError(null)
              }}
            />
            {rows.length > 0 ? (
              <Notice tone="info">
                Totals above cover the current page only. Use sorting and search to review other
                customers.
              </Notice>
            ) : null}
          </>
        ) : null}
      </Panel>

      <Modal
        open={selected !== null}
        wide
        title={selected ? (selected.first_name || selected.last_name
          ? `${selected.first_name} ${selected.last_name}`.trim()
          : selected.username) : ''}
        description={selected ? `Customer since ${formatDate(selected.date_joined)}` : undefined}
        onClose={closeCustomer}
      >
        {detailError ? <Notice tone="error">{detailError}</Notice> : null}
        {detailLoading && !profile ? <PageLoader label="Loading customer" /> : null}

        {profile ? (
          <>
            <div className="profile-grid">
              <div className="profile-block">
                <p className="eyebrow">Profile</p>
                <dl>
                  <div>
                    <dt>Username</dt>
                    <dd>{profile.username}</dd>
                  </div>
                  <div>
                    <dt>Full name</dt>
                    <dd>{profile.full_name || '—'}</dd>
                  </div>
                  <div>
                    <dt>Email</dt>
                    <dd>{profile.email || '—'}</dd>
                  </div>
                  <div>
                    <dt>Phone</dt>
                    <dd>{profile.phone_number || '—'}</dd>
                  </div>
                  <div>
                    <dt>Age</dt>
                    <dd>{profile.age ?? '—'}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>
                      <span className={`badge ${profile.is_active ? 'positive' : 'danger'}`}>
                        {profile.is_active ? 'Active' : 'Blocked'}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>Joined</dt>
                    <dd>{formatDate(profile.date_joined)}</dd>
                  </div>
                  <div>
                    <dt>Last login</dt>
                    <dd>
                      {profile.last_login ? formatDateTime(profile.last_login) : 'Never'}
                    </dd>
                  </div>
                </dl>
              </div>
              <div className="profile-block">
                <p className="eyebrow">Order history</p>
                <div className="stat-grid compact">
                  <StatCard label="Orders" value={String(profile.order_count)} />
                  <StatCard label="Spent" value={formatPrice(profile.total_spent)} tone="positive" />
                </div>
                <div className="status-mix">
                  <span className="badge warning">{profile.pending_orders} pending</span>
                  <span className="badge info">{profile.shipping_orders} shipping</span>
                  <span className="badge positive">{profile.completed_orders} completed</span>
                  <span className="badge danger">{profile.cancelled_orders} cancelled</span>
                </div>
              </div>
            </div>

            {orders && orders.results.length > 0 ? (
              <div className="profile-orders">
                <AdminTable>
                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Placed</th>
                      <th>Status</th>
                      <th className="num">Items</th>
                      <th className="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.results.map((order) => (
                      <tr key={order.id}>
                        <td>
                          <span className="cell-strong">#{order.id}</span>
                          <span className="cell-sub muted">{order.shipping_address}</span>
                        </td>
                        <td className="muted">{formatDateTime(order.created_at)}</td>
                        <td>
                          <span className={`status-pill ${order.status}`}>
                            {order.status_display}
                          </span>
                        </td>
                        <td className="num">{order.item_count}</td>
                        <td className="num">{formatPrice(order.total_price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </AdminTable>
                <Pager
                  page={orderPage}
                  count={orders.count}
                  pageSize={ORDER_PAGE_SIZE}
                  onChange={(next) => {
                    setOrderPage(next)
                    if (selected) void loadOrders(selected.id, next)
                  }}
                />
              </div>
            ) : null}

            {orders && orders.results.length === 0 ? (
              <p className="muted">This customer has not placed any orders yet.</p>
            ) : null}
          </>
        ) : null}
      </Modal>
    </div>
  )
}
