import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent as ReactKeyboardEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { usePopoverDismiss } from '@/hooks/usePopoverDismiss'
import { ChevronDown } from '@/components/ui/ChevronDown'

export interface SelectOption {
  value: string
  label: string
  color?: string
}

interface SelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  className?: string
  searchable?: boolean
  placeholder?: string
}

function Dot({ color }: { color: string }) {
  return (
    <span
      className="size-3 shrink-0 rounded-full"
      style={{ backgroundColor: color }}
    />
  )
}

export function Select({
  value,
  onChange,
  options,
  className = '',
  searchable = false,
  placeholder,
}: SelectProps) {
  const { t } = useTranslation('common')
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  usePopoverDismiss(isOpen, setIsOpen, containerRef)

  useEffect(() => {
    if (!isOpen || !searchable) return
    const el = listRef.current?.querySelector<HTMLButtonElement>(
      `[data-index="${activeIndex}"]`,
    )
    el?.scrollIntoView({ block: 'nearest' })
  }, [activeIndex, isOpen, searchable])

  const selectedOption = options.find((o) => o.value === value)
  const hasColors = options.some((o) => o.color !== undefined)
  const filteredOptions = searchable
    ? options.filter((o) =>
        o.label.toLowerCase().includes(query.trim().toLowerCase()),
      )
    : options

  function selectOption(option: SelectOption) {
    onChange(option.value)
    setIsOpen(false)
    setQuery('')
  }

  function handleInputKeyDown(e: ReactKeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!isOpen) {
        setIsOpen(true)
        return
      }
      setActiveIndex((i) => Math.min(i + 1, filteredOptions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (!isOpen) {
        setIsOpen(true)
        return
      }
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const option = filteredOptions[activeIndex] ?? filteredOptions[0]
      if (option) selectOption(option)
    }
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {searchable ? (
        <div className="relative">
          {hasColors && selectedOption?.color && !isOpen && (
            <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center">
              <Dot color={selectedOption.color} />
            </span>
          )}
          <input
            type="text"
            value={isOpen ? query : (selectedOption?.label ?? '')}
            onChange={(e) => {
              setQuery(e.target.value)
              setActiveIndex(0)
              setIsOpen(true)
            }}
            onFocus={() => {
              setQuery('')
              setActiveIndex(0)
              setIsOpen(true)
            }}
            onKeyDown={handleInputKeyDown}
            placeholder={placeholder}
            className={`w-full rounded-md border-0 py-3 pr-8 text-base text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:py-2 sm:text-sm dark:text-gray-100 dark:ring-gray-700 dark:placeholder:text-gray-500 ${
              hasColors && selectedOption?.color && !isOpen ? 'pl-8' : 'pl-3'
            }`}
          />
          <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
            <ChevronDown />
          </span>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setIsOpen((o) => !o)}
          className="flex w-full items-center justify-between gap-2 rounded-md border-0 px-4 py-3 text-left text-sm text-gray-900 outline-none ring-1 ring-inset ring-gray-300 sm:px-3 sm:py-2 dark:text-gray-100 dark:ring-gray-700"
        >
          <span className="flex min-w-0 items-center gap-2">
            {selectedOption?.color && <Dot color={selectedOption.color} />}
            <span className="truncate">{selectedOption?.label}</span>
          </span>
          <span className="shrink-0">
            <ChevronDown />
          </span>
        </button>
      )}

      {isOpen && (
        <div
          ref={listRef}
          className="absolute z-20 mt-1 w-full min-w-max max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg bg-white shadow-xl ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-800"
        >
          <div className="max-h-64 overflow-y-auto p-1 sm:max-h-80">
            {filteredOptions.length === 0 ? (
              <p className="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400">{t('noMatches')}</p>
            ) : (
              filteredOptions.map((option, index) => {
                const isSelected = option.value === value
                const isActive = searchable && index === activeIndex
                return (
                  <button
                    key={option.value}
                    type="button"
                    data-index={index}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => selectOption(option)}
                    className={`flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-left text-base sm:py-1.5 sm:text-sm ${
                      isSelected
                        ? 'bg-indigo-600 text-white'
                        : isActive
                          ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
                          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    }`}
                  >
                    {option.color && <Dot color={option.color} />}
                    <span className="truncate">{option.label}</span>
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
