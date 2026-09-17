import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

export const SUPPORTED_LOCALES = ['en', 'ru'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

const STORAGE_KEY = 'timegrip-locale'

function isSupportedLocale(value: string | null): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value ?? '')
}

function detectBrowserLocale(): Locale {
  return navigator.language.toLowerCase().startsWith('ru') ? 'ru' : 'en'
}

export function resolveInitialLocale(): Locale {
  const stored = localStorage.getItem(STORAGE_KEY)
  return isSupportedLocale(stored) ? stored : detectBrowserLocale()
}

export function storeLocale(locale: Locale): void {
  localStorage.setItem(STORAGE_KEY, locale)
}

const localeModules = import.meta.glob<{ default: Record<string, unknown> }>(
  './locales/*/*.json',
  { eager: true },
)

const resources: Record<string, Record<string, Record<string, unknown>>> = {}
const namespaces = new Set<string>()

for (const path in localeModules) {
  const match = /\.\/locales\/([a-z]{2})\/([\w-]+)\.json$/.exec(path)
  if (!match) continue
  const [, locale, ns] = match
  resources[locale] ??= {}
  resources[locale][ns] = localeModules[path].default
  namespaces.add(ns)
}

void i18n.use(initReactI18next).init({
  resources,
  lng: resolveInitialLocale(),
  fallbackLng: 'en',
  ns: [...namespaces],
  defaultNS: 'common',
  interpolation: { escapeValue: false },
})

export default i18n
