import type { Project } from '@/api/types'
import { formatSecondsAsClock } from '@/lib/format'
import type { GroupByField, ReportColumn, ReportGroup } from '@/lib/report'
import { reportCellText } from '@/lib/report'

export interface ReportExportInput {
  groups: ReportGroup[]
  columns: ReportColumn[]
  groupBy: GroupByField
  projectById: Map<string, Project>
  hour12: boolean
  totalSeconds: number
  totalAmount: number
  filename: string
  totalLabel: string
  entriesLabel: string
}

function buildTotalRow(
  columns: ReportColumn[],
  totalSeconds: number,
  totalAmount: number,
  totalLabel: string,
): string[] {
  const firstMetricIndex = columns.findIndex(
    (c) => c.key === 'duration' || c.key === 'amount',
  )
  return columns.map((column, index) => {
    if (firstMetricIndex === -1) return index === 0 ? totalLabel : ''
    if (index < firstMetricIndex) return index === 0 ? totalLabel : ''
    if (column.key === 'duration') return formatSecondsAsClock(totalSeconds)
    if (column.key === 'amount') return totalAmount.toFixed(2)
    return ''
  })
}

function buildReportRows({
  groups,
  columns,
  groupBy,
  projectById,
  hour12,
  totalSeconds,
  totalAmount,
  totalLabel,
  entriesLabel,
}: ReportExportInput): string[][] {
  const rows: string[][] = [columns.map((column) => column.label)]

  for (const group of groups) {
    if (groupBy !== 'none') {
      const summary = `${group.label} (${group.timers.length} ${entriesLabel}, ${formatSecondsAsClock(group.totalSeconds)}, ${group.totalAmount.toFixed(2)})`
      rows.push([summary, ...Array(Math.max(0, columns.length - 1)).fill('')])
    }
    for (const timer of group.timers) {
      rows.push(
        columns.map((column) =>
          reportCellText(column.key, timer, projectById, hour12),
        ),
      )
    }
  }

  rows.push(buildTotalRow(columns, totalSeconds, totalAmount, totalLabel))

  return rows
}

function escapeCsvValue(value: string): string {
  return /[",\r\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function exportReportToCsv(input: ReportExportInput): void {
  const rows = buildReportRows(input)
  const csv = rows.map((row) => row.map(escapeCsvValue).join(',')).join('\r\n')
  const csvWithBom = '﻿' + csv
  downloadBlob(
    new Blob([csvWithBom], { type: 'text/csv;charset=utf-8;' }),
    input.filename,
  )
}
