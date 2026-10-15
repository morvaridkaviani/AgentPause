/**
 * @agentpause/sdk: typed TypeScript/JavaScript client for the AgentPause REST API.
 *
 * AgentPause decides when an AI agent should continue autonomously and when it should pause
 * and involve a human. It is research software and not a security boundary.
 */

export {
  AgentPauseClient,
  API_PREFIX,
  DEFAULT_BASE_URL,
  DEFAULT_TIMEOUT_MS,
  type AgentPauseClientOptions,
  type EvaluateOptions,
  type HttpMethod,
  type QueryValue,
  type RawRequestOptions,
  type RequestOptions,
  type RespondOptions,
  type WaitForExperimentOptions,
} from "./client.js";
export {
  DECISION_TYPES,
  PROCEED_RESPONSES,
  RESPONSE_NAMES,
  interrupts,
  isBlocked,
  isDecisionType,
  isResponseName,
  shouldAsk,
  shouldProceed,
} from "./decision.js";
export { AgentPauseConnectionError, AgentPauseError, AgentPauseTimeoutError, formatDetail } from "./errors.js";
export {
  ActionBlockedError,
  ActionRejectedError,
  AgentPauseGuardError,
  InterventionRequiredError,
  guard,
  withGuard,
  type AskContext,
  type AskResult,
  type GuardOptions,
  type GuardTarget,
  type WithGuardOptions,
} from "./guard.js";
export type * from "./types.js";
