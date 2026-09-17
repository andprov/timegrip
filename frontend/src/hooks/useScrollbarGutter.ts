import { useEffect, useState } from 'react'

export function useScrollbarGutter() {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const probe = document.createElement('div')
    probe.style.visibility = 'hidden'
    probe.style.position = 'absolute'
    probe.style.top = '-9999px'
    probe.style.overflowY = 'scroll'
    probe.style.setProperty('scrollbar-gutter', 'stable')
    document.body.appendChild(probe)
    setWidth(probe.offsetWidth - probe.clientWidth)
    document.body.removeChild(probe)
  }, [])

  return width
}
