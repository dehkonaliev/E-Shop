import { createContext, useContext } from 'react'
import type { Cart, Order } from '../types'

export interface CartContextValue {
  cart: Cart | null
  count: number
  total: string
  loading: boolean
  add: (productId: number, quantity?: number) => Promise<void>
  setQuantity: (productId: number, quantity: number) => Promise<void>
  remove: (productId: number) => Promise<void>
  checkout: (shippingAddress: string) => Promise<Order>
  reload: () => Promise<void>
  clearLocal: () => void
}

export const CartContext = createContext<CartContextValue | null>(null)

export function useCart(): CartContextValue {
  const context = useContext(CartContext)
  if (!context) throw new Error('useCart must be used inside CartProvider')
  return context
}
