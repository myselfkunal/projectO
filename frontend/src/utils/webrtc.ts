export class WebRTCManager {
  private peerConnection: RTCPeerConnection | null = null
  private localStream: MediaStream | null = null
  private remoteStream: MediaStream | null = null
  private onRemoteStream?: (stream: MediaStream) => void
  private onIceCandidate?: (candidate: RTCIceCandidate) => void

  private readonly STUN_SERVERS = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ]

  private readonly TURN_SERVERS = [
    {
      urls: 'turn:turnserver.kiit.ac.in:3478',
      username: 'user',
      credential: 'password'
    }
  ]

  async initialize() {
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: { width: 1280, height: 720 }
      })
      return this.localStream
    } catch (error) {
      console.error('Error accessing media devices:', error)
      throw error
    }
  }

  createPeerConnection() {
    this.peerConnection = new RTCPeerConnection({
      iceServers: [...this.STUN_SERVERS, ...this.TURN_SERVERS]
    })

    // Add local stream tracks
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => {
        this.peerConnection!.addTrack(track, this.localStream!)
      })
    }

    // Handle remote stream
    this.peerConnection.ontrack = (event: RTCTrackEvent) => {
      if (this.remoteStream?.id !== event.streams[0].id) {
        this.remoteStream = event.streams[0]
        this.onRemoteStream?.(this.remoteStream)
      }
    }

    // Handle ICE candidates
    this.peerConnection.onicecandidate = (event: RTCPeerConnectionIceEvent) => {
      if (event.candidate) {
        this.onIceCandidate?.(event.candidate)
      }
    }

    return this.peerConnection
  }

  async createOffer() {
    if (!this.peerConnection) {
      this.createPeerConnection()
    }
    const offer = await this.peerConnection!.createOffer()
    await this.peerConnection!.setLocalDescription(offer)
    return offer
  }

  async createAnswer() {
    if (!this.peerConnection) {
      this.createPeerConnection()
    }
    const answer = await this.peerConnection!.createAnswer()
    await this.peerConnection!.setLocalDescription(answer)
    return answer
  }

  async setRemoteDescription(description: RTCSessionDescription) {
    if (!this.peerConnection) {
      this.createPeerConnection()
    }
    await this.peerConnection!.setRemoteDescription(new RTCSessionDescription(description))
  }

  async addIceCandidate(candidate: RTCIceCandidateInit) {
    if (this.peerConnection) {
      await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate))
    }
  }

  getLocalStream() {
    return this.localStream
  }

  getRemoteStream() {
    return this.remoteStream
  }

  cleanup() {
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop())
    }
    if (this.peerConnection) {
      this.peerConnection.close()
      this.peerConnection = null
    }
  }

  setOnRemoteStream(callback: (stream: MediaStream) => void) {
    this.onRemoteStream = callback
  }

  setOnIceCandidate(callback: (candidate: RTCIceCandidate) => void) {
    this.onIceCandidate = callback
  }
}
