/** Typed client for the AgentPause API. All requests go to /api/v1 on the same origin;
 * Next.js rewrites them to the backend (see next.config.ts). */

import type {
  ApiEvent,
  CompareResult,
  Decision,
  Experiment,
  Instrument,
  Metrics,
  Participant,
  PolicyInfo,
  PolicySpec,
  Preferences,
  ResponseName,
  ScenarioSummary,
  Session,
  StepResponse,
  StudyConfig,
} from "./types";

import { engineRequest } from "./browser-api";
import { STATIC_DEMO } from "./site";

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(formatDetail(detail) || `Request failed (${status})`);
  }
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: unknown }).msg) : String(d)))
      .join("; ");
  }
  return "";
}

let researcherToken: string | null = null;

/** Set a researcher token (study administration); kept in memory and sessionStorage only. */
export function setResearcherToken(token: string | null): void {
  researcherToken = token;
  try {
    if (token) sessionStorage.setItem("agentpause.token", token);
    else sessionStorage.removeItem("agentpause.token");
  } catch {
    /* storage unavailable: keep in memory */
  }
}

function token(): string | null {
  if (researcherToken) return researcherToken;
  try {
    return sessionStorage.getItem("agentpause.token");
  } catch {
    return null;
  }
}

/** The static online demo answers requests from the in-browser engine instead of a server. */
async function engineFetch<T>(method: string, path: string, body?: unknown): Promise<T> {
  const full = `${BASE}${path}`;
  const cut = full.indexOf("?");
  const pathname = cut < 0 ? full : full.slice(0, cut);
  const search = cut < 0 ? "" : full.slice(cut + 1);
  const response = await engineRequest(method, pathname, search, body === undefined ? null : JSON.stringify(body));
  if (response.status >= 400) {
    let detail: unknown = response.body;
    try {
      detail = (JSON.parse(response.body) as { detail?: unknown }).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204 || !response.body) return undefined as T;
  return (response.contentType.includes("json") ? JSON.parse(response.body) : response.body) as T;
}

export async function request<T>(method: string, path: string, body?: unknown, init?: RequestInit): Promise<T> {
  if (STATIC_DEMO) return engineFetch<T>(method, path, body);
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const t = token();
  if (t) headers["Authorization"] = `Bearer ${t}`;
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    ...init,
  });
  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      detail = ((await response.json()) as { detail?: unknown }).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function query(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export interface ActionContextInput {
  action: string;
  description?: string;
  consequence?: string;
  severity?: number;
  reversible?: boolean;
  recoverability?: number;
  agent_confidence?: number;
  intent_confidence?: number;
  task_progress?: number;
  at_breakpoint?: boolean;
  cognitive_load?: number;
  external_effects?: boolean;
  step?: number;
}

export const api = {
  health: () => request<Record<string, unknown>>("GET", "/health"),
  policies: () => request<PolicyInfo[]>("GET", "/policies"),
  scenarios: () => request<ScenarioSummary[]>("GET", "/scenarios"),
  model: () => request<Record<string, unknown>>("GET", "/model"),

  evaluate: (
    context: ActionContextInput,
    policy: PolicySpec | string = "adaptive",
    opts: { preferences?: Preferences | null; state?: Record<string, unknown> | null } = {},
  ) => request<Decision>("POST", "/evaluate", { context, policy, preferences: opts.preferences ?? null, state: opts.state ?? null }),

  createSession: (body: {
    mode?: "demo" | "study" | "api";
    scenario_id?: string;
    policy: PolicySpec | string;
    preferences?: Preferences | null;
    seed?: number | null;
    episode?: number;
  }) => request<Session>("POST", "/session", { mode: "demo", ...body }),
  session: (id: string) => request<Session>("GET", `/session/${id}`),
  step: (id: string, until: "next" | "intervention" = "next") => request<StepResponse>("POST", `/session/${id}/step`, { until }),
  respond: (sessionId: string, response: ResponseName, answers: Record<string, string> = {}, interventionId?: string) =>
    request<StepResponse>("POST", "/intervention", {
      session_id: sessionId,
      response,
      answers,
      intervention_id: interventionId ?? null,
    }),
  sessionEvents: (id: string, since = -1) => request<ApiEvent[]>("GET", `/session/${id}/events${query({ since })}`),

  events: (params: Record<string, string | number | boolean | undefined>) =>
    request<{ total: number; offset: number; limit: number; items: ApiEvent[] }>("GET", `/events${query(params)}`),
  metrics: (params: Record<string, string | undefined>) => request<Metrics>("GET", `/metrics${query(params)}`),
  compare: (body: {
    scenarios: string[];
    policies: (PolicySpec | string)[];
    episodes: number;
    seed: number;
    trace_scenario?: string | null;
    trace_episode?: number;
    user?: Record<string, unknown>;
    engine?: Record<string, unknown>;
  }) => request<CompareResult>("POST", "/compare", body),

  experiments: () => request<Experiment[]>("GET", "/experiments"),
  experiment: (id: string) => request<Experiment>("GET", `/experiments/${id}`),
  createExperiment: (body: Record<string, unknown>) => request<Experiment>("POST", "/experiments", body),
  deleteExperiment: (id: string) => request<void>("DELETE", `/experiments/${id}`),

  studyConfig: () => request<StudyConfig>("GET", "/study/config"),
  updateStudyConfig: (config: StudyConfig) => request<StudyConfig>("PUT", "/study/config", config),
  enrol: () => request<Participant>("POST", "/study/participants"),
  participant: (code: string) => request<Participant>("GET", `/study/participants/${encodeURIComponent(code)}`),
  updateParticipant: (code: string, body: { consented?: boolean; completed?: boolean }) =>
    request<Participant>("PATCH", `/study/participants/${encodeURIComponent(code)}`, body),
  startBlock: (code: string, block: number) => request<Session>("POST", "/study/sessions", { participant_code: code, block }),
  instruments: () => request<Instrument[]>("GET", "/study/instruments"),
  submitQuestionnaire: (body: {
    participant_code: string;
    instrument_id: string;
    responses: Record<string, number | string>;
    session_id?: string;
    block?: number;
  }) => request<{ id: number; instrument_id: string; score: Record<string, unknown> | null }>("POST", "/study/responses", body),
};

/** URL for a file download (CSV/JSON export). The browser follows it directly. */
export function downloadUrl(path: string, params: Record<string, string | number | boolean | undefined> = {}): string {
  return `${BASE}${path}${query(params)}`;
}

/** Save an export as a file. Used by the static demo, where there is no server URL to follow. */
export async function downloadFile(path: string, params: Record<string, string | number | boolean | undefined>, filename: string): Promise<void> {
  const response = await engineRequest("GET", `${BASE}${path}`, query(params).replace(/^\?/, ""), null);
  if (response.status >= 400) throw new ApiError(response.status, response.body);
  const url = URL.createObjectURL(new Blob([response.body], { type: response.contentType }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
