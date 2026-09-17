import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { startTimer, stopTimer } from '@/api/timers'
import { useAuth } from '@/auth/useAuth'
import { StartTimerModal } from '@/components/StartTimerModal'
import { useAllProjects } from '@/hooks/useAllProjects'
import { useRunningTimer } from '@/hooks/useRunningTimer'
import { useTicker } from '@/hooks/useTicker'
import { formatElapsed } from '@/lib/format'
import { compareNames } from '@/lib/sort'

export function RunningTimerBar() {
  const { t } = useTranslation('common')
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const isActive = Boolean(user?.is_active)
  const [showStartModal, setShowStartModal] = useState(false)

  const runningQuery = useRunningTimer(isActive)
  const projectsQuery = useAllProjects(isActive)
  const running = runningQuery.data
  const now = useTicker(Boolean(running))

  const stopMutation = useMutation({
    mutationFn: stopTimer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timers'] })
    },
  })

  const startMutation = useMutation({
    mutationFn: startTimer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timers'] })
      setShowStartModal(false)
    },
  })

  if (!isActive) return null

  const projects = [...(projectsQuery.data?.items ?? [])].sort((a, b) =>
    compareNames(a.name, b.name),
  )
  const activeProjects = projects.filter((p) => p.status === 'active')

  if (running) {
    return (
      <div className="flex h-11 items-center gap-2 sm:h-9 sm:gap-3">
        <span className="text-lg leading-none font-bold text-red-700 tabular-nums dark:text-red-400">
          {formatElapsed(running.start_time, now)}
        </span>
        <button
          type="button"
          onClick={() => stopMutation.mutate()}
          disabled={stopMutation.isPending}
          className="flex h-11 min-w-20 items-center justify-center rounded-md bg-red-600 px-3 text-base font-medium text-white hover:bg-red-500 disabled:bg-red-300 sm:h-9 sm:min-w-28 sm:text-sm dark:disabled:bg-red-900"
        >
          {t('stop')}
        </button>
      </div>
    )
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setShowStartModal(true)}
        disabled={activeProjects.length === 0}
        className="flex h-11 min-w-20 items-center justify-center rounded-md bg-indigo-600 px-3 text-base font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-300 sm:h-9 sm:min-w-28 sm:text-sm dark:disabled:bg-indigo-900"
      >
        {t('startTimer')}
      </button>
      {showStartModal && (
        <StartTimerModal
          projects={activeProjects}
          onClose={() => setShowStartModal(false)}
          onSelect={(projectId) => startMutation.mutate(projectId)}
          isSubmitting={startMutation.isPending}
        />
      )}
    </>
  )
}
