// Fixed locale collator: `localeCompare()` without a locale argument falls
// back to the runtime's default locale, whose script ordering (e.g. Latin vs
// Cyrillic) can differ between devices/browsers, producing inconsistent
// sort order for the same data.
const collator = new Intl.Collator('en')

export function compareNames(a: string, b: string): number {
  return collator.compare(a, b)
}
