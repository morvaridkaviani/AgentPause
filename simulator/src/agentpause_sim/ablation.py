"""Signal ablation (RQ2): hide signals from a policy as if they were not measured.

``SignalAblation(base, drop=["recoverability"])`` deletes the dropped signals from every
context before the base policy sees them. AgentPause then falls back to its documented
defaults, exactly as it would for a real agent that cannot measure that signal. Comparing
the ablated policy with the full policy shows how much each signal contributes, **under the
simulator's assumptions**.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

from agentpause import ActionContext, Decision, InterventionPolicy, SessionState

ABLATABLE = (
    "agent_confidence",
    "intent",
    "severity",
    "recoverability",
    "at_breakpoint",
    "cognitive_load",
    "habituation",
    "history",
    "plan",
)


class SignalAblation(InterventionPolicy):
    def __init__(self, base: InterventionPolicy, drop: list[str]) -> None:
        unknown = set(drop) - set(ABLATABLE)
        if unknown:
            raise ValueError(f"Cannot ablate {sorted(unknown)}; choose from {ABLATABLE}")
        super().__init__(base.parameters, base.preferences)
        self.base = base
        self.drop = sorted(drop)
        self.name = f"{base.name}-no_{'+'.join(self.drop)}"
        self.summary = f"{base.name} without: {', '.join(self.drop)}"

    def config(self) -> dict[str, Any]:
        return {"base": self.base.name, "base_config": self.base.config(), "drop": self.drop}

    def _mask(self, context: ActionContext, state: SessionState) -> tuple[ActionContext, SessionState]:
        changes: dict[str, Any] = {}
        for signal in ("agent_confidence", "severity", "cognitive_load", "at_breakpoint"):
            if signal in self.drop:
                changes[signal] = None
        if "recoverability" in self.drop:
            changes["recoverability"] = None
            changes["reversible"] = None
        if "intent" in self.drop:
            changes.update(intent_confidence=None, assumptions=(), depends_on=())
        if "plan" in self.drop:
            changes["plan"] = ()
        masked = replace(context, **changes) if changes else context
        if {"habituation", "history", "intent", "plan"} & set(self.drop):
            state = copy.copy(state)
            if "habituation" in self.drop:
                state.interruption_steps = []
            if "history" in self.drop:
                state.stats = {}
            if "intent" in self.drop:
                state.assumptions = {}
            if "plan" in self.drop:
                state.plan = []
        return masked, state

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        masked, masked_state = self._mask(context, state)
        decision = self.base.decide(masked, masked_state)
        decision.policy = self.name
        return decision
