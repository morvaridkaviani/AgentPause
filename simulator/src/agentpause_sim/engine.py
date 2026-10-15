"""The episode engine: runs one scenario under one policy, step by step.

The engine is a serializable state machine, so the same code drives:

* batch experiments, where a :class:`~agentpause_sim.user.SimulatedUser` answers every card;
* the interactive web demo and study mode, where a person answers through the API and the
  state is stored as JSON between requests.

Ground truth: see ``scenario.py`` for error events. Each intervention is labelled
**necessary** if, at that moment, it showed the human at least one pending error event
(a visible mistake, or a wrong assumption it asked about), and **unnecessary** otherwise.
An error event that causes harm without ever having been shown is a **missed intervention**.
One that was shown but approved anyway is a **human miss** (an oversight failure).
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

from agentpause import (
    ActionContext,
    AgentPause,
    Assumption,
    Decision,
    DecisionType,
    InterventionKind,
    PlannedAction,
    Provenance,
    ResponseType,
)
from agentpause.model import ModelParameters, clamp01, error_cost

from .rng import derive_rng
from .scenario import Scenario, Step
from .user import CardTruth, HumanResponse, SimulatedUser


class EngineError(RuntimeError):
    pass


# Harm accounting uses the engine's default undo-cost fraction, independent of the policy under
# test, so that every policy is scored with the same yardstick.
_PARAMS = ModelParameters()


@dataclass(frozen=True)
class EngineConfig:
    calibration: float = 0.7
    """How strongly an injected mistake lowers the agent's reported confidence (0 = not at all)."""
    confidence_drop: float = 0.3
    propagated_calibration: float = 0.35
    """How strongly a mistake made at an *earlier* step lowers the agent's confidence at a later step
    where it is visible (e.g. reviewing the order summary). 0 = the agent never notices upstream mistakes."""
    confidence_noise: float = 0.03
    max_attempts: int = 2
    """After this many rejections of the same step, the user takes over the step."""
    commitment_recoverability: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> EngineConfig:
        return cls(**(data or {}))


@dataclass
class ErrorEvent:
    id: str
    kind: str  # "mistake" | "assumption"
    ref: str  # mistake id or assumption id
    description: str
    source_step: int
    harm_step: int
    visible_steps: list[int]
    severity: float
    recoverability: float
    status: str = "pending"  # pending | caught | harm | averted
    caught_at: int | None = None
    shown_at: list[int] = field(default_factory=list)
    rework_steps: int = 0

    @property
    def harm(self) -> float:
        return error_cost(self.severity, self.recoverability, _PARAMS)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ErrorEvent:
        return cls(**data)


@dataclass
class EpisodeState:
    scenario_id: str
    policy: str
    seed: int
    episode: int
    condition: str = "default"
    index: int = 0
    attempt: int = 0
    status: str = "running"  # running | awaiting_human | completed | cancelled
    clock_s: float = 0.0
    human_time_s: float = 0.0
    truth: dict[str, str] = field(default_factory=dict)
    values: dict[str, str] = field(default_factory=dict)
    errors: dict[str, ErrorEvent] = field(default_factory=dict)
    executed: list[dict[str, Any]] = field(default_factory=list)
    pending: dict[str, Any] | None = None
    interruption_steps: list[int] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)
    sequence: int = 0

    def bump(self, key: str, by: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + by

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["errors"] = {k: v.to_dict() for k, v in self.errors.items()}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EpisodeState:
        data = dict(data)
        data["errors"] = {k: ErrorEvent.from_dict(v) for k, v in (data.get("errors") or {}).items()}
        return cls(**data)


@dataclass
class StepResult:
    """What happened in one call to :meth:`EpisodeEngine.step` or :meth:`EpisodeEngine.respond`."""

    events: list[dict[str, Any]] = field(default_factory=list)
    decision: Decision | None = None
    card: dict[str, Any] | None = None
    status: str = "running"

    def extend(self, other: StepResult) -> StepResult:
        self.events += other.events
        self.decision = other.decision or self.decision
        self.card = other.card
        self.status = other.status
        return self


class EpisodeEngine:
    def __init__(
        self,
        scenario: Scenario,
        pause: AgentPause,
        *,
        seed: int,
        episode: int = 0,
        condition: str = "default",
        config: EngineConfig | None = None,
        user: SimulatedUser | None = None,
        state: EpisodeState | None = None,
    ) -> None:
        self.scenario = scenario
        self.pause = pause
        self.config = config or EngineConfig()
        self.user = user
        if state is None:
            self.state = EpisodeState(
                scenario_id=scenario.id, policy=pause.policy.name, seed=seed, episode=episode, condition=condition
            )
            self._inject_ground_truth()
        else:
            self.state = state

    # ---- setup ---------------------------------------------------------------------------
    def _rng(self, *parts: object) -> random.Random:
        return derive_rng(self.state.seed, self.scenario.id, self.state.episode, *parts)

    def _inject_ground_truth(self) -> None:
        """Sample which assumptions are wrong and which mistakes occur (depends only on the seed)."""
        state = self.state
        sc = self.scenario
        for assumption in sc.assumptions:
            rng = self._rng("assumption", assumption.id)
            wrong = rng.random() < assumption.wrong_probability
            truth = rng.choice(assumption.alternatives) if wrong else assumption.agent_value
            state.truth[assumption.id] = truth
            state.values[assumption.id] = assumption.agent_value
            if wrong:
                harm_index = sc.harm_step(assumption.id, self.config.commitment_recoverability)
                harm_step = sc.steps[harm_index]
                introduced = sc.step_index(assumption.introduced_at)
                state.errors[f"assumption:{assumption.id}"] = ErrorEvent(
                    id=f"assumption:{assumption.id}",
                    kind="assumption",
                    ref=assumption.id,
                    description=f"Wrong assumption: {assumption.description} (you meant: {truth}). {assumption.if_wrong}",
                    source_step=introduced,
                    harm_step=harm_index,
                    visible_steps=list(range(introduced, harm_index + 1)),
                    severity=float(assumption.severity if assumption.severity is not None else harm_step.severity),
                    recoverability=harm_step.recoverability,
                )
        for mistake in sc.mistakes:
            if self._rng("mistake", mistake.id).random() < mistake.probability:
                state.errors[f"mistake:{mistake.id}"] = ErrorEvent(
                    id=f"mistake:{mistake.id}",
                    kind="mistake",
                    ref=mistake.id,
                    description=mistake.description,
                    source_step=sc.step_index(mistake.step),
                    harm_step=sc.step_index(mistake.harm_at),
                    visible_steps=[sc.step_index(s) for s in mistake.visible_at],
                    severity=mistake.severity,
                    recoverability=mistake.recoverability,
                )

    # ---- views ---------------------------------------------------------------------------
    @property
    def done(self) -> bool:
        return self.state.status in ("completed", "cancelled")

    def current_step(self) -> Step | None:
        if self.state.index >= len(self.scenario.steps):
            return None
        return self.scenario.steps[self.state.index]

    def _pending_mistakes_visible(self, index: int) -> list[ErrorEvent]:
        return [
            e
            for e in self.state.errors.values()
            if e.kind == "mistake" and e.status == "pending" and index in e.visible_steps and e.source_step <= index
        ]

    def preview(self, index: int) -> dict[str, str]:
        step = self.scenario.steps[index]
        fields = dict(step.preview)
        for event in self._pending_mistakes_visible(index):
            mistake = next(m for m in self.scenario.mistakes if m.id == event.ref)
            fields.update(mistake.preview.get(step.id, {}))
        return {k: self.scenario.render(v, self.state.values) for k, v in fields.items()}

    def brief(self) -> str:
        return self.scenario.render(self.scenario.brief, self.state.truth)

    def build_context(self) -> ActionContext:
        step = self.current_step()
        if step is None:
            raise EngineError("Episode has no remaining steps")
        i = self.state.index
        sc = self.scenario
        rng = self._rng("confidence", i, self.state.attempt)
        confidence = step.agent_confidence + rng.uniform(-self.config.confidence_noise, self.config.confidence_noise)
        visible = self._pending_mistakes_visible(i)
        if any(e.source_step == i for e in visible):
            confidence -= self.config.calibration * self.config.confidence_drop
        elif visible:
            confidence -= self.config.propagated_calibration * self.config.confidence_drop
        new_assumptions = tuple(
            Assumption(
                id=a.id,
                description=a.description,
                confidence=a.confidence,
                kind=a.kind,
                options=a.options,
                agent_value=self.state.values[a.id],
                provenance=Provenance.SIMULATED,
            )
            for a in sc.assumptions
            if a.introduced_at == step.id
        )
        plan = tuple(
            PlannedAction(
                step=j,
                action=s.action,
                category=s.category,
                description=s.label,
                severity=s.severity,
                recoverability=s.recoverability,
                depends_on=s.depends_on,
                at_breakpoint=s.breakpoint,
                cognitive_load=s.load,
            )
            for j, s in enumerate(sc.steps)
            if j > i
        )
        n = len(sc.steps)
        return ActionContext(
            action=step.action,
            description=sc.render(step.description, self.state.values),
            category=step.category,
            severity=step.severity,
            recoverability=step.recoverability,
            agent_confidence=clamp01(confidence),
            intent_confidence=step.intent_confidence,
            task_progress=i / max(1, n - 1),
            at_breakpoint=step.breakpoint,
            cognitive_load=step.load,
            external_effects=step.external,
            requires_human_input=step.requires_human_input,
            assumptions=new_assumptions,
            depends_on=step.depends_on,
            plan=plan,
            step=i,
            action_key=step.action,
            provenance={
                "agent_confidence": Provenance.SIMULATED,
                "intent_confidence": Provenance.SIMULATED,
                "cognitive_load": Provenance.SIMULATED,
                "at_breakpoint": Provenance.SIMULATED,
                "severity": Provenance.ESTIMATED,
                "recoverability": Provenance.ESTIMATED,
                "task_progress": Provenance.INFERRED,
            },
            metadata={"scenario": sc.id, "step_id": step.id, "simulated": True},
        )

    # ---- running -------------------------------------------------------------------------
    def step(self) -> StepResult:
        if self.state.status != "running":
            raise EngineError(f"Cannot step: episode is {self.state.status}")
        skipped = self._skip_unneeded_steps()
        if self.done:
            return StepResult(events=skipped, status=self.state.status)
        step = self.current_step()
        assert step is not None
        i = self.state.index
        context = self.build_context()
        decision = self.pause.evaluate(context=context)
        result = StepResult(events=skipped, decision=decision)
        self.state.bump("decisions")
        self.state.bump(f"decision_{decision.decision.value.lower()}")
        error_present = bool(self._pending_mistakes_visible(i)) or any(
            self.state.values[a] != self.state.truth[a] for a in step.depends_on
        )
        record = self._record(decision, context, error_present)
        result.events.append(
            self._event(
                "decision",
                step=i,
                step_id=step.id,
                label=step.label,
                description=context.description,
                decision=decision.to_dict(),
                record=record,
            )
        )

        if decision.should_proceed:
            if decision.decision == DecisionType.DEFER:
                self.state.bump("deferrals")
            result.events += self._execute(i, decision.decision)
            result.status = self.state.status
            return result

        card = self._open_card(decision, context)
        result.card = card
        result.status = self.state.status
        result.events.append(self._event("intervention", step=i, card=self._public_card(card)))
        if self.user is not None:
            response = self.user.respond(
                self._card_truth(card), self._rng("user", i, self.state.attempt, self.state.sequence)
            )
            result.extend(self.respond(response))
        return result

    def respond(self, response: HumanResponse) -> StepResult:
        if self.state.status != "awaiting_human" or self.state.pending is None:
            raise EngineError("No intervention is awaiting a response")
        card = self.state.pending
        decision = Decision.from_dict(card["decision"])
        i = card["step_index"]
        step = self.scenario.steps[i]
        result = StepResult(decision=decision)
        kind = response.response

        if kind == ResponseType.ASK_WHY:
            result.events.append(self._event("ask_why", step=i, timing=card["decision"].get("timing")))
            result.card = self._public_card(card)
            result.status = self.state.status
            return result

        self.state.human_time_s += response.response_time_s
        self.state.clock_s += response.response_time_s
        self.state.bump("responses")
        self.state.bump(f"response_{kind.value}")
        records = [r for r in self.state.records if r["step_index"] == i and r.get("intervention")]
        if records:
            records[-1]["user_response"] = kind.value
            records[-1]["response_time_s"] = round(response.response_time_s, 3)

        # 1. clarification answers (also shown on batched confirmation cards)
        answers = dict(response.answers)
        for a_id in card["assumption_ids"]:
            if a_id not in answers and kind in (ResponseType.APPROVE, ResponseType.ANSWER, ResponseType.OVERRIDE):
                answers[a_id] = self.state.values[a_id]
            if kind == ResponseType.TAKEOVER:
                answers[a_id] = self.state.truth[a_id]
        corrections_before = self.state.counters.get("corrections", 0)
        for a_id, answer in answers.items():
            self._apply_answer(a_id, answer, i)
        corrected = self.state.counters.get("corrections", 0) > corrections_before
        if kind in (ResponseType.APPROVE, ResponseType.ANSWER) and not corrected:
            self.state.bump("accepted")

        # 2. the action itself
        executes = False
        if kind == ResponseType.CANCEL_TASK:
            self.state.status = "cancelled"
            for event in self.state.errors.values():
                if event.status == "pending":
                    event.status = "averted"
        elif decision.decision == DecisionType.CLARIFY:
            pass  # the agent re-proposes the same step with the answers applied
        elif kind in (ResponseType.APPROVE, ResponseType.OVERRIDE):
            self._count_misses(i)
            executes = True
        elif kind in (ResponseType.EDIT, ResponseType.TAKEOVER):
            self._fix_visible(i)
            if kind == ResponseType.TAKEOVER:
                for a_id in step.depends_on:
                    self._apply_answer(a_id, self.state.truth[a_id], i)
            executes = True
        elif kind == ResponseType.REJECT:
            if self._pending_mistakes_visible(i):
                self._fix_visible(i)
            else:
                self.state.bump("false_rejections")
            self.state.attempt += 1
            if self.state.attempt > self.config.max_attempts:
                self._fix_visible(i)
                self.state.human_time_s += 45.0
                self.state.clock_s += 45.0
                executes = True
        elif kind == ResponseType.ANSWER:
            pass
        elif kind == ResponseType.TIMEOUT:
            executes = decision.decision != DecisionType.BLOCK
            if executes:
                self._count_misses(i)

        self.pause.respond(decision, kind, answers=answers)
        result.events.append(self._event("response", step=i, response=response.to_dict()))
        self.state.pending = None
        if self.state.status == "awaiting_human":
            self.state.status = "running"
        if executes:
            result.events += self._execute(i, decision.decision)
        result.status = self.state.status
        return result

    def run(self, max_iterations: int = 200) -> EpisodeState:
        """Run to completion with the simulated user."""
        if self.user is None:
            raise EngineError("run() needs a simulated user; use step()/respond() for humans")
        iterations = 0
        while not self.done:
            iterations += 1
            if iterations > max_iterations:
                raise EngineError("Episode did not terminate (check the scenario and policy)")
            self.step()
        return self.state

    # ---- internals -----------------------------------------------------------------------
    def _skip_unneeded_steps(self) -> list[dict[str, Any]]:
        """Skip steps made unnecessary by the user's answers (e.g. "Do not email anyone")."""
        events: list[dict[str, Any]] = []
        while (step := self.current_step()) is not None and step.skipped(self.state.values):
            i = self.state.index
            for event in self.state.errors.values():
                if event.status == "pending" and event.kind == "mistake" and event.harm_step == i:
                    event.status = "averted"
            self.state.executed.append(
                {"index": i, "step_id": step.id, "decision": "SKIPPED", "harm": [], "wrong_basis": [], "skipped": True}
            )
            self.state.index += 1
            self.state.attempt = 0
            events.append(
                self._event("skipped", step=i, step_id=step.id, label=step.label, reason="Not needed given your answer")
            )
        if self.state.index >= len(self.scenario.steps) and self.state.status == "running":
            events += self._complete()
        return events

    def _complete(self) -> list[dict[str, Any]]:
        self.state.status = "completed"
        for event in self.state.errors.values():
            if event.status == "pending":
                event.status = "averted"
        self._finalize_records()
        return [self._event("completed", summary=self.outcome())]

    def _execute(self, i: int, decision_type: DecisionType) -> list[dict[str, Any]]:
        step = self.scenario.steps[i]
        harmed: list[str] = []
        for event in self.state.errors.values():
            if event.status != "pending":
                continue
            active = event.kind == "mistake" or self.state.values[event.ref] != self.state.truth[event.ref]
            if active and event.harm_step == i:
                event.status = "harm"
                harmed.append(event.id)
        wrong_basis = [a for a in step.depends_on if self.state.values[a] != self.state.truth[a]]
        self.state.executed.append(
            {
                "index": i,
                "step_id": step.id,
                "decision": decision_type.value,
                "harm": harmed,
                "wrong_basis": wrong_basis,
            }
        )
        self.state.clock_s += step.duration_s
        self.state.index += 1
        self.state.attempt = 0
        events = [self._event("executed", step=i, step_id=step.id, harm=harmed, simulated=True)]
        if self.state.index >= len(self.scenario.steps):
            events += self._complete()
        else:
            events += self._skip_unneeded_steps()
        return events

    def _apply_answer(self, assumption_id: str, answer: str, i: int) -> None:
        current = self.state.values[assumption_id]
        truth = self.state.truth[assumption_id]
        event = self.state.errors.get(f"assumption:{assumption_id}")
        if answer == current:
            if event is not None and event.status == "pending" and current != truth:
                self.state.bump("human_misses")
            return
        self.state.values[assumption_id] = answer
        self.state.bump("corrections")
        if event is not None and event.status == "pending" and answer == truth:
            event.status = "caught"
            event.caught_at = i
            rework = [e for e in self.state.executed if assumption_id in e["wrong_basis"] and not e.get("reworked")]
            for entry in rework:
                entry["reworked"] = True
                self.state.clock_s += self.scenario.steps[entry["index"]].duration_s
            event.rework_steps = len(rework)
            self.state.bump("rework_steps", len(rework))

    def _fix_visible(self, i: int) -> None:
        for event in self._pending_mistakes_visible(i):
            event.status = "caught"
            event.caught_at = i
            if event.source_step < i:
                event.rework_steps = 1
                self.state.bump("rework_steps")
                self.state.clock_s += self.scenario.steps[event.source_step].duration_s

    def _count_misses(self, i: int) -> None:
        if self._pending_mistakes_visible(i):
            self.state.bump("human_misses", len(self._pending_mistakes_visible(i)))

    def _open_card(self, decision: Decision, context: ActionContext) -> dict[str, Any]:
        i = self.state.index
        step = self.scenario.steps[i]
        has_confirmation = decision.decision == DecisionType.BLOCK or any(
            q.kind == InterventionKind.CONFIRMATION for q in decision.questions
        )
        assumption_ids = [q.assumption_id for q in decision.questions if q.assumption_id]
        shown: list[str] = []
        if has_confirmation:
            shown += [e.id for e in self._pending_mistakes_visible(i)]
        for a_id in assumption_ids:
            event = self.state.errors.get(f"assumption:{a_id}")
            if event is not None and event.status == "pending" and self.state.values[a_id] != self.state.truth[a_id]:
                shown.append(event.id)
        if decision.decision == DecisionType.BLOCK:
            for a_id in step.depends_on:
                event = self.state.errors.get(f"assumption:{a_id}")
                if (
                    event is not None
                    and event.status == "pending"
                    and self.state.values[a_id] != self.state.truth[a_id]
                ):
                    shown.append(event.id)
        for error_id in set(shown):
            self.state.errors[error_id].shown_at.append(i)
        necessary = bool(shown) or step.requires_human_input
        self.state.bump("interventions")
        self.state.bump("necessary" if necessary else "unnecessary")
        self.state.bump("questions", max(1, len(decision.questions)))
        if len(decision.questions) > 1:
            self.state.bump("batched_interventions")
        self.state.interruption_steps.append(i)
        for record in reversed(self.state.records):
            if record["step_index"] == i:
                record["necessary"] = necessary
                break
        window = self.user.params.habituation_window if self.user is not None else 8
        recent = sum(1 for s in self.state.interruption_steps[:-1] if i - window <= s < i)
        card = {
            "intervention_id": f"{self.state.scenario_id}-{self.state.seed}-{self.state.episode}-{i}-{self.state.sequence}",
            "step_index": i,
            "step_id": step.id,
            "decision": decision.to_dict(),
            "has_confirmation": has_confirmation,
            "assumption_ids": assumption_ids,
            "shown_errors": sorted(set(shown)),
            "necessary": necessary,
            "recent_interruptions": recent,
            "action": {
                "label": step.label,
                "description": context.description,
                "category": step.category.value,
                "consequence": step.consequence,
                "undo": step.undo,
                "reversible": step.reversible,
                "recoverability": step.recoverability,
                "severity": step.severity,
                "what_could_go_wrong": step.what_could_go_wrong,
                "preview": self.preview(i),
                "alternatives": list(step.alternatives),
                "requires_human_input": step.requires_human_input,
                "agent_confidence": context.agent_confidence,
                "simulated": True,
            },
            "assumptions": [
                {
                    "id": a_id,
                    "description": self.scenario.assumption(a_id).description,
                    "kind": self.scenario.assumption(a_id).kind.value,
                    "agent_value": self.state.values[a_id],
                    "options": list(self.scenario.assumption(a_id).options),
                    "confidence": self.scenario.assumption(a_id).confidence,
                    "if_wrong": self.scenario.assumption(a_id).if_wrong,
                }
                for a_id in assumption_ids
            ],
            "allowed_responses": self._allowed(decision),
        }
        self.state.pending = card
        self.state.status = "awaiting_human"
        return card

    @staticmethod
    def _allowed(decision: Decision) -> list[str]:
        if decision.decision == DecisionType.BLOCK:
            return ["takeover", "override", "ask_why", "cancel_task"]
        if decision.decision == DecisionType.CLARIFY:
            return ["answer", "ask_why", "cancel_task"]
        return ["approve", "edit", "reject", "ask_why", "cancel_task"]

    @staticmethod
    def _public_card(card: dict[str, Any]) -> dict[str, Any]:
        """The card as shown to a participant: ground-truth labels removed."""
        return {k: v for k, v in card.items() if k not in ("shown_errors", "necessary")}

    def public_pending(self) -> dict[str, Any] | None:
        return self._public_card(self.state.pending) if self.state.pending else None

    def _card_truth(self, card: dict[str, Any]) -> CardTruth:
        i = card["step_index"]
        return CardTruth(
            step_index=i,
            decision=DecisionType(card["decision"]["decision"]),
            load=self.scenario.steps[i].load,
            has_confirmation=card["has_confirmation"],
            requires_human_input=card["action"]["requires_human_input"],
            action_mistakes=[e.id for e in self._pending_mistakes_visible(i)] if card["has_confirmation"] else [],
            assumptions={a: (self.state.values[a], self.state.truth[a]) for a in card["assumption_ids"]},
            recent_interruptions=card["recent_interruptions"],
            n_questions=max(1, len(card["decision"].get("questions", []))),
        )

    def _record(self, decision: Decision, context: ActionContext, error_present: bool) -> dict[str, Any]:
        signals = decision.signals
        record = {
            "scenario": self.scenario.id,
            "policy": self.pause.policy.name,
            "condition": self.state.condition,
            "seed": self.state.seed,
            "episode": self.state.episode,
            "participant_id": f"sim-{self.state.episode:04d}",
            "step_index": self.state.index,
            "attempt": self.state.attempt,
            "step_id": self.scenario.steps[self.state.index].id,
            "action": context.action,
            "category": context.category.value,
            "severity": signals.get("severity"),
            "recoverability": signals.get("recoverability"),
            "agent_confidence": signals.get("agent_confidence"),
            "intent_confidence": signals.get("intent_confidence"),
            "cognitive_load": signals.get("cognitive_load"),
            "external_effects": signals.get("external_effects"),
            "at_breakpoint": signals.get("at_breakpoint"),
            "task_progress": signals.get("task_progress"),
            "habituation": signals.get("habituation"),
            "decision": decision.decision.value,
            "score": round(decision.score, 6),
            "decision_confidence": decision.confidence,
            "reason_codes": ";".join(decision.reason_codes),
            "n_questions": len(decision.questions),
            "n_deferred": len(decision.deferred),
            "intervention": decision.decision.interrupts_now,
            "necessary": None,
            "error_present": error_present,
            "decision_latency_ms": round(decision.latency_ms or 0.0, 4),
            "sim_time_s": round(self.state.clock_s, 3),
            "user_response": None,
            "response_time_s": None,
            "task_success": None,
            "task_duration_s": None,
            "subjective_rating": None,
        }
        self.state.records.append(record)
        return record

    def _finalize_records(self) -> None:
        outcome = self.outcome()
        for record in self.state.records:
            record["task_success"] = outcome["task_success"]
            record["task_duration_s"] = outcome["task_duration_s"]

    def _event(self, kind: str, **payload: Any) -> dict[str, Any]:
        self.state.sequence += 1
        return {"seq": self.state.sequence, "type": kind, "sim_time_s": round(self.state.clock_s, 3), **payload}

    # ---- outcome -------------------------------------------------------------------------
    def outcome(self) -> dict[str, Any]:
        errors = list(self.state.errors.values())
        harmful = [e for e in errors if e.status == "harm"]
        return {
            "status": self.state.status,
            "task_success": self.state.status == "completed" and not harmful,
            "task_duration_s": round(self.state.clock_s, 3),
            "human_time_s": round(self.state.human_time_s, 3),
            "errors_total": len(errors),
            "errors_caught": sum(1 for e in errors if e.status == "caught"),
            "errors_harmful": len(harmful),
            "missed_interventions": sum(1 for e in harmful if not e.shown_at),
            "harm": round(sum(e.harm for e in harmful), 6),
        }

    # ---- persistence ---------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario.id,
            "config": self.config.to_dict(),
            "state": self.state.to_dict(),
            "pause": self.pause.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], scenario: Scenario, *, user: SimulatedUser | None = None) -> EpisodeEngine:
        state = EpisodeState.from_dict(data["state"])
        pause = AgentPause.from_dict(data["pause"])
        return cls(
            scenario,
            pause,
            seed=state.seed,
            episode=state.episode,
            condition=state.condition,
            config=EngineConfig.from_dict(data.get("config")),
            user=user,
            state=state,
        )
