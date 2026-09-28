import type { QueryClient } from '@tanstack/react-query'

export const RUNNING_TIMER_KEY = ['timers', 'running']

// Adding, editing or deleting a timer never changes the running one (the API
// refuses to edit or delete a running timer), so only the lists need a refetch.
export function invalidateTimerLists(queryClient: QueryClient) {
  return queryClient.invalidateQueries({
    queryKey: ['timers'],
    predicate: (query) => query.queryKey[1] !== 'running',
  })
}
