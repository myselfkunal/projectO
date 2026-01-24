import { useRef, useEffect, FC } from 'react'

interface VideoDisplayProps {
  stream: MediaStream | null
  isLocal?: boolean
  label?: string
}

export const VideoDisplay: FC<VideoDisplayProps> = ({ stream, isLocal = false, label }) => {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '100%',
      background: '#000',
      borderRadius: '8px',
      overflow: 'hidden',
      minHeight: isLocal ? '150px' : '300px'
    }}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={isLocal}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: isLocal ? 'scaleX(-1)' : 'none'
        }}
      />
      {label && (
        <div style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '5px 10px',
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          {label}
        </div>
      )}
      {!stream && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: '#888',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '14px' }}>{label || 'No video'}</div>
        </div>
      )}
    </div>
  )
}
