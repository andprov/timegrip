import fs from 'node:fs'
import path from 'node:path'

import type { HtmlTagDescriptor, Plugin } from 'vite'

// Deployment-specific SEO for the landing page. The SPA ships a single
// index.html, so everything crawlers without JS (and link previews) can see
// has to be baked into it at build time — hence a Vite plugin fed by a JSON
// file that each instance keeps outside of git (see seo.config.example.json).

export interface SeoConfig {
  // Public origin, e.g. "https://timegrip.example.com". Used for canonical,
  // og:url, absolute image URLs, sitemap.xml and the Sitemap line in robots.txt.
  siteUrl: string
  // false → noindex meta, "Disallow: /" in robots.txt and no sitemap.
  indexing: boolean
  lang?: string
  title: string
  description?: string
  keywords?: string[]
  siteName?: string
  // Path under public/ or an absolute URL.
  image?: string
  imageAlt?: string
  twitterSite?: string
  // Extra <meta name content>, e.g. search engine verification codes.
  meta?: Record<string, string>
  // Paths hidden from crawlers in robots.txt.
  disallow?: string[]
  // Emitted as-is into <script type="application/ld+json">.
  structuredData?: unknown
}

const DEFAULT_CONFIG_FILE = 'seo.config.json'

function fail(file: string, message: string): never {
  throw new Error(`[seo] ${file}: ${message}`)
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function validate(raw: unknown, file: string): SeoConfig {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    fail(file, 'root must be an object')
  }
  const c = raw as Record<string, unknown>

  if (typeof c.siteUrl !== 'string' || !URL.canParse(c.siteUrl)) {
    fail(file, '"siteUrl" must be an absolute URL')
  }
  if (typeof c.indexing !== 'boolean') fail(file, '"indexing" must be a boolean')
  if (typeof c.title !== 'string' || !c.title) fail(file, '"title" is required')

  for (const key of ['lang', 'description', 'siteName', 'image', 'imageAlt', 'twitterSite']) {
    if (c[key] !== undefined && typeof c[key] !== 'string') {
      fail(file, `"${key}" must be a string`)
    }
  }
  for (const key of ['keywords', 'disallow']) {
    if (c[key] !== undefined && !isStringArray(c[key])) {
      fail(file, `"${key}" must be an array of strings`)
    }
  }
  if (
    c.meta !== undefined &&
    (typeof c.meta !== 'object' ||
      c.meta === null ||
      !Object.values(c.meta).every((v) => typeof v === 'string'))
  ) {
    fail(file, '"meta" must be an object of strings')
  }

  return { ...(c as unknown as SeoConfig), siteUrl: c.siteUrl.replace(/\/+$/, '') }
}

function loadConfig(root: string): SeoConfig | null {
  const explicit = process.env.SEO_CONFIG
  const file = path.resolve(root, explicit ?? DEFAULT_CONFIG_FILE)

  if (!fs.existsSync(file)) {
    if (explicit) fail(file, 'file not found (set via SEO_CONFIG)')
    return null
  }

  let raw: unknown
  try {
    raw = JSON.parse(fs.readFileSync(file, 'utf8'))
  } catch (e) {
    fail(file, `invalid JSON: ${(e as Error).message}`)
  }
  return validate(raw, file)
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function absoluteUrl(config: SeoConfig, value: string): string {
  return new URL(value, `${config.siteUrl}/`).href
}

function metaName(name: string, content: string): HtmlTagDescriptor {
  return { tag: 'meta', attrs: { name, content }, injectTo: 'head' }
}

function metaProperty(property: string, content: string): HtmlTagDescriptor {
  return { tag: 'meta', attrs: { property, content }, injectTo: 'head' }
}

function headTags(config: SeoConfig): HtmlTagDescriptor[] {
  const pageUrl = `${config.siteUrl}/`
  const image = config.image && absoluteUrl(config, config.image)
  const tags: HtmlTagDescriptor[] = []

  if (config.description) tags.push(metaName('description', config.description))
  if (config.keywords?.length) tags.push(metaName('keywords', config.keywords.join(', ')))
  tags.push(metaName('robots', config.indexing ? 'index, follow' : 'noindex, nofollow'))
  tags.push({ tag: 'link', attrs: { rel: 'canonical', href: pageUrl }, injectTo: 'head' })

  tags.push(metaProperty('og:type', 'website'))
  tags.push(metaProperty('og:url', pageUrl))
  tags.push(metaProperty('og:title', config.title))
  if (config.description) tags.push(metaProperty('og:description', config.description))
  if (config.siteName) tags.push(metaProperty('og:site_name', config.siteName))
  if (config.lang) tags.push(metaProperty('og:locale', config.lang.replace('-', '_')))
  if (image) {
    tags.push(metaProperty('og:image', image))
    if (config.imageAlt) tags.push(metaProperty('og:image:alt', config.imageAlt))
  }

  tags.push(metaName('twitter:card', image ? 'summary_large_image' : 'summary'))
  if (config.twitterSite) tags.push(metaName('twitter:site', config.twitterSite))

  for (const [name, content] of Object.entries(config.meta ?? {})) {
    if (content) tags.push(metaName(name, content))
  }

  if (config.structuredData !== undefined) {
    tags.push({
      tag: 'script',
      attrs: { type: 'application/ld+json' },
      // "<" is escaped so a string value can never close the <script> early.
      children: JSON.stringify(config.structuredData).replace(/</g, '\\u003c'),
      injectTo: 'head',
    })
  }

  return tags
}

function robotsTxt(config: SeoConfig): string {
  if (!config.indexing) return 'User-agent: *\nDisallow: /\n'

  const lines = ['User-agent: *', ...(config.disallow ?? []).map((p) => `Disallow: ${p}`)]
  if (lines.length === 1) lines.push('Allow: /')
  lines.push('', `Sitemap: ${config.siteUrl}/sitemap.xml`)
  return `${lines.join('\n')}\n`
}

function sitemapXml(config: SeoConfig): string {
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    `  <url><loc>${escapeHtml(`${config.siteUrl}/`)}</loc></url>`,
    '</urlset>',
    '',
  ].join('\n')
}

export function seo(): Plugin {
  let root = process.cwd()

  return {
    name: 'timegrip-seo',

    configResolved(resolved) {
      root = resolved.root
      const config = loadConfig(root)
      resolved.logger.info(
        config
          ? `[seo] using ${process.env.SEO_CONFIG ?? DEFAULT_CONFIG_FILE}`
          : `[seo] ${DEFAULT_CONFIG_FILE} not found, SEO tags are skipped`,
      )
    },

    // Re-read on every request so config edits show up on reload in dev.
    transformIndexHtml(html) {
      const config = loadConfig(root)
      if (!config) return html

      let result = html.replace(
        /<title>[\s\S]*?<\/title>/,
        `<title>${escapeHtml(config.title)}</title>`,
      )
      if (config.lang) {
        result = result.replace(/<html lang="[^"]*"/, `<html lang="${escapeHtml(config.lang)}"`)
      }
      return { html: result, tags: headTags(config) }
    },

    generateBundle() {
      const config = loadConfig(root)
      if (!config) return

      this.emitFile({ type: 'asset', fileName: 'robots.txt', source: robotsTxt(config) })
      if (config.indexing) {
        this.emitFile({ type: 'asset', fileName: 'sitemap.xml', source: sitemapXml(config) })
      }
    },
  }
}
