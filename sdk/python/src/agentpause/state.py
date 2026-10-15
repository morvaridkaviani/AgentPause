"""Session state: everything AgentPause remembers between decisions in one task."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .context import ActionContext, Assumption, PlannedAction
from .decision import DeferredQuestion
from .types import DecisionType, ResponseType

if TYPE_CHECKING:
    from .decision import Decision


@dataclass
class ActionStats:
    """Weighted record of the user's past responses to one kind of action.

    Approvals given while the user was habituated count for less, because they may be rubber
    stamps. AgentPause therefore never treats "approved" as ground truth for "correct" (see
    Mozannar et al. 2024, which warns against optimizing for acceptance).
    """

    approvals: float = 0.0
    disagreements: float = 0.0
    count: int = 0

    @property
    def total_weight(self) -> float:
        return self.approvals + self.disagreements

    @property
    def disagreement_rate(self) -> float:
        total = self.total_weight
        return self.disagreements / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"approvals": self.approvals, "disagreements": self.disagreements, "count": self.count}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionStats:
        return cls(
            approvals=float(data.get("approvals", 0.0)),
            disagreements=float(data.get("disagreements", 0.0)),
            count=int(data.get("count", 0)),
        )


@dataclass
class HistoryEntry:
    """One evaluated proposal and, if the human was involved, their response."""

    step: int
    action: str
    action_key: str
    decision: DecisionType
    score: float
    interrupted: bool
    reason_codes: list[str]
    context: dict[str, Any]
    signals: dict[str, Any]
    item_values: dict[str, float] = field(default_factory=dict)
    """Net value of asking each question at this step (for "why not earlier?")."""
    deferred_targets: dict[str, int] = field(default_factory=dict)
    """Assumption id → step it was scheduled for, if deferred at this step."""
    asked: list[str] = field(default_factory=list)
    """Question ids asked at this step."""
    habituation: float = 0.0
    response: ResponseType | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "action_key": self.action_key,
            "decision": self.decision.value,
            "score": self.score,
            "interrupted": self.interrupted,
            "reason_codes": list(self.reason_codes),
            "context": self.context,
            "signals": self.signals,
            "item_values": dict(self.item_values),
            "deferred_targets": dict(self.deferred_targets),
            "asked": list(self.asked),
            "habituation": self.habituation,
            "response": self.response.value if self.response else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        return cls(
            step=int(data["step"]),
            action=data["action"],
            action_key=data.get("action_key", data["action"]),
            decision=DecisionType(data["decision"]),
            score=float(data.get("score", 0.0)),
            interrupted=bool(data.get("interrupted", False)),
            reason_codes=list(data.get("reason_codes", [])),
            context=dict(data.get("context", {})),
            signals=dict(data.get("signals", {})),
            item_values={k: float(v) for k, v in (data.get("item_values") or {}).items()},
            deferred_targets={k: int(v) for k, v in (data.get("deferred_targets") or {}).items()},
            asked=list(data.get("asked") or []),
            habituation=float(data.get("habituation", 0.0)),
            response=ResponseType(data["response"]) if data.get("response") else None,
        )


@dataclass
class SessionState:
    """Mutable state of one AgentPause session (typically one task).

    Policies only *read* the state. :class:`~agentpause.session.AgentPause` updates it after
    each decision and response, so decisions stay reproducible.
    """

    step: int = 0
    history: list[HistoryEntry] = field(default_factory=list)
    stats: dict[str, ActionStats] = field(default_factory=dict)
    interruption_steps: list[int] = field(default_factory=list)
    assumptions: dict[str, Assumption] = field(default_factory=dict)
    assumption_introduced: dict[str, int] = field(default_factory=dict)
    resolved: dict[str, str] = field(default_factory=dict)
    """Resolved assumptions: id → "confirmed" or "corrected"."""
    pending: list[DeferredQuestion] = field(default_factory=list)
    plan: list[PlannedAction] = field(default_factory=list)

    # ---- queries -------------------------------------------------------------------------
    def recent_interruptions(self, window: int) -> int:
        """Interruptions within the last ``window`` steps before the current step."""
        lower = self.step - window
        return sum(1 for s in self.interruption_steps if lower <= s < self.step)

    @property
    def task_interruptions(self) -> int:
        return len(self.interruption_steps)

    def unresolved_assumptions(self) -> list[Assumption]:
        return [a for a_id, a in self.assumptions.items() if a_id not in self.resolved]

    def planned_after(self, step: int) -> list[PlannedAction]:
        return sorted((p for p in self.plan if p.step > step), key=lambda p: p.step)

    # ---- updates (called by AgentPause, never by policies) ---------------------------------
    def register_context(self, context: ActionContext) -> None:
        step = context.step if context.step is not None else self.step
        for assumption in context.assumptions:
            if assumption.id not in self.assumptions:
                self.assumption_introduced[assumption.id] = step
            self.assumptions[assumption.id] = assumption
        if context.plan:
            self.plan = list(context.plan)

    def record_decision(self, context: ActionContext, decision: Decision) -> None:
        self.register_context(context)
        step = decision.step
        interrupted = decision.decision.interrupts_now
        item_values: dict[str, float] = {}
        for timing in decision.item_timings:
            now = next((c for c in timing.candidates if c.step == step), None)
            if now is not None:
                item_values[timing.item_id] = now.value
        self.history.append(
            HistoryEntry(
                step=step,
                action=context.action,
                action_key=context.key,
                decision=decision.decision,
                score=decision.score,
                interrupted=interrupted,
                reason_codes=list(decision.reason_codes),
                context=context.to_dict(),
                signals=dict(decision.signals),
                item_values=item_values,
                deferred_targets={d.assumption_id: d.target_step for d in decision.deferred},
                asked=[q.id for q in decision.questions],
                habituation=float(decision.signals.get("habituation", 0.0)),
            )
        )
        if interrupted:
            self.interruption_steps.append(step)
        asked = {q.assumption_id for q in decision.questions if q.assumption_id}
        self.pending = [
            d for d in decision.deferred if d.assumption_id not in self.resolved and d.assumption_id not in asked
        ]
        self.step = max(self.step, step + 1)

    def record_response(
        self,
        decision: Decision,
        response: ResponseType,
        *,
        answers: dict[str, str] | None = None,
        habituation_discount: float = 0.5,
    ) -> None:
        """Update history statistics and resolve assumptions after a human response."""
        if response == ResponseType.ASK_WHY:
            return
        entry = next(
            (h for h in reversed(self.history) if h.step == decision.step and h.action == decision.action),
            None,
        )
        if entry is not None:
            entry.response = response
            key = entry.action_key
            weight = 1.0 - habituation_discount * entry.habituation
            stats = self.stats.setdefault(key, ActionStats())
            stats.count += 1
            if response.disagrees_with_agent:
                stats.disagreements += 1.0
            elif response in (ResponseType.APPROVE, ResponseType.ANSWER, ResponseType.OVERRIDE):
                stats.approvals += max(0.0, weight)

        answers = answers or {}
        for question in decision.questions:
            if not question.assumption_id:
                continue
            a_id = question.assumption_id
            if a_id in answers:
                assumption = self.assumptions.get(a_id)
                agent_value = assumption.agent_value if assumption else question.agent_value
                self.resolved[a_id] = "confirmed" if answers[a_id] == agent_value else "corrected"
            elif response in (ResponseType.APPROVE, ResponseType.ANSWER):
                self.resolved[a_id] = "confirmed"
            elif response in (ResponseType.EDIT, ResponseType.REJECT):
                self.resolved[a_id] = "corrected"
        self.pending = [d for d in self.pending if d.assumption_id not in self.resolved]

    def resolve(self, assumption_id: str, outcome: str = "confirmed") -> None:
        self.resolved[assumption_id] = outcome
        self.pending = [d for d in self.pending if d.assumption_id != assumption_id]

    # ---- serialization --------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "history": [h.to_dict() for h in self.history],
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
            "interruption_steps": list(self.interruption_steps),
            "assumptions": {k: v.to_dict() for k, v in self.assumptions.items()},
            "assumption_introduced": dict(self.assumption_introduced),
            "resolved": dict(self.resolved),
            "pending": [d.to_dict() for d in self.pending],
            "plan": [p.to_dict() for p in self.plan],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SessionState:
        if not data:
            return cls()
        return cls(
            step=int(data.get("step", 0)),
            history=[HistoryEntry.from_dict(h) for h in data.get("history", [])],
            stats={k: ActionStats.from_dict(v) for k, v in (data.get("stats") or {}).items()},
            interruption_steps=[int(s) for s in data.get("interruption_steps", [])],
            assumptions={k: Assumption.from_dict(v) for k, v in (data.get("assumptions") or {}).items()},
            assumption_introduced={k: int(v) for k, v in (data.get("assumption_introduced") or {}).items()},
            resolved=dict(data.get("resolved") or {}),
            pending=[DeferredQuestion.from_dict(d) for d in data.get("pending", [])],
            plan=[PlannedAction.from_dict(p) for p in data.get("plan", [])],
        )
