import { ArrowRight, Lock, Minus, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ProductMedia } from '../components/ProductCard'
import { EmptyState, ErrorNote, Field, PageLoader } from '../components/ui'
import { useAuth } from '../context/auth-context'
import { useCart } from '../context/cart-context'
import { fieldError } from '../lib/api'
import { formatPrice } from '../lib/format'
import type { Order } from '../types'
const FREE_SHIPPING_THRESHOLD = 150

export function CartPage() {
  const { cart, count, total, loading, remove, setQuantity, checkout } = useCart()
  const { user } = useAuth()
  const [address, setAddress] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [order, setOrder] = useState<Order | null>(null)

  const shipping = 12
  const subtotal = Number.parseFloat(total)
  const remaining = Math.max(0, FREE_SHIPPING_THRESHOLD - subtotal)
  const grandTotal = subtotal + shipping

  const handleCheckout = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const created = await checkout(address)
      setOrder(created)
      setAddress('')
    } catch (caught) {
      setError(fieldError(caught, 'shipping_address') ?? 'Checkout could not be completed.')
    } finally {
      setBusy(false)
    }
  }

  if (loading && !cart) return <PageLoader label="Loading your cart" />

  if (order) {
    return (
      <div className="container page narrow">
        <div className="success-panel">
          <p className="eyebrow">Order confirmed</p>
          <h1 className="headline">Thank you, {user?.first_name || user?.username}.</h1>
          <p className="lead lead-small">
            Your order <strong>#{order.id}</strong> is {order.status_display.toLowerCase()}. We will
            keep you posted as it moves.
          </p>
          <div className="success-actions">
            <Link className="btn btn-dark" to="/orders">
              View orders
              <ArrowRight size={16} />
            </Link>
            <Link className="btn btn-ghost" to="/shop">
              Continue shopping
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!cart || count === 0) {
    return (
      <div className="container page">
        <header className="page-head">
          <p className="eyebrow">Cart</p>
          <h1 className="headline">Your cart is empty</h1>
        </header>
        <EmptyState
          title="Nothing here yet"
          description="Browse the catalogue and add something you will keep."
          action={
            <Link className="btn btn-dark btn-sm" to="/shop">
              Start shopping
            </Link>
          }
        />
      </div>
    )
  }

  return (
    <div className="container page">
      <header className="page-head">
        <p className="eyebrow">Cart</p>
        <h1 className="headline">
          {count} {count === 1 ? 'item' : 'items'} ready to go
        </h1>
      </header>

      <div className="cart-layout">
        <div className="cart-lines">
          {cart.items.map((item) => (
            <article className="line" key={item.id}>
              <Link className="line-thumb" to={`/product/${item.product}`}>
                <ProductMedia src="" name={item.product_name} />
              </Link>
              <div className="line-info">
                <h3>
                  <Link to={`/product/${item.product}`}>{item.product_name}</Link>
                </h3>
                <p className="muted">{formatPrice(item.unit_price)} each</p>
                <div className="line-controls">
                  <span className="qty-static">
                    <button
                      type="button"
                      aria-label={`Decrease ${item.product_name}`}
                      disabled={item.quantity <= 1}
                      onClick={() => void remove(item.product)}
                    >
                      <Minus size={13} />
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      type="button"
                      aria-label={`Increase ${item.product_name}`}
                      onClick={() => {
                        void (async () => {
                          try {
                            await setQuantity(item.product, item.quantity + 1)
                          } catch {
                            setError('We could not update the quantity.')
                          }
                        })()
                      }}
                    >
                      <Plus size={13} />
                    </button>
                  </span>
                  <button
                    type="button"
                    className="link-btn danger"
                    onClick={() => void remove(item.product)}
                  >
                    <Trash2 size={14} /> Remove
                  </button>
                </div>
              </div>
              <p className="line-total">{formatPrice(item.line_total)}</p>
            </article>
          ))}

          <div className="shipping-meter">
            <p>
              {remaining > 0
                ? `You are ${formatPrice(remaining)} away from complimentary shipping.`
                : 'Complimentary shipping is unlocked for this order.'}
            </p>
            <div className="meter">
              <span
                style={{ width: `${Math.min(100, (subtotal / FREE_SHIPPING_THRESHOLD) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        <aside className="summary panel">
          <h3>Order summary</h3>
          {error ? <ErrorNote message={error} /> : null}
          <div className="summary-row">
            <span>Subtotal</span>
            <span>{formatPrice(subtotal)}</span>
          </div>
          <div className="summary-row">
            <span>Shipping</span>
            <span>{formatPrice(shipping)}</span>
          </div>
          <div className="summary-row total">
            <span>Total</span>
            <span>{formatPrice(grandTotal)}</span>
          </div>

          <form className="checkout-form" onSubmit={(event) => void handleCheckout(event)}>
            <Field label="Shipping address" htmlFor="address">
              <textarea
                id="address"
                className="input"
                rows={4}
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                placeholder="Street, city, postal code, country"
                required
              />
            </Field>
            <button type="submit" className="btn btn-dark full" disabled={busy}>
              {busy ? 'Placing order…' : 'Place order'}
              <Lock size={15} />
            </button>
            <p className="hint center">Stock is reserved and decremented when your order is placed.</p>
          </form>
        </aside>
      </div>
    </div>
  )
}
