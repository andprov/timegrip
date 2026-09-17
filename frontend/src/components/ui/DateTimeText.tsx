import { formatDate, formatTime } from '@/lib/format'

export function DateTimeText({
  iso,
  hour12,
  className = '',
  emptyText = '',
}: {
  iso: string
  hour12: boolean
  className?: string
  emptyText?: string
}) {
  if (!iso) {
    return <span className={className}>{emptyText}</span>
  }

  const date = new Date(iso)

  return (
    <span className={className}>
      {formatDate(date)}{' '}
      <span className="select-none text-gray-300 dark:text-gray-600">·</span>{' '}
      {formatTime(date, hour12)}
    </span>
  )
}
