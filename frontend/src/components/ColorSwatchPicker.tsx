import { PROJECT_COLORS } from '@/api/types'

export function ColorSwatchPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (color: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {PROJECT_COLORS.map((color) => (
        <button
          key={color}
          type="button"
          aria-label={color}
          onClick={() => onChange(color)}
          className={`size-7 rounded-full ring-2 ring-offset-2 dark:ring-offset-gray-900 ${
            value === color ? 'ring-gray-900 dark:ring-white' : 'ring-transparent'
          }`}
          style={{ backgroundColor: color }}
        />
      ))}
    </div>
  )
}
