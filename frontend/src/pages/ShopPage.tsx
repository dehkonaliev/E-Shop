import { SlidersHorizontal, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ProductCard } from '../components/ProductCard'
import { EmptyState, ErrorNote, ProductSkeleton } from '../components/ui'
import { api } from '../lib/api'
import type { ProductQuery } from '../lib/api'
import type { Category, Product } from '../types'

const orderingOptions = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'price', label: 'Price: low to high' },
  { value: '-price', label: 'Price: high to low' },
  { value: 'name', label: 'Alphabetical' },
]

const pageSizes = [10, 20, 40]

function readNumber(value: string | null): number | null {
  if (!value) return null
  const parsed = Number.parseInt(value, 10)
  return Number.isNaN(parsed) ? null : parsed
}

export function ShopPage() {
  const [params, setParams] = useSearchParams()
  const [products, setProducts] = useState<Product[] | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [count, setCount] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [showFilters, setShowFilters] = useState(false)

  const [minPrice, setMinPrice] = useState(params.get('min_price') ?? '')
  const [maxPrice, setMaxPrice] = useState(params.get('max_price') ?? '')

  const category = params.get('category') ?? ''
  const search = params.get('search') ?? ''
  const ordering = params.get('ordering') ?? '-created_at'
  const inStock = params.get('in_stock') ?? ''
  const page = readNumber(params.get('page')) ?? 1
  const pageSize = readNumber(params.get('page_size')) ?? 12

  const query = useMemo<ProductQuery>(
    () => ({
      category: category || undefined,
      search: search || undefined,
      ordering,
      in_stock: inStock || undefined,
      min_price: params.get('min_price') || undefined,
      max_price: params.get('max_price') || undefined,
      page,
      page_size: pageSize,
    }),
    [category, search, ordering, inStock, params, page, pageSize],
  )

  const load = useCallback(async () => {
    try {
      const result = await api.products.list(query)
      setProducts(result.results)
      setCount(result.count)
    } catch {
      setError('We could not load the catalogue. Please try again.')
      setProducts([])
    } finally {
      setLoading(false)
    }
  }, [query])

  useEffect(() => {
    void load()
  }, [load])

  const retry = () => {
    setError(null)
    setLoading(true)
    void load()
  }

  useEffect(() => {
    api.categories
      .list()
      .then((result) => setCategories(result.results))
      .catch(() => setCategories([]))
  }, [])

  const update = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(patch)) {
      if (value === null || value === '') next.delete(key)
      else next.set(key, value)
    }
    if (!('page' in patch)) next.delete('page')
    setLoading(true)
    setParams(next, { replace: true })
  }

  const applyPrice = () => {
    update({ min_price: minPrice || null, max_price: maxPrice || null })
  }

  const activeCategory = categories.find((item) => item.slug === category)
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  const hasFilters = Boolean(category || search || inStock || params.get('min_price') || params.get('max_price'))

  return (
    <div className="container page">
      <header className="page-head">
        <p className="eyebrow">Catalogue</p>
        <h1 className="headline">
          {activeCategory ? activeCategory.name : search ? `Results for “${search}”` : 'All products'}
        </h1>
        <p className="lead lead-small">
          {loading ? 'Loading the catalogue…' : `${count} ${count === 1 ? 'product' : 'products'} available`}
        </p>
      </header>

      <div className="shop-toolbar">
        <form
          className="search-box"
          onSubmit={(event) => {
            event.preventDefault()
            const value = new FormData(event.currentTarget).get('search')
            update({ search: typeof value === 'string' ? value : null })
          }}
        >
          <input
            type="search"
            name="search"
            defaultValue={search}
            placeholder="Search products…"
            aria-label="Search products"
          />
        </form>
        <div className="toolbar-right">
          <button
            type="button"
            className="btn btn-ghost btn-sm filter-toggle"
            onClick={() => setShowFilters((value) => !value)}
          >
            <SlidersHorizontal size={15} />
            Filters
          </button>
          <label className="select-wrap">
            <span className="sr-only">Sort by</span>
            <select value={ordering} onChange={(event) => update({ ordering: event.target.value })}>
              {orderingOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="select-wrap">
            <span className="sr-only">Items per page</span>
            <select
              value={String(pageSize)}
              onChange={(event) => update({ page_size: event.target.value })}
            >
              {pageSizes.map((size) => (
                <option key={size} value={size}>
                  {size} / page
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="shop-layout">
        <aside className={`filters ${showFilters ? 'open' : ''}`}>
          <div className="filter-block">
            <p className="eyebrow">Category</p>
            <div className="filter-list">
              <button
                type="button"
                className={!category ? 'active' : ''}
                onClick={() => update({ category: null })}
              >
                All
              </button>
              {categories.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={category === item.slug ? 'active' : ''}
                  onClick={() => update({ category: item.slug })}
                >
                  {item.name}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-block">
            <p className="eyebrow">Availability</p>
            <div className="filter-list">
              <button
                type="button"
                className={inStock === '' ? 'active' : ''}
                onClick={() => update({ in_stock: null })}
              >
                Any
              </button>
              <button
                type="button"
                className={inStock === 'true' ? 'active' : ''}
                onClick={() => update({ in_stock: 'true' })}
              >
                In stock
              </button>
              <button
                type="button"
                className={inStock === 'false' ? 'active' : ''}
                onClick={() => update({ in_stock: 'false' })}
              >
                Sold out
              </button>
            </div>
          </div>

          <div className="filter-block">
            <p className="eyebrow">Price</p>
            <div className="price-fields">
              <input
                type="number"
                min="0"
                step="0.01"
                value={minPrice}
                onChange={(event) => setMinPrice(event.target.value)}
                placeholder="Min"
                aria-label="Minimum price"
              />
              <span aria-hidden="true">–</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={maxPrice}
                onChange={(event) => setMaxPrice(event.target.value)}
                placeholder="Max"
                aria-label="Maximum price"
              />
            </div>
            <button type="button" className="btn btn-dark btn-sm full" onClick={applyPrice}>
              Apply price
            </button>
          </div>

          {hasFilters ? (
            <button
              type="button"
              className="btn btn-ghost btn-sm full"
              onClick={() => {
                setMinPrice('')
                setMaxPrice('')
                setParams(new URLSearchParams(), { replace: true })
              }}
            >
              <X size={14} />
              Clear all filters
            </button>
          ) : null}
        </aside>

        <div className="shop-results">
          {error ? <ErrorNote message={error} onRetry={retry} /> : null}
          {loading ? (
            <ProductSkeleton count={8} />
          ) : products && products.length > 0 ? (
            <div className="grid-products">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Nothing matches those filters"
              description="Try widening the price range, clearing filters or searching a different term."
              action={
                <button
                  type="button"
                  className="btn btn-dark btn-sm"
                  onClick={() => {
                    setMinPrice('')
                    setMaxPrice('')
                    setParams(new URLSearchParams(), { replace: true })
                  }}
                >
                  Reset filters
                </button>
              }
            />
          )}

          {!loading && count > pageSize ? (
            <nav className="pagination" aria-label="Pagination">
              <button
                type="button"
                className="page-btn"
                disabled={page <= 1}
                onClick={() => update({ page: String(page - 1) })}
              >
                Previous
              </button>
              <span className="muted">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                className="page-btn"
                disabled={page >= totalPages}
                onClick={() => update({ page: String(page + 1) })}
              >
                Next
              </button>
            </nav>
          ) : null}
        </div>
      </div>
    </div>
  )
}
