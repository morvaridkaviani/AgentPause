"""Batch simulation experiments (background thread) and quick synchronous comparisons."""

from __future__ import annotations

import sys
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker

from agentpause_sim import ConditionSpec, ExperimentConfig, build_policy, run_episode, run_experiment
from agentpause_sim.metrics import aggregate, paired_comparison, summarize

from ..models import ExperimentEpisodeRow, ExperimentRecordRow, ExperimentRow
from ..schemas.api import CompareRequest, ExperimentCreate, ExperimentOut
from .common import iso, normalize_spec, risk_level

NOTE = "SIMULATED RESULTS. Not evaluated with human participants."


def _config_dict(req: ExperimentCreate) -> dict[str, Any]:
    policies = []
    for spec in req.policies:
        normalized = normalize_spec(spec)
        policies.append({k: v for k, v in normalized.items() if v not in (None, {}, [])} | {"name": normalized["name"]})
    return {
        "name": req.name,
        "description": req.description,
        "scenarios": req.scenarios,
        "policies": policies,
        "episodes": req.episodes,
        "seed": req.seed,
        "conditions": [c.model_dump() for c in req.conditions] or [{"name": "default"}],
        "explain": "none",
        "bootstrap": req.bootstrap,
    }


def parse_config(data: dict[str, Any]) -> ExperimentConfig:
    try:
        return ExperimentConfig.from_dict(data)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {err}") from err
    except (ValueError, TypeError) as err:
        raise HTTPException(status_code=422, detail=str(err)) from err


class ExperimentService:
    def __init__(self, db: Session, sessions: sessionmaker[Session], max_episodes: int) -> None:
        self.db = db
        self.sessions = sessions
        self.max_episodes = max_episodes

    def create(self, req: ExperimentCreate, *, wait: bool = False) -> ExperimentRow:
        data = _config_dict(req)
        config = parse_config(data)
        # Validate every policy spec up front, so the request fails now rather than in the background thread.
        for spec in config.policies:
            try:
                build_policy(spec, config.conditions[0])
            except (ValueError, TypeError, FileNotFoundError) as err:
                raise HTTPException(status_code=422, detail=f"Invalid policy {spec.name!r}: {err}") from err
        if config.total_episodes > self.max_episodes:
            raise HTTPException(
                status_code=422,
                detail=f"{config.total_episodes} episodes exceeds the server limit of {self.max_episodes}. "
                "Reduce episodes, policies, or scenarios, or run experiments/ scripts locally.",
            )
        row = ExperimentRow(
            id=str(uuid.uuid4()),
            name=req.name,
            status="queued",
            config=config.to_dict(),
            progress_total=config.total_episodes,
        )
        self.db.add(row)
        self.db.commit()
        # WebAssembly builds (the in-browser demo) cannot start threads, so they run inline.
        if wait or sys.platform == "emscripten":
            execute(row.id, self.sessions)
            self.db.refresh(row)
        else:
            threading.Thread(target=execute, args=(row.id, self.sessions), daemon=True).start()
        return row

    def get(self, experiment_id: str) -> ExperimentRow:
        row = self.db.get(ExperimentRow, experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
        return row

    def recent(self, limit: int = 50) -> list[ExperimentRow]:
        return list(self.db.scalars(select(ExperimentRow).order_by(ExperimentRow.created_at.desc()).limit(limit)))

    def delete(self, experiment_id: str) -> None:
        row = self.get(experiment_id)
        self.db.execute(delete(ExperimentRecordRow).where(ExperimentRecordRow.experiment_id == row.id))
        self.db.execute(delete(ExperimentEpisodeRow).where(ExperimentEpisodeRow.experiment_id == row.id))
        self.db.delete(row)
        self.db.commit()

    def records(self, experiment_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(ExperimentRecordRow.data)
            .where(ExperimentRecordRow.experiment_id == experiment_id)
            .order_by(ExperimentRecordRow.id)
        )
        return [dict(d) for d in self.db.scalars(stmt)]

    def episodes(self, experiment_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(ExperimentEpisodeRow.data)
            .where(ExperimentEpisodeRow.experiment_id == experiment_id)
            .order_by(ExperimentEpisodeRow.id)
        )
        return [dict(d) for d in self.db.scalars(stmt)]

    @staticmethod
    def to_out(row: ExperimentRow) -> ExperimentOut:
        return ExperimentOut(
            id=row.id,
            name=row.name,
            status=row.status,
            created_at=iso(row.created_at) or "",
            finished_at=iso(row.finished_at),
            config=row.config,
            progress={"done": row.progress_done, "total": row.progress_total},
            result=row.result,
            error=row.error,
        )


def execute(experiment_id: str, sessions: sessionmaker[Session]) -> None:
    """Run a stored experiment and persist its results. Safe to call in a background thread."""
    with sessions() as db:
        row = db.get(ExperimentRow, experiment_id)
        if row is None:
            return
        row.status = "running"
        db.commit()
        config = ExperimentConfig.from_dict(row.config)
        last = [0.0]

        def progress(done: int, total: int) -> None:
            now = time.monotonic()
            if done == total or now - last[0] > 0.5:
                last[0] = now
                row.progress_done = done
                db.commit()

        try:
            result = run_experiment(config, progress=progress)
            db.execute(
                insert(ExperimentEpisodeRow),
                [
                    {
                        "experiment_id": row.id,
                        "scenario_id": s.scenario,
                        "policy": s.policy,
                        "condition": s.condition,
                        "episode": s.episode,
                        "data": s.to_dict(),
                    }
                    for s in result.summaries
                ],
            )
            if result.records:
                db.execute(
                    insert(ExperimentRecordRow),
                    [
                        {
                            "experiment_id": row.id,
                            "scenario_id": r["scenario"],
                            "policy": r["policy"],
                            "condition": r["condition"],
                            "decision": r["decision"],
                            "intervention": bool(r["intervention"]),
                            "risk_level": risk_level(r.get("severity"), r.get("recoverability")),
                            "data": r,
                        }
                        for r in result.records
                    ],
                )
            row.result = result.to_dict()
            row.status = "completed"
            row.progress_done = row.progress_total
        except Exception as err:
            row.status = "failed"
            row.error = f"{err}\n{traceback.format_exc(limit=3)}"
        row.finished_at = datetime.now(UTC)
        db.commit()


def compare(
    req: CompareRequest, max_episodes: int, progress: Callable[[int, int], None] | None = None
) -> dict[str, Any]:
    """Run a quick, unpersisted comparison and an example trace per policy."""
    policies = [normalize_spec(p) for p in req.policies]
    data = {
        "name": "quick_compare",
        "scenarios": req.scenarios,
        "policies": [{k: v for k, v in p.items() if v not in (None, {}, [])} | {"name": p["name"]} for p in policies],
        "episodes": req.episodes,
        "seed": req.seed,
        "conditions": [{"name": "default", "user": req.user, "engine": req.engine}],
        "bootstrap": 200,
        "keep_records": False,
    }
    config = parse_config(data)
    if config.total_episodes > max_episodes:
        raise HTTPException(
            status_code=422, detail=f"{config.total_episodes} episodes exceeds the limit of {max_episodes}"
        )
    try:
        result = run_experiment(config, progress=progress)
    except (ValueError, TypeError, FileNotFoundError) as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    trace_scenario = req.trace_scenario or config.scenario_ids()[0]
    traces: dict[str, dict[str, Any]] = {}
    condition = ConditionSpec(name="default", user=req.user, engine=req.engine)
    for spec in config.policies:
        engine = run_episode(trace_scenario, spec, condition, seed=req.seed, episode=req.trace_episode, explain="light")
        steps = engine.scenario.steps
        steps_trace = [
            {
                "step_index": r["step_index"],
                "step_id": r["step_id"],
                "label": steps[r["step_index"]].label,
                "decision": r["decision"],
                "n_questions": r["n_questions"],
                "n_deferred": r["n_deferred"],
                "intervention": r["intervention"],
                "necessary": r["necessary"],
                "error_present": r["error_present"],
                "user_response": r["user_response"],
            }
            for r in engine.state.records
        ]
        traces[spec.key] = {
            "steps": steps_trace,
            "outcome": engine.outcome() | {"summary": summarize(engine.state, len(steps)).to_dict()},
        }
    comparisons = []
    keys = [p.key for p in config.policies]
    if "adaptive" in keys:
        for baseline in keys:
            if baseline != "adaptive":
                comparisons += paired_comparison(
                    result.summaries, baseline=baseline, treatment="adaptive", n_boot=200, seed=req.seed
                )
    return {
        "note": NOTE,
        "episodes": req.episodes,
        "seed": req.seed,
        "aggregates": result.aggregates,
        "by_scenario": aggregate(result.summaries, group_by=("scenario", "policy"), n_boot=0),
        "comparisons": comparisons,
        "traces": traces,
        "trace_scenario": trace_scenario,
    }


__all__ = ["NOTE", "ExperimentService", "compare", "execute", "parse_config"]
