"""Reproducible batch experiments over scenarios × policies × conditions × episodes."""

from __future__ import annotations

import hashlib
import json
import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentpause import AgentPause, InterventionPolicy, ModelParameters, create_policy

from .ablation import SignalAblation
from .engine import EngineConfig, EpisodeEngine
from .metrics import EpisodeSummary, aggregate, paired_comparison, summarize
from .scenario import list_scenarios, load_scenario
from .user import SimulatedUser, SimulatedUserParams


@dataclass(frozen=True)
class PolicySpec:
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    ablate: tuple[str, ...] = ()
    label: str | None = None

    @property
    def key(self) -> str:
        return self.label or (f"{self.name}-no_{'+'.join(sorted(self.ablate))}" if self.ablate else self.name)

    @classmethod
    def from_value(cls, value: str | dict[str, Any]) -> PolicySpec:
        if isinstance(value, str):
            return cls(name=value)
        return cls(
            name=value["name"],
            config=dict(value.get("config") or {}),
            preferences=value.get("preferences"),
            parameters=dict(value.get("parameters") or {}),
            ablate=tuple(value.get("ablate") or ()),
            label=value.get("label"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "config": self.config,
            "preferences": self.preferences,
            "parameters": self.parameters,
            "ablate": list(self.ablate),
            "label": self.label,
        }


@dataclass(frozen=True)
class ConditionSpec:
    """A simulation condition: simulated-user and engine settings shared by all policies."""

    name: str = "default"
    user: dict[str, Any] = field(default_factory=dict)
    engine: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    """Model-parameter overrides applied to every policy (e.g. a misspecified habituation rate)."""

    @classmethod
    def from_value(cls, value: dict[str, Any]) -> ConditionSpec:
        return cls(
            name=str(value.get("name", "default")),
            user=dict(value.get("user") or {}),
            engine=dict(value.get("engine") or {}),
            parameters=dict(value.get("parameters") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "user": self.user, "engine": self.engine, "parameters": self.parameters}


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    policies: tuple[PolicySpec, ...]
    scenarios: tuple[str, ...] = ("all",)
    episodes: int = 50
    seed: int = 20261014
    conditions: tuple[ConditionSpec, ...] = (ConditionSpec(),)
    explain: str = "none"
    description: str = ""
    keep_records: bool = True
    bootstrap: int = 500

    def scenario_ids(self) -> list[str]:
        if "all" in self.scenarios:
            return [s.id for s in list_scenarios()]
        return list(self.scenarios)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExperimentConfig:
        policies = tuple(PolicySpec.from_value(p) for p in data.get("policies", []))
        if not policies:
            raise ValueError("An experiment needs at least one policy")
        conditions = tuple(ConditionSpec.from_value(c) for c in data.get("conditions", [])) or (ConditionSpec(),)
        scenarios = data.get("scenarios", ["all"])
        if isinstance(scenarios, str):
            scenarios = [scenarios]
        episodes = int(data.get("episodes", 50))
        if episodes < 1:
            raise ValueError("episodes must be ≥ 1")
        config = cls(
            name=str(data.get("name", "experiment")),
            description=str(data.get("description", "")),
            policies=policies,
            scenarios=tuple(scenarios),
            episodes=episodes,
            seed=int(data.get("seed", 20261014)),
            conditions=conditions,
            explain=str(data.get("explain", "none")),
            keep_records=bool(data.get("keep_records", True)),
            bootstrap=int(data.get("bootstrap", 500)),
        )
        for sid in config.scenario_ids():
            load_scenario(sid)  # validate early
        return config

    @classmethod
    def from_file(cls, path: str | Path) -> ExperimentConfig:
        path = Path(path)
        if path.suffix == ".toml":
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "policies": [p.to_dict() for p in self.policies],
            "scenarios": list(self.scenarios),
            "episodes": self.episodes,
            "seed": self.seed,
            "conditions": [c.to_dict() for c in self.conditions],
            "explain": self.explain,
            "keep_records": self.keep_records,
            "bootstrap": self.bootstrap,
        }

    @property
    def total_episodes(self) -> int:
        return len(self.scenario_ids()) * len(self.policies) * len(self.conditions) * self.episodes


@dataclass
class ExperimentResult:
    config: ExperimentConfig
    summaries: list[EpisodeSummary]
    records: list[dict[str, Any]]
    aggregates: list[dict[str, Any]]
    by_scenario: list[dict[str, Any]]
    comparisons: list[dict[str, Any]]
    duration_s: float
    result_hash: str

    def to_dict(self, *, include_records: bool = False, include_summaries: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "config": self.config.to_dict(),
            "aggregates": self.aggregates,
            "by_scenario": self.by_scenario,
            "comparisons": self.comparisons,
            "duration_s": round(self.duration_s, 3),
            "result_hash": self.result_hash,
            "note": "SIMULATED RESULTS. Not evaluated with human participants.",
        }
        if include_summaries:
            data["summaries"] = [s.to_dict() for s in self.summaries]
        if include_records:
            data["records"] = self.records
        return data


def build_policy(spec: PolicySpec, condition: ConditionSpec) -> InterventionPolicy:
    parameters = ModelParameters.from_dict({**condition.parameters, **spec.parameters})
    policy = create_policy(spec.name, parameters=parameters, preferences=spec.preferences, **spec.config)
    if spec.ablate:
        policy = SignalAblation(policy, list(spec.ablate))
    if spec.label:
        policy.name = spec.label
    return policy


def run_episode(
    scenario_id: str,
    spec: PolicySpec,
    condition: ConditionSpec,
    *,
    seed: int,
    episode: int,
    explain: str = "none",
) -> EpisodeEngine:
    scenario = load_scenario(scenario_id)
    policy = build_policy(spec, condition)
    pause = AgentPause(policy, explain=explain)
    user = SimulatedUser(SimulatedUserParams.from_dict(condition.user))
    engine = EpisodeEngine(
        scenario,
        pause,
        seed=seed,
        episode=episode,
        condition=condition.name,
        config=EngineConfig.from_dict(condition.engine),
        user=user,
    )
    engine.run()
    return engine


_NON_DETERMINISTIC = {"decision_latency_ms"}


def result_hash(summaries: list[EpisodeSummary], records: list[dict[str, Any]]) -> str:
    """SHA-256 over all outputs except machine-dependent timing fields."""
    digest = hashlib.sha256()
    for s in summaries:
        data = {k: v for k, v in s.to_dict().items() if k not in _NON_DETERMINISTIC}
        digest.update(json.dumps(data, sort_keys=True, default=str).encode())
    for r in records:
        data = {k: v for k, v in r.items() if k not in _NON_DETERMINISTIC}
        digest.update(json.dumps(data, sort_keys=True, default=str).encode())
    return digest.hexdigest()


def run_experiment(
    config: ExperimentConfig,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> ExperimentResult:
    started = time.perf_counter()
    summaries: list[EpisodeSummary] = []
    records: list[dict[str, Any]] = []
    total = config.total_episodes
    done = 0
    for condition in config.conditions:
        for scenario_id in config.scenario_ids():
            n_steps = len(load_scenario(scenario_id).steps)
            for spec in config.policies:
                for episode in range(config.episodes):
                    engine = run_episode(
                        scenario_id, spec, condition, seed=config.seed, episode=episode, explain=config.explain
                    )
                    summary = summarize(engine.state, n_steps)
                    summary.policy = spec.key
                    summaries.append(summary)
                    if config.keep_records:
                        for record in engine.state.records:
                            records.append({**record, "policy": spec.key})
                    done += 1
                    if progress is not None:
                        progress(done, total)
    aggregates = aggregate(summaries, group_by=("condition", "policy"), n_boot=config.bootstrap, seed=config.seed)
    by_scenario = aggregate(summaries, group_by=("condition", "scenario", "policy"), n_boot=0, seed=config.seed)
    comparisons: list[dict[str, Any]] = []
    keys = [p.key for p in config.policies]
    treatment = "adaptive" if "adaptive" in keys else keys[-1]
    for baseline in keys:
        if baseline != treatment:
            comparisons += paired_comparison(
                summaries, baseline=baseline, treatment=treatment, n_boot=max(200, config.bootstrap), seed=config.seed
            )
    return ExperimentResult(
        config=config,
        summaries=summaries,
        records=records,
        aggregates=aggregates,
        by_scenario=by_scenario,
        comparisons=comparisons,
        duration_s=time.perf_counter() - started,
        result_hash=result_hash(summaries, records),
    )
