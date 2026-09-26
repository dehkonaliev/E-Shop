import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { hasAdminAccess } from '../lib/access'
import { useAuth } from '../context/auth-context'
import { useCart } from '../context/cart-context'
import { initials } from '../lib/format'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [pathname])
  return null
}

function Wordmark() {
  return (
    <Link className="brand" to="/" aria-label="E-Shop home">
      <span className="brand-mark" aria-hidden="true">
        E
      </span>
      <span className="brand-name">E-Shop</span>
    </Link>
  )
}

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const container = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return
    const onClick = (event: MouseEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  if (!user) {
    return (
      <div className="nav-actions">
        <NavLink className="btn btn-ghost btn-sm" to="/signin">
          Sign in
        </NavLink>
        <NavLink className="btn btn-dark btn-sm hide-sm" to="/register">
          Create account
        </NavLink>
      </div>
    )
  }

  const admin = user.role === 'admin'

  return (
    <div className="user-menu" ref={container}>
      <button
        type="button"
        className="avatar"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Account menu"
      >
        {initials(user.first_name || user.username)}
      </button>
      {open ? (
        <div className="menu" role="menu">
          <div className="menu-head">
            <p className="menu-name">{user.username}</p>
            <p className="muted">{user.email}</p>
          </div>
          {admin ? (
            <Link className="menu-item" to="/admin" role="menuitem" onClick={() => setOpen(false)}>
              Admin panel
            </Link>
          ) : (
            <>
              <Link className="menu-item" to="/account" role="menuitem" onClick={() => setOpen(false)}>
                Account
              </Link>
              <Link className="menu-item" to="/orders" role="menuitem" onClick={() => setOpen(false)}>
                Orders
              </Link>
              <Link className="menu-item" to="/likes" role="menuitem" onClick={() => setOpen(false)}>
                Saved items
              </Link>
            </>
          )}
          <button
            type="button"
            className="menu-item danger"
            role="menuitem"
            onClick={() => {
              setOpen(false)
              void logout()
            }}
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  )
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { count } = useCart()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const admin = user ? hasAdminAccess(user) : false

  const cartTarget = () => {
    if (!user) {
      navigate('/signin', { state: { from: '/cart' } })
      return
    }
    navigate('/cart')
  }

  return (
    <div className="app-shell">
      <ScrollToTop />
      <div className="announce">
        <p>Complimentary shipping on orders over $150 · 30-day returns</p>
      </div>
      <header className="site-header">
        <div className="container header-inner">
          <button
            type="button"
            className="icon-btn mobile-only"
            aria-label="Open menu"
            onClick={() => setMenuOpen((value) => !value)}
          >
            <span className="burger" aria-hidden="true" />
          </button>
          <Wordmark />
          <nav className={`nav-links ${menuOpen ? 'open' : ''}`} aria-label="Primary">
            <NavLink to="/shop" onClick={() => setMenuOpen(false)}>
              Shop
            </NavLink>
            <NavLink to="/shop?ordering=-created_at" onClick={() => setMenuOpen(false)}>
              New arrivals
            </NavLink>
            <NavLink to="/shop?in_stock=true" onClick={() => setMenuOpen(false)}>
              In stock
            </NavLink>
            <NavLink to="/#philosophy" onClick={() => setMenuOpen(false)}>
              Our approach
            </NavLink>
          </nav>
          <div className="nav-actions">
            {admin ? (
              <NavLink className="btn btn-dark btn-sm" to="/admin">
                Admin panel
              </NavLink>
            ) : (
              <button type="button" className="cart-btn" onClick={cartTarget} aria-label="Open cart">
                <span>Cart</span>
                {count > 0 ? <span className="cart-count">{count}</span> : null}
              </button>
            )}
            <UserMenu />
          </div>
        </div>
      </header>
      <main className="site-main">{children}</main>
      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <Wordmark />
            <p className="muted footer-blurb">
              Considered goods, chosen for how they age. Built with Django and React.
            </p>
          </div>
          <div className="footer-col">
            <p className="eyebrow">Shop</p>
            <Link to="/shop">All products</Link>
            <Link to="/shop?in_stock=true">Ready to ship</Link>
            <Link to="/shop?ordering=price">Price ascending</Link>
          </div>
          <div className="footer-col">
            <p className="eyebrow">Account</p>
            <Link to="/account">Profile</Link>
            <Link to="/orders">Orders</Link>
            <Link to="/likes">Saved items</Link>
          </div>
          <div className="footer-col">
            <p className="eyebrow">Company</p>
            <Link to="/#philosophy">Our approach</Link>
            <a href="http://127.0.0.1:8000/api/docs/">API documentation</a>
          </div>
        </div>
        <div className="container footer-bottom">
          <p className="muted">© {new Date().getFullYear()} E-Shop</p>
          <p className="muted">Secure checkout · JWT protected accounts</p>
        </div>
      </footer>
    </div>
  )
}
