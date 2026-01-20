import { useState, FC, useRef, useEffect } from 'react'

interface Message {
  id: string
  sender_id: string
  sender_username: string
  message: string
  timestamp: string
  isSent: boolean
}

interface ChatBoxProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  disabled?: boolean
}

export const ChatBox: FC<ChatBoxProps> = ({ messages, onSendMessage, disabled = false }) => {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input)
      setInput('')
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col h-full bg-white border-l border-gray-200">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.isSent ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`chat-message ${msg.isSent ? 'sent' : 'received'}`}
            >
              <p className="text-xs font-semibold mb-1">{msg.sender_username}</p>
              <p>{msg.message}</p>
              <p className="text-xs opacity-70 mt-1">{new Date(msg.timestamp).toLocaleTimeString()}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-3 bg-gray-50">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            disabled={disabled}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:bg-gray-400"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
