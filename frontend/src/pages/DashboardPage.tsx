import { Fragment, useState } from 'react'
import { useTranslation } from 'react-i18next'

import type { Timer } from '@/api/types'
import { useAllProjects } from '@/hooks/useAllProjects'
import { useAllTimers } from '@/hooks/useAllTimers'
import { useDateRangeFilter } from '@/hooks/useDateRangeFilter'
import { Alert } from '@/components/ui/Alert'
import { BarChart } from '@/components/ui/BarChart'
import { Card } from '@/components/ui/Card'
import { DateRangeFilter } from '@/components/ui/DateRangeFilter'
import { MultiSelect } from '@/components/ui/MultiSelect'
import { PieChart } from '@/components/ui/PieChart'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import {
  aggregateProjectTotals,
  aggregateTimeSeries,
  foldIntoChartSlices,
  topByAmount,
} from '@/lib/dashboard'
import { formatAmount, formatSecondsAsClock } from '@/lib/format'
import { sumBillableAmount, sumDurationSeconds } from '@/lib/report'
import { compareNames } from '@/lib/sort'

function hasEnded(timer: Timer): boolean {
  return timer.end_time !== null
}

export function DashboardPage() {
  const { t } = useTranslation('dashboard')
  const { t: tc } = useTranslation('common')
  const projectsQuery = useAllProjects()
  const [projectIds, setProjectIds] = useState<string[]>([])
  const [billableFilter, setBillableFilter] = useState<'' | 'true' | 'false'>(
    '',
  )
  const { dateFrom, dateTo, onChange: handleDateRangeChange } =
    useDateRangeFilter()

  const projects = [...(projectsQuery.data?.items ?? [])].sort((a, b) =>
    compareNames(a.name, b.name),
  )
  const projectById = new Map(projects.map((p) => [p.id, p]))
  const billableProjects =
    billableFilter === ''
      ? projects
      : billableFilter === 'true'
        ? projects.filter((p) => p.hourly_rate !== null)
        : projects.filter((p) => p.hourly_rate === null)

  const timersQuery = useAllTimers({
    project_id: projectIds.length > 0 ? projectIds : undefined,
    billable: billableFilter === '' ? undefined : billableFilter === 'true',
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    include_archived_projects: true,
  })

  const timers = (timersQuery.data ?? []).filter(hasEnded)
  const totalSeconds = sumDurationSeconds(timers)
  const totalAmount = sumBillableAmount(timers)
  const projectTotals = aggregateProjectTotals(timers, projectById)
  const slices = foldIntoChartSlices(projectTotals)
  const topProjectByTime = projectTotals[0] ?? null
  const showAmountCard = billableFilter !== 'false'
  const topProjectByAmount = showAmountCard ? topByAmount(projectTotals) : null
  const timeSeries = aggregateTimeSeries(
    timers,
    dateFrom ? new Date(dateFrom) : null,
    dateTo ? new Date(dateTo) : null,
  )
  const timeSeriesTitle =
    timeSeries.granularity === 'hour'
      ? t('timeByHour')
      : timeSeries.granularity === 'month'
        ? t('timeByMonth')
        : t('timeByDay')

  return (
    <div>
      <div className="mb-6 flex min-h-9 flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{tc('dashboard')}</h1>
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
          options={billableProjects.map((project) => ({
            value: project.id,
            label: project.name,
            color: project.color,
          }))}
        />
        <Select
          className="w-full sm:w-40"
          value={billableFilter}
          onChange={(v) => {
            setBillableFilter(v as '' | 'true' | 'false')
            setProjectIds([])
          }}
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
      </div>

      {timersQuery.isPending && (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      )}

      {timersQuery.isError && <Alert>{t('loadFailed')}</Alert>}

      {timersQuery.isSuccess && (
        <div className="space-y-3">
          <div
            className={`grid grid-cols-1 gap-3 sm:grid-cols-2 ${showAmountCard ? 'lg:grid-cols-4' : 'lg:grid-cols-3'}`}
          >
            <Card>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalTime')}</p>
              <p className="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">
                {formatSecondsAsClock(totalSeconds)}
              </p>
              <p className="mt-1 text-sm text-transparent select-none">{' '}</p>
            </Card>
            <Card>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalAmount')}</p>
              <p className="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">
                {formatAmount(totalAmount)}
              </p>
              <p className="mt-1 text-sm text-transparent select-none">{' '}</p>
            </Card>
            <Card>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('topProjectByTime')}
              </p>
              <div className="mt-1 flex h-9 min-w-0 items-center gap-2">
                {topProjectByTime && (
                  <span
                    className="size-3 shrink-0 rounded-full"
                    style={{ backgroundColor: topProjectByTime.color }}
                  />
                )}
                <p
                  className="min-w-0 truncate text-xl font-semibold text-gray-900 dark:text-gray-100"
                  title={topProjectByTime ? topProjectByTime.label : undefined}
                >
                  {topProjectByTime ? topProjectByTime.label : '—'}
                </p>
              </div>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {topProjectByTime
                  ? formatSecondsAsClock(topProjectByTime.totalSeconds)
                  : ' '}
              </p>
            </Card>
            {showAmountCard && (
              <Card>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('topProjectByAmount')}
                </p>
                <div className="mt-1 flex h-9 min-w-0 items-center gap-2">
                  {topProjectByAmount && (
                    <span
                      className="size-3 shrink-0 rounded-full"
                      style={{ backgroundColor: topProjectByAmount.color }}
                    />
                  )}
                  <p
                    className="min-w-0 truncate text-xl font-semibold text-gray-900 dark:text-gray-100"
                    title={topProjectByAmount ? topProjectByAmount.label : undefined}
                  >
                    {topProjectByAmount ? topProjectByAmount.label : '—'}
                  </p>
                </div>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {topProjectByAmount
                    ? formatAmount(topProjectByAmount.totalAmount)
                    : ' '}
                </p>
              </Card>
            )}
          </div>

          <Card>
            <p className="mb-4 text-sm font-medium text-gray-900 dark:text-gray-100">
              {t('timeByProject')}
            </p>
            {slices.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('noTimeEntries')}
              </p>
            ) : (
              <div className="flex flex-col items-center gap-6 sm:flex-row">
                <PieChart
                  slices={slices.map((slice) => ({
                    key: slice.key,
                    label: slice.label,
                    value: slice.totalSeconds,
                    color: slice.color,
                  }))}
                  formatValue={formatSecondsAsClock}
                  centerLabel={formatSecondsAsClock(totalSeconds)}
                />
                <div className="grid w-full min-w-0 grid-cols-[minmax(0,1fr)_auto_auto_auto] items-center gap-x-3 gap-y-1.5 text-sm sm:max-w-xs">
                  {slices.map((slice) => (
                    <Fragment key={slice.key}>
                      <span className="flex min-w-0 items-center gap-2">
                        <span
                          className="size-3 shrink-0 rounded-full"
                          style={{ backgroundColor: slice.color }}
                        />
                        <span className="truncate text-gray-700 dark:text-gray-300">
                          {slice.label}
                        </span>
                      </span>
                      <span className="whitespace-nowrap tabular-nums text-gray-500 dark:text-gray-400">
                        {formatSecondsAsClock(slice.totalSeconds)}
                      </span>
                      <span className="whitespace-nowrap tabular-nums text-gray-400 dark:text-gray-500">
                        {totalSeconds > 0
                          ? Math.round((slice.totalSeconds / totalSeconds) * 100)
                          : 0}
                        %
                      </span>
                      <span className="whitespace-nowrap tabular-nums text-gray-500 dark:text-gray-400">
                        {formatAmount(slice.totalAmount)}
                      </span>
                    </Fragment>
                  ))}
                </div>
              </div>
            )}
          </Card>

          <Card>
            <p className="mb-4 text-sm font-medium text-gray-900 dark:text-gray-100">
              {timeSeriesTitle}
            </p>
            <BarChart
              points={timeSeries.points.map((point) => ({
                key: point.key,
                label: point.label,
                value: point.totalSeconds,
              }))}
              formatValue={formatSecondsAsClock}
            />
          </Card>
        </div>
      )}
    </div>
  )
}
