"""Helpers shared by services: policy construction, risk levels, presentation rules."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from agentpause import InterventionPolicy, ModelParameters, create_policy
from agentpause.model import consequence_risk

from ..schemas.common import PolicySpecIn, PreferencesIn

_PARAMS = ModelParameters()

# Fields that reveal simulator ground truth. They are stored for analysis but never sent to
# study participants.
GROUND_TRUTH_KEYS = {"necessary", "error_present", "shown_errors", "harm", "wrong_basis"}

PLACEBIC_EXPLANATION = "AgentPause paused here because it needs your input before continuing."


def normalize_spec(spec: PolicySpecIn | str, preferences: PreferencesIn | None = None) -> dict[str, Any]:
    if isinstance(spec, str):
        spec = PolicySpecIn(name=spec)
    prefs = spec.preferences or preferences
    return {
        "name": spec.name,
        "config": dict(spec.config),
        "preferences": prefs.model_dump() if prefs else None,
        "parameters": dict(spec.parameters),
        "label": spec.label,
    }


def build_policy(spec: dict[str, Any]) -> InterventionPolicy:
    try:
        policy = create_policy(
            spec["name"],
            parameters=spec.get("parameters") or None,
            preferences=spec.get("preferences"),
            **spec.get("config", {}),
        )
    except (ValueError, TypeError, FileNotFoundError) as err:
        raise HTTPException(status_code=422, detail=f"Invalid policy specification: {err}") from err
    if spec.get("label"):
        policy.name = spec["label"]
    return policy


def risk_level(severity: float | None, recoverability: float | None) -> str:
    if severity is None or recoverability is None:
        return "unknown"
    risk = consequence_risk(severity, recoverability, _PARAMS)
    if risk < 0.1:
        return "low"
    if risk < 0.35:
        return "medium"
    return "high"


def present_decision(decision: dict[str, Any] | None, mode: str) -> dict[str, Any] | None:
    """Apply a study explanation condition to a decision before it is shown.

    * ``full``: everything (factors, reason codes, feature and timing counterfactuals).
    * ``factors``: no timing counterfactuals ("why not earlier/later").
    * ``placebo``: a content-free justification only (Eiband et al. 2019 control condition).
    * ``none``: no explanation at all.
    """
    if decision is None or mode == "full":
        return decision
    d = copy.deepcopy(decision)
    if mode == "factors":
        d["timing"] = None
        d["counterfactuals"] = [c for c in d.get("counterfactuals", []) if c.get("kind") != "timing"]
        return d
    d["factors"] = []
    d["counterfactuals"] = []
    d["timing"] = None
    d["reason_codes"] = []
    d["item_timings"] = []
    d["terms"] = {}
    d["explanation"] = PLACEBIC_EXPLANATION if mode == "placebo" and decision.get("should_ask") else ""
    return d


def strip_ground_truth(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: strip_ground_truth(v) for k, v in value.items() if k not in GROUND_TRUTH_KEYS}
    if isinstance(value, list):
        return [strip_ground_truth(v) for v in value]
    return value


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
