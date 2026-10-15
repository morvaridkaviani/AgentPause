import clsx from "clsx";
import type { ReactNode } from "react";

export function Stat({ label, value, sub, className }: { label: string; value: ReactNode; sub?: ReactNode; className?: string }) {
  return (
    <div className={clsx("rounded-xl border border-line bg-surface px-4 py-3", className)}>
      <p className="text-xs font-medium text-ink-2">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
      {sub ? <p className="mt-0.5 text-xs text-ink-3">{sub}</p> : null}
    </div>
  );
}

/** A horizontal meter for values in [0, 1]. The track is a lighter step of the fill's hue. */
export function Meter({ value, label, threshold, color = "var(--accent)", className }: { value: number; label: string; threshold?: number; color?: string; className?: string }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className={clsx("relative h-2 w-full rounded-full", className)} style={{ background: `color-mix(in oklab, ${color} 18%, transparent)` }}>
      <div
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={1}
        aria-valuenow={Number(value.toFixed(3))}
        className="h-2 rounded-full transition-[width] duration-300"
        style={{ width: `${pct}%`, background: color }}
      />
      {threshold !== undefined ? (
        <div aria-hidden className="absolute -top-1 h-4 w-0.5 rounded bg-ink" style={{ left: `calc(${threshold * 100}% - 1px)` }} />
      ) : null}
    </div>
  );
}
