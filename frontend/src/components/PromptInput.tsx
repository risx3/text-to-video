import { useState, type FormEvent } from 'react'
import type { JobCreate } from '../types/job'

interface Props {
  onSubmit: (payload: JobCreate) => void
  disabled?: boolean
}

export default function PromptInput({ onSubmit, disabled = false }: Props) {
  const [prompt, setPrompt] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [numFrames, setNumFrames] = useState(8)
  const [steps, setSteps] = useState(25)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return
    const payload: JobCreate = {
      prompt: prompt.trim(),
      num_frames: numFrames,
      num_inference_steps: steps,
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="prompt" className="block text-sm font-medium text-gray-300 mb-1">
          Describe your video
        </label>
        <textarea
          id="prompt"
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={disabled}
          placeholder="A majestic eagle soaring over mountain peaks at sunset, cinematic, 4K…"
          className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-gray-100
                     placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500
                     disabled:opacity-50 disabled:cursor-not-allowed resize-none text-sm"
        />
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced((v) => !v)}
        className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
      >
        {showAdvanced ? '▲ Hide' : '▼ Advanced'} options
      </button>

      {showAdvanced && (
        <div className="grid grid-cols-2 gap-4 p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Frames ({numFrames})
            </label>
            <input
              type="range" min={4} max={16} step={4}
              value={numFrames}
              onChange={(e) => setNumFrames(Number(e.target.value))}
              disabled={disabled}
              className="w-full accent-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Steps ({steps})
            </label>
            <input
              type="range" min={10} max={50} step={5}
              value={steps}
              onChange={(e) => setSteps(Number(e.target.value))}
              disabled={disabled}
              className="w-full accent-indigo-500"
            />
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={disabled || !prompt.trim()}
        className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700
                   disabled:text-gray-500 disabled:cursor-not-allowed text-white font-semibold
                   rounded-lg transition-colors text-sm"
      >
        {disabled ? 'Generating…' : 'Generate Video'}
      </button>
    </form>
  )
}
