import {
  FolderTree,
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  ShoppingBag,
  Users,
  X,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../../context/auth-context'
import { initials } from '../../lib/format'
import '../../admin.css'

const navigation = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/products', label: 'Products', icon: Package, end: false },
  { to: '/admin/categories', label: 'Categories', icon: FolderTree, end: false },
  { to: '/admin/orders', label: 'Orders', icon: ShoppingBag, end: false },
  { to: '/admin/customers', label: 'Customers', icon: Users, end: false },
]

export function AdminLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <div className="admin-shell">
      <button
        type="button"
        className="admin-burger"
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? 'Close navigation' : 'Open navigation'}
      >
        <Menu size={18} strokeWidth={1.8} />
      </button>

      <aside className={`admin-sidebar ${open ? 'open' : ''}`}>
        <div className="admin-sidebar-head">
          <Link className="brand" to="/admin" onClick={() => setOpen(false)}>
            <span className="brand-mark" aria-hidden="true">
              E
            </span>
            <span className="brand-name">E-Shop</span>
          </Link>
          <p className="admin-tag">Admin</p>
          <button
            type="button"
            className="icon-btn admin-close"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          >
            <X size={17} strokeWidth={1.8} />
          </button>
        </div>

        <nav className="admin-nav" aria-label="Admin">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setOpen(false)}
                className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={16} strokeWidth={1.7} aria-hidden="true" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="admin-sidebar-foot">
          {user ? (
            <div className="admin-user">
              <span className="avatar" aria-hidden="true">
                {initials(user.first_name || user.username)}
              </span>
              <div>
                <p className="admin-user-name">{user.username}</p>
                <p className="muted">{user.email}</p>
              </div>
              <button
                type="button"
                className="icon-btn"
                onClick={() => void logout()}
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut size={16} strokeWidth={1.7} />
              </button>
            </div>
          ) : null}
        </div>
      </aside>

      {open ? <div className="admin-scrim" onClick={() => setOpen(false)} /> : null}
      <main className="admin-main">{children}</main>
    </div>
  )
}
