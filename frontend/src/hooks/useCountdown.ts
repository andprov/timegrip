import { useEffect, useState } from 'react'

function secondsUntil(deadline: number, now: number): number {
  return Math.max(0, Math.ceil((deadline - now) / 1000))
}

// Whole seconds left of a countdown that was `seconds` long at `startedAt`.
// The value is derived during render, so it is correct in the same render
// that receives a new countdown, and re-renders once per whole second.
export function useCountdown(seconds: number, startedAt: number): number {
  const deadline = startedAt + seconds * 1000
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (seconds <= 0) return
    const interval = setInterval(() => {
      const current = Date.now()
      setNow((prev) =>
        secondsUntil(deadline, prev) === secondsUntil(deadline, current)
          ? prev
          : current,
      )
      if (current >= deadline) clearInterval(interval)
    }, 250)
    return () => clearInterval(interval)
  }, [seconds, deadline])

  // `now` is stale until the first tick after a new countdown arrives, but a
  // countdown never has more time left than it started with.
  return Math.min(seconds, secondsUntil(deadline, now))
}
