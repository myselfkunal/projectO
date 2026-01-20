export class WebRTCManager {
  private peerConnection: RTCPeerConnection | null = null
  private localStream: MediaStream | null = null
  private remoteStream: MediaStream | null = null
  private dataChannel: RTCDataChannel | null = null
  private websocket: WebSocket | null = null
  
  private onRemoteStream?: (stream: MediaStream) => void
  private onIceCandidate?: (candidate: RTCIceCandidate) => void
  private onConnectionStateChange?: (state: RTCPeerConnectionState) => void
  private onDataChannelMessage?: (message: string) => void
  private onError?: (error: Error) => void

  private readonly STUN_SERVERS = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' },
    { urls: 'stun:stun3.l.google.com:19302' },
    { urls: 'stun:stun4.l.google.com:19302' },
  ]

  private readonly TURN_SERVERS: RTCIceServer[] = []
  // Add TURN servers if needed for production
  // {
  //   urls: 'turn:turnserver.example.com:3478',
  //   username: 'user',
  //   credential: 'password'
  // }

  async initialize(constraints: MediaStreamConstraints = {}) {
    try {
      const defaultConstraints: MediaStreamConstraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
        video: {
          width: { min: 320, ideal: 640, max: 1280 },
          height: { min: 240, ideal: 480, max: 720 },
          frameRate: { ideal: 30, max: 60 }
        }
      }
      
      this.localStream = await navigator.mediaDevices.getUserMedia({
        ...defaultConstraints,
        ...constraints
      })
      console.log('✓ Local media obtained')
      return this.localStream
    } catch (error) {
      const err = new Error(`Error accessing media devices: ${error}`)
      this.onError?.(err)
      throw err
    }
  }

  createPeerConnection(config?: RTCConfiguration) {
    try {
      const peerConfig: RTCConfiguration = config || {
        iceServers: [...this.STUN_SERVERS, ...this.TURN_SERVERS]
      }
      
      this.peerConnection = new RTCPeerConnection(peerConfig)
      console.log('✓ Peer connection created')

      // Add local stream tracks
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => {
          this.peerConnection!.addTrack(track, this.localStream!)
        })
        console.log('✓ Local tracks added to peer connection')
      }

      // Handle remote stream
      this.peerConnection.ontrack = (event: RTCTrackEvent) => {
        if (this.remoteStream?.id !== event.streams[0]?.id) {
          this.remoteStream = event.streams[0]
          console.log('✓ Remote stream received')
          this.onRemoteStream?.(this.remoteStream)
        }
      }

      // Handle ICE candidates
      this.peerConnection.onicecandidate = (event: RTCPeerConnectionIceEvent) => {
        if (event.candidate) {
          this.onIceCandidate?.(event.candidate)
        }
      }
      
      // Handle connection state changes
      this.peerConnection.onconnectionstatechange = () => {
        const state = this.peerConnection!.connectionState
        console.log(`Connection state: ${state}`)
        this.onConnectionStateChange?.(state)
      }

      // Handle data channel (if created by remote peer)
      this.peerConnection.ondatachannel = (event: RTCDataChannelEvent) => {
        this.setupDataChannel(event.channel)
      }

      return this.peerConnection
    } catch (error) {
      const err = new Error(`Error creating peer connection: ${error}`)
      this.onError?.(err)
      throw err
    }
  }

  async connectSignaling(callId: string, wsUrl: string, token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const url = `${wsUrl}/${callId}?token=${encodeURIComponent(token)}`
        this.websocket = new WebSocket(url)
        console.log(`Connecting to WebRTC signaling: ${url.split('?')[0]}`)

        this.websocket.onopen = () => {
          console.log('✓ WebSocket signaling connected')
          resolve()
        }

        this.websocket.onmessage = (event) => {
          this.handleSignalingMessage(JSON.parse(event.data))
        }

        this.websocket.onerror = (error) => {
          const err = new Error(`WebSocket signaling error: ${error}`)
          this.onError?.(err)
          reject(err)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  private handleSignalingMessage(message: any) {
    try {
      switch (message.type) {
        case 'offer':
          this.handleOffer(message.offer)
          break
        case 'answer':
          this.handleAnswer(message.answer)
          break
        case 'ice_candidate':
          this.addIceCandidate(message.candidate).catch(e => console.warn('ICE error:', e))
          break
        case 'connection_ready':
          console.log(message.message)
          break
        case 'error':
          console.error(`Signaling error: ${message.message}`)
          break
        default:
          console.warn(`Unknown signaling message: ${message.type}`)
      }
    } catch (error) {
      console.error(`Error handling signaling message: ${error}`)
    }
  }

  private sendSignalingMessage(message: Record<string, any>) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected')
    }
  }

  async createOffer() {
    try {
      if (!this.peerConnection) {
        this.createPeerConnection()
      }
      const offer = await this.peerConnection!.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true
      })
      await this.peerConnection!.setLocalDescription(offer)
      console.log('✓ SDP offer created')
      
      // Send offer through signaling
      this.sendSignalingMessage({ type: 'offer', offer })
      
      return offer
    } catch (error) {
      const err = new Error(`Error creating offer: ${error}`)
      this.onError?.(err)
      throw err
    }
  }

  private async handleOffer(offer: RTCSessionDescriptionInit) {
    try {
      if (!this.peerConnection) {
        this.createPeerConnection()
      }
      await this.peerConnection!.setRemoteDescription(new RTCSessionDescription(offer))
      console.log('✓ Remote offer set')
      
      const answer = await this.createAnswer()
      this.sendSignalingMessage({ type: 'answer', answer })
    } catch (error) {
      console.error(`Error handling offer: ${error}`)
    }
  }

  async createAnswer() {
    try {
      if (!this.peerConnection) {
        this.createPeerConnection()
      }
      const answer = await this.peerConnection!.createAnswer()
      await this.peerConnection!.setLocalDescription(answer)
      console.log('✓ SDP answer created')
      return answer
    } catch (error) {
      const err = new Error(`Error creating answer: ${error}`)
      this.onError?.(err)
      throw err
    }
  }

  private async handleAnswer(answer: RTCSessionDescriptionInit) {
    try {
      if (this.peerConnection && this.peerConnection.signalingState === 'have-local-offer') {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer))
        console.log('✓ Remote answer set')
      }
    } catch (error) {
      console.error(`Error handling answer: ${error}`)
    }
  }

  async setRemoteDescription(description: RTCSessionDescription) {
    try {
      if (!this.peerConnection) {
        this.createPeerConnection()
      }
      await this.peerConnection!.setRemoteDescription(new RTCSessionDescription(description))
      console.log('✓ Remote description set')
    } catch (error) {
      const err = new Error(`Error setting remote description: ${error}`)
      this.onError?.(err)
      throw err
    }
  }

  async addIceCandidate(candidate: RTCIceCandidateInit) {
    try {
      if (this.peerConnection && candidate.candidate) {
        await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate))
        console.log('✓ ICE candidate added')
      }
    } catch (error) {
      console.warn(`Error adding ICE candidate: ${error}`)
    }
  }

  createDataChannel(label: string = 'chat'): RTCDataChannel | null {
    if (!this.peerConnection) return null
    
    this.dataChannel = this.peerConnection.createDataChannel(label, { ordered: true })
    this.setupDataChannel(this.dataChannel)
    console.log(`✓ Data channel created: ${label}`)
    return this.dataChannel
  }

  private setupDataChannel(channel: RTCDataChannel) {
    this.dataChannel = channel

    this.dataChannel.onopen = () => {
      console.log('✓ Data channel opened')
    }

    this.dataChannel.onclose = () => {
      console.log('✓ Data channel closed')
    }

    this.dataChannel.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.onDataChannelMessage?.(message.message)
      } catch {
        this.onDataChannelMessage?.(event.data)
      }
    }

    this.dataChannel.onerror = (error) => {
      console.error(`Data channel error: ${error}`)
    }
  }

  sendChatMessage(message: string): boolean {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(
        JSON.stringify({
          type: 'text',
          message,
          timestamp: new Date().toISOString()
        })
      )
      return true
    }
    return false
  }

  getLocalStream() {
    return this.localStream
  }

  getRemoteStream() {
    return this.remoteStream
  }

  getConnectionState(): RTCPeerConnectionState | null {
    return this.peerConnection?.connectionState ?? null
  }

  getIceConnectionState(): RTCIceConnectionState | null {
    return this.peerConnection?.iceConnectionState ?? null
  }

  cleanup() {
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop())
      this.localStream = null
    }
    if (this.dataChannel) {
      this.dataChannel.close()
      this.dataChannel = null
    }
    if (this.peerConnection) {
      this.peerConnection.close()
      this.peerConnection = null
    }
    if (this.websocket) {
      this.websocket.close()
      this.websocket = null
    }
    console.log('✓ WebRTC resources cleaned up')
  }

  setOnRemoteStream(callback: (stream: MediaStream) => void) {
    this.onRemoteStream = callback
  }

  setOnIceCandidate(callback: (candidate: RTCIceCandidate) => void) {
    this.onIceCandidate = callback
  }

  setOnConnectionStateChange(callback: (state: RTCPeerConnectionState) => void) {
    this.onConnectionStateChange = callback
  }

  setOnDataChannelMessage(callback: (message: string) => void) {
    this.onDataChannelMessage = callback
  }

  setOnError(callback: (error: Error) => void) {
    this.onError = callback
  }
}
