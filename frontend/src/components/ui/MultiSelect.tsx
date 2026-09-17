import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { usePopoverDismiss } from '@/hooks/usePopoverDismiss'
import { ChevronDown } from '@/components/ui/ChevronDown'

export interface MultiSelectOption {
  value: string
  label: string
  color?: string
}

interface MultiSelectProps {
  values: string[]
  onChange: (values: string[]) => void
  options: MultiSelectOption[]
  className?: string
  placeholder?: string
  searchable?: boolean
  /** Fixed trigger text, shown instead of a selection summary. */
  title?: string
  /** Stage changes locally and only commit them via an "Apply" button. */
  applyButton?: boolean
  /** Show the "Select all" quick action. */
  showSelectAll?: boolean
  /** Show the "Clear" quick action. */
  showClear?: boolean
  /** Minimum number of selected options required to apply. */
  minSelected?: number
  /** Prefix for the multi-selected summary, e.g. "Project" -> "Project: 3". Falls back to "N selected". */
  countLabel?: string
}

function Dot({ color }: { color: string }) {
  return (
    <span
      className="size-3 shrink-0 rounded-full"
      style={{ backgroundColor: color }}
    />
  )
}

export function MultiSelect({
  values,
  onChange,
  options,
  className = '',
  placeholder,
  searchable = false,
  title,
  applyButton = false,
  showSelectAll = true,
  showClear = true,
  minSelected = 0,
  countLabel,
}: MultiSelectProps) {
  const { t } = useTranslation('common')
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [draftValues, setDraftValues] = useState(values)
  const containerRef = useRef<HTMLDivElement>(null)

  const activeValues = applyButton ? draftValues : values

  usePopoverDismiss(isOpen, setIsOpen, containerRef)

  function openDropdown() {
    if (applyButton) setDraftValues(values)
    setIsOpen(true)
  }

  function setActiveValues(next: string[]) {
    if (applyButton) setDraftValues(next)
    else onChange(next)
  }

  function toggleValue(value: string) {
    if (activeValues.includes(value)) {
      setActiveValues(activeValues.filter((v) => v !== value))
    } else {
      setActiveValues([...activeValues, value])
    }
  }

  function handleApply() {
    if (draftValues.length < minSelected) return
    onChange(draftValues)
    setIsOpen(false)
  }

  const selectedOptions = options.filter((o) => values.includes(o.value))
  const triggerLabel =
    title ??
    (selectedOptions.length === 0
      ? (placeholder ?? t('all'))
      : selectedOptions.length === 1
        ? selectedOptions[0].label
        : countLabel
          ? `${countLabel}: ${selectedOptions.length}`
          : t('nSelected', { count: selectedOptions.length }))

  const filteredOptions =
    searchable && query.trim()
      ? options.filter((o) =>
          o.label.toLowerCase().includes(query.trim().toLowerCase()),
        )
      : options

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => (isOpen ? setIsOpen(false) : openDropdown())}
        className="flex w-full items-center justify-between gap-2 rounded-md border-0 px-4 py-3 text-left text-sm text-gray-900 outline-none ring-1 ring-inset ring-gray-300 sm:px-3 sm:py-2 dark:text-gray-100 dark:ring-gray-700"
      >
        <span className="truncate">{triggerLabel}</span>
        <span className="shrink-0">
          <ChevronDown />
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-1 w-full min-w-max max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg bg-white shadow-xl ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-800">
          <div className="max-h-64 overflow-y-auto p-1">
            {searchable && (
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t('search')}
                className="mb-1 w-full rounded-md border-0 px-3 py-2.5 text-base text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:py-1.5 sm:text-sm dark:text-gray-100 dark:ring-gray-700 dark:placeholder:text-gray-500"
              />
            )}
            {(showSelectAll || showClear) && options.length > 0 && (
              <div className="flex items-center justify-between gap-2 border-b border-gray-100 px-2 py-1 dark:border-gray-800">
                {showSelectAll && (
                  <button
                    type="button"
                    onClick={() => setActiveValues(options.map((o) => o.value))}
                    className="rounded px-1 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-800 sm:py-1 sm:text-xs dark:text-indigo-400 dark:hover:text-indigo-300"
                  >
                    {t('selectAll')}
                  </button>
                )}
                {showClear && (
                  <button
                    type="button"
                    onClick={() => setActiveValues([])}
                    className="rounded px-1 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 sm:py-1 sm:text-xs dark:text-gray-400 dark:hover:text-gray-300"
                  >
                    {t('clear')}
                  </button>
                )}
              </div>
            )}
            {filteredOptions.length === 0 ? (
              <p className="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400">{t('noMatches')}</p>
            ) : (
              filteredOptions.map((option) => {
                const isChecked = activeValues.includes(option.value)
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => toggleValue(option.value)}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-left text-base text-gray-700 hover:bg-gray-100 sm:py-1.5 sm:text-sm dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      readOnly
                      className="pointer-events-none"
                    />
                    {option.color && <Dot color={option.color} />}
                    <span className="truncate">{option.label}</span>
                  </button>
                )
              })
            )}
          </div>
          {applyButton && (
            <div className="border-t border-gray-100 p-1 dark:border-gray-800">
              <button
                type="button"
                onClick={handleApply}
                disabled={draftValues.length < minSelected}
                className="w-full rounded-md bg-indigo-600 px-3 py-2.5 text-center text-base font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-300 sm:py-1.5 sm:text-sm dark:disabled:bg-indigo-900"
              >
                {t('apply')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
