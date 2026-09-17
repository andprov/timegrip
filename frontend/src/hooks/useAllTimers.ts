import { useQuery } from '@tanstack/react-query'

import { listTimers } from '@/api/timers'
import type { TimersFilter } from '@/api/types'
import { MAX_PAGE_SIZE } from '@/lib/pagination'

type AllTimersFilter = Omit<TimersFilter, 'page' | 'page_size'>

export function useAllTimers(filter: AllTimersFilter, enabled = true) {
  return useQuery({
    queryKey: ['timers', 'all', filter],
    queryFn: async () => {
      const first = await listTimers({
        ...filter,
        page: 1,
        page_size: MAX_PAGE_SIZE,
      })
      const items = [...first.items]
      const totalPages = Math.ceil(first.total / MAX_PAGE_SIZE)
      for (let page = 2; page <= totalPages; page++) {
        const next = await listTimers({
          ...filter,
          page,
          page_size: MAX_PAGE_SIZE,
        })
        items.push(...next.items)
      }
      return items
    },
    enabled,
  })
}
