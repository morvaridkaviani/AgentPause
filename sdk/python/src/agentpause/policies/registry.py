"""Policy registry: create policies by name, and register new ones."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..context import UserPreferences
from ..model import ModelParameters
from .adaptive import AdaptivePolicy, MyopicVOIPolicy
from .base import InterventionPolicy
from .baselines import (
    AlwaysConfirmPolicy,
    ConfidenceThresholdPolicy,
    FullAutonomyPolicy,
    RuleBasedPolicy,
    ThresholdPolicy,
)
from .customized import UserCustomizedPolicy
from .learned import LearnedPolicy

PolicyFactory = Callable[..., InterventionPolicy]

_REGISTRY: dict[str, PolicyFactory] = {
    "full_autonomy": FullAutonomyPolicy,
    "always_confirm": AlwaysConfirmPolicy,
    "fixed_threshold": ThresholdPolicy,
    "confidence_threshold": ConfidenceThresholdPolicy,
    "rule_based": RuleBasedPolicy,
    "myopic_voi": MyopicVOIPolicy,
    "adaptive": AdaptivePolicy,
    "user_customized": UserCustomizedPolicy,
    "learned": LearnedPolicy,
}

ALIASES: dict[str, str] = {
    "never": "full_autonomy",
    "autonomy": "full_autonomy",
    "always": "always_confirm",
    "threshold": "fixed_threshold",
    "fixed_risk_threshold": "fixed_threshold",
    "confidence": "confidence_threshold",
    "rules": "rule_based",
    "voi": "myopic_voi",
    "agentpause": "adaptive",
    "adaptive_agentpause": "adaptive",
    "customized": "user_customized",
}

# Metadata for UIs and docs. ``core`` marks the four conditions of the planned user study.
POLICY_INFO: dict[str, dict[str, Any]] = {
    "full_autonomy": {
        "label": "Full autonomy",
        "core": True,
        "study_code": "A",
        "origin": "AutoGen human_input_mode=NEVER; OpenHands NeverConfirm",
    },
    "always_confirm": {
        "label": "Always confirm",
        "core": True,
        "study_code": "B",
        "origin": "AutoGen ALWAYS; OpenHands AlwaysConfirm",
    },
    "fixed_threshold": {
        "label": "Fixed risk threshold",
        "core": True,
        "study_code": "C",
        "origin": "OpenHands ConfirmRisky; Mastra classifier ≥ τ",
    },
    "adaptive": {
        "label": "Adaptive (AgentPause)",
        "core": True,
        "study_code": "D",
        "origin": "This project (builds on Horvitz 1999; Iqbal & Bailey; Gulati et al. 2026)",
    },
    "user_customized": {
        "label": "User-customized",
        "core": False,
        "study_code": "E",
        "origin": "Adaptive + user rules (cf. Ask4Help preference conditioning; Yan 2026)",
    },
    "myopic_voi": {
        "label": "Myopic value of asking",
        "core": False,
        "study_code": None,
        "origin": "Ablation in the spirit of Horvitz 1999 / Dong et al. 2026",
    },
    "rule_based": {
        "label": "Rule-based",
        "core": False,
        "study_code": None,
        "origin": "Magentic-UI action guards; ask-or-act rules",
    },
    "confidence_threshold": {
        "label": "Confidence threshold",
        "core": False,
        "study_code": None,
        "origin": "KnowNo-style 'ask when uncertain' (non-conformal); Warp 'Agent decides'",
    },
    "learned": {
        "label": "Learned (experimental)",
        "core": False,
        "study_code": None,
        "origin": "Logistic model on simulated logs; illustrates the plug-in interface",
    },
}


def canonical_name(name: str) -> str:
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    return ALIASES.get(key, key)


def create_policy(
    name: str,
    *,
    parameters: ModelParameters | dict[str, Any] | None = None,
    preferences: UserPreferences | dict[str, Any] | None = None,
    **config: Any,
) -> InterventionPolicy:
    """Create a policy by name.

    >>> create_policy("fixed_threshold", threshold=0.5).name
    'fixed_threshold'
    """
    key = canonical_name(name)
    if key not in _REGISTRY:
        raise ValueError(f"Unknown policy {name!r}. Available: {', '.join(sorted(_REGISTRY))}")
    params = parameters if isinstance(parameters, ModelParameters) else ModelParameters.from_dict(parameters)
    prefs = (
        preferences
        if isinstance(preferences, UserPreferences) or preferences is None
        else UserPreferences.from_dict(preferences)
    )
    policy = _REGISTRY[key](params, prefs, **config)
    policy.registry_key = key  # lets sessions restore the policy even if `name` becomes a display label
    return policy


def register_policy(name: str, factory: PolicyFactory, *, info: dict[str, Any] | None = None) -> None:
    """Register a custom policy so it can be created by name (SDK, API, simulator)."""
    key = canonical_name(name)
    _REGISTRY[key] = factory
    POLICY_INFO[key] = info or {"label": name, "core": False, "study_code": None, "origin": "custom"}


def available_policies() -> list[dict[str, Any]]:
    out = []
    for key, factory in _REGISTRY.items():
        info = POLICY_INFO.get(key, {})
        summary = getattr(factory, "summary", "")
        out.append({"name": key, "summary": summary, **info})
    return out
