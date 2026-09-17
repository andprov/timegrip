import { apiFetch } from '@/api/client'
import type {
  Page,
  RunningTimer,
  Timer,
  TimerManualAddData,
  TimerUpdateData,
  TimersFilter,
} from '@/api/types'

export function listTimers(filter: TimersFilter): Promise<Page<Timer>> {
  return apiFetch<Page<Timer>>('/timers', { query: { ...filter } })
}

export function getTimer(id: string): Promise<Timer> {
  return apiFetch<Timer>(`/timers/${id}`)
}

export function getRunningTimer(): Promise<RunningTimer | null> {
  return apiFetch<RunningTimer | null>('/timers/running')
}

export function startTimer(projectId: string): Promise<RunningTimer> {
  return apiFetch<RunningTimer>('/timers/start', {
    method: 'POST',
    body: { project_id: projectId },
  })
}

export function stopTimer(): Promise<Timer> {
  return apiFetch<Timer>('/timers/stop', { method: 'POST' })
}

export function addManualTimer(data: TimerManualAddData): Promise<Timer> {
  return apiFetch<Timer>('/timers', { method: 'POST', body: data })
}

export function updateTimer(
  id: string,
  data: TimerUpdateData,
): Promise<Timer> {
  return apiFetch<Timer>(`/timers/${id}`, { method: 'PATCH', body: data })
}

export function deleteTimer(id: string): Promise<void> {
  return apiFetch<void>(`/timers/${id}`, { method: 'DELETE' })
}

export function deleteTimers(ids: string[]): Promise<void> {
  return apiFetch<void>('/timers', { method: 'DELETE', body: { ids } })
}
