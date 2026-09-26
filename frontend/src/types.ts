export type UserRole = 'admin' | 'customer'

export interface User {
  id: number
  uuid: string
  username: string
  email: string
  first_name: string
  last_name: string
  phone_number: string | null
  age: number | null
  role: UserRole
  is_staff: boolean
}

export interface Category {
  id: number
  uuid: string
  name: string
  slug: string
  parent: number | null
  parent_name: string | null
  created_at: string
  updated_at: string
}

export interface Product {
  id: number
  uuid: string
  category: number
  category_name: string
  name: string
  slug: string
  description: string
  price: string
  stock: number
  image: string
  likes_count: number
  average_rating: string | null
  is_liked: boolean
  created_at: string
  updated_at: string
}

export interface ProductSummary {
  id: number
  uuid: string
  name: string
  slug: string
  price: string
  stock: number
  image: string
}

export interface Like {
  id: number
  uuid: string
  product: ProductSummary
  created_at: string
}

export interface Comment {
  id: number
  uuid: string
  user: string
  user_id: number
  product: number
  text: string
  rating: number
  created_at: string
}

export interface CartItem {
  id: number
  product: number
  product_name: string
  quantity: number
  unit_price: string
  line_total: string
}

export interface Cart {
  id: number
  uuid: string
  items: CartItem[]
  total_price: string
  created_at: string
  updated_at: string
}

export type OrderStatus = 'pending' | 'shipping' | 'completed' | 'cancelled'

export interface OrderItem {
  id: number
  product: number
  product_name: string
  quantity: number
  price_at_that_time: string
  line_total: string
}

export interface Order {
  id: number
  uuid: string
  user: number
  user_username: string
  user_email: string
  total_price: string
  status: OrderStatus
  status_display: string
  shipping_address: string
  items: OrderItem[]
  item_count: number
  created_at: string
  updated_at: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AuthResponse {
  access: string
  refresh: string
  user: User
}

export interface RegisterResponse {
  message: string
  data: { email: string }
}

export interface VerifyCodeResponse {
  message: string
  email: string
  token: string
  activation_token: string
  activation_required: boolean
}

export interface LikeResponse {
  liked: boolean
  product_id: number
  likes_count: number
}

export interface DashboardStats {
  generated_at: string
  products: {
    total: number
    in_stock: number
    sold_out: number
    low_stock: number
    units_in_stock: number
    catalogue_value: string
  }
  categories: { total: number }
  customers: { total: number; with_orders: number; new_this_month: number }
  orders: {
    total: number
    pending: number
    shipping: number
    completed: number
    cancelled: number
    revenue: string
  }
  sales: { units: number; revenue: string; average_order: string }
  top_products: ProductSale[]
  top_customers: TopCustomer[]
  recent_orders: RecentOrder[]
  low_stock: LowStockItem[]
  sales_by_day: { date: string; orders: number; revenue: string }[]
  category_breakdown: {
    id: number
    name: string
    products: number
    units_sold: number
    revenue: string
  }[]
}

export interface ProductSale {
  id: number
  name: string
  slug: string
  image: string | null
  category: string | null
  category_id: number
  price: string
  stock: number
  units_sold: number
  revenue: string
  order_count: number
  created_at: string
}

export interface TopCustomer {
  id: number
  username: string
  email: string
  order_count: number
  total_spent: string
  last_order_at: string | null
}

export interface RecentOrder {
  id: number
  uuid: string
  username: string
  email: string
  status: OrderStatus
  status_display: string
  total_price: string
  item_count: number
  created_at: string
}

export interface LowStockItem {
  id: number
  name: string
  category: string | null
  stock: number
}

export interface CustomerReport {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  is_active: boolean
  date_joined: string
  order_count: number
  pending_orders: number
  shipping_orders: number
  completed_orders: number
  cancelled_orders: number
  total_spent: string
  last_order_at: string | null
}

export interface CustomerProfile extends CustomerReport {
  phone_number: string | null
  age: number | null
  is_staff: boolean
  last_login: string | null
  full_name: string
}

export interface CustomerOrder {
  id: number
  uuid: string
  status: OrderStatus
  status_display: string
  total_price: string
  item_count: number
  shipping_address: string
  created_at: string
}
