"""Baseline policies.

These are simplified re-implementations of designs found in prior work and products. They
are not faithful reproductions of those systems. See research/prior_art.md.
"""

from __future__ import annotations

from typing import Any

from ..context import ActionContext, UserPreferences
from ..decision import Decision
from ..explain.reasons import ReasonCode
from ..model import ModelParameters, clamp01
from ..state import SessionState
from ..types import ConsequenceCategory, DecisionType, InterventionKind
from .base import (
    InterventionPolicy,
    action_question,
    assumption_question,
    autonomy_reasons,
    consequence_reasons,
    uncertainty_reasons,
    unresolved_dependency_questions,
)

_LOW_STAKES = (ConsequenceCategory.READ_ONLY, ConsequenceCategory.INTERNAL_DRAFT)


class FullAutonomyPolicy(InterventionPolicy):
    """Never ask, unless the step is technically impossible without the human.

    Analogue of AutoGen ``human_input_mode="NEVER"`` and OpenHands ``NeverConfirm``.
    """

    name = "full_autonomy"
    summary = "Never interrupts the user (except steps that need their input)."

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        return self.make_decision(
            context, state, signals, DecisionType.CONTINUE, score=0.0, reasons=[ReasonCode.POLICY_FULL_AUTONOMY]
        )


class AlwaysConfirmPolicy(InterventionPolicy):
    """Ask before every meaningful (non read-only) action.

    Analogue of AutoGen ``ALWAYS`` and OpenHands ``AlwaysConfirm``. Read-only actions are not
    "meaningful" by default, which matches products that auto-approve reads (e.g. Claude Code's
    default mode). Set ``include_read_only=True`` to confirm everything.
    """

    name = "always_confirm"
    summary = "Asks before every action that changes anything."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        include_read_only: bool = False,
    ) -> None:
        super().__init__(parameters, preferences)
        self.include_read_only = include_read_only

    def config(self) -> dict[str, Any]:
        return {"include_read_only": self.include_read_only}

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        if context.category == ConsequenceCategory.READ_ONLY and not self.include_read_only:
            return self.make_decision(
                context, state, signals, DecisionType.CONTINUE, score=0.0, reasons=[ReasonCode.READ_ONLY_ACTION]
            )
        questions = [action_question(context), *unresolved_dependency_questions(signals)]
        return self.make_decision(
            context,
            state,
            signals,
            DecisionType.ASK_HUMAN,
            score=1.0,
            reasons=[ReasonCode.POLICY_ALWAYS_CONFIRM, *consequence_reasons(context, signals)],
            questions=questions,
        )


class ThresholdPolicy(InterventionPolicy):
    """Ask when risk ≥ a fixed threshold τ.

    ``mode="consequence"`` (default) uses severity × irreversibility, ignoring uncertainty.
    That is how most risk-gated products work (OpenHands ``ConfirmRisky``, Mastra's
    "classifier ≥ 0.7"). ``mode="expected_harm"`` multiplies by p_err.
    """

    name = "fixed_threshold"
    summary = "Asks when the action's risk exceeds a fixed threshold."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        threshold: float = 0.35,
        mode: str = "consequence",
    ) -> None:
        super().__init__(parameters, preferences)
        if mode not in ("consequence", "expected_harm"):
            raise ValueError("mode must be 'consequence' or 'expected_harm'")
        self.threshold = float(threshold)
        self.mode = mode

    def config(self) -> dict[str, Any]:
        return {"threshold": self.threshold, "mode": self.mode}

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        risk = self.risk(signals)
        if self.mode == "expected_harm":
            risk *= signals.p_error
        terms = {"risk": risk, "threshold": self.threshold, "mode": self.mode}
        if risk >= self.threshold:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.ASK_HUMAN,
                score=clamp01(risk),
                reasons=[ReasonCode.RISK_ABOVE_THRESHOLD, *consequence_reasons(context, signals)],
                questions=[action_question(context), *unresolved_dependency_questions(signals)],
                terms=terms,
            )
        return self.make_decision(
            context,
            state,
            signals,
            DecisionType.CONTINUE,
            score=clamp01(risk),
            reasons=[ReasonCode.RISK_BELOW_THRESHOLD, *autonomy_reasons(context, signals, self.parameters)],
            terms=terms,
        )


class ConfidenceThresholdPolicy(InterventionPolicy):
    """Ask when the agent's or intent confidence falls below τ, regardless of stakes.

    A non-conformal simplification of KnowNo-style "ask when uncertain" (Ren et al. 2023) and
    Warp's "Agent decides" mode. It produces CLARIFY when the lowest confidence belongs to an
    explicit assumption.
    """

    name = "confidence_threshold"
    summary = "Asks whenever confidence is low, regardless of what is at stake."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        threshold: float = 0.8,
    ) -> None:
        super().__init__(parameters, preferences)
        self.threshold = float(threshold)

    def config(self) -> dict[str, Any]:
        return {"threshold": self.threshold}

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        lowest = min(signals.agent_confidence, signals.intent_confidence)
        terms = {
            "agent_confidence": signals.agent_confidence,
            "intent_confidence": signals.intent_confidence,
            "threshold": self.threshold,
        }
        score = clamp01(1.0 - lowest)
        if lowest >= self.threshold:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.CONTINUE,
                score=score,
                reasons=[ReasonCode.CONFIDENCE_ABOVE_THRESHOLD],
                terms=terms,
            )
        uncertain = [a for a in signals.unresolved_dependencies if a.confidence < self.threshold]
        reasons = [ReasonCode.CONFIDENCE_BELOW_THRESHOLD, *uncertainty_reasons(signals, self.threshold)]
        if uncertain and signals.intent_confidence <= signals.agent_confidence:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.CLARIFY,
                score=score,
                reasons=reasons,
                questions=[assumption_question(a) for a in uncertain],
                terms=terms,
            )
        return self.make_decision(
            context,
            state,
            signals,
            DecisionType.ASK_HUMAN,
            score=score,
            reasons=reasons,
            questions=[action_question(context), *unresolved_dependency_questions(signals)],
            terms=terms,
        )


class RuleBasedPolicy(InterventionPolicy):
    """Transparent rules over reversibility × confidence.

    Mirrors the structure of Magentic-UI action guards (irreversibility labels) and the
    ask-or-act/Kiri rule: reads → act; reversible → act if confident, else ask; irreversible or
    external → always ask; catastrophic → block.
    """

    name = "rule_based"
    summary = "Fixed rules: irreversible or external actions are always confirmed; reversible ones only when unsure."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        confidence_threshold: float = 0.8,
        block_catastrophic: bool = True,
    ) -> None:
        super().__init__(parameters, preferences)
        self.confidence_threshold = float(confidence_threshold)
        self.block_catastrophic = block_catastrophic

    def config(self) -> dict[str, Any]:
        return {"confidence_threshold": self.confidence_threshold, "block_catastrophic": self.block_catastrophic}

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        if self.block_catastrophic and self.is_catastrophic(signals):
            return self.catastrophic_block(context, state, signals)
        if context.category in _LOW_STAKES:
            return self.make_decision(
                context, state, signals, DecisionType.CONTINUE, score=0.0, reasons=[ReasonCode.READ_ONLY_ACTION]
            )
        irreversible = signals.recoverability < self.parameters.commitment_recoverability
        if irreversible or signals.external_effects:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.ASK_HUMAN,
                score=1.0,
                reasons=[ReasonCode.RULE_IRREVERSIBLE_OR_EXTERNAL, *consequence_reasons(context, signals)],
                questions=[action_question(context), *unresolved_dependency_questions(signals)],
            )
        tau = self.confidence_threshold
        if signals.agent_confidence >= tau and signals.intent_confidence >= tau:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.CONTINUE,
                score=0.0,
                reasons=[ReasonCode.REVERSIBLE_ACTION, ReasonCode.HIGH_CONFIDENCE],
            )
        uncertain = [a for a in signals.unresolved_dependencies if a.confidence < tau]
        reasons = [ReasonCode.RULE_UNCERTAIN_REVERSIBLE, *uncertainty_reasons(signals, tau)]
        if uncertain and signals.agent_confidence >= tau:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.CLARIFY,
                score=1.0,
                reasons=reasons,
                questions=[assumption_question(a) for a in uncertain],
                kind=InterventionKind.CLARIFICATION if len(uncertain) == 1 else InterventionKind.BATCHED_REVIEW,
            )
        return self.make_decision(
            context,
            state,
            signals,
            DecisionType.ASK_HUMAN,
            score=1.0,
            reasons=reasons,
            questions=[action_question(context), *unresolved_dependency_questions(signals)],
        )
