import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api, tokenStore } from '../lib/api'
import type { AuthResponse, User } from '../types'
import { AuthContext } from './auth-context'
import type { AuthContextValue } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(() => tokenStore.access === null)

  const clearSession = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  const applySession = useCallback((response: AuthResponse) => {
    tokenStore.set(response.access, response.refresh)
    setUser(response.user)
  }, [])

  const refreshUser = useCallback(async () => {
    if (!tokenStore.access) return
    try {
      setUser(await api.auth.profile())
    } catch {
      clearSession()
    } finally {
      setReady(true)
    }
  }, [clearSession])

  useEffect(() => {
    if (!tokenStore.access) return
    let cancelled = false
    api.auth
      .profile()
      .then((profile) => {
        if (!cancelled) setUser(profile)
      })
      .catch(() => {
        if (!cancelled) clearSession()
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [clearSession])

  useEffect(() => {
    const handleExpired = () => clearSession()
    window.addEventListener('eshop:session-expired', handleExpired)
    return () => window.removeEventListener('eshop:session-expired', handleExpired)
  }, [clearSession])

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.auth.login(email, password)
      applySession(response)
      return response.user
    },
    [applySession],
  )

  const logout = useCallback(async () => {
    const refresh = tokenStore.refresh
    try {
      if (refresh && tokenStore.access) await api.auth.logout(refresh)
    } catch {
      tokenStore.clear()
    }
    clearSession()
  }, [clearSession])

  const updateProfile = useCallback<AuthContextValue['updateProfile']>(async (payload) => {
    const updated = await api.auth.updateProfile(payload)
    setUser(updated)
    return updated
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, ready, login, applySession, logout, refreshUser, updateProfile }),
    [user, ready, login, applySession, logout, refreshUser, updateProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
