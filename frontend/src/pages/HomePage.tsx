import { useEffect, useRef, useState } from 'react'
import type { PointerEvent as ReactPointerEvent, ReactNode, SVGProps } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { useAuth } from '@/auth/useAuth'
import { AppLogo } from '@/components/AppLogo'
import { LinkButton } from '@/components/ui/Button'
import { SUPPORTED_LOCALES } from '@/i18n/config'
import { useLocaleSetting } from '@/i18n/useLocaleSetting'
import type { ThemePreference } from '@/theme/ThemeContext'
import { useTheme } from '@/theme/useTheme'

// Reserves width for the widest translation of `i18nKey` up front, by
// stacking every locale's variant in the same grid cell and showing only
// the active one — so switching languages never resizes (and shifts) the
// header/footer around it, no matter how much translations vary in length.
function StableText({ i18nKey, ns = 'common' }: { i18nKey: string; ns?: string }) {
  const { i18n } = useTranslation()

  return (
    <span className="inline-grid justify-items-center *:col-start-1 *:row-start-1">
      {SUPPORTED_LOCALES.map((loc) => (
        <span
          key={loc}
          aria-hidden={loc !== i18n.language}
          className={loc === i18n.language ? '' : 'invisible'}
        >
          {i18n.getFixedT(loc, ns)(i18nKey)}
        </span>
      ))}
    </span>
  )
}

function Icon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    />
  )
}

function IconProjects(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M4 6h5l2 2h9v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z" />
    </Icon>
  )
}

function IconTimer(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx={12} cy={12} r={9} />
      <path d="M12 7v5l4 2" />
    </Icon>
  )
}

function IconChart(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M4 20V10M12 20V4M20 20v-7" />
      <path d="M2 20h20" />
    </Icon>
  )
}

function IconBilling(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx={12} cy={12} r={9} />
      <path d="M12 7v10M15 9.5c0-1.4-1.3-2.5-3-2.5s-3 1-3 2.3 1.3 1.9 3 2.2 3 .9 3 2.2-1.3 2.3-3 2.3-3-1.1-3-2.5" />
    </Icon>
  )
}

function IconApi(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M8 6 3 12l5 6M16 6l5 6-5 6" />
    </Icon>
  )
}

function IconDevices(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <rect x="3" y="4" width="14" height="10" rx="1" />
      <path d="M10 14v3M8 20h4" />
      <rect x="17" y="9" width="5" height="9" rx="1" />
    </Icon>
  )
}

function IconSun(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx={12} cy={12} r={4} />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </Icon>
  )
}

function IconMoon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
    </Icon>
  )
}

function IconSystemTheme(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx={12} cy={12} r={9} />
      <path d="M12 3a9 9 0 0 0 0 18Z" fill="currentColor" />
    </Icon>
  )
}

function IconGitHub(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor" {...props}>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
    </svg>
  )
}

function ThemeToggle({ className = '' }: { className?: string }) {
  const { t } = useTranslation('common')
  const { theme, setTheme } = useTheme()

  // Cycles through all three preferences, ordered so that the first click
  // from «system» always visibly flips the page: system → opposite of the OS
  // theme → OS theme → system.
  const systemTheme: ThemePreference = window.matchMedia(
    '(prefers-color-scheme: dark)',
  ).matches
    ? 'dark'
    : 'light'
  const next: ThemePreference =
    theme === 'system'
      ? systemTheme === 'dark'
        ? 'light'
        : 'dark'
      : theme === systemTheme
        ? 'system'
        : systemTheme

  const label = {
    light: t('switchToLightTheme'),
    dark: t('switchToDarkTheme'),
    system: t('switchToSystemTheme'),
  }[next]

  const iconClass = 'size-6 sm:size-5'

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={() => setTheme(next)}
      className={`flex size-11 items-center justify-center rounded-full text-gray-600 hover:bg-gray-100 sm:size-9 dark:text-gray-400 dark:hover:bg-gray-800 ${className}`}
    >
      {theme === 'light' && <IconSun className={iconClass} />}
      {theme === 'dark' && <IconMoon className={iconClass} />}
      {theme === 'system' && <IconSystemTheme className={iconClass} />}
    </button>
  )
}

function LanguageToggle({ className = '' }: { className?: string }) {
  const { t } = useTranslation('common')
  const { locale, changeLocale } = useLocaleSetting()

  return (
    <button
      type="button"
      aria-label={t('switchLanguage')}
      onClick={() => changeLocale(locale === 'ru' ? 'en' : 'ru')}
      className={`flex h-11 min-w-11 items-center justify-center rounded-full px-2 text-sm font-medium text-gray-600 hover:bg-gray-100 sm:h-9 sm:min-w-9 dark:text-gray-400 dark:hover:bg-gray-800 ${className}`}
    >
      {locale.toUpperCase()}
    </button>
  )
}

const FEATURE_ITEMS: { icon: (p: SVGProps<SVGSVGElement>) => ReactNode; key: string }[] = [
  { icon: IconProjects, key: 'projects' },
  { icon: IconTimer, key: 'tracking' },
  { icon: IconChart, key: 'reports' },
  { icon: IconBilling, key: 'billing' },
  { icon: IconDevices, key: 'devices' },
  { icon: IconApi, key: 'api' },
]

function ScreenshotCard({
  src,
  alt,
  onZoom,
}: {
  src: string
  alt: string
  onZoom: ((src: string, alt: string) => void) | null
}) {
  if (!onZoom) {
    return (
      <div className="block w-full overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
        <img src={src} alt={alt} className="w-full" loading="lazy" />
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => onZoom(src, alt)}
      className="block w-full cursor-zoom-in overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-gray-200 transition hover:opacity-90 dark:bg-gray-800 dark:ring-gray-700"
    >
      <img src={src} alt={alt} className="w-full" loading="lazy" />
    </button>
  )
}

const MOBILE_MEDIA_QUERY = '(max-width: 639px)'

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(MOBILE_MEDIA_QUERY).matches,
  )

  useEffect(() => {
    const mql = window.matchMedia(MOBILE_MEDIA_QUERY)
    const handleChange = () => setIsMobile(mql.matches)
    mql.addEventListener('change', handleChange)
    return () => mql.removeEventListener('change', handleChange)
  }, [])

  return isMobile
}

function Lightbox({
  image,
  onClose,
}: {
  image: { src: string; alt: string } | null
  onClose: () => void
}) {
  const { t } = useTranslation('home')

  useEffect(() => {
    if (!image) return

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [image, onClose])

  if (!image) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <button
        type="button"
        aria-label={t('closeAria')}
        onClick={onClose}
        className="absolute top-4 right-4 flex size-12 items-center justify-center rounded-full bg-white text-gray-900 shadow-lg ring-1 ring-black/10 transition hover:bg-gray-100 sm:size-10"
      >
        <Icon className="size-7 sm:size-6">
          <path d="M6 6l12 12M18 6 6 18" />
        </Icon>
      </button>
      <img
        src={image.src}
        alt={image.alt}
        className="max-h-full max-w-full rounded-lg object-contain shadow-2xl ring-1 ring-white/20"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  )
}

const HERO_SLIDE_ITEMS = [
  { src: '/img/home/Dashboard-light.png', key: 'dashboardLight' },
  { src: '/img/home/Dashboard-dark.png', key: 'dashboardDark' },
  { src: '/img/home/Projects-1.png', key: 'projects1' },
  { src: '/img/home/Projects-2-dark.png', key: 'projects2Dark' },
]

const CAROUSEL_INTERVAL_MS = 6000

const SWIPE_THRESHOLD_RATIO = 0.15

function Carousel({ slides }: { slides: { src: string; alt: string }[] }) {
  const { t } = useTranslation('home')
  const count = slides.length
  // Clone the last slide before the first, and the first after the last,
  // so sliding past either end can keep moving in the same direction —
  // then we snap (no transition) from the clone to the real slide once
  // the animation has finished, which looks identical to the viewer.
  const extended = [slides[count - 1], ...slides, slides[0]]

  const [trackIndex, setTrackIndex] = useState(1)
  const [dragOffset, setDragOffset] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [withTransition, setWithTransition] = useState(true)
  const trackRef = useRef<HTMLDivElement>(null)
  const startXRef = useRef(0)

  const activeIndex = ((trackIndex - 1) % count + count) % count

  useEffect(() => {
    if (isDragging) return
    const id = setTimeout(() => {
      setWithTransition(true)
      setTrackIndex((i) => i + 1)
    }, CAROUSEL_INTERVAL_MS)
    return () => clearTimeout(id)
  }, [trackIndex, isDragging])

  function move(delta: number) {
    setWithTransition(true)
    setTrackIndex((i) => i + delta)
  }

  function goToSlide(i: number) {
    setWithTransition(true)
    setTrackIndex(i + 1)
  }

  function handleTransitionEnd() {
    // Clicking (or auto-advancing) again before a transition finishes
    // retargets it instead of queuing it — the browser only fires one
    // transitionend, for wherever trackIndex ended up. A quick run of
    // clicks can land that past the single cloned slide on either end
    // (e.g. 7, with only 6 slides in the track), which this exact
    // trackIndex === 0 / === count + 1 check never catches, permanently
    // stranding the track past the last real image. Snapping back from
    // the whole out-of-range span, not just the one clone step, keeps a
    // burst of input from ever leaving it stuck on a blank slide.
    if (trackIndex < 1 || trackIndex > count) {
      setWithTransition(false)
      setTrackIndex(((((trackIndex - 1) % count) + count) % count) + 1)
    }
  }

  function handlePointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    setIsDragging(true)
    setWithTransition(false)
    startXRef.current = e.clientX
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  function handlePointerMove(e: ReactPointerEvent<HTMLDivElement>) {
    if (!isDragging) return
    setDragOffset(e.clientX - startXRef.current)
  }

  function endDrag() {
    if (!isDragging) return
    const width = trackRef.current?.offsetWidth ?? 1
    if (dragOffset < -width * SWIPE_THRESHOLD_RATIO) move(1)
    else if (dragOffset > width * SWIPE_THRESHOLD_RATIO) move(-1)
    else setWithTransition(true)
    setIsDragging(false)
    setDragOffset(0)
  }

  return (
    <div className="relative">
      <div
        ref={trackRef}
        className="touch-pan-y overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-gray-200 select-none dark:bg-gray-800 dark:ring-gray-700"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        <div
          className="flex"
          onTransitionEnd={handleTransitionEnd}
          style={{
            transform: `translateX(calc(${-trackIndex * 100}% + ${dragOffset}px))`,
            transition: withTransition ? 'transform 400ms ease' : 'none',
          }}
        >
          {extended.map((slide, i) => (
            <img
              key={`${slide.src}-${i}`}
              src={slide.src}
              alt={slide.alt}
              className="w-full shrink-0"
              draggable={false}
            />
          ))}
        </div>
      </div>

      <button
        type="button"
        aria-label={t('previousSlideAria')}
        onClick={() => move(-1)}
        className="absolute top-1/2 left-3 flex size-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-gray-700 shadow ring-1 ring-gray-200 hover:bg-white sm:size-9 dark:bg-gray-900/90 dark:text-gray-300 dark:ring-gray-700 dark:hover:bg-gray-900"
      >
        <Icon className="size-6 sm:size-5">
          <path d="M15 19 8 12l7-7" />
        </Icon>
      </button>
      <button
        type="button"
        aria-label={t('nextSlideAria')}
        onClick={() => move(1)}
        className="absolute top-1/2 right-3 flex size-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-gray-700 shadow ring-1 ring-gray-200 hover:bg-white sm:size-9 dark:bg-gray-900/90 dark:text-gray-300 dark:ring-gray-700 dark:hover:bg-gray-900"
      >
        <Icon className="size-6 sm:size-5">
          <path d="m9 5 7 7-7 7" />
        </Icon>
      </button>

      <div className="mt-4 flex justify-center gap-2">
        {slides.map((slide, i) => (
          <button
            key={slide.src}
            type="button"
            aria-label={t('goToSlideAria', { number: i + 1 })}
            aria-current={i === activeIndex}
            onClick={() => goToSlide(i)}
            className={`h-2 rounded-full transition-all ${
              i === activeIndex
                ? 'w-6 bg-indigo-600'
                : 'w-2 bg-gray-300 hover:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-600'
            }`}
          />
        ))}
      </div>
    </div>
  )
}

function ShowcaseRow({
  title,
  description,
  reverse,
  action,
  children,
}: {
  title: string
  description: string
  reverse?: boolean
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <div
      className={`flex flex-col items-center gap-10 md:gap-16 ${reverse ? 'md:flex-row-reverse' : 'md:flex-row'}`}
    >
      <div className="w-full md:w-1/2">{children}</div>
      <div className="w-full md:w-1/2">
        <h3 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h3>
        <p className="mt-3 text-gray-600 dark:text-gray-400">{description}</p>
        {action && <div className="mt-5">{action}</div>}
      </div>
    </div>
  )
}

const MOBILE_SHOT_ITEMS = [
  { src: '/img/home/Dashboard-mobile-1.png', key: 'dashboard1' },
  { src: '/img/home/Dashboard-mobile-2.png', key: 'dashboard2' },
  { src: '/img/home/Projects-mobile.png', key: 'projects' },
  { src: '/img/home/Timers-mobile.png', key: 'timers' },
]

export function HomePage() {
  const { t } = useTranslation('home')
  const { t: tc } = useTranslation('common')
  const { status } = useAuth()
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'
  const isAuthenticated = status === 'authenticated'
  const isMobile = useIsMobile()

  const img = (base: string) =>
    `/img/home/${base}-${isDark ? 'dark' : 'light'}.png`

  const heroSlides = HERO_SLIDE_ITEMS.map((slide) => ({
    src: slide.src,
    alt: t(`slides.${slide.key}`),
  }))

  const mobileShots = MOBILE_SHOT_ITEMS.map((shot) => ({
    src: shot.src,
    alt: t(`mobile.shots.${shot.key}`),
  }))

  const [lightboxImage, setLightboxImage] = useState<{
    src: string
    alt: string
  } | null>(null)
  const openLightbox = (src: string, alt: string) =>
    setLightboxImage({ src, alt })
  const onZoom = isMobile ? null : openLightbox

  return (
    <div className="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <header className="sticky top-0 z-50 h-16 border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto flex h-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <span className="flex items-center gap-1.5 text-lg font-semibold">
            <AppLogo className="size-6" />
            TimeGrip
          </span>
          <div className="flex items-center gap-1 sm:gap-3">
            <LanguageToggle />
            <ThemeToggle />
            <Link
              to="/signin"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            >
              <StableText i18nKey="signIn" />
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col justify-center px-4 pt-6 pb-10 sm:px-6 sm:pt-8 sm:pb-12">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-balance sm:text-5xl">
            {t('hero.title')}
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            {t('hero.subtitle')}
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            {isAuthenticated ? (
              <LinkButton to="/dashboard" className="min-w-40">
                {tc('goToDashboard')}
              </LinkButton>
            ) : (
              <LinkButton to="/signup" className="min-w-40">
                {tc('getStartedFree')}
              </LinkButton>
            )}
          </div>
        </div>

        <div className="mx-auto mt-6 max-w-4xl">
          <Carousel slides={heroSlides} />
        </div>
      </section>

      <section className="bg-gray-50 py-20 dark:bg-gray-800/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              {t('featuresTitle')}
            </h2>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURE_ITEMS.map(({ icon: FeatureIcon, key }) => (
              <div key={key}>
                <div className="flex size-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                  <FeatureIcon className="size-5" />
                </div>
                <h3 className="mt-4 font-semibold text-gray-900 dark:text-gray-100">
                  {t(`features.${key}.title`)}
                </h3>
                <p className="mt-1.5 text-sm text-gray-600 dark:text-gray-400">
                  {t(`features.${key}.description`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <div className="flex flex-col gap-24 sm:gap-28">
          <ShowcaseRow
            title={t('showcase.projects.title')}
            description={t('showcase.projects.description')}
          >
            <ScreenshotCard
              src={img('Projects-2')}
              alt={t('showcase.projects.alt')}
              onZoom={onZoom}
            />
          </ShowcaseRow>

          <ShowcaseRow
            title={t('showcase.timers.title')}
            description={t('showcase.timers.description')}
            reverse
          >
            <ScreenshotCard
              src={img('Timers-2')}
              alt={t('showcase.timers.alt')}
              onZoom={onZoom}
            />
          </ShowcaseRow>

          <ShowcaseRow
            title={t('showcase.reports.title')}
            description={t('showcase.reports.description')}
          >
            <ScreenshotCard
              src={img('Reports')}
              alt={t('showcase.reports.alt')}
              onZoom={onZoom}
            />
          </ShowcaseRow>

          <ShowcaseRow
            title={t('showcase.api.title')}
            description={t('showcase.api.description')}
            reverse
            action={
              <a
                href="/api/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                {t('showcase.api.cta')}
              </a>
            }
          >
            <ScreenshotCard
              src={`/img/home/API-docs-${isDark ? 'dark' : 'light'}.png`}
              alt={t('showcase.api.alt')}
              onZoom={onZoom}
            />
          </ShowcaseRow>
        </div>
      </section>

      <section className="bg-gray-50 dark:bg-gray-800/40">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight">
            {t('openSource.title')}
          </h2>
          <p className="mx-auto mt-3 max-w-4xl text-gray-600 dark:text-gray-400">
            {t('openSource.description')}
          </p>
          <div className="mt-8 flex justify-center">
            <a
              href="https://github.com/andprov/timegrip"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              {t('openSource.cta')}
            </a>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              {t('mobile.title')}
            </h2>
            <p className="mt-3 text-gray-600 sm:whitespace-nowrap dark:text-gray-400">
              {t('mobile.subtitle')}
            </p>
          </div>
          <div className="mx-auto mt-12 grid max-w-3xl grid-cols-2 gap-4 sm:grid-cols-4">
            {mobileShots.map(({ src, alt }) =>
              onZoom ? (
                <button
                  key={src}
                  type="button"
                  onClick={() => onZoom(src, alt)}
                  className="block cursor-zoom-in overflow-hidden rounded-xl bg-white shadow-lg ring-1 ring-gray-200 transition hover:opacity-90 dark:bg-gray-800 dark:ring-gray-700"
                >
                  <img src={src} alt={alt} className="w-full" loading="lazy" />
                </button>
              ) : (
                <div
                  key={src}
                  className="block overflow-hidden rounded-xl bg-white shadow-lg ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700"
                >
                  <img src={src} alt={alt} className="w-full" loading="lazy" />
                </div>
              ),
            )}
          </div>
        </div>
      </section>

      <section>
        <div className="mx-auto max-w-6xl px-4 py-20 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight">
            {t('cta.title')}
          </h2>
          <p className="mt-3 text-gray-600 dark:text-gray-400">
            {t('cta.subtitle')}
          </p>
          <div className="mt-6">
            {isAuthenticated ? (
              <LinkButton to="/dashboard" className="min-w-40">
                {tc('goToDashboard')}
              </LinkButton>
            ) : (
              <LinkButton to="/signup" className="min-w-40">
                {tc('getStartedFree')}
              </LinkButton>
            )}
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-200 dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <div className="flex flex-col items-center gap-8 sm:grid sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] sm:items-center">
            <div className="flex flex-col items-center gap-2 sm:items-start">
              <span className="flex items-center gap-1.5 font-semibold">
                <AppLogo className="size-5" />
                TimeGrip
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {t('footer.copyright', { year: new Date().getFullYear() })}
              </p>
            </div>

            <a
              href="https://github.com/andprov/timegrip"
              target="_blank"
              rel="noopener noreferrer"
              aria-label={tc('github')}
              className="text-gray-600 hover:text-gray-900 sm:justify-self-center dark:text-gray-400 dark:hover:text-gray-100"
            >
              <IconGitHub className="size-6" />
            </a>

            <nav className="flex items-center gap-x-6 text-sm text-gray-600 sm:justify-self-end dark:text-gray-400">
              <a
                href="/api/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 dark:hover:text-gray-100"
              >
                <StableText i18nKey="apiDocs" />
              </a>
            </nav>
          </div>
        </div>
      </footer>

      <Lightbox image={lightboxImage} onClose={() => setLightboxImage(null)} />
    </div>
  )
}
