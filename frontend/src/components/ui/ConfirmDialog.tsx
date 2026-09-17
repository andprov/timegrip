import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/Button'

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  cancelLabel,
  isConfirming = false,
  onConfirm,
  onCancel,
}: {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  isConfirming?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const { t } = useTranslation('common')

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900"
      >
        <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
        <div className="mt-6 flex flex-col gap-3">
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            onClick={onCancel}
          >
            {cancelLabel ?? t('cancel')}
          </Button>
          <Button
            type="button"
            variant="danger"
            disabled={isConfirming}
            onClick={onConfirm}
            className="w-full"
          >
            {confirmLabel ?? t('confirm')}
          </Button>
        </div>
      </div>
    </div>
  )
}
