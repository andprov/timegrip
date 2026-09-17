import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent as ReactKeyboardEvent } from 'react'
import { useTranslation } from 'react-i18next'

import type { Project } from '@/api/types'
import { Modal } from '@/components/ui/Modal'

export function StartTimerModal({
  projects,
  onClose,
  onSelect,
  isSubmitting,
}: {
  projects: Project[]
  onClose: () => void
  onSelect: (projectId: string) => void
  isSubmitting: boolean
}) {
  const { t } = useTranslation('timers')
  const { t: tc } = useTranslation('common')
  const [search, setSearch] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const listRef = useRef<HTMLUListElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(search.trim().toLowerCase()),
  )

  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLButtonElement>(
      `[data-index="${activeIndex}"]`,
    )
    el?.scrollIntoView({ block: 'nearest' })
  }, [activeIndex])

  useEffect(() => {
    // Autofocus only on devices with a mouse: on touch devices it pops the
    // keyboard the instant the modal mounts, which races Android's address
    // bar animation and leaves it overlapping the modal.
    if (window.matchMedia('(pointer: fine)').matches) {
      searchRef.current?.focus()
    }
  }, [])

  function handleSearchKeyDown(e: ReactKeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, filteredProjects.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const project = filteredProjects[activeIndex]
      if (project && !isSubmitting) onSelect(project.id)
    }
  }

  return (
    <Modal title={tc('startTimer')} onClose={onClose} fullScreenOnMobile>
      {projects.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('noProjectsYetShort')}
        </p>
      ) : (
        <>
          <input
            ref={searchRef}
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setActiveIndex(0)
            }}
            onKeyDown={handleSearchKeyDown}
            placeholder={t('searchProjects')}
            className="mb-3 w-full rounded-md border-0 px-3 py-3 text-base text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:py-2 sm:text-sm dark:text-gray-100 dark:ring-gray-700 dark:placeholder:text-gray-500"
          />
          {filteredProjects.length === 0 ? (
            <p className="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400">
              {t('noProjectsMatchSearch')}
            </p>
          ) : (
            <ul
              ref={listRef}
              className="flex min-h-0 flex-1 flex-col overflow-y-auto rounded-lg p-1 ring-1 ring-gray-200 sm:flex-none sm:max-h-80 dark:ring-gray-800"
            >
              {filteredProjects.map((project, index) => (
                <li key={project.id}>
                  <button
                    type="button"
                    data-index={index}
                    disabled={isSubmitting}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => onSelect(project.id)}
                    className={`flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-left text-base disabled:cursor-not-allowed disabled:opacity-50 sm:py-1.5 sm:text-sm ${
                      index === activeIndex
                        ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
                        : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    }`}
                  >
                    <span
                      className="size-3 shrink-0 rounded-full"
                      style={{ backgroundColor: project.color }}
                    />
                    <span className="truncate">{project.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </Modal>
  )
}
