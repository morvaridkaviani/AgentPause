import { describe, expect, it, vi } from "vitest";

import {
  ActionBlockedError,
  ActionRejectedError,
  AgentPauseClient,
  AgentPauseError,
  AgentPauseGuardError,
  InterventionRequiredError,
  guard,
  interrupts,
  isBlocked,
  isDecisionType,
  isResponseName,
  shouldAsk,
  shouldProceed,
  withGuard,
  type DecisionType,
  type ResponseName,
} from "../src/index.js";
import { jsonResponse, makeActionResult, makeDecision, makeSession, mockFetch } from "./helpers.js";

const BASE = "http://localhost:8000/api/v1";

function stepResult() {
  return { session: makeSession(), events: [], decision: null, card: null };
}

function setup(...responses: Parameters<typeof mockFetch>) {
  const mock = mockFetch(...responses);
  return { client: new AgentPauseClient({ fetch: mock.fetch }), calls: mock.calls };
}

describe("guard, stateless (POST /api/v1/evaluate)", () => {
  it.each<DecisionType>(["CONTINUE", "DEFER"])("runs the function on %s", async (type) => {
    const { client, calls } = setup(jsonResponse(makeDecision(type)));
    const fn = vi.fn(() => "sent");
    await expect(guard(client, {}, "send_email", fn)).resolves.toBe("sent");
    expect(fn).toHaveBeenCalledOnce();
    expect(calls).toHaveLength(1);
    expect(calls[0]).toMatchObject({
      method: "POST",
      url: `${BASE}/evaluate`,
      body: { context: { action: "send_email" }, policy: "adaptive", explain: "full" },
    });
  });

  it("forwards evaluate options and the full action context", async () => {
    const { client, calls } = setup(jsonResponse(makeDecision("CONTINUE")));
    const context = { action: "delete_file", consequence: "data_deletion", reversible: false };
    await guard(client, { policy: "always_confirm", explain: "none", preferences: { profile: "balanced" } }, context, () => 1);
    expect(calls[0]?.body).toStrictEqual({
      context,
      policy: "always_confirm",
      explain: "none",
      preferences: { profile: "balanced" },
    });
  });

  it("awaits async functions and propagates their errors", async () => {
    const { client } = setup(jsonResponse(makeDecision("CONTINUE")), jsonResponse(makeDecision("CONTINUE")));
    await expect(guard(client, {}, "a", async () => 42)).resolves.toBe(42);
    const failure = new Error("tool failed");
    await expect(
      guard(client, {}, "a", async () => {
        throw failure;
      }),
    ).rejects.toBe(failure);
  });

  it("throws ActionBlockedError on BLOCK without running the function or asking", async () => {
    const decision = makeDecision("BLOCK", { explanation: "Deleting backups is blocked by your rules." });
    const { client } = setup(jsonResponse(decision));
    const fn = vi.fn();
    const onAsk = vi.fn(() => true);
    const error = (await guard(client, {}, "delete_backups", fn, { onAsk }).catch((e: unknown) => e)) as ActionBlockedError;
    expect(error).toBeInstanceOf(ActionBlockedError);
    expect(error).toBeInstanceOf(AgentPauseGuardError);
    expect(error).not.toBeInstanceOf(AgentPauseError);
    expect(error.message).toBe("Deleting backups is blocked by your rules.");
    expect(error.decision).toEqual(decision);
    expect(error.sessionId).toBeNull();
    expect(error.interventionId).toBeNull();
    expect(fn).not.toHaveBeenCalled();
    expect(onAsk).not.toHaveBeenCalled();
  });

  it.each<DecisionType>(["ASK_HUMAN", "CLARIFY"])("throws InterventionRequiredError on %s without onAsk", async (type) => {
    const { client } = setup(jsonResponse(makeDecision(type)));
    const fn = vi.fn();
    const error = (await guard(client, {}, "send_email", fn).catch((e: unknown) => e)) as InterventionRequiredError;
    expect(error).toBeInstanceOf(InterventionRequiredError);
    expect(error.decision.decision).toBe(type);
    expect(error.message).toBe(`Decision ${type} for send_email`);
    expect(fn).not.toHaveBeenCalled();
  });

  it("runs the function when onAsk approves, without recording anything", async () => {
    const decision = makeDecision("ASK_HUMAN");
    const { client, calls } = setup(jsonResponse(decision));
    const onAsk = vi.fn(() => true);
    await expect(guard(client, {}, { action: "send_email" }, () => "ok", { onAsk })).resolves.toBe("ok");
    expect(onAsk).toHaveBeenCalledWith(decision, {
      action: { action: "send_email" },
      sessionId: null,
      interventionId: null,
    });
    expect(calls).toHaveLength(1);
  });

  it("throws ActionRejectedError when onAsk declines", async () => {
    const { client } = setup(jsonResponse(makeDecision("ASK_HUMAN")));
    const fn = vi.fn();
    const error = (await guard(client, {}, "send_email", fn, { onAsk: async () => false }).catch(
      (e: unknown) => e,
    )) as ActionRejectedError;
    expect(error).toBeInstanceOf(ActionRejectedError);
    expect(error.response).toBe("reject");
    expect(error.message).toBe("The user responded 'reject' to send_email");
    expect(fn).not.toHaveBeenCalled();
  });
});

describe("guard, session mode (POST /api/v1/action + /api/v1/intervention)", () => {
  it.each([
    { label: "a session id string", target: "s1" },
    { label: "{ sessionId }", target: { sessionId: "s1" } },
  ])("submits the action to the session given as $label", async ({ target }) => {
    const { client, calls } = setup(jsonResponse(makeActionResult("CONTINUE")));
    const fn = vi.fn(() => "done");
    await expect(guard(client, target, { action: "search", consequence: "read_only" }, fn)).resolves.toBe("done");
    expect(calls).toHaveLength(1);
    expect(calls[0]).toMatchObject({
      method: "POST",
      url: `${BASE}/action`,
      body: { session_id: "s1", context: { action: "search", consequence: "read_only" } },
    });
  });

  it("records an approval with the intervention id, then runs the function", async () => {
    const { client, calls } = setup(jsonResponse(makeActionResult("ASK_HUMAN")), jsonResponse(stepResult()));
    const fn = vi.fn(() => "sent");
    const onAsk = vi.fn(() => "approve" as const);
    await expect(guard(client, "s1", "send_email", fn, { onAsk })).resolves.toBe("sent");
    expect(onAsk).toHaveBeenCalledWith(expect.objectContaining({ decision: "ASK_HUMAN" }), {
      action: { action: "send_email" },
      sessionId: "s1",
      interventionId: "s1-1",
    });
    expect(calls[1]).toMatchObject({
      method: "POST",
      url: `${BASE}/intervention`,
      body: { session_id: "s1", intervention_id: "s1-1", response: "approve", answers: {} },
    });
    expect(fn).toHaveBeenCalledOnce();
  });

  it("records clarification answers", async () => {
    const { client, calls } = setup(jsonResponse(makeActionResult("CLARIFY")), jsonResponse(stepResult()));
    const fn = vi.fn(() => "booked");
    await expect(
      guard(client, "s1", "book_flight", fn, {
        onAsk: () => ({ response: "answer", answers: { travel_dates: "May 3-7" } }),
      }),
    ).resolves.toBe("booked");
    expect(calls[1]?.body).toStrictEqual({
      session_id: "s1",
      intervention_id: "s1-1",
      response: "answer",
      answers: { travel_dates: "May 3-7" },
    });
  });

  it.each<ResponseName>(["approve", "edit", "answer", "override"])("runs the function after '%s'", async (response) => {
    const { client, calls } = setup(jsonResponse(makeActionResult("ASK_HUMAN")), jsonResponse(stepResult()));
    const fn = vi.fn(() => "ran");
    await expect(guard(client, "s1", "send_email", fn, { onAsk: () => response })).resolves.toBe("ran");
    expect(calls[1]?.body).toMatchObject({ response });
  });

  it.each<ResponseName>(["reject", "takeover", "cancel_task", "timeout", "ask_why"])(
    "records '%s' and throws ActionRejectedError",
    async (response) => {
      const { client, calls } = setup(jsonResponse(makeActionResult("ASK_HUMAN")), jsonResponse(stepResult()));
      const fn = vi.fn();
      const error = (await guard(client, "s1", "send_email", fn, { onAsk: () => response }).catch(
        (e: unknown) => e,
      )) as ActionRejectedError;
      expect(error).toBeInstanceOf(ActionRejectedError);
      expect(error.response).toBe(response);
      expect(error.sessionId).toBe("s1");
      expect(error.interventionId).toBe("s1-1");
      expect(calls[1]?.body).toMatchObject({ response, intervention_id: "s1-1" });
      expect(fn).not.toHaveBeenCalled();
    },
  );

  it("leaves the intervention pending and reports its id on BLOCK", async () => {
    const { client, calls } = setup(jsonResponse(makeActionResult("BLOCK")));
    const error = (await guard(client, "s1", "wire_money", () => 1, { onAsk: () => true }).catch(
      (e: unknown) => e,
    )) as ActionBlockedError;
    expect(error).toBeInstanceOf(ActionBlockedError);
    expect(error.sessionId).toBe("s1");
    expect(error.interventionId).toBe("s1-1");
    expect(calls).toHaveLength(1);
  });

  it("reports the pending intervention when no onAsk is given", async () => {
    const { client, calls } = setup(jsonResponse(makeActionResult("ASK_HUMAN")));
    const error = (await guard(client, "s1", "send_email", () => 1).catch((e: unknown) => e)) as InterventionRequiredError;
    expect(error).toBeInstanceOf(InterventionRequiredError);
    expect(error.interventionId).toBe("s1-1");
    expect(calls).toHaveLength(1);
  });

  it("rejects unknown onAsk responses without recording them", async () => {
    const { client, calls } = setup(jsonResponse(makeActionResult("ASK_HUMAN")));
    const fn = vi.fn();
    const onAsk = (() => "maybe") as unknown as () => ResponseName;
    await expect(guard(client, "s1", "send_email", fn, { onAsk })).rejects.toThrow(
      'onAsk returned an unknown response: "maybe"',
    );
    expect(calls).toHaveLength(1);
    expect(fn).not.toHaveBeenCalled();
  });

  it("propagates API errors", async () => {
    const { client } = setup(jsonResponse({ detail: "Simulated sessions are driven by POST /api/v1/session/{id}/step" }, 409));
    const fn = vi.fn();
    await expect(guard(client, "demo-session", "x", fn)).rejects.toMatchObject({ status: 409 });
    expect(fn).not.toHaveBeenCalled();
  });
});

describe("withGuard", () => {
  it("merges static and dynamic signals and passes the arguments through", async () => {
    const { client, calls } = setup(jsonResponse(makeActionResult("CONTINUE")));
    const send = withGuard(
      client,
      "s1",
      {
        signals: { consequence: "external_communication", reversible: false },
        contextFn: (_to: string, draftConfidence: number) => ({ agent_confidence: draftConfidence }),
      },
      async function sendEmail(to: string, draftConfidence: number) {
        return `${to}:${draftConfidence}`;
      },
    );
    await expect(send("prof@example.edu", 0.8)).resolves.toBe("prof@example.edu:0.8");
    expect(calls[0]?.body).toStrictEqual({
      session_id: "s1",
      context: { consequence: "external_communication", reversible: false, agent_confidence: 0.8, action: "sendEmail" },
    });
  });

  it("uses an explicit action name and the onAsk handler", async () => {
    const { client, calls } = setup(jsonResponse(makeDecision("ASK_HUMAN")));
    const onAsk = vi.fn(() => true);
    const wrapped = withGuard(client, { policy: "adaptive" }, { action: "post_comment", onAsk }, (text: string) =>
      text.toUpperCase(),
    );
    await expect(wrapped("hi")).resolves.toBe("HI");
    expect(calls[0]?.body).toMatchObject({ context: { action: "post_comment" } });
    expect(onAsk).toHaveBeenCalledOnce();
  });

  it("requires an action name for anonymous functions", () => {
    const { client } = setup();
    expect(() => withGuard(client, {}, {}, () => 1)).toThrow(TypeError);
  });
});

describe("decision helpers", () => {
  it("classify decisions like the Python SDK", () => {
    expect(["CONTINUE", "DEFER", "CLARIFY", "ASK_HUMAN", "BLOCK"].map((d) => shouldProceed(d as DecisionType))).toEqual(
      [true, true, false, false, false],
    );
    expect(shouldAsk(makeDecision("CLARIFY"))).toBe(true);
    expect(shouldAsk("BLOCK")).toBe(false);
    expect(isBlocked("BLOCK")).toBe(true);
    expect(interrupts("BLOCK")).toBe(true);
    expect(interrupts("DEFER")).toBe(false);
    expect(isDecisionType("ASK_HUMAN")).toBe(true);
    expect(isDecisionType("ask_human")).toBe(false);
    expect(isResponseName("cancel_task")).toBe(true);
    expect(isResponseName("cancel")).toBe(false);
  });
});
