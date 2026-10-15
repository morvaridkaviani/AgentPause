/**
 * Gate any function (a tool call, an API request, a file write) with AgentPause.
 *
 * Mirrors the Python SDK's `agentpause.integrations.guard`: CONTINUE and DEFER run the
 * function; CLARIFY and ASK_HUMAN ask the human through `onAsk` (or throw
 * {@link InterventionRequiredError} when no handler is given); BLOCK throws
 * {@link ActionBlockedError}.
 *
 * AgentPause decides *when to involve a human*. It is not a security boundary: keep your
 * own permission checks, sandboxing and least-privilege credentials.
 */

import type { AgentPauseClient, EvaluateOptions, RequestOptions } from "./client.js";
import { PROCEED_RESPONSES, isBlocked, isResponseName, shouldProceed } from "./decision.js";
import type { ActionContextInput, Decision, ResponseName } from "./types.js";

/**
 * Where decisions come from:
 * - a session id (string) or `{ sessionId }`: an `api` session. Actions go to
 *   `POST /api/v1/action` and the human's response is recorded with `POST /api/v1/intervention`,
 *   so the server keeps history, habituation and deferred questions.
 * - {@link EvaluateOptions} (`{ policy, preferences, explain, state }`, possibly `{}`):
 *   stateless `POST /api/v1/evaluate`. Nothing is stored and responses are not recorded.
 */
export type GuardTarget = string | { sessionId: string } | EvaluateOptions;

/**
 * What `onAsk` returns: `true`/`false` (approve/reject), a response name, or a response with
 * clarification answers keyed by assumption id.
 */
export type AskResult = boolean | ResponseName | { response: ResponseName; answers?: Record<string, string> };

export interface AskContext {
  /** The action context that was evaluated. */
  action: ActionContextInput;
  /** Session id in session mode, otherwise `null`. */
  sessionId: string | null;
  /** The pending intervention in session mode, otherwise `null`. */
  interventionId: string | null;
}

export interface GuardOptions extends RequestOptions {
  /**
   * Show the intervention (questions, explanation) to the human and return their response.
   * `approve`, `edit`, `answer` and `override` run the function; anything else throws
   * {@link ActionRejectedError}. Without a handler, CLARIFY/ASK_HUMAN throw
   * {@link InterventionRequiredError}.
   */
  onAsk?: (decision: Decision, context: AskContext) => AskResult | Promise<AskResult>;
}

interface GuardErrorContext {
  sessionId: string | null;
  interventionId: string | null;
}

/** Base class of the errors thrown by {@link guard}. */
export class AgentPauseGuardError extends Error {
  override name = "AgentPauseGuardError";
  readonly decision: Decision;
  /** Session id in session mode, otherwise `null`. */
  readonly sessionId: string | null;
  /**
   * The server-side intervention in session mode. When it is still pending (BLOCK, no `onAsk`,
   * `ask_why`), resolve it with `client.respond(sessionId, response, { interventionId })`
   * before submitting the next action.
   */
  readonly interventionId: string | null;

  constructor(message: string, decision: Decision, context: GuardErrorContext) {
    super(message);
    this.decision = decision;
    this.sessionId = context.sessionId;
    this.interventionId = context.interventionId;
  }
}

/**
 * AgentPause wants the human involved (CLARIFY / ASK_HUMAN) and no `onAsk` handler was given.
 * Show `err.decision` to the user, record their answer with `client.respond(...)` (session
 * mode), then retry or skip the action.
 */
export class InterventionRequiredError extends AgentPauseGuardError {
  override name = "InterventionRequiredError";

  constructor(decision: Decision, context: GuardErrorContext) {
    super(decision.explanation || decision.decision, decision, context);
  }
}

/** AgentPause decided BLOCK: the action was not run. Hand control back to the human. */
export class ActionBlockedError extends AgentPauseGuardError {
  override name = "ActionBlockedError";

  constructor(decision: Decision, context: GuardErrorContext) {
    super(decision.explanation || "Blocked by AgentPause", decision, context);
  }
}

/** The human did not allow the action (reject, takeover, cancel_task, timeout, ask_why). */
export class ActionRejectedError extends AgentPauseGuardError {
  override name = "ActionRejectedError";
  readonly response: ResponseName;

  constructor(decision: Decision, response: ResponseName, context: GuardErrorContext) {
    super(`The user responded '${response}' to ${decision.action}`, decision, context);
    this.response = response;
  }
}

/**
 * Evaluate `action` with AgentPause, then run `fn` only if allowed.
 *
 * ```ts
 * const sent = await guard(client, session.id,
 *   { action: "send_email", consequence: "external_communication", reversible: false },
 *   () => sendEmail(draft),
 *   { onAsk: async (decision) => confirm(decision.explanation) },
 * );
 * ```
 *
 * - CONTINUE / DEFER: runs `fn` and returns its result.
 * - BLOCK: throws {@link ActionBlockedError}; `fn` is not run.
 * - CLARIFY / ASK_HUMAN: calls `onAsk` (throws {@link InterventionRequiredError} without it). In
 *   session mode the response is recorded on the server. `approve`, `edit`, `answer` and
 *   `override` run `fn`; other responses throw {@link ActionRejectedError}.
 */
export async function guard<T>(
  client: AgentPauseClient,
  target: GuardTarget,
  action: string | ActionContextInput,
  fn: () => T | PromiseLike<T>,
  options: GuardOptions = {},
): Promise<T> {
  const { onAsk, signal, timeoutMs } = options;
  const request: RequestOptions = { signal, timeoutMs };
  const context: ActionContextInput = typeof action === "string" ? { action } : action;
  const sessionId = sessionOf(target);

  let decision: Decision;
  let interventionId: string | null = null;
  if (sessionId !== null) {
    const result = await client.submitAction(sessionId, context, request);
    decision = result.decision;
    interventionId = result.intervention_id;
  } else {
    decision = await client.evaluate(context, { ...(target as EvaluateOptions), ...request });
  }
  const errorContext: GuardErrorContext = { sessionId, interventionId };

  if (shouldProceed(decision)) return await fn();
  if (isBlocked(decision)) throw new ActionBlockedError(decision, errorContext);
  if (!onAsk) throw new InterventionRequiredError(decision, errorContext);

  const { response, answers } = normalizeAskResult(await onAsk(decision, { action: context, ...errorContext }));
  if (sessionId !== null) {
    await client.respond(sessionId, response, { ...request, interventionId, answers });
  }
  if (PROCEED_RESPONSES.includes(response)) return await fn();
  throw new ActionRejectedError(decision, response, errorContext);
}

export interface WithGuardOptions<A extends unknown[]> extends GuardOptions {
  /** Action name. Default: the wrapped function's name. */
  action?: string;
  /** Static signals, e.g. `{ consequence: "external_communication", reversible: false }`. */
  signals?: Omit<ActionContextInput, "action">;
  /**
   * Dynamic signals computed from the call arguments (merged over `signals`). Return metadata
   * only (e.g. `{ agent_confidence: 0.7 }`), never secrets or message bodies.
   */
  contextFn?: (...args: A) => Omit<ActionContextInput, "action">;
}

/**
 * Wrap a function so every call goes through {@link guard} (the TypeScript counterpart of the
 * Python `@pause.guard(...)` decorator).
 *
 * ```ts
 * const sendEmail = withGuard(client, session.id,
 *   { signals: { consequence: "external_communication", reversible: false }, onAsk },
 *   async function sendEmail(to: string, subject: string) { ... },
 * );
 * await sendEmail("prof@example.edu", "Draft");
 * ```
 */
export function withGuard<A extends unknown[], R>(
  client: AgentPauseClient,
  target: GuardTarget,
  options: WithGuardOptions<A>,
  fn: (...args: A) => R | PromiseLike<R>,
): (...args: A) => Promise<R> {
  const { action, signals, contextFn, ...guardOptions } = options;
  const name = action || fn.name;
  if (!name) throw new TypeError("withGuard needs an action name: pass `action` or wrap a named function");
  return (...args: A): Promise<R> => {
    const dynamic = contextFn ? contextFn(...args) : {};
    const context: ActionContextInput = { ...signals, ...dynamic, action: name };
    return guard(client, target, context, () => fn(...args), guardOptions);
  };
}

function sessionOf(target: GuardTarget): string | null {
  if (typeof target === "string") return target;
  if ("sessionId" in target && typeof target.sessionId === "string") return target.sessionId;
  return null;
}

function normalizeAskResult(raw: AskResult): { response: ResponseName; answers?: Record<string, string> } {
  if (typeof raw === "boolean") return { response: raw ? "approve" : "reject" };
  const result: { response: unknown; answers?: Record<string, string> } | null =
    typeof raw === "string" ? { response: raw } : typeof raw === "object" ? raw : null;
  if (result === null || !isResponseName(result.response)) {
    const shown = result === null ? raw : result.response;
    throw new TypeError(`onAsk returned an unknown response: ${JSON.stringify(shown) ?? String(shown)}`);
  }
  return result.answers === undefined
    ? { response: result.response }
    : { response: result.response, answers: result.answers };
}
