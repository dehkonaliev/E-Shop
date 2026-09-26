import { Heart, Package } from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatPrice, pluralize } from '../lib/format'
import type { Product } from '../types'
import { Stars } from './ui'

export function ProductMedia({
  src,
  name,
  ratio = 'square',
}: {
  src: string
  name: string
  ratio?: 'square' | 'tall'
}) {
  if (src) {
    return <img className={`media media-${ratio}`} src={src} alt={name} loading="lazy" />
  }
  return (
    <div className={`media media-${ratio} media-empty`} aria-hidden="true">
      <Package size={28} strokeWidth={1.2} />
    </div>
  )
}

export function ProductCard({ product }: { product: Product }) {
  const stockClass =
    product.stock === 0 ? 'out' : product.stock <= 5 ? 'low' : 'in'
  const stockLabel =
    product.stock === 0
      ? 'Out of stock'
      : product.stock <= 5
        ? `Only ${product.stock} left in stock`
        : `${product.stock} in stock`

  return (
    <article className="product-card">
      <Link className="product-card-media" to={`/product/${product.id}`}>
        <ProductMedia src={product.image} name={product.name} />
      </Link>
      <div className="product-card-body">
        <div className="product-card-meta">
          <span className="eyebrow">{product.category_name}</span>
          <span className="price">{formatPrice(product.price)}</span>
        </div>
        <h3>
          <Link to={`/product/${product.id}`}>{product.name}</Link>
        </h3>
        <p className={`stock-note ${stockClass}`}>{stockLabel}</p>
        <div className="product-card-foot">
          {product.average_rating ? (
            <span className="rating">
              <Stars value={Number.parseFloat(product.average_rating)} />
              <span className="muted">
                {Number.parseFloat(product.average_rating).toFixed(1)} ·{' '}
                {product.likes_count} {pluralize(product.likes_count, 'like')}
              </span>
            </span>
          ) : (
            <span className="muted">No reviews yet</span>
          )}
          {product.likes_count > 0 ? <Heart size={14} strokeWidth={1.6} /> : null}
        </div>
      </div>
    </article>
  )
}
