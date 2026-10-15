"""Resolve raw (possibly incomplete or contradictory) inputs into a complete signal set.

Rules, documented here because they affect research validity:

* **Missing signals** fall back to a documented default (category prior or constant), tagged
  ``Provenance.DEFAULT``, and are listed in ``ResolvedSignals.missing``.
* **Out-of-range values** are clamped to [0, 1] and reported in ``warnings``.
* **Contradictions** keep the more specific value and report a warning. Example:
  ``reversible=True`` with ``recoverability=0.1``; the explicit number wins.
* **Intent confidence** combines the scalar ``intent_confidence`` with the product of the
  confidences of the *unresolved* assumptions the action depends on (taking the minimum),
  then shrinks toward the user's observed disagreement rate for this action type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .categories import prior_for
from .context import ActionContext, Assumption
from .model import ModelParameters, clamp01, error_probability, habituation
from .state import SessionState
from .types import Provenance

# Defaults used when a signal is missing. Each is a documented assumption.
DEFAULT_AGENT_CONFIDENCE = 0.8
DEFAULT_INTENT_CONFIDENCE = 0.85
DEFAULT_COGNITIVE_LOAD = 0.3
DEFAULT_TASK_PROGRESS = 0.5
REVERSIBLE_MIN_RECOVERABILITY = 0.9
IRREVERSIBLE_MAX_RECOVERABILITY = 0.1


@dataclass
class ResolvedSignals:
    severity: float
    recoverability: float
    agent_confidence: float
    intent_confidence: float
    """Overall intent confidence: min(scalar, product of unresolved assumptions), history-adjusted."""
    intent_confidence_raw: float
    residual_intent_confidence: float
    """Intent confidence *not* explained by explicit assumptions (scalar only), history-adjusted.
    The adaptive policy uses it for the approval question so that ambiguity attached to an
    assumption is not double-counted."""
    task_progress: float
    at_breakpoint: bool | None
    cognitive_load: float
    external_effects: bool
    habituation: float
    recent_interruptions: int
    history_weight: float
    history_disagreement_rate: float | None
    unresolved_dependencies: tuple[Assumption, ...]
    provenance: dict[str, Provenance] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def p_agent_error(self) -> float:
        return clamp01(1.0 - self.agent_confidence)

    @property
    def p_intent_error(self) -> float:
        return clamp01(1.0 - self.intent_confidence)

    @property
    def p_error(self) -> float:
        return error_probability(self.agent_confidence, self.intent_confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "recoverability": self.recoverability,
            "agent_confidence": self.agent_confidence,
            "intent_confidence": self.intent_confidence,
            "intent_confidence_raw": self.intent_confidence_raw,
            "residual_intent_confidence": self.residual_intent_confidence,
            "task_progress": self.task_progress,
            "at_breakpoint": self.at_breakpoint,
            "cognitive_load": self.cognitive_load,
            "external_effects": self.external_effects,
            "habituation": self.habituation,
            "recent_interruptions": self.recent_interruptions,
            "history_weight": self.history_weight,
            "history_disagreement_rate": self.history_disagreement_rate,
            "unresolved_dependencies": [a.id for a in self.unresolved_dependencies],
            "provenance": {k: v.value for k, v in self.provenance.items()},
            "missing": list(self.missing),
            "warnings": list(self.warnings),
        }


def _checked(name: str, value: float | None, warnings: list[str]) -> float | None:
    if value is None:
        return None
    if value < 0.0 or value > 1.0:
        warnings.append(f"{name}={value:.3g} is outside [0, 1]; clamped")
        return clamp01(value)
    return value


def resolve_signals(context: ActionContext, state: SessionState | None, params: ModelParameters) -> ResolvedSignals:
    state = state or SessionState()
    warnings: list[str] = []
    missing: list[str] = []
    provenance: dict[str, Provenance] = {}
    prior = prior_for(context.category)

    # --- severity ---
    severity = _checked("severity", context.severity, warnings)
    if severity is None:
        severity = prior.severity
        provenance["severity"] = Provenance.DEFAULT
        missing.append("severity")
    else:
        provenance["severity"] = context.provenance_of("severity")

    # --- recoverability / reversible ---
    recoverability = _checked("recoverability", context.recoverability, warnings)
    if recoverability is not None:
        provenance["recoverability"] = context.provenance_of("recoverability")
        if context.reversible is True and recoverability < 0.5:
            warnings.append(
                f"CONTRADICTORY_SIGNALS: reversible=True but recoverability={recoverability:.2f}; using recoverability"
            )
        if context.reversible is False and recoverability > 0.5:
            warnings.append(
                f"CONTRADICTORY_SIGNALS: reversible=False but recoverability={recoverability:.2f}; using recoverability"
            )
    elif context.reversible is not None:
        if context.reversible:
            recoverability = max(prior.recoverability, REVERSIBLE_MIN_RECOVERABILITY)
        else:
            recoverability = min(prior.recoverability, IRREVERSIBLE_MAX_RECOVERABILITY)
        provenance["recoverability"] = context.provenance.get(
            "recoverability", context.provenance.get("reversible", Provenance.AGENT_PROVIDED)
        )
    else:
        recoverability = prior.recoverability
        provenance["recoverability"] = Provenance.DEFAULT
        missing.append("recoverability")

    # --- agent confidence ---
    agent_confidence = _checked("agent_confidence", context.agent_confidence, warnings)
    if agent_confidence is None:
        agent_confidence = DEFAULT_AGENT_CONFIDENCE
        provenance["agent_confidence"] = Provenance.DEFAULT
        missing.append("agent_confidence")
    else:
        provenance["agent_confidence"] = context.provenance_of("agent_confidence")

    # --- intent confidence (scalar + unresolved assumptions) ---
    known = dict(state.assumptions)
    for assumption in context.assumptions:
        known[assumption.id] = assumption
    unresolved = tuple(known[a_id] for a_id in context.dependency_ids if a_id in known and a_id not in state.resolved)
    unknown_deps = [a_id for a_id in context.dependency_ids if a_id not in known]
    if unknown_deps:
        warnings.append(f"depends_on references undeclared assumption(s): {unknown_deps}")

    scalar_intent = _checked("intent_confidence", context.intent_confidence, warnings)
    assumption_intent = 1.0
    for assumption in unresolved:
        assumption_intent *= clamp01(assumption.confidence)
    if scalar_intent is None and not unresolved and context.dependency_ids and not unknown_deps:
        # Every declared intent assumption has been resolved by the user.
        residual_raw = 1.0
        provenance["intent_confidence"] = Provenance.INFERRED
    elif scalar_intent is None and not unresolved:
        residual_raw = DEFAULT_INTENT_CONFIDENCE
        provenance["intent_confidence"] = Provenance.DEFAULT
        missing.append("intent_confidence")
    elif scalar_intent is None:
        # All known ambiguity is captured by explicit assumptions.
        residual_raw = 1.0
        provenance["intent_confidence"] = Provenance.INFERRED
    else:
        residual_raw = scalar_intent
        provenance["intent_confidence"] = (
            context.provenance_of("intent_confidence") if not unresolved else Provenance.INFERRED
        )
    intent_raw = min(residual_raw, assumption_intent)

    # Shrink toward the user's observed disagreement rate for similar actions.
    # Approvals given while habituated count for less (they may be rubber stamps; see
    # Mozannar et al. 2024 on not optimizing for acceptance).
    stats = state.stats.get(context.key)
    history_weight = 0.0
    disagreement_rate: float | None = None
    intent_confidence = intent_raw
    residual_intent = residual_raw
    if stats is not None and stats.total_weight > 0:
        history_weight = stats.total_weight
        disagreement_rate = stats.disagreement_rate
        n0 = params.history_prior_strength

        def shrink(confidence: float) -> float:
            p_err = (n0 * (1.0 - confidence) + history_weight * disagreement_rate) / (n0 + history_weight)
            return clamp01(1.0 - p_err)

        intent_confidence = shrink(intent_raw)
        residual_intent = shrink(residual_raw)
        provenance["intent_confidence"] = Provenance.INFERRED

    # --- task progress ---
    task_progress = _checked("task_progress", context.task_progress, warnings)
    if task_progress is None:
        inferred = _infer_progress(context, state)
        if inferred is None:
            task_progress = DEFAULT_TASK_PROGRESS
            provenance["task_progress"] = Provenance.DEFAULT
            missing.append("task_progress")
        else:
            task_progress = inferred
            provenance["task_progress"] = Provenance.INFERRED
    else:
        provenance["task_progress"] = context.provenance_of("task_progress")

    # --- breakpoint ---
    at_breakpoint = context.at_breakpoint
    if at_breakpoint is None:
        if context.task_progress is not None and context.task_progress <= 0.0:
            at_breakpoint = True  # the start of a task is a natural breakpoint
            provenance["at_breakpoint"] = Provenance.INFERRED
        else:
            provenance["at_breakpoint"] = Provenance.DEFAULT
            missing.append("at_breakpoint")
    else:
        provenance["at_breakpoint"] = context.provenance_of("at_breakpoint")

    # --- cognitive load ---
    cognitive_load = _checked("cognitive_load", context.cognitive_load, warnings)
    if cognitive_load is None:
        cognitive_load = DEFAULT_COGNITIVE_LOAD
        provenance["cognitive_load"] = Provenance.DEFAULT
        missing.append("cognitive_load")
    else:
        provenance["cognitive_load"] = context.provenance_of("cognitive_load")

    # --- external effects ---
    if context.external_effects is None:
        external = prior.external
        provenance["external_effects"] = Provenance.DEFAULT
    else:
        external = bool(context.external_effects)
        provenance["external_effects"] = context.provenance_of("external_effects")

    # --- habituation (always inferred from session history) ---
    recent = state.recent_interruptions(params.habituation_window)
    h = habituation(recent, params)
    provenance["habituation"] = Provenance.INFERRED

    return ResolvedSignals(
        severity=float(severity),
        recoverability=float(recoverability),
        agent_confidence=float(agent_confidence),
        intent_confidence=float(intent_confidence),
        intent_confidence_raw=float(intent_raw),
        residual_intent_confidence=float(residual_intent),
        task_progress=float(task_progress),
        at_breakpoint=at_breakpoint,
        cognitive_load=float(cognitive_load),
        external_effects=external,
        habituation=h,
        recent_interruptions=recent,
        history_weight=history_weight,
        history_disagreement_rate=disagreement_rate,
        unresolved_dependencies=unresolved,
        provenance=provenance,
        missing=missing,
        warnings=warnings,
    )


def _infer_progress(context: ActionContext, state: SessionState) -> float | None:
    step = context.step if context.step is not None else state.step
    plan = context.plan or tuple(state.plan)
    if not plan:
        return None
    last = max(p.step for p in plan)
    total = max(last, step) + 1
    return clamp01(step / max(1, total - 1)) if total > 1 else 0.0
