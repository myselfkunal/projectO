import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '@/utils/api'
import { useAuthStore } from '@/context/authStore'

interface CallHistoryItem {
  id: string
  initiator_id: string
  receiver_id: string
  initiator_username?: string | null
  receiver_username?: string | null
  status: string
  started_at: string
  ended_at?: string | null
  duration_seconds?: number
}

export const CallHistory = () => {
  const currentUser = useAuthStore(state => state.user)
  const navigate = useNavigate()
  const [history, setHistory] = useState<CallHistoryItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  const parseApiDate = (value: string) => {
    if (!value) return new Date()
    const hasTimezone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value)
    return new Date(hasTimezone ? value : `${value}Z`)
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get<CallHistoryItem[]>('/calls/history')
      const filtered = currentUser?.id
        ? response.data.filter(call => call.initiator_id === currentUser.id || call.receiver_id === currentUser.id)
        : response.data
      const sorted = [...filtered].sort((a, b) => {
        const aTime = parseApiDate(a.ended_at || a.started_at).getTime()
        const bTime = parseApiDate(b.ended_at || b.started_at).getTime()
        return bTime - aTime
      })
      setHistory(sorted)
    } catch (err: any) {
      console.error('Error fetching call history:', err)
      setError(err.response?.data?.detail || 'Failed to fetch call history')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ background: '#111', color: 'white', minHeight: '100vh', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '1px solid #333', paddingBottom: '15px' }}>
        <div>
          <div style={{ fontSize: '28px', fontWeight: '700' }}>Call History</div>
          <div style={{ fontSize: '13px', color: '#888', marginTop: '5px' }}>
            Recent calls
          </div>
        </div>
        <button
          onClick={() => navigate('/dashboard')}
          style={{
            padding: '10px 16px',
            background: '#374151',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 600
          }}
        >
          Back to Dashboard
        </button>
      </div>

      {error && (
        <div style={{ background: '#7f1d1d', color: '#fca5a5', padding: '12px', borderRadius: '4px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ color: '#aaa' }}>Loading...</div>
      ) : history.length === 0 ? (
        <div style={{ padding: '30px', background: '#1a1a1a', border: '1px solid #333', borderRadius: '6px', color: '#aaa' }}>
          No call history yet.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {history.map(call => (
            <div key={call.id} style={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', padding: '16px' }}>
              <div style={{ fontWeight: 600, marginBottom: '6px' }}>
                {call.initiator_username || call.initiator_id} → {call.receiver_username || call.receiver_id}
              </div>
              <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '8px' }}>
                Status: {call.status}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>
                Started: {parseApiDate(call.started_at).toLocaleString()}
              </div>
              {call.ended_at && (
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  Ended: {parseApiDate(call.ended_at).toLocaleString()}
                </div>
              )}
              {typeof call.duration_seconds === 'number' && (
                <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px' }}>
                  Duration: {Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
