/** Public source repository. Override with NEXT_PUBLIC_REPO_URL (e.g. for a fork). */
export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL || "https://github.com/morvaridkaviani/AgentPause";

/** True in the static online demo (GitHub Pages), where the API runs in the browser. */
export const STATIC_DEMO = process.env.NEXT_PUBLIC_STATIC_DEMO === "1";

/** Path prefix of the static site (e.g. "/AgentPause" on GitHub Pages). */
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

/** Interactive OpenAPI docs come from the server; the static demo links to the Markdown reference. */
export const API_DOCS_URL = STATIC_DEMO ? `${REPO_URL}/blob/main/docs/api.md` : "/docs";
