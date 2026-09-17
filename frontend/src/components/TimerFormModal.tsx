import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '@/api/client'
import type { Project, Timer } from '@/api/types'
import { useTimeFormat } from '@/hooks/useTimeFormat'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { DatePicker } from '@/components/ui/DatePicker'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { TimePicker } from '@/components/ui/TimePicker'
import { formatDurationBetween } from '@/lib/format'

export interface TimerFormValues {
  project_id: string
  start_time: string
  end_time: string
}

interface TimeValue {
  hours: number
  minutes: number | null
}

function datePartOf(iso: string | null | undefined): Date | null {
  return iso ? new Date(iso) : null
}

function timePartOf(iso: string | null | undefined): TimeValue | null {
  if (!iso) return null
  const d = new Date(iso)
  return { hours: d.getHours(), minutes: d.getMinutes() }
}

function combine(datePart: Date | null, timePart: TimeValue | null): string {
  if (!datePart || !timePart || timePart.minutes === null) return ''
  const { hours, minutes } = timePart
  const combined = new Date(datePart)
  combined.setHours(hours, minutes, 0, 0)
  return combined.toISOString()
}

export function TimerFormModal({
  timer,
  projects,
  onClose,
  onSubmit,
  isSubmitting,
  error,
  onDelete,
  isDeleting,
}: {
  timer?: Timer
  projects: Project[]
  onClose: () => void
  onSubmit: (values: TimerFormValues) => void
  isSubmitting: boolean
  error: unknown
  onDelete?: () => void
  isDeleting?: boolean
}) {
  const { t } = useTranslation('timers')
  const { t: tc } = useTranslation('common')
  const { hour12 } = useTimeFormat()
  const [projectId, setProjectId] = useState(timer?.project_id ?? '')
  const [startDate, setStartDate] = useState(() => datePartOf(timer?.start_time))
  const [startTimeValue, setStartTimeValue] = useState(() =>
    timePartOf(timer?.start_time),
  )
  const [endDate, setEndDate] = useState(() => datePartOf(timer?.end_time))
  const [endTimeValue, setEndTimeValue] = useState(() =>
    timePartOf(timer?.end_time),
  )
  const [showValidation, setShowValidation] = useState(false)

  const startTime = combine(startDate, startTimeValue)
  const endTime = combine(endDate, endTimeValue)
  const isValid = Boolean(projectId && startTime && endTime)
  const startDateTime = startTime ? new Date(startTime) : undefined
  const selectableProjects = projects.filter(
    (project) => project.status === 'active' || project.id === timer?.project_id,
  )

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isValid) {
      setShowValidation(true)
      return
    }
    // The pickers only resolve to minute precision, so an end time equal to
    // the start time is a valid "1 minute apart" choice from the user's
    // point of view — nudge it a second later so the backend's strict
    // end > start check doesn't reject it.
    const submittedEndTime =
      endTime === startTime
        ? new Date(new Date(endTime).getTime() + 1000).toISOString()
        : endTime
    onSubmit({
      project_id: projectId,
      start_time: startTime,
      end_time: submittedEndTime,
    })
  }

  return (
    <Modal
      title={timer ? t('editTimeEntry') : t('addTimeEntry')}
      fullScreenOnMobile
      showCloseButton={false}
      onClose={onClose}
    >
      <form
        className="flex flex-1 flex-col gap-4 sm:flex-none"
        onSubmit={handleSubmit}
      >
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('project')}</span>
          <Select
            searchable
            placeholder={t('selectProject')}
            value={projectId}
            onChange={setProjectId}
            options={selectableProjects.map((project) => ({
              value: project.id,
              label: project.name,
              color: project.color,
            }))}
          />
        </div>
        {showValidation && !projectId && (
          <p className="-mt-3 text-sm text-red-600 dark:text-red-400">{t('projectRequired')}</p>
        )}
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('startTime')}</span>
          <div className="flex gap-2">
            <DatePicker value={startDate} onChange={setStartDate} disallowFuture />
            <TimePicker
              date={startDate}
              time={startTimeValue}
              onChange={(hours, minutes) => {
                setStartTimeValue({ hours, minutes })
                setStartDate((prev) => prev ?? new Date())
              }}
              hour12={hour12}
            />
          </div>
        </div>
        {showValidation && !startTime && (
          <p className="-mt-3 text-sm text-red-600 dark:text-red-400">{t('startTimeRequired')}</p>
        )}
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('endTime')}</span>
          <div className="flex gap-2">
            <DatePicker
              value={endDate}
              onChange={setEndDate}
              disallowFuture
              minDate={startDate ?? undefined}
            />
            <TimePicker
              date={endDate}
              time={endTimeValue}
              onChange={(hours, minutes) => {
                setEndTimeValue({ hours, minutes })
                setEndDate((prev) => prev ?? new Date())
              }}
              hour12={hour12}
              minTime={startDateTime}
            />
          </div>
        </div>
        {showValidation && !endTime && (
          <p className="-mt-3 text-sm text-red-600 dark:text-red-400">{t('endTimeRequired')}</p>
        )}
        {startTime && endTime && endTime > startTime && (
          <p className="-mt-2 text-sm text-gray-500 dark:text-gray-400">
            {t('total', {
              duration: formatDurationBetween(startTime, endTime, {
                hour: tc('hourShort'),
                minute: tc('minuteShort'),
              }),
            })}
          </p>
        )}
        {error !== undefined && error !== null && (
          <Alert>
            {error instanceof ApiError ? error.message : tc('somethingWentWrong')}
          </Alert>
        )}
        <div className="grid grid-cols-2 gap-3">
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            onClick={onClose}
          >
            {tc('cancel')}
          </Button>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {timer ? t('save') : t('add')}
          </Button>
        </div>
        {onDelete && (
          <Button
            type="button"
            variant="danger"
            disabled={isDeleting}
            onClick={onDelete}
            className="mt-auto w-full sm:mt-0"
          >
            {tc('delete')}
          </Button>
        )}
      </form>
    </Modal>
  )
}
