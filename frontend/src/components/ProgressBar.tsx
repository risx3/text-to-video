interface Props {
  percent: number
  message?: string
}

export default function ProgressBar({ percent, message }: Props) {
  const clamped = Math.max(0, Math.min(100, percent))
  return (
    <div className="w-full space-y-1">
      <div className="flex justify-between text-xs text-gray-400">
        <span className="truncate max-w-xs">{message ?? 'Processing…'}</span>
        <span>{clamped}%</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
