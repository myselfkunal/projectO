import { useState, FC, useRef, useEffect } from 'react'

interface Message {
  id: string
  from: string
  text: string
  timestamp: string
}

interface ChatBoxProps {
  callId: string
  ws: WebSocket | null
  currentUserId: string | null
  userNameById: Record<string, string>
}

export const ChatBox: FC<ChatBoxProps> = ({ callId, ws, currentUserId, userNameById }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ws) return

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'chat_message') {
          if (currentUserId && message.from === currentUserId) {
            return
          }
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            from: message.from,
            text: message.text,
            timestamp: message.timestamp || new Date().toISOString()
          }])
        }
      } catch (err) {
        console.error('Error handling chat message:', err)
      }
    }

    ws.addEventListener('message', handleMessage)
    return () => ws.removeEventListener('message', handleMessage)
  }, [ws])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (input.trim() && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'chat_message',
        text: input,
        timestamp: new Date().toISOString()
      }))
      
      // Add to local messages
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        from: 'You',
        text: input,
        timestamp: new Date().toISOString()
      }])
      
      setInput('')
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: '#1a1a1a',
      border: '1px solid #333',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}>
        {messages.length === 0 ? (
          <div style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No messages yet
          </div>
        ) : (
          messages.map((msg) => {
            const displayFrom = msg.from === 'You'
              ? 'You'
              : (userNameById[msg.from] || 'Remote User')
            return (
            <div key={msg.id} style={{
              display: 'flex',
              justifyContent: msg.from === 'You' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                maxWidth: '80%',
                background: msg.from === 'You' ? '#3b82f6' : '#333',
                padding: '8px 12px',
                borderRadius: '6px',
                wordWrap: 'break-word'
              }}>
                <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#aaa' }}>
                  {displayFrom}
                </p>
                <p style={{ margin: 0, fontSize: '14px' }}>
                  {msg.text}
                </p>
              </div>
            </div>
          )})
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{
        borderTop: '1px solid #333',
        padding: '12px',
        display: 'flex',
        gap: '8px',
        background: '#0a0a0a'
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type message..."
          disabled={!ws || ws.readyState !== WebSocket.OPEN}
          style={{
            flex: 1,
            padding: '8px',
            border: '1px solid #333',
            borderRadius: '4px',
            background: '#1a1a1a',
            color: 'white',
            fontSize: '13px',
            outline: 'none'
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || !ws || ws.readyState !== WebSocket.OPEN}
          style={{
            padding: '8px 12px',
            background: input.trim() && ws && ws.readyState === WebSocket.OPEN ? '#3b82f6' : '#666',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: input.trim() && ws && ws.readyState === WebSocket.OPEN ? 'pointer' : 'not-allowed',
            fontSize: '13px',
            fontWeight: '600'
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
