/** Errors raised by the AgentPause HTTP client. */

/**
 * The AgentPause API returned an error, or could not be reached.
 *
 * `status` is the HTTP status code (0 when no response was received). `detail` is the
 * server's `detail` field: a string for most errors, or a list of validation errors
 * (`{ loc, msg, type }`) for 422 responses.
 */
export class AgentPauseError extends Error {
  override name = "AgentPauseError";
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown, options: { message?: string; cause?: unknown } = {}) {
    super(
      options.message ?? `AgentPause API error ${status}: ${formatDetail(detail) || "request failed"}`,
      options.cause === undefined ? undefined : { cause: options.cause },
    );
    this.status = status;
    this.detail = detail;
  }
}

/** A request (or a wait such as `waitForExperiment`) did not complete within its time limit. */
export class AgentPauseTimeoutError extends AgentPauseError {
  override name = "AgentPauseTimeoutError";
  readonly timeoutMs: number;

  constructor(timeoutMs: number, detail: string, options: { cause?: unknown } = {}) {
    super(0, detail, { message: `AgentPause timeout: ${detail}`, cause: options.cause });
    this.timeoutMs = timeoutMs;
  }
}

/** The server could not be reached (DNS failure, connection refused, CORS, ...). */
export class AgentPauseConnectionError extends AgentPauseError {
  override name = "AgentPauseConnectionError";

  constructor(url: string, cause: unknown) {
    const reason = cause instanceof Error ? cause.message : String(cause);
    const detail = `Could not reach ${url}: ${reason}`;
    super(0, detail, { message: `AgentPause connection error: ${detail}`, cause });
  }
}

/** Render a FastAPI `detail` value (string, validation error list, or object) as text. */
export function formatDetail(detail: unknown): string {
  if (detail === null || detail === undefined) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const { loc, msg } = item as { loc?: unknown; msg: unknown };
          const where = Array.isArray(loc) ? loc.join(".") : "";
          return where ? `${where}: ${String(msg)}` : String(msg);
        }
        return typeof item === "string" ? item : JSON.stringify(item);
      })
      .join("; ");
  }
  if (typeof detail === "object") return JSON.stringify(detail);
  return String(detail);
}
