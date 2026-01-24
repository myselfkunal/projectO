import { ReactNode, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { Register } from '@/pages/Register'
import { VerifyEmail } from '@/pages/VerifyEmail'
import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
import { Call } from '@/pages/Call'
import { CallHistory } from '@/pages/CallHistory'
import { Profile } from '@/pages/Profile'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import '@/index.css'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

export function App() {
  const initialized = useAuthStore(state => state.initialized)
  const initAuth = useAuthStore(state => state.init)
  const user = useAuthStore(state => state.user)
  const token = useAuthStore(state => state.token)
  const presenceWsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    initAuth()
  }, [initAuth])

  useEffect(() => {
    if (!user?.id || !token) return

    const apiUrl = (((import.meta as unknown) as Record<string, Record<string, string>>).env.VITE_API_URL) || 'http://localhost:8000'
    const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://')
    const ws = new WebSocket(`${wsUrl}/calls/ws/${user.id}?token=${token}`)

    let pingInterval: ReturnType<typeof setInterval> | null = null

    ws.onopen = () => {
      pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 30000)
    }

    ws.onclose = () => {
      if (pingInterval) {
        clearInterval(pingInterval)
      }
    }

    presenceWsRef.current = ws

    const handleUnload = () => {
      fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        keepalive: true
      }).catch(() => null)
      try {
        ws.close()
      } catch {
        // ignore
      }
    }

    window.addEventListener('beforeunload', handleUnload)

    return () => {
      window.removeEventListener('beforeunload', handleUnload)
      if (pingInterval) {
        clearInterval(pingInterval)
      }
      if (presenceWsRef.current) {
        presenceWsRef.current.close()
        presenceWsRef.current = null
      }
    }
  }, [user?.id, token])

  if (!initialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 text-gray-700">
        Loading...
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/verify" element={<VerifyEmail />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/call/:callId"
            element={
              <ProtectedRoute>
                <Call />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <CallHistory />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users/:userId"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
