"""Gate any Python tool function with AgentPause."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from ..decision import Decision
from ..types import ResponseType

if TYPE_CHECKING:
    from ..session import AgentPause

F = TypeVar("F", bound=Callable[..., Any])


class InterventionRequired(RuntimeError):
    """Raised when AgentPause wants the human involved and no ``on_ask`` handler was given.

    Catch it in your agent loop, show ``err.decision`` to the user (questions, explanation),
    call ``pause.respond(err.decision, ...)``, then retry or skip the tool call.
    """

    def __init__(self, decision: Decision) -> None:
        super().__init__(decision.explanation or decision.decision.value)
        self.decision = decision


class ActionBlocked(RuntimeError):
    def __init__(self, decision: Decision) -> None:
        super().__init__(decision.explanation or "Blocked by AgentPause")
        self.decision = decision


class ActionRejected(RuntimeError):
    def __init__(self, decision: Decision, response: ResponseType) -> None:
        super().__init__(f"The user responded '{response.value}' to {decision.action}")
        self.decision = decision
        self.response = response


def guard(
    pause: AgentPause,
    *,
    action: str | None = None,
    signals: dict[str, Any] | None = None,
    context_fn: Callable[..., dict[str, Any]] | None = None,
    on_ask: Callable[[Decision], ResponseType | str | bool] | None = None,
) -> Callable[[F], F]:
    """Decorate a tool so each call is evaluated by AgentPause first.

    * ``signals``: static signals (e.g. ``{"consequence": "external_communication"}``).
    * ``context_fn(*args, **kwargs)``: dynamic signals computed from the call arguments.
      Return metadata only (e.g. ``{"agent_confidence": 0.7}``), never secrets or message bodies.
    * ``on_ask(decision)``: shows the intervention to the user and returns their response
      (``"approve"``, ``"reject"``, …, or ``True``/``False``). If omitted,
      :class:`InterventionRequired` is raised.

    CONTINUE and DEFER run the tool. BLOCK raises :class:`ActionBlocked`.
    """
    static = dict(signals or {})

    def decorator(fn: F) -> F:
        name = action or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            dynamic = context_fn(*args, **kwargs) if context_fn else {}
            decision = pause.evaluate(name, **{**static, **dynamic})
            if decision.should_proceed:
                return fn(*args, **kwargs)
            if decision.is_blocked:
                raise ActionBlocked(decision)
            if on_ask is None:
                raise InterventionRequired(decision)
            raw = on_ask(decision)
            if isinstance(raw, bool):
                response = ResponseType.APPROVE if raw else ResponseType.REJECT
            else:
                response = ResponseType(raw)
            pause.respond(decision, response)
            if response in (ResponseType.APPROVE, ResponseType.EDIT, ResponseType.ANSWER, ResponseType.OVERRIDE):
                return fn(*args, **kwargs)
            raise ActionRejected(decision, response)

        return wrapper  # type: ignore[return-value]

    return decorator
