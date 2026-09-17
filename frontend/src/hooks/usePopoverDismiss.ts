import { useEffect } from 'react'
import type { Dispatch, RefObject, SetStateAction } from 'react'

/** Closes an open popover/menu on an outside click or Escape. */
export function usePopoverDismiss(
  isOpen: boolean,
  setIsOpen: Dispatch<SetStateAction<boolean>>,
  containerRef: RefObject<HTMLElement | null>,
) {
  useEffect(() => {
    if (!isOpen) return

    function handlePointerDown(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false)
        // The mouseup/click that completes this same tap is still coming —
        // without swallowing it, it falls through to whatever is under the
        // popover (e.g. a row opening its own edit modal). Capture it once,
        // before it reaches its target, and stop it there.
        function swallowClick(clickEvent: MouseEvent) {
          clickEvent.stopPropagation()
        }
        document.addEventListener('click', swallowClick, {
          capture: true,
          once: true,
        })
        setTimeout(() => {
          document.removeEventListener('click', swallowClick, {
            capture: true,
          })
        }, 0)
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false)
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, setIsOpen, containerRef])
}
