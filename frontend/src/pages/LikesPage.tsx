import { Heart } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ProductCard } from '../components/ProductCard'
import { EmptyState, ErrorNote, PageLoader } from '../components/ui'
import { api } from '../lib/api'
import type { Like, Product } from '../types'

export function LikesPage() {
  const [likes, setLikes] = useState<Like[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const result = await api.likes.list()
      setLikes(result.results)
    } catch {
      setError('We could not load your saved items.')
      setLikes([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const retry = () => {
    setError(null)
    setLoading(true)
    void load()
  }

  const products: Product[] = (likes ?? []).map((like) => ({
    id: like.product.id,
    uuid: like.product.uuid,
    category: 0,
    category_name: '',
    name: like.product.name,
    slug: like.product.slug,
    description: '',
    price: like.product.price,
    stock: like.product.stock,
    image: like.product.image,
    likes_count: 0,
    average_rating: null,
    is_liked: true,
    created_at: like.created_at,
    updated_at: like.created_at,
  }))

  return (
    <div className="container page">
      <header className="page-head">
        <p className="eyebrow">Saved items</p>
        <h1 className="headline">Your shortlist</h1>
        <p className="lead lead-small">
          {likes ? `${likes.length} ${likes.length === 1 ? 'piece' : 'pieces'} saved for later` : ''}
        </p>
      </header>

      {error ? <ErrorNote message={error} onRetry={retry} /> : null}
      {loading ? (
        <PageLoader label="Loading saved items" />
      ) : products.length > 0 ? (
        <div className="grid-products">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="Nothing saved yet"
          description="Tap Save on any product to keep it here while you decide."
          action={
            <Link className="btn btn-dark btn-sm" to="/shop">
              <Heart size={15} />
              Find something
            </Link>
          }
        />
      )}
    </div>
  )
}
