import type { Project, Timer } from '@/api/types'
import { startOfMonth } from '@/lib/calendar'
import { isSameDay, parseIsoDurationSeconds } from '@/lib/format'

export interface ProjectSlice {
  key: string
  label: string
  color: string
  totalSeconds: number
  totalAmount: number
}

const OTHER_COLOR = '#9CA3AF'
const MAX_SLICES = 7

function timerSeconds(timer: Timer): number {
  return timer.duration ? parseIsoDurationSeconds(timer.duration) : 0
}

function timerAmount(timer: Timer): number {
  return timer.billable_amount ? Number(timer.billable_amount) : 0
}

/** Per-project totals for every project present in `timers`, sorted by time descending. */
export function aggregateProjectTotals(
  timers: Timer[],
  projectById: Map<string, Project>,
): ProjectSlice[] {
  const totals = new Map<string, { seconds: number; amount: number }>()
  for (const timer of timers) {
    const seconds = timerSeconds(timer)
    const amount = timerAmount(timer)
    if (seconds <= 0 && amount <= 0) continue
    const current = totals.get(timer.project_id) ?? { seconds: 0, amount: 0 }
    totals.set(timer.project_id, {
      seconds: current.seconds + seconds,
      amount: current.amount + amount,
    })
  }

  return [...totals.entries()]
    .map(([projectId, { seconds, amount }]) => ({
      key: projectId,
      label: projectById.get(projectId)?.name ?? 'Unknown project',
      color: projectById.get(projectId)?.color ?? OTHER_COLOR,
      totalSeconds: seconds,
      totalAmount: amount,
    }))
    .sort((a, b) => b.totalSeconds - a.totalSeconds)
}

/** Folds every project past the top `MAX_SLICES - 1` into an "Other" slice, for chart display. */
export function foldIntoChartSlices(totals: ProjectSlice[]): ProjectSlice[] {
  if (totals.length <= MAX_SLICES) return totals

  const top = totals.slice(0, MAX_SLICES - 1)
  const rest = totals.slice(MAX_SLICES - 1)
  const otherSeconds = rest.reduce((sum, s) => sum + s.totalSeconds, 0)
  const otherAmount = rest.reduce((sum, s) => sum + s.totalAmount, 0)
  return [
    ...top,
    {
      key: 'other',
      label: 'Other',
      color: OTHER_COLOR,
      totalSeconds: otherSeconds,
      totalAmount: otherAmount,
    },
  ]
}

export function topByAmount(totals: ProjectSlice[]): ProjectSlice | null {
  if (totals.length === 0) return null
  return totals.reduce((best, slice) =>
    slice.totalAmount > best.totalAmount ? slice : best,
  )
}

export type TimeGranularity = 'hour' | 'day' | 'month'

export interface TimeSeriesPoint {
  key: string
  label: string
  totalSeconds: number
}

export interface TimeSeriesResult {
  granularity: TimeGranularity
  points: TimeSeriesPoint[]
}

/** A day range longer than this is grouped by month instead of by day. */
const DAY_GRANULARITY_MAX_DAYS = 62
const MS_PER_DAY = 86400000

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function diffInDays(start: Date, end: Date): number {
  return (
    Math.round(
      (startOfDay(end).getTime() - startOfDay(start).getTime()) / MS_PER_DAY,
    ) + 1
  )
}

function pickGranularity(rangeFrom: Date, rangeTo: Date): TimeGranularity {
  const days = diffInDays(rangeFrom, rangeTo)
  if (days <= 1) return 'hour'
  if (days <= DAY_GRANULARITY_MAX_DAYS) return 'day'
  return 'month'
}

function dayKey(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function formatShortDate(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}`
}

function aggregateByHour(timers: Timer[], day: Date): TimeSeriesPoint[] {
  const totals = new Map<number, number>()
  for (const timer of timers) {
    const start = new Date(timer.start_time)
    if (!isSameDay(start, day)) continue
    const seconds = timerSeconds(timer)
    if (seconds <= 0) continue
    const hour = start.getHours()
    totals.set(hour, (totals.get(hour) ?? 0) + seconds)
  }

  return Array.from({ length: 24 }, (_, hour) => ({
    key: hour.toString().padStart(2, '0'),
    label: `${hour.toString().padStart(2, '0')}:00`,
    totalSeconds: totals.get(hour) ?? 0,
  }))
}

function aggregateByDayRange(
  timers: Timer[],
  rangeFrom: Date,
  rangeTo: Date,
): TimeSeriesPoint[] {
  const totals = new Map<string, number>()
  for (const timer of timers) {
    const seconds = timerSeconds(timer)
    if (seconds <= 0) continue
    const key = dayKey(new Date(timer.start_time))
    totals.set(key, (totals.get(key) ?? 0) + seconds)
  }

  const points: TimeSeriesPoint[] = []
  const cursor = new Date(rangeFrom)
  while (cursor.getTime() <= rangeTo.getTime()) {
    const key = dayKey(cursor)
    points.push({
      key,
      label: formatShortDate(cursor),
      totalSeconds: totals.get(key) ?? 0,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return points
}

function monthKey(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`
}

function formatMonthShortLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { month: 'short' })
}

function aggregateByMonthRange(
  timers: Timer[],
  rangeFrom: Date,
  rangeTo: Date,
): TimeSeriesPoint[] {
  const totals = new Map<string, number>()
  for (const timer of timers) {
    const seconds = timerSeconds(timer)
    if (seconds <= 0) continue
    const key = monthKey(new Date(timer.start_time))
    totals.set(key, (totals.get(key) ?? 0) + seconds)
  }

  const points: TimeSeriesPoint[] = []
  const cursor = startOfMonth(rangeFrom)
  const last = startOfMonth(rangeTo)
  while (cursor.getTime() <= last.getTime()) {
    const key = monthKey(cursor)
    points.push({
      key,
      label: formatMonthShortLabel(cursor),
      totalSeconds: totals.get(key) ?? 0,
    })
    cursor.setMonth(cursor.getMonth() + 1)
  }
  return points
}

/**
 * Total time bucketed by hour, day, or month depending on how long
 * [rangeFrom, rangeTo] spans: a single day groups by hour, up to ~2 months
 * groups by day, longer spans group by month. Falls back to the span of
 * `timers` when no explicit range is given.
 */
export function aggregateTimeSeries(
  timers: Timer[],
  rangeFrom: Date | null,
  rangeTo: Date | null,
): TimeSeriesResult {
  let start = rangeFrom ? startOfDay(rangeFrom) : null
  let end = rangeTo ? startOfDay(rangeTo) : null
  if (!start || !end) {
    const times = timers.map((t) => startOfDay(new Date(t.start_time)).getTime())
    if (times.length === 0) return { granularity: 'day', points: [] }
    start ??= new Date(Math.min(...times))
    end ??= new Date(Math.max(...times))
  }

  const granularity = pickGranularity(start, end)
  if (granularity === 'hour') {
    return { granularity, points: aggregateByHour(timers, start) }
  }
  if (granularity === 'month') {
    return { granularity, points: aggregateByMonthRange(timers, start, end) }
  }
  return { granularity, points: aggregateByDayRange(timers, start, end) }
}
