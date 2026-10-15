"""The AgentPause intervention value model.

The model is an *expected-value-of-asking* formulation in the tradition of Horvitz (1999,
"Principles of Mixed-Initiative User Interfaces") and Horvitz et al. (2003, attention-
sensitive alerting), adapted to multi-step tool-using agents. It is not a new decision
theory. What it adds is the set of terms below, and how the adaptive policy combines them
over the trajectory (see ``policies/adaptive.py``).

For a question ``q`` that could be asked at step ``t``::

    V(q, t) = p_err(q) · C_err(q) · e(t)  −  C_int(t)  −  RW(q, now→t)
              └──────── benefit ───────┘     └ cost ┘    └ cost of waiting ┘

* ``p_err``: probability that proceeding without the human is wrong. It combines agent
  error and intent mismatch, assumed independent.
* ``C_err``: harm if the wrong action executes: severity, reduced by recoverability.
* ``e(t)``: probability the human actually catches the problem when asked. It falls with
  habituation, because repeated prompts produce rubber-stamping (Böhme & Köpsell 2010;
  Anderson et al. 2015; Turan 2026).
* ``C_int(t)``: cost of interrupting at ``t``. It grows with cognitive load and outside
  natural breakpoints (Adamczyk & Bailey 2004; Iqbal & Bailey 2005–2010), with
  habituation-driven annoyance, and with the user's preference profile.
* ``RW``: expected rework when the agent continues on a possibly wrong assumption until ``t``.

All quantities share one scale: 1.0 = the worst outcome the deployment cares about.
``interruption_cost`` is the exchange rate between interruptions and harm. With the default
0.02, a user would accept roughly 50 interruptions to prevent one worst-case error.

The default 0.02 was chosen on *development* seeds as the knee of the simulated
harm-vs-interruption frontier (see experiments/README.md). Reported results use held-out
seeds and show the full frontier over this parameter, not just the default.

RESEARCH ASSUMPTION: every default below is a documented prior, not a calibrated estimate.
Calibrating them requires human data (see research/research_questions.md, RQ2).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, fields, replace
from typing import Any

from .types import AssumptionKind, InterventionKind


@dataclass(frozen=True)
class ModelParameters:
    # --- interruption cost ---
    interruption_cost: float = 0.02
    """c₀: cost of one interruption at a breakpoint with zero load, in harm units."""
    load_weight: float = 1.0
    """γ: C_int scales with (1 + γ · cognitive_load)."""
    non_breakpoint_multiplier: float = 1.5
    """Interrupting mid-subtask costs more than at a task boundary (Iqbal & Bailey)."""
    unknown_breakpoint_multiplier: float = 1.25
    """Used when breakpoint information is missing (midpoint of the two cases)."""
    clarification_cost_multiplier: float = 0.8
    """A clarification (pick an option) is assumed lighter than reviewing an action."""
    batch_marginal_cost: float = 0.35
    """Each additional question in an interruption that happens anyway costs this fraction."""
    habituation_annoyance: float = 0.5
    """κ: C_int scales with (1 + κ · habituation)."""

    # --- human effectiveness ---
    base_catch_probability: float = 0.9
    """e₀: probability an attentive user catches a problem shown to them."""
    habituation_rate: float = 0.12
    """λ: habituation h = 1 − exp(−λ · recent interruptions)."""
    habituation_window: int = 8
    """Number of recent steps counted for habituation."""
    habituation_effect: float = 0.5
    """Maximum relative reduction in catch probability under full habituation."""

    # --- harm and rework ---
    undo_cost_fraction: float = 0.15
    """ρ: undoing a recoverable mistake still costs this fraction of its severity."""
    rework_cost_per_step: float = 0.01
    """Fixed cost of redoing one reversible step built on a wrong assumption."""
    commitment_recoverability: float = 0.5
    """Actions with recoverability below this are commitment points (deadlines for questions)."""

    # --- timing ---
    anticipated_agent_confidence: float = 0.9
    """Agent confidence assumed for *planned* steps when predicting whether they will need a
    confirmation anyway (used to batch deferred questions with it)."""
    deferrable_kinds: frozenset[AssumptionKind] = field(
        default_factory=lambda: frozenset({AssumptionKind.INPUT, AssumptionKind.CONTEXT})
    )
    """Only these assumption kinds may be deferred. Goal and constraint questions lose value
    early (Gulati et al. 2026), so they are asked immediately or not at all."""

    # --- learning from history ---
    history_prior_strength: float = 4.0
    """n₀: pseudo-observations given to the agent's own intent estimate when shrinking
    toward the user's observed disagreement rate for this action type."""

    # --- hard constraints ---
    block_severity: float = 0.9
    block_max_recoverability: float = 0.15
    block_min_error_probability: float = 0.6
    """BLOCK when severity ≥ block_severity AND recoverability ≤ block_max_recoverability AND
    p_err ≥ block_min_error_probability: the agent should not even propose this."""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["deferrable_kinds"] = sorted(k.value for k in self.deferrable_kinds)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ModelParameters:
        if not data:
            return cls()
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"Unknown model parameter(s): {sorted(unknown)}")
        values = dict(data)
        if "deferrable_kinds" in values:
            values["deferrable_kinds"] = frozenset(AssumptionKind(k) for k in values["deferrable_kinds"])
        return replace(cls(), **values)


def clamp01(value: float) -> float:
    if math.isnan(value):
        return 0.0
    return max(0.0, min(1.0, value))


def error_probability(agent_confidence: float, intent_confidence: float) -> float:
    """P(proceeding is wrong) = 1 − P(agent executes correctly) · P(it matches user intent).

    ASSUMPTION: agent errors and intent mismatches are independent.
    """
    return clamp01(1.0 - clamp01(agent_confidence) * clamp01(intent_confidence))


def error_cost(severity: float, recoverability: float, params: ModelParameters) -> float:
    """Harm if a wrong action executes: severity · [(1 − r) + r · ρ].

    A fully recoverable mistake still costs ρ · severity (time and effort to undo it).
    """
    r = clamp01(recoverability)
    return clamp01(severity) * ((1.0 - r) + r * params.undo_cost_fraction)


def consequence_risk(severity: float, recoverability: float, params: ModelParameters) -> float:
    """Uncertainty-free risk used by the fixed-threshold baseline (= error cost)."""
    return error_cost(severity, recoverability, params)


def habituation(recent_interruptions: int, params: ModelParameters) -> float:
    """h ∈ [0, 1): saturating effect of recent interruptions."""
    return 1.0 - math.exp(-params.habituation_rate * max(0, recent_interruptions))


def catch_probability(habituation_level: float, params: ModelParameters) -> float:
    """e = e₀ · (1 − effect · h). Rubber-stamping lowers the value of asking."""
    return clamp01(params.base_catch_probability * (1.0 - params.habituation_effect * clamp01(habituation_level)))


def breakpoint_multiplier(at_breakpoint: bool | None, params: ModelParameters) -> float:
    if at_breakpoint is None:
        return params.unknown_breakpoint_multiplier
    return 1.0 if at_breakpoint else params.non_breakpoint_multiplier


def interruption_cost(
    *,
    cognitive_load: float,
    at_breakpoint: bool | None,
    habituation_level: float,
    kind: InterventionKind,
    params: ModelParameters,
    preference_multiplier: float = 1.0,
) -> float:
    """C_int = c₀ · pref · (1 + γ·load) · breakpoint · (1 + κ·h) · kind multiplier."""
    kind_multiplier = params.clarification_cost_multiplier if kind == InterventionKind.CLARIFICATION else 1.0
    return (
        params.interruption_cost
        * preference_multiplier
        * (1.0 + params.load_weight * clamp01(cognitive_load))
        * breakpoint_multiplier(at_breakpoint, params)
        * (1.0 + params.habituation_annoyance * clamp01(habituation_level))
        * kind_multiplier
    )


def rework_cost(severity: float, params: ModelParameters) -> float:
    """Cost of redoing one reversible step that was built on a wrong assumption."""
    return params.rework_cost_per_step + params.undo_cost_fraction * clamp01(severity)


def is_commitment(recoverability: float, params: ModelParameters) -> bool:
    """True if the action is a commitment point: hard to undo once executed."""
    return recoverability < params.commitment_recoverability


def score_from_terms(benefit: float, cost: float) -> float:
    """Map a benefit/cost pair onto [0, 1]: score = B / (B + C).

    score > 0.5 exactly when the net value B − C is positive, so the score reads like a
    probability that asking is worthwhile, with a decision boundary at 0.5.
    """
    total = benefit + cost
    if total <= 0:
        return 0.0
    return clamp01(benefit / total)
