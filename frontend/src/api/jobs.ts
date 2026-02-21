import client from './client'
import type { JobCreate, JobResponse } from '../types/job'

export async function submitJob(payload: JobCreate): Promise<JobResponse> {
  const { data } = await client.post<JobResponse>('/jobs', payload)
  return data
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const { data } = await client.get<JobResponse>(`/jobs/${jobId}`)
  return data
}

export async function listJobs(): Promise<JobResponse[]> {
  const { data } = await client.get<JobResponse[]>('/jobs')
  return data
}
