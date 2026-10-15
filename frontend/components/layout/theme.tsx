"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useCallback, useSyncExternalStore } from "react";

import { THEME_KEY as KEY } from "./theme-script";

type Theme = "light" | "dark" | "system";

function read(): Theme {
  try {
    return (localStorage.getItem(KEY) as Theme | null) ?? "system";
  } catch {
    return "system";
  }
}

function apply(theme: Theme): void {
  const dark = theme === "dark" || (theme === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}

const listeners = new Set<() => void>();
function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, read, () => "system" as Theme);
  const cycle = useCallback(() => {
    const next: Theme = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* ignore */
    }
    apply(next);
    listeners.forEach((l) => l());
  }, [theme]);
  const Icon = theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;
  const label = `Theme: ${theme}. Switch theme`;
  return (
    <button
      type="button"
      onClick={cycle}
      aria-label={label}
      title={label}
      className="inline-flex size-9 items-center justify-center rounded-lg text-ink-2 hover:bg-surface-2 hover:text-ink"
    >
      <Icon className="size-4" aria-hidden />
    </button>
  );
}
