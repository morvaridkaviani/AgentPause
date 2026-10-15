/** The AgentPause mark: a pause glyph inside a decision node. */
export function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden focusable="false">
      <rect x="1.5" y="1.5" width="29" height="29" rx="8" fill="var(--accent)" />
      <rect x="10" y="9" width="4" height="14" rx="1.5" fill="var(--accent-ink)" />
      <rect x="18" y="9" width="4" height="14" rx="1.5" fill="var(--accent-ink)" />
    </svg>
  );
}
