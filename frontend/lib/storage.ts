/** Per-browser conveniences (remembered preferences, study progress). Every access is guarded:
 * storage can be unavailable (private windows, blocked site data), and the app must still work. */

export function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? ({ ...fallbackObject(fallback), ...JSON.parse(raw) } as T) : fallback;
  } catch {
    return fallback;
  }
}

function fallbackObject<T>(fallback: T): object {
  return typeof fallback === "object" && fallback !== null && !Array.isArray(fallback) ? fallback : {};
}

export function save(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore: preferences then last for this page view only */
  }
}

export function remove(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}
