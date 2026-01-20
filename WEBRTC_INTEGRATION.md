# WebRTC Integration Documentation

## Overview

The WebRTC integration enables real-time 1v1 video calling with peer-to-peer media streaming and data channel support for text chat.

## Architecture

### Backend Components

#### 1. WebRTC Signaling Service (`app/utils/webrtc_service.py`)
- **WebRTCPeerConnection**: Represents a peer connection state
- **WebRTCSignalingManager**: Manages all active WebRTC sessions
- Tracks offer/answer exchange and ICE candidates
- Monitors connection health and cleanup of stale connections

#### 2. WebSocket Endpoint (`app/routes/webrtc.py`)
- **WebSocket `/ws/webrtc/{call_id}`**: Main signaling endpoint
  - Requires JWT token for authentication
  - Validates user is part of the call
  - Relays SDP offer/answer between peers
  - Relays ICE candidates
  - Handles connection state management
  - Broadcasts chat messages via data channel

### Frontend Components

#### 1. WebRTC Manager (`src/utils/webrtc.ts`)
- **WebRTCManager**: Class for managing peer connections
  - Initialize media streams with constraints optimization
  - Create and manage RTCPeerConnection
  - Handle SDP offer/answer negotiation
  - ICE candidate collection and relay
  - Data channel setup for chat
  - Connection state monitoring
  - Automatic cleanup

#### 2. useWebRTC Hook (`src/hooks/useWebRTCConnection.ts`)
- React hook for WebRTC integration in components
- Manages connection lifecycle
- Provides callbacks for stream events
- Audio/video track control
- Chat message sending

## Call Flow

### Initiating a Call

```
1. User A clicks "Call User B"
   ├─ POST /calls/initiate -> creates Call record (status: pending)
   
2. User B receives notification (via polling or WebSocket)
   ├─ UI shows incoming call
   
3. User B clicks "Accept"
   ├─ POST /calls/accept/{call_id} -> updates status to ongoing
   ├─ WebSocket connection established for User B
   
4. User A's client initiates WebRTC connection
   ├─ GET /calls/active -> retrieves active call
   ├─ WebSocket: /ws/webrtc/{call_id}
   ├─ Initialize peer connection
   ├─ Create SDP offer
   ├─ Send offer via WebSocket
   
5. User B's client receives offer
   ├─ Set remote description
   ├─ Create SDP answer
   ├─ Send answer via WebSocket
   
6. Both clients exchange ICE candidates
   ├─ As candidates are gathered, send via WebSocket
   ├─ Receive and add remote candidates
   
7. Connection established
   ├─ Media streams flowing peer-to-peer
   ├─ Data channel ready for chat
```

## Message Protocol

### SDP Offer
```json
{
  "type": "offer",
  "offer": {
    "type": "offer",
    "sdp": "v=0\r\no=..."
  }
}
```

### SDP Answer
```json
{
  "type": "answer",
  "answer": {
    "type": "answer",
    "sdp": "v=0\r\no=..."
  }
}
```

### ICE Candidate
```json
{
  "type": "ice_candidate",
  "candidate": {
    "candidate": "candidate:...",
    "sdpMLineIndex": 0,
    "sdpMid": "0"
  }
}
```

### Chat Message (via Data Channel)
```json
{
  "type": "text",
  "message": "Hello!",
  "timestamp": "2026-01-21T10:30:00Z"
}
```

### Connection State
```json
{
  "type": "connection_state",
  "state": "connected"
}
```

## Configuration

### STUN Servers (Default)
```
- stun:stun.l.google.com:19302
- stun:stun1.l.google.com:19302
- stun:stun2.l.google.com:19302
- stun:stun3.l.google.com:19302
- stun:stun4.l.google.com:19302
```

### Media Constraints (Default)
```
Audio:
- Echo cancellation: Enabled
- Noise suppression: Enabled
- Auto gain control: Enabled

Video:
- Resolution: 320x240 (min) to 1280x720 (max)
- Ideal: 640x480
- Frame rate: 30 fps ideal, 60 fps max
```

### TURN Servers (Optional)
Add to `WebRTCManager` for production if needed:
```typescript
{
  urls: 'turn:turnserver.example.com:3478',
  username: 'user',
  credential: 'password'
}
```

## Usage Example

### Frontend Component
```typescript
import { useWebRTC } from './hooks/useWebRTCConnection'

function VideoCall({ callId, token }) {
  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)

  const {
    localStream,
    remoteStream,
    connectionState,
    isInitialized,
    initialize,
    endCall,
    sendChatMessage,
    setAudioEnabled,
    setVideoEnabled
  } = useWebRTC({
    callId,
    token,
    wsUrl: 'ws://localhost:8000/ws',
    onRemoteStream: (stream) => {
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = stream
      }
    },
    onError: (error) => console.error('WebRTC Error:', error)
  })

  useEffect(() => {
    if (localStream && localVideoRef.current) {
      localVideoRef.current.srcObject = localStream
    }
  }, [localStream])

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <div>
      <video ref={localVideoRef} autoPlay muted />
      <video ref={remoteVideoRef} autoPlay />
      <p>Connection: {connectionState}</p>
      <button onClick={() => endCall()}>End Call</button>
      <input 
        type="text"
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            sendChatMessage(e.currentTarget.value)
            e.currentTarget.value = ''
          }
        }}
        placeholder="Send message..."
      />
    </div>
  )
}
```

## Error Handling

### Connection Failures
1. **No ICE candidates**: Check firewall and network connectivity
2. **Offer/answer not set**: Ensure signaling messages are delivered
3. **Media access denied**: User denied camera/microphone permissions
4. **WebSocket disconnection**: Network issue or server restart

### Recovery Strategies
- Automatic ICE restart on failed connection
- Exponential backoff for WebSocket reconnection
- Graceful cleanup of stale connections

## Performance Optimization

1. **Bandwidth Management**
   - Adaptive bitrate streaming
   - Video resolution adjusts to network conditions
   - Configure constraints based on network quality

2. **CPU Usage**
   - Hardware video encoding/decoding
   - Frame rate limiting
   - Adaptive quality

3. **Latency Reduction**
   - Use STUN servers for NAT traversal
   - Consider TURN servers for 100% connectivity
   - WebSocket compression enabled

## Monitoring

### Connection Metrics
- Connection state (new → connecting → connected → failed/closed)
- ICE connection state
- ICE gathering state
- Audio/video track state
- Bandwidth usage

### Debug Endpoint
```
GET /ws/webrtc/connection-state/{call_id}
Response: {
  "call_id": "...",
  "connection_state": "connected",
  "ice_candidates_count": 12,
  "created_at": "...",
  "updated_at": "..."
}

GET /ws/webrtc/active-connections
Response: {
  "total_calls": 5,
  "connections": { ... }
}
```

## Security Considerations

1. **WebSocket Authentication**
   - JWT token validation required
   - User verified to be part of the call
   - Tokens expire and require refresh

2. **Signaling Message Validation**
   - All messages validated before relay
   - Invalid messages rejected
   - Rate limiting on WebSocket messages

3. **DTLS-SRTP**
   - All media is encrypted end-to-end
   - Browsers enforce DTLS-SRTP automatically
   - No server access to media streams

## Troubleshooting

### No remote video
- Check firewall allows WebRTC connections
- Verify both clients can reach STUN servers
- Check browser console for errors

### Audio/video lag
- Check network latency
- Reduce video resolution
- Check CPU usage on both clients

### Connection drops
- Verify WebSocket connection stability
- Check for network interruptions
- Review backend logs

## Future Enhancements

1. **Multi-party Conferencing** - Extend to group calls with SFU
2. **Screen Sharing** - Add capability to share screen
3. **Recording** - Server-side or client-side call recording
4. **Quality Monitoring** - Real-time statistics dashboard
5. **Advanced Codecs** - VP9, H.265 for better compression
