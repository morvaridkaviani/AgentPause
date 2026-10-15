"""Factor attribution by occlusion.

Each signal's contribution is ``score(actual) − score(signal set to a low-risk reference)``.
The method treats the policy as a black box, so it works for every policy. It is a local,
one-at-a-time attribution. Interactions between signals are not decomposed, and the
contributions need not sum to the score. The UI says so.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..context import ActionContext
from ..decision import Decision, Factor
from ..state import SessionState
from ..types import Level, Provenance

if TYPE_CHECKING:
    from ..policies.base import InterventionPolicy


@dataclass(frozen=True)
class SignalSpec:
    signal: str
    label: str
    reference: object
    description: str
    level: Callable[[float], Level] | None = None


def _conf_level(v: float) -> Level:
    return Level.HIGH if v >= 0.85 else Level.MEDIUM if v >= 0.65 else Level.LOW


def _risk_level(v: float) -> Level:
    return Level.HIGH if v >= 0.6 else Level.MEDIUM if v >= 0.25 else Level.LOW


def _rec_level(v: float) -> Level:
    return Level.HIGH if v >= 0.8 else Level.MEDIUM if v >= 0.4 else Level.LOW


def _load_level(v: float) -> Level:
    return Level.HIGH if v >= 0.6 else Level.MEDIUM if v >= 0.3 else Level.LOW


SPECS: tuple[SignalSpec, ...] = (
    SignalSpec(
        "agent_confidence",
        "Agent confidence",
        0.95,
        "How sure the agent is that it executes the action correctly",
        _conf_level,
    ),
    SignalSpec(
        "intent_confidence",
        "Intent clarity",
        0.95,
        "How sure the agent is that this matches what you meant",
        _conf_level,
    ),
    SignalSpec("severity", "Consequence severity", 0.05, "How bad it would be if this action were wrong", _risk_level),
    SignalSpec("recoverability", "Reversibility", 1.0, "How easily a wrong action could be undone", _rec_level),
    SignalSpec(
        "external_effects",
        "External side effects",
        False,
        "Whether the action affects people or systems outside the task",
    ),
    SignalSpec(
        "at_breakpoint", "Natural breakpoint", True, "Whether you are between parts of the task (cheaper to interrupt)"
    ),
    SignalSpec(
        "cognitive_load",
        "Your current load",
        0.3,
        "Estimated busyness; interrupting a busy person costs more",
        _load_level,
    ),
    SignalSpec("task_progress", "Task progress", 0.5, "How far the task has progressed", None),
)
STATE_SPECS: tuple[tuple[str, str, str], ...] = (
    ("assumptions", "Open assumptions", "Interpretations of your request the agent had to guess"),
    (
        "habituation",
        "Recent interruptions",
        "How often you were interrupted recently (repeated prompts get rubber-stamped)",
    ),
    ("history", "Your past decisions", "How you responded to similar actions before"),
)


def display_value(signal: str, value: object) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if signal in ("agent_confidence", "intent_confidence", "task_progress"):
        return f"{float(value):.0%}"  # type: ignore[arg-type]
    if signal == "recoverability":
        v = float(value)  # type: ignore[arg-type]
        return "easily undone" if v >= 0.8 else "partly reversible" if v >= 0.4 else "hard to undo"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def compute_factors(
    decision: Decision, context: ActionContext, state: SessionState, policy: InterventionPolicy
) -> list[Factor]:
    signals = decision.signals
    provenance = signals.get("provenance", {})
    base_score = decision.score
    factors: list[Factor] = []

    for spec in SPECS:
        value = signals.get(spec.signal)
        if (
            spec.signal == "intent_confidence"
            and context.intent_confidence is None
            and signals.get("unresolved_dependencies")
        ):
            continue  # represented by the "assumptions" factor instead
        occluded = context.with_signal(spec.signal, spec.reference)
        if spec.signal == "recoverability":
            occluded = replace(occluded, reversible=None)
        alt = policy.decide(occluded, state)
        level = (
            spec.level(float(value))
            if spec.level and isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )
        factors.append(
            Factor(
                signal=spec.signal,
                label=spec.label,
                value=value,
                display=display_value(spec.signal, value),
                level=level,
                provenance=Provenance(provenance.get(spec.signal, Provenance.DEFAULT.value)),
                contribution=base_score - alt.score,
                description=spec.description,
            )
        )

    # State-level factors.
    unresolved = signals.get("unresolved_dependencies", [])
    if unresolved or state.unresolved_assumptions() or context.assumptions:
        confident_state = copy.deepcopy(state)
        for a_id, assumption in list(confident_state.assumptions.items()):
            confident_state.assumptions[a_id] = replace(assumption, confidence=0.95)
        confident_context = replace(
            context, assumptions=tuple(replace(a, confidence=0.95) for a in context.assumptions)
        )
        alt = policy.decide(confident_context, confident_state)
        n_open = len({*unresolved, *(a.id for a in context.assumptions if a.id not in state.resolved)})
        factors.append(
            Factor(
                signal="assumptions",
                label="Open assumptions",
                value=n_open,
                display=f"{n_open} unresolved",
                level=Level.HIGH if n_open >= 2 else Level.MEDIUM if n_open == 1 else Level.LOW,
                provenance=Provenance.AGENT_PROVIDED,
                contribution=base_score - alt.score,
                description=STATE_SPECS[0][2],
            )
        )
    if state.interruption_steps:
        fresh = copy.deepcopy(state)
        fresh.interruption_steps = []
        alt = policy.decide(context, fresh)
        recent = int(signals.get("recent_interruptions", 0))
        factors.append(
            Factor(
                signal="habituation",
                label="Recent interruptions",
                value=recent,
                display=f"{recent} in the last steps",
                level=Level.HIGH if recent >= 4 else Level.MEDIUM if recent >= 2 else Level.LOW,
                provenance=Provenance.INFERRED,
                contribution=base_score - alt.score,
                description=STATE_SPECS[1][2],
            )
        )
    if context.key in state.stats:
        fresh = copy.deepcopy(state)
        fresh.stats.pop(context.key, None)
        alt = policy.decide(context, fresh)
        rate = signals.get("history_disagreement_rate")
        factors.append(
            Factor(
                signal="history",
                label="Your past decisions",
                value=rate,
                display="you corrected similar actions" if (rate or 0) >= 0.3 else "you approved similar actions",
                level=None,
                provenance=Provenance.INFERRED,
                contribution=base_score - alt.score,
                description=STATE_SPECS[2][2],
            )
        )
    return factors
