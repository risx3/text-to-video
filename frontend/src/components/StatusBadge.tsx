import type { JobStatus } from '../types/job'

interface Props {
  status: JobStatus
}

const config: Record<JobStatus, { label: string; classes: string }> = {
  pending:    { label: 'Queued',      classes: 'bg-gray-700 text-gray-300' },
  enhancing:  { label: 'Enhancing',   classes: 'bg-blue-900 text-blue-300 animate-pulse' },
  generating: { label: 'Generating',  classes: 'bg-indigo-900 text-indigo-300 animate-pulse' },
  completed:  { label: 'Done',        classes: 'bg-green-900 text-green-300' },
  failed:     { label: 'Failed',      classes: 'bg-red-900 text-red-300' },
}

export default function StatusBadge({ status }: Props) {
  const { label, classes } = config[status] ?? config.pending
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${classes}`}>
      {label}
    </span>
  )
}
