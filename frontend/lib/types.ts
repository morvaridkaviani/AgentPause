/** Types mirroring the AgentPause REST API (see /docs for the OpenAPI schema). */

export type DecisionType = "CONTINUE" | "CLARIFY" | "ASK_HUMAN" | "DEFER" | "BLOCK";
export type TimelineDecision = DecisionType | "SKIPPED";
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
export type Provenance = "agent_provided" | "user_provided" | "estimated" | "inferred" | "simulated" | "default";
export type ExplanationMode = "full" | "factors" | "placebo" | "none";

export interface Factor {
  signal: string;
  label: string;
  value: number | boolean | string | null;
  display: string;
  level: "LOW" | "MEDIUM" | "HIGH" | null;
  provenance: Provenance;
  contribution: number;
  direction: "toward_intervention" | "toward_autonomy" | "neutral";
  description: string;
}

export interface Question {
  id: string;
  kind: string;
  prompt: string;
  assumption_id: string | null;
  options: string[];
  agent_value: string | null;
  benefit: number;
  cost: number;
  value: number;
  piggybacked: boolean;
}

export interface DeferredQuestion {
  assumption_id: string;
  description: string;
  kind: string;
  created_step: number;
  target_step: number;
  target_action: string | null;
  deadline_step: number | null;
  deadline_action: string | null;
  value_now: number;
  value_at_target: number;
}

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

export interface Timing {
  why_now: string;
  why_not_earlier: string;
  why_not_later: string;
  earlier: TimingNote[];
  later: TimingNote[];
}

export interface Decision {
  decision: DecisionType;
  score: number;
  confidence: number | null;
  policy: string;
  action: string;
  step: number;
  reason_codes: string[];
  explanation: string;
  recommended_intervention: string;
  should_ask: boolean;
  questions: Question[];
  deferred: DeferredQuestion[];
  factors: Factor[];
  counterfactuals: Counterfactual[];
  timing: Timing | null;
  item_timings: Record<string, unknown>[];
  terms: Record<string, unknown>;
  signals: Record<string, unknown> & { provenance?: Record<string, Provenance>; missing?: string[] };
  warnings: string[];
  latency_ms: number | null;
}

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
  decision: TimelineDecision;
  score: number;
  confidence: number | null;
  risk_level: "low" | "medium" | "high" | "unknown";
  signals: Record<string, unknown> & { provenance?: Record<string, Provenance> };
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

export interface CardAssumption {
  id: string;
  description: string;
  kind: string;
  agent_value: string;
  options: string[];
  confidence: number;
  if_wrong: string;
}

export interface InterventionCard {
  intervention_id: string;
  step_index: number;
  step_id?: string;
  decision: Decision;
  has_confirmation?: boolean;
  assumption_ids?: string[];
  recent_interruptions?: number;
  action?: {
    label: string;
    description: string;
    category: string;
    consequence: string;
    undo: string;
    reversible: boolean;
    recoverability: number;
    severity: number;
    what_could_go_wrong: string;
    preview: Record<string, string>;
    alternatives: string[];
    requires_human_input: boolean;
    agent_confidence: number;
    simulated: boolean;
  };
  assumptions?: CardAssumption[];
  allowed_responses?: ResponseName[];
}

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

export interface Session {
  id: string;
  created_at: string;
  mode: "demo" | "study" | "api";
  kind: "simulated" | "external";
  policy: string;
  policy_spec: Record<string, unknown>;
  explanation_mode: ExplanationMode;
  scenario: ScenarioSummary | null;
  brief: string | null;
  status: "running" | "awaiting_human" | "completed" | "cancelled";
  step_index: number;
  n_steps: number;
  steps: StepInfo[];
  timeline: TimelineItem[];
  pending: InterventionCard | null;
  pending_questions: DeferredQuestion[];
  outcome: Record<string, unknown> | null;
  participant_code: string | null;
  block: number | null;
  seed: number;
  episode: number;
}

export interface StepResponse {
  session: Session;
  events: ApiEvent[];
  decision: Decision | null;
  card: InterventionCard | null;
}

export interface ApiEvent {
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

export interface PolicyInfo {
  name: string;
  summary: string;
  label: string;
  core: boolean;
  study_code: string | null;
  origin: string;
}

export interface Preferences {
  profile: "fewer_interruptions" | "balanced" | "maximum_control";
  always_ask_categories: string[];
  never_ask_categories: string[];
  block_categories: string[];
  ask_before_irreversible: boolean;
  ask_before_external: boolean;
  allow_low_risk_autonomy: boolean;
  low_risk_threshold: number;
  max_interruptions_per_task: number | null;
}

export interface PolicySpec {
  name: string;
  config?: Record<string, unknown>;
  preferences?: Preferences | null;
  parameters?: Record<string, unknown>;
  label?: string | null;
}

export type Aggregate = Record<string, unknown> & { policy: string; episodes: number };

export interface CompareResult {
  note: string;
  episodes: number;
  seed: number;
  aggregates: Aggregate[];
  by_scenario: Aggregate[];
  comparisons: Record<string, unknown>[];
  traces: Record<string, { steps: TraceStep[]; outcome: Record<string, unknown> }>;
  trace_scenario: string | null;
}

export interface TraceStep {
  step_index: number;
  step_id: string;
  label: string;
  decision: DecisionType;
  n_questions: number;
  n_deferred: number;
  intervention: boolean;
  necessary: boolean | null;
  error_present: boolean;
  user_response: string | null;
}

export interface Experiment {
  id: string;
  name: string;
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  finished_at: string | null;
  config: Record<string, unknown> & { policies?: { name: string; label?: string }[]; scenarios?: string[]; episodes?: number; seed?: number };
  progress: { done: number; total: number };
  result: (Record<string, unknown> & { aggregates?: Aggregate[]; comparisons?: Record<string, unknown>[]; result_hash?: string; duration_s?: number; by_scenario?: Aggregate[] }) | null;
  error: string | null;
}

export interface MetricDefinition {
  key: string;
  label: string;
  kind: "objective" | "ground_truth" | "simulated";
  higher_is_better: boolean | null;
  description: string;
  is_rate: boolean;
}

export interface Metrics {
  source: "experiment" | "sessions";
  filters: Record<string, unknown>;
  n_episodes: number;
  aggregates: Aggregate[];
  charts: {
    policies: string[];
    decisions_by_policy: (Record<string, number | string> & { policy: string })[];
    intervention_timing: { policy: string; bin: string; count: number; share: number }[];
    reasons: { code: string; phrase: string; count: number }[];
    risk: { policy: string; risk_level: string; decisions: number; interventions: number; rate: number }[];
    responses: (Record<string, number | string> & { policy: string })[];
    uncertainty: { policy: string; decision: string; n: number; mean_agent_confidence: number; mean_intent_confidence: number }[];
    summary: (Record<string, number | null | string> & { policy: string })[];
  };
  available: { experiments?: { id: string; name: string; created_at: string }[]; scenarios?: string[]; policies?: string[]; conditions?: string[]; participants?: string[] };
  metric_definitions: MetricDefinition[];
  note: string;
}

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
  scale: { type: "likert" | "slider" | "choice"; min?: number; max?: number; step?: number; min_label?: string; max_label?: string };
  items: InstrumentItem[];
  notes: string;
  ready: boolean;
  items_source: string;
}
