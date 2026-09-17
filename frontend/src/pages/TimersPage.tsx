import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import {
  addManualTimer,
  deleteTimer,
  deleteTimers,
  listTimers,
  updateTimer,
} from '@/api/timers'
import type { Timer } from '@/api/types'
import { useAllProjects } from '@/hooks/useAllProjects'
import { useDateRangeFilter } from '@/hooks/useDateRangeFilter'
import { useTimeFormat } from '@/hooks/useTimeFormat'
import type { TimerFormValues } from '@/components/TimerFormModal'
import { TimerFormModal } from '@/components/TimerFormModal'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { DateRangeFilter } from '@/components/ui/DateRangeFilter'
import { DateTimeText } from '@/components/ui/DateTimeText'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import { Switch } from '@/components/ui/Switch'
import {
  formatAmount,
  formatDate,
  formatDurationClock,
  formatTime,
  isSameDay,
} from '@/lib/format'
import { TIMERS_PAGE_SIZE } from '@/lib/pagination'
import { compareNames } from '@/lib/sort'

export function TimersPage() {
  const { t } = useTranslation('timers')
  const { t: tc } = useTranslation('common')
  const queryClient = useQueryClient()
  const projectsQuery = useAllProjects()
  const { hour12 } = useTimeFormat()
  const [page, setPage] = useState(1)
  const [projectFilter, setProjectFilter] = useState('')
  const [billableFilter, setBillableFilter] = useState<'' | 'true' | 'false'>('')
  const [showArchivedProjects, setShowArchivedProjects] = useState(false)
  const { dateFrom, dateTo, onChange: handleDateRangeChange } =
    useDateRangeFilter()
  const [modalTimer, setModalTimer] = useState<Timer | 'new' | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)

  const timersQuery = useQuery({
    queryKey: [
      'timers',
      'list',
      page,
      projectFilter,
      billableFilter,
      dateFrom,
      dateTo,
      showArchivedProjects,
    ],
    queryFn: () =>
      listTimers({
        page,
        page_size: TIMERS_PAGE_SIZE,
        project_id: projectFilter || undefined,
        billable: billableFilter === '' ? undefined : billableFilter === 'true',
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        include_archived_projects: showArchivedProjects,
      }),
    placeholderData: keepPreviousData,
  })

  const createMutation = useMutation({
    mutationFn: addManualTimer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timers'] })
      setModalTimer(null)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Parameters<typeof updateTimer>[1]) =>
      updateTimer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timers'] })
      setModalTimer(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTimer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timers'] })
      setModalTimer(null)
    },
  })

  const bulkDeleteMutation = useMutation({
    mutationFn: deleteTimers,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timers'] })
      setSelectedIds(new Set())
      setConfirmingBulkDelete(false)
    },
  })

  const projects = [...(projectsQuery.data?.items ?? [])].sort((a, b) =>
    compareNames(a.name, b.name),
  )
  const projectById = new Map(projects.map((p) => [p.id, p]))
  const activeProjects = projects.filter((p) => p.status === 'active')
  const filterableProjects = showArchivedProjects ? projects : activeProjects

  function handleSubmit(values: TimerFormValues) {
    if (modalTimer === 'new' || modalTimer === null) {
      createMutation.mutate(values)
    } else {
      updateMutation.mutate({ id: modalTimer.id, ...values })
    }
  }

  const activeMutation = modalTimer === 'new' ? createMutation : updateMutation

  function closeModal() {
    createMutation.reset()
    updateMutation.reset()
    setModalTimer(null)
  }

  const totalPages = timersQuery.data
    ? Math.max(1, Math.ceil(timersQuery.data.total / TIMERS_PAGE_SIZE))
    : 1

  useEffect(() => {
    if (timersQuery.data && page > totalPages) {
      goToPage(totalPages)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timersQuery.data, page, totalPages])

  const visibleTimers = timersQuery.data?.items ?? []
  const selectableTimers = visibleTimers.filter((timer) => timer.end_time)
  const allSelected =
    selectableTimers.length > 0 &&
    selectableTimers.every((timer) => selectedIds.has(timer.id))
  const someSelected = selectableTimers.some((timer) =>
    selectedIds.has(timer.id),
  )

  function toggleSelected(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (allSelected) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(selectableTimers.map((timer) => timer.id)))
    }
  }

  function goToPage(next: number) {
    setSelectedIds(new Set())
    setPage(next)
  }

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-0">
        <h1 className="flex min-h-9 items-center text-2xl font-semibold text-gray-900 dark:text-gray-100">
          {t('title')}
        </h1>
        <Button
          className="w-full sm:w-40"
          onClick={() => {
            setConfirmingDelete(false)
            setModalTimer('new')
          }}
          disabled={activeProjects.length === 0}
        >
          {t('addTimeEntry')}
        </Button>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 sm:flex sm:flex-wrap sm:items-center">
        <Select
          searchable
          className="w-full sm:w-40"
          value={projectFilter}
          onChange={(v) => {
            setProjectFilter(v)
            goToPage(1)
          }}
          options={[
            { value: '', label: t('allProjects') },
            ...filterableProjects.map((project) => ({
              value: project.id,
              label: project.name,
              color: project.color,
            })),
          ]}
        />
        <Select
          className="w-full sm:w-40"
          value={billableFilter}
          onChange={(v) => {
            setBillableFilter(v as '' | 'true' | 'false')
            goToPage(1)
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
          onChange={(nextFrom, nextTo) => {
            handleDateRangeChange(nextFrom, nextTo)
            goToPage(1)
          }}
        />
        <Switch
          checked={showArchivedProjects}
          label={t('showArchivedProjects')}
          onChange={(checked) => {
            setShowArchivedProjects(checked)
            if (!checked && projectById.get(projectFilter)?.status === 'archived') {
              setProjectFilter('')
            }
            goToPage(1)
          }}
        />
      </div>

      {selectedIds.size > 0 && (
        <div className="mb-4 flex items-center gap-3 rounded-md bg-indigo-50 px-4 py-2 dark:bg-indigo-950/50">
          <span className="text-sm text-indigo-900 dark:text-indigo-200">
            {tc('nSelected', { count: selectedIds.size })}
          </span>
          <Button variant="danger" onClick={() => setConfirmingBulkDelete(true)}>
            {t('deleteSelected')}
          </Button>
        </div>
      )}

      {timersQuery.isPending && (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      )}

      {timersQuery.isError && <Alert>{t('loadFailed')}</Alert>}
      {bulkDeleteMutation.isError && (
        <Alert>{t('bulkDeleteFailed')}</Alert>
      )}

      {timersQuery.data && timersQuery.data.items.length === 0 && (
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">{t('noTimeEntries')}</p>
        </Card>
      )}

      {timersQuery.data && timersQuery.data.items.length > 0 && (
        <div className="min-h-[612px] overflow-x-auto rounded-lg ring-1 ring-gray-200 dark:ring-gray-800">
          <table className="w-full table-auto text-sm">
            <thead className="border-b-2 border-gray-200 bg-gray-50 text-left text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
              <tr className="h-[42px]">
                <th className="w-10 px-4 py-2 font-medium">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected && !allSelected
                    }}
                    onChange={toggleSelectAll}
                    aria-label={t('selectAllEntries')}
                  />
                </th>
                <th className="px-4 py-2 font-medium">{t('date')}</th>
                <th className="px-4 py-2 font-medium">{t('project')}</th>
                <th className="px-4 py-2 font-medium">{t('start')}</th>
                <th className="px-4 py-2 font-medium">{t('end')}</th>
                <th className="px-4 py-2 font-medium">{t('duration')}</th>
                <th className="px-4 py-2 font-medium">{t('rounded')}</th>
                <th className="px-4 py-2 font-medium">{t('amount')}</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900">
              {timersQuery.data.items.map((timer, index) => {
                const isRunning = !timer.end_time
                const cellTextClass = isRunning
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-gray-500 dark:text-gray-400'
                return (
                  <tr
                    key={timer.id}
                    className={`h-[38px] odd:bg-white even:bg-gray-50 dark:odd:bg-gray-900 dark:even:bg-gray-800/60 ${
                      index > 0 ? 'border-t border-gray-100 dark:border-gray-800' : ''
                    } ${
                      timer.end_time ? 'cursor-pointer hover:brightness-95 dark:hover:brightness-125' : ''
                    }`}
                    onClick={
                      timer.end_time
                        ? () => {
                            setConfirmingDelete(false)
                            setModalTimer(timer)
                          }
                        : undefined
                    }
                  >
                    <td className="px-4 py-2" onClick={(e) => e.stopPropagation()}>
                      {!isRunning && (
                        <input
                          type="checkbox"
                          checked={selectedIds.has(timer.id)}
                          onChange={() => toggleSelected(timer.id)}
                          aria-label={t('selectEntry')}
                        />
                      )}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {formatDate(new Date(timer.start_time))}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {projectById.get(timer.project_id)?.name ?? '—'}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {formatTime(new Date(timer.start_time), hour12)}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {timer.end_time ? (
                        isSameDay(
                          new Date(timer.start_time),
                          new Date(timer.end_time),
                        ) ? (
                          formatTime(new Date(timer.end_time), hour12)
                        ) : (
                          <DateTimeText iso={timer.end_time} hour12={hour12} />
                        )
                      ) : (
                        <span className="font-medium">{t('running')}</span>
                      )}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {formatDurationClock(timer.duration)}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {projectById.get(timer.project_id)?.round_to_hour && (
                        <span title={t('roundedToHourTitle')}>R</span>
                      )}
                    </td>
                    <td className={`truncate px-4 py-2 ${cellTextClass}`}>
                      {formatAmount(timer.billable_amount)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tbody className="bg-white dark:bg-gray-900">
              {Array.from({
                length: Math.max(
                  0,
                  TIMERS_PAGE_SIZE - timersQuery.data.items.length,
                ),
              }).map((_, i) => (
                <tr
                  key={`filler-${i}`}
                  className="h-[38px] border-t border-gray-100 dark:border-gray-800"
                  aria-hidden="true"
                >
                  <td className="px-4 py-2" colSpan={8}>
                    &nbsp;
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            disabled={page <= 1}
            onClick={() => goToPage(page - 1)}
          >
            {tc('previous')}
          </Button>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {tc('pageOf', { page, total: totalPages })}
          </span>
          <Button
            variant="secondary"
            disabled={page >= totalPages}
            onClick={() => goToPage(page + 1)}
          >
            {tc('next')}
          </Button>
        </div>
      )}

      {modalTimer && (
        <TimerFormModal
          timer={modalTimer === 'new' ? undefined : modalTimer}
          projects={projects}
          onClose={closeModal}
          onSubmit={handleSubmit}
          isSubmitting={activeMutation.isPending}
          error={activeMutation.error}
          onDelete={
            modalTimer === 'new'
              ? undefined
              : () => setConfirmingDelete(true)
          }
          isDeleting={deleteMutation.isPending}
        />
      )}

      {confirmingDelete && modalTimer && modalTimer !== 'new' && (
        <ConfirmDialog
          title={t('deleteTimeEntry')}
          message={t('deleteTimeEntryMessage')}
          confirmLabel={tc('delete')}
          isConfirming={deleteMutation.isPending}
          onConfirm={() => deleteMutation.mutate(modalTimer.id)}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}

      {confirmingBulkDelete && (
        <ConfirmDialog
          title={t('deleteTimeEntries')}
          message={t('deleteTimeEntriesMessage', { count: selectedIds.size })}
          confirmLabel={tc('delete')}
          isConfirming={bulkDeleteMutation.isPending}
          onConfirm={() => bulkDeleteMutation.mutate([...selectedIds])}
          onCancel={() => setConfirmingBulkDelete(false)}
        />
      )}
    </div>
  )
}
