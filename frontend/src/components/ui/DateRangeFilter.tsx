import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { usePopoverDismiss } from '@/hooks/usePopoverDismiss'
import { usePopoverPosition } from '@/hooks/usePopoverPosition'
import {
  daysInMonth,
  formatMonthLabel,
  mondayIndex,
  startOfMonth,
  toIsoEndOfDay,
  toIsoStartOfDay,
  weekdayLabels,
} from '@/lib/calendar'
import { DATE_RANGE_PRESETS } from '@/lib/dateRangePresets'
import type { DateRangePreset } from '@/lib/dateRangePresets'
import { formatDate, isSameDay } from '@/lib/format'

interface DateRangeFilterProps {
  from: string
  to: string
  onChange: (from: string, to: string) => void
  className?: string
}

export function DateRangeFilter({
  from,
  to,
  onChange,
  className = '',
}: DateRangeFilterProps) {
  const { t, i18n } = useTranslation('common')
  const [isOpen, setIsOpen] = useState(false)
  const fromDate = from ? new Date(from) : null
  const toDate = to ? new Date(to) : null
  // First click of a new range is staged here and only committed via
  // onChange (which drives the actual query) once a second day completes
  // the range — a single click must never fetch with a one-sided range.
  const [pendingFrom, setPendingFrom] = useState<Date | null>(null)
  const [viewMonth, setViewMonth] = useState(() =>
    startOfMonth(fromDate ?? new Date()),
  )
  const containerRef = useRef<HTMLDivElement>(null)
  const popupRef = useRef<HTMLDivElement>(null)

  const popoverPosition = usePopoverPosition(isOpen, containerRef, popupRef)
  usePopoverDismiss(isOpen, setIsOpen, containerRef)

  function openPicker() {
    setPendingFrom(null)
    setViewMonth(startOfMonth(fromDate ?? new Date()))
    setIsOpen(true)
  }

  function applyPreset(preset: DateRangePreset) {
    const range = preset.range()
    onChange(toIsoStartOfDay(range.from), toIsoEndOfDay(range.to))
    setPendingFrom(null)
    setIsOpen(false)
  }

  function isPresetActive(preset: DateRangePreset): boolean {
    if (!fromDate || !toDate) return false
    const range = preset.range()
    return isSameDay(fromDate, range.from) && isSameDay(toDate, range.to)
  }

  function handleSelectDay(day: Date) {
    if (!pendingFrom) {
      // First click of a range: stage it, don't fetch yet.
      setPendingFrom(day)
      return
    }
    if (day.getTime() < pendingFrom.getTime()) {
      // Picked an earlier day than the start: it becomes the new start.
      onChange(toIsoStartOfDay(day), toIsoEndOfDay(pendingFrom))
    } else {
      onChange(toIsoStartOfDay(pendingFrom), toIsoEndOfDay(day))
    }
    setPendingFrom(null)
    setIsOpen(false)
  }

  // While a range is mid-selection, the calendar reflects only the staged
  // first click — the previously committed range stays untouched until a
  // second day is picked.
  const displayFromDate = pendingFrom ?? fromDate
  const displayToDate = pendingFrom ? null : toDate

  const leadingBlanks = mondayIndex(viewMonth)
  const totalDays = daysInMonth(viewMonth)
  const cells: (number | null)[] = [
    ...Array(leadingBlanks).fill(null),
    ...Array.from({ length: totalDays }, (_, i) => i + 1),
  ]

  const activePreset = DATE_RANGE_PRESETS.find((preset) =>
    isPresetActive(preset),
  )

  const label = activePreset
    ? t(`presets.${activePreset.id}`)
    : fromDate && toDate
      ? `${formatDate(fromDate)} - ${formatDate(toDate)}`
      : fromDate
        ? t('dateFrom', { date: formatDate(fromDate) })
        : toDate
          ? t('dateTo', { date: formatDate(toDate) })
          : t('allDates')

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => (isOpen ? setIsOpen(false) : openPicker())}
        className="flex w-full min-w-0 items-center justify-between gap-2 rounded-md border-0 px-4 py-3 text-left text-sm text-gray-900 outline-none ring-1 ring-inset ring-gray-300 sm:px-3 sm:py-2 dark:text-gray-100 dark:ring-gray-700"
      >
        <span className={`min-w-0 truncate ${fromDate || toDate ? '' : 'text-gray-400 dark:text-gray-500'}`}>
          {label}
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
          className="z-30 flex max-h-[calc(100dvh-2rem)] w-72 max-w-[calc(100vw-2rem)] flex-col gap-3 overflow-y-auto rounded-lg bg-white p-3 shadow-xl ring-1 ring-gray-200 sm:w-auto sm:flex-row dark:bg-gray-900 dark:ring-gray-800"
        >
          <div className="grid shrink-0 grid-cols-2 gap-1.5 border-b border-gray-100 pb-3 sm:flex sm:w-32 sm:flex-col sm:gap-0.5 sm:border-r sm:border-b-0 sm:pr-3 sm:pb-0 dark:border-gray-800">
            {DATE_RANGE_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => applyPreset(preset)}
                className={`rounded-md px-3 py-2.5 text-center text-base ring-1 ring-inset sm:py-1.5 sm:text-left sm:text-sm sm:ring-0 ${
                  isPresetActive(preset)
                    ? 'bg-indigo-600 text-white ring-indigo-600 sm:ring-0'
                    : 'text-gray-700 ring-gray-200 hover:bg-gray-100 sm:ring-0 dark:text-gray-300 dark:ring-gray-700 dark:hover:bg-gray-800'
                }`}
              >
                {t(`presets.${preset.id}`)}
              </button>
            ))}
          </div>

          <div className="w-full shrink-0 sm:w-64">
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
                const isFromDay =
                  displayFromDate && isSameDay(cellDate, displayFromDate)
                const isToDay =
                  displayToDate && isSameDay(cellDate, displayToDate)
                const isInRange =
                  displayFromDate &&
                  displayToDate &&
                  cellDate.getTime() > displayFromDate.getTime() &&
                  cellDate.getTime() < displayToDate.getTime()
                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => handleSelectDay(cellDate)}
                    className={`mx-auto flex size-9 items-center justify-center rounded-full text-base sm:size-7 sm:text-sm ${
                      isFromDay || isToDay
                        ? 'bg-indigo-600 text-white'
                        : isInRange
                          ? 'bg-indigo-50 text-gray-700 dark:bg-indigo-950/50 dark:text-gray-300'
                          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    }`}
                  >
                    {day}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
