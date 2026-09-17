import { useLayoutEffect, useState } from 'react'
import type { RefObject } from 'react'

const MARGIN = 16
const GAP = 4
const MOBILE_BREAKPOINT = 640

export interface PopoverPosition {
  position: 'fixed'
  top: number
  left: number
  transform: string
  isMobile: boolean
}

/**
 * Position for a popover that opens next to its field.
 *
 * Desktop: pinned to the viewport (`fixed`), right below the field (or
 * above it if there's no room), horizontally centered on screen.
 *
 * Mobile: the field is often near the top of a long page and the popover
 * (a calendar with presets, say) can be taller than what's left of the
 * screen below it, so it opens centered on screen as a modal-style panel
 * over a backdrop instead. Centering is measured against the *visible*
 * area — `visualViewport`, which excludes Safari's toolbars — and the top
 * edge is never pushed above `MARGIN`, so a popover too tall to fit stays
 * anchored under the top edge and scrolls inside itself rather than
 * having its head cut off.
 */
export function usePopoverPosition(
  isOpen: boolean,
  containerRef: RefObject<HTMLElement | null>,
  popupRef: RefObject<HTMLElement | null>,
): PopoverPosition | null {
  const [pos, setPos] = useState<PopoverPosition | null>(null)

  useLayoutEffect(() => {
    if (!isOpen) return
    const container = containerRef.current
    const popup = popupRef.current
    if (!container || !popup) return
    const containerRect = container.getBoundingClientRect()
    const popupHeight = popup.getBoundingClientRect().height

    if (window.innerWidth < MOBILE_BREAKPOINT) {
      const visual = window.visualViewport
      const viewportHeight = visual?.height ?? window.innerHeight
      const viewportTop = visual?.offsetTop ?? 0
      setPos({
        position: 'fixed',
        top: viewportTop + Math.max((viewportHeight - popupHeight) / 2, MARGIN),
        left: window.innerWidth / 2,
        transform: 'translateX(-50%)',
        isMobile: true,
      })
      return
    }

    const spaceBelow = window.innerHeight - containerRect.bottom - MARGIN
    const spaceAbove = containerRect.top - MARGIN
    const openBelow = spaceBelow >= popupHeight || spaceBelow >= spaceAbove
    let top = openBelow
      ? containerRect.bottom + GAP
      : containerRect.top - popupHeight - GAP
    top = Math.min(
      Math.max(top, MARGIN),
      window.innerHeight - popupHeight - MARGIN,
    )
    setPos({
      position: 'fixed',
      top,
      left: window.innerWidth / 2,
      transform: 'translateX(-50%)',
      isMobile: false,
    })
  }, [isOpen, containerRef, popupRef])

  return pos
}
