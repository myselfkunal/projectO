import { create } from 'zustand'
import { authService } from '@/utils/authService'

export interface User {
  id: string
  email: string
  username: string
  full_name: string
  profile_picture?: string
  bio?: string
  is_verified: boolean
  is_online: boolean
  created_at: string
}

export interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  initialized: boolean
  setUser: (user: User) => void
  setToken: (token: string) => void
  init: () => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  initialized: false,
  
  setUser: (user: User) => set({ user, isAuthenticated: true }),
  
  setToken: (token: string) => {
    localStorage.setItem('token', token)
    set({ token, isAuthenticated: true })
  },

  init: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ user: null, token: null, isAuthenticated: false, initialized: true })
      return
    }

    try {
      const user = await authService.getCurrentUser()
      set({ user, token, isAuthenticated: true, initialized: true })
    } catch (err) {
      console.error('Auth init failed', err)
      localStorage.removeItem('token')
      set({ user: null, token: null, isAuthenticated: false, initialized: true })
    }
  },
  
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, isAuthenticated: false, initialized: true })
  }
}))
