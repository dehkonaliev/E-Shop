import { createContext, useContext } from 'react'
import type { AuthResponse, User } from '../types'

export interface AuthContextValue {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<User>
  applySession: (response: AuthResponse) => void
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  updateProfile: (payload: {
    username: string
    first_name: string
    last_name: string
    phone_number: string
    age: number | null
  }) => Promise<User>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
