import type { Project, Timer } from '@/api/types'
import {
  formatAmountPlain,
  formatDate,
  formatDurationClock,
  formatTime,
  isSameDay,
  parseIsoDurationSeconds,
} from '@/lib/format'
import { compareNames } from '@/lib/sort'

export type GroupByField = 'none' | 'project' | 'date'

export interface ReportColumn {
  key: string
  label: string
}

export const REPORT_COLUMNS: ReportColumn[] = [
  { key: 'date', label: 'Date' },
  { key: 'project', label: 'Project' },
  { key: 'start', label: 'Start' },
  { key: 'end', label: 'End' },
  { key: 'duration', label: 'Duration' },
  { key: 'rounded', label: 'Rounded' },
  { key: 'amount', label: 'Amount' },
]

export const DEFAULT_VISIBLE_COLUMNS = [
  'date',
  'project',
  'start',
  'end',
  'duration',
  'amount',
]

export interface ReportGroup {
  key: string
  label: string
  timers: Timer[]
  totalSeconds: number
  totalAmount: number
}

export function sumDurationSeconds(timers: Timer[]): number {
  return timers.reduce(
    (total, timer) =>
      total + (timer.duration ? parseIsoDurationSeconds(timer.duration) : 0),
    0,
  )
}

export function sumBillableAmount(timers: Timer[]): number {
  return timers.reduce(
    (total, timer) =>
      total + (timer.billable_amount ? Number(timer.billable_amount) : 0),
    0,
  )
}

function dayKey(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function groupKey(timer: Timer, groupBy: GroupByField): string {
  switch (groupBy) {
    case 'project':
      return timer.project_id
    case 'date':
      return dayKey(new Date(timer.start_time))
    case 'none':
      return 'all'
  }
}

function groupLabel(
  sample: Timer,
  groupBy: GroupByField,
  projectById: Map<string, Project>,
  unknownProjectLabel: string,
): string {
  switch (groupBy) {
    case 'project':
      return projectById.get(sample.project_id)?.name ?? unknownProjectLabel
    case 'date':
      return formatDate(new Date(sample.start_time))
    case 'none':
      return ''
  }
}

function compareGroups(
  a: ReportGroup,
  b: ReportGroup,
  groupBy: GroupByField,
): number {
  if (groupBy === 'project') return compareNames(a.label, b.label)
  if (groupBy === 'date') return b.key.localeCompare(a.key)
  return 0
}

export function groupTimers(
  timers: Timer[],
  groupBy: GroupByField,
  projectById: Map<string, Project>,
  unknownProjectLabel = 'Unknown project',
): ReportGroup[] {
  if (groupBy === 'none') {
    return [
      {
        key: 'all',
        label: '',
        timers,
        totalSeconds: sumDurationSeconds(timers),
        totalAmount: sumBillableAmount(timers),
      },
    ]
  }

  const groups = new Map<string, Timer[]>()
  for (const timer of timers) {
    const key = groupKey(timer, groupBy)
    const list = groups.get(key)
    if (list) list.push(timer)
    else groups.set(key, [timer])
  }

  const result: ReportGroup[] = [...groups.entries()].map(
    ([key, groupItems]) => ({
      key,
      label: groupLabel(groupItems[0], groupBy, projectById, unknownProjectLabel),
      timers: groupItems,
      totalSeconds: sumDurationSeconds(groupItems),
      totalAmount: sumBillableAmount(groupItems),
    }),
  )

  return result.sort((a, b) => compareGroups(a, b, groupBy))
}

export function groupedColumnKey(groupBy: GroupByField): string | null {
  if (groupBy === 'none') return null
  return groupBy
}

export function reportCellText(
  key: string,
  timer: Timer,
  projectById: Map<string, Project>,
  hour12: boolean,
): string {
  switch (key) {
    case 'date':
      return formatDate(new Date(timer.start_time))
    case 'project':
      return projectById.get(timer.project_id)?.name ?? '—'
    case 'start':
      return formatTime(new Date(timer.start_time), hour12)
    case 'end': {
      if (!timer.end_time) return ''
      const end = new Date(timer.end_time)
      return isSameDay(new Date(timer.start_time), end)
        ? formatTime(end, hour12)
        : `${formatDate(end)} ${formatTime(end, hour12)}`
    }
    case 'duration':
      return formatDurationClock(timer.duration)
    case 'rounded':
      return projectById.get(timer.project_id)?.round_to_hour ? 'R' : ''
    case 'amount':
      return formatAmountPlain(timer.billable_amount)
    default:
      return ''
  }
}
