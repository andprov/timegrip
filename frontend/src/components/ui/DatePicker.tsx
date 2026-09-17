import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { usePopoverDismiss } from '@/hooks/usePopoverDismiss'
import { usePopoverPosition } from '@/hooks/usePopoverPosition'
import {
  daysInMonth,
  formatMonthLabel,
  isBeforeDay,
  isFutureDay,
  mondayIndex,
  startOfMonth,
  weekdayLabels,
} from '@/lib/calendar'
import { formatDate, isSameDay } from '@/lib/format'

interface DatePickerProps {
  value: Date | null
  onChange: (date: Date) => void
  disallowFuture?: boolean
  minDate?: Date
}

export function DatePicker({
  value,
  onChange,
  disallowFuture,
  minDate,
}: DatePickerProps) {
  const { t, i18n } = useTranslation('common')
  const [isOpen, setIsOpen] = useState(false)
  const [viewMonth, setViewMonth] = useState(() =>
    startOfMonth(value ?? new Date()),
  )
  const containerRef = useRef<HTMLDivElement>(null)
  const popupRef = useRef<HTMLDivElement>(null)

  const popoverPosition = usePopoverPosition(isOpen, containerRef, popupRef)
  usePopoverDismiss(isOpen, setIsOpen, containerRef)

  function openPicker() {
    setViewMonth(startOfMonth(value ?? new Date()))
    setIsOpen(true)
  }

  function handleSelectDay(day: number) {
    onChange(new Date(viewMonth.getFullYear(), viewMonth.getMonth(), day))
    setIsOpen(false)
  }

  const today = new Date()
  const leadingBlanks = mondayIndex(viewMonth)
  const totalDays = daysInMonth(viewMonth)
  const cells: (number | null)[] = [
    ...Array(leadingBlanks).fill(null),
    ...Array.from({ length: totalDays }, (_, i) => i + 1),
  ]

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => (isOpen ? setIsOpen(false) : openPicker())}
        className="flex w-full items-center rounded-md border-0 px-4 py-3 text-left text-base text-gray-900 outline-none ring-1 ring-inset ring-gray-300 sm:px-3 sm:py-2 sm:text-sm dark:text-gray-100 dark:ring-gray-700"
      >
        {/* An invisible date reserves the field's width up front, so a shorter
            placeholder doesn't shrink it before a date is picked. */}
        <span className="grid">
          <span aria-hidden className="invisible col-start-1 row-start-1">
            {formatDate(today)}
          </span>
          <span
            className={`col-start-1 row-start-1 ${value ? '' : 'text-gray-400 dark:text-gray-500'}`}
          >
            {value ? formatDate(value) : t('selectDate')}
          </span>
        </span>
      </button>

      {isOpen && popoverPosition?.isMobile && (
        <div
          className="fixed inset-0 z-20 bg-black/50"
          onClick={() => setIsOpen(false)}
        />
      )}

      {isOpen && (
        <div
          ref={popupRef}
          style={
            popoverPosition
              ? {
                  position: popoverPosition.position,
                  top: popoverPosition.top,
                  left: popoverPosition.left,
                  transform: popoverPosition.transform,
                }
              : { position: 'fixed' }
          }
          className="z-30 max-h-[calc(100dvh-2rem)] w-72 max-w-[calc(100vw-2rem)] overflow-y-auto rounded-lg bg-white p-3 shadow-xl ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-800"
        >
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              aria-label={t('previousMonth')}
              onClick={() =>
                setViewMonth(
                  (m) => new Date(m.getFullYear(), m.getMonth() - 1, 1),
                )
              }
              className="rounded p-2.5 text-lg text-gray-500 hover:bg-gray-100 sm:p-1 sm:text-base dark:text-gray-400 dark:hover:bg-gray-800"
            >
              ‹
            </button>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatMonthLabel(viewMonth, i18n.language)}
            </span>
            <button
              type="button"
              aria-label={t('nextMonth')}
              onClick={() =>
                setViewMonth(
                  (m) => new Date(m.getFullYear(), m.getMonth() + 1, 1),
                )
              }
              className="rounded p-2.5 text-lg text-gray-500 hover:bg-gray-100 sm:p-1 sm:text-base dark:text-gray-400 dark:hover:bg-gray-800"
            >
              ›
            </button>
          </div>

          <div className="mb-1 grid grid-cols-7 text-center text-xs text-gray-400 dark:text-gray-500">
            {weekdayLabels(i18n.language).map((wd, i) => (
              <span key={i}>{wd}</span>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-y-1 text-center text-sm">
            {cells.map((day, i) => {
              if (day === null) return <span key={`blank-${i}`} />
              const cellDate = new Date(
                viewMonth.getFullYear(),
                viewMonth.getMonth(),
                day,
              )
              const isSelected = value !== null && isSameDay(cellDate, value)
              const isToday = isSameDay(cellDate, today)
              const isDisabled =
                (Boolean(disallowFuture) && isFutureDay(cellDate, today)) ||
                (minDate ? isBeforeDay(cellDate, minDate) : false)
              return (
                <button
                  key={day}
                  type="button"
                  disabled={isDisabled}
                  onClick={() => handleSelectDay(day)}
                  className={`mx-auto flex size-9 items-center justify-center rounded-full text-base sm:size-7 sm:text-sm ${
                    isSelected
                      ? 'bg-indigo-600 text-white'
                      : isDisabled
                        ? 'cursor-not-allowed text-gray-300 dark:text-gray-700'
                        : isToday
                          ? 'text-indigo-600 ring-1 ring-inset ring-indigo-300 dark:text-indigo-400 dark:ring-indigo-800'
                          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                  }`}
                >
                  {day}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
