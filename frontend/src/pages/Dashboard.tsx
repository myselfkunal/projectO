import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import api from '@/utils/api'

interface AvailableUser {
  id: string
  username: string
  full_name: string
  profile_picture?: string
  bio?: string
  is_online: boolean
}

interface CallResponse {
  id: string
  initiator_id: string
  receiver_id: string
  status: string
  call_token: string
  started_at: string
  ended_at?: string
  duration_seconds: number
}

export const Dashboard = () => {
  const user = useAuthStore(state => state.user)
  const [availableUsers, setAvailableUsers] = useState<AvailableUser[]>([])
  const [error, setError] = useState<string | null>(null)
  const [calling, setCallingUserId] = useState<string | null>(null)
  const [pendingCall, setPendingCall] = useState<CallResponse | null>(null)
  const [pendingLoading, setPendingLoading] = useState<boolean>(false)
  const navigate = useNavigate()
  const pollTimerRef = useRef<number | null>(null)
  const isPollingRef = useRef(false)
  const isMountedRef = useRef(false)

  // Fetch available users and pending calls
  useEffect(() => {
    if (!user?.id) return

    isMountedRef.current = true

    const poll = async () => {
      if (!isMountedRef.current) return
      if (isPollingRef.current) {
        pollTimerRef.current = window.setTimeout(poll, 5000)
        return
      }

      isPollingRef.current = true
      await Promise.all([fetchAvailableUsers(), fetchPendingCall()])
      isPollingRef.current = false

      if (isMountedRef.current) {
        pollTimerRef.current = window.setTimeout(poll, 5000)
      }
    }

    poll()

    return () => {
      isMountedRef.current = false
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current)
      }
    }
  }, [user?.id])

  const fetchAvailableUsers = async () => {
    try {
      setError(null)
      const response = await api.get('/calls/available')
      if (!isMountedRef.current) return
      setAvailableUsers(response.data)
    } catch (err: any) {
      console.error('Error fetching available users:', err)
      if (!isMountedRef.current) return
      if (err.response?.status !== 404) {
        setError(err.response?.data?.detail || 'Failed to fetch available users')
      }
    }
  }

  const fetchPendingCall = async () => {
    try {
      const response = await api.get<CallResponse | null>('/calls/pending')
      if (!isMountedRef.current) return
      setPendingCall(response.data)
    } catch (err) {
      console.error('Error fetching pending call:', err)
    }
  }

  const handleAcceptCall = async () => {
    if (!pendingCall) return

    try {
      setPendingLoading(true)
      const response = await api.post<CallResponse>(`/calls/accept/${pendingCall.id}`)
      const callData = response.data

      const jwtToken = localStorage.getItem('token')
      navigate(`/call/${callData.id}?token=${encodeURIComponent(jwtToken || '')}`)
    } catch (err: any) {
      console.error('Error accepting call:', err)
      setError(err.response?.data?.detail || 'Failed to accept call')
    } finally {
      setPendingLoading(false)
    }
  }

  const handleRejectCall = async () => {
    if (!pendingCall) return

    try {
      setPendingLoading(true)
      await api.post(`/calls/reject/${pendingCall.id}`)
      setPendingCall(null)
    } catch (err: any) {
      console.error('Error rejecting call:', err)
      setError(err.response?.data?.detail || 'Failed to reject call')
    } finally {
      setPendingLoading(false)
    }
  }

  const handleStartCall = async (receiverId: string) => {
    try {
      setError(null)
      setCallingUserId(receiverId)

      // Initiate call via API
      const response = await api.post<CallResponse>('/calls/initiate', {
        receiver_id: receiverId,
      })

      const callData = response.data
      console.log('Call initiated:', callData)

      // Get JWT token from localStorage
      const jwtToken = localStorage.getItem('token')
      
      // Redirect to call page with call ID and JWT token
      navigate(`/call/${callData.id}?token=${encodeURIComponent(jwtToken || '')}`)
    } catch (err: any) {
      console.error('Error starting call:', err)
      setError(err.response?.data?.detail || 'Failed to start call')
      setCallingUserId(null)
    }
  }

  const handleLogout = () => {
    try {
      api.post('/auth/logout').catch(() => null)
    } finally {
      localStorage.removeItem('token')
      navigate('/login')
    }
  }

  return (
    <div style={{ background: '#111', color: 'white', minHeight: '100vh', padding: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px', borderBottom: '1px solid #333', paddingBottom: '20px' }}>
        <div>
          <div style={{ fontSize: '32px', fontWeight: 'bold' }}>UniLink</div>
          <div style={{ fontSize: '14px', color: '#888', marginTop: '5px' }}>
            Logged in as: {user?.username || 'loading...'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => navigate('/history')}
            style={{
              padding: '10px 16px',
              fontSize: '14px',
              cursor: 'pointer',
              background: '#374151',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontWeight: '500'
            }}
          >
            Call History
          </button>
          <button
            onClick={() => navigate('/profile')}
            style={{
              padding: '10px 16px',
              fontSize: '14px',
              cursor: 'pointer',
              background: '#1f2937',
              color: 'white',
              border: '1px solid #374151',
              borderRadius: '4px',
              fontWeight: '500'
            }}
          >
            My Profile
          </button>
          <button
            onClick={handleLogout}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              cursor: 'pointer',
              background: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontWeight: '500'
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ background: '#7f1d1d', color: '#fca5a5', padding: '12px', borderRadius: '4px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {pendingCall && (
        <div style={{ background: '#1f2937', border: '1px solid #374151', padding: '16px', borderRadius: '8px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '16px', fontWeight: '600' }}>Incoming call</div>
            <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '4px' }}>
              Call ID: {pendingCall.id}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleRejectCall}
              disabled={pendingLoading}
              style={{
                padding: '8px 14px',
                background: '#7f1d1d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: pendingLoading ? 'not-allowed' : 'pointer'
              }}
            >
              Reject
            </button>
            <button
              onClick={handleAcceptCall}
              disabled={pendingLoading}
              style={{
                padding: '8px 14px',
                background: '#16a34a',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: pendingLoading ? 'not-allowed' : 'pointer'
              }}
            >
              {pendingLoading ? 'Accepting...' : 'Accept'}
            </button>
          </div>
        </div>
      )}

      {/* Available Users Section */}
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px' }}>
          Available Users ({availableUsers.length})
        </h2>

        {availableUsers.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666', background: '#1a1a1a', borderRadius: '4px' }}>
            No users available for calling right now
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {availableUsers.map((availableUser) => (
              <div 
                key={availableUser.id}
                style={{
                  background: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: '8px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                {/* User Info */}
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '5px' }}>
                    {availableUser.full_name || availableUser.username}
                  </div>
                  <div style={{ fontSize: '14px', color: '#888', marginBottom: '10px' }}>
                    @{availableUser.username}
                  </div>
                  {availableUser.bio && (
                    <div style={{ fontSize: '13px', color: '#aaa', marginBottom: '10px', minHeight: '40px' }}>
                      {availableUser.bio}
                    </div>
                  )}
                  <div style={{ fontSize: '12px', color: '#4ade80', marginTop: '10px' }}>
                    🟢 Online
                  </div>
                </div>

                {/* Start Call Button */}
                <button
                  onClick={() => handleStartCall(availableUser.id)}
                  disabled={calling === availableUser.id}
                  style={{
                    marginTop: '15px',
                    padding: '10px 16px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: calling === availableUser.id ? 'not-allowed' : 'pointer',
                    background: calling === availableUser.id ? '#666' : '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    opacity: calling === availableUser.id ? 0.7 : 1,
                    transition: 'all 0.2s'
                  }}
                >
                  {calling === availableUser.id ? 'Calling...' : 'Start Call'}
                </button>

                <button
                  onClick={() => navigate(`/users/${availableUser.id}`)}
                  style={{
                    marginTop: '10px',
                    padding: '8px 14px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    background: '#374151',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px'
                  }}
                >
                  View Profile
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

