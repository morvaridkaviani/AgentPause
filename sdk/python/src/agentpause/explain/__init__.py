"""Explanations for AgentPause decisions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..context import ActionContext
from ..decision import Counterfactual, Decision
from ..state import SessionState
from .counterfactual import decision_stability, feature_counterfactuals
from .factors import compute_factors
from .narrative import build_explanation
from .reasons import PHRASES, ReasonCode, phrase
from .timing import explain_timing

if TYPE_CHECKING:
    from ..policies.base import InterventionPolicy

EXPLAIN_LEVELS = ("full", "light", "none")


class Explainer:
    """Adds explanations to a decision without changing it.

    Levels:

    * ``"full"``: narrative, factor attribution, feature and timing counterfactuals, and
      decision stability. Used for interactive use and studies.
    * ``"light"``: narrative and reason codes only. Used for large batch simulations.
    * ``"none"``: nothing beyond the policy's own reason codes.
    """

    def __init__(self, level: str = "full", *, max_counterfactuals: int = 3, stability_samples: int = 16) -> None:
        if level not in EXPLAIN_LEVELS:
            raise ValueError(f"explain level must be one of {EXPLAIN_LEVELS}")
        self.level = level
        self.max_counterfactuals = max_counterfactuals
        self.stability_samples = stability_samples

    def enrich(
        self, decision: Decision, context: ActionContext, state: SessionState, policy: InterventionPolicy
    ) -> Decision:
        if self.level == "none":
            return decision
        decision.explanation = build_explanation(decision, context, state)
        if self.level == "light":
            return decision
        decision.factors = compute_factors(decision, context, state, policy)
        decision.timing = explain_timing(decision, context, state, policy)
        decision.counterfactuals = [
            *feature_counterfactuals(decision, context, state, policy, limit=self.max_counterfactuals),
            Counterfactual(kind="timing", text=decision.timing.why_not_earlier, original_decision=decision.decision),
            Counterfactual(kind="timing", text=decision.timing.why_not_later, original_decision=decision.decision),
        ]
        decision.confidence = decision_stability(decision, context, state, policy, samples=self.stability_samples)
        return decision


__all__ = [
    "EXPLAIN_LEVELS",
    "PHRASES",
    "Explainer",
    "ReasonCode",
    "build_explanation",
    "compute_factors",
    "decision_stability",
    "explain_timing",
    "feature_counterfactuals",
    "phrase",
]
