"""Event log, metrics, experiments, quick comparisons, exports."""

from __future__ import annotations

import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select

from agentpause_sim import rows_to_csv

from ..db import Database
from ..deps import Admin, AppSettings, DbSession, get_database
from ..models import EventRow, SessionRow
from ..schemas.api import CompareOut, CompareRequest, EventList, ExperimentCreate, ExperimentOut, MetricsOut
from ..services.experiments import ExperimentService, compare
from ..services.metrics import compute_metrics, event_query
from ..services.sessions import SessionService

router = APIRouter(tags=["research"])

EVENT_COLUMNS = (
    "id",
    "seq",
    "session_id",
    "created_at",
    "type",
    "mode",
    "scenario_id",
    "policy",
    "participant_code",
    "condition",
    "step_index",
    "action",
    "decision",
    "score",
    "intervention",
    "risk_level",
    "user_response",
    "latency_ms",
)

DatabaseDep = Annotated[Database, Depends(get_database)]


def _experiments(db: DbSession, database: DatabaseDep, settings: AppSettings) -> ExperimentService:
    return ExperimentService(db, database.sessionmaker, settings.max_experiment_episodes)


Experiments = Annotated[ExperimentService, Depends(_experiments)]


@router.get("/events", response_model=EventList, summary="Event log (all sessions)", dependencies=[Admin])
def events(
    db: DbSession,
    session_id: str | None = None,
    mode: str | None = None,
    scenario: str | None = None,
    policy: str | None = None,
    participant: str | None = None,
    decision: str | None = None,
    risk: Literal["low", "medium", "high"] | None = None,
    type: str | None = None,
    interventions_only: bool = False,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    format: Literal["json", "csv"] = "json",
) -> EventList | Response:
    """Filterable log of every proposal, decision, response, and execution. `format=csv` exports
    all matching rows (no PII: participants appear only as pseudonymous codes)."""
    stmt = event_query(
        db,
        session_id=session_id,
        mode=mode,
        scenario=scenario,
        policy=policy,
        participant=participant,
        decision=decision,
        risk=risk,
        type_=type,
        interventions_only=interventions_only,
    )
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    stmt = stmt.order_by(EventRow.id.desc())
    rows = list(db.scalars(stmt.offset(offset).limit(limit) if format == "json" else stmt))
    sessions = {s.id: s for s in db.scalars(select(SessionRow).where(SessionRow.id.in_({r.session_id for r in rows})))}
    service = SessionService(db)
    items = [service.event_out(sessions[r.session_id], r) for r in rows]
    if format == "csv":
        body = rows_to_csv([i.model_dump() for i in items], columns=EVENT_COLUMNS)
        return Response(
            body, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="agentpause-events.csv"'}
        )
    return EventList(total=total, offset=offset, limit=limit, items=items)


@router.get("/metrics", response_model=MetricsOut, summary="Aggregated research metrics and chart data")
def metrics(
    db: DbSession,
    source: Literal["experiment", "sessions"] = "experiment",
    experiment_id: str | None = None,
    scenario: str | None = None,
    policy: str | None = None,
    participant: str | None = None,
    condition: str | None = None,
    risk: Literal["low", "medium", "high"] | None = None,
    mode: Literal["demo", "study"] | None = None,
) -> MetricsOut:
    """`source=experiment` aggregates a stored simulation experiment (default: latest).
    `source=sessions` aggregates completed interactive sessions (real human responses)."""
    return MetricsOut(
        **compute_metrics(
            db,
            source=source,
            experiment_id=experiment_id,
            scenario=scenario,
            policy=policy,
            participant=participant,
            condition=condition,
            risk=risk,
            mode=mode,
        )
    )


@router.post("/compare", response_model=CompareOut, summary="Quick policy comparison (simulated, not stored)")
def quick_compare(req: CompareRequest, settings: AppSettings) -> CompareOut:
    return CompareOut(**compare(req, settings.max_compare_episodes))


@router.post("/experiments", response_model=ExperimentOut, status_code=201, summary="Create and run an experiment")
def create_experiment(
    req: ExperimentCreate,
    service: Experiments,
    wait: bool = Query(default=False, description="Run synchronously (small experiments, tests)"),
) -> ExperimentOut:
    """Runs in a background thread; poll `GET /api/v1/experiments/{id}` for progress."""
    return service.to_out(service.create(req, wait=wait))


@router.get("/experiments", response_model=list[ExperimentOut], summary="List experiments")
def list_experiments(service: Experiments, limit: int = Query(default=50, ge=1, le=500)) -> list[ExperimentOut]:
    return [service.to_out(r) for r in service.recent(limit)]


@router.get("/experiments/{experiment_id}", response_model=ExperimentOut, summary="Experiment status and results")
def get_experiment(experiment_id: str, service: Experiments) -> ExperimentOut:
    return service.to_out(service.get(experiment_id))


@router.get("/experiments/{experiment_id}/export", summary="Export experiment data (CSV or JSON)", dependencies=[Admin])
def export_experiment(
    experiment_id: str,
    service: Experiments,
    table: Literal["records", "episodes", "summary"] = "records",
    format: Literal["csv", "json"] = "csv",
) -> Response:
    row = service.get(experiment_id)
    if table == "summary":
        return Response(
            json.dumps({"config": row.config, "result": row.result}, indent=2), media_type="application/json"
        )
    data = service.records(row.id) if table == "records" else service.episodes(row.id)
    name = f"agentpause-{row.name}-{table}".replace(" ", "_")
    if format == "json":
        return Response(
            json.dumps(data),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{name}.json"'},
        )
    return Response(
        rows_to_csv(data), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}.csv"'}
    )


@router.delete("/experiments/{experiment_id}", status_code=204, summary="Delete an experiment", dependencies=[Admin])
def delete_experiment(experiment_id: str, service: Experiments) -> None:
    service.delete(experiment_id)
