import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export interface PieChartSlice {
  key: string
  label: string
  value: number
  color: string
}

interface PieChartProps {
  slices: PieChartSlice[]
  formatValue: (value: number) => string
  centerLabel: string
  size?: number
  thickness?: number
  className?: string
}

const GAP_PX = 3

export function PieChart({
  slices,
  formatValue,
  centerLabel,
  size = 200,
  thickness = 28,
  className = '',
}: PieChartProps) {
  const { t } = useTranslation('common')
  const [hoveredKey, setHoveredKey] = useState<string | null>(null)

  const total = slices.reduce((sum, slice) => sum + slice.value, 0)
  const radius = (size - thickness) / 2
  const circumference = 2 * Math.PI * radius

  const arcs = slices.reduce<
    (PieChartSlice & { dash: number; offset: number; fraction: number })[]
  >((acc, slice) => {
    const cumulative = acc.reduce((sum, a) => sum + a.fraction, 0) * circumference
    const fraction = total > 0 ? slice.value / total : 0
    const sliceLength = fraction * circumference
    const dash = Math.max(sliceLength - GAP_PX, 0)
    return [...acc, { ...slice, dash, offset: -cumulative, fraction }]
  }, [])

  const hovered = arcs.find((arc) => arc.key === hoveredKey) ?? null

  if (total === 0) {
    return (
      <div
        className={`flex items-center justify-center rounded-full ring-1 ring-inset ring-gray-200 dark:ring-gray-800 ${className}`}
        style={{ width: size, height: size }}
      >
        <span className="text-sm text-gray-400 dark:text-gray-500">{t('noData')}</span>
      </div>
    )
  }

  return (
    <div
      className={`relative inline-flex shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox={`0 0 ${size} ${size}`}
        width={size}
        height={size}
        className="-rotate-90"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={thickness}
          className="stroke-gray-100 dark:stroke-gray-800"
        />
        {arcs.map((arc) => (
          <circle
            key={arc.key}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={arc.color}
            strokeWidth={thickness}
            strokeDasharray={`${arc.dash} ${circumference - arc.dash}`}
            strokeDashoffset={arc.offset}
            strokeLinecap="butt"
            opacity={hoveredKey && hoveredKey !== arc.key ? 0.35 : 1}
            tabIndex={0}
            className="cursor-pointer outline-none transition-opacity"
            onMouseEnter={() => setHoveredKey(arc.key)}
            onMouseLeave={() => setHoveredKey(null)}
            onFocus={() => setHoveredKey(arc.key)}
            onBlur={() => setHoveredKey(null)}
          >
            <title>{`${arc.label} · ${formatValue(arc.value)} · ${Math.round(arc.fraction * 100)}%`}</title>
          </circle>
        ))}
      </svg>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
        {hovered ? (
          <>
            <span className="max-w-full truncate text-xs font-medium text-gray-500 dark:text-gray-400">
              {hovered.label}
            </span>
            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {formatValue(hovered.value)}
            </span>
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {Math.round(hovered.fraction * 100)}%
            </span>
          </>
        ) : (
          <>
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              {t('total')}
            </span>
            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {centerLabel}
            </span>
          </>
        )}
      </div>
    </div>
  )
}
