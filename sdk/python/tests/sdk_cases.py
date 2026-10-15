"""Reusable action contexts for the SDK tests."""

from __future__ import annotations

from agentpause import ActionContext, Assumption, AssumptionKind, ConsequenceCategory, PlannedAction


def low_risk(**overrides: object) -> ActionContext:
    values: dict[str, object] = {
        "action": "search_flights",
        "category": ConsequenceCategory.READ_ONLY,
        "agent_confidence": 0.95,
        "intent_confidence": 0.95,
        "at_breakpoint": True,
        "cognitive_load": 0.3,
    }
    values.update(overrides)
    return ActionContext(**values)  # type: ignore[arg-type]


def risky(**overrides: object) -> ActionContext:
    values: dict[str, object] = {
        "action": "purchase_ticket",
        "description": "Purchase a non-refundable ticket",
        "category": ConsequenceCategory.FINANCIAL_TRANSACTION,
        "severity": 0.8,
        "recoverability": 0.05,
        "agent_confidence": 0.7,
        "intent_confidence": 0.75,
        "at_breakpoint": False,
        "cognitive_load": 0.4,
    }
    values.update(overrides)
    return ActionContext(**values)  # type: ignore[arg-type]


def timing_task(step: int, *, introduce: bool = False) -> ActionContext:
    """A task where an input assumption appears mid-task (step 1, not a breakpoint).

    Steps: 0 search (bp) · 1 select (mid-task, introduces 'seat') · 2 details (bp)
    · 3 purchase (irreversible, depends on 'seat') · 4 wrap-up (bp).
    """
    plan = (
        PlannedAction(
            step=2,
            action="enter_details",
            category=ConsequenceCategory.DATA_ENTRY,
            at_breakpoint=True,
            depends_on=("seat",),
        ),
        PlannedAction(
            step=3,
            action="purchase",
            category=ConsequenceCategory.FINANCIAL_TRANSACTION,
            severity=0.8,
            recoverability=0.05,
            at_breakpoint=False,
            depends_on=("seat",),
        ),
        PlannedAction(step=4, action="wrap_up", category=ConsequenceCategory.INTERNAL_DRAFT, at_breakpoint=True),
    )
    assumption = Assumption("seat", "you want an aisle seat", 0.75, AssumptionKind.INPUT, ("aisle", "window"), "aisle")
    if step <= 1:
        current = PlannedAction(
            step=step,
            action="select_flight",
            category=ConsequenceCategory.INTERNAL_DRAFT,
            severity=0.1,
            recoverability=1.0,
            at_breakpoint=False,
        )
    else:
        current = next(p for p in plan if p.step == step)
    return ActionContext(
        action=current.action,
        category=current.category,
        severity=current.severity,
        recoverability=current.recoverability,
        agent_confidence=0.95,
        intent_confidence=0.98,
        at_breakpoint=current.at_breakpoint,
        cognitive_load=0.5,
        assumptions=(assumption,) if introduce else (),
        depends_on=current.depends_on,
        plan=tuple(p for p in plan if p.step > step),
        step=step,
    )
