"""Health, policies, scenarios, reason codes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

import agentpause
from agentpause import CATEGORY_PRIORS, ModelParameters, available_policies
from agentpause.explain.reasons import PHRASES
from agentpause_sim import list_scenarios, load_scenario, metric_catalog

from ..deps import AppSettings

router = APIRouter(tags=["meta"])


@router.get("/health", summary="Service health")
def health(settings: AppSettings) -> dict[str, Any]:
    return {
        "status": "ok",
        "version": agentpause.__version__,
        "environment": settings.environment,
        "database": settings.database_url.split(":", 1)[0],
        "auth": settings.admin_token is not None,
        "simulated_actions_only": True,
    }


@router.get("/policies", summary="Available intervention policies")
def policies() -> list[dict[str, Any]]:
    return available_policies()


@router.get("/model", summary="Default model parameters and category priors (all documented assumptions)")
def model() -> dict[str, Any]:
    return {
        "parameters": ModelParameters().to_dict(),
        "category_priors": {
            c.value: {
                "severity": p.severity,
                "recoverability": p.recoverability,
                "external": p.external,
                "description": p.description,
            }
            for c, p in CATEGORY_PRIORS.items()
        },
        "reason_codes": {code.value: text for code, text in PHRASES.items()},
        "metrics": metric_catalog(),
    }


@router.get("/scenarios", summary="Bundled simulated scenarios")
def scenarios() -> list[dict[str, Any]]:
    return [s.summary() for s in list_scenarios()]


@router.get("/scenarios/{scenario_id}", summary="Scenario definition")
def scenario(scenario_id: str) -> dict[str, Any]:
    try:
        return load_scenario(scenario_id).to_dict()
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
