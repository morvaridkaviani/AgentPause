"""EXPERIMENTAL learned intervention policy (logistic regression).

Status and caveats (read before using):

* The bundled weights were trained on **simulated** episodes produced by ``agentpause_sim``,
  with the simulator's scripted ground truth as labels. A model trained this way recovers
  the simulator's assumptions. That is circular, and it is **not** evidence about real users
  (see research/research_questions.md, RQ2).
* Its legitimate uses are:
  - (a) a worked example of plugging a learned model into the ``InterventionPolicy``
    interface;
  - (b) a training pipeline that becomes meaningful once real study logs are collected.
* Training is reproducible: ``python experiments/train_learned_policy.py``. That script
  separates training seeds from evaluation seeds and holds out one scenario per fold (no
  leakage).

The model predicts p(intervention needed | features). The decision rule is: ask when
p ≥ threshold. It produces CLARIFY when the dominant uncertainty is an explicit assumption,
and ASK_HUMAN otherwise.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..context import ActionContext, UserPreferences
from ..decision import Decision
from ..explain.reasons import ReasonCode
from ..model import ModelParameters, error_cost
from ..signals import ResolvedSignals
from ..state import SessionState
from ..types import DecisionType
from .base import (
    InterventionPolicy,
    action_question,
    assumption_question,
    autonomy_reasons,
    consequence_reasons,
    uncertainty_reasons,
    unresolved_dependency_questions,
)

FEATURE_NAMES: tuple[str, ...] = (
    "p_agent_error",
    "p_intent_error",
    "severity",
    "irreversibility",
    "error_cost",
    "expected_harm",
    "cognitive_load",
    "not_breakpoint",
    "habituation",
    "external",
    "task_progress",
)

DEFAULT_WEIGHTS_PATH = Path(__file__).with_name("learned_weights.json")


def extract_features(signals: ResolvedSignals, params: ModelParameters) -> list[float]:
    """Feature vector for the learned policy. Uses only information available at decision time."""
    cost = error_cost(signals.severity, signals.recoverability, params)
    not_breakpoint = 0.5 if signals.at_breakpoint is None else (0.0 if signals.at_breakpoint else 1.0)
    return [
        signals.p_agent_error,
        signals.p_intent_error,
        signals.severity,
        1.0 - signals.recoverability,
        cost,
        signals.p_error * cost,
        signals.cognitive_load,
        not_breakpoint,
        signals.habituation,
        1.0 if signals.external_effects else 0.0,
        signals.task_progress,
    ]


class LogisticModel:
    def __init__(
        self,
        coefficients: Sequence[float],
        intercept: float,
        means: Sequence[float],
        scales: Sequence[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not (len(coefficients) == len(means) == len(scales) == len(FEATURE_NAMES)):
            raise ValueError(f"Learned model must have {len(FEATURE_NAMES)} features in order {FEATURE_NAMES}")
        self.coefficients = list(coefficients)
        self.intercept = float(intercept)
        self.means = list(means)
        self.scales = [s if s > 1e-12 else 1.0 for s in scales]
        self.metadata = metadata or {}

    def predict(self, features: Sequence[float]) -> float:
        z = self.intercept
        for x, w, m, s in zip(features, self.coefficients, self.means, self.scales, strict=True):
            z += w * (x - m) / s
        if z >= 0:
            return 1.0 / (1.0 + math.exp(-z))
        ez = math.exp(z)
        return ez / (1.0 + ez)

    def to_dict(self) -> dict[str, Any]:
        return {
            "features": list(FEATURE_NAMES),
            "coefficients": self.coefficients,
            "intercept": self.intercept,
            "means": self.means,
            "scales": self.scales,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogisticModel:
        if list(data.get("features", [])) != list(FEATURE_NAMES):
            raise ValueError("Feature list in weights file does not match this version of AgentPause")
        return cls(data["coefficients"], data["intercept"], data["means"], data["scales"], data.get("metadata"))

    @classmethod
    def load(cls, path: str | Path) -> LogisticModel:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


class LearnedPolicy(InterventionPolicy):
    name = "learned"
    summary = "EXPERIMENTAL: logistic model trained on simulated episodes (not on real users)."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        model: LogisticModel | None = None,
        weights_path: str | None = None,
        threshold: float = 0.5,
        block_catastrophic: bool = True,
    ) -> None:
        super().__init__(parameters, preferences)
        # Kept so that a restored session reloads the same weights (None = bundled weights).
        self.weights_path = str(weights_path) if weights_path and model is None else None
        if model is None:
            path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
            if not path.exists():
                raise FileNotFoundError(
                    f"No learned-policy weights at {path}. Train them with "
                    "`python experiments/train_learned_policy.py` or pass `model=`."
                )
            model = LogisticModel.load(path)
        self.model = model
        self.threshold = float(threshold)
        self.block_catastrophic = block_catastrophic

    def config(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "block_catastrophic": self.block_catastrophic,
            "weights_path": self.weights_path,
            "training": self.model.metadata,
        }

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        if self.block_catastrophic and self.is_catastrophic(signals):
            return self.catastrophic_block(context, state, signals)
        features = extract_features(signals, self.parameters)
        probability = self.model.predict(features)
        terms = {
            "p_intervention_needed": probability,
            "threshold": self.threshold,
            "features": dict(zip(FEATURE_NAMES, features, strict=True)),
        }
        if probability < self.threshold:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.CONTINUE,
                score=probability,
                reasons=[
                    ReasonCode.LEARNED_MODEL_BELOW_THRESHOLD,
                    *autonomy_reasons(context, signals, self.parameters),
                ],
                terms=terms,
            )
        reasons = [
            ReasonCode.LEARNED_MODEL_ABOVE_THRESHOLD,
            *uncertainty_reasons(signals),
            *consequence_reasons(context, signals),
        ]
        uncertain = list(signals.unresolved_dependencies)
        if uncertain and signals.p_intent_error > signals.p_agent_error:
            return self.make_decision(
                context,
                state,
                signals,
                DecisionType.CLARIFY,
                score=probability,
                reasons=reasons,
                questions=[assumption_question(a) for a in uncertain],
                terms=terms,
            )
        return self.make_decision(
            context,
            state,
            signals,
            DecisionType.ASK_HUMAN,
            score=probability,
            reasons=reasons,
            questions=[action_question(context), *unresolved_dependency_questions(signals)],
            terms=terms,
        )
