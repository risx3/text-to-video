import { useCallback, useRef, useState } from 'react'
import type { JobCreate, JobResponse, JobStatus, WSMessage } from '../types/job'
import { submitJob } from '../api/jobs'
import { useJobWebSocket } from './useJobWebSocket'

export interface VideoJobState {
  job: JobResponse | null
  isSubmitting: boolean
  error: string | null
}

export function useVideoJob() {
  const [state, setState] = useState<VideoJobState>({
    job: null,
    isSubmitting: false,
    error: null,
  })
  const jobIdRef = useRef<string | null>(null)
  const isActiveRef = useRef(false)

  const handleWsMessage = useCallback((msg: WSMessage) => {
    setState((prev) => {
      if (!prev.job) return prev

      const updates: Partial<JobResponse> = {}

      if (msg.percent !== undefined) updates.progress = msg.percent
      if (msg.message) updates.message = msg.message
      if (msg.status) updates.status = msg.status as JobStatus
      if (msg.video_url) updates.video_url = msg.video_url
      if (msg.enhanced_prompt) updates.enhanced_prompt = msg.enhanced_prompt
      if (msg.error) updates.error = msg.error

      if (msg.type === 'completed') {
        updates.status = 'completed'
        updates.progress = 100
        isActiveRef.current = false
      } else if (msg.type === 'error') {
        updates.status = 'failed'
        isActiveRef.current = false
      }

      return { ...prev, job: { ...prev.job, ...updates } }
    })
  }, [])

  const isTerminal =
    state.job?.status === 'completed' || state.job?.status === 'failed'

  useJobWebSocket({
    jobId: jobIdRef.current,
    onMessage: handleWsMessage,
    enabled: !isTerminal && jobIdRef.current !== null,
  })

  const submit = useCallback(async (payload: JobCreate) => {
    setState({ job: null, isSubmitting: true, error: null })
    try {
      const job = await submitJob(payload)
      jobIdRef.current = job.job_id
      isActiveRef.current = true
      setState({ job, isSubmitting: false, error: null })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed'
      setState((prev) => ({ ...prev, isSubmitting: false, error: message }))
    }
  }, [])

  const reset = useCallback(() => {
    jobIdRef.current = null
    isActiveRef.current = false
    setState({ job: null, isSubmitting: false, error: null })
  }, [])

  return { ...state, submit, reset }
}
