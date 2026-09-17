import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { createProject, deleteProject, updateProject } from '@/api/projects'
import type { Project } from '@/api/types'
import { useAllProjects } from '@/hooks/useAllProjects'
import { useRunningTimer } from '@/hooks/useRunningTimer'
import type { ProjectFormValues } from '@/components/ProjectFormModal'
import { ProjectFormModal } from '@/components/ProjectFormModal'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import { formatAmount } from '@/lib/format'
import { PROJECTS_PAGE_SIZE } from '@/lib/pagination'
import { compareNames } from '@/lib/sort'

function toApiPayload(values: ProjectFormValues) {
  const rate = values.hourly_rate.trim()
  return {
    name: values.name,
    color: values.color,
    hourly_rate: rate === '' || Number(rate) === 0 ? null : rate,
    round_to_hour: values.round_to_hour,
  }
}

export function ProjectsPage() {
  const { t } = useTranslation('projects')
  const { t: tc } = useTranslation('common')
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [projectFilter, setProjectFilter] = useState('')
  const [billableFilter, setBillableFilter] = useState<'' | 'true' | 'false'>('')
  const [statusFilter, setStatusFilter] = useState<'' | 'active' | 'archived'>(
    'active',
  )
  const [modalProject, setModalProject] = useState<Project | 'new' | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteBlocked, setDeleteBlocked] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  const projectsQuery = useAllProjects()
  const runningTimerQuery = useRunningTimer()
  const runningProjectId = runningTimerQuery.data?.project_id ?? null
  const isModalProjectTimerRunning =
    modalProject !== null &&
    modalProject !== 'new' &&
    modalProject.id === runningProjectId
  const allProjects = [...(projectsQuery.data?.items ?? [])].sort((a, b) =>
    compareNames(a.name, b.name),
  )
  const selectedProject = allProjects.find((p) => p.id === projectFilter)
  const statusFilteredProjects = allProjects.filter((project) => {
    if (statusFilter === 'active') return project.status === 'active'
    if (statusFilter === 'archived') return project.status === 'archived'
    return true
  })
  const billableFilteredProjects = statusFilteredProjects.filter((project) => {
    if (billableFilter === 'true') return project.hourly_rate !== null
    if (billableFilter === 'false') return project.hourly_rate === null
    return true
  })
  const filteredProjects = billableFilteredProjects.filter(
    (project) => !projectFilter || project.id === projectFilter,
  )
  // The currently selected project must stay listed in the project filter
  // even if it no longer matches the billing/status filters (e.g. it was
  // just edited) — otherwise the select goes blank instead of showing it.
  const projectOptions = [
    { value: '', label: t('allProjects') },
    ...billableFilteredProjects.map((project) => ({
      value: project.id,
      label: project.name,
      color: project.color,
    })),
    ...(selectedProject && !billableFilteredProjects.includes(selectedProject)
      ? [{ value: selectedProject.id, label: selectedProject.name, color: selectedProject.color }]
      : []),
  ]

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setModalProject(null)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Parameters<typeof updateProject>[1]) =>
      updateProject(id, data),
    onSuccess: (updatedProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setModalProject(null)
      const stillMatchesBillable =
        billableFilter === '' ||
        (billableFilter === 'true') === (updatedProject.hourly_rate !== null)
      const stillMatchesStatus = statusFilter === '' || statusFilter === updatedProject.status
      if (!stillMatchesBillable || !stillMatchesStatus) {
        setNotice(t('filterMatchNotice', { name: updatedProject.name }))
      }
    },
  })

  useEffect(() => {
    if (!notice) return
    const timer = setTimeout(() => setNotice(null), 5000)
    return () => clearTimeout(timer)
  }, [notice])

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setModalProject(null)
    },
    onError: () => {
      // The running timer cache may be stale (e.g. a timer was started on
      // another device): close the confirmation so the error shows in the
      // project modal, and refresh the timer so Delete gets blocked.
      setConfirmingDelete(false)
      queryClient.invalidateQueries({ queryKey: ['timers', 'running'] })
    },
  })

  function handleSubmit(values: ProjectFormValues) {
    if (modalProject === 'new' || modalProject === null) {
      createMutation.mutate(toApiPayload(values))
    } else {
      updateMutation.mutate({
        id: modalProject.id,
        ...toApiPayload(values),
        status: values.status,
      })
    }
  }

  const activeMutation = modalProject === 'new' ? createMutation : updateMutation

  function closeModal() {
    createMutation.reset()
    updateMutation.reset()
    deleteMutation.reset()
    setDeleteBlocked(false)
    setModalProject(null)
  }

  const totalPages = Math.max(
    1,
    Math.ceil(filteredProjects.length / PROJECTS_PAGE_SIZE),
  )
  const pagedProjects = filteredProjects.slice(
    (page - 1) * PROJECTS_PAGE_SIZE,
    page * PROJECTS_PAGE_SIZE,
  )

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
        <h1 className="flex min-h-9 items-center text-2xl font-semibold text-gray-900 dark:text-gray-100">
          {t('title')}
        </h1>
        <Button
          className="w-full sm:w-40"
          onClick={() => {
            setConfirmingDelete(false)
            setDeleteBlocked(false)
            setModalProject('new')
          }}
        >
          {t('newProject')}
        </Button>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 sm:flex sm:flex-wrap">
        <Select
          searchable
          className="w-full sm:w-40"
          value={projectFilter}
          onChange={(v) => {
            setProjectFilter(v)
            setPage(1)
          }}
          options={projectOptions}
        />
        <Select
          className="w-full sm:w-40"
          value={billableFilter}
          onChange={(v) => {
            setBillableFilter(v as '' | 'true' | 'false')
            setPage(1)
          }}
          options={[
            { value: '', label: t('allBilling') },
            { value: 'true', label: t('billable') },
            { value: 'false', label: t('nonBillable') },
          ]}
        />
        <Select
          className="w-full sm:w-40"
          value={statusFilter}
          onChange={(v) => {
            setStatusFilter(v as '' | 'active' | 'archived')
            setPage(1)
          }}
          options={[
            { value: '', label: t('allStatuses') },
            { value: 'active', label: t('active') },
            { value: 'archived', label: t('archived') },
          ]}
        />
      </div>

      {projectsQuery.isPending && (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      )}

      {projectsQuery.isError && <Alert>{t('loadFailed')}</Alert>}

      {notice && (
        <div className="mb-4">
          <Alert variant="info">{notice}</Alert>
        </div>
      )}

      {projectsQuery.data && allProjects.length === 0 && (
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('noProjectsYet')}
          </p>
        </Card>
      )}

      {projectsQuery.data && allProjects.length > 0 && filteredProjects.length === 0 && (
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">{t('noProjectsMatch')}</p>
        </Card>
      )}

      {pagedProjects.length > 0 && (
        <div className="grid min-h-[612px] gap-3">
          {pagedProjects.map((project) => (
            <Card
              key={project.id}
              className="flex items-center gap-3"
              onClick={() => {
                setConfirmingDelete(false)
                setDeleteBlocked(false)
                setModalProject(project)
              }}
            >
              <span
                className="size-4 rounded-full"
                style={{ backgroundColor: project.color }}
              />
              <div className="min-w-0 break-words">
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {project.name}
                  {statusFilter === '' && project.status === 'archived' && (
                    <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-normal text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                      {t('archived')}
                    </span>
                  )}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {project.hourly_rate === null
                    ? t('nonBillable')
                    : t('perHour', { amount: formatAmount(project.hourly_rate) })}
                  {project.round_to_hour && t('roundedToHour')}
                </p>
              </div>
              {project.hourly_rate !== null && (
                <span className="ml-auto shrink-0 text-lg font-medium text-gray-900 dark:text-gray-100">
                  $
                </span>
              )}
            </Card>
          ))}
          {Array.from({
            length: Math.max(0, PROJECTS_PAGE_SIZE - pagedProjects.length),
          }).map((_, i) => (
            <Card key={`filler-${i}`} className="invisible flex items-center gap-3">
              <span className="size-4 rounded-full" />
              <div>
                <p className="font-medium">Placeholder</p>
                <p className="text-sm">Placeholder</p>
              </div>
            </Card>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            {tc('previous')}
          </Button>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {tc('pageOf', { page, total: totalPages })}
          </span>
          <Button
            variant="secondary"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            {tc('next')}
          </Button>
        </div>
      )}

      {modalProject && (
        <ProjectFormModal
          project={modalProject === 'new' ? undefined : modalProject}
          onClose={closeModal}
          onSubmit={handleSubmit}
          isSubmitting={activeMutation.isPending}
          error={activeMutation.error ?? deleteMutation.error}
          onDelete={
            modalProject === 'new'
              ? undefined
              : () => {
                  deleteMutation.reset()
                  if (isModalProjectTimerRunning) {
                    setDeleteBlocked(true)
                    return
                  }
                  setDeleteBlocked(false)
                  setConfirmingDelete(true)
                }
          }
          isDeleting={deleteMutation.isPending}
          deleteNotice={
            deleteBlocked && isModalProjectTimerRunning
              ? t('deleteBlockedByRunningTimer')
              : undefined
          }
        />
      )}

      {confirmingDelete && modalProject && modalProject !== 'new' && (
        <ConfirmDialog
          title={t('deleteProject')}
          message={t('deleteProjectMessage', { name: modalProject.name })}
          confirmLabel={tc('delete')}
          isConfirming={deleteMutation.isPending}
          onConfirm={() => deleteMutation.mutate(modalProject.id)}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </div>
  )
}
