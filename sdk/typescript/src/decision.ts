/** Runtime constants and predicates for decisions and human responses. */

import type { Decision, DecisionType, ResponseName } from "./types.js";

/** All decision types, in order of increasing human involvement. */
export const DECISION_TYPES: readonly DecisionType[] = ["CONTINUE", "DEFER", "CLARIFY", "ASK_HUMAN", "BLOCK"];

/** All responses accepted by `POST /api/v1/intervention`. */
export const RESPONSE_NAMES: readonly ResponseName[] = [
  "approve",
  "edit",
  "reject",
  "answer",
  "takeover",
  "override",
  "cancel_task",
  "ask_why",
  "timeout",
];

/** Responses after which a guarded action runs (the human allowed it, possibly with changes). */
export const PROCEED_RESPONSES: readonly ResponseName[] = ["approve", "edit", "answer", "override"];

function typeOf(decision: Decision | DecisionType): DecisionType {
  return typeof decision === "string" ? decision : decision.decision;
}

/** True if the agent may execute the action now (CONTINUE or DEFER). */
export function shouldProceed(decision: Decision | DecisionType): boolean {
  const type = typeOf(decision);
  return type === "CONTINUE" || type === "DEFER";
}

/** True if the human must be asked before the action runs (CLARIFY or ASK_HUMAN). */
export function shouldAsk(decision: Decision | DecisionType): boolean {
  const type = typeOf(decision);
  return type === "CLARIFY" || type === "ASK_HUMAN";
}

/** True if the action must not run (BLOCK). */
export function isBlocked(decision: Decision | DecisionType): boolean {
  return typeOf(decision) === "BLOCK";
}

/** True if the decision interrupts the human now (CLARIFY, ASK_HUMAN or BLOCK). */
export function interrupts(decision: Decision | DecisionType): boolean {
  return shouldAsk(decision) || isBlocked(decision);
}

export function isDecisionType(value: unknown): value is DecisionType {
  return typeof value === "string" && (DECISION_TYPES as readonly string[]).includes(value);
}

export function isResponseName(value: unknown): value is ResponseName {
  return typeof value === "string" && (RESPONSE_NAMES as readonly string[]).includes(value);
}
