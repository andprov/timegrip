import type { TokenPair } from '@/api/types'
import i18n from '@/i18n/config'

const ACCESS_TOKEN_KEY = 'timegrip_access_token'
const REFRESH_TOKEN_KEY = 'timegrip_refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

const LOCATION_PARTS = ['body', 'query', 'path', 'header', 'cookie']

export class ApiError extends Error {
  status: number
  code?: string

  constructor(status: number, detail: string, code?: string) {
    super(detail)
    this.status = status
    this.code = code
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  query?: Record<string, string | number | boolean | string[] | undefined>
}

function buildQuery(query?: RequestOptions['query']): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined) continue
    if (Array.isArray(value)) {
      for (const item of value) params.append(key, item)
    } else {
      params.set(key, String(value))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

// Endpoints that must never trigger a refresh-and-retry themselves,
// otherwise a failed signin/signup/refresh would loop back into refresh.
const AUTH_ENDPOINTS_WITHOUT_RETRY = [
  '/auth/signin',
  '/auth/signup',
  '/auth/refresh',
]

// Only one refresh call may be in flight per tab at a time. Every
// request that hits a 401 concurrently must await this same promise
// instead of starting its own refresh — otherwise two parallel
// refreshes race on the same refresh token, and the loser looks like a
// reused (stolen) token to the backend.
let refreshPromise: Promise<boolean> | null = null

async function refreshSession(): Promise<boolean> {
  if (refreshPromise === null) {
    refreshPromise = (async () => {
      const refreshToken = getRefreshToken()
      if (!refreshToken) return false

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) return false

      const tokens = (await response.json()) as TokenPair
      setTokens(tokens)
      return true
    })()
      .catch(() => false)
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

async function rawFetch(
  path: string,
  options: RequestOptions,
): Promise<Response> {
  const headers: Record<string, string> = {}
  const accessToken = getAccessToken()
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  let body: string | undefined
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }

  return fetch(`/api${path}${buildQuery(options.query)}`, {
    method: options.method ?? 'GET',
    headers,
    body,
  })
}

interface ValidationErrorItem {
  loc?: unknown[]
  msg?: unknown
  type?: unknown
}

// Pydantic reports a machine-readable `type` per failed field; a field-specific
// key wins over the generic one, and the English `msg` stays as the fallback.
function formatValidationError(item: ValidationErrorItem): string | null {
  if (typeof item.msg !== 'string') return null

  const field = item.loc?.findLast(
    (part) => typeof part === 'string' && !LOCATION_PARTS.includes(part),
  )
  if (typeof item.type !== 'string') {
    return field ? `${String(field)}: ${item.msg}` : item.msg
  }

  const keys = field
    ? [`validation.${String(field)}.${item.type}`, `validation.${item.type}`]
    : [`validation.${item.type}`]
  const translated = i18n.t(keys, { ns: 'errors', defaultValue: '' })
  if (translated) return translated

  return field ? `${String(field)}: ${item.msg}` : item.msg
}

function extractDetail(data: unknown): string | null {
  if (!data || typeof data !== 'object' || !('detail' in data)) return null

  const detail = (data as { detail: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return formatValidationError(detail[0] as ValidationErrorItem)
  }

  return null
}

function extractCode(data: unknown): string | undefined {
  if (!data || typeof data !== 'object' || !('code' in data)) return undefined

  const code = (data as { code: unknown }).code
  return typeof code === 'string' ? code : undefined
}

const GATEWAY_STATUSES = [502, 503, 504]
const TOO_MANY_REQUESTS_STATUS = 429

// A response without a JSON body (the proxy rate limiting a client or
// answering for a backend that is down, or an unhandled crash) only carries
// the untranslated statusText.
function genericErrorMessage(status: number): string {
  if (status === TOO_MANY_REQUESTS_STATUS) {
    return i18n.t('too_many_requests', { ns: 'errors' })
  }
  return GATEWAY_STATUSES.includes(status)
    ? i18n.t('server_unavailable', { ns: 'errors' })
    : i18n.t('somethingWentWrong', { ns: 'common' })
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const fallback = extractDetail(data) ?? genericErrorMessage(response.status)
    const code = extractCode(data)
    throw new ApiError(
      response.status,
      code ? i18n.t(code, { ns: 'errors', defaultValue: fallback }) : fallback,
      code,
    )
  }

  return data as T
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await rawFetch(path, options)

  if (
    response.status === 401 &&
    !AUTH_ENDPOINTS_WITHOUT_RETRY.includes(path)
  ) {
    const refreshed = await refreshSession()
    if (refreshed) {
      const retryResponse = await rawFetch(path, options)
      return parseResponse<T>(retryResponse)
    }
  }

  return parseResponse<T>(response)
}
