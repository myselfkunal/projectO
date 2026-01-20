import { useEffect, useRef, useCallback, useState } from 'react'

export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

export const useWebSocket = (userId: string, token: string, onMessage: (msg: WebSocketMessage) => void | Promise<void>) => {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const shouldReconnectRef = useRef(false)
  const [isConnected, setIsConnected] = useState(false)

  const buildWebSocketUrl = useCallback(() => {
    const apiBase = (((import.meta as unknown) as Record<string, Record<string, string>>).env.VITE_API_URL) || window.location.origin
    const base = new URL(apiBase)
    const protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${base.host}/calls/ws/${userId}?token=${token}`
  }, [token, userId])

  const connect = useCallback(() => {
    if (!userId || !token) return

    shouldReconnectRef.current = true
    const wsUrl = buildWebSocketUrl()
    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      setIsConnected(true)
    }

    wsRef.current.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data)
        onMessage(message)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    wsRef.current.onclose = () => {
      setIsConnected(false)
      if (shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 3000)
      }
    }
  }, [buildWebSocketUrl, onMessage, token, userId])

  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { send, isConnected }
}
