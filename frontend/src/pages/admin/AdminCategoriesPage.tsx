import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { FolderPlus, Pencil, Trash2 } from 'lucide-react'
import {
  AdminPageHeader,
  AdminTable,
  EmptyRow,
  Modal,
  Notice,
  Panel,
} from '../../components/admin/AdminUI'
import { ErrorNote, Field, PageLoader } from '../../components/ui'
import { api, ApiError, fieldError } from '../../lib/api'
import { formatDate, pluralize } from '../../lib/format'
import type { Category, Paginated } from '../../types'

interface FormState {
  id: number | null
  name: string
  slug: string
  parent: string
}

const emptyForm: FormState = { id: null, name: '', slug: '', parent: '' }

interface TreeRow {
  category: Category
  depth: number
}

export function AdminCategoriesPage() {
  const [data, setData] = useState<Paginated<Category> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<FormState | null>(null)
  const [formError, setFormError] = useState<unknown>(null)
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<Category | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [flash, setFlash] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await api.categories.list())
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Categories could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const rows = useMemo<TreeRow[]>(() => {
    const all = data?.results ?? []
    const byParent = new Map<number | null, Category[]>()
    for (const category of all) {
      const key = category.parent
      const bucket = byParent.get(key)
      if (bucket) bucket.push(category)
      else byParent.set(key, [category])
    }
    const ordered: TreeRow[] = []
    const walk = (parent: number | null, depth: number) => {
      const bucket = byParent.get(parent)
      if (!bucket) return
      for (const category of bucket) {
        ordered.push({ category, depth })
        walk(category.id, depth + 1)
      }
    }
    walk(null, 0)
    for (const category of all) {
      if (!ordered.some((row) => row.category.id === category.id)) {
        ordered.push({ category, depth: 0 })
      }
    }
    return ordered
  }, [data])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!form) return
    setSaving(true)
    setFormError(null)
    const payload = {
      name: form.name.trim(),
      parent: form.parent ? Number.parseInt(form.parent, 10) : null,
      slug: form.slug.trim() || undefined,
    }
    try {
      if (form.id) {
        await api.admin.updateCategory(form.id, payload)
        setFlash(`“${payload.name}” was updated.`)
      } else {
        await api.admin.createCategory(payload)
        setFlash(`“${payload.name}” was created.`)
      }
      setForm(null)
      await load()
    } catch (caught) {
      setFormError(caught)
    } finally {
      setSaving(false)
    }
  }

  const remove = async () => {
    if (!confirmDelete) return
    setDeleting(true)
    setError(null)
    try {
      await api.admin.deleteCategory(confirmDelete.id)
      setFlash(`“${confirmDelete.name}” was deleted.`)
      setConfirmDelete(null)
      await load()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Category could not be deleted. Remove its products and subcategories first.',
      )
      setConfirmDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  const total = data?.count ?? 0

  return (
    <div className="admin-stack">
      <AdminPageHeader
        eyebrow="Catalogue"
        title="Categories"
        description="Group products, nest subcategories, and remove empty groups."
        actions={
          <button
            type="button"
            className="btn btn-dark btn-sm"
            onClick={() => {
              setFormError(null)
              setForm({ ...emptyForm })
            }}
          >
            <FolderPlus size={15} strokeWidth={1.9} />
            New category
          </button>
        }
      />

      {flash ? <Notice tone="success" onClose={() => setFlash(null)}>{flash}</Notice> : null}
      {error ? <ErrorNote message={error} onRetry={() => void load()} /> : null}

      <Panel title="All categories" description={`${total} ${pluralize(total, 'category')}`}>
        {loading && !data ? <PageLoader label="Loading categories" /> : null}
        {data ? (
          <AdminTable>
            <thead>
              <tr>
                <th>Name</th>
                <th>Slug</th>
                <th>Parent</th>
                <th>Created</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <EmptyRow colSpan={5}>
                  No categories yet. Create one before adding products.
                </EmptyRow>
              ) : (
                rows.map(({ category, depth }) => (
                  <tr
                    key={category.id}
                    className="row-clickable"
                    onClick={() => {
                      setFormError(null)
                      setForm({
                        id: category.id,
                        name: category.name,
                        slug: category.slug,
                        parent: category.parent ? String(category.parent) : '',
                      })
                    }}
                  >
                    <td>
                      <span
                        className="cell-strong"
                        style={{ paddingLeft: `${depth * 18}px`, display: 'inline-block' }}
                      >
                        {depth > 0 ? '↳ ' : ''}
                        {category.name}
                      </span>
                    </td>
                    <td className="muted">{category.slug}</td>
                    <td className="muted">{category.parent_name ?? '—'}</td>
                    <td className="muted">{formatDate(category.created_at)}</td>
                    <td className="actions" onClick={(event) => event.stopPropagation()}>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => {
                          setFormError(null)
                          setForm({
                            id: category.id,
                            name: category.name,
                            slug: category.slug,
                            parent: category.parent ? String(category.parent) : '',
                          })
                        }}
                      >
                        <Pencil size={14} strokeWidth={1.8} aria-hidden="true" />
                        Edit
                      </button>
                      <button
                        type="button"
                        className="icon-btn danger"
                        aria-label={`Delete ${category.name}`}
                        title="Delete"
                        onClick={() => setConfirmDelete(category)}
                      >
                        <Trash2 size={15} strokeWidth={1.8} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </AdminTable>
        ) : null}
      </Panel>

      <Modal
        open={form !== null}
        title={form?.id ? 'Edit category' : 'New category'}
        onClose={() => setForm(null)}
        footer={
          <>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setForm(null)}>
              Cancel
            </button>
            <button type="submit" form="category-form" className="btn btn-dark btn-sm" disabled={saving}>
              {saving ? 'Saving…' : form?.id ? 'Save changes' : 'Create category'}
            </button>
          </>
        }
      >
        {form ? (
          <form id="category-form" className="admin-form" onSubmit={submit} noValidate>
            {formError ? (
              <Notice tone="error">
                {formError instanceof ApiError ? formError.message : 'Something went wrong.'}
              </Notice>
            ) : null}
            <Field label="Name" error={fieldError(formError, 'name')}>
              <input
                className="input"
                value={form.name}
                required
                maxLength={150}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </Field>
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
            <Field label="Parent category" error={fieldError(formError, 'parent')}>
              <select
                className="select"
                value={form.parent}
                onChange={(event) => setForm({ ...form, parent: event.target.value })}
              >
                <option value="">No parent (top level)</option>
                {(data?.results ?? [])
                  .filter((category) => category.id !== form.id)
                  .map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.parent_name ? `${category.parent_name} / ` : ''}
                      {category.name}
                    </option>
                  ))}
              </select>
            </Field>
          </form>
        ) : null}
      </Modal>

      <Modal
        open={confirmDelete !== null}
        title="Delete category"
        description={confirmDelete ? `“${confirmDelete.name}” will be removed.` : undefined}
        onClose={() => setConfirmDelete(null)}
        footer={
          <>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setConfirmDelete(null)}
            >
              Keep it
            </button>
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={() => void remove()}
              disabled={deleting}
            >
              {deleting ? 'Deleting…' : 'Delete category'}
            </button>
          </>
        }
      >
        <p className="muted">
          A category can only be deleted when it has no products and no subcategories.
        </p>
      </Modal>
    </div>
  )
}
