import { useQuery } from '@tanstack/react-query'

import { listTimers } from '@/api/timers'
import type { TimersFilter } from '@/api/types'
import { fetchAllPages } from '@/lib/pagination'

type AllTimersFilter = Omit<TimersFilter, 'page' | 'page_size'>

export function useAllTimers(filter: AllTimersFilter, enabled = true) {
  return useQuery({
    queryKey: ['timers', 'all', filter],
    queryFn: async () => {
      const all = await fetchAllPages((page, pageSize) =>
        listTimers({ ...filter, page, page_size: pageSize }),
      )
      return all.items
    },
    enabled,
  })
}
