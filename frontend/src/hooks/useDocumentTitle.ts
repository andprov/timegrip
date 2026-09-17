import { useEffect, useRef } from 'react'

// Sets document.title while the calling component is mounted, restoring
// whatever title was in place beforehand on unmount. The SPA ships a single
// index.html with a build-time SEO title (see seo.config.json) meant for the
// landing page; this lets authenticated pages show their own tab title
// without touching that baked-in default.
export function useDocumentTitle(title: string): void {
  const originalTitle = useRef(document.title)

  useEffect(() => {
    document.title = title
  }, [title])

  useEffect(() => {
    const original = originalTitle.current
    return () => {
      document.title = original
    }
  }, [])
}
