import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '@/api/client'
import type { Project, ProjectStatus } from '@/api/types'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { ColorSwatchPicker } from '@/components/ColorSwatchPicker'

export interface ProjectFormValues {
  name: string
  color: string
  hourly_rate: string
  round_to_hour: boolean
  status: ProjectStatus
}

export function ProjectFormModal({
  project,
  onClose,
  onSubmit,
  isSubmitting,
  error,
  onDelete,
  isDeleting,
  deleteNotice,
}: {
  project?: Project
  onClose: () => void
  onSubmit: (values: ProjectFormValues) => void
  isSubmitting: boolean
  error: unknown
  onDelete?: () => void
  isDeleting?: boolean
  deleteNotice?: string
}) {
  const { t } = useTranslation('projects')
  const { t: tc } = useTranslation('common')
  const [name, setName] = useState(project?.name ?? '')
  const [color, setColor] = useState(project?.color ?? '#9E9E9E')
  const [hourlyRate, setHourlyRate] = useState(project?.hourly_rate ?? '')
  const [roundToHour, setRoundToHour] = useState(project?.round_to_hour ?? false)
  const [status, setStatus] = useState<ProjectStatus>(project?.status ?? 'active')
  const hasRate = hourlyRate.trim() !== '' && Number(hourlyRate) !== 0

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    onSubmit({
      name,
      color,
      hourly_rate: hourlyRate,
      round_to_hour: roundToHour,
      status,
    })
  }

  return (
    <Modal
      title={project ? t('editProject') : t('newProject')}
      fullScreenOnMobile
      showCloseButton={false}
      onClose={onClose}
    >
      <form
        className="flex flex-1 flex-col gap-4 sm:flex-none"
        onSubmit={handleSubmit}
      >
        <Input
          label={t('name')}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('color')}</span>
          <ColorSwatchPicker value={color} onChange={setColor} />
        </div>
        <Input
          label={t('hourlyRate')}
          type="number"
          step="0.01"
          min="0"
          max="99999999.99"
          placeholder={t('hourlyRatePlaceholder')}
          value={hourlyRate}
          onChange={(e) => {
            const next = e.target.value
            setHourlyRate(next)
            if (next.trim() === '' || Number(next) === 0) setRoundToHour(false)
          }}
        />
        <label
          className={`flex items-center gap-2 text-sm ${hasRate ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400 dark:text-gray-600'}`}
        >
          <input
            type="checkbox"
            checked={roundToHour}
            disabled={!hasRate}
            onChange={(e) => setRoundToHour(e.target.checked)}
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-600 disabled:cursor-not-allowed dark:border-gray-600"
          />
          {t('roundToHourLabel')}
        </label>
        {project && (
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('status')}</span>
            <Select
              value={status}
              onChange={(v) => setStatus(v as ProjectStatus)}
              options={[
                { value: 'active', label: t('active') },
                { value: 'archived', label: t('archived') },
              ]}
            />
          </div>
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
            {project ? t('save') : t('create')}
          </Button>
        </div>
        {onDelete && (
          <div className="mt-auto flex flex-col gap-2 sm:mt-0">
            <Button
              type="button"
              variant="danger"
              disabled={isDeleting}
              onClick={onDelete}
              className="w-full"
            >
              {tc('delete')}
            </Button>
            {deleteNotice !== undefined && <Alert>{deleteNotice}</Alert>}
          </div>
        )}
      </form>
    </Modal>
  )
}
