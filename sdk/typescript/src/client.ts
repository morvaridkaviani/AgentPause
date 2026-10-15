/** Typed HTTP client for an AgentPause server (`uvicorn app.main:app`). No runtime dependencies. */

import { AgentPauseConnectionError, AgentPauseError, AgentPauseTimeoutError } from "./errors.js";
import { SseParser } from "./sse.js";
import type {
  ActionContextInput,
  ActionRequest,
  ActionResult,
  CompareInput,
  CompareResult,
  Decision,
  EvaluateRequest,
  EventFilters,
  EventList,
  Experiment,
  ExperimentCreateInput,
  ExplainLevel,
  HealthInfo,
  Instrument,
  InterventionRequest,
  Metrics,
  MetricsFilters,
  ModelInfo,
  Participant,
  ParticipantUpdate,
  PolicyInfo,
  PolicyInput,
  PreferencesInput,
  QuestionnaireInput,
  QuestionnaireResult,
  ResponseName,
  ScenarioDefinition,
  ScenarioSummary,
  Session,
  SessionCreateInput,
  SessionEvent,
  SessionFilters,
  SessionList,
  StepResult,
  StepUntil,
  StudyConfig,
} from "./types.js";

export const DEFAULT_BASE_URL = "http://localhost:8000";
export const DEFAULT_TIMEOUT_MS = 15_000;
/** Path prefix of every AgentPause endpoint. */
export const API_PREFIX = "/api/v1";

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
export type QueryValue = string | number | boolean | null | undefined;

export interface AgentPauseClientOptions {
  /** Server URL without the `/api/v1` prefix. Default `http://localhost:8000`. */
  baseUrl?: string;
  /** Researcher token (`AGENTPAUSE_ADMIN_TOKEN`), sent as `Authorization: Bearer <token>`. */
  token?: string;
  /** Custom `fetch` implementation. Default: the global `fetch` (Node.js 18+, browsers, Deno, Bun). */
  fetch?: typeof fetch;
  /** Per-request timeout in milliseconds. Default 15000. `0` disables the timeout. */
  timeoutMs?: number;
}

/** Options accepted by every endpoint method. */
export interface RequestOptions {
  /** Abort the request. An aborted request rejects with the signal's reason. */
  signal?: AbortSignal;
  /** Override the client's timeout for this request. `0` disables the timeout. */
  timeoutMs?: number;
}

/** Options of the low-level {@link AgentPauseClient.request} method. */
export interface RawRequestOptions extends RequestOptions {
  /** JSON-serialized request body. */
  body?: unknown;
  /** Query parameters; `null` and `undefined` values are omitted. */
  query?: Record<string, QueryValue>;
  /** `"json"` (default) parses the response; `"text"` returns it unparsed (CSV exports). */
  responseType?: "json" | "text";
}

/** Options of `POST /api/v1/evaluate` besides the action context. */
export interface EvaluateOptions {
  /** Policy name or specification. Default `"adaptive"`. */
  policy?: PolicyInput;
  preferences?: PreferencesInput | null;
  /** Explanation detail. Default `"full"`. */
  explain?: ExplainLevel;
  /** Optional serialized SessionState (history) to evaluate against. */
  state?: Record<string, unknown> | null;
}

export interface RespondOptions extends RequestOptions {
  /** The pending intervention's id (from `submitAction()` or the session's `pending`). Recommended: the server rejects stale ids with 409. */
  interventionId?: string | null;
  /** Clarification answers keyed by assumption id (with `response: "answer"`). */
  answers?: Record<string, string>;
}

export interface WaitForExperimentOptions extends RequestOptions {
  /** Delay between status polls. Default 1000 ms. */
  pollIntervalMs?: number;
  /** Give up (with `AgentPauseTimeoutError`) after this long. Default: wait indefinitely. */
  maxWaitMs?: number;
}

type Expect = "object" | "array" | "any";

interface SendOptions extends RequestOptions {
  body?: unknown;
  query?: Record<string, QueryValue> | undefined;
  accept: string;
}

/**
 * Talk to a running AgentPause server.
 *
 * ```ts
 * const client = new AgentPauseClient({ baseUrl: "http://localhost:8000" });
 * const decision = await client.evaluate({
 *   action: "send_email",
 *   consequence: "external_communication",
 *   reversible: false,
 *   intent_confidence: 0.72,
 * });
 * ```
 */
export class AgentPauseClient {
  readonly baseUrl: string;
  readonly timeoutMs: number;
  private readonly token: string | undefined;
  private readonly fetchImpl: typeof fetch;

  constructor(options: AgentPauseClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.token = options.token || undefined;
    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    if (!(timeoutMs >= 0)) throw new RangeError(`timeoutMs must be a non-negative number, got ${timeoutMs}`);
    this.timeoutMs = timeoutMs;
    const fetchImpl = options.fetch ?? globalThis.fetch;
    if (typeof fetchImpl !== "function") {
      throw new TypeError("No fetch implementation found: use Node.js 18+ or pass `fetch` in the client options");
    }
    this.fetchImpl = fetchImpl;
  }

  // ---------------------------------------------------------------------------- low level

  /**
   * Send a request to any endpoint. `path` includes the `/api/v1` prefix.
   * Resolves to the parsed JSON body (`undefined` for empty bodies), or the raw text with
   * `responseType: "text"`.
   */
  async request<T = unknown>(method: HttpMethod, path: string, options: RawRequestOptions = {}): Promise<T> {
    const { responseType = "json", ...rest } = options;
    const accept = responseType === "json" ? "application/json" : "*/*";
    const { status, text } = await this.send(method, path, { ...rest, accept });
    if (responseType === "text") return text as T;
    return parseJson(text, status, method, path) as T;
  }

  // ---------------------------------------------------------------------------- meta

  /** Service health (`GET /api/v1/health`). */
  health(options: RequestOptions = {}): Promise<HealthInfo> {
    return this.json("GET", `${API_PREFIX}/health`, "object", options);
  }

  /** Available intervention policies (`GET /api/v1/policies`). */
  policies(options: RequestOptions = {}): Promise<PolicyInfo[]> {
    return this.json("GET", `${API_PREFIX}/policies`, "array", options);
  }

  /** Default model parameters, category priors, reason codes and metric definitions (`GET /api/v1/model`). */
  model(options: RequestOptions = {}): Promise<ModelInfo> {
    return this.json("GET", `${API_PREFIX}/model`, "object", options);
  }

  /** Bundled simulated scenarios (`GET /api/v1/scenarios`). */
  scenarios(options: RequestOptions = {}): Promise<ScenarioSummary[]> {
    return this.json("GET", `${API_PREFIX}/scenarios`, "array", options);
  }

  /** One scenario definition (`GET /api/v1/scenarios/{scenarioId}`). */
  getScenario(scenarioId: string, options: RequestOptions = {}): Promise<ScenarioDefinition> {
    return this.json("GET", `${API_PREFIX}/scenarios/${segment(scenarioId)}`, "object", options);
  }

  // ---------------------------------------------------------------------------- evaluate

  /**
   * Stateless evaluation of one proposed action (`POST /api/v1/evaluate`). Nothing is stored.
   * Pass an action name or a full {@link ActionContextInput}.
   */
  evaluate(context: ActionContextInput | string, options: EvaluateOptions & RequestOptions = {}): Promise<Decision> {
    const { policy, preferences, explain, state, signal, timeoutMs } = options;
    const body: EvaluateRequest = {
      context: toContext(context),
      policy: policy ?? "adaptive",
      explain: explain ?? "full",
    };
    if (preferences !== undefined) body.preferences = preferences;
    if (state !== undefined) body.state = state;
    return this.json("POST", `${API_PREFIX}/evaluate`, "object", { body, signal, timeoutMs });
  }

  // ---------------------------------------------------------------------------- sessions

  /**
   * Create a session (`POST /api/v1/session`): `mode: "api"` for your own agent (then use
   * {@link submitAction}), or `mode: "demo"` with a `scenario_id` for the simulated agent.
   */
  createSession(body: SessionCreateInput, options: RequestOptions = {}): Promise<Session> {
    return this.json("POST", `${API_PREFIX}/session`, "object", { ...options, body });
  }

  /** Session state and timeline (`GET /api/v1/session/{sessionId}`). */
  getSession(sessionId: string, options: RequestOptions = {}): Promise<Session> {
    return this.json("GET", `${API_PREFIX}/session/${segment(sessionId)}`, "object", options);
  }

  /** Events of one session, optionally only those after sequence number `since` (`GET /api/v1/session/{sessionId}/events`). */
  sessionEvents(sessionId: string, options: { since?: number } & RequestOptions = {}): Promise<SessionEvent[]> {
    const { since, ...rest } = options;
    return this.json("GET", `${API_PREFIX}/session/${segment(sessionId)}/events`, "array", {
      ...rest,
      query: { since },
    });
  }

  /**
   * Advance the simulated agent of a demo/study session (`POST /api/v1/session/{sessionId}/step`).
   * `until: "intervention"` keeps stepping until a card opens or the task ends.
   */
  stepSession(sessionId: string, until: StepUntil = "next", options: RequestOptions = {}): Promise<StepResult> {
    return this.json("POST", `${API_PREFIX}/session/${segment(sessionId)}/step`, "object", {
      ...options,
      body: { until },
    });
  }

  /**
   * Submit an action proposed by your own agent in an `api` session (`POST /api/v1/action`).
   * If the decision interrupts (CLARIFY, ASK_HUMAN, BLOCK), the session waits for
   * {@link respond} with the returned `intervention_id`.
   */
  submitAction(
    sessionId: string,
    context: ActionContextInput | string,
    options: RequestOptions = {},
  ): Promise<ActionResult> {
    const body: ActionRequest = { session_id: sessionId, context: toContext(context) };
    return this.json("POST", `${API_PREFIX}/action`, "object", { ...options, body });
  }

  /**
   * Record the human's response to the pending intervention (`POST /api/v1/intervention`):
   * `approve`, `edit`, `reject`, `answer` (with `answers`), `takeover`/`override` (after BLOCK),
   * `cancel_task`, `timeout`, or `ask_why` (logged; the intervention stays pending).
   */
  respond(sessionId: string, response: ResponseName, options: RespondOptions = {}): Promise<StepResult> {
    const { interventionId, answers, ...rest } = options;
    const body: InterventionRequest = {
      session_id: sessionId,
      intervention_id: interventionId ?? null,
      response,
      answers: answers ?? {},
    };
    return this.json("POST", `${API_PREFIX}/intervention`, "object", { ...rest, body });
  }

  /** List sessions, newest first (`GET /api/v1/sessions`). Requires the researcher token when one is configured. */
  listSessions(options: SessionFilters & RequestOptions = {}): Promise<SessionList> {
    const { signal, timeoutMs, ...filters } = options;
    return this.json("GET", `${API_PREFIX}/sessions`, "object", { signal, timeoutMs, query: { ...filters } });
  }

  /** Delete a session and its events (`DELETE /api/v1/session/{sessionId}`). Requires the researcher token when one is configured. */
  async deleteSession(sessionId: string, options: RequestOptions = {}): Promise<void> {
    await this.send("DELETE", `${API_PREFIX}/session/${segment(sessionId)}`, { ...options, accept: "application/json" });
  }

  /**
   * Live session events over Server-Sent Events (`GET /api/v1/session/{sessionId}/stream`).
   * Yields each new event until the session ends or `signal` aborts. The client timeout does
   * not apply to this long-lived request.
   *
   * ```ts
   * for await (const event of client.streamSession(id)) console.log(event.type, event.decision);
   * ```
   */
  async *streamSession(
    sessionId: string,
    options: { since?: number; signal?: AbortSignal } = {},
  ): AsyncGenerator<SessionEvent, void, undefined> {
    const path = `${API_PREFIX}/session/${segment(sessionId)}/stream`;
    const url = this.url(path, { since: options.since });
    const init: RequestInit = { method: "GET", headers: this.headers("text/event-stream", false) };
    if (options.signal) init.signal = options.signal;
    const fetchImpl = this.fetchImpl;
    let response: Response;
    try {
      response = await fetchImpl(url, init);
    } catch (err) {
      if (options.signal?.aborted) throw err;
      throw new AgentPauseConnectionError(url, err);
    }
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new AgentPauseError(response.status, errorDetail(text, response.statusText));
    }
    if (!response.body) throw new AgentPauseError(response.status, `No response body from GET ${path}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const parser = new SseParser();
    try {
      for (;;) {
        const { done, value } = await reader.read();
        const text = done ? decoder.decode() : decoder.decode(value, { stream: true });
        for (const message of parser.push(text)) {
          if (message.event === "end") return;
          const event = parseJson(message.data, response.status, "GET", path);
          if (!isPlainObject(event)) {
            throw new AgentPauseError(response.status, `Expected a JSON object in event data from GET ${path}`);
          }
          yield event as unknown as SessionEvent;
        }
        if (done) return;
      }
    } finally {
      await reader.cancel().catch(() => undefined);
    }
  }

  // ---------------------------------------------------------------------------- research

  /** Filterable event log across sessions (`GET /api/v1/events`). Requires the researcher token when one is configured. */
  listEvents(options: EventFilters & RequestOptions = {}): Promise<EventList> {
    const { signal, timeoutMs, ...filters } = options;
    return this.json("GET", `${API_PREFIX}/events`, "object", { signal, timeoutMs, query: { ...filters } });
  }

  /** All matching events as CSV (`GET /api/v1/events?format=csv`). Requires the researcher token when one is configured. */
  async exportEventsCsv(options: Omit<EventFilters, "offset" | "limit"> & RequestOptions = {}): Promise<string> {
    const { signal, timeoutMs, ...filters } = options;
    const { text } = await this.send("GET", `${API_PREFIX}/events`, {
      signal,
      timeoutMs,
      query: { ...filters, format: "csv" },
      accept: "text/csv",
    });
    return text;
  }

  /**
   * Aggregated research metrics and chart data (`GET /api/v1/metrics`). `source: "experiment"`
   * (default) aggregates a stored simulation experiment; `source: "sessions"` aggregates
   * completed interactive sessions.
   */
  metrics(options: MetricsFilters & RequestOptions = {}): Promise<Metrics> {
    const { signal, timeoutMs, ...filters } = options;
    return this.json("GET", `${API_PREFIX}/metrics`, "object", { signal, timeoutMs, query: { ...filters } });
  }

  /** Quick simulated policy comparison, not stored (`POST /api/v1/compare`). */
  compare(body: CompareInput = {}, options: RequestOptions = {}): Promise<CompareResult> {
    return this.json("POST", `${API_PREFIX}/compare`, "object", { ...options, body });
  }

  /**
   * Create and start a simulation experiment (`POST /api/v1/experiments`). It runs in the
   * background: poll {@link getExperiment} or use {@link waitForExperiment}. `wait: true` runs it
   * synchronously (small experiments only).
   */
  createExperiment(
    body: ExperimentCreateInput,
    options: { wait?: boolean } & RequestOptions = {},
  ): Promise<Experiment> {
    const { wait, ...rest } = options;
    return this.json("POST", `${API_PREFIX}/experiments`, "object", { ...rest, body, query: { wait } });
  }

  /** Recent experiments (`GET /api/v1/experiments`). */
  listExperiments(options: { limit?: number } & RequestOptions = {}): Promise<Experiment[]> {
    const { limit, ...rest } = options;
    return this.json("GET", `${API_PREFIX}/experiments`, "array", { ...rest, query: { limit } });
  }

  /** Experiment status, progress and results (`GET /api/v1/experiments/{experimentId}`). */
  getExperiment(experimentId: string, options: RequestOptions = {}): Promise<Experiment> {
    return this.json("GET", `${API_PREFIX}/experiments/${segment(experimentId)}`, "object", options);
  }

  /**
   * Poll an experiment until its status is `completed` or `failed` and return it (check
   * `status` and `error`). Throws `AgentPauseTimeoutError` after `maxWaitMs`.
   */
  async waitForExperiment(experimentId: string, options: WaitForExperimentOptions = {}): Promise<Experiment> {
    const { pollIntervalMs = 1000, maxWaitMs, ...request } = options;
    const started = Date.now();
    for (;;) {
      const experiment = await this.getExperiment(experimentId, request);
      if (experiment.status === "completed" || experiment.status === "failed") return experiment;
      const elapsed = Date.now() - started;
      if (maxWaitMs !== undefined && elapsed >= maxWaitMs) {
        throw new AgentPauseTimeoutError(
          maxWaitMs,
          `Experiment ${experimentId} did not finish within ${maxWaitMs} ms (status: ${experiment.status})`,
        );
      }
      const delay = maxWaitMs === undefined ? pollIntervalMs : Math.min(pollIntervalMs, maxWaitMs - elapsed);
      await sleep(delay, request.signal);
    }
  }

  /**
   * Export experiment data as text (`GET /api/v1/experiments/{experimentId}/export`): CSV by
   * default, JSON with `format: "json"` (`table: "summary"` is always JSON). Parse JSON with
   * `JSON.parse`. Requires the researcher token when one is configured.
   */
  async exportExperiment(
    experimentId: string,
    options: { table?: "records" | "episodes" | "summary"; format?: "csv" | "json" } & RequestOptions = {},
  ): Promise<string> {
    const { table, format, ...rest } = options;
    const { text } = await this.send("GET", `${API_PREFIX}/experiments/${segment(experimentId)}/export`, {
      ...rest,
      query: { table, format },
      accept: "*/*",
    });
    return text;
  }

  /** Delete an experiment (`DELETE /api/v1/experiments/{experimentId}`). Requires the researcher token when one is configured. */
  async deleteExperiment(experimentId: string, options: RequestOptions = {}): Promise<void> {
    await this.send("DELETE", `${API_PREFIX}/experiments/${segment(experimentId)}`, {
      ...options,
      accept: "application/json",
    });
  }

  // ---------------------------------------------------------------------------- study

  /** Active study configuration (`GET /api/v1/study/config`). */
  getStudyConfig(options: RequestOptions = {}): Promise<StudyConfig> {
    return this.json("GET", `${API_PREFIX}/study/config`, "object", options);
  }

  /** Replace the study configuration (`PUT /api/v1/study/config`). Requires the researcher token when one is configured. */
  updateStudyConfig(config: StudyConfig, options: RequestOptions = {}): Promise<StudyConfig> {
    return this.json("PUT", `${API_PREFIX}/study/config`, "object", { ...options, body: config });
  }

  /** Enrol a participant with a pseudonymous code and counterbalanced plan (`POST /api/v1/study/participants`). */
  createParticipant(options: RequestOptions = {}): Promise<Participant> {
    return this.json("POST", `${API_PREFIX}/study/participants`, "object", options);
  }

  /** Participant plan and progress (`GET /api/v1/study/participants/{code}`). */
  getParticipant(code: string, options: RequestOptions = {}): Promise<Participant> {
    return this.json("GET", `${API_PREFIX}/study/participants/${segment(code)}`, "object", options);
  }

  /** Record consent or completion (`PATCH /api/v1/study/participants/{code}`). */
  updateParticipant(code: string, update: ParticipantUpdate, options: RequestOptions = {}): Promise<Participant> {
    return this.json("PATCH", `${API_PREFIX}/study/participants/${segment(code)}`, "object", {
      ...options,
      body: update,
    });
  }

  /** Start the session for one block of a participant's plan (`POST /api/v1/study/sessions`). */
  startStudySession(participantCode: string, block: number, options: RequestOptions = {}): Promise<Session> {
    return this.json("POST", `${API_PREFIX}/study/sessions`, "object", {
      ...options,
      body: { participant_code: participantCode, block },
    });
  }

  /** Questionnaire instruments (`GET /api/v1/study/instruments`). */
  instruments(options: RequestOptions = {}): Promise<Instrument[]> {
    return this.json("GET", `${API_PREFIX}/study/instruments`, "array", options);
  }

  /** Submit questionnaire responses (`POST /api/v1/study/responses`). */
  submitQuestionnaire(body: QuestionnaireInput, options: RequestOptions = {}): Promise<QuestionnaireResult> {
    return this.json("POST", `${API_PREFIX}/study/responses`, "object", { ...options, body });
  }

  /** Export questionnaire data as CSV (default) or JSON text (`GET /api/v1/study/export`). Requires the researcher token when one is configured. */
  async exportStudy(options: { format?: "csv" | "json" } & RequestOptions = {}): Promise<string> {
    const { format, ...rest } = options;
    const { text } = await this.send("GET", `${API_PREFIX}/study/export`, { ...rest, query: { format }, accept: "*/*" });
    return text;
  }

  // ---------------------------------------------------------------------------- internals

  private async json<T>(
    method: HttpMethod,
    path: string,
    expect: Expect,
    options: RequestOptions & { body?: unknown; query?: Record<string, QueryValue> },
  ): Promise<T> {
    const { status, text } = await this.send(method, path, { ...options, accept: "application/json" });
    const data = parseJson(text, status, method, path);
    if (expect === "object" && !isPlainObject(data)) {
      throw new AgentPauseError(status, `Expected a JSON object from ${method} ${path}`);
    }
    if (expect === "array" && !Array.isArray(data)) {
      throw new AgentPauseError(status, `Expected a JSON array from ${method} ${path}`);
    }
    return data as T;
  }

  private async send(method: HttpMethod, path: string, options: SendOptions): Promise<{ status: number; text: string }> {
    const url = this.url(path, options.query);
    const init: RequestInit = { method, headers: this.headers(options.accept, options.body !== undefined) };
    if (options.body !== undefined) init.body = JSON.stringify(options.body);

    const controller = new AbortController();
    init.signal = controller.signal;
    const external = options.signal;
    const onAbort = (): void => controller.abort(external?.reason);
    if (external?.aborted) controller.abort(external.reason);
    else external?.addEventListener("abort", onAbort, { once: true });

    const timeoutMs = options.timeoutMs ?? this.timeoutMs;
    let timedOut = false;
    const timer =
      timeoutMs > 0 && Number.isFinite(timeoutMs)
        ? setTimeout(() => {
            timedOut = true;
            controller.abort();
          }, timeoutMs)
        : undefined;

    const fetchImpl = this.fetchImpl;
    try {
      const response = await fetchImpl(url, init);
      const text = await response.text();
      if (!response.ok) throw new AgentPauseError(response.status, errorDetail(text, response.statusText));
      return { status: response.status, text };
    } catch (err) {
      if (err instanceof AgentPauseError) throw err;
      if (timedOut) {
        throw new AgentPauseTimeoutError(timeoutMs, `${method} ${url} timed out after ${timeoutMs} ms`, { cause: err });
      }
      if (external?.aborted) throw err;
      throw new AgentPauseConnectionError(url, err);
    } finally {
      if (timer !== undefined) clearTimeout(timer);
      external?.removeEventListener("abort", onAbort);
    }
  }

  private headers(accept: string, hasBody: boolean): Record<string, string> {
    const headers: Record<string, string> = { Accept: accept };
    if (hasBody) headers["Content-Type"] = "application/json";
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
    return headers;
  }

  private url(path: string, query?: Record<string, QueryValue>): string {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query ?? {})) {
      if (value !== undefined && value !== null) search.append(key, String(value));
    }
    const qs = search.toString();
    return `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}${qs ? `?${qs}` : ""}`;
  }
}

function toContext(context: ActionContextInput | string): ActionContextInput {
  return typeof context === "string" ? { action: context } : context;
}

function segment(value: string): string {
  return encodeURIComponent(value);
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseJson(text: string, status: number, method: string, path: string): unknown {
  if (text === "") return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch (err) {
    throw new AgentPauseError(status, `Invalid JSON in response from ${method} ${path}`, { cause: err });
  }
}

/** The `detail` of a FastAPI error body, or the raw text / status text for non-JSON bodies. */
function errorDetail(text: string, statusText: string): unknown {
  if (text) {
    try {
      const parsed = JSON.parse(text) as unknown;
      if (isPlainObject(parsed) && "detail" in parsed) return parsed.detail;
      return parsed;
    } catch {
      return text;
    }
  }
  return statusText || null;
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(signal.reason);
      return;
    }
    const onAbort = (): void => {
      clearTimeout(timer);
      reject(signal?.reason);
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}
