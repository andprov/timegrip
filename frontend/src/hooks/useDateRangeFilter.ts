import { useState } from 'react'

import {
  endOfMonth,
  startOfMonth,
  toIsoEndOfDay,
  toIsoStartOfDay,
} from '@/lib/calendar'

function defaultDateFrom(): string {
  return toIsoStartOfDay(startOfMonth(new Date()))
}

function defaultDateTo(): string {
  return toIsoEndOfDay(endOfMonth(new Date()))
}

/** Shared date-range filter state, defaulting to the current month, for pages with timer queries. */
export function useDateRangeFilter() {
  const [dateFrom, setDateFrom] = useState(defaultDateFrom)
  const [dateTo, setDateTo] = useState(defaultDateTo)

  function onChange(nextFrom: string, nextTo: string) {
    setDateFrom(nextFrom)
    setDateTo(nextTo)
  }

  return { dateFrom, dateTo, onChange }
}
