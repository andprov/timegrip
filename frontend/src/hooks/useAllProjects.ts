import { useQuery } from '@tanstack/react-query'

import { listProjects } from '@/api/projects'
import { MAX_PAGE_SIZE } from '@/lib/pagination'

export function useAllProjects(enabled = true) {
  return useQuery({
    queryKey: ['projects', 'all'],
    queryFn: async () => {
      const first = await listProjects(1, MAX_PAGE_SIZE)
      const items = [...first.items]
      const totalPages = Math.ceil(first.total / MAX_PAGE_SIZE)
      for (let page = 2; page <= totalPages; page++) {
        const next = await listProjects(page, MAX_PAGE_SIZE)
        items.push(...next.items)
      }
      return { ...first, items }
    },
    staleTime: 5 * 60_000,
    enabled,
  })
}
