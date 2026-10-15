"""Sessions, the simulated agent loop, human responses, external agent actions, live events."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from ..db import Database
from ..deps import Admin, DbSession, get_database
from ..models import SessionRow
from ..schemas.api import (
    ActionOut,
    ActionRequest,
    InterventionRequest,
    SessionCreate,
    SessionList,
    SessionOut,
    StepOut,
    StepRequest,
)
from ..schemas.common import DecisionOut, EventOut
from ..services.common import present_decision
from ..services.sessions import SessionService

router = APIRouter(tags=["sessions"])


@router.post("/session", response_model=SessionOut, status_code=201, summary="Create a session")
def create_session(req: SessionCreate, db: DbSession) -> SessionOut:
    """Create a **demo/study** session (a simulated agent works through a scenario) or an
    **api** session (your own agent submits actions with `POST /api/v1/action`).

    Study sessions are normally created via `POST /api/v1/study/sessions`, which applies the
    participant's counterbalanced plan.
    """
    service = SessionService(db)
    return service.to_out(service.create(req))


@router.get("/session/{session_id}", response_model=SessionOut, summary="Session state and timeline")
def get_session(session_id: str, db: DbSession) -> SessionOut:
    service = SessionService(db)
    return service.to_out(service.get(session_id))


@router.get("/session/{session_id}/events", response_model=list[EventOut], summary="Session events")
def session_events(session_id: str, db: DbSession, since: int = Query(default=-1, ge=-1)) -> list[EventOut]:
    service = SessionService(db)
    row = service.get(session_id)
    return [service.event_out(row, e) for e in service.events(row, since)]


@router.post("/session/{session_id}/step", response_model=StepOut, summary="Advance the simulated agent")
def step_session(session_id: str, db: DbSession, req: StepRequest | None = None) -> StepOut:
    """Let the simulated agent propose its next action. AgentPause decides; CONTINUE/DEFER
    execute (simulated), CLARIFY/ASK_HUMAN/BLOCK open an intervention card.
    `until="intervention"` keeps stepping until a card opens or the task ends."""
    service = SessionService(db)
    row = service.get(session_id)
    events, decision, card = service.step(row, (req or StepRequest()).until)
    presented = present_decision(decision, row.explanation_mode) if row.mode == "study" else decision
    return StepOut(
        session=service.to_out(row),
        events=[service.event_out(row, e) for e in events],
        decision=DecisionOut(**presented) if presented else None,
        card=service.to_out(row).pending if card else None,
    )


@router.post("/intervention", response_model=StepOut, summary="Respond to an intervention")
def respond(req: InterventionRequest, db: DbSession) -> StepOut:
    """Record the human's response: `approve`, `edit`, `reject`, `answer` (clarifications, with
    `answers`), `takeover`/`override` (after BLOCK), `cancel_task`, or `ask_why` (no state change)."""
    service = SessionService(db)
    row = service.get(req.session_id)
    events, decision = service.respond(row, req.response, req.answers, req.intervention_id)
    presented = present_decision(decision, row.explanation_mode) if row.mode == "study" else decision
    return StepOut(
        session=service.to_out(row),
        events=[service.event_out(row, e) for e in events],
        decision=DecisionOut(**presented) if presented else None,
        card=None,
    )


@router.post("/action", response_model=ActionOut, summary="Submit an action from your own agent")
def submit_action(req: ActionRequest, db: DbSession) -> ActionOut:
    """For **api** sessions. If the decision interrupts, the session waits for
    `POST /api/v1/intervention` with the human's response."""
    service = SessionService(db)
    row = service.get(req.session_id)
    decision, intervention_id, _ = service.action(row, req.context)
    return ActionOut(
        decision=DecisionOut(**decision.to_dict()), intervention_id=intervention_id, session=service.to_out(row)
    )


@router.get("/sessions", response_model=SessionList, summary="List sessions", dependencies=[Admin])
def list_sessions(
    db: DbSession,
    mode: str | None = None,
    scenario: str | None = None,
    policy: str | None = None,
    participant: str | None = None,
    status: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> SessionList:
    stmt = select(SessionRow)
    if mode:
        stmt = stmt.where(SessionRow.mode == mode)
    if scenario:
        stmt = stmt.where(SessionRow.scenario_id == scenario)
    if policy:
        stmt = stmt.where(SessionRow.policy == policy)
    if participant:
        stmt = stmt.where(SessionRow.participant_code == participant)
    if status:
        stmt = stmt.where(SessionRow.status == status)
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = db.scalars(stmt.order_by(SessionRow.created_at.desc()).offset(offset).limit(limit))
    service = SessionService(db)
    return SessionList(total=total, offset=offset, limit=limit, items=[service.to_out(r) for r in rows])


@router.delete(
    "/session/{session_id}", status_code=204, summary="Delete a session and its events", dependencies=[Admin]
)
def delete_session(session_id: str, db: DbSession) -> None:
    row = SessionService(db).get(session_id)
    db.delete(row)
    db.commit()


@router.get("/session/{session_id}/stream", summary="Live events (Server-Sent Events)")
async def stream(
    session_id: str,
    request: Request,
    database: Annotated[Database, Depends(get_database)],
    since: int = Query(default=-1, ge=-1),
) -> StreamingResponse:
    """Streams new events as `text/event-stream` until the session ends or the client disconnects."""
    with database.sessionmaker() as db:
        SessionService(db).get(session_id)

    async def generate() -> AsyncIterator[str]:
        last = since
        idle = 0
        while True:
            if await request.is_disconnected():
                return
            with database.sessionmaker() as db:
                service = SessionService(db)
                row = service.get(session_id)
                new = service.events(row, last)
                for event in new:
                    last = event.seq
                    yield f"id: {event.seq}\nevent: {event.type}\ndata: {json.dumps(service.event_out(row, event).model_dump())}\n\n"
                finished = row.status in ("completed", "cancelled")
            if finished and not new:
                yield "event: end\ndata: {}\n\n"
                return
            idle = 0 if new else idle + 1
            if idle and idle % 30 == 0:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
