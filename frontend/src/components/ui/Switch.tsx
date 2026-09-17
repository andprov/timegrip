export function Switch({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-8 w-14 shrink-0 items-center rounded-full transition-colors outline-none sm:h-6 sm:w-11 ${
          checked ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
        }`}
      >
        <span
          className={`inline-block size-6 transform rounded-full bg-white shadow transition-transform sm:size-4 ${
            checked ? 'translate-x-7 sm:translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      {label}
    </label>
  )
}
