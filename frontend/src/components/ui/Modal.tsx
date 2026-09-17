import { useEffect } from 'react'
import type { ReactNode } from 'react'

export function Modal({
  title,
  titleClassName = 'text-gray-900 dark:text-gray-100',
  minHeightClassName = 'min-h-[22rem]',
  fullScreenOnMobile = false,
  showCloseButton = true,
  onClose,
  children,
}: {
  title: string
  titleClassName?: string
  minHeightClassName?: string
  /** Fills the whole screen below `sm:` instead of a small centered card — for forms with enough content to be worth the extra room. */
  fullScreenOnMobile?: boolean
  /** Hide when the modal already has its own Cancel button. */
  showCloseButton?: boolean
  onClose: () => void
  children: ReactNode
}) {
  useEffect(() => {
    const original = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = original
    }
  }, [])

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/40 sm:p-4 ${fullScreenOnMobile ? '' : 'p-3'}`}
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        className={`flex w-full flex-col bg-white p-4 sm:p-6 dark:bg-gray-900 ${minHeightClassName} ${
          fullScreenOnMobile
            ? 'h-dvh overflow-y-auto sm:h-auto sm:overflow-visible sm:max-w-md sm:rounded-lg sm:shadow-xl'
            : 'max-w-md rounded-lg shadow-xl'
        }`}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className={`text-lg font-semibold ${titleClassName}`}>{title}</h2>
          {showCloseButton && (
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="-m-2 rounded-md p-2 text-xl leading-none text-gray-400 hover:text-gray-600 sm:m-0 sm:p-0 sm:text-base dark:text-gray-500 dark:hover:text-gray-300"
            >
              ✕
            </button>
          )}
        </div>
        <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      </div>
    </div>
  )
}
