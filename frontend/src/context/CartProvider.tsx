import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../lib/api'
import type { Cart } from '../types'
import { useAuth } from './auth-context'
import { CartContext } from './cart-context'
import type { CartContextValue } from './cart-context'

const emptyCart: Cart = {
  id: 0,
  uuid: '',
  items: [],
  total_price: '0.00',
  created_at: '',
  updated_at: '',
}

export function CartProvider({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const [cart, setCart] = useState<Cart | null | undefined>(undefined)

  const reload = useCallback(async () => {
    setCart(await api.cart.get())
  }, [])

  useEffect(() => {
    if (!ready || !user) return
    let cancelled = false
    api.cart
      .get()
      .then((result) => {
        if (!cancelled) setCart(result)
      })
      .catch(() => {
        if (!cancelled) setCart(null)
      })
    return () => {
      cancelled = true
    }
  }, [ready, user])

  const add = useCallback(async (productId: number, quantity = 1) => {
    setCart(await api.cart.add(productId, quantity))
  }, [])

  const setQuantity = useCallback(async (productId: number, quantity: number) => {
    if (quantity < 1) return
    setCart(await api.cart.add(productId, quantity))
  }, [])

  const remove = useCallback(async (productId: number) => {
    setCart(await api.cart.remove(productId))
  }, [])

  const checkout = useCallback(async (shippingAddress: string) => {
    const order = await api.orders.checkout(shippingAddress)
    setCart(emptyCart)
    return order
  }, [])

  const clearLocal = useCallback(() => setCart(null), [])

  const value = useMemo<CartContextValue>(() => {
    const current = cart === undefined ? null : cart
    return {
      cart: current,
      count: current?.items.reduce((total, item) => total + item.quantity, 0) ?? 0,
      total: current?.total_price ?? '0.00',
      loading: ready && user !== null && cart === undefined,
      add,
      setQuantity,
      remove,
      checkout,
      reload,
      clearLocal,
    }
  }, [cart, ready, user, add, setQuantity, remove, checkout, reload, clearLocal])

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}
