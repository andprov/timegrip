import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/auth/useAuth'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { usePopoverDismiss } from '@/hooks/usePopoverDismiss'
import { useScrollbarGutter } from '@/hooks/useScrollbarGutter'
import { ActivationGate } from '@/components/ActivationGate'
import { AppLogo } from '@/components/AppLogo'
import { RunningTimerBar } from '@/components/layout/RunningTimerBar'

const NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium ${
    isActive
      ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
      : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
  }`

const MENU_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `block rounded-md px-4 py-3.5 text-lg font-medium ${
    isActive
      ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
      : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
  }`

// Maps each personal-cabinet route to its already-translated nav label, so
// the browser tab title tracks the current page instead of staying stuck on
// the landing page's build-time SEO title (see seo.config.json).
const PAGE_TITLE_KEYS: Record<string, string> = {
  '/dashboard': 'dashboard',
  '/projects': 'projects',
  '/timers': 'timers',
  '/report': 'report',
  '/account': 'account',
}

export function AppLayout() {
  const { t } = useTranslation('common')
  const { user, signOut } = useAuth()
  const location = useLocation()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const mainRef = useRef<HTMLElement>(null)

  useEffect(() => {
    setIsMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    mainRef.current?.scrollTo(0, 0)
  }, [location.pathname])

  usePopoverDismiss(isMenuOpen, setIsMenuOpen, menuRef)

  const pageTitleKey = PAGE_TITLE_KEYS[location.pathname]
  useDocumentTitle(pageTitleKey ? `${t(pageTitleKey)} - TimeGrip` : 'TimeGrip')

  useEffect(() => {
    if (!isMenuOpen) return
    const original = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = original
    }
  }, [isMenuOpen])

  const scrollbarGutter = useScrollbarGutter()

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-gray-50 dark:bg-gray-950">
      <header
        className="shrink-0 border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
        style={{ paddingRight: scrollbarGutter }}
      >
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-x-2 gap-y-3 px-4 py-3 sm:gap-x-4">
          <div className="flex min-w-0 items-center gap-x-4 gap-y-2">
            {location.pathname === '/dashboard' ? (
              <span className="flex min-w-0 items-center gap-1.5 text-lg font-semibold text-gray-900 dark:text-gray-100">
                <AppLogo className="size-6 shrink-0" />
                <span className="truncate">TimeGrip</span>
              </span>
            ) : (
              <Link
                to="/dashboard"
                className="flex min-w-0 items-center gap-1.5 text-lg font-semibold text-gray-900 hover:text-gray-700 dark:text-gray-100 dark:hover:text-gray-300"
              >
                <AppLogo className="size-6 shrink-0" />
                <span className="truncate">TimeGrip</span>
              </Link>
            )}
            <nav className="hidden flex-wrap items-center gap-1 sm:flex">
              <NavLink to="/dashboard" className={NAV_LINK_CLASS}>
                {t('dashboard')}
              </NavLink>
              <NavLink to="/projects" className={NAV_LINK_CLASS}>
                {t('projects')}
              </NavLink>
              <NavLink to="/timers" className={NAV_LINK_CLASS}>
                {t('timers')}
              </NavLink>
              <NavLink to="/report" className={NAV_LINK_CLASS}>
                {t('report')}
              </NavLink>
              <NavLink to="/account" className={NAV_LINK_CLASS}>
                {t('account')}
              </NavLink>
            </nav>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <RunningTimerBar />
            <button
              type="button"
              onClick={signOut}
              className="hidden text-sm font-medium text-gray-600 hover:text-gray-900 sm:block dark:text-gray-400 dark:hover:text-gray-100"
            >
              {t('signOut')}
            </button>
            <div ref={menuRef} className="sm:hidden">
              <button
                type="button"
                onClick={() => setIsMenuOpen((o) => !o)}
                aria-label={t('openMenu')}
                aria-expanded={isMenuOpen}
                className="flex size-11 items-center justify-center rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  strokeLinecap="round"
                  className="size-9"
                >
                  <path d="M2 6h20M2 12h20M2 18h20" />
                </svg>
              </button>
              <div
                aria-hidden={!isMenuOpen}
                onClick={() => setIsMenuOpen(false)}
                className={`fixed inset-0 z-30 bg-black/50 transition-opacity ${
                  isMenuOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
                }`}
              />
              <div
                className={`fixed inset-y-0 right-0 z-40 flex w-4/5 max-w-xs flex-col bg-white shadow-xl transition-transform duration-300 dark:bg-gray-900 ${
                  isMenuOpen ? 'translate-x-0' : 'translate-x-full'
                }`}
              >
                <div className="flex items-center justify-end p-3">
                  <button
                    type="button"
                    onClick={() => setIsMenuOpen(false)}
                    aria-label={t('closeMenu')}
                    className="flex size-11 items-center justify-center rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={2}
                      strokeLinecap="round"
                      className="size-7"
                    >
                      <path d="M6 6l12 12M18 6L6 18" />
                    </svg>
                  </button>
                </div>
                <nav className="flex flex-col gap-1 px-2">
                  <NavLink to="/dashboard" className={MENU_LINK_CLASS}>
                    {t('dashboard')}
                  </NavLink>
                  <NavLink to="/projects" className={MENU_LINK_CLASS}>
                    {t('projects')}
                  </NavLink>
                  <NavLink to="/timers" className={MENU_LINK_CLASS}>
                    {t('timers')}
                  </NavLink>
                  <NavLink to="/report" className={MENU_LINK_CLASS}>
                    {t('report')}
                  </NavLink>
                  <NavLink to="/account" className={MENU_LINK_CLASS}>
                    {t('account')}
                  </NavLink>
                  <div className="my-1 border-t border-gray-100 dark:border-gray-800" />
                  <button
                    type="button"
                    onClick={signOut}
                    className="block w-full rounded-md px-4 py-3.5 text-left text-lg font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    {t('signOut')}
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </div>
      </header>
      <main
        ref={mainRef}
        className="scrollbar-stable min-h-0 flex-1 overflow-y-auto"
      >
        <div className="mx-auto max-w-5xl px-4 py-8">
          {user && !user.is_active ? <ActivationGate /> : <Outlet />}
        </div>
      </main>
    </div>
  )
}
