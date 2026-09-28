import type { Page } from '@/api/types'

export const PAGE = 1
export const PROJECTS_PAGE_SIZE = 6
export const TIMERS_PAGE_SIZE = 15
export const MIN_PAGE_SIZE = 1
export const MAX_PAGE_SIZE = 100

/** Fetch every page of a list: the first one reveals the total, the rest go out in parallel. */
export async function fetchAllPages<T>(
  fetchPage: (page: number, pageSize: number) => Promise<Page<T>>,
): Promise<Page<T>> {
  const first = await fetchPage(PAGE, MAX_PAGE_SIZE)
  const totalPages = Math.ceil(first.total / MAX_PAGE_SIZE)
  const rest = await Promise.all(
    Array.from({ length: Math.max(totalPages - 1, 0) }, (_, i) =>
      fetchPage(PAGE + 1 + i, MAX_PAGE_SIZE),
    ),
  )
  return { ...first, items: first.items.concat(...rest.map((p) => p.items)) }
}
