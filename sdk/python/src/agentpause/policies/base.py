"""The policy interface and helpers shared by all policies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..context import ActionContext, Assumption, UserPreferences
from ..decision import Decision, Question
from ..explain.reasons import ReasonCode
from ..model import ModelParameters, consequence_risk, error_cost
from ..signals import ResolvedSignals, resolve_signals
from ..state import SessionState
from ..types import ConsequenceCategory, DecisionType, InterventionKind


class InterventionPolicy(ABC):
    """Decides whether and when to involve the human for one proposed action.

    Implementations must be **pure**: ``decide`` may read ``state`` but must not modify it,
    and must not use randomness or wall-clock time. The explainer relies on this, because it
    calls ``decide`` many times on hypothetical inputs to compute counterfactuals.

    To add a policy::

        class MyPolicy(InterventionPolicy):
            name = "my_policy"
            def decide(self, context, state):
                signals = self.resolve(context, state)
                ...
                return self.make_decision(context, state, signals, DecisionType.CONTINUE, score=0.1)

        register_policy("my_policy", MyPolicy)
    """

    name: str = "base"
    #: Short human-readable description shown in the UI and docs.
    summary: str = ""
    #: Name the policy was created under in the registry (set by ``create_policy``).
    registry_key: str | None = None

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
    ) -> None:
        self.parameters = parameters or ModelParameters()
        self.preferences = preferences

    @abstractmethod
    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        """Return the core decision (type, score, reason codes, model terms)."""

    def config(self) -> dict[str, Any]:
        """Policy-specific hyperparameters (override in subclasses)."""
        return {}

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            # The registry name: ``name`` may be a display label set by an experiment or a user.
            "policy": self.registry_key or type(self).name,
            "summary": self.summary,
            "config": self.config(),
            "parameters": self.parameters.to_dict(),
            "preferences": self.preferences.to_dict() if self.preferences else None,
        }

    # ---- helpers --------------------------------------------------------------------------
    def resolve(self, context: ActionContext, state: SessionState) -> ResolvedSignals:
        return resolve_signals(context, state, self.parameters)

    @staticmethod
    def step_of(context: ActionContext, state: SessionState) -> int:
        return context.step if context.step is not None else state.step

    def make_decision(
        self,
        context: ActionContext,
        state: SessionState,
        signals: ResolvedSignals,
        decision: DecisionType,
        *,
        score: float,
        reasons: list[ReasonCode] | None = None,
        kind: InterventionKind | None = None,
        questions: list[Question] | None = None,
        terms: dict[str, Any] | None = None,
    ) -> Decision:
        codes = [r.value for r in (reasons or [])]
        if signals.missing:
            codes.append(ReasonCode.MISSING_SIGNAL_DEFAULTED.value)
        if any(w.startswith("CONTRADICTORY_SIGNALS") for w in signals.warnings):
            codes.append(ReasonCode.CONTRADICTORY_SIGNALS.value)
        if kind is None:
            kind = default_kind(decision, questions or [])
        return Decision(
            decision=decision,
            score=float(score),
            policy=self.name,
            action=context.action,
            step=self.step_of(context, state),
            reason_codes=_unique(codes),
            recommended_intervention=kind,
            questions=list(questions or []),
            terms=dict(terms or {}),
            signals=signals.to_dict(),
            warnings=list(signals.warnings),
        )

    def hard_constraint(self, context: ActionContext, state: SessionState, signals: ResolvedSignals) -> Decision | None:
        """Constraints that apply to every policy: the step needs the human (e.g. credentials)."""
        if context.requires_human_input:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.BLOCK,
                score=1.0,
                reasons=[ReasonCode.REQUIRES_HUMAN_INPUT],
                kind=InterventionKind.TAKEOVER,
            )
        return None

    def is_catastrophic(self, signals: ResolvedSignals) -> bool:
        p = self.parameters
        return (
            signals.severity >= p.block_severity
            and signals.recoverability <= p.block_max_recoverability
            and signals.p_error >= p.block_min_error_probability
        )

    def catastrophic_block(self, context: ActionContext, state: SessionState, signals: ResolvedSignals) -> Decision:
        return self.make_decision(
            context,
            state,
            signals,
            DecisionType.BLOCK,
            score=1.0,
            reasons=[ReasonCode.CATASTROPHIC_RISK, ReasonCode.IRREVERSIBLE_ACTION, ReasonCode.HIGH_SEVERITY],
            kind=InterventionKind.TAKEOVER,
            terms={"p_error": signals.p_error, "severity": signals.severity, "recoverability": signals.recoverability},
        )

    def risk(self, signals: ResolvedSignals) -> float:
        """Consequence risk, independent of uncertainty."""
        return consequence_risk(signals.severity, signals.recoverability, self.parameters)

    def error_cost(self, signals: ResolvedSignals) -> float:
        return error_cost(signals.severity, signals.recoverability, self.parameters)


def default_kind(decision: DecisionType, questions: list[Question]) -> InterventionKind:
    if decision == DecisionType.BLOCK:
        return InterventionKind.TAKEOVER
    if decision == DecisionType.DEFER:
        return InterventionKind.SCHEDULED
    if decision == DecisionType.CONTINUE:
        return InterventionKind.NONE
    if len(questions) > 1:
        return InterventionKind.BATCHED_REVIEW
    if decision == DecisionType.CLARIFY:
        return InterventionKind.CLARIFICATION
    return InterventionKind.CONFIRMATION


def action_question(
    context: ActionContext, *, benefit: float = 0.0, cost: float = 0.0, piggybacked: bool = False
) -> Question:
    what = context.description or context.action.replace("_", " ")
    return Question(
        id=f"action:{context.action}",
        kind=InterventionKind.CONFIRMATION,
        prompt=f"The agent wants to: {what}. Should it proceed?",
        benefit=benefit,
        cost=cost,
        piggybacked=piggybacked,
    )


def assumption_question(
    assumption: Assumption, *, benefit: float = 0.0, cost: float = 0.0, piggybacked: bool = False
) -> Question:
    return Question(
        id=f"assumption:{assumption.id}",
        kind=InterventionKind.CLARIFICATION,
        prompt=f"The agent assumed: {assumption.description}. Is that right?",
        assumption_id=assumption.id,
        options=list(assumption.options),
        agent_value=assumption.agent_value,
        benefit=benefit,
        cost=cost,
        piggybacked=piggybacked,
    )


def consequence_reasons(context: ActionContext, signals: ResolvedSignals) -> list[ReasonCode]:
    """Reason codes describing *what is at stake* (independent of the decision)."""
    reasons: list[ReasonCode] = []
    if signals.severity >= 0.6:
        reasons.append(ReasonCode.HIGH_SEVERITY)
    if signals.recoverability < 0.5:
        reasons.append(ReasonCode.IRREVERSIBLE_ACTION)
    if signals.external_effects:
        reasons.append(ReasonCode.EXTERNAL_CONSEQUENCE)
    if context.category == ConsequenceCategory.FINANCIAL_TRANSACTION:
        reasons.append(ReasonCode.FINANCIAL_CONSEQUENCE)
    if context.category == ConsequenceCategory.DATA_SHARING:
        reasons.append(ReasonCode.PRIVACY_RISK)
    if context.category == ConsequenceCategory.DATA_DELETION:
        reasons.append(ReasonCode.DATA_LOSS_RISK)
    return reasons


def uncertainty_reasons(signals: ResolvedSignals, threshold: float = 0.8) -> list[ReasonCode]:
    reasons: list[ReasonCode] = []
    if signals.agent_confidence < threshold:
        reasons.append(ReasonCode.LOW_AGENT_CONFIDENCE)
    if signals.intent_confidence < threshold:
        reasons.append(ReasonCode.LOW_INTENT_CONFIDENCE)
    if signals.unresolved_dependencies:
        reasons.append(ReasonCode.AMBIGUOUS_ASSUMPTION)
    if (
        signals.history_weight >= 2.0
        and signals.history_disagreement_rate is not None
        and signals.history_disagreement_rate >= 0.3
    ):
        reasons.append(ReasonCode.USER_HISTORY_DISAGREES)
    return reasons


def autonomy_reasons(context: ActionContext, signals: ResolvedSignals, params: ModelParameters) -> list[ReasonCode]:
    reasons: list[ReasonCode] = []
    if context.category == ConsequenceCategory.READ_ONLY:
        reasons.append(ReasonCode.READ_ONLY_ACTION)
    elif error_cost(signals.severity, signals.recoverability, params) < 0.1:
        reasons.append(ReasonCode.LOW_RISK_ACTION)
    if signals.recoverability >= 0.5 and context.category != ConsequenceCategory.READ_ONLY:
        reasons.append(ReasonCode.REVERSIBLE_ACTION)
    if signals.p_error < 0.1:
        reasons.append(ReasonCode.HIGH_CONFIDENCE)
    if (
        signals.history_weight >= 2.0
        and signals.history_disagreement_rate is not None
        and signals.history_disagreement_rate < 0.1
    ):
        reasons.append(ReasonCode.USER_HISTORY_APPROVES)
    return reasons


def unresolved_dependency_questions(signals: ResolvedSignals) -> list[Question]:
    """Clarification items for assumptions the current action depends on, shown on the same card."""
    return [assumption_question(a, piggybacked=True) for a in signals.unresolved_dependencies]


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
