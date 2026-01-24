import { useState, useEffect, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import api from '@/utils/api'
import { VideoDisplay } from '@/components/VideoDisplay'
import { ChatBox } from '@/components/ChatBox'
import { CallTimer } from '@/components/CallTimer'

interface CallState {
  id: string
  status: string
  initiator_id: string
  receiver_id: string
  started_at: string
}

export const Call = () => {
  const { callId } = useParams<{ callId: string }>()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const user = useAuthStore(state => state.user)
  
  const [callState, setCallState] = useState<CallState | null>(null)
  const [localStream, setLocalStream] = useState<MediaStream | null>(null)
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [callStartTime, setCallStartTime] = useState<Date | null>(null)
  const [isInitiator, setIsInitiator] = useState<boolean>(false)
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [userNameById, setUserNameById] = useState<Record<string, string>>({})
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [isCameraOff, setIsCameraOff] = useState<boolean>(false)
  const [connectionState, setConnectionState] = useState<string>('connecting')
  const reconnectAttemptsRef = useRef<number>(0)
  const reconnectTimerRef = useRef<number | null>(null)
  const shouldReconnectRef = useRef<boolean>(true)
  const wsRef = useRef<WebSocket | null>(null)
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null)
  const localStreamRef = useRef<MediaStream | null>(null)
  const isInitiatorRef = useRef<boolean>(false)
  const remoteReadyRef = useRef<boolean>(false)
  const offerSentRef = useRef<boolean>(false)

  // Initialize call
  useEffect(() => {
    if (!callId || !token || !user?.id) return
    
    initializeCall()
    return () => {
      cleanupCall()
    }
  }, [callId, token, user?.id])

  useEffect(() => {
    if (user?.id && user.username) {
      setUserNameById(prev => ({ ...prev, [user.id]: user.username }))
    }
  }, [user?.id, user?.username])

  useEffect(() => {
    const fetchRemoteUser = async () => {
      if (!callState || !user?.id) return
      const remoteUserId = callState.initiator_id === user.id ? callState.receiver_id : callState.initiator_id
      if (!remoteUserId || userNameById[remoteUserId]) return
      try {
        const response = await api.get(`/users/${remoteUserId}`)
        if (response.data?.username) {
          setUserNameById(prev => ({ ...prev, [remoteUserId]: response.data.username }))
        }
      } catch (err) {
        console.warn('Failed to fetch remote user profile:', err)
      }
    }

    fetchRemoteUser()
  }, [callState, user?.id, userNameById])

  const initializeCall = async () => {
    try {
      setError(null)
      shouldReconnectRef.current = true
      reconnectAttemptsRef.current = 0

      await fetchCallInfo()

      const getStream = async () => {
        try {
          return await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
          })
        } catch (err: any) {
          if (err?.name === 'NotReadableError' || err?.name === 'OverconstrainedError') {
            console.warn('Camera unavailable, falling back to audio-only')
            setError('Camera is in use. Falling back to audio-only.')
            return await navigator.mediaDevices.getUserMedia({
              video: false,
              audio: true
            })
          }
          throw err
        }
      }

      // Get local media stream
      const stream = await getStream()
      localStreamRef.current = stream
      setLocalStream(stream)

      // Connect to WebRTC WebSocket
      connectWebRTCWebSocket()

      setCallStartTime(new Date())

    } catch (err: any) {
      console.error('Error initializing call:', err)
      setError(err.message || 'Failed to initialize call')
    }
  }

  const fetchCallInfo = async () => {
    if (!callId) return

    try {
      const call = await api.get<CallState>(`/calls/by-id/${callId}`)
      setCallState(call.data)
      const initiator = call.data.initiator_id === user?.id
      setIsInitiator(initiator)
      isInitiatorRef.current = initiator
      return
    } catch (err) {
      console.warn('Failed to fetch call by id, falling back to active/pending:', err)
    }

    try {
      const active = await api.get<CallState | null>('/calls/active')
      if (active.data && active.data.id === callId) {
        setCallState(active.data)
        const initiator = active.data.initiator_id === user?.id
        setIsInitiator(initiator)
        isInitiatorRef.current = initiator
        return
      }

      const pending = await api.get<CallState | null>('/calls/pending')
      if (pending.data && pending.data.id === callId) {
        setCallState(pending.data)
        const initiator = pending.data.initiator_id === user?.id
        setIsInitiator(initiator)
        isInitiatorRef.current = initiator
      }
    } catch (err) {
      console.error('Failed to fetch call info:', err)
    }
  }

  const connectWebRTCWebSocket = () => {
    if (!callId || !token) return
    
    try {
      const apiUrl = (((import.meta as unknown) as Record<string, Record<string, string>>).env.VITE_API_URL) || 'http://localhost:8000'
      const baseUrl = apiUrl.replace(/\/$/, '') // Remove trailing slash if any
      const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://')
      
      // Build the token parameter - add Bearer prefix if not already present
      const tokenParam = token.startsWith('Bearer ') ? token : `Bearer ${token}`
      const wsEndpoint = `${wsUrl}/ws/webrtc/${callId}?token=${encodeURIComponent(tokenParam)}`
      
      console.log('Connecting to WebSocket:', wsEndpoint.substring(0, 100) + '...')
      const ws = new WebSocket(wsEndpoint)
      
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          console.error('WebSocket connection timeout')
          setError('WebSocket connection timeout')
          ws.close()
        }
      }, 5000)
      
      ws.onopen = () => {
        clearTimeout(connectionTimeout)
        console.log('Connected to WebRTC WebSocket, ready state:', ws.readyState)
        reconnectAttemptsRef.current = 0
        // Wait a bit to ensure connection is fully established
        setTimeout(() => {
          setupPeerConnection(localStreamRef.current, isInitiatorRef.current)
        }, 100)
      }
      
      ws.onmessage = async (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('Received WebSocket message:', message.type)
          await handleWebRTCMessage(message)
        } catch (err) {
          console.error('Error handling WebRTC message:', err)
        }
      }
      
      ws.onerror = (event) => {
        console.error('WebSocket error event:', event)
        setError('WebSocket connection error - check browser console')
        scheduleReconnect('ws_error')
      }
      
      ws.onclose = (event) => {
        console.log('Disconnected from WebRTC WebSocket, code:', event.code, 'reason:', event.reason)
        scheduleReconnect('ws_close')
      }
      
      wsRef.current = ws
    } catch (err) {
      console.error('Error connecting to WebRTC WebSocket:', err)
      setError(`Failed to connect to WebRTC server: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  const setupPeerConnection = (stream: MediaStream | null, initiator: boolean) => {
    try {
      console.log('Setting up peer connection with local stream:', stream?.getTracks().length)
      
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: ['stun:stun.l.google.com:19302'] },
          { urls: ['stun:stun1.l.google.com:19302'] }
        ]
      })
      
      // Add local stream tracks
      if (stream) {
        console.log('Adding local tracks to peer connection')
        stream.getTracks().forEach(track => {
          console.log('Adding track:', track.kind, track.enabled)
          pc.addTrack(track, stream)
        })
      } else {
        console.warn('No local stream available')
      }
      
      // Handle remote stream
      pc.ontrack = (event) => {
        console.log('Remote track received:', event.track.kind)
        if (event.streams && event.streams.length > 0) {
          setRemoteStream(event.streams[0])
          setIsConnected(true)
          setCallState(prev => (prev ? { ...prev, status: 'ongoing' } : prev))
        }
      }
      
      // Handle ICE candidates
      pc.onicecandidate = (event) => {
        if (event.candidate) {
          console.log('ICE candidate:', event.candidate.candidate.substring(0, 50))
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'ice_candidate',
              candidate: event.candidate
            }))
          }
        }
      }
      
      // Handle connection state changes
      pc.onconnectionstatechange = () => {
        console.log('Connection state:', pc.connectionState)
        setConnectionState(pc.connectionState)
        if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          setError('Connection failed - trying to reconnect')
          restartIce()
          scheduleReconnect('pc_failed')
        } else if (pc.connectionState === 'connected') {
          setIsConnected(true)
          setCallState(prev => (prev ? { ...prev, status: 'ongoing' } : prev))
          setError(null)
        }
      }
      
      // Handle signaling state
      pc.onsignalingstatechange = () => {
        console.log('Signaling state:', pc.signalingState)
      }

      pc.oniceconnectionstatechange = () => {
        console.log('ICE connection state:', pc.iceConnectionState)
        if (!isConnected) {
          setConnectionState(pc.iceConnectionState)
        }
      }
      
      peerConnectionRef.current = pc
      console.log('Peer connection created')

      if (initiator) {
        console.log('Current user is initiator, waiting for receiver to connect')
        createOfferIfReady()
      } else {
        console.log('Current user is receiver, waiting for offer')
      }
    } catch (err) {
      console.error('Error setting up peer connection:', err)
      setError(`Failed to setup peer connection: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  const createOfferIfReady = () => {
    const pc = peerConnectionRef.current
    if (!pc) return

    if (!isInitiatorRef.current) return
    if (!remoteReadyRef.current) return
    if (offerSentRef.current) return

    offerSentRef.current = true
    console.log('Receiver is connected, creating offer')
    createOffer(pc)
  }

  const createOffer = async (pc: RTCPeerConnection) => {
    try {
      console.log('Creating offer...')
      const offer = await pc.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true
      })
      console.log('Offer created, setting local description')
      
      await pc.setLocalDescription(offer)
      console.log('Local description set, sending offer via WebSocket')
      
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'offer',
          offer
        }))
        console.log('Offer sent')
      } else {
        console.error('WebSocket not open, state:', wsRef.current?.readyState)
        setError('WebSocket not ready to send offer')
      }
    } catch (err) {
      console.error('Error creating offer:', err)
      setError(`Failed to create offer: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  const restartIce = async () => {
    const pc = peerConnectionRef.current
    if (!pc) return
    try {
      if (typeof pc.restartIce === 'function') {
        pc.restartIce()
      }
      if (isInitiatorRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        const offer = await pc.createOffer({
          iceRestart: true,
          offerToReceiveAudio: true,
          offerToReceiveVideo: true
        })
        await pc.setLocalDescription(offer)
        wsRef.current.send(JSON.stringify({
          type: 'offer',
          offer
        }))
      }
    } catch (err) {
      console.error('Error restarting ICE:', err)
    }
  }

  const resetPeerConnection = () => {
    if (peerConnectionRef.current) {
      try {
        peerConnectionRef.current.ontrack = null
        peerConnectionRef.current.onicecandidate = null
        peerConnectionRef.current.onconnectionstatechange = null
        peerConnectionRef.current.onsignalingstatechange = null
        peerConnectionRef.current.oniceconnectionstatechange = null
        peerConnectionRef.current.close()
      } catch (err) {
        console.warn('Error closing peer connection:', err)
      }
    }
    peerConnectionRef.current = null
    offerSentRef.current = false
    remoteReadyRef.current = false
    setIsConnected(false)
    setConnectionState('connecting')
  }

  const scheduleReconnect = (reason: string) => {
    if (!shouldReconnectRef.current) return
    if (reconnectAttemptsRef.current >= 3) {
      setError('Reconnection failed. Please refresh the page.')
      return
    }

    reconnectAttemptsRef.current += 1
    const delay = 1000 * reconnectAttemptsRef.current
    setError(`Connection lost. Reconnecting... (${reconnectAttemptsRef.current}/3)`) 
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current)
    }
    reconnectTimerRef.current = window.setTimeout(() => {
      resetPeerConnection()
      connectWebRTCWebSocket()
    }, delay)
    console.log('Scheduled reconnect:', reason)
  }

  const handleWebRTCMessage = async (message: any) => {
    try {
      if (message.type === 'connection_ready') {
        if (message.user_id && message.user_id !== user?.id) {
          remoteReadyRef.current = true
          console.log('Remote user connected, ready to negotiate')
          createOfferIfReady()
        }
        return
      }
      if (message.type === 'user_disconnected') {
        setError('The other user disconnected.')
        cleanupCall()
        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 500)
        return
      }
      if (message.type === 'call_ended') {
        setError('Call ended.')
        cleanupCall()
        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 500)
        return
      }
      if (message.type === 'offer') {
        await handleOffer(message.offer)
      } else if (message.type === 'answer') {
        await handleAnswer(message.answer)
      } else if (message.type === 'ice_candidate') {
        await handleICECandidate(message.candidate)
      }
    } catch (err) {
      console.error('Error handling WebRTC message:', err)
    }
  }

  const handleOffer = async (offer: any) => {
    try {
      if (!peerConnectionRef.current) {
        setupPeerConnection(localStreamRef.current, false)
      }
      
      const pc = peerConnectionRef.current!
      await pc.setRemoteDescription(new RTCSessionDescription(offer))
      
      const answer = await pc.createAnswer()
      await pc.setLocalDescription(answer)
      
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'answer',
          answer
        }))
      }
    } catch (err) {
      console.error('Error handling offer:', err)
    }
  }

  const handleAnswer = async (answer: any) => {
    try {
      if (peerConnectionRef.current) {
        await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(answer))
      }
    } catch (err) {
      console.error('Error handling answer:', err)
    }
  }

  const handleICECandidate = async (candidate: any) => {
    try {
      if (peerConnectionRef.current && candidate) {
        await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(candidate))
      }
    } catch (err) {
      console.error('Error adding ICE candidate:', err)
    }
  }

  const cleanupCall = () => {
    shouldReconnectRef.current = false
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current)
    }
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop())
    }
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close()
    }
    if (wsRef.current) {
      wsRef.current.close()
    }
  }

  const handleEndCall = async () => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'end_call' }))
      }
      if (callId) {
        try {
          await api.post(`/calls/end/${callId}`)
        } catch (apiErr) {
          console.error('Error calling end API:', apiErr)
          // Still continue with cleanup even if API fails
        }
      }
    } finally {
      cleanupCall()
      setTimeout(() => {
        window.location.href = '/dashboard'
      }, 500)
    }
  }

  const toggleMute = () => {
    const stream = localStreamRef.current
    if (!stream) return
    const tracks = stream.getAudioTracks()
    if (tracks.length === 0) return
    const next = !isMuted
    tracks.forEach(track => { track.enabled = !next })
    setIsMuted(next)
  }

  const toggleCamera = () => {
    const stream = localStreamRef.current
    if (!stream) return
    const tracks = stream.getVideoTracks()
    if (tracks.length === 0) return
    const next = !isCameraOff
    tracks.forEach(track => { track.enabled = !next })
    setIsCameraOff(next)
  }

  return (
    <div style={{ background: '#111', color: 'white', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ background: '#1a1a1a', padding: '20px', borderBottom: '1px solid #333' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ margin: '0', fontSize: '24px', fontWeight: '600' }}>UniLink Call</h1>
            <p style={{ margin: '5px 0 0 0', color: '#888', fontSize: '14px' }}>
              {isConnected || callState?.status === 'ongoing' ? 'Call in progress' : 'Connecting...'}
            </p>
            <div style={{ marginTop: '6px', fontSize: '12px', color: '#9ca3af' }}>
              Connection: {connectionState}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={toggleMute}
              style={{
                padding: '8px 12px',
                background: isMuted ? '#6b7280' : '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              {isMuted ? 'Unmute' : 'Mute'}
            </button>
            <button
              onClick={toggleCamera}
              style={{
                padding: '8px 12px',
                background: isCameraOff ? '#6b7280' : '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              {isCameraOff ? 'Camera On' : 'Camera Off'}
            </button>
            <button
              onClick={handleEndCall}
              style={{
                padding: '10px 20px',
                background: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              End Call
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: '#7f1d1d', color: '#fca5a5', padding: '12px 20px', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {/* Video area */}
      <div style={{ flex: 1, display: 'flex', padding: '20px', gap: '20px', overflow: 'auto' }}>
        {/* Remote video */}
        <div style={{ flex: 2, minWidth: '300px' }}>
          <VideoDisplay stream={remoteStream} label="Remote User" isLocal={false} />
        </div>

        {/* Local video and chat */}
        <div style={{ flex: 1, minWidth: '250px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <VideoDisplay stream={localStream} label="You" isLocal={true} />
          <ChatBox
            callId={callId!}
            ws={wsRef.current}
            currentUserId={user?.id || null}
            userNameById={userNameById}
          />
        </div>
      </div>

      {/* Call timer */}
      {callStartTime && (
        <div style={{ background: '#1a1a1a', padding: '15px', textAlign: 'center', borderTop: '1px solid #333', fontSize: '18px', fontWeight: '600' }}>
          <CallTimer startTime={callStartTime} />
        </div>
      )}
    </div>
  )
}
