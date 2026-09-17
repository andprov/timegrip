import { useQuery } from '@tanstack/react-query'

import { getRunningTimer } from '@/api/timers'

export function useRunningTimer(enabled = true) {
  return useQuery({
    queryKey: ['timers', 'running'],
    queryFn: getRunningTimer,
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
    enabled,
  })
}
