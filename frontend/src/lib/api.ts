import type {
  AuthResponse,
  Cart,
  Category,
  Comment,
  CustomerOrder,
  CustomerProfile,
  CustomerReport,
  DashboardStats,
  Like,
  LikeResponse,
  Order,
  OrderStatus,
  Paginated,
  Product,
  ProductSale,
  RegisterResponse,
  User,
  VerifyCodeResponse,
} from '../types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

const ACCESS_KEY = 'eshop.access'
const REFRESH_KEY = 'eshop.refresh'

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

type ErrorFields = Record<string, string[] | string>

export class ApiError extends Error {
  status: number
  fields: ErrorFields

  constructor(status: number, message: string, fields: ErrorFields = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fields = fields
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function buildError(status: number, payload: unknown): ApiError {
  if (isRecord(payload)) {
    const fields: ErrorFields = {}
    const messages: string[] = []
    for (const [key, value] of Object.entries(payload)) {
      const list = Array.isArray(value) ? value.map(String) : [String(value)]
      fields[key] = list
      if (key === 'detail') {
        messages.push(...list)
      } else {
        messages.push(...list.map((item) => `${key}: ${item}`))
      }
    }
    if (messages.length > 0) {
      return new ApiError(status, messages.join(' '), fields)
    }
  }
  const fallback =
    status === 404
      ? 'We could not find what you were looking for.'
      : status === 429
        ? 'Too many attempts. Please wait a moment and try again.'
        : status >= 500
          ? 'Something went wrong on our side. Please try again.'
          : 'The request could not be completed.'
  return new ApiError(status, fallback)
}

function readPayload(text: string): unknown {
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    return null
  }
}

let refreshInFlight: Promise<boolean> | null = null

async function refreshAccessToken(): Promise<boolean> {
  const refresh = tokenStore.refresh
  if (!refresh) return false
  if (!refreshInFlight) {
    const pending = (async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/auth/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        })
        if (!response.ok) {
          tokenStore.clear()
          return false
        }
        const data = (await response.json()) as { access: string; refresh?: string }
        tokenStore.set(data.access, data.refresh)
        return true
      } catch {
        return false
      }
    })()
    refreshInFlight = pending
    const result = await pending
    if (refreshInFlight === pending) refreshInFlight = null
    return result
  }
  return refreshInFlight
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  allowRefresh = true,
): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const access = tokenStore.access
  if (access) headers.set('Authorization', `Bearer ${access}`)

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (response.status === 401 && allowRefresh && tokenStore.refresh && !path.includes('/auth/')) {
    const refreshed = await refreshAccessToken()
    if (refreshed) return apiFetch<T>(path, options, false)
    tokenStore.clear()
    window.dispatchEvent(new Event('eshop:session-expired'))
  }

  if (response.status === 204) return undefined as T

  const text = await response.text()
  const payload = readPayload(text)
  if (!response.ok) throw buildError(response.status, payload)
  return payload as T
}

function query(params: object): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    search.set(key, String(value))
  }
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

function body(payload: unknown): RequestInit {
  return { body: JSON.stringify(payload) }
}

export interface ProductQuery {
  category?: string
  category_id?: number
  min_price?: string
  max_price?: string
  in_stock?: string
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}

export interface SalesQuery {
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}

export interface CustomerQuery {
  search?: string
  ordering?: string
  has_orders?: string
  page?: number
  page_size?: number
}

export interface ProductWritePayload {
  category: number
  name: string
  description: string
  price: string
  stock: number
  image?: File | null
  slug?: string
}

export interface CategoryWritePayload {
  name: string
  parent: number | null
  slug?: string
}

function formData(payload: ProductWritePayload): FormData {
  const data = new FormData()
  data.set('category', String(payload.category))
  data.set('name', payload.name)
  data.set('description', payload.description)
  data.set('price', payload.price)
  data.set('stock', String(payload.stock))
  if (payload.slug) data.set('slug', payload.slug)
  if (payload.image) data.set('image', payload.image)
  return data
}

export const api = {
  products: {
    list: (params: ProductQuery = {}) =>
      apiFetch<Paginated<Product>>(`/api/products/${query(params)}`),
    get: (id: number) => apiFetch<Product>(`/api/products/${id}/`),
    toggleLike: (id: number) =>
      apiFetch<LikeResponse>(`/api/products/${id}/like/`, { method: 'POST' }),
  },
  admin: {
    dashboard: () => apiFetch<DashboardStats>('/api/reports/dashboard/'),
    sales: (params: SalesQuery = {}) =>
      apiFetch<Paginated<ProductSale>>(`/api/reports/sales/${query(params)}`),
    customers: (params: CustomerQuery = {}) =>
      apiFetch<Paginated<CustomerReport>>(`/api/reports/customers/${query(params)}`),
    customer: (id: number) => apiFetch<CustomerProfile>(`/api/reports/customers/${id}/`),
    customerOrders: (id: number, params: { page?: number; page_size?: number } = {}) =>
      apiFetch<Paginated<CustomerOrder>>(`/api/reports/customers/${id}/orders/${query(params)}`),
    createProduct: (payload: ProductWritePayload) =>
      apiFetch<Product>('/api/products/', { method: 'POST', body: formData(payload) }),
    updateProduct: (id: number, payload: ProductWritePayload) =>
      apiFetch<Product>(`/api/products/${id}/`, { method: 'PATCH', body: formData(payload) }),
    deleteProduct: (id: number) =>
      apiFetch<void>(`/api/products/${id}/`, { method: 'DELETE' }),
    createCategory: (payload: CategoryWritePayload) =>
      apiFetch<Category>('/api/categories/', { method: 'POST', ...body(payload) }),
    updateCategory: (id: number, payload: CategoryWritePayload) =>
      apiFetch<Category>(`/api/categories/${id}/`, { method: 'PATCH', ...body(payload) }),
    deleteCategory: (id: number) => apiFetch<void>(`/api/categories/${id}/`, { method: 'DELETE' }),
    setOrderStatus: (id: number, status: OrderStatus) =>
      apiFetch<Order>(`/api/orders/${id}/`, { method: 'PATCH', ...body({ status }) }),
  },
  categories: {
    list: () => apiFetch<Paginated<Category>>('/api/categories/?page_size=100'),
  },
  comments: {
    list: (productId: number) =>
      apiFetch<Paginated<Comment>>(`/api/products/${productId}/comments/`),
    create: (productId: number, payload: { text: string; rating: number }) =>
      apiFetch<Comment>(`/api/products/${productId}/comments/`, {
        method: 'POST',
        ...body(payload),
      }),
  },
  likes: {
    list: () => apiFetch<Paginated<Like>>('/api/likes/'),
  },
  cart: {
    get: () => apiFetch<Cart>('/api/cart/'),
    add: (productId: number, quantity = 1) =>
      apiFetch<Cart>('/api/cart/add/', {
        method: 'POST',
        ...body({ product_id: productId, quantity }),
      }),
    remove: (productId: number) =>
      apiFetch<Cart>('/api/cart/remove/', {
        method: 'POST',
        ...body({ product_id: productId }),
      }),
  },
  orders: {
    list: (params: { status?: OrderStatus; page?: number; page_size?: number } = {}) =>
      apiFetch<Paginated<Order>>(`/api/orders/${query(params)}`),
    checkout: (shippingAddress: string) =>
      apiFetch<Order>('/api/orders/checkout/', {
        method: 'POST',
        ...body({ shipping_address: shippingAddress }),
      }),
  },
  auth: {
    register: (email: string) =>
      apiFetch<RegisterResponse>('/api/auth/register/', { method: 'POST', ...body({ email }) }),
    confirmCode: (email: string, code: string) =>
      apiFetch<VerifyCodeResponse>('/api/auth/email/confirm/', {
        method: 'POST',
        ...body({ email, code }),
      }),
    activate: (payload: {
      token: string
      username: string
      password: string
      first_name?: string
      last_name?: string
      phone_number?: string
    }) => apiFetch<AuthResponse>('/api/auth/user-activation/', { method: 'POST', ...body(payload) }),
    login: (email: string, password: string) =>
      apiFetch<AuthResponse>('/api/auth/login/', { method: 'POST', ...body({ email, password }) }),
    profile: () => apiFetch<User>('/api/auth/profile/'),
    updateProfile: (payload: {
      username: string
      first_name: string
      last_name: string
      phone_number: string
      age: number | null
    }) => apiFetch<User>('/api/auth/profile/', { method: 'PATCH', ...body(payload) }),
    logout: (refresh: string) =>
      apiFetch<{ message: string }>('/api/auth/logout/', { method: 'POST', ...body({ refresh }) }),
  },
}

export function fieldError(error: unknown, field: string): string | null {
  if (error instanceof ApiError) {
    const value = error.fields[field]
    if (!value) return null
    return Array.isArray(value) ? (value[0] ?? null) : value
  }
  if (error instanceof Error) return error.message
  return null
}
