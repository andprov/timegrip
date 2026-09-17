import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { usePopoverDismiss } from '@/hooks/usePopoverDismiss'
import { usePopoverPosition } from '@/hooks/usePopoverPosition'
import { Button } from '@/components/ui/Button'
import { formatTime, isSameDay } from '@/lib/format'

interface TimeValue {
  hours: number
  minutes: number | null
}

interface TimePickerProps {
  date: Date | null
  time: TimeValue | null
  onChange: (hours: number, minutes: number | null) => void
  hour12: boolean
  minTime?: Date
}

export function TimePicker({
  date,
  time,
  onChange,
  hour12,
  minTime,
}: TimePickerProps) {
  const { t } = useTranslation('common')
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const minuteListRef = useRef<HTMLDivElement>(null)

  const popoverPosition = usePopoverPosition(isOpen, containerRef, popupRef)
  usePopoverDismiss(isOpen, setIsOpen, containerRef)

  useEffect(() => {
    if (!isOpen) return
    const el = minuteListRef.current?.querySelector<HTMLButtonElement>(
      '[data-selected="true"]',
    )
    el?.scrollIntoView({ block: 'nearest' })
    // Only scroll the selected minute into view when the popover opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  const now = new Date()

  // Minutes are the only field that commits a value on its own — picking an
  // hour (or toggling AM/PM) never invents a minute, it only fills the hour.
  function handleHourChange(hour24: number) {
    onChange(hour24, time ? time.minutes : null)
  }

  function handleMinuteChange(minute: number) {
    onChange(time ? time.hours : now.getHours(), minute)
  }

  function handleToggleMeridiem() {
    const hours = time ? time.hours : now.getHours()
    const minutes = time ? time.minutes : null
    onChange((hours + 12) % 24, minutes)
  }

  const hasMinutes = time !== null && time.minutes !== null
  const displayHour24 = time ? time.hours : now.getHours()
  const displayMinute =
    time && time.minutes !== null ? time.minutes : now.getMinutes()
  const isPM = displayHour24 >= 12
  const displayHour12 = displayHour24 % 12 === 0 ? 12 : displayHour24 % 12

  const hourOptions = Array.from(
    { length: hour12 ? 12 : 24 },
    (_, i) => (hour12 ? i + 1 : i),
  )
  const minuteOptions = Array.from({ length: 60 }, (_, i) => i)

  function selectHour(h: number) {
    if (!hour12) {
      handleHourChange(h)
      return
    }
    handleHourChange((h % 12) + (isPM ? 12 : 0))
  }

  const restrictToMinTime = Boolean(
    minTime && isSameDay(date ?? now, minTime),
  )
  const restrictToNow = isSameDay(date ?? now, now)

  function isHourDisabled(h24: number): boolean {
    if (restrictToMinTime && minTime && h24 < minTime.getHours()) return true
    if (restrictToNow && h24 > now.getHours()) return true
    return false
  }

  function isMinuteDisabled(m: number): boolean {
    // displayHour24 defaulting to the current hour when no time is chosen
    // yet is exactly correct for this comparison, so it applies even before
    // an hour is chosen (mirrors the restrictToNow check below).
    if (restrictToMinTime && minTime) {
      if (displayHour24 < minTime.getHours()) return true
      if (displayHour24 === minTime.getHours() && m < minTime.getMinutes()) {
        return true
      }
    }
    // displayHour24 defaulting to the current hour is exactly correct for
    // this comparison, so it applies even before an hour is chosen.
    if (restrictToNow) {
      if (displayHour24 > now.getHours()) return true
      if (displayHour24 === now.getHours() && m > now.getMinutes()) {
        return true
      }
    }
    return false
  }

  return (
    <div
      ref={containerRef}
      className={`relative shrink-0 ${hour12 ? 'w-28 sm:w-24' : 'w-20 sm:w-16'}`}
    >
      <button
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        className="flex w-full items-center justify-center rounded-md border-0 px-2 py-3 text-base text-gray-900 outline-none ring-1 ring-inset ring-gray-300 sm:py-2 sm:text-sm dark:text-gray-100 dark:ring-gray-700"
      >
        <span className={time ? '' : 'text-gray-400 dark:text-gray-500'}>
          {time
            ? time.minutes !== null
              ? formatTime(new Date(2000, 0, 1, time.hours, time.minutes), hour12)
              : formatTime(new Date(2000, 0, 1, time.hours, 0), hour12).replace(
                  /:\d{2}/,
                  ':--',
                )
            : '--:--'}
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
          className="z-30 max-h-[calc(100dvh-2rem)] w-[21rem] max-w-[calc(100vw-2rem)] overflow-y-auto rounded-lg bg-white p-3 shadow-xl ring-1 ring-gray-200 sm:w-80 dark:bg-gray-900 dark:ring-gray-800"
        >
          <div className="flex gap-3">
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-400 dark:text-gray-500">{t('hours')}</span>
                {hour12 && (
                  <button
                    type="button"
                    onClick={handleToggleMeridiem}
                    className="ml-1 rounded px-2 py-1.5 text-sm font-medium text-gray-600 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:px-1.5 sm:py-0.5 sm:text-xs dark:text-gray-400 dark:ring-gray-700 dark:hover:bg-gray-800"
                  >
                    {isPM ? 'PM' : 'AM'}
                  </button>
                )}
              </div>
              <div className="grid grid-cols-4 gap-1">
                {hourOptions.map((h) => {
                  const isSelected =
                    time !== null &&
                    (hour12 ? displayHour12 === h : displayHour24 === h)
                  const h24 = hour12 ? (h % 12) + (isPM ? 12 : 0) : h
                  const isDisabled = isHourDisabled(h24)
                  const isNow = !time && h24 === now.getHours()
                  return (
                    <button
                      key={h}
                      type="button"
                      disabled={isDisabled}
                      onClick={() => selectHour(h)}
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-base sm:h-7 sm:w-7 sm:text-sm ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : isDisabled
                            ? 'cursor-not-allowed text-gray-300 dark:text-gray-700'
                            : isNow
                              ? 'text-indigo-600 ring-1 ring-inset ring-indigo-300 dark:text-indigo-400 dark:ring-indigo-800'
                              : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                      }`}
                    >
                      {h.toString().padStart(2, '0')}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="w-px bg-gray-200 dark:bg-gray-800" />

            <div className="flex w-36 shrink-0 flex-col items-center gap-2">
              <span className="text-xs text-gray-400 dark:text-gray-500">{t('minutes')}</span>
              <div
                ref={minuteListRef}
                className="grid max-h-[188px] grid-cols-4 gap-1 overflow-y-auto overflow-x-hidden"
              >
                {minuteOptions.map((m) => {
                  const isSelected = hasMinutes && displayMinute === m
                  const isDisabled = isMinuteDisabled(m)
                  const isNow =
                    !hasMinutes &&
                    displayHour24 === now.getHours() &&
                    m === now.getMinutes()
                  return (
                    <button
                      key={m}
                      type="button"
                      disabled={isDisabled}
                      data-selected={isSelected || isNow}
                      onClick={() => handleMinuteChange(m)}
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-base sm:h-7 sm:w-7 sm:text-sm ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : isDisabled
                            ? 'cursor-not-allowed text-gray-300 dark:text-gray-700'
                            : isNow
                              ? 'text-indigo-600 ring-1 ring-inset ring-indigo-300 dark:text-indigo-400 dark:ring-indigo-800'
                              : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                      }`}
                    >
                      {m.toString().padStart(2, '0')}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
          <div className="mt-3 flex justify-center">
            <Button type="button" onClick={() => setIsOpen(false)}>
              {t('done')}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
