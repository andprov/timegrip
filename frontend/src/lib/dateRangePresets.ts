import { endOfMonth, mondayOf, startOfMonth } from '@/lib/calendar'

export interface DateRangePreset {
  id: string
  label: string
  range: () => { from: Date; to: Date }
}

export const DATE_RANGE_PRESETS: DateRangePreset[] = [
  {
    id: 'today',
    label: 'Today',
    range: () => {
      const today = new Date()
      return { from: today, to: today }
    },
  },
  {
    id: 'yesterday',
    label: 'Yesterday',
    range: () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return { from: yesterday, to: yesterday }
    },
  },
  {
    id: 'this-week',
    label: 'This week',
    range: () => {
      const monday = mondayOf(new Date())
      const sunday = new Date(monday)
      sunday.setDate(sunday.getDate() + 6)
      return { from: monday, to: sunday }
    },
  },
  {
    id: 'last-week',
    label: 'Last week',
    range: () => {
      const thisMonday = mondayOf(new Date())
      const lastMonday = new Date(thisMonday)
      lastMonday.setDate(lastMonday.getDate() - 7)
      const lastSunday = new Date(thisMonday)
      lastSunday.setDate(lastSunday.getDate() - 1)
      return { from: lastMonday, to: lastSunday }
    },
  },
  {
    id: 'this-month',
    label: 'This month',
    range: () => {
      const today = new Date()
      return { from: startOfMonth(today), to: endOfMonth(today) }
    },
  },
  {
    id: 'last-month',
    label: 'Last month',
    range: () => {
      const firstOfThisMonth = startOfMonth(new Date())
      const lastOfLastMonth = new Date(firstOfThisMonth)
      lastOfLastMonth.setDate(0)
      return { from: startOfMonth(lastOfLastMonth), to: lastOfLastMonth }
    },
  },
  {
    id: 'this-year',
    label: 'This year',
    range: () => {
      const year = new Date().getFullYear()
      return { from: new Date(year, 0, 1), to: new Date(year, 11, 31) }
    },
  },
  {
    id: 'last-year',
    label: 'Last year',
    range: () => {
      const lastYear = new Date().getFullYear() - 1
      return {
        from: new Date(lastYear, 0, 1),
        to: new Date(lastYear, 11, 31),
      }
    },
  },
]
