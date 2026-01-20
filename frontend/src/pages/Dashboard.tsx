import { useState, useRef, FC } from 'react'
import { WebRTCManager } from '@/utils/webrtc'
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket'
import { VideoDisplay } from '@/components/VideoDisplay'
import { ChatBox } from '@/components/ChatBox'
import { CallTimer } from '@/components/CallTimer'
import { useAuthStore } from '@/context/authStore'

interface Message {
  id: string
  sender_id: string
  sender_username: string
  message: string
  timestamp: string
  isSent: boolean
}

export const Dashboard: FC = () => {
  const user = useAuthStore(state => state.user)
  const token = useAuthStore(state => state.token)
  const [page, setPage] = useState<'menu' | 'calling' | 'in-call'>('menu')
  const [queuePosition, setQueuePosition] = useState(0)
  const [remoteUser, setRemoteUser] = useState<any>(null)
  const [localStream, setLocalStream] = useState<MediaStream | null>(null)
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [callStartTime, setCallStartTime] = useState(0)
  const webrtcRef = useRef(new WebRTCManager())
  const callIdRef = useRef<string>('')
  const callTokenRef = useRef<string>('')
  const messageIdRef = useRef(0)

  const { send: sendWs, isConnected } = useWebSocket(user?.id || '', token || '', handleWebSocketMessage)

  async function handleWebSocketMessage(msg: WebSocketMessage) {
    switch (msg.type) {
      case 'queue_joined':
        setQueuePosition(msg.queue_position)
        break

      case 'match_found':
        callIdRef.current = msg.call_id
        callTokenRef.current = msg.call_token
        setRemoteUser(msg.matched_user)
        setPage('in-call')
        setCallStartTime(Date.now())
        await initiateWebRTC(true)
        break

      case 'webrtc_offer':
        await handleWebRTCOffer(msg.offer)
        break

      case 'webrtc_answer':
        await handleWebRTCAnswer(msg.answer)
        break

      case 'webrtc_ice':
        await webrtcRef.current.addIceCandidate(msg.candidate)
        break

      case 'chat_message':
        addMessage(msg.sender_username, msg.message, false, msg.sender_id)
        break

      case 'call_ended':
        endCall()
        break
    }
  }

  async function initiateWebRTC(isInitiator: boolean) {
    try {
      const stream = await webrtcRef.current.initialize()
      setLocalStream(stream)

      webrtcRef.current.createPeerConnection()

      webrtcRef.current.setOnRemoteStream((stream) => {
        setRemoteStream(stream)
      })

      webrtcRef.current.setOnIceCandidate((candidate) => {
        sendWs({
          type: 'webrtc_ice',
          candidate: candidate.candidate,
          receiver_id: remoteUser.id,
        })
      })

      if (isInitiator) {
        const offer = await webrtcRef.current.createOffer()
        sendWs({
          type: 'webrtc_offer',
          offer: offer,
          receiver_id: remoteUser.id,
        })
      }
    } catch (error) {
      console.error('WebRTC initialization error:', error)
    }
  }

  async function handleWebRTCOffer(offer: RTCSessionDescription) {
    try {
      await webrtcRef.current.setRemoteDescription(offer)
      const answer = await webrtcRef.current.createAnswer()
      sendWs({
        type: 'webrtc_answer',
        answer: answer,
        receiver_id: remoteUser.id,
      })
    } catch (error) {
      console.error('Error handling WebRTC offer:', error)
    }
  }

  async function handleWebRTCAnswer(answer: RTCSessionDescription) {
    try {
      await webrtcRef.current.setRemoteDescription(answer)
    } catch (error) {
      console.error('Error handling WebRTC answer:', error)
    }
  }

  function addMessage(username: string, text: string, isSent: boolean, senderId: string) {
    setMessages(prev => [...prev, {
      id: `msg-${messageIdRef.current++}`,
      sender_id: senderId,
      sender_username: username,
      message: text,
      timestamp: new Date().toISOString(),
      isSent,
    }])
  }

  function handleSendMessage(text: string) {
    if (remoteUser) {
      addMessage(user?.username || 'You', text, true, user?.id || '')
      sendWs({
        type: 'chat_message',
        message: text,
        receiver_id: remoteUser.id,
        timestamp: new Date().toISOString(),
      })
    }
  }

  function startCall() {
    setPage('calling')
    sendWs({ type: 'join_queue' })
  }

  function endCall() {
    if (remoteUser) {
      sendWs({
        type: 'end_call',
        receiver_id: remoteUser.id,
      })
    }
    webrtcRef.current.cleanup()
    setRemoteStream(null)
    setRemoteUser(null)
    setMessages([])
    setPage('menu')
  }

  function leaveQueue() {
    sendWs({ type: 'leave_queue' })
    setPage('menu')
    setQueuePosition(0)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">UniLink</h1>
          <div className="flex items-center gap-4">
            <span className={`w-3 h-3 rounded-full ${user?.is_online ? 'bg-green-500' : 'bg-gray-500'}`}></span>
            <span>{user?.username}</span>
            <button
              onClick={() => {
                localStorage.removeItem('token')
                window.location.href = '/login'
              }}
              className="px-4 py-2 bg-red-600 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6 max-w-7xl mx-auto">
        {page === 'menu' && (
          <div className="flex flex-col items-center justify-center h-96">
            <h2 className="text-4xl font-bold mb-8">Find Someone to Talk To</h2>
            <button
              onClick={startCall}
              disabled={!isConnected}
              className="px-8 py-4 bg-blue-500 rounded-lg font-bold text-lg hover:bg-blue-600 disabled:bg-gray-600"
            >
              Start a Call
            </button>
            {!isConnected && <p className="text-red-500 mt-4">Connecting...</p>}
          </div>
        )}

        {page === 'calling' && (
          <div className="flex flex-col items-center justify-center h-96">
            <h2 className="text-3xl font-bold mb-8">Finding a match...</h2>
            <div className="text-2xl mb-8">Position in queue: {queuePosition}</div>
            <button
              onClick={leaveQueue}
              className="px-8 py-4 bg-red-600 rounded-lg font-bold text-lg hover:bg-red-700"
            >
              Cancel
            </button>
          </div>
        )}

        {page === 'in-call' && remoteUser && (
          <div className="grid grid-cols-3 gap-4 h-screen">
            {/* Video Area - 2 columns */}
            <div className="col-span-2 flex flex-col gap-4">
              {/* Remote Video */}
              <div className="flex-1 bg-black rounded-lg overflow-hidden">
                <VideoDisplay stream={remoteStream} label={remoteUser.username} />
              </div>

              {/* Local Video */}
              <div className="h-32 bg-black rounded-lg overflow-hidden relative">
                <VideoDisplay stream={localStream} isLocalVideo={true} label="You" />
              </div>

              {/* Call Controls */}
              <div className="flex justify-center gap-4">
                <CallTimer startTime={callStartTime} maxDuration={15 * 60} />
                <button
                  onClick={endCall}
                  className="px-6 py-2 bg-red-600 rounded-lg font-bold hover:bg-red-700"
                >
                  End Call
                </button>
              </div>
            </div>

            {/* Chat Area - 1 column */}
            <div className="h-full">
              <ChatBox
                messages={messages}
                onSendMessage={handleSendMessage}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
