"use client";

import clsx from "clsx";
import { useId, type KeyboardEvent, type ReactNode } from "react";

export function Field({ label, hint, children, className }: { label: ReactNode; hint?: ReactNode; children: (id: string) => ReactNode; className?: string }) {
  const id = useId();
  return (
    <div className={clsx("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      {children(id)}
      {hint ? <p className="text-xs text-ink-3">{hint}</p> : null}
    </div>
  );
}

export function Select<T extends string>({
  id,
  value,
  onChange,
  options,
  className,
  ariaLabel,
}: {
  id?: string;
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
  className?: string;
  ariaLabel?: string;
}) {
  return (
    <select
      id={id}
      aria-label={ariaLabel}
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className={clsx(
        "h-10 w-full rounded-lg border border-line-strong bg-surface px-3 text-sm text-ink focus-visible:outline-2",
        className,
      )}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export function TextInput({
  id,
  value,
  onChange,
  placeholder,
  type = "text",
  className,
  ariaLabel,
}: {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  className?: string;
  ariaLabel?: string;
}) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      aria-label={ariaLabel}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={clsx("h-10 w-full rounded-lg border border-line-strong bg-surface px-3 text-sm text-ink placeholder:text-ink-3", className)}
    />
  );
}

export function Slider({
  label,
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.01,
  format = (v: number) => v.toFixed(2),
  hint,
  tag,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  format?: (v: number) => string;
  hint?: string;
  tag?: ReactNode;
}) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={id} className="flex items-center gap-2 text-sm font-medium text-ink">
          {label}
          {tag}
        </label>
        <output htmlFor={id} className="tabular text-sm text-ink-2">
          {format(value)}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer accent-[var(--accent)]"
      />
      {hint ? <p className="text-xs text-ink-3">{hint}</p> : null}
    </div>
  );
}

export function Toggle({ label, checked, onChange, description }: { label: string; checked: boolean; onChange: (v: boolean) => void; description?: string }) {
  const id = useId();
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <label htmlFor={id} className="text-sm font-medium text-ink">
          {label}
        </label>
        {description ? <p className="text-xs text-ink-3">{description}</p> : null}
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={clsx(
          "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border transition-colors",
          checked ? "border-accent bg-accent" : "border-line-strong bg-surface-3",
        )}
      >
        <span
          aria-hidden
          className={clsx(
            "inline-block size-4 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-6" : "translate-x-1",
          )}
        />
      </button>
    </div>
  );
}

export function Segmented<T extends string>({
  value,
  onChange,
  options,
  ariaLabel,
  size = "md",
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: ReactNode }[];
  ariaLabel: string;
  size?: "sm" | "md";
}) {
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const index = options.findIndex((o) => o.value === value);
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      onChange(options[(index + 1) % options.length]!.value);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      onChange(options[(index - 1 + options.length) % options.length]!.value);
    }
  };
  return (
    <div role="radiogroup" aria-label={ariaLabel} onKeyDown={onKey} className="inline-flex flex-wrap rounded-lg border border-line bg-surface-2 p-0.5">
      {options.map((o) => {
        const selected = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(o.value)}
            className={clsx(
              "rounded-md font-medium transition-colors",
              size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm",
              selected ? "bg-surface text-ink shadow-sm" : "text-ink-2 hover:text-ink",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function CheckboxChips<T extends string>({
  values,
  onChange,
  options,
  ariaLabel,
}: {
  values: T[];
  onChange: (values: T[]) => void;
  options: { value: T; label: string }[];
  ariaLabel: string;
}) {
  return (
    <div role="group" aria-label={ariaLabel} className="flex flex-wrap gap-2">
      {options.map((o) => {
        const checked = values.includes(o.value);
        return (
          <button
            key={o.value}
            type="button"
            role="checkbox"
            aria-checked={checked}
            onClick={() => onChange(checked ? values.filter((v) => v !== o.value) : [...values, o.value])}
            className={clsx(
              "rounded-full border px-3 py-1 text-sm transition-colors",
              checked ? "border-accent bg-accent-soft text-accent-strong" : "border-line-strong text-ink-2 hover:bg-surface-2",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
