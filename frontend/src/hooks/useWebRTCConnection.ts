/**
 * React hook for managing WebRTC connections
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { WebRTCManager } from '../utils/webrtc'

export interface UseWebRTCOptions {
  callId: string
  token: string
  wsUrl: string
  onRemoteStream?: (stream: MediaStream) => void
  onError?: (error: Error) => void
  onConnectionStateChange?: (state: RTCPeerConnectionState) => void
}

export const useWebRTC = (options: UseWebRTCOptions) => {
  const { callId, token, wsUrl, onRemoteStream, onError, onConnectionStateChange } = options
  
  const webrtcRef = useRef<WebRTCManager | null>(null)
  const [localStream, setLocalStream] = useState<MediaStream | null>(null)
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null)
  const [connectionState, setConnectionState] = useState<RTCPeerConnectionState | null>(null)
  const [iceConnectionState, setIceConnectionState] = useState<RTCIceConnectionState | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  // Initialize WebRTC manager
  useEffect(() => {
    if (webrtcRef.current) return

    const webrtc = new WebRTCManager()
    webrtcRef.current = webrtc

    // Set callbacks
    webrtc.setOnRemoteStream((stream) => {
      setRemoteStream(stream)
      onRemoteStream?.(stream)
    })

    webrtc.setOnConnectionStateChange((state) => {
      setConnectionState(state)
      onConnectionStateChange?.(state)
    })

    webrtc.setOnError((err) => {
      setError(err)
      onError?.(err)
    })

    return () => {
      webrtc.cleanup()
      webrtcRef.current = null
    }
  }, [onRemoteStream, onError, onConnectionStateChange])

  // Initialize media and connect
  const initialize = useCallback(async () => {
    try {
      if (isInitialized || isConnecting) return

      setIsConnecting(true)
      setError(null)

      if (!webrtcRef.current) {
        throw new Error('WebRTC manager not initialized')
      }

      // Get local media
      const stream = await webrtcRef.current.initialize()
      setLocalStream(stream)

      // Create peer connection
      webrtcRef.current.createPeerConnection()

      // Connect signaling
      const signalingUrl = `${wsUrl}/webrtc/${callId}`
      await webrtcRef.current.connectSignaling(callId, wsUrl, token)

      // Initiate call (create offer)
      await webrtcRef.current.createOffer()

      // Create data channel for chat
      webrtcRef.current.createDataChannel('chat')

      setIsInitialized(true)
      return true
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)
      return false
    } finally {
      setIsConnecting(false)
    }
  }, [callId, token, wsUrl, isInitialized, isConnecting, onError])

  // End call
  const endCall = useCallback(() => {
    if (webrtcRef.current) {
      webrtcRef.current.cleanup()
      setLocalStream(null)
      setRemoteStream(null)
      setIsInitialized(false)
    }
  }, [])

  // Send chat message
  const sendChatMessage = useCallback((message: string): boolean => {
    if (webrtcRef.current) {
      return webrtcRef.current.sendChatMessage(message)
    }
    return false
  }, [])

  // Mute/unmute audio
  const setAudioEnabled = useCallback((enabled: boolean) => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = enabled
      })
    }
  }, [localStream])

  // Enable/disable video
  const setVideoEnabled = useCallback((enabled: boolean) => {
    if (localStream) {
      localStream.getVideoTracks().forEach(track => {
        track.enabled = enabled
      })
    }
  }, [localStream])

  // Get connection stats
  const getStats = useCallback(async () => {
    if (webrtcRef.current) {
      const state = webrtcRef.current.getConnectionState()
      const iceState = webrtcRef.current.getIceConnectionState()
      return { state, iceState }
    }
    return null
  }, [])

  return {
    // State
    localStream,
    remoteStream,
    connectionState,
    iceConnectionState,
    isInitialized,
    isConnecting,
    error,
    
    // Methods
    initialize,
    endCall,
    sendChatMessage,
    setAudioEnabled,
    setVideoEnabled,
    getStats,
    
    // Direct access to manager (if needed)
    webrtc: webrtcRef.current
  }
}

export default useWebRTC
