import { Check, Heart, Pencil, ShieldCheck, Truck } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ProductCard, ProductMedia } from '../components/ProductCard'
import { hasAdminAccess } from '../lib/access'
import { EmptyState, ErrorNote, Field, PageLoader, QuantityStepper, Stars } from '../components/ui'
import { useAuth } from '../context/auth-context'
import { useCart } from '../context/cart-context'
import { api, fieldError } from '../lib/api'
import { formatDate, formatPrice, pluralize } from '../lib/format'
import type { Comment, Product } from '../types'

function RatingInput({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return (
    <div className="rating-input" role="radiogroup" aria-label="Your rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} ${pluralize(star, 'star')}`}
          className={star <= value ? 'active' : ''}
          onClick={() => onChange(star)}
        >
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="M10 1.6l2.5 5.1 5.6.8-4 4 .9 5.6-5-2.7-5 2.7.9-5.6-4-4 5.6-.8z" />
          </svg>
        </button>
      ))}
    </div>
  )
}

export function ProductPage() {
  const { id } = useParams()
  const productId = Number.parseInt(id ?? '', 10)
  const navigate = useNavigate()
  const { user } = useAuth()
  const { add } = useCart()

  const [product, setProduct] = useState<Product | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [related, setRelated] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [busy, setBusy] = useState(false)
  const [added, setAdded] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  const [commentText, setCommentText] = useState('')
  const [commentRating, setCommentRating] = useState(5)
  const [commentError, setCommentError] = useState<string | null>(null)
  const [commenting, setCommenting] = useState(false)

  const load = useCallback(async () => {
    if (Number.isNaN(productId)) {
      setError('That product link is not valid.')
      setLoading(false)
      return
    }
    try {
      const [detail, commentPage, all] = await Promise.all([
        api.products.get(productId),
        api.comments.list(productId),
        api.products.list({ page_size: 8, ordering: '-created_at' }),
      ])
      setProduct(detail)
      setComments(commentPage.results)
      setRelated(
        all.results.filter((item) => item.id !== detail.id).slice(0, 4),
      )
    } catch {
      setError('We could not load this product.')
    } finally {
      setLoading(false)
    }
  }, [productId])

  useEffect(() => {
    void load()
  }, [load])

  const retry = () => {
    setError(null)
    setLoading(true)
    void load()
  }

  const toggleLike = async () => {
    if (!user) {
      navigate('/signin', { state: { from: `/product/${productId}` } })
      return
    }
    if (!product) return
    setBusy(true)
    try {
      const result = await api.products.toggleLike(product.id)
      setProduct((current) =>
        current
          ? {
              ...current,
              is_liked: result.liked,
              likes_count: result.likes_count,
            }
          : current,
      )
    } catch {
      setNotice('We could not update your saved items.')
    } finally {
      setBusy(false)
    }
  }

  const handleAdd = async () => {
    if (!user) {
      navigate('/signin', { state: { from: `/product/${productId}` } })
      return
    }
    if (!product) return
    setBusy(true)
    setAdded(false)
    try {
      await add(product.id, quantity)
      setAdded(true)
      window.setTimeout(() => setAdded(false), 2500)
    } catch {
      setNotice('We could not add this item to your cart.')
    } finally {
      setBusy(false)
    }
  }

  const submitComment = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!user) {
      navigate('/signin', { state: { from: `/product/${productId}` } })
      return
    }
    setCommenting(true)
    setCommentError(null)
    try {
      const created = await api.comments.create(productId, {
        text: commentText,
        rating: commentRating,
      })
      setComments((current) => [created, ...current])
      setCommentText('')
      setCommentRating(5)
      void load()
    } catch (caught) {
      setCommentError(fieldError(caught, 'text') ?? 'Your review could not be posted.')
    } finally {
      setCommenting(false)
    }
  }

  if (loading) return <PageLoader label="Loading product" />
  if (error || !product) {
    return (
      <div className="container page">
        <ErrorNote message={error ?? 'Product not found.'} onRetry={retry} />
        <div className="page-foot">
          <Link className="btn btn-ghost" to="/shop">
            Back to shop
          </Link>
        </div>
      </div>
    )
  }

  const inStock = product.stock > 0
  const myReview = user
    ? (comments.find((comment) => comment.user_id === user.id) ?? null)
    : null

  return (
    <div className="container page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span aria-hidden="true">/</span>
        <Link to="/shop">Shop</Link>
        <span aria-hidden="true">/</span>
        <span className="muted">{product.name}</span>
      </nav>

      <div className="pdp">
        <div className="pdp-media">
          <ProductMedia src={product.image} name={product.name} ratio="tall" />
        </div>
        <div className="pdp-info">
          <p className="eyebrow">{product.category_name}</p>
          <h1 className="headline">{product.name}</h1>
          <div className="pdp-meta">
            <span className="price price-lg">{formatPrice(product.price)}</span>
            {product.average_rating ? (
              <span className="rating">
                <Stars value={Number.parseFloat(product.average_rating)} />
                <span className="muted">
                  {Number.parseFloat(product.average_rating).toFixed(1)} · {comments.length}{' '}
                  {pluralize(comments.length, 'review')}
                </span>
              </span>
            ) : null}
          </div>

          <p className="lead lead-small pdp-description">{product.description}</p>

          {notice ? <ErrorNote message={notice} /> : null}

          <div className="pdp-actions">
            {hasAdminAccess(user) ? (
              <div className="pdp-admin-note">
                <p className="cell-strong">Administrator view</p>
                <p className="muted">
                  Administrators manage the catalogue instead of buying. Use the admin panel to
                  edit price, stock and images.
                </p>
                <div className="pdp-admin-actions">
                  <Link className="btn btn-dark" to={`/admin/products?edit=${product.id}`}>
                    <Pencil size={15} strokeWidth={1.8} aria-hidden="true" />
                    Edit this product
                  </Link>
                  <Link className="btn btn-ghost" to="/admin/products">
                    All products
                  </Link>
                </div>
              </div>
            ) : (
              <>
                <div className="pdp-buy">
                  <QuantityStepper
                    value={quantity}
                    max={Math.max(1, Math.min(product.stock, 99))}
                    onChange={setQuantity}
                  />
                  <button
                    type="button"
                    className="btn btn-dark grow"
                    onClick={() => void handleAdd()}
                    disabled={!inStock || busy}
                  >
                    {added ? (
                      <>
                        <Check size={16} /> Added to cart
                      </>
                    ) : inStock ? (
                      'Add to cart'
                    ) : (
                      'Sold out'
                    )}
                  </button>
                </div>
                <button
                  type="button"
                  className={`btn btn-ghost like-btn ${product.is_liked ? 'liked' : ''}`}
                  onClick={() => void toggleLike()}
                  disabled={busy}
                  aria-pressed={product.is_liked}
                >
                  <Heart size={16} fill={product.is_liked ? 'currentColor' : 'none'} />
                  {product.is_liked ? 'Saved' : 'Save'}
                </button>
              </>
            )}
          </div>

          <ul className="pdp-assurances">
            <li>
              <Truck size={16} strokeWidth={1.5} /> Free shipping over $150
            </li>
            <li>
              <ShieldCheck size={16} strokeWidth={1.5} /> Secure checkout
            </li>
            <li>
              <Check size={16} strokeWidth={1.5} /> 30-day returns
            </li>
          </ul>

          <div className="pdp-details">
            <div>
              <p className="eyebrow">Availability</p>
              <p>{inStock ? `${product.stock} in stock` : 'Currently unavailable'}</p>
            </div>
            <div>
              <p className="eyebrow">Added</p>
              <p>{formatDate(product.created_at)}</p>
            </div>
            <div>
              <p className="eyebrow">Saves</p>
              <p>
                {product.likes_count} {pluralize(product.likes_count, 'person', 'people')}
              </p>
            </div>
          </div>
        </div>
      </div>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Reviews</p>
            <h2 className="headline">What customers say</h2>
          </div>
        </div>

        <div className="reviews-layout">
          <div className="reviews-list">
            {comments.length > 0 ? (
              comments.map((comment) => (
                <article className="review" key={comment.id}>
                  <div className="review-head">
                    <span className="avatar avatar-sm">{comment.user.slice(0, 2).toUpperCase()}</span>
                    <div>
                      <p className="review-author">{comment.user}</p>
                      <p className="muted">{formatDate(comment.created_at)}</p>
                    </div>
                    <Stars value={comment.rating} />
                  </div>
                  <p>{comment.text}</p>
                </article>
              ))
            ) : (
              <EmptyState
                title="No reviews yet"
                description="Be the first to share how this piece holds up."
              />
            )}
          </div>

          {myReview ? (
            <div className="panel review-done">
              <h3>Your review is live</h3>
              <p className="muted">
                You rated this {myReview.rating} of 5. One review per person is allowed, so this
                form is closed.
              </p>
            </div>
          ) : (
            <form className="review-form panel" onSubmit={(event) => void submitComment(event)}>
              <h3>Write a review</h3>
              <Field label="Your rating" htmlFor="rating">
                <div id="rating">
                  <RatingInput value={commentRating} onChange={setCommentRating} />
                </div>
              </Field>
              <Field label="Your thoughts" htmlFor="comment" error={commentError}>
                <textarea
                  id="comment"
                  className="input"
                  rows={5}
                  value={commentText}
                  onChange={(event) => setCommentText(event.target.value)}
                  placeholder="What did you like or dislike? How does it fit into your routine?"
                  required
                />
              </Field>
              <button type="submit" className="btn btn-dark" disabled={commenting}>
                {commenting ? 'Posting…' : 'Post review'}
              </button>
            </form>
          )}
        </div>
      </section>

      {related.length > 0 ? (
        <section className="section">
          <div className="section-head">
            <div>
              <p className="eyebrow">You may also like</p>
              <h2 className="headline">Pairs well with</h2>
            </div>
            <Link className="link-arrow" to="/shop">
              Shop all
            </Link>
          </div>
          <div className="grid-products">
            {related.map((item) => (
              <ProductCard key={item.id} product={item} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}
