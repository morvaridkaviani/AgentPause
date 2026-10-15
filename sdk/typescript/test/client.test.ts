import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AgentPauseClient,
  AgentPauseConnectionError,
  AgentPauseError,
  AgentPauseTimeoutError,
  formatDetail,
  type Experiment,
  type StudyConfig,
} from "../src/index.js";
import { SseParser } from "../src/sse.js";
import {
  emptyResponse,
  hangingFetch,
  jsonResponse,
  makeDecision,
  makeSession,
  mockFetch,
  sseResponse,
  textResponse,
} from "./helpers.js";

const BASE = "http://localhost:8000/api/v1";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function clientWith(...responses: Parameters<typeof mockFetch>) {
  const mock = mockFetch(...responses);
  return { client: new AgentPauseClient({ fetch: mock.fetch }), calls: mock.calls };
}

const studyConfig: StudyConfig = {
  title: "AgentPause study",
  consent_text: "Consent",
  conditions: ["full_autonomy", "adaptive"],
  scenarios: ["email"],
  practice_scenario: null,
  explanation_modes: ["full"],
  post_task_instruments: [],
  final_instruments: [],
  seed_base: 900000,
};

function experiment(status: Experiment["status"]): Experiment {
  return {
    id: "e1",
    name: "pilot",
    status,
    created_at: "2026-10-15T10:00:00+00:00",
    finished_at: status === "completed" ? "2026-10-15T10:01:00+00:00" : null,
    config: {},
    progress: { done: status === "completed" ? 10 : 3, total: 10 },
    result: status === "completed" ? { aggregates: [] } : null,
    error: null,
  };
}

describe("AgentPauseClient endpoints", () => {
  type Case = {
    name: string;
    call: (client: AgentPauseClient) => Promise<unknown>;
    method: string;
    url: string;
    body?: unknown;
    reply?: unknown;
  };

  const cases: Case[] = [
    { name: "health", call: (c) => c.health(), method: "GET", url: `${BASE}/health`, reply: { status: "ok" } },
    { name: "policies", call: (c) => c.policies(), method: "GET", url: `${BASE}/policies`, reply: [] },
    { name: "model", call: (c) => c.model(), method: "GET", url: `${BASE}/model`, reply: { parameters: {} } },
    { name: "scenarios", call: (c) => c.scenarios(), method: "GET", url: `${BASE}/scenarios`, reply: [] },
    {
      name: "getScenario",
      call: (c) => c.getScenario("email"),
      method: "GET",
      url: `${BASE}/scenarios/email`,
      reply: { id: "email" },
    },
    {
      name: "createSession",
      call: (c) => c.createSession({ mode: "api", policy: "adaptive" }),
      method: "POST",
      url: `${BASE}/session`,
      body: { mode: "api", policy: "adaptive" },
      reply: makeSession(),
    },
    {
      name: "getSession (path segment is encoded)",
      call: (c) => c.getSession("a b/c"),
      method: "GET",
      url: `${BASE}/session/a%20b%2Fc`,
      reply: makeSession(),
    },
    {
      name: "sessionEvents",
      call: (c) => c.sessionEvents("s1"),
      method: "GET",
      url: `${BASE}/session/s1/events`,
      reply: [],
    },
    {
      name: "sessionEvents with since",
      call: (c) => c.sessionEvents("s1", { since: 4 }),
      method: "GET",
      url: `${BASE}/session/s1/events?since=4`,
      reply: [],
    },
    {
      name: "stepSession",
      call: (c) => c.stepSession("s1"),
      method: "POST",
      url: `${BASE}/session/s1/step`,
      body: { until: "next" },
      reply: { session: makeSession(), events: [], decision: null, card: null },
    },
    {
      name: "stepSession until intervention",
      call: (c) => c.stepSession("s1", "intervention"),
      method: "POST",
      url: `${BASE}/session/s1/step`,
      body: { until: "intervention" },
      reply: { session: makeSession(), events: [], decision: null, card: null },
    },
    {
      name: "submitAction",
      call: (c) =>
        c.submitAction("s1", {
          action: "send_email",
          consequence: "external_communication",
          reversible: false,
          provenance: { intent_confidence: "estimated" },
        }),
      method: "POST",
      url: `${BASE}/action`,
      body: {
        session_id: "s1",
        context: {
          action: "send_email",
          consequence: "external_communication",
          reversible: false,
          provenance: { intent_confidence: "estimated" },
        },
      },
      reply: { decision: makeDecision("CONTINUE"), intervention_id: null, session: makeSession() },
    },
    {
      name: "submitAction with an action name",
      call: (c) => c.submitAction("s1", "search"),
      method: "POST",
      url: `${BASE}/action`,
      body: { session_id: "s1", context: { action: "search" } },
      reply: { decision: makeDecision("CONTINUE"), intervention_id: null, session: makeSession() },
    },
    {
      name: "respond (defaults)",
      call: (c) => c.respond("s1", "approve"),
      method: "POST",
      url: `${BASE}/intervention`,
      body: { session_id: "s1", intervention_id: null, response: "approve", answers: {} },
      reply: { session: makeSession(), events: [], decision: null, card: null },
    },
    {
      name: "respond with intervention id and answers",
      call: (c) => c.respond("s1", "answer", { interventionId: "s1-2", answers: { recipient: "prof" } }),
      method: "POST",
      url: `${BASE}/intervention`,
      body: { session_id: "s1", intervention_id: "s1-2", response: "answer", answers: { recipient: "prof" } },
      reply: { session: makeSession(), events: [], decision: null, card: null },
    },
    {
      name: "listSessions",
      call: (c) => c.listSessions({ mode: "api", status: undefined, limit: 10 }),
      method: "GET",
      url: `${BASE}/sessions?mode=api&limit=10`,
      reply: { total: 0, offset: 0, limit: 10, items: [] },
    },
    {
      name: "listEvents",
      call: (c) => c.listEvents({ session_id: "s1", interventions_only: true, risk: "high" }),
      method: "GET",
      url: `${BASE}/events?session_id=s1&interventions_only=true&risk=high`,
      reply: { total: 0, offset: 0, limit: 100, items: [] },
    },
    {
      name: "metrics",
      call: (c) => c.metrics(),
      method: "GET",
      url: `${BASE}/metrics`,
      reply: { source: "experiment" },
    },
    {
      name: "metrics with filters",
      call: (c) => c.metrics({ source: "sessions", policy: "adaptive", scenario: undefined, mode: "study" }),
      method: "GET",
      url: `${BASE}/metrics?source=sessions&policy=adaptive&mode=study`,
      reply: { source: "sessions" },
    },
    {
      name: "compare",
      call: (c) => c.compare({ policies: ["adaptive", { name: "fixed_threshold", config: { threshold: 0.35 } }] }),
      method: "POST",
      url: `${BASE}/compare`,
      body: { policies: ["adaptive", { name: "fixed_threshold", config: { threshold: 0.35 } }] },
      reply: { note: "SIMULATED" },
    },
    {
      name: "createExperiment",
      call: (c) => c.createExperiment({ name: "pilot", policies: ["adaptive"], episodes: 10 }),
      method: "POST",
      url: `${BASE}/experiments`,
      body: { name: "pilot", policies: ["adaptive"], episodes: 10 },
      reply: experiment("queued"),
    },
    {
      name: "createExperiment with wait",
      call: (c) => c.createExperiment({ name: "pilot", policies: ["adaptive"] }, { wait: true }),
      method: "POST",
      url: `${BASE}/experiments?wait=true`,
      body: { name: "pilot", policies: ["adaptive"] },
      reply: experiment("completed"),
    },
    {
      name: "listExperiments",
      call: (c) => c.listExperiments({ limit: 5 }),
      method: "GET",
      url: `${BASE}/experiments?limit=5`,
      reply: [],
    },
    {
      name: "getExperiment",
      call: (c) => c.getExperiment("e1"),
      method: "GET",
      url: `${BASE}/experiments/e1`,
      reply: experiment("running"),
    },
    {
      name: "getStudyConfig",
      call: (c) => c.getStudyConfig(),
      method: "GET",
      url: `${BASE}/study/config`,
      reply: studyConfig,
    },
    {
      name: "updateStudyConfig",
      call: (c) => c.updateStudyConfig(studyConfig),
      method: "PUT",
      url: `${BASE}/study/config`,
      body: studyConfig,
      reply: studyConfig,
    },
    {
      name: "createParticipant",
      call: (c) => c.createParticipant(),
      method: "POST",
      url: `${BASE}/study/participants`,
      reply: { code: "P-1" },
    },
    {
      name: "getParticipant",
      call: (c) => c.getParticipant("P-1"),
      method: "GET",
      url: `${BASE}/study/participants/P-1`,
      reply: { code: "P-1" },
    },
    {
      name: "updateParticipant",
      call: (c) => c.updateParticipant("P-1", { consented: true }),
      method: "PATCH",
      url: `${BASE}/study/participants/P-1`,
      body: { consented: true },
      reply: { code: "P-1" },
    },
    {
      name: "startStudySession",
      call: (c) => c.startStudySession("P-1", 2),
      method: "POST",
      url: `${BASE}/study/sessions`,
      body: { participant_code: "P-1", block: 2 },
      reply: makeSession({ mode: "study" }),
    },
    {
      name: "instruments",
      call: (c) => c.instruments(),
      method: "GET",
      url: `${BASE}/study/instruments`,
      reply: [],
    },
    {
      name: "submitQuestionnaire",
      call: (c) => c.submitQuestionnaire({ participant_code: "P-1", instrument_id: "nasa_tlx_raw", responses: { q1: 3 } }),
      method: "POST",
      url: `${BASE}/study/responses`,
      body: { participant_code: "P-1", instrument_id: "nasa_tlx_raw", responses: { q1: 3 } },
      reply: { id: 1, instrument_id: "nasa_tlx_raw", score: null },
    },
  ];

  it.each(cases)("$name → $method $url", async ({ call, method, url, body, reply }) => {
    const { client, calls } = clientWith(jsonResponse(reply));
    await expect(call(client)).resolves.toEqual(reply);
    expect(calls).toHaveLength(1);
    const [sent] = calls;
    expect(sent?.method).toBe(method);
    expect(sent?.url).toBe(url);
    expect(sent?.body).toEqual(body);
    expect(sent?.headers["Accept"]).toBe("application/json");
    if (body === undefined) expect(sent?.headers["Content-Type"]).toBeUndefined();
    else expect(sent?.headers["Content-Type"]).toBe("application/json");
  });

  it.each([
    { name: "deleteSession", call: (c: AgentPauseClient) => c.deleteSession("s1"), url: `${BASE}/session/s1` },
    { name: "deleteExperiment", call: (c: AgentPauseClient) => c.deleteExperiment("e1"), url: `${BASE}/experiments/e1` },
  ])("$name sends DELETE and resolves on 204", async ({ call, url }) => {
    const { client, calls } = clientWith(emptyResponse(204));
    await expect(call(client)).resolves.toBeUndefined();
    expect(calls[0]).toMatchObject({ method: "DELETE", url, body: undefined });
  });

  it.each([
    {
      name: "exportEventsCsv",
      call: (c: AgentPauseClient) => c.exportEventsCsv({ policy: "adaptive" }),
      url: `${BASE}/events?policy=adaptive&format=csv`,
    },
    {
      name: "exportExperiment",
      call: (c: AgentPauseClient) => c.exportExperiment("e1", { table: "episodes", format: "json" }),
      url: `${BASE}/experiments/e1/export?table=episodes&format=json`,
    },
    {
      name: "exportExperiment (server defaults)",
      call: (c: AgentPauseClient) => c.exportExperiment("e1"),
      url: `${BASE}/experiments/e1/export`,
    },
    {
      name: "exportStudy",
      call: (c: AgentPauseClient) => c.exportStudy({ format: "csv" }),
      url: `${BASE}/study/export?format=csv`,
    },
  ])("$name returns the raw body", async ({ call, url }) => {
    const { client, calls } = clientWith(textResponse("id,seq\n1,0\n"));
    await expect(call(client)).resolves.toBe("id,seq\n1,0\n");
    expect(calls[0]).toMatchObject({ method: "GET", url });
  });
});

describe("evaluate", () => {
  it("posts the context with the default policy and explanation level", async () => {
    const decision = makeDecision("ASK_HUMAN");
    const { client, calls } = clientWith(jsonResponse(decision));
    const context = {
      action: "send_email",
      consequence: "external_communication",
      reversible: false,
      intent_confidence: 0.72,
      provenance: { intent_confidence: "estimated" as const },
    };
    await expect(client.evaluate(context)).resolves.toEqual(decision);
    expect(calls[0]).toMatchObject({ method: "POST", url: `${BASE}/evaluate` });
    expect(calls[0]?.body).toStrictEqual({ context, policy: "adaptive", explain: "full" });
  });

  it("accepts an action name and forwards policy, preferences, explain and state", async () => {
    const { client, calls } = clientWith(jsonResponse(makeDecision("CONTINUE")));
    await client.evaluate("search", {
      policy: { name: "fixed_threshold", config: { threshold: 0.35 } },
      preferences: { profile: "maximum_control", always_ask_categories: ["external_communication"] },
      explain: "light",
      state: null,
    });
    expect(calls[0]?.body).toStrictEqual({
      context: { action: "search" },
      policy: { name: "fixed_threshold", config: { threshold: 0.35 } },
      preferences: { profile: "maximum_control", always_ask_categories: ["external_communication"] },
      explain: "light",
      state: null,
    });
  });
});

describe("configuration and headers", () => {
  it("defaults to http://localhost:8000 and strips trailing slashes from baseUrl", async () => {
    const a = mockFetch(jsonResponse({ status: "ok" }));
    await new AgentPauseClient({ fetch: a.fetch }).health();
    expect(a.calls[0]?.url).toBe("http://localhost:8000/api/v1/health");

    const b = mockFetch(jsonResponse({ status: "ok" }));
    const client = new AgentPauseClient({ baseUrl: "https://agentpause.example.org/lab//", fetch: b.fetch });
    expect(client.baseUrl).toBe("https://agentpause.example.org/lab");
    await client.health();
    expect(b.calls[0]?.url).toBe("https://agentpause.example.org/lab/api/v1/health");
  });

  it("sends no Authorization header without a token", async () => {
    const { client, calls } = clientWith(jsonResponse({ status: "ok" }));
    await client.health();
    expect(calls[0]?.headers).toStrictEqual({ Accept: "application/json" });
  });

  it("sends the bearer token on every request", async () => {
    const mock = mockFetch(jsonResponse({ status: "ok" }), textResponse("a,b\n"), emptyResponse(204));
    const client = new AgentPauseClient({ fetch: mock.fetch, token: "s3cret" });
    await client.health();
    await client.exportEventsCsv();
    await client.deleteSession("s1");
    for (const call of mock.calls) expect(call.headers["Authorization"]).toBe("Bearer s3cret");
    expect(mock.calls[1]?.headers["Accept"]).toBe("text/csv");
  });

  it("uses the global fetch when none is passed", async () => {
    const mock = mockFetch(jsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", mock.fetch);
    await expect(new AgentPauseClient().health()).resolves.toEqual({ status: "ok" });
    expect(mock.calls).toHaveLength(1);
  });

  it("calls the fetch implementation without binding it to the client", async () => {
    let receiver: unknown = "unset";
    const impl = function (this: unknown): Promise<Response> {
      receiver = this;
      return Promise.resolve(jsonResponse({ status: "ok" }));
    };
    await new AgentPauseClient({ fetch: impl as unknown as typeof fetch }).health();
    expect(receiver).toBeUndefined();
  });

  it("fails fast when no fetch implementation exists", () => {
    vi.stubGlobal("fetch", undefined);
    expect(() => new AgentPauseClient()).toThrow(TypeError);
  });

  it("rejects an invalid timeout", () => {
    expect(() => new AgentPauseClient({ fetch: mockFetch().fetch, timeoutMs: -1 })).toThrow(RangeError);
    expect(() => new AgentPauseClient({ fetch: mockFetch().fetch, timeoutMs: Number.NaN })).toThrow(RangeError);
  });

  it("exposes a low-level request method", async () => {
    const mock = mockFetch(jsonResponse({ ok: true }), textResponse("raw"));
    const client = new AgentPauseClient({ fetch: mock.fetch });
    await expect(
      client.request("POST", "/api/v1/custom", { query: { a: 1, b: null, c: false }, body: { x: 1 } }),
    ).resolves.toEqual({ ok: true });
    expect(mock.calls[0]).toMatchObject({
      method: "POST",
      url: `${BASE}/custom?a=1&c=false`,
      body: { x: 1 },
    });
    await expect(client.request("GET", "api/v1/raw", { responseType: "text" })).resolves.toBe("raw");
    expect(mock.calls[1]?.url).toBe(`${BASE}/raw`);
    expect(mock.calls[1]?.headers["Accept"]).toBe("*/*");
  });
});

describe("errors", () => {
  it("raises AgentPauseError with the server's detail", async () => {
    const { client } = clientWith(jsonResponse({ detail: "Session missing not found" }, 404));
    const error = await client.getSession("missing").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(AgentPauseError);
    expect(error).toBeInstanceOf(Error);
    expect(error).toMatchObject({
      name: "AgentPauseError",
      status: 404,
      detail: "Session missing not found",
      message: "AgentPause API error 404: Session missing not found",
    });
  });

  it("keeps validation errors structured and readable", async () => {
    const detail = [{ loc: ["body", "context", "action"], msg: "Field required", type: "missing" }];
    const { client } = clientWith(jsonResponse({ detail }, 422));
    const error = (await client.evaluate({ action: "" }).catch((e: unknown) => e)) as AgentPauseError;
    expect(error.status).toBe(422);
    expect(error.detail).toEqual(detail);
    expect(error.message).toBe("AgentPause API error 422: body.context.action: Field required");
  });

  it("reports 409 conflicts from session endpoints", async () => {
    const { client } = clientWith(
      jsonResponse({ detail: "Respond to the pending intervention first (POST /api/v1/intervention)" }, 409),
    );
    await expect(client.submitAction("s1", "x")).rejects.toMatchObject({ status: 409 });
  });

  it("uses the text body or status text for non-JSON errors", async () => {
    const { client } = clientWith(
      textResponse("Internal Server Error", 500),
      textResponse("", 401, "Unauthorized"),
    );
    await expect(client.health()).rejects.toMatchObject({ status: 500, detail: "Internal Server Error" });
    await expect(client.listSessions()).rejects.toMatchObject({ status: 401, detail: "Unauthorized" });
  });

  it("rejects invalid JSON and unexpected shapes", async () => {
    const { client } = clientWith(textResponse("<html>"), jsonResponse([1, 2]), jsonResponse({ a: 1 }));
    await expect(client.health()).rejects.toThrow(/Invalid JSON in response from GET \/api\/v1\/health/);
    await expect(client.health()).rejects.toThrow(/Expected a JSON object/);
    await expect(client.policies()).rejects.toThrow(/Expected a JSON array/);
  });

  it("wraps network failures in AgentPauseConnectionError", async () => {
    const cause = new TypeError("fetch failed");
    const { client } = clientWith(() => Promise.reject(cause));
    const error = (await client.health().catch((e: unknown) => e)) as AgentPauseConnectionError;
    expect(error).toBeInstanceOf(AgentPauseConnectionError);
    expect(error).toBeInstanceOf(AgentPauseError);
    expect(error.status).toBe(0);
    expect(error.cause).toBe(cause);
    expect(error.message).toContain("http://localhost:8000/api/v1/health");
  });

  it("formats details", () => {
    expect(formatDetail(undefined)).toBe("");
    expect(formatDetail("x")).toBe("x");
    expect(formatDetail([{ msg: "bad" }, "plain"])).toBe("bad; plain");
    expect(formatDetail({ code: 1 })).toBe('{"code":1}');
  });
});

describe("timeouts and cancellation", () => {
  it("aborts and throws AgentPauseTimeoutError after timeoutMs", async () => {
    vi.useFakeTimers();
    const client = new AgentPauseClient({ fetch: hangingFetch(), timeoutMs: 250 });
    const outcome = client.health().catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(250);
    const error = (await outcome) as AgentPauseTimeoutError;
    expect(error).toBeInstanceOf(AgentPauseTimeoutError);
    expect(error).toBeInstanceOf(AgentPauseError);
    expect(error.status).toBe(0);
    expect(error.timeoutMs).toBe(250);
    expect(error.message).toContain("GET http://localhost:8000/api/v1/health timed out after 250 ms");
  });

  it("lets a request override the client timeout", async () => {
    vi.useFakeTimers();
    const client = new AgentPauseClient({ fetch: hangingFetch(), timeoutMs: 60_000 });
    const outcome = client.evaluate("search", { timeoutMs: 50 }).catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(50);
    expect(await outcome).toMatchObject({ name: "AgentPauseTimeoutError", timeoutMs: 50 });
  });

  it("does not time out when timeoutMs is 0", async () => {
    vi.useFakeTimers();
    const slow = (() =>
      new Promise<Response>((resolve) => {
        setTimeout(() => resolve(jsonResponse({ status: "ok" })), 120_000);
      })) as unknown as typeof fetch;
    const client = new AgentPauseClient({ fetch: slow, timeoutMs: 0 });
    const outcome = client.health();
    await vi.advanceTimersByTimeAsync(120_000);
    await expect(outcome).resolves.toEqual({ status: "ok" });
  });

  it("clears its timer after a response", async () => {
    vi.useFakeTimers();
    const { client } = clientWith(jsonResponse({ status: "ok" }));
    await client.health();
    expect(vi.getTimerCount()).toBe(0);
  });

  it("rethrows the caller's abort reason instead of a timeout", async () => {
    const client = new AgentPauseClient({ fetch: hangingFetch() });
    const controller = new AbortController();
    const outcome = client.health({ signal: controller.signal }).catch((e: unknown) => e);
    controller.abort();
    const error = (await outcome) as Error;
    expect(error).not.toBeInstanceOf(AgentPauseError);
    expect(error.name).toBe("AbortError");
  });

  it("rejects immediately with an already aborted signal", async () => {
    const client = new AgentPauseClient({ fetch: hangingFetch() });
    const reason = new Error("stop");
    await expect(client.health({ signal: AbortSignal.abort(reason) })).rejects.toBe(reason);
  });
});

describe("waitForExperiment", () => {
  it("polls until the experiment completes", async () => {
    const { client, calls } = clientWith(
      jsonResponse(experiment("queued")),
      jsonResponse(experiment("running")),
      jsonResponse(experiment("completed")),
    );
    const done = await client.waitForExperiment("e1", { pollIntervalMs: 1 });
    expect(done.status).toBe("completed");
    expect(calls.map((c) => c.url)).toEqual([`${BASE}/experiments/e1`, `${BASE}/experiments/e1`, `${BASE}/experiments/e1`]);
  });

  it("returns failed experiments for the caller to inspect", async () => {
    const failed = { ...experiment("failed"), error: "boom" };
    const { client } = clientWith(jsonResponse(failed));
    await expect(client.waitForExperiment("e1")).resolves.toEqual(failed);
  });

  it("gives up after maxWaitMs", async () => {
    vi.useFakeTimers();
    const { client } = clientWith(
      ...Array.from({ length: 5 }, () => () => jsonResponse(experiment("running"))),
    );
    const outcome = client.waitForExperiment("e1", { pollIntervalMs: 100, maxWaitMs: 250 }).catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(300);
    const error = (await outcome) as AgentPauseTimeoutError;
    expect(error).toBeInstanceOf(AgentPauseTimeoutError);
    expect(error.message).toContain("Experiment e1 did not finish within 250 ms (status: running)");
  });
});

describe("streamSession", () => {
  const decisionEvent = { id: 1, seq: 1, session_id: "s1", type: "decision", decision: "CONTINUE" };
  const responseEvent = { id: 2, seq: 2, session_id: "s1", type: "response", decision: null };

  it("yields events until the end event", async () => {
    const decisionJson = JSON.stringify(decisionEvent);
    const mock = mockFetch(
      sseResponse([
        `id: 1\nevent: decision\ndata: ${decisionJson.slice(0, 10)}`,
        `${decisionJson.slice(10)}\n\n: keep-alive\n\n`,
        `id: 2\r\nevent: response\r\ndata: ${JSON.stringify(responseEvent)}\r\n\r\n`,
        "event: end\ndata: {}\n\n",
        `id: 3\nevent: decision\ndata: ${JSON.stringify({ ...decisionEvent, seq: 3 })}\n\n`,
      ]),
    );
    const client = new AgentPauseClient({ fetch: mock.fetch, token: "s3cret" });
    const events = [];
    for await (const event of client.streamSession("s1", { since: 0 })) events.push(event);
    expect(events).toEqual([decisionEvent, responseEvent]);
    expect(mock.calls[0]).toMatchObject({ method: "GET", url: `${BASE}/session/s1/stream?since=0` });
    expect(mock.calls[0]?.headers).toStrictEqual({ Accept: "text/event-stream", Authorization: "Bearer s3cret" });
  });

  it("finishes when the stream closes without an end event", async () => {
    const { client } = clientWith(sseResponse([`event: decision\ndata: ${JSON.stringify(decisionEvent)}\n\n`]));
    const events = [];
    for await (const event of client.streamSession("s1")) events.push(event);
    expect(events).toEqual([decisionEvent]);
  });

  it("cancels the stream when the consumer stops early", async () => {
    const onCancel = vi.fn();
    const { client } = clientWith(
      sseResponse(
        [
          `event: decision\ndata: ${JSON.stringify(decisionEvent)}\n\n`,
          `event: response\ndata: ${JSON.stringify(responseEvent)}\n\n`,
        ],
        onCancel,
      ),
    );
    for await (const event of client.streamSession("s1")) {
      expect(event).toEqual(decisionEvent);
      break;
    }
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("raises AgentPauseError for error responses", async () => {
    const { client } = clientWith(jsonResponse({ detail: "Session nope not found" }, 404));
    const stream = client.streamSession("nope");
    await expect(stream.next()).rejects.toMatchObject({ status: 404, detail: "Session nope not found" });
  });

  it("parses SSE framing split across chunks", () => {
    const parser = new SseParser();
    expect(parser.push("event: a\r")).toEqual([]);
    expect(parser.push("\ndata: 1\ndata: 2\r")).toEqual([]);
    expect(parser.push("\n\r\n")).toEqual([{ event: "a", data: "1\n2", id: null }]);
    expect(parser.push("data:x\n\n")).toEqual([{ event: "message", data: "x", id: null }]);
  });
});
