/**
 * Types mirroring the AgentPause REST API (`/api/v1`).
 *
 * Request types (`*Input`) follow the backend's Pydantic request models; optional fields fall
 * back to the server's documented defaults. Response types follow the response models.
 * Field names are the wire names (snake_case), so values can be passed through unchanged.
 */

// ------------------------------------------------------------------------------- enumerations

/** What AgentPause tells the agent to do with a proposed action. */
export type DecisionType = "CONTINUE" | "CLARIFY" | "ASK_HUMAN" | "DEFER" | "BLOCK";

/** How the human responded to an intervention (`POST /api/v1/intervention`). */
export type ResponseName =
  | "approve"
  | "edit"
  | "reject"
  | "answer"
  | "takeover"
  | "override"
  | "cancel_task"
  | "ask_why"
  | "timeout";

/** Where a signal value came from. */
export type Provenance = "agent_provided" | "user_provided" | "estimated" | "inferred" | "simulated" | "default";

/** Coarse category of an action's real-world consequence (sets default severity/recoverability priors). */
export type ConsequenceCategory =
  | "read_only"
  | "internal_draft"
  | "local_modification"
  | "data_entry"
  | "external_communication"
  | "scheduling"
  | "financial_transaction"
  | "data_deletion"
  | "data_sharing"
  | "account_change"
  | "other";

/** Type of missing information behind an intent assumption. */
export type AssumptionKind = "goal" | "constraint" | "input" | "context";

/** The form of the human-facing intervention recommended with a decision. */
export type InterventionKind = "none" | "clarification" | "confirmation" | "batched_review" | "takeover" | "scheduled";

/** Explanation detail computed by `POST /api/v1/evaluate`. */
export type ExplainLevel = "full" | "light" | "none";

/** Explanation condition applied to decisions shown in study sessions. */
export type ExplanationMode = "full" | "factors" | "placebo" | "none";

export type SessionMode = "demo" | "study" | "api";
export type SessionKind = "simulated" | "external";
export type SessionStatus = "running" | "awaiting_human" | "completed" | "cancelled";
export type RiskLevel = "low" | "medium" | "high";
export type Level = "LOW" | "MEDIUM" | "HIGH";
export type StepUntil = "next" | "intervention" | "end";
export type ExperimentStatus = "queued" | "running" | "completed" | "failed";

/** Consequence category, or one of the aliases the engine accepts. */
export type ConsequenceInput = ConsequenceCategory | (string & {});

// ------------------------------------------------------------------------------- requests

/** An interpretation of the user's intent that the action depends on. */
export interface AssumptionInput {
  id: string;
  description: string;
  /** Agent's confidence that the assumption is right, in [0, 1]. */
  confidence: number;
  kind?: AssumptionKind;
  options?: string[];
  agent_value?: string | null;
}

/** An upcoming action, used for timing lookahead (DEFER). */
export interface PlannedActionInput {
  step: number;
  action: string;
  category?: ConsequenceInput;
  description?: string;
  severity?: number | null;
  recoverability?: number | null;
  reversible?: boolean | null;
  depends_on?: string[];
  at_breakpoint?: boolean | null;
  cognitive_load?: number | null;
}

/**
 * A proposed action. Only `action` is required; missing signals use documented defaults.
 * Unit-interval signals must be in [0, 1].
 *
 * Send action *metadata* only. Never send passwords, tokens, or private message content.
 */
export interface ActionContextInput {
  /** Action name, 1 to 128 characters. */
  action: string;
  /** Short description, at most 500 characters. */
  description?: string;
  /** Consequence category or alias (alias of `category`). */
  consequence?: ConsequenceInput | null;
  category?: ConsequenceInput | null;
  severity?: number | null;
  reversible?: boolean | null;
  recoverability?: number | null;
  agent_confidence?: number | null;
  intent_confidence?: number | null;
  task_progress?: number | null;
  at_breakpoint?: boolean | null;
  cognitive_load?: number | null;
  external_effects?: boolean | null;
  requires_human_input?: boolean;
  assumptions?: AssumptionInput[];
  depends_on?: string[];
  plan?: PlannedActionInput[];
  step?: number | null;
  action_key?: string | null;
  /** Where each signal value came from, keyed by signal name (e.g. `{ agent_confidence: "estimated" }`). */
  provenance?: Record<string, Provenance>;
}

/** User autonomy preferences. All fields have server-side defaults. */
export interface PreferencesInput {
  profile?: "fewer_interruptions" | "balanced" | "maximum_control";
  always_ask_categories?: string[];
  never_ask_categories?: string[];
  block_categories?: string[];
  ask_before_irreversible?: boolean;
  ask_before_external?: boolean;
  allow_low_risk_autonomy?: boolean;
  low_risk_threshold?: number;
  max_interruptions_per_task?: number | null;
}

/** A policy by name with optional configuration. A bare string is also accepted wherever a policy is. */
export interface PolicySpecInput {
  /** Policy name (default `"adaptive"`), e.g. `"fixed_threshold"`, `"always_confirm"`. */
  name?: string;
  /** Policy constructor options, e.g. `{ threshold: 0.35 }`. */
  config?: Record<string, unknown>;
  preferences?: PreferencesInput | null;
  /** ModelParameters overrides, e.g. `{ interruption_cost: 0.03 }`. */
  parameters?: Record<string, unknown>;
  label?: string | null;
}

export type PolicyInput = PolicySpecInput | string;

/** Body of `POST /api/v1/evaluate`. */
export interface EvaluateRequest {
  context: ActionContextInput;
  policy?: PolicyInput;
  preferences?: PreferencesInput | null;
  explain?: ExplainLevel;
  /** Optional serialized SessionState (history) to evaluate against. */
  state?: Record<string, unknown> | null;
}

/** Body of `POST /api/v1/session`. */
export interface SessionCreateInput {
  /** `"demo"` (default, simulated agent), `"study"`, or `"api"` (your own agent submits actions). */
  mode?: SessionMode;
  /** Required for demo and study sessions. */
  scenario_id?: string | null;
  policy?: PolicyInput;
  preferences?: PreferencesInput | null;
  /** Random if omitted; stored for reproducibility. */
  seed?: number | null;
  episode?: number;
  explanation_mode?: ExplanationMode;
  participant_code?: string | null;
  block?: number | null;
  condition?: string | null;
}

/** Body of `POST /api/v1/action`. */
export interface ActionRequest {
  session_id: string;
  context: ActionContextInput;
}

/** Body of `POST /api/v1/intervention`. */
export interface InterventionRequest {
  session_id: string;
  intervention_id?: string | null;
  response: ResponseName;
  /** Clarification answers keyed by assumption id. */
  answers?: Record<string, string>;
}

/** One experimental condition (simulated user / engine / model overrides). */
export interface ConditionInput {
  name?: string;
  user?: Record<string, unknown>;
  engine?: Record<string, unknown>;
  parameters?: Record<string, unknown>;
}

/** Body of `POST /api/v1/experiments`. */
export interface ExperimentCreateInput {
  name: string;
  description?: string;
  /** Scenario ids, or `["all"]` (default). */
  scenarios?: string[];
  policies: PolicyInput[];
  episodes?: number;
  seed?: number;
  conditions?: ConditionInput[];
  bootstrap?: number;
}

/** Body of `POST /api/v1/compare`. */
export interface CompareInput {
  scenarios?: string[];
  policies?: PolicyInput[];
  episodes?: number;
  seed?: number;
  user?: Record<string, unknown>;
  engine?: Record<string, unknown>;
  trace_scenario?: string | null;
  trace_episode?: number;
}

/** Query filters of `GET /api/v1/metrics`. */
export interface MetricsFilters {
  source?: "experiment" | "sessions";
  experiment_id?: string;
  scenario?: string;
  policy?: string;
  participant?: string;
  condition?: string;
  risk?: RiskLevel;
  mode?: "demo" | "study";
}

/** Query filters of `GET /api/v1/events`. */
export interface EventFilters {
  session_id?: string;
  mode?: string;
  scenario?: string;
  policy?: string;
  participant?: string;
  decision?: string;
  risk?: RiskLevel;
  type?: string;
  interventions_only?: boolean;
  offset?: number;
  limit?: number;
}

/** Query filters of `GET /api/v1/sessions`. */
export interface SessionFilters {
  mode?: string;
  scenario?: string;
  policy?: string;
  participant?: string;
  status?: string;
  offset?: number;
  limit?: number;
}

/** Body of `PATCH /api/v1/study/participants/{code}`. */
export interface ParticipantUpdate {
  consented?: boolean | null;
  completed?: boolean | null;
}

/** Body of `POST /api/v1/study/responses`. */
export interface QuestionnaireInput {
  participant_code: string;
  instrument_id: string;
  session_id?: string | null;
  block?: number | null;
  responses: Record<string, number | string>;
}

// ------------------------------------------------------------------------------- decisions

/** One signal's role in a decision. */
export interface Factor {
  signal: string;
  label: string;
  value: number | boolean | string | null;
  display: string;
  level: Level | null;
  provenance: Provenance;
  /** Change in the decision score when this signal is moved to its low-risk reference value. */
  contribution: number;
  direction: "toward_intervention" | "toward_autonomy" | "neutral";
  description: string;
}

/** A question to put to the human now. */
export interface Question {
  id: string;
  kind: InterventionKind;
  prompt: string;
  assumption_id: string | null;
  options: string[];
  agent_value: string | null;
  benefit: number;
  cost: number;
  value: number;
  /** True if the question was batched into an interruption that was happening anyway. */
  piggybacked: boolean;
}

/** A question scheduled for a later step (DEFER). */
export interface DeferredQuestion {
  assumption_id: string;
  description: string;
  kind: AssumptionKind;
  created_step: number;
  target_step: number;
  target_action: string | null;
  deadline_step: number | null;
  deadline_action: string | null;
  value_now: number;
  value_at_target: number;
}

/** A minimal change that would have produced a different decision. */
export interface Counterfactual {
  kind: "feature" | "timing";
  text: string;
  signal: string | null;
  original_value: unknown;
  counterfactual_value: unknown;
  original_decision: DecisionType | null;
  counterfactual_decision: DecisionType | null;
}

export interface TimingNote {
  step: number;
  action: string;
  text: string;
  decision: DecisionType | null;
  value: number | null;
  feasible: boolean;
}

/** Answers to "Why now?", "Why not earlier?" and "Why not later?". */
export interface Timing {
  why_now: string;
  why_not_earlier: string;
  why_not_later: string;
  earlier: TimingNote[];
  later: TimingNote[];
}

/** The value of asking a given question at a given step. */
export interface TimingCandidate {
  step: number;
  action: string;
  feasible: boolean;
  benefit: number;
  interruption_cost: number;
  rework_cost: number;
  value: number;
  at_breakpoint: boolean | null;
  batched: boolean;
  note: string;
}

/** Timing analysis for one question (the action approval or one assumption). */
export interface ItemTiming {
  item_id: string;
  label: string;
  is_assumption: boolean;
  deferrable: boolean;
  commitment_step: number | null;
  commitment_action: string | null;
  candidates: TimingCandidate[];
  chosen_step: number | null;
}

/** AgentPause's decision for one proposed action, with its explanation. */
export interface Decision {
  decision: DecisionType;
  /** Intervention pressure in [0, 1]. */
  score: number;
  /** Decision stability under perturbation of estimated/default signals. */
  confidence: number | null;
  policy: string;
  action: string;
  step: number;
  reason_codes: string[];
  explanation: string;
  recommended_intervention: InterventionKind;
  /** True for CLARIFY and ASK_HUMAN. */
  should_ask: boolean;
  questions: Question[];
  deferred: DeferredQuestion[];
  factors: Factor[];
  counterfactuals: Counterfactual[];
  timing: Timing | null;
  item_timings: ItemTiming[];
  /** Model terms (e.g. p_err, C_err, C_int, V) so the decision is fully inspectable. */
  terms: Record<string, unknown>;
  signals: Record<string, unknown> & { provenance?: Record<string, Provenance>; missing?: string[] };
  warnings: string[];
  latency_ms: number | null;
}

// ------------------------------------------------------------------------------- sessions & events

export interface ScenarioSummary {
  id: string;
  name: string;
  agent_name: string;
  domain: string;
  icon: string;
  goal: string;
  description: string;
  n_steps: number;
  n_assumptions: number;
  n_mistakes: number;
  irreversible_steps: string[];
}

/** Full scenario definition (`GET /api/v1/scenarios/{id}`): the summary plus steps, assumptions, brief, etc. */
export type ScenarioDefinition = ScenarioSummary & Record<string, unknown>;

export interface StepInfo {
  index: number;
  id: string;
  label: string;
  subtask: string;
  category: string;
  reversible: boolean;
  breakpoint: boolean;
  requires_human_input: boolean;
}

export interface TimelineItem {
  seq: number;
  step_index: number;
  step_id: string | null;
  label: string;
  description: string;
  decision: DecisionType | "SKIPPED";
  score: number;
  confidence: number | null;
  risk_level: RiskLevel | "unknown";
  signals: Record<string, unknown>;
  reason_codes: string[];
  explanation: string;
  n_questions: number;
  deferred: DeferredQuestion[];
  response: ResponseName | null;
  executed: boolean;
  skipped: boolean;
  harm: string[] | null;
  decision_detail: Decision | null;
}

/**
 * The intervention awaiting a human response. API sessions carry `intervention_id` and
 * `decision`; simulated sessions add a richer card (action preview, assumptions, allowed responses).
 */
export interface PendingIntervention {
  intervention_id: string;
  decision: Decision;
  step_index?: number;
  step_id?: string;
  allowed_responses?: ResponseName[];
  [key: string]: unknown;
}

export interface Session {
  id: string;
  created_at: string;
  mode: SessionMode;
  kind: SessionKind;
  policy: string;
  policy_spec: Record<string, unknown>;
  explanation_mode: ExplanationMode;
  scenario: ScenarioSummary | null;
  brief: string | null;
  status: SessionStatus;
  step_index: number;
  n_steps: number;
  steps: StepInfo[];
  timeline: TimelineItem[];
  pending: PendingIntervention | null;
  pending_questions: DeferredQuestion[];
  outcome: Record<string, unknown> | null;
  participant_code: string | null;
  block: number | null;
  seed: number;
  episode: number;
}

/** One logged event (proposal, decision, intervention, response, execution, ...). */
export interface SessionEvent {
  id: number;
  seq: number;
  session_id: string;
  created_at: string;
  type: string;
  mode: string;
  scenario_id: string | null;
  policy: string;
  participant_code: string | null;
  condition: string | null;
  step_index: number | null;
  action: string | null;
  decision: DecisionType | null;
  score: number | null;
  intervention: boolean;
  risk_level: string | null;
  user_response: string | null;
  latency_ms: number | null;
  payload: Record<string, unknown>;
}

/** Response of `POST /api/v1/session/{id}/step` and `POST /api/v1/intervention`. */
export interface StepResult {
  session: Session;
  events: SessionEvent[];
  decision: Decision | null;
  card: PendingIntervention | null;
}

/** Response of `POST /api/v1/action`. */
export interface ActionResult {
  decision: Decision;
  /** Set when the decision interrupts; pass it to `respond()`. */
  intervention_id: string | null;
  session: Session;
}

export interface Page<T> {
  total: number;
  offset: number;
  limit: number;
  items: T[];
}

export type SessionList = Page<Session>;
export type EventList = Page<SessionEvent>;

// ------------------------------------------------------------------------------- meta

export interface HealthInfo {
  status: string;
  version: string;
  environment: string;
  database: string;
  /** True when researcher endpoints require a bearer token. */
  auth: boolean;
  simulated_actions_only: boolean;
}

export interface PolicyInfo {
  name: string;
  summary: string;
  label: string;
  core: boolean;
  study_code: string | null;
  origin: string;
}

export interface MetricDefinition {
  key: string;
  label: string;
  kind: "objective" | "ground_truth" | "simulated";
  higher_is_better: boolean | null;
  numerator: string | null;
  denominator: string | null;
  description: string;
  is_rate: boolean;
}

export interface CategoryPrior {
  severity: number;
  recoverability: number;
  external: boolean;
  description: string;
}

/** Response of `GET /api/v1/model`. */
export interface ModelInfo {
  parameters: Record<string, unknown>;
  category_priors: Record<string, CategoryPrior>;
  reason_codes: Record<string, string>;
  metrics: MetricDefinition[];
}

// ------------------------------------------------------------------------------- research

export type Aggregate = Record<string, unknown> & { policy: string };

export interface Experiment {
  id: string;
  name: string;
  status: ExperimentStatus;
  created_at: string;
  finished_at: string | null;
  config: Record<string, unknown>;
  progress: { done: number; total: number };
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface CompareResult {
  note: string;
  episodes: number;
  seed: number;
  aggregates: Aggregate[];
  by_scenario: Aggregate[];
  comparisons: Record<string, unknown>[];
  traces: Record<string, Record<string, unknown>>;
  trace_scenario: string | null;
}

export interface MetricsCharts {
  policies: string[];
  decisions_by_policy: (Record<string, number | string> & { policy: string })[];
  intervention_timing: { policy: string; bin: string; count: number; share: number }[];
  reasons: { code: string; phrase: string; count: number }[];
  reasons_by_policy: Record<string, { code: string; count: number }[]>;
  risk: { policy: string; risk_level: string; decisions: number; interventions: number; rate: number }[];
  responses: (Record<string, number | string> & { policy: string })[];
  uncertainty: {
    policy: string;
    decision: string;
    n: number;
    mean_agent_confidence: number;
    mean_intent_confidence: number;
  }[];
  summary: (Record<string, number | string | null> & { policy: string })[];
  [key: string]: unknown;
}

/** Response of `GET /api/v1/metrics`. */
export interface Metrics {
  source: "experiment" | "sessions";
  filters: Record<string, unknown>;
  n_episodes: number;
  aggregates: Aggregate[];
  charts: MetricsCharts;
  available: {
    experiments?: { id: string; name: string; created_at: string }[];
    scenarios?: string[];
    policies?: string[];
    conditions?: string[];
    participants?: string[];
  };
  metric_definitions: MetricDefinition[];
  note: string;
}

// ------------------------------------------------------------------------------- study

export interface StudyConfig {
  title: string;
  consent_text: string;
  conditions: string[];
  scenarios: string[];
  practice_scenario: string | null;
  explanation_modes: ExplanationMode[];
  post_task_instruments: string[];
  final_instruments: string[];
  seed_base: number;
}

export interface BlockPlan {
  block: number;
  policy: string;
  scenario_id: string;
  seed: number;
  practice: boolean;
}

export interface Participant {
  code: string;
  number: number;
  explanation_mode: ExplanationMode;
  plan: BlockPlan[];
  consented: boolean;
  completed: boolean;
}

export interface InstrumentItem {
  id: string;
  text: string;
  reverse?: boolean;
  subscale?: string;
  options?: string[];
  correct?: string;
  min_label?: string;
  max_label?: string;
}

/** A questionnaire instrument (definition, licensing, readiness). */
export interface Instrument {
  id: string;
  name: string;
  citation: string;
  doi: string | null;
  source_url: string | null;
  license: string;
  redistributable: boolean;
  validated: boolean;
  construct: string;
  when: "post_task" | "final";
  scale: Record<string, unknown> & { type: "likert" | "slider" | "choice" };
  /** Empty when the item text cannot be redistributed and was not supplied locally. */
  items: InstrumentItem[];
  scoring: Record<string, unknown>;
  notes: string;
  /** True when item text is available, so responses can be submitted. */
  ready: boolean;
  items_source: "bundled" | "local" | "missing";
  [key: string]: unknown;
}

export interface QuestionnaireResult {
  id: number;
  instrument_id: string;
  score: Record<string, unknown> | null;
}
