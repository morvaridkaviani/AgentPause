"""Training pipeline for the EXPERIMENTAL learned policy (pure Python, deterministic).

Data:
    Each scenario is run under a *recording* policy that always continues (full autonomy), so
    every step is observed exactly once and the training distribution does not depend on
    which policy chose to ask (no selection bias).

Label:
    ``intervention_needed``: at this step a pending error is visible to the human (an
    injected mistake) or the step builds on a wrong assumption. This uses simulator ground
    truth. It is never available at decision time and is never used as a feature.

Leakage control:
    * Training seed ≠ test seed.
    * Leave-one-scenario-out cross-validation measures generalization to unseen tasks.
    * Features use only signals available to the policy at decision time.

Caveat:
    The labels come from the simulator's own generative assumptions. The resulting model can
    at best rediscover them (circularity). It demonstrates the pipeline. It is not evidence
    about real users.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agentpause import ActionContext, AgentPause, Decision, DecisionType, InterventionPolicy, SessionState
from agentpause.policies.learned import FEATURE_NAMES, LogisticModel, extract_features

from .engine import EpisodeEngine
from .scenario import list_scenarios
from .user import SimulatedUser


class _FeatureRecorder(InterventionPolicy):
    name = "feature_recorder"

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[float]] = []

    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        self.rows.append(extract_features(signals, self.parameters))
        return self.make_decision(context, state, signals, DecisionType.CONTINUE, score=0.0)


@dataclass
class Dataset:
    features: list[list[float]]
    labels: list[int]
    scenarios: list[str]

    def subset(self, keep: Sequence[bool]) -> Dataset:
        return Dataset(
            [f for f, k in zip(self.features, keep, strict=True) if k],
            [y for y, k in zip(self.labels, keep, strict=True) if k],
            [s for s, k in zip(self.scenarios, keep, strict=True) if k],
        )


def generate_dataset(*, seed: int, episodes: int, scenarios: Sequence[str] | None = None) -> Dataset:
    ids = list(scenarios) if scenarios else [s.id for s in list_scenarios()]
    data = Dataset([], [], [])
    for scenario in list_scenarios():
        if scenario.id not in ids:
            continue
        for episode in range(episodes):
            recorder = _FeatureRecorder()
            engine = EpisodeEngine(
                scenario, AgentPause(recorder, explain="none"), seed=seed, episode=episode, user=SimulatedUser()
            )
            engine.run()
            if len(recorder.rows) != len(engine.state.records):
                raise RuntimeError("feature/record misalignment")
            for row, record in zip(recorder.rows, engine.state.records, strict=True):
                data.features.append(row)
                data.labels.append(int(bool(record["error_present"])))
                data.scenarios.append(scenario.id)
    return data


def _standardize(features: list[list[float]]) -> tuple[list[float], list[float]]:
    n = len(features)
    k = len(features[0])
    means = [sum(row[j] for row in features) / n for j in range(k)]
    scales = []
    for j in range(k):
        var = sum((row[j] - means[j]) ** 2 for row in features) / n
        scales.append(math.sqrt(var) if var > 1e-12 else 1.0)
    return means, scales


def fit_logistic(
    data: Dataset, *, l2: float = 1e-3, iterations: int = 1500, learning_rate: float = 0.5, balanced: bool = True
) -> LogisticModel:
    """Batch gradient descent on the (optionally class-balanced) logistic loss."""
    if not data.features:
        raise ValueError("empty dataset")
    means, scales = _standardize(data.features)
    x = [[(v - m) / s for v, m, s in zip(row, means, scales, strict=True)] for row in data.features]
    y = data.labels
    n, k = len(x), len(x[0])
    pos = sum(y)
    neg = n - pos
    if balanced and pos and neg:
        weights = [n / (2.0 * pos) if label else n / (2.0 * neg) for label in y]
    else:
        weights = [1.0] * n
    w = [0.0] * k
    b = 0.0
    for _ in range(iterations):
        grad_w = [0.0] * k
        grad_b = 0.0
        for xi, yi, wi in zip(x, y, weights, strict=True):
            z = b + sum(a * c for a, c in zip(w, xi, strict=True))
            p = 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
            err = (p - yi) * wi
            grad_b += err
            for j in range(k):
                grad_w[j] += err * xi[j]
        for j in range(k):
            w[j] -= learning_rate * (grad_w[j] / n + l2 * w[j])
        b -= learning_rate * grad_b / n
    return LogisticModel(w, b, means, scales)


def auc(scores: Sequence[float], labels: Sequence[int]) -> float | None:
    """Area under the ROC curve via the Mann–Whitney statistic (ties count half)."""
    pos = [s for s, y in zip(scores, labels, strict=True) if y]
    neg = [s for s, y in zip(scores, labels, strict=True) if not y]
    if not pos or not neg:
        return None
    ranked = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg])
    rank_sum = 0.0
    i = 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and ranked[j][0] == ranked[i][0]:
            j += 1
        avg_rank = (i + j + 1) / 2.0
        rank_sum += avg_rank * sum(1 for t in range(i, j) if ranked[t][1] == 1)
        i = j
    return (rank_sum - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def train(
    *, train_seed: int = 1001, test_seed: int = 2002, train_episodes: int = 120, test_episodes: int = 60
) -> tuple[LogisticModel, dict[str, Any]]:
    train_data = generate_dataset(seed=train_seed, episodes=train_episodes)
    test_data = generate_dataset(seed=test_seed, episodes=test_episodes)

    folds: dict[str, float | None] = {}
    for scenario in sorted(set(train_data.scenarios)):
        fit = fit_logistic(train_data.subset([s != scenario for s in train_data.scenarios]))
        held = train_data.subset([s == scenario for s in train_data.scenarios])
        folds[scenario] = auc([fit.predict(f) for f in held.features], held.labels)

    model = fit_logistic(train_data)
    test_auc = auc([model.predict(f) for f in test_data.features], test_data.labels)
    report = {
        "status": "EXPERIMENTAL: trained on simulated data; not evidence about real users",
        "features": list(FEATURE_NAMES),
        "label": "intervention_needed (simulator ground truth: visible mistake or wrong assumption at this step)",
        "train": {
            "seed": train_seed,
            "episodes_per_scenario": train_episodes,
            "rows": len(train_data.labels),
            "positives": sum(train_data.labels),
        },
        "test": {
            "seed": test_seed,
            "episodes_per_scenario": test_episodes,
            "rows": len(test_data.labels),
            "positives": sum(test_data.labels),
        },
        "leave_one_scenario_out_auc": folds,
        "test_auc": test_auc,
        "coefficients": dict(zip(FEATURE_NAMES, model.coefficients, strict=True)),
        "hyperparameters": {"l2": 1e-3, "iterations": 1500, "learning_rate": 0.5, "class_balanced": True},
    }
    model.metadata = {
        "train_seed": train_seed,
        "test_seed": test_seed,
        "test_auc": test_auc,
        "rows": len(train_data.labels),
        "data": "simulated (agentpause_sim scenarios, full-autonomy recording policy)",
    }
    return model, report
