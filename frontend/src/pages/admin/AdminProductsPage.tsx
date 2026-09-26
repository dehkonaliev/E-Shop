import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  AdminPageHeader,
  AdminTable,
  EmptyRow,
  Modal,
  Notice,
  Pager,
  Panel,
} from '../../components/admin/AdminUI'
import { ErrorNote, Field, PageLoader } from '../../components/ui'
import { api, ApiError, fieldError } from '../../lib/api'
import { formatDate, formatPrice, pluralize } from '../../lib/format'
import type { Category, Paginated, Product, ProductSale } from '../../types'

const PAGE_SIZE = 12

interface FormState {
  id: number | null
  name: string
  slug: string
  description: string
  price: string
  stock: string
  category: string
  image: File | null
}

const emptyForm: FormState = {
  id: null,
  name: '',
  slug: '',
  description: '',
  price: '',
  stock: '0',
  category: '',
  image: null,
}

const orderingOptions = [
  { value: '-units_sold', label: 'Best selling' },
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: 'stock', label: 'Lowest stock' },
  { value: '-stock', label: 'Highest stock' },
  { value: '-revenue', label: 'Highest revenue' },
  { value: 'name', label: 'Name A–Z' },
]

export function AdminProductsPage() {
  const [rows, setRows] = useState<Paginated<ProductSale> | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [term, setTerm] = useState('')
  const [ordering, setOrdering] = useState('-units_sold')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<FormState | null>(null)
  const [formError, setFormError] = useState<unknown>(null)
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<ProductSale | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [flash, setFlash] = useState<string | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setRows(await api.admin.sales({ page, page_size: PAGE_SIZE, search: term, ordering }))
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Products could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [page, term, ordering])

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

  const loadCategories = useCallback(async () => {
    try {
      const response = await api.categories.list()
      setCategories(response.results)
    } catch {
      setCategories([])
    }
  }, [])

  useEffect(() => {
    void loadCategories()
  }, [loadCategories])

  const categoryOptions = useMemo(
    () => [...categories].sort((a, b) => a.name.localeCompare(b.name)),
    [categories],
  )

  const openCreate = () => {
    setForm({
      ...emptyForm,
      category: categoryOptions[0] ? String(categoryOptions[0].id) : '',
    })
    setFormError(null)
  }

  const openEdit = useCallback(
    async (id: number) => {
      setFormError(null)
      try {
        const product: Product = await api.products.get(id)
        setForm({
          id: product.id,
          name: product.name,
          slug: product.slug,
          description: product.description,
          price: product.price,
          stock: String(product.stock),
          category: String(product.category),
          image: null,
        })
        if (searchParams.get('edit')) {
          const next = new URLSearchParams(searchParams)
          next.delete('edit')
          setSearchParams(next, { replace: true })
        }
      } catch (caught) {
        setError(caught instanceof ApiError ? caught.message : 'Product could not be opened.')
      }
    },
    [searchParams, setSearchParams],
  )

  const editTarget = searchParams.get('edit')

  useEffect(() => {
    if (!editTarget) return
    const id = Number.parseInt(editTarget, 10)
    if (Number.isNaN(id)) return
    void openEdit(id)
  }, [editTarget, openEdit])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!form) return
    setSaving(true)
    setFormError(null)
    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      price: form.price,
      stock: Number.parseInt(form.stock, 10) || 0,
      category: Number.parseInt(form.category, 10),
      image: form.image,
      slug: form.slug.trim() || undefined,
    }
    try {
      if (form.id) {
        await api.admin.updateProduct(form.id, payload)
        setFlash(`“${payload.name}” was updated.`)
      } else {
        await api.admin.createProduct(payload)
        setFlash(`“${payload.name}” was added to the catalogue.`)
      }
      setForm(null)
      await Promise.all([load(), loadCategories()])
    } catch (caught) {
      setFormError(caught)
    } finally {
      setSaving(false)
    }
  }

  const remove = async () => {
    if (!confirmDelete) return
    setDeleting(true)
    try {
      await api.admin.deleteProduct(confirmDelete.id)
      setFlash(`“${confirmDelete.name}” was removed.`)
      setConfirmDelete(null)
      await load()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Product could not be deleted.')
      setConfirmDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="admin-stack">
      <AdminPageHeader
        eyebrow="Catalogue"
        title="Products"
        description="Add, edit and retire products. Stock and sales update in real time."
        actions={
          <button type="button" className="btn btn-dark btn-sm" onClick={openCreate}>
            <Plus size={15} strokeWidth={2} />
            New product
          </button>
        }
      />

      {flash ? <Notice tone="success" onClose={() => setFlash(null)}>{flash}</Notice> : null}
      {error ? <ErrorNote message={error} onRetry={() => void load()} /> : null}
      {categoryOptions.length === 0 ? (
        <Notice tone="info">
          Create a category first — every product needs one.{' '}
          <Link to="/admin/categories">Add a category</Link>
        </Notice>
      ) : null}

      <Panel
        title="Catalogue"
        description={rows ? `${rows.count} ${pluralize(rows.count, 'product')}` : undefined}
        action={
          <div className="toolbar">
            <div className="search">
              <Search size={15} strokeWidth={1.8} aria-hidden="true" />
              <input
                type="search"
                value={search}
                placeholder="Search products"
                aria-label="Search products"
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <select
              className="select"
              value={ordering}
              aria-label="Sort products"
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
        {loading && !rows ? <PageLoader label="Loading products" /> : null}
        {rows ? (
          <>
            <AdminTable>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th className="num">Price</th>
                  <th className="num">Stock</th>
                  <th className="num">Sold</th>
                  <th className="num">Revenue</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {rows.results.length === 0 ? (
                  <EmptyRow colSpan={7}>
                    {term ? 'No products match that search.' : 'No products yet. Add the first one.'}
                  </EmptyRow>
                ) : (
                  rows.results.map((row) => (
                    <tr
                      key={row.id}
                      className="row-clickable"
                      onClick={() => void openEdit(row.id)}
                    >
                      <td>
                        <div className="cell-product">
                          {row.image ? (
                            <img className="cell-thumb" src={row.image} alt="" />
                          ) : (
                            <span className="cell-thumb placeholder" aria-hidden="true" />
                          )}
                          <div>
                            <span className="cell-strong">{row.name}</span>
                            <span className="cell-sub muted">
                              {row.slug} · added {formatDate(row.created_at)}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="muted">{row.category ?? '—'}</td>
                      <td className="num">{formatPrice(row.price)}</td>
                      <td className="num">
                        <span
                          className={`badge ${row.stock === 0 ? 'danger' : row.stock <= 5 ? 'warning' : 'neutral'}`}
                        >
                          {row.stock}
                        </span>
                        <span className="cell-sub muted">
                          {row.stock === 0
                            ? 'out of stock'
                            : row.stock <= 5
                              ? 'low stock'
                              : 'in stock'}
                        </span>
                      </td>
                      <td className="num">
                        {row.units_sold}
                        <span className="cell-sub muted"> {row.order_count} orders</span>
                      </td>
                      <td className="num">{formatPrice(row.revenue)}</td>
                      <td className="actions" onClick={(event) => event.stopPropagation()}>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => void openEdit(row.id)}
                        >
                          <Pencil size={14} strokeWidth={1.8} aria-hidden="true" />
                          Edit
                        </button>
                        <button
                          type="button"
                          className="icon-btn danger"
                          onClick={() => setConfirmDelete(row)}
                          aria-label={`Delete ${row.name}`}
                          title="Delete"
                        >
                          <Trash2 size={15} strokeWidth={1.8} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </AdminTable>
            <Pager
              page={page}
              count={rows.count}
              pageSize={PAGE_SIZE}
              onChange={(next) => {
                setPage(next)
                setFlash(null)
              }}
            />
          </>
        ) : null}
      </Panel>

      <Modal
        open={form !== null}
        wide
        title={form?.id ? 'Edit product' : 'New product'}
        description="Everything here is visible in the storefront immediately."
        onClose={() => setForm(null)}
        footer={
          <>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setForm(null)}>
              Cancel
            </button>
            <button
              type="submit"
              form="product-form"
              className="btn btn-dark btn-sm"
              disabled={saving}
            >
              {saving ? 'Saving…' : form?.id ? 'Save changes' : 'Add product'}
            </button>
          </>
        }
      >
        {form ? (
          <form id="product-form" className="admin-form" onSubmit={submit} noValidate>
            {formError ? <Notice tone="error">{errorMessage(formError)}</Notice> : null}
            <div className="admin-form-grid">
              <Field label="Name" error={fieldError(formError, 'name')}>
                <input
                  className="input"
                  value={form.name}
                  required
                  maxLength={200}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                />
              </Field>
              <Field
                label="Category"
                error={fieldError(formError, 'category')}
              >
                <select
                  className="select"
                  value={form.category}
                  required
                  onChange={(event) => setForm({ ...form, category: event.target.value })}
                >
                  <option value="">Select a category</option>
                  {categoryOptions.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.parent_name ? `${category.parent_name} / ` : ''}
                      {category.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Price" hint="USD" error={fieldError(formError, 'price')}>
                <input
                  className="input"
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.price}
                  required
                  onChange={(event) => setForm({ ...form, price: event.target.value })}
                />
              </Field>
              <Field label="Stock" error={fieldError(formError, 'stock')}>
                <input
                  className="input"
                  type="number"
                  min="0"
                  value={form.stock}
                  required
                  onChange={(event) => setForm({ ...form, stock: event.target.value })}
                />
              </Field>
            </div>
            <Field
              label="Slug"
              hint="Optional — generated from the name"
              error={fieldError(formError, 'slug')}
            >
              <input
                className="input"
                value={form.slug}
                onChange={(event) => setForm({ ...form, slug: event.target.value })}
              />
            </Field>
            <Field label="Description" error={fieldError(formError, 'description')}>
              <textarea
                className="textarea"
                rows={4}
                value={form.description}
                required
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </Field>
            <Field label="Image" hint="JPEG or PNG, up to 5 MB" error={fieldError(formError, 'image')}>
              <input
                className="input"
                type="file"
                accept="image/*"
                onChange={(event) => setForm({ ...form, image: event.target.files?.[0] ?? null })}
              />
            </Field>
          </form>
        ) : null}
      </Modal>

      <Modal
        open={confirmDelete !== null}
        title="Delete product"
        description={
          confirmDelete
            ? `“${confirmDelete.name}” will be removed from the storefront.`
            : undefined
        }
        onClose={() => setConfirmDelete(null)}
        footer={
          <>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setConfirmDelete(null)}>
              Keep it
            </button>
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={() => void remove()}
              disabled={deleting}
            >
              {deleting ? 'Deleting…' : 'Delete product'}
            </button>
          </>
        }
      >
        <p className="muted">
          Products that already appear in a cart or an order cannot be deleted. Cancel the related
          orders first.
        </p>
      </Modal>
    </div>
  )
}

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.'
}
