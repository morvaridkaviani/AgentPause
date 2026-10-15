"""The high-level SDK: one ``AgentPause`` object per agent task."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from .context import ActionContext, Assumption, PlannedAction, UserPreferences
from .decision import Decision, DeferredQuestion, TimingExplanation
from .explain import Explainer
from .explain.timing import explain_timing
from .model import ModelParameters
from .policies import InterventionPolicy, create_policy
from .state import SessionState
from .types import AssumptionKind, ResponseType

F = TypeVar("F", bound=Callable[..., Any])


class AgentPause:
    """Decide when an AI agent should continue, clarify, ask, defer, or stop.

    >>> pause = AgentPause(policy="adaptive")
    >>> decision = pause.evaluate(
    ...     action="send_email",
    ...     consequence="external_communication",
    ...     reversible=False,
    ...     intent_confidence=0.72,
    ...     agent_confidence=0.86,
    ... )
    >>> decision.should_ask
    True
    >>> decision.decision.value
    'ASK_HUMAN'

    Keep one instance per task. The instance remembers recent interruptions (habituation),
    open assumptions, scheduled (deferred) questions, and the user's responses.
    """

    def __init__(
        self,
        policy: str | InterventionPolicy = "adaptive",
        *,
        preferences: UserPreferences | dict[str, Any] | None = None,
        parameters: ModelParameters | dict[str, Any] | None = None,
        explain: str = "full",
        state: SessionState | None = None,
        **policy_config: Any,
    ) -> None:
        if isinstance(policy, InterventionPolicy):
            self.policy = policy
        else:
            self.policy = create_policy(policy, parameters=parameters, preferences=preferences, **policy_config)
        self.explainer = Explainer(explain)
        self.state = state or SessionState()
        self.decisions: list[Decision] = []
        self._contexts: dict[int, ActionContext] = {}

    # ---- core loop --------------------------------------------------------------------------
    def evaluate(
        self,
        action: str | ActionContext | None = None,
        *,
        context: ActionContext | None = None,
        record: bool = True,
        **signals: Any,
    ) -> Decision:
        """Evaluate a proposed action and return a :class:`Decision`.

        Pass either an :class:`ActionContext` or keyword signals (``consequence``,
        ``reversible``, ``recoverability``, ``severity``, ``agent_confidence``,
        ``intent_confidence``, ``task_progress``, ``at_breakpoint``, ``cognitive_load``,
        ``assumptions``, ``depends_on``, ``plan``, ``description``, ...).

        With ``record=False`` the decision is not added to the session (a "what if" query).
        """
        ctx = self._build_context(action, context, signals)
        started = time.perf_counter()
        decision = self.policy.decide(ctx, self.state)
        self.explainer.enrich(decision, ctx, self.state, self.policy)
        decision.latency_ms = (time.perf_counter() - started) * 1000.0
        if record:
            self.state.record_decision(ctx, decision)
            self.decisions.append(decision)
            self._contexts[id(decision)] = ctx
        return decision

    def respond(
        self,
        decision: Decision,
        response: ResponseType | str,
        *,
        answers: dict[str, str] | None = None,
    ) -> None:
        """Record the human's response to an intervention.

        ``answers`` maps assumption ids to the user's answer for clarification questions.
        An answer equal to the agent's assumed value counts as a confirmation; anything else
        counts as a correction.
        """
        self.state.record_response(
            decision,
            ResponseType(response),
            answers=answers,
            habituation_discount=self.policy.parameters.habituation_effect,
        )

    def explain_timing(self, decision: Decision) -> TimingExplanation:
        """Return "why now / why not earlier / why not later" for a decision."""
        if decision.timing is not None:
            return decision.timing
        ctx = self._contexts.get(id(decision)) or ActionContext(action=decision.action, step=decision.step)
        prior = SessionState.from_dict(self.state.to_dict())
        prior.history = [h for h in prior.history if h.step < decision.step]
        return explain_timing(decision, ctx, prior, self.policy)

    # ---- task structure ---------------------------------------------------------------------
    def declare_assumption(
        self,
        id: str,
        description: str,
        confidence: float,
        *,
        kind: AssumptionKind | str = AssumptionKind.INPUT,
        options: Iterable[str] = (),
        agent_value: str | None = None,
    ) -> Assumption:
        """Declare an interpretation of the user's intent that later actions depend on."""
        assumption = Assumption(
            id=id,
            description=description,
            confidence=float(confidence),
            kind=AssumptionKind(kind),
            options=tuple(options),
            agent_value=agent_value,
        )
        if id not in self.state.assumptions:
            self.state.assumption_introduced[id] = self.state.step
        self.state.assumptions[id] = assumption
        return assumption

    def set_plan(self, plan: Iterable[PlannedAction | dict[str, Any]]) -> None:
        """Tell AgentPause which actions are coming. This enables timing lookahead (DEFER)."""
        self.state.plan = [p if isinstance(p, PlannedAction) else PlannedAction.from_dict(p) for p in plan]

    def resolve_assumption(self, assumption_id: str, *, correct: bool = True) -> None:
        self.state.resolve(assumption_id, "confirmed" if correct else "corrected")

    @property
    def pending_questions(self) -> list[DeferredQuestion]:
        """Questions that were deferred and have not been asked yet."""
        return list(self.state.pending)

    def reset(self) -> None:
        self.state = SessionState()
        self.decisions.clear()
        self._contexts.clear()

    # ---- persistence ------------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {"policy": self.policy.describe(), "explain": self.explainer.level, "state": self.state.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentPause:
        policy_info = data["policy"]
        registry_name = policy_info.get("policy") or policy_info["name"]
        pause = cls(
            registry_name,
            parameters=policy_info.get("parameters"),
            preferences=policy_info.get("preferences"),
            explain=data.get("explain", "full"),
            state=SessionState.from_dict(data.get("state")),
            **_constructor_config({**policy_info, "name": registry_name}),
        )
        if policy_info["name"] != registry_name:
            pause.policy.name = policy_info["name"]  # restore the display label
        return pause

    # ---- integrations -----------------------------------------------------------------------
    def guard(self, **kwargs: Any) -> Callable[[F], F]:
        """Decorator that gates a tool function. See :func:`agentpause.integrations.guard`."""
        from .integrations.guard import guard

        return guard(self, **kwargs)

    # ---- internals --------------------------------------------------------------------------
    def _build_context(
        self, action: str | ActionContext | None, context: ActionContext | None, signals: dict[str, Any]
    ) -> ActionContext:
        if isinstance(action, ActionContext):
            context, action = action, None
        if context is not None:
            if signals:
                raise TypeError("Pass either an ActionContext or keyword signals, not both")
            return context
        if not action:
            raise TypeError("evaluate() needs an action name or an ActionContext")
        return ActionContext.build(str(action), **signals)


def _constructor_config(policy_info: dict[str, Any]) -> dict[str, Any]:
    """Recover keyword arguments for re-creating a policy from ``describe()`` output."""
    name = policy_info["name"]
    config = dict(policy_info.get("config") or {})
    config.pop("training", None)  # metadata of the learned policy, not a constructor argument
    if name == "myopic_voi":
        config.pop("timing", None)  # fixed to False by the class
    if name == "user_customized":
        base_config = dict(config.pop("base_config", {}) or {})
        base_config.pop("training", None)
        if config.get("base") == "myopic_voi":
            base_config.pop("timing", None)
        config.update(base_config)
    return config
