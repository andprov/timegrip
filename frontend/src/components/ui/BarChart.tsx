import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

export interface BarChartPoint {
  key: string
  label: string
  value: number
}

interface BarChartProps {
  points: BarChartPoint[]
  formatValue: (value: number) => string
  className?: string
}

const ACCENT = '#4F46E5'
const DEFAULT_WIDTH = 600
const MAX_BAR_WIDTH = 24
const MIN_BAR_WIDTH = 1
const BAR_RADIUS = 4
const PADDING_LEFT = 40
const PADDING_TOP = 12
const PLOT_HEIGHT = 140
const LABEL_BAND = 24
const CHART_HEIGHT = PADDING_TOP + PLOT_HEIGHT + LABEL_BAND

function roundedTopRectPath(
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
): string {
  if (height <= 0) return ''
  const r = Math.min(radius, width / 2, height)
  return (
    `M ${x} ${y + height} ` +
    `L ${x} ${y + r} ` +
    `Q ${x} ${y} ${x + r} ${y} ` +
    `L ${x + width - r} ${y} ` +
    `Q ${x + width} ${y} ${x + width} ${y + r} ` +
    `L ${x + width} ${y + height} Z`
  )
}

export function BarChart({ points, formatValue, className = '' }: BarChartProps) {
  const { t } = useTranslation('common')
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(0)
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width
      if (width) setContainerWidth(width)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  if (points.length === 0) {
    return (
      <div
        className={`flex h-44 items-center justify-center text-sm text-gray-400 dark:text-gray-500 ${className}`}
      >
        {t('noData')}
      </div>
    )
  }

  const chartWidth = containerWidth > 0 ? containerWidth : DEFAULT_WIDTH
  const plotWidth = Math.max(chartWidth - PADDING_LEFT, 0)
  const step = plotWidth / points.length
  const barWidth = Math.min(MAX_BAR_WIDTH, Math.max(step - 2, MIN_BAR_WIDTH))
  const maxValue = Math.max(...points.map((p) => p.value), 1)
  const baseline = PADDING_TOP + PLOT_HEIGHT

  function slotCenter(index: number): number {
    return PADDING_LEFT + step * index + step / 2
  }
  function barHeight(value: number): number {
    return (value / maxValue) * PLOT_HEIGHT
  }

  const maxLabels = Math.max(2, Math.floor(plotWidth / 56))
  const labelStep = Math.max(1, Math.ceil(points.length / maxLabels))
  const hovered = hoveredIndex !== null ? points[hoveredIndex] : null

  return (
    <div ref={containerRef} className={className}>
      <div className="relative" style={{ width: chartWidth, height: CHART_HEIGHT }}>
        <svg
          viewBox={`0 0 ${chartWidth} ${CHART_HEIGHT}`}
          width={chartWidth}
          height={CHART_HEIGHT}
          className="block"
        >
          {[0, 0.5, 1].map((fraction) => (
            <line
              key={fraction}
              x1={PADDING_LEFT}
              x2={chartWidth}
              y1={PADDING_TOP + PLOT_HEIGHT * (1 - fraction)}
              y2={PADDING_TOP + PLOT_HEIGHT * (1 - fraction)}
              strokeWidth={1}
              className="stroke-gray-100 dark:stroke-gray-800"
            />
          ))}

          <text
            x={PADDING_LEFT - 8}
            y={PADDING_TOP + 3}
            textAnchor="end"
            className="fill-gray-400 text-[10px] dark:fill-gray-500"
          >
            {formatValue(maxValue)}
          </text>
          <text
            x={PADDING_LEFT - 8}
            y={baseline + 3}
            textAnchor="end"
            className="fill-gray-400 text-[10px] dark:fill-gray-500"
          >
            {formatValue(0)}
          </text>

          {points.map((p, i) => {
            const height = barHeight(p.value)
            const x = slotCenter(i) - barWidth / 2
            const y = baseline - height
            return (
              <path
                key={p.key}
                d={roundedTopRectPath(x, y, barWidth, height, BAR_RADIUS)}
                fill={ACCENT}
                opacity={i === hoveredIndex ? 1 : 0.85}
              />
            )
          })}

          {points.map((p, i) => (
            <rect
              key={p.key}
              x={slotCenter(i) - step / 2}
              y={PADDING_TOP}
              width={step}
              height={PLOT_HEIGHT}
              fill="transparent"
              tabIndex={0}
              className="cursor-pointer outline-none"
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
              onFocus={() => setHoveredIndex(i)}
              onBlur={() => setHoveredIndex(null)}
            >
              <title>{`${p.label} · ${formatValue(p.value)}`}</title>
            </rect>
          ))}

          {points.map((p, i) =>
            i % labelStep === 0 ? (
              <text
                key={p.key}
                x={slotCenter(i)}
                y={baseline + 16}
                textAnchor="middle"
                className="fill-gray-400 text-[10px] dark:fill-gray-500"
              >
                {p.label}
              </text>
            ) : null,
          )}
        </svg>

        {hoveredIndex !== null && hovered && (
          <div
            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-md bg-gray-900 px-2 py-1 text-xs whitespace-nowrap text-white shadow-lg dark:bg-gray-100 dark:text-gray-900"
            style={{
              left: Math.min(
                Math.max(slotCenter(hoveredIndex), 32),
                chartWidth - 32,
              ),
              top: baseline - barHeight(hovered.value) - 8,
            }}
          >
            <span className="font-medium">{formatValue(hovered.value)}</span>
            <span className="ml-1 opacity-70">· {hovered.label}</span>
          </div>
        )}
      </div>
    </div>
  )
}
