import { ArrowRight, Package, RefreshCw, Sparkles, Truck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ProductCard } from '../components/ProductCard'
import { ErrorNote, ProductSkeleton } from '../components/ui'
import { api } from '../lib/api'
import type { Category, Product } from '../types'

const principles = [
  {
    title: 'Made to be kept',
    body: 'We favour materials and construction that age well, so every piece earns its place over time.',
  },
  {
    title: 'Fewer, better things',
    body: 'A small, deliberate catalogue instead of endless choice. Everything here earns its shelf space.',
  },
  {
    title: 'Straightforward pricing',
    body: 'No gimmicks, no hidden fees. The price you see is the price you pay, and returns are free.',
  },
]

export function HomePage() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const [productPage, categoryPage] = await Promise.all([
        api.products.list({ page_size: 8, ordering: '-created_at' }),
        api.categories.list(),
      ])
      setProducts(productPage.results)
      setCategories(categoryPage.results)
    } catch {
      setError('The catalogue is unavailable right now. Please check that the API is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const retry = () => {
    setError(null)
    setLoading(true)
    void load()
  }

  const featured = products?.slice(0, 4) ?? []
  const hasCatalogue = products !== null

  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Spring edit · 2026</p>
            <h1 className="display">
              Objects chosen to
              <br />
              <em>last a lifetime.</em>
            </h1>
            <p className="lead">
              A small catalogue of everyday goods built with honest materials, quiet details and no
              disposable thinking.
            </p>
            <div className="hero-actions">
              <Link className="btn btn-dark" to="/shop">
                Shop the collection
                <ArrowRight size={16} />
              </Link>
              <Link className="btn btn-ghost" to="/shop?ordering=-created_at">
                New arrivals
              </Link>
            </div>
            <ul className="hero-facts">
              <li>
                <Truck size={16} strokeWidth={1.5} /> Free shipping over $150
              </li>
              <li>
                <RefreshCw size={16} strokeWidth={1.5} /> 30-day returns, no questions
              </li>
              <li>
                <Sparkles size={16} strokeWidth={1.5} /> Small-batch production
              </li>
            </ul>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="art-card art-card-back">
              <Package size={30} strokeWidth={1} />
              <span>Since 2026</span>
            </div>
            <div className="art-card art-card-mid">
              <span className="art-kicker">Edit No. 04</span>
              <p className="art-quote">
                Buy less,
                <br />
                choose well.
              </p>
            </div>
            <div className="art-card art-card-front">
              <span className="art-line" />
              <p className="art-label">Everyday, refined</p>
            </div>
          </div>
        </div>
      </section>

      {categories.length > 0 ? (
        <section className="section section-tight">
          <div className="container">
            <div className="section-head">
              <div>
                <p className="eyebrow">Browse</p>
                <h2 className="headline">Shop by category</h2>
              </div>
              <Link className="link-arrow" to="/shop">
                View everything
                <ArrowRight size={15} />
              </Link>
            </div>
            <div className="category-row">
              {categories.slice(0, 6).map((category) => (
                <Link
                  className="category-chip"
                  key={category.id}
                  to={`/shop?category=${category.slug}`}
                >
                  <span>{category.name}</span>
                  {category.parent_name ? <small>{category.parent_name}</small> : null}
                </Link>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      <section className="section">
        <div className="container">
          <div className="section-head">
            <div>
              <p className="eyebrow">Featured</p>
              <h2 className="headline">Recently added</h2>
            </div>
            <Link className="link-arrow" to="/shop">
              See all
              <ArrowRight size={15} />
            </Link>
          </div>

          {error ? <ErrorNote message={error} onRetry={retry} /> : null}

          {loading ? (
            <ProductSkeleton count={4} />
          ) : (
            <>
              {featured.length > 0 ? (
                <div className="grid-products">
                  {featured.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              ) : null}
              {hasCatalogue && featured.length === 0 ? (
                <div className="empty-panel">
                  <h3>The catalogue is ready for its first product</h3>
                  <p className="muted">
                    Add products through the Django admin or the API, then they will appear here
                    automatically.
                  </p>
                  <a className="btn btn-dark btn-sm" href="http://127.0.0.1:8000/admin/">
                    Open Django admin
                  </a>
                </div>
              ) : null}
            </>
          )}
        </div>
      </section>

      <section className="section philosophy" id="philosophy">
        <div className="container">
          <div className="section-head">
            <div>
              <p className="eyebrow">Our approach</p>
              <h2 className="headline">Less, but better</h2>
            </div>
          </div>
          <div className="value-grid">
            {principles.map((principle, index) => (
              <article className="value" key={principle.title}>
                <span className="value-index">0{index + 1}</span>
                <h3>{principle.title}</h3>
                <p className="muted">{principle.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
