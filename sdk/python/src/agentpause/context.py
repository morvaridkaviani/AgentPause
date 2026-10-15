"""Input data model: what an agent tells AgentPause about a proposed action."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any, ClassVar

from .categories import parse_category
from .types import AssumptionKind, ConsequenceCategory, Provenance


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(result) else result


@dataclass(frozen=True)
class Assumption:
    """An interpretation of the user's intent that the agent is acting on.

    Intent ambiguity is attached to explicit assumptions rather than a single scalar, so that
    AgentPause can (a) ask *about something specific* (CLARIFY), (b) find the first
    irreversible action that depends on it (its *commitment point*), and (c) decide whether
    the question can wait.

    Example: ``Assumption("travel_date", "'next Friday' means Fri 14 Nov", confidence=0.7,
    kind=AssumptionKind.INPUT, options=("Fri 14 Nov", "Fri 21 Nov"))``.
    """

    id: str
    description: str
    confidence: float
    kind: AssumptionKind = AssumptionKind.INPUT
    options: tuple[str, ...] = ()
    agent_value: str | None = None
    provenance: Provenance = Provenance.AGENT_PROVIDED

    def __post_init__(self) -> None:
        # Accept plain strings and lists, as the lenient dict/keyword entry points do.
        kind: Any = self.kind
        provenance: Any = self.provenance
        options: Any = self.options
        if not isinstance(kind, AssumptionKind):
            object.__setattr__(self, "kind", AssumptionKind(kind))
        if not isinstance(provenance, Provenance):
            object.__setattr__(self, "provenance", Provenance(provenance))
        if not isinstance(options, tuple):
            object.__setattr__(self, "options", tuple(options))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "confidence": self.confidence,
            "kind": self.kind.value,
            "options": list(self.options),
            "agent_value": self.agent_value,
            "provenance": self.provenance.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Assumption:
        return cls(
            id=str(data["id"]),
            description=str(data.get("description", "")),
            confidence=float(data.get("confidence", 0.5)),
            kind=AssumptionKind(data.get("kind", AssumptionKind.INPUT.value)),
            options=tuple(data.get("options", ()) or ()),
            agent_value=data.get("agent_value"),
            provenance=Provenance(data.get("provenance", Provenance.AGENT_PROVIDED.value)),
        )


@dataclass(frozen=True)
class PlannedAction:
    """A future step the agent expects to take. Used for timing lookahead only.

    ``step`` is the absolute step index in the session (the current action has
    ``ActionContext.step``). Unknown fields fall back to category priors.
    """

    step: int
    action: str
    category: ConsequenceCategory = ConsequenceCategory.OTHER
    description: str = ""
    severity: float | None = None
    recoverability: float | None = None
    reversible: bool | None = None
    depends_on: tuple[str, ...] = ()
    at_breakpoint: bool | None = None
    cognitive_load: float | None = None

    def __post_init__(self) -> None:
        category: Any = self.category
        depends_on: Any = self.depends_on
        if not isinstance(category, ConsequenceCategory):
            object.__setattr__(self, "category", parse_category(category))
        if not isinstance(depends_on, tuple):
            object.__setattr__(self, "depends_on", tuple(depends_on))

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "category": self.category.value,
            "description": self.description,
            "severity": self.severity,
            "recoverability": self.recoverability,
            "reversible": self.reversible,
            "depends_on": list(self.depends_on),
            "at_breakpoint": self.at_breakpoint,
            "cognitive_load": self.cognitive_load,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlannedAction:
        return cls(
            step=int(data["step"]),
            action=str(data["action"]),
            category=parse_category(data.get("category") or data.get("consequence")),
            description=str(data.get("description", "")),
            severity=_opt_float(data.get("severity")),
            recoverability=_opt_float(data.get("recoverability")),
            reversible=data.get("reversible"),
            depends_on=tuple(data.get("depends_on", ()) or ()),
            at_breakpoint=data.get("at_breakpoint"),
            cognitive_load=_opt_float(data.get("cognitive_load")),
        )


# Signals whose provenance is tracked. Keys are also used in explanations and the UI.
SIGNAL_NAMES: tuple[str, ...] = (
    "agent_confidence",
    "intent_confidence",
    "severity",
    "recoverability",
    "task_progress",
    "at_breakpoint",
    "cognitive_load",
    "external_effects",
)


@dataclass(frozen=True)
class ActionContext:
    """A proposed action plus everything the agent knows about it.

    Only ``action`` is required. Every missing signal is filled with a documented default and
    tagged ``Provenance.DEFAULT``, and the decision carries the reason code
    ``MISSING_SIGNAL_DEFAULTED``.

    Values supplied here are tagged ``Provenance.AGENT_PROVIDED`` unless ``provenance`` says
    otherwise (e.g. ``provenance={"cognitive_load": Provenance.SIMULATED}``).
    """

    action: str
    description: str = ""
    category: ConsequenceCategory = ConsequenceCategory.OTHER
    severity: float | None = None
    reversible: bool | None = None
    recoverability: float | None = None
    agent_confidence: float | None = None
    intent_confidence: float | None = None
    task_progress: float | None = None
    at_breakpoint: bool | None = None
    cognitive_load: float | None = None
    external_effects: bool | None = None
    requires_human_input: bool = False
    assumptions: tuple[Assumption, ...] = ()
    depends_on: tuple[str, ...] = ()
    plan: tuple[PlannedAction, ...] = ()
    step: int | None = None
    action_key: str | None = None
    provenance: dict[str, Provenance] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Direct construction with strings/lists behaves like ``ActionContext.build``.
        category: Any = self.category
        if not isinstance(category, ConsequenceCategory):
            object.__setattr__(self, "category", parse_category(category))
        for name in ("assumptions", "depends_on", "plan"):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                object.__setattr__(self, name, tuple(value))
        provenance: dict[str, Any] = self.provenance
        if any(not isinstance(v, Provenance) for v in provenance.values()):
            object.__setattr__(self, "provenance", {k: Provenance(v) for k, v in self.provenance.items()})

    @property
    def key(self) -> str:
        """Grouping key used to learn from the user's past decisions on similar actions."""
        return self.action_key or self.action

    @property
    def dependency_ids(self) -> tuple[str, ...]:
        """IDs of assumptions this action depends on (declared here or earlier)."""
        ids = list(self.depends_on)
        for assumption in self.assumptions:
            if assumption.id not in ids:
                ids.append(assumption.id)
        return tuple(ids)

    def provenance_of(self, signal: str) -> Provenance:
        return self.provenance.get(signal, Provenance.AGENT_PROVIDED)

    def with_signal(self, signal: str, value: Any) -> ActionContext:
        """Return a copy with one signal replaced. Used by counterfactual explanations."""
        if signal == "reversible":
            return replace(self, reversible=value)
        if signal not in SIGNAL_NAMES:
            raise KeyError(f"Unknown signal: {signal}")
        return replace(self, **{signal: value})

    @classmethod
    def build(cls, action: str, **kwargs: Any) -> ActionContext:
        """Lenient constructor used by the SDK and the REST API.

        Accepts ``consequence`` as an alias of ``category`` (string or enum), plain dicts for
        ``assumptions`` / ``plan``, and string provenances.
        """
        kwargs = dict(kwargs)
        category = kwargs.pop("category", None)
        consequence = kwargs.pop("consequence", None)
        kwargs["category"] = parse_category(category if category is not None else consequence)
        if "user_intent_confidence" in kwargs and kwargs.get("intent_confidence") is None:
            kwargs["intent_confidence"] = kwargs.pop("user_intent_confidence")
        else:
            kwargs.pop("user_intent_confidence", None)
        assumptions = kwargs.pop("assumptions", ()) or ()
        kwargs["assumptions"] = tuple(a if isinstance(a, Assumption) else Assumption.from_dict(a) for a in assumptions)
        plan = kwargs.pop("plan", ()) or ()
        kwargs["plan"] = tuple(p if isinstance(p, PlannedAction) else PlannedAction.from_dict(p) for p in plan)
        kwargs["depends_on"] = tuple(kwargs.pop("depends_on", ()) or ())
        provenance = kwargs.pop("provenance", {}) or {}
        kwargs["provenance"] = {k: Provenance(v) for k, v in provenance.items()}
        for name in (
            "severity",
            "recoverability",
            "agent_confidence",
            "intent_confidence",
            "task_progress",
            "cognitive_load",
        ):
            if name in kwargs:
                kwargs[name] = _opt_float(kwargs[name])
        unknown = set(kwargs) - set(cls.__dataclass_fields__)
        if unknown:
            metadata = dict(kwargs.pop("metadata", {}) or {})
            for name in unknown:
                metadata[name] = kwargs.pop(name)
            kwargs["metadata"] = metadata
        return cls(action=action, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity,
            "reversible": self.reversible,
            "recoverability": self.recoverability,
            "agent_confidence": self.agent_confidence,
            "intent_confidence": self.intent_confidence,
            "task_progress": self.task_progress,
            "at_breakpoint": self.at_breakpoint,
            "cognitive_load": self.cognitive_load,
            "external_effects": self.external_effects,
            "requires_human_input": self.requires_human_input,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "depends_on": list(self.depends_on),
            "plan": [p.to_dict() for p in self.plan],
            "step": self.step,
            "action_key": self.action_key,
            "provenance": {k: v.value for k, v in self.provenance.items()},
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionContext:
        data = dict(data)
        action = str(data.pop("action"))
        return cls.build(action, **data)


@dataclass(frozen=True)
class UserPreferences:
    """Autonomy preferences configured by the user.

    ``profile`` scales the cost the adaptive model assigns to interrupting the user:
    ``fewer_interruptions`` (×2.5), ``balanced`` (×1), ``maximum_control`` (×0.25). The rules
    are hard overrides applied by :class:`~agentpause.policies.UserCustomizedPolicy`.

    Caution from prior work: in Yan (2026), 114 of 140 user-authored rules were "ask", and
    user-authored policies blocked less overreach. Preferences are a research variable here
    (RQ6), not a guaranteed improvement.
    """

    profile: str = "balanced"
    always_ask_categories: tuple[ConsequenceCategory, ...] = ()
    never_ask_categories: tuple[ConsequenceCategory, ...] = ()
    block_categories: tuple[ConsequenceCategory, ...] = ()
    ask_before_irreversible: bool = False
    ask_before_external: bool = False
    allow_low_risk_autonomy: bool = False
    low_risk_threshold: float = 0.15
    max_interruptions_per_task: int | None = None

    PROFILE_MULTIPLIERS: ClassVar[dict[str, float]] = {
        "fewer_interruptions": 2.5,
        "balanced": 1.0,
        "maximum_control": 0.25,
    }

    @property
    def interruption_cost_multiplier(self) -> float:
        return self.PROFILE_MULTIPLIERS.get(self.profile, 1.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "always_ask_categories": [c.value for c in self.always_ask_categories],
            "never_ask_categories": [c.value for c in self.never_ask_categories],
            "block_categories": [c.value for c in self.block_categories],
            "ask_before_irreversible": self.ask_before_irreversible,
            "ask_before_external": self.ask_before_external,
            "allow_low_risk_autonomy": self.allow_low_risk_autonomy,
            "low_risk_threshold": self.low_risk_threshold,
            "max_interruptions_per_task": self.max_interruptions_per_task,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> UserPreferences:
        if not data:
            return cls()
        profile = str(data.get("profile", "balanced"))
        if profile not in cls.PROFILE_MULTIPLIERS:
            raise ValueError(
                f"Unknown preference profile {profile!r}; expected one of {sorted(cls.PROFILE_MULTIPLIERS)}"
            )

        def cats(key: str) -> tuple[ConsequenceCategory, ...]:
            return tuple(parse_category(c) for c in data.get(key, ()) or ())

        max_int = data.get("max_interruptions_per_task")
        return cls(
            profile=profile,
            always_ask_categories=cats("always_ask_categories"),
            never_ask_categories=cats("never_ask_categories"),
            block_categories=cats("block_categories"),
            ask_before_irreversible=bool(data.get("ask_before_irreversible", False)),
            ask_before_external=bool(data.get("ask_before_external", False)),
            allow_low_risk_autonomy=bool(data.get("allow_low_risk_autonomy", False)),
            low_risk_threshold=float(data.get("low_risk_threshold", 0.15)),
            max_interruptions_per_task=int(max_int) if max_int is not None else None,
        )
