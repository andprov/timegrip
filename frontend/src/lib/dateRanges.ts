function addDays(date: Date, days: number): Date {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

function startOfWeek(date: Date): Date {
  const daysSinceMonday = (date.getDay() + 6) % 7
  return addDays(date, -daysSinceMonday)
}

function endOfWeek(date: Date): Date {
  return addDays(startOfWeek(date), 6)
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

function startOfYear(date: Date): Date {
  return new Date(date.getFullYear(), 0, 1)
}

function endOfYear(date: Date): Date {
  return new Date(date.getFullYear(), 11, 31)
}

export interface DateRangePreset {
  label: string
  range: () => [Date, Date]
}

export const DATE_RANGE_PRESETS: DateRangePreset[] = [
  {
    label: 'Today',
    range: () => {
      const today = new Date()
      return [today, today]
    },
  },
  {
    label: 'Yesterday',
    range: () => {
      const yesterday = addDays(new Date(), -1)
      return [yesterday, yesterday]
    },
  },
  {
    label: 'This week',
    range: () => {
      const today = new Date()
      return [startOfWeek(today), endOfWeek(today)]
    },
  },
  {
    label: 'Last week',
    range: () => {
      const lastWeek = addDays(new Date(), -7)
      return [startOfWeek(lastWeek), endOfWeek(lastWeek)]
    },
  },
  {
    label: 'Past two weeks',
    range: () => {
      const today = new Date()
      return [addDays(today, -13), today]
    },
  },
  {
    label: 'This month',
    range: () => {
      const today = new Date()
      return [startOfMonth(today), endOfMonth(today)]
    },
  },
  {
    label: 'Last month',
    range: () => {
      const today = new Date()
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      return [startOfMonth(lastMonth), endOfMonth(lastMonth)]
    },
  },
  {
    label: 'This year',
    range: () => {
      const today = new Date()
      return [startOfYear(today), endOfYear(today)]
    },
  },
  {
    label: 'Last year',
    range: () => {
      const today = new Date()
      const lastYear = new Date(today.getFullYear() - 1, 0, 1)
      return [startOfYear(lastYear), endOfYear(lastYear)]
    },
  },
]
