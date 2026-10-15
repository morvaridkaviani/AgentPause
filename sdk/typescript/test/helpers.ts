import { vi } from "vitest";

import type { ActionResult, Decision, DecisionType, Session } from "../src/index.js";

export interface RecordedCall {
  url: string;
  method: string;
  headers: Record<string, string>;
  /** Parsed JSON body, or `undefined` when no body was sent. */
  body: unknown;
  signal: AbortSignal | undefined;
}

type Responder = Response | ((url: string, init: RequestInit) => Response | Promise<Response>);

/** A fetch mock that records every call and replies with the given responses in order. */
export function mockFetch(...responses: Responder[]): { fetch: typeof fetch; calls: RecordedCall[] } {
  const calls: RecordedCall[] = [];
  const impl = vi.fn(async (input: string | URL | Request, init: RequestInit = {}): Promise<Response> => {
    const url = String(input);
    calls.push({
      url,
      method: init.method ?? "GET",
      headers: { ...(init.headers as Record<string, string> | undefined) },
      body: typeof init.body === "string" ? (JSON.parse(init.body) as unknown) : undefined,
      signal: init.signal ?? undefined,
    });
    const next = responses.shift();
    if (next === undefined) throw new Error(`Unexpected request: ${init.method ?? "GET"} ${url}`);
    return typeof next === "function" ? next(url, init) : next;
  });
  return { fetch: impl as unknown as typeof fetch, calls };
}

export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}

export function textResponse(text: string, status = 200, statusText = ""): Response {
  return new Response(text, { status, statusText, headers: { "Content-Type": "text/plain" } });
}

export function emptyResponse(status = 204): Response {
  return new Response(null, { status });
}

/** A fetch that never answers and rejects when its signal aborts, like the real fetch. */
export function hangingFetch(): typeof fetch {
  return ((_input: string | URL | Request, init: RequestInit = {}) =>
    new Promise<Response>((_resolve, reject) => {
      const signal = init.signal;
      if (!signal) return;
      if (signal.aborted) reject(signal.reason);
      signal.addEventListener("abort", () => reject(signal.reason), { once: true });
    })) as typeof fetch;
}

/** A streaming `text/event-stream` response delivering `chunks` one by one. */
export function sseResponse(chunks: string[], onCancel?: () => void): Response {
  const encoder = new TextEncoder();
  let index = 0;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      const chunk = chunks[index++];
      if (chunk === undefined) controller.close();
      else controller.enqueue(encoder.encode(chunk));
    },
    cancel() {
      onCancel?.();
    },
  });
  return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

export function makeDecision(decision: DecisionType, overrides: Partial<Decision> = {}): Decision {
  const asks = decision === "CLARIFY" || decision === "ASK_HUMAN";
  return {
    decision,
    score: asks ? 0.71 : 0.12,
    confidence: 0.9,
    policy: "adaptive",
    action: "send_email",
    step: 0,
    reason_codes: asks ? ["IRREVERSIBLE_EXTERNAL"] : [],
    explanation: `Decision ${decision} for send_email`,
    recommended_intervention: asks ? "confirmation" : "none",
    should_ask: asks,
    questions: [],
    deferred: [],
    factors: [],
    counterfactuals: [],
    timing: null,
    item_timings: [],
    terms: {},
    signals: {},
    warnings: [],
    latency_ms: 1.5,
    ...overrides,
  };
}

export function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    id: "s1",
    created_at: "2026-10-15T10:00:00+00:00",
    mode: "api",
    kind: "external",
    policy: "adaptive",
    policy_spec: { name: "adaptive" },
    explanation_mode: "full",
    scenario: null,
    brief: null,
    status: "running",
    step_index: 0,
    n_steps: 0,
    steps: [],
    timeline: [],
    pending: null,
    pending_questions: [],
    outcome: null,
    participant_code: null,
    block: null,
    seed: 1,
    episode: 0,
    ...overrides,
  };
}

/** The body of `POST /api/v1/action` for a decision; interrupting decisions get an intervention id. */
export function makeActionResult(decision: DecisionType, sessionId = "s1"): ActionResult {
  const interrupts = decision === "CLARIFY" || decision === "ASK_HUMAN" || decision === "BLOCK";
  return {
    decision: makeDecision(decision),
    intervention_id: interrupts ? `${sessionId}-1` : null,
    session: makeSession({ id: sessionId, status: interrupts ? "awaiting_human" : "running" }),
  };
}
