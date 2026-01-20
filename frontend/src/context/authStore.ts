import { create } from 'zustand'

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
  setUser: (user: User) => void
  setToken: (token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  
  setUser: (user: User) => set({ user, isAuthenticated: true }),
  
  setToken: (token: string) => {
    localStorage.setItem('token', token)
    set({ token, isAuthenticated: true })
  },
  
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, isAuthenticated: false })
  }
}))
