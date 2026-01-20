import { useState, useEffect, FC } from 'react'

interface CallTimerProps {
  startTime: number
  maxDuration?: number // in seconds
}

export const CallTimer: FC<CallTimerProps> = ({ startTime, maxDuration = 15 * 60 }) => {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const newElapsed = Math.floor((now - startTime) / 1000)
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
    <div className={`text-center font-mono text-2xl font-bold ${isTimeUp ? 'text-red-500' : 'text-white'}`}>
      {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
      {isTimeUp && <p className="text-sm">Time's up!</p>}
    </div>
  )
}
