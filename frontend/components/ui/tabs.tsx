"use client";

import clsx from "clsx";
import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

export interface TabItem<T extends string> {
  id: T;
  label: ReactNode;
}

/** Accessible tabs (WAI-ARIA pattern: roving tabindex, arrow keys, Home/End). */
export function Tabs<T extends string>({
  tabs,
  value,
  onChange,
  children,
  ariaLabel,
}: {
  tabs: TabItem<T>[];
  value: T;
  onChange: (value: T) => void;
  children: ReactNode;
  ariaLabel: string;
}) {
  const base = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const index = tabs.findIndex((t) => t.id === value);
    let next = index;
    if (e.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (e.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabs.length - 1;
    else return;
    e.preventDefault();
    onChange(tabs[next]!.id);
    refs.current[next]?.focus();
  };
  return (
    <div>
      <div role="tablist" aria-label={ariaLabel} onKeyDown={onKey} className="flex gap-1 overflow-x-auto border-b border-line">
        {tabs.map((tab, i) => {
          const selected = tab.id === value;
          return (
            <button
              key={tab.id}
              ref={(el) => {
                refs.current[i] = el;
              }}
              id={`${base}-tab-${tab.id}`}
              role="tab"
              type="button"
              aria-selected={selected}
              aria-controls={`${base}-panel`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(tab.id)}
              className={clsx(
                "-mb-px border-b-2 px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
                selected ? "border-accent text-ink" : "border-transparent text-ink-2 hover:text-ink",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div id={`${base}-panel`} role="tabpanel" aria-labelledby={`${base}-tab-${value}`} className="pt-4">
        {children}
      </div>
    </div>
  );
}
