"""Study mode: configuration, participants, counterbalanced sessions, questionnaires, export."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from agentpause_sim import rows_to_csv

from ..deps import Admin, AppSettings, DbSession
from ..schemas.api import (
    ParticipantOut,
    ParticipantUpdate,
    QuestionnaireIn,
    QuestionnaireOut,
    SessionCreate,
    SessionOut,
    StudyConfig,
)
from ..services.sessions import SessionService
from ..services.study import StudyService

router = APIRouter(prefix="/study", tags=["study"])


def _service(db: DbSession, settings: AppSettings) -> StudyService:
    return StudyService(db, settings.instruments_local_dir)


Study = Annotated[StudyService, Depends(_service)]


class StudySessionRequest(BaseModel):
    participant_code: str
    block: int


@router.get("/config", response_model=StudyConfig, summary="Active study configuration")
def get_config(service: Study) -> StudyConfig:
    return service.config()


@router.put("/config", response_model=StudyConfig, summary="Update the study configuration", dependencies=[Admin])
def put_config(config: StudyConfig, service: Study) -> StudyConfig:
    return service.update_config(config)


@router.post("/participants", response_model=ParticipantOut, status_code=201, summary="Enrol a participant")
def create_participant(service: Study) -> ParticipantOut:
    """Generates a random pseudonymous code and a counterbalanced plan (practice block, then one
    block per condition) and assigns an explanation condition."""
    return service.participant_out(service.create_participant())


@router.get("/participants/{code}", response_model=ParticipantOut, summary="Participant plan and progress")
def get_participant(code: str, service: Study) -> ParticipantOut:
    return service.participant_out(service.participant(code))


@router.patch("/participants/{code}", response_model=ParticipantOut, summary="Record consent or completion")
def update_participant(code: str, update: ParticipantUpdate, db: DbSession, service: Study) -> ParticipantOut:
    row = service.participant(code)
    if update.consented is not None:
        row.consented = update.consented
    if update.completed is not None:
        row.completed = update.completed
    db.commit()
    return service.participant_out(row)


@router.post("/sessions", response_model=SessionOut, status_code=201, summary="Start the session for a plan block")
def start_block(req: StudySessionRequest, db: DbSession, service: Study) -> SessionOut:
    participant, block = service.block(req.participant_code, req.block)
    sessions = SessionService(db)
    row = sessions.create(
        SessionCreate(mode="study", participant_code=participant.code, block=req.block, condition=block["policy"]),
        plan_block=block,
        explanation_mode=participant.explanation_mode,
    )
    return sessions.to_out(row)


@router.get("/instruments", summary="Questionnaire instruments (definitions, licensing, readiness)")
def instruments(service: Study) -> list[dict[str, Any]]:
    return list(service.instruments().values())


@router.post("/responses", response_model=QuestionnaireOut, status_code=201, summary="Submit questionnaire responses")
def submit_responses(req: QuestionnaireIn, service: Study) -> QuestionnaireOut:
    instrument = service.instruments().get(req.instrument_id)
    if instrument is not None and not instrument["ready"]:
        raise HTTPException(status_code=409, detail=f"Instrument {req.instrument_id} has no item text configured")
    row = service.record_response(req)
    return QuestionnaireOut(id=row.id, instrument_id=row.instrument_id, score=row.score)


@router.get("/export", summary="Export questionnaire data", dependencies=[Admin])
def export(service: Study, format: Literal["csv", "json"] = "csv") -> Response:
    rows = service.export_rows()
    if format == "json":
        return Response(json.dumps(rows, indent=2), media_type="application/json")
    flat = [{**r, "responses": json.dumps(r["responses"]), "score": json.dumps(r["score"])} for r in rows]
    columns = (
        "participant_code",
        "participant_number",
        "explanation_mode",
        "block",
        "policy",
        "session_id",
        "instrument_id",
        "responses",
        "score",
        "created_at",
    )
    return Response(
        rows_to_csv(flat, columns=columns),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="agentpause-study.csv"'},
    )
