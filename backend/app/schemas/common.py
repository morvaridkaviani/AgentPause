"""Shared request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Unit = Field(default=None, ge=0.0, le=1.0)


class PreferencesIn(BaseModel):
    """User autonomy preferences (see docs/policies.md, "User-customized")."""

    profile: Literal["fewer_interruptions", "balanced", "maximum_control"] = "balanced"
    always_ask_categories: list[str] = Field(default_factory=list, examples=[["external_communication"]])
    never_ask_categories: list[str] = Field(default_factory=list)
    block_categories: list[str] = Field(default_factory=list)
    ask_before_irreversible: bool = False
    ask_before_external: bool = False
    allow_low_risk_autonomy: bool = False
    low_risk_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    max_interruptions_per_task: int | None = Field(default=None, ge=0)


class PolicySpecIn(BaseModel):
    name: str = Field(default="adaptive", examples=["adaptive", "fixed_threshold", "always_confirm"])
    config: dict[str, Any] = Field(default_factory=dict, examples=[{"threshold": 0.35}])
    preferences: PreferencesIn | None = None
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="ModelParameters overrides, e.g. {'interruption_cost': 0.03}"
    )
    label: str | None = None


class AssumptionIn(BaseModel):
    id: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    kind: Literal["goal", "constraint", "input", "context"] = "input"
    options: list[str] = Field(default_factory=list)
    agent_value: str | None = None


class PlannedActionIn(BaseModel):
    step: int = Field(ge=0)
    action: str
    category: str = "other"
    description: str = ""
    severity: float | None = Unit
    recoverability: float | None = Unit
    reversible: bool | None = None
    depends_on: list[str] = Field(default_factory=list)
    at_breakpoint: bool | None = None
    cognitive_load: float | None = Unit


class ActionContextIn(BaseModel):
    """A proposed action. Only ``action`` is required. Missing signals use documented defaults.

    Send *metadata* only. Never send passwords, tokens, or message bodies.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "action": "send_email",
                    "description": "Send the drafted email to Professor Smith",
                    "consequence": "external_communication",
                    "reversible": False,
                    "intent_confidence": 0.72,
                    "agent_confidence": 0.86,
                    "task_progress": 0.91,
                }
            ]
        }
    )

    action: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=500)
    consequence: str | None = Field(default=None, description="Consequence category or alias (alias of 'category')")
    category: str | None = None
    severity: float | None = Unit
    reversible: bool | None = None
    recoverability: float | None = Unit
    agent_confidence: float | None = Unit
    intent_confidence: float | None = Unit
    task_progress: float | None = Unit
    at_breakpoint: bool | None = None
    cognitive_load: float | None = Unit
    external_effects: bool | None = None
    requires_human_input: bool = False
    assumptions: list[AssumptionIn] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    plan: list[PlannedActionIn] = Field(default_factory=list)
    step: int | None = Field(default=None, ge=0)
    action_key: str | None = None
    provenance: dict[
        str, Literal["agent_provided", "user_provided", "estimated", "inferred", "simulated", "default"]
    ] = Field(default_factory=dict)

    def to_engine_kwargs(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        data.pop("action")
        return data


class FactorOut(BaseModel):
    signal: str
    label: str
    value: Any = None
    display: str
    level: str | None = None
    provenance: str
    contribution: float
    direction: str
    description: str = ""


class QuestionOut(BaseModel):
    id: str
    kind: str
    prompt: str
    assumption_id: str | None = None
    options: list[str] = Field(default_factory=list)
    agent_value: str | None = None
    benefit: float = 0.0
    cost: float = 0.0
    value: float = 0.0
    piggybacked: bool = False


class DeferredOut(BaseModel):
    assumption_id: str
    description: str
    kind: str
    created_step: int
    target_step: int
    target_action: str | None = None
    deadline_step: int | None = None
    deadline_action: str | None = None
    value_now: float
    value_at_target: float


class CounterfactualOut(BaseModel):
    kind: str
    text: str
    signal: str | None = None
    original_value: Any = None
    counterfactual_value: Any = None
    original_decision: str | None = None
    counterfactual_decision: str | None = None


class TimingNoteOut(BaseModel):
    step: int
    action: str
    text: str
    decision: str | None = None
    value: float | None = None
    feasible: bool = True


class TimingOut(BaseModel):
    why_now: str
    why_not_earlier: str
    why_not_later: str
    earlier: list[TimingNoteOut] = Field(default_factory=list)
    later: list[TimingNoteOut] = Field(default_factory=list)


class DecisionOut(BaseModel):
    """AgentPause's decision for one proposed action, with its full explanation."""

    decision: Literal["CONTINUE", "CLARIFY", "ASK_HUMAN", "DEFER", "BLOCK"]
    score: float
    confidence: float | None = None
    policy: str
    action: str
    step: int
    reason_codes: list[str]
    explanation: str
    recommended_intervention: str
    should_ask: bool
    questions: list[QuestionOut] = Field(default_factory=list)
    deferred: list[DeferredOut] = Field(default_factory=list)
    factors: list[FactorOut] = Field(default_factory=list)
    counterfactuals: list[CounterfactualOut] = Field(default_factory=list)
    timing: TimingOut | None = None
    item_timings: list[dict[str, Any]] = Field(default_factory=list)
    terms: dict[str, Any] = Field(default_factory=dict)
    signals: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    latency_ms: float | None = None


class EventOut(BaseModel):
    id: int
    seq: int
    session_id: str
    created_at: str
    type: str
    mode: str
    scenario_id: str | None = None
    policy: str
    participant_code: str | None = None
    condition: str | None = None
    step_index: int | None = None
    action: str | None = None
    decision: str | None = None
    score: float | None = None
    intervention: bool = False
    risk_level: str | None = None
    user_response: str | None = None
    latency_ms: float | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class Page(BaseModel):
    total: int
    offset: int
    limit: int
