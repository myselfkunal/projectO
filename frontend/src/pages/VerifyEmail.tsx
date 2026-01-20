import { useState, useEffect, FC } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '@/utils/api'
import { useAuthStore } from '@/context/authStore'

export const VerifyEmail: FC = () => {
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const setToken = useAuthStore(state => state.setToken)
  const setUser = useAuthStore(state => state.setUser)

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setError('Invalid verification link')
    }
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await api.post('/auth/verify-email', {
        token,
      })

      setToken(response.data.access_token)
      setUser(response.data.user)
      setSuccess(true)

      setTimeout(() => {
        window.location.href = '/dashboard'
      }, 1500)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-2 text-gray-900">Verify Email</h1>
        <p className="text-center text-gray-600 mb-8">Complete your registration</p>

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
            Email verified! Redirecting...
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <button
            type="submit"
            disabled={loading || !token}
            className="w-full py-2 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-600 disabled:bg-gray-400 transition"
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </button>
        </form>
      </div>
    </div>
  )
}
