export const THEME_KEY = "agentpause.theme";

/** Inline script run before paint so the page never flashes the wrong theme. */
export const THEME_SCRIPT = `(() => { try { const t = localStorage.getItem("${THEME_KEY}") || "system"; const dark = t === "dark" || (t === "system" && matchMedia("(prefers-color-scheme: dark)").matches); document.documentElement.classList.toggle("dark", dark); document.documentElement.dataset.theme = dark ? "dark" : "light"; } catch (e) {} })();`;
