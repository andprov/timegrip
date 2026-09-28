import { useQuery } from '@tanstack/react-query'

import { listProjects } from '@/api/projects'
import { fetchAllPages } from '@/lib/pagination'

export function useAllProjects(enabled = true) {
  return useQuery({
    queryKey: ['projects', 'all'],
    queryFn: () => fetchAllPages(listProjects),
    staleTime: 5 * 60_000,
    enabled,
  })
}
