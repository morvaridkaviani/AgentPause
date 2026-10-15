"""Endpoint-specific request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .common import ActionContextIn, DecisionOut, EventOut, Page, PolicySpecIn, PreferencesIn

ExplainLevel = Literal["full", "light", "none"]
ExplanationMode = Literal["full", "factors", "placebo", "none"]
ResponseName = Literal[
    "approve", "edit", "reject", "answer", "takeover", "override", "cancel_task", "ask_why", "timeout"
]


def _core_policies() -> list[PolicySpecIn | str]:
    return ["full_autonomy", "always_confirm", "fixed_threshold", "adaptive"]


def _all_explanation_modes() -> list[ExplanationMode]:
    return ["none", "placebo", "factors", "full"]


# ---------------------------------------------------------------- evaluate
class EvaluateRequest(BaseModel):
    """Stateless evaluation of one proposed action."""

    context: ActionContextIn
    policy: PolicySpecIn | str = "adaptive"
    preferences: PreferencesIn | None = None
    explain: ExplainLevel = "full"
    state: dict[str, Any] | None = Field(
        default=None, description="Optional serialized SessionState (history) to evaluate against"
    )


# ---------------------------------------------------------------- sessions
class SessionCreate(BaseModel):
    mode: Literal["demo", "study", "api"] = "demo"
    scenario_id: str | None = Field(default=None, description="Required for demo sessions (simulated agent)")
    policy: PolicySpecIn | str = "adaptive"
    preferences: PreferencesIn | None = None
    seed: int | None = Field(default=None, ge=0, description="Random if omitted; stored for reproducibility")
    episode: int = Field(default=0, ge=0)
    explanation_mode: ExplanationMode = "full"
    participant_code: str | None = Field(default=None, description="Study mode: pseudonymous participant code")
    block: int | None = Field(default=None, ge=0, description="Study mode: index into the participant's plan")
    condition: str | None = None


class StepInfo(BaseModel):
    index: int
    id: str
    label: str
    subtask: str
    category: str
    reversible: bool
    breakpoint: bool
    requires_human_input: bool = False


class TimelineItem(BaseModel):
    seq: int
    step_index: int
    step_id: str | None = None
    label: str
    description: str = ""
    decision: str
    score: float
    confidence: float | None = None
    risk_level: str
    signals: dict[str, Any] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)
    explanation: str = ""
    n_questions: int = 0
    deferred: list[dict[str, Any]] = Field(default_factory=list)
    response: str | None = None
    executed: bool = False
    skipped: bool = False
    harm: list[str] | None = None
    decision_detail: DecisionOut | None = None


class SessionOut(BaseModel):
    id: str
    created_at: str
    mode: str
    kind: str
    policy: str
    policy_spec: dict[str, Any]
    explanation_mode: str
    scenario: dict[str, Any] | None = None
    brief: str | None = None
    status: str
    step_index: int
    n_steps: int
    steps: list[StepInfo] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)
    pending: dict[str, Any] | None = None
    pending_questions: list[dict[str, Any]] = Field(default_factory=list)
    outcome: dict[str, Any] | None = None
    participant_code: str | None = None
    block: int | None = None
    seed: int
    episode: int


class StepRequest(BaseModel):
    until: Literal["next", "intervention", "end"] = "next"


class StepOut(BaseModel):
    session: SessionOut
    events: list[EventOut]
    decision: DecisionOut | None = None
    card: dict[str, Any] | None = None


class InterventionRequest(BaseModel):
    session_id: str
    intervention_id: str | None = None
    response: ResponseName
    answers: dict[str, str] = Field(default_factory=dict)


class ActionRequest(BaseModel):
    session_id: str
    context: ActionContextIn


class ActionOut(BaseModel):
    decision: DecisionOut
    intervention_id: str | None = None
    session: SessionOut


class SessionList(Page):
    items: list[SessionOut]


class EventList(Page):
    items: list[EventOut]


# ---------------------------------------------------------------- experiments & comparison
class ConditionIn(BaseModel):
    name: str = "default"
    user: dict[str, Any] = Field(default_factory=dict, description="SimulatedUserParams overrides")
    engine: dict[str, Any] = Field(default_factory=dict, description="EngineConfig overrides")
    parameters: dict[str, Any] = Field(default_factory=dict, description="ModelParameters overrides for all policies")


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    scenarios: list[str] = Field(default_factory=lambda: ["all"])
    policies: list[PolicySpecIn | str] = Field(min_length=1)
    episodes: int = Field(default=50, ge=1, le=2000)
    seed: int = Field(default=314159, ge=0)
    conditions: list[ConditionIn] = Field(default_factory=list)
    bootstrap: int = Field(default=300, ge=0, le=5000)


class ExperimentOut(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    finished_at: str | None = None
    config: dict[str, Any]
    progress: dict[str, int]
    result: dict[str, Any] | None = None
    error: str | None = None


class CompareRequest(BaseModel):
    scenarios: list[str] = Field(default_factory=lambda: ["all"])
    policies: list[PolicySpecIn | str] = Field(default_factory=_core_policies)
    episodes: int = Field(default=30, ge=1, le=300)
    seed: int = Field(default=314159, ge=0)
    user: dict[str, Any] = Field(default_factory=dict)
    engine: dict[str, Any] = Field(default_factory=dict)
    trace_scenario: str | None = Field(default=None, description="Scenario for the per-policy example trace")
    trace_episode: int = Field(default=0, ge=0)


class CompareOut(BaseModel):
    note: str
    episodes: int
    seed: int
    aggregates: list[dict[str, Any]]
    by_scenario: list[dict[str, Any]]
    comparisons: list[dict[str, Any]]
    traces: dict[str, dict[str, Any]]
    trace_scenario: str | None = None


class MetricsOut(BaseModel):
    source: str
    filters: dict[str, Any]
    n_episodes: int
    aggregates: list[dict[str, Any]]
    charts: dict[str, Any]
    available: dict[str, list[Any]]
    metric_definitions: list[dict[str, Any]]
    note: str


# ---------------------------------------------------------------- study
class StudyConfig(BaseModel):
    title: str = "AgentPause study"
    consent_text: str = (
        "This study investigates how an AI agent should decide when to ask you for input. You will "
        "supervise a simulated assistant in several short tasks. All actions are simulated: no real "
        "emails, purchases, or files are affected. We record your decisions and questionnaire answers "
        "under a random code. We do not collect your name or contact details. You may stop at any time."
    )
    conditions: list[str] = Field(
        default_factory=lambda: ["full_autonomy", "always_confirm", "fixed_threshold", "adaptive"]
    )
    scenarios: list[str] = Field(default_factory=lambda: ["travel", "email", "shopping", "calendar"])
    practice_scenario: str | None = "files"
    explanation_modes: list[ExplanationMode] = Field(default_factory=_all_explanation_modes)
    post_task_instruments: list[str] = Field(default_factory=lambda: ["agentpause_post_task", "nasa_tlx_raw"])
    final_instruments: list[str] = Field(default_factory=lambda: ["timing_comprehension"])
    seed_base: int = 900000


class BlockPlan(BaseModel):
    block: int
    policy: str
    scenario_id: str
    seed: int
    practice: bool = False


class ParticipantOut(BaseModel):
    code: str
    number: int
    explanation_mode: str
    plan: list[BlockPlan]
    consented: bool
    completed: bool


class ParticipantUpdate(BaseModel):
    consented: bool | None = None
    completed: bool | None = None


class QuestionnaireIn(BaseModel):
    participant_code: str
    instrument_id: str
    session_id: str | None = None
    block: int | None = None
    responses: dict[str, float | int | str]


class QuestionnaireOut(BaseModel):
    id: int
    instrument_id: str
    score: dict[str, Any] | None = None
