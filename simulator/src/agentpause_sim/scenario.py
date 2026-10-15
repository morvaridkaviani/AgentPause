"""Scenario definitions: the scripted tasks the simulated agent performs.

A scenario is a JSON file with a user instruction, the **intent assumptions** the agent has to
make, and a sequence of **steps**. **Mistakes** can be injected into steps. All actions are
simulated. Nothing in a scenario touches real money, email, files, or calendars.

Error events, the ground truth used by the metrics, come in two kinds:

* **Mistakes**: the agent executes something wrong (e.g. an autocompleted address). A mistake
  is *visible* at certain steps (an approval card there shows it) and causes harm at its
  ``harm_at`` step if still uncorrected.
* **Wrong assumptions**: the agent's interpretation of the instruction is wrong. A wrong
  assumption is visible whenever an intervention asks about it, and causes harm at its first
  irreversible dependent step (its commitment point) or, failing that, at its last dependent
  step.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from agentpause import AssumptionKind, ConsequenceCategory
from agentpause.categories import parse_category, prior_for

_PLACEHOLDER = re.compile(r"\{([a-z0-9_]+)\}")


class ScenarioError(ValueError):
    """Raised when a scenario file is invalid."""


@dataclass(frozen=True)
class ScenarioAssumption:
    id: str
    description: str
    kind: AssumptionKind
    confidence: float
    agent_value: str
    alternatives: tuple[str, ...]
    wrong_probability: float
    introduced_at: str
    if_wrong: str
    severity: float | None = None
    """Harm if the wrong assumption reaches its commitment point. Defaults to that step's severity."""

    @property
    def options(self) -> tuple[str, ...]:
        return (self.agent_value, *self.alternatives)


@dataclass(frozen=True)
class Mistake:
    id: str
    step: str
    description: str
    probability: float
    severity: float
    recoverability: float
    visible_at: tuple[str, ...]
    harm_at: str
    preview: dict[str, dict[str, str]] = field(default_factory=dict)
    """Per step id: preview fields that change when the mistake is present."""


@dataclass(frozen=True)
class Step:
    id: str
    action: str
    label: str
    description: str
    subtask: str
    category: ConsequenceCategory
    severity: float
    recoverability: float
    agent_confidence: float
    depends_on: tuple[str, ...]
    breakpoint: bool
    load: float
    duration_s: float
    consequence: str
    undo: str
    what_could_go_wrong: str
    preview: dict[str, str]
    alternatives: tuple[str, ...]
    requires_human_input: bool = False
    external: bool | None = None
    intent_confidence: float = 0.97
    """Residual intent confidence not attached to an explicit assumption."""
    skip_if: dict[str, str] = field(default_factory=dict)
    """Skip the step when these assumptions have these values (e.g. "Do not email anyone")."""

    def skipped(self, values: dict[str, str]) -> bool:
        return bool(self.skip_if) and all(values.get(k) == v for k, v in self.skip_if.items())

    @property
    def reversible(self) -> bool:
        return self.recoverability >= 0.5


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    agent_name: str
    domain: str
    icon: str
    goal: str
    brief: str
    description: str
    assumptions: tuple[ScenarioAssumption, ...]
    steps: tuple[Step, ...]
    mistakes: tuple[Mistake, ...]

    def step_index(self, step_id: str) -> int:
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                return i
        raise KeyError(step_id)

    def assumption(self, assumption_id: str) -> ScenarioAssumption:
        for assumption in self.assumptions:
            if assumption.id == assumption_id:
                return assumption
        raise KeyError(assumption_id)

    def dependents(self, assumption_id: str) -> list[int]:
        return [i for i, s in enumerate(self.steps) if assumption_id in s.depends_on]

    def harm_step(self, assumption_id: str, commitment_recoverability: float = 0.5) -> int:
        """Index of the step where a wrong assumption causes harm."""
        deps = self.dependents(assumption_id)
        for i in deps:
            if self.steps[i].recoverability < commitment_recoverability:
                return i
        return deps[-1]

    def render(self, text: str, values: dict[str, str]) -> str:
        return _PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), text)

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "icon": self.icon,
            "goal": self.goal,
            "description": self.description,
            "n_steps": len(self.steps),
            "n_assumptions": len(self.assumptions),
            "n_mistakes": len(self.mistakes),
            "irreversible_steps": [s.label for s in self.steps if not s.reversible],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "brief": self.brief,
            "assumptions": [
                {
                    "id": a.id,
                    "description": a.description,
                    "kind": a.kind.value,
                    "confidence": a.confidence,
                    "agent_value": a.agent_value,
                    "alternatives": list(a.alternatives),
                    "wrong_probability": a.wrong_probability,
                    "introduced_at": a.introduced_at,
                    "if_wrong": a.if_wrong,
                }
                for a in self.assumptions
            ],
            "steps": [
                {
                    "id": s.id,
                    "action": s.action,
                    "label": s.label,
                    "description": s.description,
                    "subtask": s.subtask,
                    "category": s.category.value,
                    "severity": s.severity,
                    "recoverability": s.recoverability,
                    "reversible": s.reversible,
                    "agent_confidence": s.agent_confidence,
                    "depends_on": list(s.depends_on),
                    "breakpoint": s.breakpoint,
                    "load": s.load,
                    "duration_s": s.duration_s,
                    "consequence": s.consequence,
                    "undo": s.undo,
                    "what_could_go_wrong": s.what_could_go_wrong,
                    "requires_human_input": s.requires_human_input,
                    "skip_if": dict(s.skip_if),
                }
                for s in self.steps
            ],
            "mistakes": [
                {
                    "id": m.id,
                    "step": m.step,
                    "description": m.description,
                    "probability": m.probability,
                    "severity": m.severity,
                    "visible_at": list(m.visible_at),
                    "harm_at": m.harm_at,
                }
                for m in self.mistakes
            ],
        }


# ---------------------------------------------------------------------------------------
def _num(data: dict[str, Any], key: str, default: float | None = None, *, where: str) -> float:
    value = data.get(key, default)
    if value is None:
        raise ScenarioError(f"{where}: missing '{key}'")
    value = float(value)
    if not 0.0 <= value <= 1.0 and key not in ("duration_s",):
        raise ScenarioError(f"{where}: '{key}'={value} outside [0, 1]")
    return value


def parse_scenario(data: dict[str, Any]) -> Scenario:
    sid = str(data.get("id", "")).strip()
    if not sid:
        raise ScenarioError("scenario needs an 'id'")
    step_ids: list[str] = []
    steps: list[Step] = []
    for raw in data.get("steps", []):
        where = f"{sid}.steps.{raw.get('id', '?')}"
        category = parse_category(raw.get("category"))
        prior = prior_for(category)
        step = Step(
            id=str(raw["id"]),
            action=str(raw.get("action", raw["id"])),
            label=str(raw.get("label", raw["id"])),
            description=str(raw.get("description", "")),
            subtask=str(raw.get("subtask", "")),
            category=category,
            severity=_num(raw, "severity", prior.severity, where=where),
            recoverability=_num(raw, "recoverability", prior.recoverability, where=where),
            agent_confidence=_num(raw, "agent_confidence", 0.9, where=where),
            depends_on=tuple(raw.get("depends_on", [])),
            breakpoint=bool(raw.get("breakpoint", False)),
            load=_num(raw, "load", 0.3, where=where),
            duration_s=float(raw.get("duration_s", 5.0)),
            consequence=str(raw.get("consequence", prior.description)),
            undo=str(raw.get("undo", "")),
            what_could_go_wrong=str(raw.get("what_could_go_wrong", "")),
            preview={str(k): str(v) for k, v in (raw.get("preview") or {}).items()},
            alternatives=tuple(raw.get("alternatives", [])),
            requires_human_input=bool(raw.get("requires_human_input", False)),
            external=raw.get("external"),
            intent_confidence=_num(raw, "intent_confidence", 0.97, where=where),
            skip_if={str(k): str(v) for k, v in (raw.get("skip_if") or {}).items()},
        )
        if step.id in step_ids:
            raise ScenarioError(f"{where}: duplicate step id")
        step_ids.append(step.id)
        steps.append(step)
    if not steps:
        raise ScenarioError(f"{sid}: no steps")

    assumptions: list[ScenarioAssumption] = []
    for raw in data.get("assumptions", []):
        where = f"{sid}.assumptions.{raw.get('id', '?')}"
        confidence = _num(raw, "confidence", where=where)
        assumption = ScenarioAssumption(
            id=str(raw["id"]),
            description=str(raw["description"]),
            kind=AssumptionKind(raw.get("kind", "input")),
            confidence=confidence,
            agent_value=str(raw["agent_value"]),
            alternatives=tuple(str(v) for v in raw.get("alternatives", [])),
            wrong_probability=_num(raw, "wrong_probability", round(1.0 - confidence, 4), where=where),
            introduced_at=str(raw.get("introduced_at", steps[0].id)),
            if_wrong=str(raw.get("if_wrong", "")),
            severity=raw.get("severity"),
        )
        if not assumption.alternatives:
            raise ScenarioError(f"{where}: needs at least one alternative value")
        if assumption.introduced_at not in step_ids:
            raise ScenarioError(f"{where}: introduced_at '{assumption.introduced_at}' is not a step")
        dependents = [s for s in steps if assumption.id in s.depends_on]
        if not dependents:
            raise ScenarioError(f"{where}: no step depends on this assumption")
        if step_ids.index(dependents[0].id) < step_ids.index(assumption.introduced_at):
            raise ScenarioError(f"{where}: a step depends on it before it is introduced")
        assumptions.append(assumption)
    assumption_ids = {a.id for a in assumptions}
    by_id = {a.id: a for a in assumptions}
    for step in steps:
        unknown = set(step.depends_on) - assumption_ids
        if unknown:
            raise ScenarioError(f"{sid}.steps.{step.id}: depends on unknown assumption(s) {sorted(unknown)}")
        for a_id, value in step.skip_if.items():
            if a_id not in by_id or value not in by_id[a_id].options:
                raise ScenarioError(f"{sid}.steps.{step.id}: skip_if {a_id}={value!r} is not a known option")

    mistakes: list[Mistake] = []
    for raw in data.get("mistakes", []):
        where = f"{sid}.mistakes.{raw.get('id', '?')}"
        step_id = str(raw["step"])
        if step_id not in step_ids:
            raise ScenarioError(f"{where}: unknown step '{step_id}'")
        harm_at = str(raw.get("harm_at", step_id))
        visible_at = tuple(raw.get("visible_at", [step_id]))
        for ref in (harm_at, *visible_at):
            if ref not in step_ids:
                raise ScenarioError(f"{where}: unknown step '{ref}'")
        if step_ids.index(harm_at) < step_ids.index(step_id):
            raise ScenarioError(f"{where}: harm_at precedes the step that introduces the mistake")
        harm_step = steps[step_ids.index(harm_at)]
        mistakes.append(
            Mistake(
                id=str(raw["id"]),
                step=step_id,
                description=str(raw["description"]),
                probability=_num(raw, "probability", where=where),
                severity=_num(raw, "severity", harm_step.severity, where=where),
                recoverability=_num(raw, "recoverability", harm_step.recoverability, where=where),
                visible_at=visible_at,
                harm_at=harm_at,
                preview={
                    str(k): {str(f): str(v) for f, v in fields.items()}
                    for k, fields in (raw.get("preview") or {}).items()
                },
            )
        )

    return Scenario(
        id=sid,
        name=str(data.get("name", sid)),
        agent_name=str(data.get("agent_name", "Agent")),
        domain=str(data.get("domain", sid)),
        icon=str(data.get("icon", "bot")),
        goal=str(data.get("goal", "")),
        brief=str(data.get("brief", "")),
        description=str(data.get("description", "")),
        assumptions=tuple(assumptions),
        steps=tuple(steps),
        mistakes=tuple(mistakes),
    )


def load_scenario_file(path: str | Path) -> Scenario:
    return parse_scenario(json.loads(Path(path).read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def _bundled() -> dict[str, Scenario]:
    out: dict[str, Scenario] = {}
    folder = resources.files("agentpause_sim") / "scenarios"
    for entry in sorted(folder.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".json"):
            scenario = parse_scenario(json.loads(entry.read_text(encoding="utf-8")))
            out[scenario.id] = scenario
    return out


SCENARIO_ORDER = ("travel", "email", "shopping", "files", "calendar", "research")


def list_scenarios() -> list[Scenario]:
    bundled = _bundled()
    ordered = [bundled[s] for s in SCENARIO_ORDER if s in bundled]
    ordered += [s for k, s in bundled.items() if k not in SCENARIO_ORDER]
    return ordered


def load_scenario(scenario_id: str) -> Scenario:
    bundled = _bundled()
    if scenario_id not in bundled:
        raise KeyError(f"Unknown scenario {scenario_id!r}. Available: {', '.join(bundled)}")
    return bundled[scenario_id]
