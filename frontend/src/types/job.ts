export type JobStatus =
  | 'pending'
  | 'enhancing'
  | 'generating'
  | 'completed'
  | 'failed'

export interface JobCreate {
  prompt: string
  num_frames?: number
  num_inference_steps?: number
  guidance_scale?: number
  width?: number
  height?: number
}

export interface JobResponse {
  job_id: string
  status: JobStatus
  prompt: string
  enhanced_prompt?: string
  progress: number
  message: string
  video_url?: string
  error?: string
  created_at: string
  updated_at: string
}

export type WSMessageType = 'progress' | 'completed' | 'error' | 'state' | 'ping'

export interface WSMessage {
  type: WSMessageType
  job_id: string
  percent?: number
  message?: string
  video_url?: string
  enhanced_prompt?: string
  status?: JobStatus
  error?: string
}
