import { useRef, useEffect, FC } from 'react'

interface VideoDisplayProps {
  stream: MediaStream | null
  isLocalVideo?: boolean
  label?: string
}

export const VideoDisplay: FC<VideoDisplayProps> = ({ stream, isLocalVideo = false, label }) => {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  return (
    <div className={`relative w-full h-full bg-black rounded-lg overflow-hidden ${isLocalVideo ? 'local-video' : ''}`}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={isLocalVideo}
        className="w-full h-full object-cover"
      />
      {label && (
        <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
          {label}
        </div>
      )}
    </div>
  )
}
