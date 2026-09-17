import type { Locale } from '@/i18n/config'

export const PROJECT_COLORS = [
  '#F44336',
  '#FF9800',
  '#FFEB3B',
  '#4CAF50',
  '#00CCCC',
  '#2196F3',
  '#3F51B5',
  '#9C27B0',
  '#E91E63',
  '#9E9E9E',
] as const

export type ProjectColor = (typeof PROJECT_COLORS)[number]

export const PROJECT_STATUSES = ['active', 'archived'] as const

export type ProjectStatus = (typeof PROJECT_STATUSES)[number]

export const TIME_FORMATS = ['12h', '24h'] as const

export type TimeFormatPreference = (typeof TIME_FORMATS)[number]

export interface User {
  id: string
  email: string
  is_active: boolean
  time_format: TimeFormatPreference
  locale: Locale
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface ResendCooldown {
  retry_after_seconds: number
}

export interface Session {
  id: number
  user_agent: string | null
  ip_address: string | null
  created_at: string
}

export interface Project {
  id: string
  name: string
  color: string
  hourly_rate: string | null
  round_to_hour: boolean
  status: ProjectStatus
}

export interface ProjectAddData {
  name: string
  color?: string | null
  hourly_rate?: string | null
  round_to_hour?: boolean
}

export interface ProjectUpdateData {
  name?: string
  color?: string
  hourly_rate?: string | null
  round_to_hour?: boolean
  status?: ProjectStatus
}

export interface RunningTimer {
  id: string
  start_time: string
  hourly_rate: string | null
  round_to_hour: boolean
  user_id: string
  project_id: string
}

export interface Timer {
  id: string
  start_time: string
  end_time: string | null
  duration: string | null
  hourly_rate: string | null
  round_to_hour: boolean
  billable_amount: string | null
  user_id: string
  project_id: string
}

export interface TimerManualAddData {
  project_id: string
  start_time: string
  end_time: string
}

export interface TimerUpdateData {
  project_id?: string
  start_time?: string
  end_time?: string
}

export interface Page<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export interface TimersFilter {
  page?: number
  page_size?: number
  project_id?: string | string[]
  date_from?: string
  date_to?: string
  billable?: boolean
  include_archived_projects?: boolean
}
