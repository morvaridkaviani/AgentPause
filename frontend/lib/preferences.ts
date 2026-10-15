import { useSyncExternalStore } from "react";

import { load, save } from "./storage";
import type { Preferences } from "./types";

export const PREFERENCES_KEY = "agentpause.preferences";

export const DEFAULT_PREFERENCES: Preferences = {
  profile: "balanced",
  always_ask_categories: [],
  never_ask_categories: [],
  block_categories: [],
  ask_before_irreversible: false,
  ask_before_external: false,
  allow_low_risk_autonomy: false,
  low_risk_threshold: 0.15,
  max_interruptions_per_task: null,
};

export const PROFILES: { id: Preferences["profile"]; title: string; description: string; multiplier: string }[] = [
  {
    id: "fewer_interruptions",
    title: "Fewer interruptions",
    description: "The assistant acts more on its own and asks only when it really matters.",
    multiplier: "×2.5",
  },
  {
    id: "balanced",
    title: "Balanced",
    description: "A middle ground between your time and the risk of mistakes.",
    multiplier: "×1",
  },
  {
    id: "maximum_control",
    title: "Maximum control",
    description: "The assistant checks with you much more often.",
    multiplier: "×0.25",
  },
];

export function loadPreferences(): Preferences {
  return load<Preferences>(PREFERENCES_KEY, DEFAULT_PREFERENCES);
}

export function savePreferences(preferences: Preferences): void {
  save(PREFERENCES_KEY, preferences);
}

// A tiny external store so components read preferences without setState-in-effect and
// without hydration mismatches (the server always renders the defaults). The in-memory
// copy keeps edits working for the page view when storage is unavailable.
let current: Preferences | null = null;
const listeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  const onStorage = (event: StorageEvent) => {
    if (event.key !== PREFERENCES_KEY) return;
    current = null;
    listener();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function getSnapshot(): Preferences {
  current ??= loadPreferences();
  return current;
}

function getServerSnapshot(): Preferences {
  return DEFAULT_PREFERENCES;
}

export function storePreferences(preferences: Preferences): void {
  current = preferences;
  savePreferences(preferences);
  for (const listener of listeners) listener();
}

/** The user's saved preferences (defaults during server rendering) and a setter that persists them. */
export function usePreferences(): [Preferences, (preferences: Preferences) => void] {
  return [useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot), storePreferences];
}

export function describePreferences(p: Preferences): string[] {
  const out: string[] = [PROFILES.find((x) => x.id === p.profile)?.title ?? p.profile];
  if (p.ask_before_external) out.push("Ask before external communication");
  if (p.ask_before_irreversible) out.push("Ask before irreversible actions");
  if (p.allow_low_risk_autonomy) out.push("Allow low-risk actions autonomously");
  if (p.always_ask_categories.length) out.push(`Always ask: ${p.always_ask_categories.length} categories`);
  if (p.never_ask_categories.length) out.push(`Never ask: ${p.never_ask_categories.length} categories`);
  if (p.block_categories.length) out.push(`Blocked: ${p.block_categories.length} categories`);
  if (p.max_interruptions_per_task !== null) out.push(`At most ${p.max_interruptions_per_task} interruptions per task`);
  return out;
}
