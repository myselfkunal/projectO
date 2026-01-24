import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '@/utils/api'
import { useAuthStore } from '@/context/authStore'

interface UserProfile {
  id: string
  username: string
  email: string
  full_name?: string | null
  bio?: string | null
  profile_picture?: string | null
  is_online?: boolean
}

export const Profile = () => {
  const { userId } = useParams<{ userId?: string }>()
  const currentUser = useAuthStore(state => state.user)
  const navigate = useNavigate()
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState<boolean>(false)
  const [blocking, setBlocking] = useState<boolean>(false)
  const [reporting, setReporting] = useState<boolean>(false)
  const [isBlocked, setIsBlocked] = useState<boolean>(false)
  const [reportReason, setReportReason] = useState<string>('spam')
  const [reportDescription, setReportDescription] = useState<string>('')

  const [fullName, setFullName] = useState<string>('')
  const [bio, setBio] = useState<string>('')
  const [profilePicture, setProfilePicture] = useState<string>('')

  const isOwnProfile = !userId || userId === currentUser?.id

  useEffect(() => {
    fetchProfile()
  }, [userId])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = userId
        ? await api.get<UserProfile>(`/users/${userId}`)
        : await api.get<UserProfile>('/users/me')

      setUser(response.data)
      setFullName(response.data.full_name || '')
      setBio(response.data.bio || '')
      setProfilePicture(response.data.profile_picture || '')
    } catch (err: any) {
      console.error('Error fetching profile:', err)
      setError(err.response?.data?.detail || 'Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setError(null)

      const response = await api.put<UserProfile>('/users/me', {
        full_name: fullName || null,
        bio: bio || null,
        profile_picture: profilePicture || null
      })

      setUser(response.data)
    } catch (err: any) {
      console.error('Error saving profile:', err)
      setError(err.response?.data?.detail || 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const handleBlockToggle = async () => {
    if (!user) return
    try {
      setBlocking(true)
      if (isBlocked) {
        await api.post(`/users/unblock/${user.id}`)
        setIsBlocked(false)
      } else {
        await api.post(`/users/block/${user.id}`)
        setIsBlocked(true)
      }
    } catch (err: any) {
      console.error('Error updating block status:', err)
      setError(err.response?.data?.detail || 'Failed to update block status')
    } finally {
      setBlocking(false)
    }
  }

  const handleReport = async () => {
    if (!user) return
    try {
      setReporting(true)
      await api.post(`/users/report/${user.id}`, {
        user_id: user.id,
        reason: reportReason,
        description: reportDescription || null
      })
      setReportDescription('')
    } catch (err: any) {
      console.error('Error reporting user:', err)
      setError(err.response?.data?.detail || 'Failed to report user')
    } finally {
      setReporting(false)
    }
  }

  return (
    <div style={{ background: '#111', color: 'white', minHeight: '100vh', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '1px solid #333', paddingBottom: '15px' }}>
        <div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>Profile</div>
          <div style={{ fontSize: '13px', color: '#888', marginTop: '5px' }}>
            {isOwnProfile ? 'Your profile' : 'User profile'}
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
      ) : user ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px, 320px) 1fr', gap: '20px' }}>
          <div style={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', padding: '20px' }}>
            <div style={{ width: '100%', aspectRatio: '1 / 1', borderRadius: '10px', background: '#0f172a', marginBottom: '12px', overflow: 'hidden' }}>
              {user.profile_picture ? (
                <img src={user.profile_picture} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>
                  No photo
                </div>
              )}
            </div>
            <div style={{ fontSize: '18px', fontWeight: 600 }}>{user.full_name || user.username}</div>
            <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '4px' }}>@{user.username}</div>
            {user.email && (
              <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>{user.email}</div>
            )}
          </div>

          <div style={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', padding: '20px' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Profile Details</div>

            <div style={{ display: 'grid', gap: '12px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af' }}>Full name</label>
              <input
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                disabled={!isOwnProfile}
                style={{ padding: '10px', borderRadius: '4px', border: '1px solid #333', background: '#0b0b0b', color: 'white' }}
              />

              <label style={{ fontSize: '12px', color: '#9ca3af' }}>Bio</label>
              <textarea
                value={bio}
                onChange={e => setBio(e.target.value)}
                disabled={!isOwnProfile}
                rows={4}
                style={{ padding: '10px', borderRadius: '4px', border: '1px solid #333', background: '#0b0b0b', color: 'white' }}
              />

              <label style={{ fontSize: '12px', color: '#9ca3af' }}>Profile picture URL</label>
              <input
                value={profilePicture}
                onChange={e => setProfilePicture(e.target.value)}
                disabled={!isOwnProfile}
                style={{ padding: '10px', borderRadius: '4px', border: '1px solid #333', background: '#0b0b0b', color: 'white' }}
              />

              {isOwnProfile && (
                <button
                  onClick={handleSave}
                  disabled={saving}
                  style={{
                    marginTop: '10px',
                    padding: '10px 16px',
                    background: saving ? '#4b5563' : '#16a34a',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: saving ? 'not-allowed' : 'pointer',
                    fontWeight: 600
                  }}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              )}

              {!isOwnProfile && (
                <div style={{ marginTop: '10px', display: 'grid', gap: '12px' }}>
                  <button
                    onClick={handleBlockToggle}
                    disabled={blocking}
                    style={{
                      padding: '10px 16px',
                      background: isBlocked ? '#4b5563' : '#dc2626',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: blocking ? 'not-allowed' : 'pointer',
                      fontWeight: 600
                    }}
                  >
                    {blocking ? 'Please wait...' : isBlocked ? 'Unblock User' : 'Block User'}
                  </button>

                  <div style={{ fontSize: '14px', fontWeight: 600, marginTop: '4px' }}>Report User</div>
                  <select
                    value={reportReason}
                    onChange={e => setReportReason(e.target.value)}
                    style={{ padding: '10px', borderRadius: '4px', border: '1px solid #333', background: '#0b0b0b', color: 'white' }}
                  >
                    <option value="spam">Spam</option>
                    <option value="harassment">Harassment</option>
                    <option value="impersonation">Impersonation</option>
                    <option value="other">Other</option>
                  </select>
                  <textarea
                    value={reportDescription}
                    onChange={e => setReportDescription(e.target.value)}
                    rows={3}
                    placeholder="Additional details (optional)"
                    style={{ padding: '10px', borderRadius: '4px', border: '1px solid #333', background: '#0b0b0b', color: 'white' }}
                  />
                  <button
                    onClick={handleReport}
                    disabled={reporting}
                    style={{
                      padding: '10px 16px',
                      background: '#2563eb',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: reporting ? 'not-allowed' : 'pointer',
                      fontWeight: 600
                    }}
                  >
                    {reporting ? 'Reporting...' : 'Report User'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ color: '#aaa' }}>Profile not found.</div>
      )}
    </div>
  )
}
