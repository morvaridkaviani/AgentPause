"""User-customized policy: a base policy plus the user's autonomy rules."""

from __future__ import annotations

from typing import Any

from ..context import ActionContext, UserPreferences
from ..decision import Decision
from ..explain.reasons import ReasonCode
from ..model import ModelParameters
from ..state import SessionState
from ..types import ConsequenceCategory, DecisionType, InterventionKind
from .base import InterventionPolicy, action_question, unresolved_dependency_questions


class UserCustomizedPolicy(InterventionPolicy):
    """Applies user rules on top of a base policy (default: ``adaptive``).

    Precedence, highest first:

    1. ``block_categories`` (BLOCK);
    2. the base policy's BLOCK;
    3. "always ask" rules (``always_ask_categories``, ``ask_before_irreversible``,
       ``ask_before_external``);
    4. "never ask" rules (``never_ask_categories``, ``allow_low_risk_autonomy``);
    5. the interruption budget (``max_interruptions_per_task``);
    6. the base decision.

    The profile (``fewer_interruptions`` / ``balanced`` / ``maximum_control``) is passed to the
    base policy and scales its interruption cost.
    """

    name = "user_customized"
    summary = "The adaptive policy plus your own rules (always ask / never ask / block) and interruption profile."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        base: str | InterventionPolicy = "adaptive",
        **base_config: Any,
    ) -> None:
        super().__init__(parameters, preferences or UserPreferences())
        if isinstance(base, InterventionPolicy):
            self.base = base
        else:
            from .registry import create_policy

            self.base = create_policy(base, parameters=self.parameters, preferences=self.preferences, **base_config)

    def config(self) -> dict[str, Any]:
        return {"base": self.base.name, "base_config": self.base.config()}

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        prefs = self.preferences or UserPreferences()
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return self._relabel(hard)

        if context.category in prefs.block_categories:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.BLOCK,
                score=1.0,
                reasons=[ReasonCode.USER_RULE_BLOCK],
                kind=InterventionKind.TAKEOVER,
            )

        base = self.base.decide(context, state)
        if base.decision == DecisionType.BLOCK:
            return self._relabel(base)

        forced: list[ReasonCode] = []
        if context.category in prefs.always_ask_categories:
            forced.append(ReasonCode.USER_RULE_ALWAYS_ASK)
        if (
            prefs.ask_before_irreversible
            and signals.recoverability < self.parameters.commitment_recoverability
            and context.category != ConsequenceCategory.READ_ONLY
        ):
            forced.append(ReasonCode.USER_RULE_IRREVERSIBLE)
        if prefs.ask_before_external and signals.external_effects:
            forced.append(ReasonCode.USER_RULE_EXTERNAL)
        if forced:
            if base.decision == DecisionType.ASK_HUMAN:
                base.reason_codes = [r.value for r in forced] + base.reason_codes
                return self._relabel(base)
            questions = [action_question(context)]
            existing = {q.id for q in questions}
            for q in base.questions + unresolved_dependency_questions(signals):
                if q.id not in existing:
                    questions.append(q)
                    existing.add(q.id)
            decision = self.make_decision(
                context,
                state,
                signals,
                DecisionType.ASK_HUMAN,
                score=max(base.score, 0.5),
                reasons=forced,
                questions=questions,
            )
            return self._merge(decision, base)

        if base.decision in (DecisionType.ASK_HUMAN, DecisionType.CLARIFY):
            allow: list[ReasonCode] = []
            if context.category in prefs.never_ask_categories:
                allow.append(ReasonCode.USER_RULE_NEVER_ASK)
            elif prefs.allow_low_risk_autonomy and self.risk(signals) < prefs.low_risk_threshold:
                allow.append(ReasonCode.USER_RULE_LOW_RISK_AUTONOMY)
            elif (
                prefs.max_interruptions_per_task is not None
                and state.task_interruptions >= prefs.max_interruptions_per_task
            ):
                allow.append(ReasonCode.INTERRUPTION_BUDGET_EXHAUSTED)
            if allow:
                decision = self.make_decision(
                    context, state, signals, DecisionType.CONTINUE, score=min(base.score, 0.49), reasons=allow
                )
                return self._merge(decision, base)

        return self._relabel(base)

    def _relabel(self, decision: Decision) -> Decision:
        decision.policy = self.name
        return decision

    @staticmethod
    def _merge(decision: Decision, base: Decision) -> Decision:
        """Keep the base policy's analysis (terms, timings) for inspection and explanation."""
        decision.terms = {**base.terms, "base_decision": base.decision.value, "base_policy": base.policy}
        decision.item_timings = base.item_timings
        decision.deferred = base.deferred if decision.decision.proceeds else []
        return decision
