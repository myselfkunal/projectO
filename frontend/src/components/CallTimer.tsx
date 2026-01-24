import { useState, useEffect, FC } from 'react'

interface CallTimerProps {
  startTime: Date | number
  maxDuration?: number // in seconds
}

export const CallTimer: FC<CallTimerProps> = ({ startTime, maxDuration = 60 * 60 }) => {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const start = typeof startTime === 'number' ? startTime : startTime.getTime()
      const newElapsed = Math.floor((now - start) / 1000)
      setElapsed(newElapsed)

      if (newElapsed >= maxDuration) {
        clearInterval(interval)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime, maxDuration])

  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  const isTimeUp = elapsed >= maxDuration

  return (
    <div style={{
      fontFamily: 'monospace',
      fontSize: '24px',
      fontWeight: 'bold',
      color: isTimeUp ? '#ef4444' : 'white'
    }}>
      {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
      {isTimeUp && <p style={{ fontSize: '14px', margin: '5px 0 0 0' }}>Time's up!</p>}
    </div>
  )
}
