import type { User } from '../types'

export function hasAdminAccess(user: User | null): boolean {
  return Boolean(user && (user.role === 'admin' || user.is_staff))
}
