"""Feature counterfactuals ("what would have to differ?") and decision stability.

Both treat the policy as a black box and are deterministic.
"""

from __future__ import annotations

import random
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from ..context import ActionContext
from ..decision import Counterfactual, Decision
from ..state import SessionState
from ..types import DecisionType, Provenance
from .factors import display_value

if TYPE_CHECKING:
    from ..policies.base import InterventionPolicy

_GRID_UNIT = [round(i * 0.05, 2) for i in range(21)]
_SEARCH: dict[str, list[Any]] = {
    "agent_confidence": _GRID_UNIT,
    "intent_confidence": _GRID_UNIT,
    "severity": _GRID_UNIT,
    "recoverability": _GRID_UNIT,
    "cognitive_load": [round(i * 0.1, 1) for i in range(11)],
    "at_breakpoint": [True, False],
}
_LABELS = {
    "agent_confidence": "the agent's confidence",
    "intent_confidence": "the clarity of your intent",
    "severity": "the consequence severity",
    "recoverability": "the action's reversibility",
    "cognitive_load": "your current load",
    "at_breakpoint": "being at a natural breakpoint",
}

VERBS: dict[DecisionType, str] = {
    DecisionType.CONTINUE: "let the agent continue",
    DecisionType.CLARIFY: "asked you a clarifying question",
    DecisionType.ASK_HUMAN: "asked for your confirmation",
    DecisionType.DEFER: "let the agent continue and asked you later",
    DecisionType.BLOCK: "stopped the agent",
}


def _apply(context: ActionContext, state: SessionState, signal: str, value: Any) -> tuple[ActionContext, SessionState]:
    if (
        signal == "intent_confidence"
        and context.intent_confidence is None
        and (context.assumptions or state.unresolved_assumptions())
    ):
        # Ambiguity lives in explicit assumptions: move their confidence instead.
        new_state = SessionState.from_dict(state.to_dict())
        for a_id, a in list(new_state.assumptions.items()):
            new_state.assumptions[a_id] = replace(a, confidence=float(value))
        new_context = replace(
            context, assumptions=tuple(replace(a, confidence=float(value)) for a in context.assumptions)
        )
        return new_context, new_state
    new_context = context.with_signal(signal, value)
    if signal == "recoverability":
        new_context = replace(new_context, reversible=None)
    return new_context, state


def _fmt(signal: str, value: Any) -> str:
    if signal in ("agent_confidence", "intent_confidence"):
        return f"{float(value):.0%}"
    return f"{float(value):.2f}"


def _describe(signal: str, value: Any, current: Any) -> str:
    if signal == "at_breakpoint":
        return "you had been at a natural breakpoint" if value else "you had been in the middle of a sub-task"
    if signal == "recoverability":
        return f"the action were {display_value(signal, float(value))} (it is {display_value(signal, float(current))})"
    return f"{_LABELS[signal]} were {_fmt(signal, value)} instead of {_fmt(signal, current)}"


def feature_counterfactuals(
    decision: Decision,
    context: ActionContext,
    state: SessionState,
    policy: InterventionPolicy,
    *,
    limit: int = 3,
) -> list[Counterfactual]:
    signals = decision.signals
    found: list[tuple[float, Counterfactual]] = []
    for signal, grid in _SEARCH.items():
        current = signals.get(signal)
        if signal == "at_breakpoint":
            candidates = [v for v in grid if v != current]
            distance = dict.fromkeys(candidates, 0.5)
        else:
            if current is None:
                continue
            candidates = sorted(
                (v for v in grid if abs(v - float(current)) > 1e-9), key=lambda v: abs(v - float(current))
            )
            distance = {v: abs(v - float(current)) for v in candidates}
        for value in candidates:
            new_context, new_state = _apply(context, state, signal, value)
            alt = policy.decide(new_context, new_state)
            if alt.decision != decision.decision:
                text = f"If {_describe(signal, value, current)}, AgentPause would have {VERBS[alt.decision]}."
                found.append(
                    (
                        distance[value],
                        Counterfactual(
                            kind="feature",
                            text=text,
                            signal=signal,
                            original_value=current,
                            counterfactual_value=value,
                            original_decision=decision.decision,
                            counterfactual_decision=alt.decision,
                        ),
                    )
                )
                break
    found.sort(key=lambda item: item[0])
    return [cf for _, cf in found[:limit]]


_PERTURBABLE = {
    "agent_confidence": 0.05,
    "intent_confidence": 0.05,
    "severity": 0.1,
    "recoverability": 0.1,
    "cognitive_load": 0.15,
}


def decision_stability(
    decision: Decision,
    context: ActionContext,
    state: SessionState,
    policy: InterventionPolicy,
    *,
    samples: int = 16,
    seed: int = 0,
) -> float:
    """Share of perturbed inputs that keep the same decision.

    Only signals that are *not* user-provided are perturbed: estimates, defaults,
    agent-reported and simulated values. The fixed seed keeps the result reproducible.
    """
    signals = decision.signals
    provenance = signals.get("provenance", {})
    perturbable = [
        (name, scale)
        for name, scale in _PERTURBABLE.items()
        if provenance.get(name) != Provenance.USER_PROVIDED.value and signals.get(name) is not None
    ]
    if not perturbable:
        return 1.0
    rng = random.Random(seed)
    same = 0
    for _ in range(samples):
        new_context = context
        for name, scale in perturbable:
            value = min(1.0, max(0.0, float(signals[name]) + rng.uniform(-scale, scale)))
            if name == "intent_confidence" and context.intent_confidence is None:
                continue  # assumption-driven intent is perturbed via assumption confidences below
            new_context = new_context.with_signal(name, value)
            if name == "recoverability":
                new_context = replace(new_context, reversible=None)
        if new_context.assumptions:
            new_context = replace(
                new_context,
                assumptions=tuple(
                    replace(a, confidence=min(1.0, max(0.0, a.confidence + rng.uniform(-0.05, 0.05))))
                    for a in new_context.assumptions
                ),
            )
        alt = policy.decide(new_context, state)
        same += int(alt.decision == decision.decision)
    return same / samples
