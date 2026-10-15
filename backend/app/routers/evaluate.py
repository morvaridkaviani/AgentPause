"""Stateless evaluation of a single action."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agentpause import ActionContext, AgentPause, SessionState

from ..schemas.api import EvaluateRequest
from ..schemas.common import DecisionOut
from ..services.common import build_policy, normalize_spec

router = APIRouter(tags=["evaluate"])


@router.post(
    "/evaluate",
    response_model=DecisionOut,
    summary="Evaluate one proposed action",
    description=(
        "Returns CONTINUE / CLARIFY / ASK_HUMAN / DEFER / BLOCK with score, reason codes, factors, "
        "counterfactuals, and timing explanations. Nothing is stored."
    ),
)
def evaluate(req: EvaluateRequest) -> DecisionOut:
    policy = build_policy(normalize_spec(req.policy, req.preferences))
    try:
        state = SessionState.from_dict(req.state) if req.state else SessionState()
        context = ActionContext.build(req.context.action, **req.context.to_engine_kwargs())
    except (ValueError, TypeError, KeyError) as err:
        raise HTTPException(status_code=422, detail=f"Invalid context or state: {err}") from err
    pause = AgentPause(policy, explain=req.explain, state=state)
    decision = pause.evaluate(context=context, record=False)
    return DecisionOut(**decision.to_dict())
