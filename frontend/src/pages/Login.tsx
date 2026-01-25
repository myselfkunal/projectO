import { useState, FC } from 'react'
import { authService } from '@/utils/authService'
import { useAuthStore } from '@/context/authStore'

export const Login: FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const setToken = useAuthStore(state => state.setToken)
  const setUser = useAuthStore(state => state.setUser)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setInfo('')
    setLoading(true)

    try {
      if (!otpSent) {
        const response = await authService.login(email, password)
        if (response?.otp_required) {
          setOtpSent(true)
          setInfo(response.message || 'OTP sent to your email')
        } else {
          setError('Login failed')
        }
      } else {
        const response = await authService.verifyLoginOtp(email, otp)
        setToken(response.access_token)
        setUser(response.user)

        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 500)
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-2 text-gray-900">UniLink</h1>
        <p className="text-center text-gray-600 mb-8">Connect with your university</p>

        {info && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-6">
            {info}
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!otpSent && (
            <>
              <input
                type="email"
                placeholder="your.email@kiit.ac.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </>
          )}

          {otpSent && (
            <>
              <input
                type="text"
                inputMode="numeric"
                placeholder="Enter OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 tracking-widest text-center"
              />
              <button
                type="button"
                disabled={loading}
                onClick={async () => {
                  setError('')
                  setInfo('')
                  setLoading(true)
                  try {
                    const response = await authService.login(email, password)
                    if (response?.otp_required) {
                      setInfo(response.message || 'OTP resent to your email')
                    }
                  } catch (err: unknown) {
                    const error = err as { response?: { data?: { detail?: string } } }
                    setError(error.response?.data?.detail || 'Failed to resend OTP')
                  } finally {
                    setLoading(false)
                  }
                }}
                className="w-full py-2 border border-blue-500 text-blue-600 rounded-lg font-semibold hover:bg-blue-50 disabled:bg-gray-100 transition"
              >
                Resend OTP
              </button>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-600 disabled:bg-gray-400 transition"
          >
            {loading ? (otpSent ? 'Verifying...' : 'Sending OTP...') : (otpSent ? 'Verify OTP' : 'Login')}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-500 font-semibold hover:underline">
            Register
          </a>
        </p>
      </div>
    </div>
  )
}
