"""Shared helpers for the experiment scripts (run from the repository root)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentpause_sim import ExperimentConfig, ExperimentResult, run_experiment, write_result

EXPERIMENTS = Path(__file__).resolve().parent
CONFIGS = EXPERIMENTS / "configs"
RESULTS = EXPERIMENTS / "results"
FIGURES = EXPERIMENTS / "figures"

TABLE_METRICS = (
    "interventions",
    "questions",
    "deferrals",
    "unnecessary_rate",
    "missed_rate",
    "recovery_rate",
    "harm",
    "rework_steps",
    "task_success",
    "task_duration_s",
)


def parse_args(default_config: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Run {default_config} (SIMULATED experiment)")
    parser.add_argument("--config", type=Path, default=CONFIGS / default_config)
    parser.add_argument("--episodes", type=int, default=None, help="Override episodes per scenario×policy (quick runs)")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args()


def run_config(config_path: Path, *, episodes: int | None = None, out: Path | None = None) -> ExperimentResult:
    config = ExperimentConfig.from_file(config_path)
    if episodes is not None:
        config = ExperimentConfig.from_dict({**config.to_dict(), "episodes": episodes})
    out_dir = out or RESULTS / config.name
    print(f"[{config.name}] {config.total_episodes} simulated episodes, seed {config.seed}", file=sys.stderr)

    def progress(done: int, total: int) -> None:
        if done == total or done % max(1, total // 10) == 0:
            print(f"  {done}/{total}", file=sys.stderr)

    result = run_experiment(config, progress=progress)
    paths = write_result(result, out_dir)
    print(
        f"[{config.name}] done in {result.duration_s:.1f}s; hash {result.result_hash[:16]}; wrote {paths['summary'].parent}",
        file=sys.stderr,
    )
    return result


def _fmt(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def print_table(result: ExperimentResult, metrics: tuple[str, ...] = TABLE_METRICS) -> None:
    print("\nSIMULATED RESULTS — not evaluated with human participants\n")
    header = f"{'condition':12s} {'policy':30s}" + "".join(f"{m[:12]:>13s}" for m in metrics)
    print(header)
    print("-" * len(header))
    for row in result.aggregates:
        print(
            f"{row['condition'][:12]:12s} {row['policy'][:30]:30s}"
            + "".join(f"{_fmt(row.get(m)):>13s}" for m in metrics)
        )


def print_comparisons(
    result: ExperimentResult,
    metrics: tuple[str, ...] = ("interventions", "harm", "missed_interventions", "rework_steps"),
) -> None:
    print("\nPaired differences (treatment − baseline, same seeds; 95% bootstrap CI)\n")
    for row in result.comparisons:
        parts = []
        for metric in metrics:
            cell = row.get(metric) or {}
            mean, ci = cell.get("mean_diff"), cell.get("ci", [None, None])
            if mean is None:
                continue
            parts.append(f"{metric}={mean:+.3f} [{_fmt(ci[0])}, {_fmt(ci[1])}]")
        print(f"  {row['treatment']} vs {row['baseline']:28s} n={row['pairs']:5d}  " + "  ".join(parts))
