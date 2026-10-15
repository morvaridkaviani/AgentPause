import { useSyncExternalStore } from "react";

import { load, save } from "./storage";

/** "simple" hides model internals (scores, factors, reason codes); "detailed" shows everything. */
export type ViewMode = "simple" | "detailed";

const KEY = "agentpause.view";
let current: ViewMode | null = null;
const listeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): ViewMode {
  current ??= load<{ mode?: string }>(KEY, {}).mode === "detailed" ? "detailed" : "simple";
  return current;
}

function getServerSnapshot(): ViewMode {
  return "simple";
}

export function setViewMode(mode: ViewMode): void {
  current = mode;
  save(KEY, { mode });
  for (const listener of listeners) listener();
}

/** The remembered view mode (simple by default) and a setter that persists it in this browser. */
export function useViewMode(): [ViewMode, (mode: ViewMode) => void] {
  return [useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot), setViewMode];
}
