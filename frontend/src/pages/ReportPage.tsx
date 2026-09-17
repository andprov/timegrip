import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import type { Timer, TimersFilter } from '@/api/types'
import { useAllProjects } from '@/hooks/useAllProjects'
import { useAllTimers } from '@/hooks/useAllTimers'
import { useDateRangeFilter } from '@/hooks/useDateRangeFilter'
import { useTimeFormat } from '@/hooks/useTimeFormat'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { DateRangeFilter } from '@/components/ui/DateRangeFilter'
import { DateTimeText } from '@/components/ui/DateTimeText'
import { MultiSelect } from '@/components/ui/MultiSelect'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import {
  formatAmount,
  formatDate,
  formatDurationClock,
  formatSecondsAsClock,
  formatTime,
  isSameDay,
} from '@/lib/format'
import type { GroupByField } from '@/lib/report'
import {
  DEFAULT_VISIBLE_COLUMNS,
  REPORT_COLUMNS,
  groupTimers,
  groupedColumnKey,
  sumBillableAmount,
  sumDurationSeconds,
} from '@/lib/report'
import { exportReportToCsv } from '@/lib/reportExport'
import { compareNames } from '@/lib/sort'

function hasEnded(timer: Timer): boolean {
  return timer.end_time !== null
}

type ReportFilters = Omit<TimersFilter, 'page' | 'page_size'>

export function ReportPage() {
  const { t } = useTranslation('report')
  const GROUP_BY_OPTIONS: { value: GroupByField; label: string }[] = [
    { value: 'none', label: t('noGrouping') },
    { value: 'project', label: t('groupByProject') },
    { value: 'date', label: t('groupByDate') },
  ]
  const projectsQuery = useAllProjects()
  const { hour12 } = useTimeFormat()
  const [projectIds, setProjectIds] = useState<string[]>([])
  const [billableFilter, setBillableFilter] = useState<'' | 'true' | 'false'>(
    '',
  )
  const { dateFrom, dateTo, onChange: handleDateRangeChange } =
    useDateRangeFilter()
  const [groupBy, setGroupBy] = useState<GroupByField>('none')
  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    DEFAULT_VISIBLE_COLUMNS,
  )
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters | null>(
    null,
  )

  const projects = [...(projectsQuery.data?.items ?? [])].sort((a, b) =>
    compareNames(a.name, b.name),
  )
  const projectById = new Map(projects.map((p) => [p.id, p]))

  function handleGenerate() {
    setAppliedFilters({
      project_id: projectIds.length > 0 ? projectIds : undefined,
      billable: billableFilter === '' ? undefined : billableFilter === 'true',
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      include_archived_projects: true,
    })
  }

  const timersQuery = useAllTimers(
    appliedFilters ?? {},
    appliedFilters !== null,
  )

  const timers = (timersQuery.data ?? []).filter(hasEnded)
  const groups = groupTimers(timers, groupBy, projectById, t('unknownProject'))
  const hiddenColumnKey = groupedColumnKey(groupBy)
  const activeColumns = REPORT_COLUMNS.filter(
    (column) =>
      visibleColumns.includes(column.key) && column.key !== hiddenColumnKey,
  )
  const totalSeconds = sumDurationSeconds(timers)
  const totalAmount = sumBillableAmount(timers)
  const firstMetricIndex = activeColumns.findIndex(
    (c) => c.key === 'duration' || c.key === 'amount',
  )
  const leadingColumnCount =
    firstMetricIndex === -1 ? activeColumns.length : firstMetricIndex
  const trailingColumns =
    firstMetricIndex === -1 ? [] : activeColumns.slice(firstMetricIndex)

  function renderCell(key: string, timer: Timer) {
    switch (key) {
      case 'date':
        return formatDate(new Date(timer.start_time))
      case 'project':
        return projectById.get(timer.project_id)?.name ?? '—'
      case 'start':
        return formatTime(new Date(timer.start_time), hour12)
      case 'end': {
        // Running timers are filtered out before rendering (see hasEnded).
        const endTime = timer.end_time as string
        return isSameDay(new Date(timer.start_time), new Date(endTime)) ? (
          formatTime(new Date(endTime), hour12)
        ) : (
          <DateTimeText iso={endTime} hour12={hour12} />
        )
      }
      case 'duration':
        return formatDurationClock(timer.duration)
      case 'rounded':
        return projectById.get(timer.project_id)?.round_to_hour ? (
          <span title={t('roundedToHourTitle')}>R</span>
        ) : null
      case 'amount':
        return formatAmount(timer.billable_amount)
      default:
        return null
    }
  }

  function exportFilenameBase(): string {
    if (appliedFilters?.date_from && appliedFilters.date_to) {
      return `report_${appliedFilters.date_from.slice(0, 10)}_${appliedFilters.date_to.slice(0, 10)}`
    }
    return `report_${new Date().toISOString().slice(0, 10)}`
  }

  function handleExportCsv() {
    exportReportToCsv({
      groups,
      columns: activeColumns.map((column) => ({
        ...column,
        label: t(`columns.${column.key}`),
      })),
      groupBy,
      projectById,
      hour12,
      totalSeconds,
      totalAmount,
      totalLabel: t('total'),
      entriesLabel: t('entries'),
      filename: `${exportFilenameBase()}.csv`,
    })
  }

  return (
    <div>
      <div className="mb-6 flex min-h-9 flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{t('title')}</h1>
      </div>

      <div className="mb-4 grid grid-cols-2 items-center gap-3 sm:flex sm:flex-wrap">
        <MultiSelect
          searchable
          className="w-full sm:w-40"
          placeholder={t('allProjects')}
          countLabel={t('projectCountLabel')}
          showSelectAll={false}
          values={projectIds}
          onChange={setProjectIds}
          options={projects.map((project) => ({
            value: project.id,
            label: project.name,
            color: project.color,
          }))}
        />
        <Select
          className="w-full sm:w-40"
          value={billableFilter}
          onChange={(v) => setBillableFilter(v as '' | 'true' | 'false')}
          options={[
            { value: '', label: t('allBilling') },
            { value: 'true', label: t('billable') },
            { value: 'false', label: t('nonBillable') },
          ]}
        />
        <DateRangeFilter
          className="w-full sm:w-auto sm:min-w-40"
          from={dateFrom}
          to={dateTo}
          onChange={handleDateRangeChange}
        />
        <Button
          className="col-span-2 w-full sm:w-auto"
          onClick={handleGenerate}
          disabled={appliedFilters !== null && timersQuery.isFetching}
        >
          {appliedFilters !== null && timersQuery.isFetching
            ? t('generating')
            : t('generateReport')}
        </Button>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 sm:flex sm:flex-wrap">
        <Select
          className="w-full sm:w-40"
          value={groupBy}
          onChange={(v) => setGroupBy(v as GroupByField)}
          options={GROUP_BY_OPTIONS}
        />
        <MultiSelect
          className="w-full sm:w-40"
          title={t('columnsTitle')}
          applyButton
          showSelectAll={false}
          showClear={false}
          minSelected={1}
          values={visibleColumns}
          onChange={setVisibleColumns}
          options={REPORT_COLUMNS.map((column) => ({
            value: column.key,
            label: t(`columns.${column.key}`),
          }))}
        />
      </div>

      {appliedFilters === null && (
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('setupFilters')}
          </p>
        </Card>
      )}

      {appliedFilters !== null && timersQuery.isPending && (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      )}

      {appliedFilters !== null && timersQuery.isError && (
        <Alert>{t('loadFailed')}</Alert>
      )}

      {appliedFilters !== null &&
        timersQuery.isSuccess &&
        timers.length === 0 && (
          <Card>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('noTimeEntries')}</p>
          </Card>
        )}

      {appliedFilters !== null &&
        timersQuery.isSuccess &&
        timers.length > 0 &&
        activeColumns.length === 0 && (
          <Alert>
            {t('pickColumn')}
          </Alert>
        )}

      {appliedFilters !== null &&
        timersQuery.isSuccess &&
        timers.length > 0 &&
        activeColumns.length > 0 && (
          <div className="mb-4 flex justify-end">
            <Button variant="secondary" onClick={handleExportCsv}>
              {t('exportCsv')}
            </Button>
          </div>
        )}

      {appliedFilters !== null &&
        timersQuery.isSuccess &&
        timers.length > 0 &&
        activeColumns.length > 0 && (
          <div className="overflow-x-auto rounded-lg ring-1 ring-gray-200 dark:ring-gray-800">
            <table className="w-full table-auto text-sm">
              <thead className="border-b-2 border-gray-200 bg-gray-50 text-left text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
                <tr>
                  {activeColumns.map((column) => (
                    <th key={column.key} className="px-4 py-2 font-medium">
                      {t(`columns.${column.key}`)}
                    </th>
                  ))}
                </tr>
              </thead>
              {groups.map((group) => (
                <tbody
                  key={group.key}
                  className="divide-y divide-gray-100 border-b border-gray-100 bg-white dark:divide-gray-800 dark:border-gray-800 dark:bg-gray-900"
                >
                  {groupBy !== 'none' && (
                    <tr className="bg-indigo-50 dark:bg-indigo-950/50">
                      <td
                        colSpan={activeColumns.length}
                        className="px-4 py-2 font-semibold text-indigo-900 dark:text-indigo-200"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span>{group.label}</span>
                          <span className="text-xs font-normal text-indigo-700 dark:text-indigo-300">
                            {group.timers.length} {t('entries')} ·{' '}
                            {formatSecondsAsClock(group.totalSeconds)} ·{' '}
                            {formatAmount(group.totalAmount)}
                          </span>
                        </div>
                      </td>
                    </tr>
                  )}
                  {group.timers.map((timer) => (
                    <tr key={timer.id}>
                      {activeColumns.map((column) => (
                        <td
                          key={column.key}
                          className="truncate px-4 py-2 text-gray-500 dark:text-gray-400"
                        >
                          {renderCell(column.key, timer)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              ))}
              <tfoot className="bg-gray-50 font-medium text-gray-900 dark:bg-gray-900 dark:text-gray-100">
                <tr>
                  {leadingColumnCount > 0 && (
                    <td colSpan={leadingColumnCount} className="px-4 py-2">
                      {t('total')}
                    </td>
                  )}
                  {trailingColumns.map((column) => (
                    <td key={column.key} className="px-4 py-2">
                      {column.key === 'duration'
                        ? formatSecondsAsClock(totalSeconds)
                        : column.key === 'amount'
                          ? formatAmount(totalAmount)
                          : ''}
                    </td>
                  ))}
                </tr>
              </tfoot>
            </table>
          </div>
        )}
    </div>
  )
}
