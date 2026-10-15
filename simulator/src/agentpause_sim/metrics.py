"""Episode summaries, aggregate metrics, and paired policy comparisons.

Every metric is defined formally in ``research/metrics.md``. Each metric is tagged as:

* ``objective``: computable from logs, in simulation and in human studies;
* ``ground_truth``: needs labelled errors (available in simulation and in scripted study
  scenarios);
* ``simulated``: a modelling proxy that exists only in simulation (e.g. the workload proxy).
  It is **not** a measurement of human workload.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Any

from .engine import EpisodeState


@dataclass(frozen=True)
class MetricDef:
    key: str
    label: str
    kind: str  # objective | ground_truth | simulated
    higher_is_better: bool | None
    numerator: str | None = None
    denominator: str | None = None
    description: str = ""

    @property
    def is_rate(self) -> bool:
        return self.numerator is not None


METRICS: tuple[MetricDef, ...] = (
    MetricDef(
        "task_success",
        "Task success rate",
        "ground_truth",
        True,
        "task_success",
        "episodes",
        "Share of episodes completed without any harmful error.",
    ),
    MetricDef(
        "task_duration_s",
        "Task completion time (s, simulated)",
        "objective",
        False,
        description="Simulated wall-clock time incl. human response and rework time.",
    ),
    MetricDef(
        "interventions",
        "Interventions per episode",
        "objective",
        False,
        description="Number of interruptions (CLARIFY, ASK_HUMAN, BLOCK cards).",
    ),
    MetricDef(
        "questions",
        "Questions per episode",
        "objective",
        False,
        description="Number of individual questions (a batched card counts each).",
    ),
    MetricDef("deferrals", "Deferrals per episode", "objective", None, description="Number of DEFER decisions."),
    MetricDef(
        "unnecessary_rate",
        "Unnecessary intervention rate",
        "ground_truth",
        False,
        "unnecessary",
        "interventions",
        "Interventions that showed no pending error / all interventions.",
    ),
    MetricDef(
        "missed_rate",
        "Missed intervention rate",
        "ground_truth",
        False,
        "missed_interventions",
        "errors_total",
        "Errors that caused harm without ever being shown to the human / all errors.",
    ),
    MetricDef(
        "recovery_rate",
        "Recovery rate",
        "ground_truth",
        True,
        "errors_caught",
        "errors_total",
        "Errors caught before causing harm / all errors.",
    ),
    MetricDef(
        "harm",
        "Expected harm per episode",
        "ground_truth",
        False,
        description="Sum of error costs of errors that caused harm (scale: 1 = worst outcome).",
    ),
    MetricDef(
        "human_miss_rate",
        "Human oversight failure rate",
        "ground_truth",
        False,
        "human_miss_errors",
        "errors_shown",
        "Errors shown to the human but approved anyway / errors shown.",
    ),
    MetricDef(
        "agent_error_rate",
        "Agent error rate",
        "ground_truth",
        False,
        "errors_total",
        "steps",
        "Injected mistakes plus wrong assumptions per step.",
    ),
    MetricDef(
        "human_error_rate",
        "Human error rate",
        "ground_truth",
        False,
        "human_errors",
        "responses",
        "(Errors approved despite being shown + rejections of correct actions) / responses.",
    ),
    MetricDef(
        "override_rate",
        "User override rate",
        "objective",
        None,
        "overrides",
        "responses",
        "Responses that changed the proposal (edit, reject, take over, override a block) / responses.",
    ),
    MetricDef(
        "acceptance_rate",
        "Intervention acceptance rate",
        "objective",
        None,
        "accepted",
        "responses",
        "Responses that accepted the proposal unchanged / responses.",
    ),
    MetricDef(
        "rework_steps",
        "Rework steps per episode",
        "ground_truth",
        False,
        description="Executed steps that had to be redone after a late correction (intervention lateness).",
    ),
    MetricDef(
        "decision_latency_ms",
        "Decision latency (ms)",
        "objective",
        False,
        description="Mean wall-clock time of AgentPause.evaluate (machine-dependent).",
    ),
    MetricDef(
        "human_time_s",
        "Human time (s, simulated)",
        "simulated",
        False,
        description="Simulated time the user spent responding to interventions.",
    ),
    MetricDef(
        "workload_proxy",
        "Workload proxy (simulated)",
        "simulated",
        False,
        description="Σ over interventions of (1 + load) × (1 + 0.5·(questions − 1)). NOT a measure of human workload.",
    ),
)
METRIC_BY_KEY = {m.key: m for m in METRICS}


@dataclass
class EpisodeSummary:
    scenario: str
    policy: str
    condition: str
    seed: int
    episode: int
    participant_id: str
    status: str
    task_success: int
    steps: int
    decisions: int
    interventions: int
    confirmations: int
    clarifications: int
    blocks: int
    deferrals: int
    questions: int
    batched_interventions: int
    necessary: int
    unnecessary: int
    errors_total: int
    errors_caught: int
    errors_harmful: int
    errors_shown: int
    missed_interventions: int
    human_miss_errors: int
    critical_errors: int
    false_rejections: int
    human_errors: int
    responses: int
    accepted: int
    overrides: int
    rework_steps: int
    harm: float
    task_duration_s: float
    human_time_s: float
    decision_latency_ms: float
    workload_proxy: float

    @property
    def episodes(self) -> int:
        return 1

    def value(self, key: str) -> float | None:
        metric = METRIC_BY_KEY.get(key)
        if metric is not None and metric.is_rate:
            den = float(getattr(self, metric.denominator or "episodes"))
            return None if den == 0 else float(getattr(self, metric.numerator or "")) / den
        return float(getattr(self, key))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for metric in METRICS:
            if metric.is_rate and metric.key not in data:
                data[metric.key] = self.value(metric.key)
        return data


def summarize(state: EpisodeState, n_steps: int) -> EpisodeSummary:
    c = state.counters
    errors = list(state.errors.values())
    harmful = [e for e in errors if e.status == "harm"]
    shown = [e for e in errors if e.shown_at]
    human_miss_errors = [e for e in harmful if e.shown_at]
    interventions = [r for r in state.records if r.get("intervention")]
    workload = sum(
        (1.0 + float(r.get("cognitive_load") or 0.0)) * (1.0 + 0.5 * max(0, int(r.get("n_questions") or 1) - 1))
        for r in interventions
    )
    latencies = [float(r.get("decision_latency_ms") or 0.0) for r in state.records]
    overrides = sum(c.get(f"response_{k}", 0) for k in ("edit", "reject", "takeover", "override"))
    return EpisodeSummary(
        scenario=state.scenario_id,
        policy=state.policy,
        condition=state.condition,
        seed=state.seed,
        episode=state.episode,
        participant_id=f"sim-{state.episode:04d}",
        status=state.status,
        task_success=int(state.status == "completed" and not harmful),
        steps=n_steps,
        decisions=c.get("decisions", 0),
        interventions=c.get("interventions", 0),
        confirmations=c.get("decision_ask_human", 0),
        clarifications=c.get("decision_clarify", 0),
        blocks=c.get("decision_block", 0),
        deferrals=c.get("decision_defer", 0),
        questions=c.get("questions", 0),
        batched_interventions=c.get("batched_interventions", 0),
        necessary=c.get("necessary", 0),
        unnecessary=c.get("unnecessary", 0),
        errors_total=len(errors),
        errors_caught=sum(1 for e in errors if e.status == "caught"),
        errors_harmful=len(harmful),
        errors_shown=len(shown),
        missed_interventions=sum(1 for e in harmful if not e.shown_at),
        human_miss_errors=len(human_miss_errors),
        critical_errors=sum(1 for e in harmful if e.recoverability < 0.5),
        false_rejections=c.get("false_rejections", 0),
        human_errors=len(human_miss_errors) + c.get("false_rejections", 0),
        responses=c.get("responses", 0),
        accepted=c.get("accepted", 0),
        overrides=overrides,
        rework_steps=c.get("rework_steps", 0),
        harm=round(sum(e.harm for e in harmful), 6),
        task_duration_s=round(state.clock_s, 3),
        human_time_s=round(state.human_time_s, 3),
        decision_latency_ms=round(fmean(latencies), 4) if latencies else 0.0,
        workload_proxy=round(workload, 4),
    )


# ---------------------------------------------------------------------------------------
def _metric_value(rows: Sequence[EpisodeSummary], metric: MetricDef) -> float | None:
    if not rows:
        return None
    if metric.is_rate:
        num = sum(float(getattr(r, metric.numerator or "")) for r in rows)
        den = sum(float(getattr(r, metric.denominator or "episodes")) for r in rows)
        return None if den == 0 else num / den
    return fmean(float(getattr(r, metric.key)) for r in rows)


def bootstrap_ci(
    rows: Sequence[EpisodeSummary], metric: MetricDef, *, n_boot: int = 500, seed: int = 0, alpha: float = 0.05
) -> tuple[float | None, float | None]:
    """Percentile bootstrap over episodes (deterministic seed). Rates are re-pooled per resample."""
    if len(rows) < 2:
        return (None, None)
    rng = random.Random(seed)
    values: list[float] = []
    n = len(rows)
    for _ in range(n_boot):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        v = _metric_value(sample, metric)
        if v is not None:
            values.append(v)
    if not values:
        return (None, None)
    values.sort()
    lo = values[int((alpha / 2) * (len(values) - 1))]
    hi = values[int((1 - alpha / 2) * (len(values) - 1))]
    return (lo, hi)


def aggregate(
    summaries: Iterable[EpisodeSummary],
    *,
    group_by: Sequence[str] = ("condition", "policy"),
    metrics: Sequence[str] | None = None,
    n_boot: int = 500,
    seed: int = 0,
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[EpisodeSummary]] = defaultdict(list)
    for s in summaries:
        groups[tuple(getattr(s, g) for g in group_by)].append(s)
    selected = [METRIC_BY_KEY[m] for m in metrics] if metrics else list(METRICS)
    out: list[dict[str, Any]] = []
    for key in sorted(groups, key=lambda k: tuple(str(x) for x in k)):
        rows = groups[key]
        row: dict[str, Any] = dict(zip(group_by, key, strict=True))
        row["episodes"] = len(rows)
        for metric in selected:
            row[metric.key] = _metric_value(rows, metric)
            if n_boot > 0:
                lo, hi = bootstrap_ci(rows, metric, n_boot=n_boot, seed=seed)
                row[f"{metric.key}_ci"] = [lo, hi]
        out.append(row)
    return out


def paired_comparison(
    summaries: Iterable[EpisodeSummary],
    *,
    baseline: str,
    treatment: str,
    metrics: Sequence[str] = (
        "interventions",
        "unnecessary",
        "missed_interventions",
        "harm",
        "task_duration_s",
        "rework_steps",
    ),
    by: Sequence[str] = ("condition",),
    n_boot: int = 1000,
    seed: int = 0,
) -> list[dict[str, Any]]:
    """Mean per-episode difference (treatment − baseline) on identical seeds (common random numbers)."""
    index: dict[tuple[Any, ...], dict[str, EpisodeSummary]] = defaultdict(dict)
    for s in summaries:
        index[(*(getattr(s, b) for b in by), s.scenario, s.seed, s.episode)][s.policy] = s
    grouped: dict[tuple[Any, ...], list[tuple[EpisodeSummary, EpisodeSummary]]] = defaultdict(list)
    for key, by_policy in index.items():
        if baseline in by_policy and treatment in by_policy:
            grouped[key[: len(by)]].append((by_policy[baseline], by_policy[treatment]))
    out: list[dict[str, Any]] = []
    for group_key in sorted(grouped, key=lambda k: tuple(str(x) for x in k)):
        pairs = grouped[group_key]
        row: dict[str, Any] = dict(zip(by, group_key, strict=True))
        row.update({"baseline": baseline, "treatment": treatment, "pairs": len(pairs)})
        rng = random.Random(seed)
        for metric in metrics:
            diffs = [float(getattr(t, metric)) - float(getattr(b, metric)) for b, t in pairs]
            mean = fmean(diffs) if diffs else None
            boot: list[float] = []
            if len(diffs) >= 2:
                for _ in range(n_boot):
                    boot.append(fmean(diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))))
                boot.sort()
            row[metric] = {
                "mean_diff": mean,
                "ci": [boot[int(0.025 * (len(boot) - 1))], boot[int(0.975 * (len(boot) - 1))]]
                if boot
                else [None, None],
                "share_treatment_lower": (sum(1 for d in diffs if d < 0) / len(diffs) if diffs else None),
            }
        out.append(row)
    return out


def metric_catalog() -> list[dict[str, Any]]:
    return [asdict(m) | {"is_rate": m.is_rate} for m in METRICS]
