import PromptInput from './components/PromptInput'
import ProgressBar from './components/ProgressBar'
import VideoPlayer from './components/VideoPlayer'
import StatusBadge from './components/StatusBadge'
import { useVideoJob } from './hooks/useVideoJob'

export default function App() {
  const { job, isSubmitting, error, submit, reset } = useVideoJob()

  const isRunning = isSubmitting || (job !== null && job.status !== 'completed' && job.status !== 'failed')

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-start py-12 px-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Text&nbsp;<span className="text-indigo-400">→</span>&nbsp;Video
          </h1>
          <p className="text-gray-400 text-sm">
            Powered by AnimateDiff · runs on CUDA, Apple Silicon, or CPU
          </p>
        </div>

        {/* Input card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
          <PromptInput onSubmit={submit} disabled={isRunning} />
        </div>

        {/* Global error (submission failure) */}
        {error && !job && (
          <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
            <span className="font-semibold">Error:</span> {error}
          </div>
        )}

        {/* Job status card */}
        {job && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-5">
            {/* Status row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <StatusBadge status={job.status} />
                <span className="text-xs text-gray-500 font-mono">{job.job_id.slice(0, 8)}</span>
              </div>
              {(job.status === 'completed' || job.status === 'failed') && (
                <button
                  onClick={reset}
                  className="text-xs text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 rounded-lg px-3 py-1 transition-colors"
                >
                  New video
                </button>
              )}
            </div>

            {/* Progress bar (while running) */}
            {job.status !== 'completed' && job.status !== 'failed' && (
              <ProgressBar percent={job.progress} message={job.message} />
            )}

            {/* Enhanced prompt */}
            {job.enhanced_prompt && job.enhanced_prompt !== job.prompt && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Enhanced prompt</p>
                <p className="text-sm text-gray-300 leading-relaxed">{job.enhanced_prompt}</p>
              </div>
            )}

            {/* Video output */}
            {job.video_url && (
              <div className="space-y-3">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Result</p>
                <VideoPlayer url={job.video_url} />
                <div className="flex justify-end">
                  <a
                    href={job.video_url}
                    download
                    className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    Download MP4
                  </a>
                </div>
              </div>
            )}

            {/* Error message */}
            {job.status === 'failed' && job.error && (
              <div className="bg-red-950 border border-red-800 rounded-xl p-3 text-red-300 text-sm">
                <span className="font-semibold">Failed:</span> {job.error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
