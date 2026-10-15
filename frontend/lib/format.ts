import type { DecisionType, Provenance, TimelineDecision } from "./types";

export const DECISION_ORDER: DecisionType[] = ["CONTINUE", "DEFER", "CLARIFY", "ASK_HUMAN", "BLOCK"];

export const DECISION_META: Record<
  TimelineDecision,
  { label: string; short: string; plain: string; tint: string; color: string; description: string }
> = {
  CONTINUE: {
    label: "Continue",
    short: "Continue",
    plain: "Went ahead",
    tint: "tint-continue",
    color: "var(--d-continue)",
    description: "The agent acts without involving you.",
  },
  DEFER: {
    label: "Defer",
    short: "Defer",
    plain: "Will ask later",
    tint: "tint-defer",
    color: "var(--d-defer)",
    description: "This step runs now; a question is scheduled for a better moment, before anything irreversible.",
  },
  CLARIFY: {
    label: "Clarify",
    short: "Clarify",
    plain: "Asked a question",
    tint: "tint-clarify",
    color: "var(--d-clarify)",
    description: "A quick question about what you meant, before acting.",
  },
  ASK_HUMAN: {
    label: "Ask human",
    short: "Ask",
    plain: "Asked for approval",
    tint: "tint-ask",
    color: "var(--d-ask)",
    description: "You approve, edit, or reject this specific action first.",
  },
  BLOCK: {
    label: "Block",
    short: "Block",
    plain: "Stopped",
    tint: "tint-block",
    color: "var(--d-block)",
    description: "The agent stops and hands control back to you.",
  },
  SKIPPED: {
    label: "Skipped",
    short: "Skipped",
    plain: "Skipped",
    tint: "tint-skipped",
    color: "var(--d-skipped)",
    description: "Not needed given your answer.",
  },
};

export const PROVENANCE_LABEL: Record<Provenance, string> = {
  agent_provided: "Agent-reported",
  user_provided: "You set this",
  estimated: "Estimated",
  inferred: "Inferred",
  simulated: "Simulated",
  default: "Default (missing)",
};

export const PROVENANCE_HELP: Record<Provenance, string> = {
  agent_provided: "Reported by the agent; not independently verified.",
  user_provided: "Provided by you (a preference or setting).",
  estimated: "Estimated by a model or heuristic.",
  inferred: "Derived by AgentPause from other signals or your history.",
  simulated: "Produced by the simulator for this demo.",
  default: "Not provided; a documented default prior was used.",
};

export const RESPONSE_LABEL: Record<string, string> = {
  approve: "Approved",
  edit: "Edited",
  reject: "Rejected",
  answer: "Answered",
  takeover: "Took over",
  override: "Overrode block",
  cancel_task: "Cancelled task",
  ask_why: "Asked why",
  timeout: "Timed out",
};

export const POLICY_LABEL: Record<string, string> = {
  full_autonomy: "Full autonomy",
  always_confirm: "Always confirm",
  fixed_threshold: "Fixed risk threshold",
  adaptive: "Adaptive (AgentPause)",
  user_customized: "User-customized",
  myopic_voi: "Myopic value of asking",
  rule_based: "Rule-based",
  confidence_threshold: "Confidence threshold",
  learned: "Learned (experimental)",
};

export function policyLabel(name: string): string {
  return POLICY_LABEL[name] ?? name.replace(/_/g, " ");
}

export const CATEGORY_LABEL: Record<string, string> = {
  read_only: "Read only",
  internal_draft: "Internal draft",
  data_entry: "Data entry",
  local_modification: "Local change",
  scheduling: "Scheduling",
  external_communication: "External communication",
  account_change: "Account change",
  data_deletion: "Data deletion",
  data_sharing: "Data sharing",
  financial_transaction: "Financial transaction",
  other: "Other",
};

export function categoryLabel(name: string): string {
  return CATEGORY_LABEL[name] ?? name.replace(/_/g, " ");
}

export function pct(value: unknown, digits = 0): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function num(value: unknown, digits = 2): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function seconds(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  if (value < 60) return `${value.toFixed(0)} s`;
  return `${Math.floor(value / 60)} min ${Math.round(value % 60)} s`;
}

export function level(value: number | null | undefined, kind: "confidence" | "risk" | "reversibility" | "load"): "LOW" | "MEDIUM" | "HIGH" | "—" {
  if (value === null || value === undefined) return "—";
  if (kind === "confidence") return value >= 0.85 ? "HIGH" : value >= 0.65 ? "MEDIUM" : "LOW";
  if (kind === "reversibility") return value >= 0.8 ? "HIGH" : value >= 0.4 ? "MEDIUM" : "LOW";
  if (kind === "load") return value >= 0.6 ? "HIGH" : value >= 0.3 ? "MEDIUM" : "LOW";
  return value >= 0.6 ? "HIGH" : value >= 0.25 ? "MEDIUM" : "LOW";
}

export function stepLabel(index: number): string {
  return `Step ${index + 1}`;
}

export function titleCase(text: string): string {
  return text.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
