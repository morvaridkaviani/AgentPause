"""Output data model: what AgentPause returns for a proposed action."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import AssumptionKind, DecisionType, InterventionKind, Level, Provenance


@dataclass
class Factor:
    """One signal's role in a decision, for "Why did AgentPause interrupt me?" views."""

    signal: str
    label: str
    value: float | bool | None
    display: str
    level: Level | None
    provenance: Provenance
    contribution: float
    """Change in the decision score when this signal is moved to its low-risk reference value.
    Positive means the signal pushed toward intervening."""
    description: str = ""

    @property
    def direction(self) -> str:
        if self.contribution > 1e-9:
            return "toward_intervention"
        if self.contribution < -1e-9:
            return "toward_autonomy"
        return "neutral"

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "label": self.label,
            "value": self.value,
            "display": self.display,
            "level": self.level.value if self.level else None,
            "provenance": self.provenance.value,
            "contribution": round(self.contribution, 6),
            "direction": self.direction,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Factor:
        return cls(
            signal=data["signal"],
            label=data["label"],
            value=data.get("value"),
            display=data.get("display", ""),
            level=Level(data["level"]) if data.get("level") else None,
            provenance=Provenance(data["provenance"]),
            contribution=float(data.get("contribution", 0.0)),
            description=data.get("description", ""),
        )


@dataclass
class Question:
    """A question to put to the human now (one interruption may batch several)."""

    id: str
    kind: InterventionKind
    prompt: str
    assumption_id: str | None = None
    options: list[str] = field(default_factory=list)
    agent_value: str | None = None
    benefit: float = 0.0
    cost: float = 0.0
    piggybacked: bool = False
    """True if the question was added to an interruption that was happening anyway (batching)."""

    @property
    def value(self) -> float:
        return self.benefit - self.cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "prompt": self.prompt,
            "assumption_id": self.assumption_id,
            "options": list(self.options),
            "agent_value": self.agent_value,
            "benefit": round(self.benefit, 6),
            "cost": round(self.cost, 6),
            "value": round(self.value, 6),
            "piggybacked": self.piggybacked,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Question:
        return cls(
            id=data["id"],
            kind=InterventionKind(data["kind"]),
            prompt=data.get("prompt", ""),
            assumption_id=data.get("assumption_id"),
            options=list(data.get("options", [])),
            agent_value=data.get("agent_value"),
            benefit=float(data.get("benefit", 0.0)),
            cost=float(data.get("cost", 0.0)),
            piggybacked=bool(data.get("piggybacked", False)),
        )


@dataclass
class DeferredQuestion:
    """A question scheduled for a later step (DEFER)."""

    assumption_id: str
    description: str
    kind: AssumptionKind
    created_step: int
    target_step: int
    target_action: str | None
    deadline_step: int | None
    deadline_action: str | None
    value_now: float
    value_at_target: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "assumption_id": self.assumption_id,
            "description": self.description,
            "kind": self.kind.value,
            "created_step": self.created_step,
            "target_step": self.target_step,
            "target_action": self.target_action,
            "deadline_step": self.deadline_step,
            "deadline_action": self.deadline_action,
            "value_now": round(self.value_now, 6),
            "value_at_target": round(self.value_at_target, 6),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeferredQuestion:
        return cls(
            assumption_id=data["assumption_id"],
            description=data.get("description", ""),
            kind=AssumptionKind(data.get("kind", AssumptionKind.INPUT.value)),
            created_step=int(data["created_step"]),
            target_step=int(data["target_step"]),
            target_action=data.get("target_action"),
            deadline_step=data.get("deadline_step"),
            deadline_action=data.get("deadline_action"),
            value_now=float(data.get("value_now", 0.0)),
            value_at_target=float(data.get("value_at_target", 0.0)),
        )


@dataclass
class TimingCandidate:
    """The value of asking a given question at a given step (adaptive policy internals)."""

    step: int
    action: str
    feasible: bool
    benefit: float
    interruption_cost: float
    rework_cost: float
    at_breakpoint: bool | None
    batched: bool = False
    note: str = ""

    @property
    def value(self) -> float:
        return self.benefit - self.interruption_cost - self.rework_cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "feasible": self.feasible,
            "benefit": round(self.benefit, 6),
            "interruption_cost": round(self.interruption_cost, 6),
            "rework_cost": round(self.rework_cost, 6),
            "value": round(self.value, 6),
            "at_breakpoint": self.at_breakpoint,
            "batched": self.batched,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimingCandidate:
        return cls(
            step=int(data["step"]),
            action=data.get("action", ""),
            feasible=bool(data.get("feasible", True)),
            benefit=float(data.get("benefit", 0.0)),
            interruption_cost=float(data.get("interruption_cost", 0.0)),
            rework_cost=float(data.get("rework_cost", 0.0)),
            at_breakpoint=data.get("at_breakpoint"),
            batched=bool(data.get("batched", False)),
            note=data.get("note", ""),
        )


@dataclass
class ItemTiming:
    """Timing analysis for one question (the action approval or one assumption)."""

    item_id: str
    label: str
    is_assumption: bool
    deferrable: bool
    commitment_step: int | None
    commitment_action: str | None
    candidates: list[TimingCandidate]
    chosen_step: int | None
    """Best step to ask, or None if asking is never worth it."""

    @property
    def best(self) -> TimingCandidate | None:
        feasible = [c for c in self.candidates if c.feasible]
        return max(feasible, key=lambda c: c.value) if feasible else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "label": self.label,
            "is_assumption": self.is_assumption,
            "deferrable": self.deferrable,
            "commitment_step": self.commitment_step,
            "commitment_action": self.commitment_action,
            "candidates": [c.to_dict() for c in self.candidates],
            "chosen_step": self.chosen_step,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItemTiming:
        return cls(
            item_id=data["item_id"],
            label=data.get("label", ""),
            is_assumption=bool(data.get("is_assumption", False)),
            deferrable=bool(data.get("deferrable", False)),
            commitment_step=data.get("commitment_step"),
            commitment_action=data.get("commitment_action"),
            candidates=[TimingCandidate.from_dict(c) for c in data.get("candidates", [])],
            chosen_step=data.get("chosen_step"),
        )


@dataclass
class Counterfactual:
    """A minimal change that would have produced a different decision."""

    kind: str  # "feature" | "timing"
    text: str
    signal: str | None = None
    original_value: Any = None
    counterfactual_value: Any = None
    original_decision: DecisionType | None = None
    counterfactual_decision: DecisionType | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "text": self.text,
            "signal": self.signal,
            "original_value": self.original_value,
            "counterfactual_value": self.counterfactual_value,
            "original_decision": self.original_decision.value if self.original_decision else None,
            "counterfactual_decision": self.counterfactual_decision.value if self.counterfactual_decision else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Counterfactual:
        return cls(
            kind=data["kind"],
            text=data["text"],
            signal=data.get("signal"),
            original_value=data.get("original_value"),
            counterfactual_value=data.get("counterfactual_value"),
            original_decision=DecisionType(data["original_decision"]) if data.get("original_decision") else None,
            counterfactual_decision=DecisionType(data["counterfactual_decision"])
            if data.get("counterfactual_decision")
            else None,
        )


@dataclass
class TimingNote:
    step: int
    action: str
    text: str
    decision: DecisionType | None = None
    value: float | None = None
    feasible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "text": self.text,
            "decision": self.decision.value if self.decision else None,
            "value": None if self.value is None else round(self.value, 6),
            "feasible": self.feasible,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimingNote:
        return cls(
            step=int(data["step"]),
            action=data.get("action", ""),
            text=data.get("text", ""),
            decision=DecisionType(data["decision"]) if data.get("decision") else None,
            value=data.get("value"),
            feasible=bool(data.get("feasible", True)),
        )


@dataclass
class TimingExplanation:
    """Answers to "Why now?", "Why not earlier?" and "Why not later?"."""

    why_now: str
    why_not_earlier: str
    why_not_later: str
    earlier: list[TimingNote] = field(default_factory=list)
    later: list[TimingNote] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "why_now": self.why_now,
            "why_not_earlier": self.why_not_earlier,
            "why_not_later": self.why_not_later,
            "earlier": [n.to_dict() for n in self.earlier],
            "later": [n.to_dict() for n in self.later],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimingExplanation:
        return cls(
            why_now=data.get("why_now", ""),
            why_not_earlier=data.get("why_not_earlier", ""),
            why_not_later=data.get("why_not_later", ""),
            earlier=[TimingNote.from_dict(n) for n in data.get("earlier", [])],
            later=[TimingNote.from_dict(n) for n in data.get("later", [])],
        )


@dataclass
class Decision:
    """AgentPause's decision for one proposed action."""

    decision: DecisionType
    score: float
    """Intervention pressure in [0, 1]. For value-based policies, B / (B + C); > 0.5 means
    asking is worth more than it costs."""
    policy: str
    action: str
    step: int
    reason_codes: list[str] = field(default_factory=list)
    recommended_intervention: InterventionKind = InterventionKind.NONE
    questions: list[Question] = field(default_factory=list)
    deferred: list[DeferredQuestion] = field(default_factory=list)
    item_timings: list[ItemTiming] = field(default_factory=list)
    terms: dict[str, Any] = field(default_factory=dict)
    """Model terms (e.g. p_err, C_err, e, C_int, V) so the decision is fully inspectable."""
    signals: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    # Filled by the explainer:
    explanation: str = ""
    confidence: float | None = None
    """Decision stability: share of perturbed estimated/default signals that give the same
    decision. Low values mean the decision is borderline."""
    factors: list[Factor] = field(default_factory=list)
    counterfactuals: list[Counterfactual] = field(default_factory=list)
    timing: TimingExplanation | None = None
    latency_ms: float | None = None

    @property
    def should_ask(self) -> bool:
        """True if the human must be asked before this action runs (CLARIFY or ASK_HUMAN)."""
        return self.decision in (DecisionType.CLARIFY, DecisionType.ASK_HUMAN)

    @property
    def should_proceed(self) -> bool:
        """True if the agent may execute the action now (CONTINUE or DEFER)."""
        return self.decision.proceeds

    @property
    def is_blocked(self) -> bool:
        return self.decision == DecisionType.BLOCK

    @property
    def interrupts(self) -> bool:
        return self.decision.interrupts_now

    def top_factors(self, n: int = 3) -> list[Factor]:
        relevant = [f for f in self.factors if abs(f.contribution) > 1e-9]
        if self.decision.interrupts_now:
            relevant.sort(key=lambda f: -f.contribution)
        else:
            relevant.sort(key=lambda f: f.contribution)
        return relevant[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "score": round(self.score, 6),
            "confidence": None if self.confidence is None else round(self.confidence, 4),
            "policy": self.policy,
            "action": self.action,
            "step": self.step,
            "reason_codes": list(self.reason_codes),
            "explanation": self.explanation,
            "recommended_intervention": self.recommended_intervention.value,
            "should_ask": self.should_ask,
            "questions": [q.to_dict() for q in self.questions],
            "deferred": [d.to_dict() for d in self.deferred],
            "factors": [f.to_dict() for f in self.factors],
            "counterfactuals": [c.to_dict() for c in self.counterfactuals],
            "timing": self.timing.to_dict() if self.timing else None,
            "item_timings": [t.to_dict() for t in self.item_timings],
            "terms": _round_terms(self.terms),
            "signals": self.signals,
            "warnings": list(self.warnings),
            "latency_ms": None if self.latency_ms is None else round(self.latency_ms, 3),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Decision:
        return cls(
            decision=DecisionType(data["decision"]),
            score=float(data["score"]),
            policy=data.get("policy", ""),
            action=data.get("action", ""),
            step=int(data.get("step", 0)),
            reason_codes=list(data.get("reason_codes", [])),
            recommended_intervention=InterventionKind(data.get("recommended_intervention", "none")),
            questions=[Question.from_dict(q) for q in data.get("questions", [])],
            deferred=[DeferredQuestion.from_dict(d) for d in data.get("deferred", [])],
            item_timings=[ItemTiming.from_dict(t) for t in data.get("item_timings", [])],
            terms=dict(data.get("terms", {})),
            signals=dict(data.get("signals", {})),
            warnings=list(data.get("warnings", [])),
            explanation=data.get("explanation", ""),
            confidence=data.get("confidence"),
            factors=[Factor.from_dict(f) for f in data.get("factors", [])],
            counterfactuals=[Counterfactual.from_dict(c) for c in data.get("counterfactuals", [])],
            timing=TimingExplanation.from_dict(data["timing"]) if data.get("timing") else None,
            latency_ms=data.get("latency_ms"),
        )


def _round_terms(terms: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in terms.items():
        if isinstance(value, float):
            out[key] = round(value, 6)
        elif isinstance(value, dict):
            out[key] = _round_terms(value)
        else:
            out[key] = value
    return out
