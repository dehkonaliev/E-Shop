import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AdminPageHeader,
  AdminTable,
  EmptyRow,
  Notice,
  Panel,
  StatCard,
} from '../../components/admin/AdminUI'
import { PageLoader } from '../../components/ui'
import { api, ApiError } from '../../lib/api'
import { formatDate, formatDateTime, formatPrice, pluralize } from '../../lib/format'
import type { DashboardStats } from '../../types'

export function AdminDashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      setStats(await api.admin.dashboard())
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Dashboard could not be loaded.')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  if (!stats) {
    if (error) {
      return (
        <div>
          <AdminPageHeader title="Dashboard" description="Sales, stock and customer activity" />
          <Notice tone="error">{error}</Notice>
        </div>
      )
    }
    return <PageLoader label="Loading dashboard" />
  }

  const peak = Math.max(...stats.sales_by_day.map((point) => Number(point.revenue)), 1)
  const categoryPeak = Math.max(...stats.category_breakdown.map((row) => Number(row.revenue)), 1)

  return (
    <div className="admin-stack">
      <AdminPageHeader
        eyebrow="Overview"
        title="Dashboard"
        description={`Last refreshed ${formatDateTime(stats.generated_at)}`}
        actions={
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => void load()}>
            Refresh
          </button>
        }
      />

      <div className="stat-grid">
        <StatCard
          label="Revenue"
          value={formatPrice(stats.orders.revenue)}
          hint={`${stats.orders.completed} completed ${pluralize(stats.orders.completed, 'order')}`}
          tone="positive"
        />
        <StatCard
          label="Orders"
          value={String(stats.orders.total)}
          hint={`${stats.orders.pending} pending · ${stats.orders.shipping} on the way`}
        />
        <StatCard
          label="Units sold"
          value={String(stats.sales.units)}
          hint={`Average order ${formatPrice(stats.sales.average_order)}`}
        />
        <StatCard
          label="Products"
          value={String(stats.products.total)}
          hint={`${stats.products.low_stock} low on stock · ${stats.products.sold_out} sold out`}
          tone={stats.products.low_stock > 0 ? 'warning' : 'neutral'}
        />
        <StatCard
          label="Stock value"
          value={formatPrice(stats.products.catalogue_value)}
          hint={`${stats.products.units_in_stock} units on hand`}
        />
        <StatCard
          label="Customers"
          value={String(stats.customers.total)}
          hint={`${stats.customers.with_orders} have ordered · ${stats.customers.new_this_month} new this month`}
        />
      </div>

      <Panel
        title="Sales, last 14 days"
        description={`${stats.sales.units} ${pluralize(stats.sales.units, 'unit')} · ${formatPrice(stats.sales.revenue)}`}
      >
        <div className="chart" role="img" aria-label="Revenue for the last fourteen days">
          {stats.sales_by_day.map((point) => {
            const value = Number(point.revenue)
            const height = Math.round((value / peak) * 100)
            return (
              <div className="chart-col" key={point.date}>
                <div
                  className="chart-bar"
                  style={{ height: `${Math.max(height, value > 0 ? 4 : 1)}%` }}
                  title={`${formatDate(point.date)} · ${formatPrice(value)} · ${point.orders} ${pluralize(point.orders, 'order')}`}
                />
                <span className="chart-label">{formatDate(point.date).slice(0, 6)}</span>
              </div>
            )
          })}
        </div>
      </Panel>

      <div className="admin-columns">
        <Panel
          title="Best sellers"
          description="Units sold by product"
          action={
            <Link className="btn btn-ghost btn-sm" to="/admin/products">
              Manage products
            </Link>
          }
        >
          <AdminTable>
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th className="num">Units</th>
                <th className="num">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {stats.top_products.length === 0 ? (
                <EmptyRow colSpan={4}>No sales recorded yet.</EmptyRow>
              ) : (
                stats.top_products.map((row) => (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td className="muted">{row.category ?? '—'}</td>
                    <td className="num">{row.units_sold}</td>
                    <td className="num">{formatPrice(row.revenue)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </AdminTable>
        </Panel>

        <Panel
          title="Top customers"
          description="By number of orders"
          action={
            <Link className="btn btn-ghost btn-sm" to="/admin/customers">
              All customers
            </Link>
          }
        >
          <AdminTable>
            <thead>
              <tr>
                <th>Customer</th>
                <th className="num">Orders</th>
                <th className="num">Spent</th>
              </tr>
            </thead>
            <tbody>
              {stats.top_customers.length === 0 ? (
                <EmptyRow colSpan={3}>No customer orders yet.</EmptyRow>
              ) : (
                stats.top_customers.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <span className="cell-strong">{row.username}</span>
                      <span className="cell-sub muted">{row.email}</span>
                    </td>
                    <td className="num">{row.order_count}</td>
                    <td className="num">{formatPrice(row.total_spent)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </AdminTable>
        </Panel>
      </div>

      <div className="admin-columns">
        <Panel
          title="Recent orders"
          description="Newest first"
          action={
            <Link className="btn btn-ghost btn-sm" to="/admin/orders">
              All orders
            </Link>
          }
        >
          <AdminTable>
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Status</th>
                <th className="num">Total</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_orders.length === 0 ? (
                <EmptyRow colSpan={4}>No orders yet.</EmptyRow>
              ) : (
                stats.recent_orders.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <span className="cell-strong">#{row.id}</span>
                      <span className="cell-sub muted">{formatDateTime(row.created_at)}</span>
                    </td>
                    <td>{row.username}</td>
                    <td>
                      <span className={`status-pill ${row.status}`}>{row.status_display}</span>
                    </td>
                    <td className="num">{formatPrice(row.total_price)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </AdminTable>
        </Panel>

        <Panel
          title="Low stock"
          description="Five units or fewer"
          action={
            <Link className="btn btn-ghost btn-sm" to="/admin/products?ordering=stock">
              Restock
            </Link>
          }
        >
          <AdminTable>
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th className="num">Stock</th>
              </tr>
            </thead>
            <tbody>
              {stats.low_stock.length === 0 ? (
                <EmptyRow colSpan={3}>Every product is comfortably stocked.</EmptyRow>
              ) : (
                stats.low_stock.map((row) => (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td className="muted">{row.category ?? '—'}</td>
                    <td className="num">
                      <span className={`badge ${row.stock === 0 ? 'danger' : 'warning'}`}>
                        {row.stock}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </AdminTable>
        </Panel>
      </div>

      <Panel title="Revenue by category" description="All time, cancelled orders excluded">
        {stats.category_breakdown.length === 0 ? (
          <p className="muted">No categories yet. Create one to start organising products.</p>
        ) : (
          <div className="bar-list">
            {stats.category_breakdown.map((row) => (
              <div className="bar-row" key={row.id}>
                <div className="bar-head">
                  <span className="cell-strong">{row.name}</span>
                  <span className="muted">
                    {row.products} {pluralize(row.products, 'product')} · {row.units_sold} sold ·{' '}
                    {formatPrice(row.revenue)}
                  </span>
                </div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${Math.max(2, Math.round((Number(row.revenue) / categoryPeak) * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
