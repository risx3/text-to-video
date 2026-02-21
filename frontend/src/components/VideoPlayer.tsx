interface Props {
  url: string
  alt?: string
}

export default function VideoPlayer({ url, alt = 'Generated video' }: Props) {
  const isGif = url.toLowerCase().endsWith('.gif')
  const isMp4 = url.toLowerCase().endsWith('.mp4') || url.toLowerCase().endsWith('.webm')

  if (isGif) {
    return (
      <div className="flex justify-center">
        <img
          src={url}
          alt={alt}
          className="rounded-xl border border-gray-700 max-w-full shadow-2xl"
          style={{ maxHeight: '480px' }}
        />
      </div>
    )
  }

  if (isMp4) {
    return (
      <div className="flex justify-center">
        <video
          src={url}
          controls
          autoPlay
          loop
          muted
          className="rounded-xl border border-gray-700 max-w-full shadow-2xl"
          style={{ maxHeight: '480px' }}
        />
      </div>
    )
  }

  return (
    <div className="text-center text-gray-400 text-sm">
      Unsupported format:{' '}
      <a href={url} className="text-indigo-400 hover:underline" target="_blank" rel="noreferrer">
        Download
      </a>
    </div>
  )
}
