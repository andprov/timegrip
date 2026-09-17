export function AppLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M13.34 1.08 A11 11 0 0 1 22.92 10.66 L19.34 11.1 A7.4 7.4 0 0 0 12.9 4.66 Z" fill="#EA4335" />
      <path d="M22.92 13.34 A11 11 0 0 1 13.34 22.92 L12.9 19.34 A7.4 7.4 0 0 0 19.34 12.9 Z" fill="#4285F4" />
      <path d="M10.66 22.92 A11 11 0 0 1 1.08 13.34 L4.66 12.9 A7.4 7.4 0 0 0 11.1 19.34 Z" fill="#FBBC04" />
      <path d="M1.08 10.66 A11 11 0 0 1 10.66 1.08 L11.1 4.66 A7.4 7.4 0 0 0 4.66 11.1 Z" fill="#34A853" />
      <g stroke="currentColor" strokeWidth={1.6} strokeLinecap="round">
        <line x1={12} y1={12} x2={17.77} y2={8.67} />
        <line x1={12} y1={12} x2={8.41} y2={9.93} />
      </g>
      <circle cx={12} cy={12} r={1.1} fill="currentColor" />
    </svg>
  )
}
