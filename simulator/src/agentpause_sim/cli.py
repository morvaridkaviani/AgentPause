"""Command line: ``agentpause-sim run CONFIG``, ``agentpause-sim scenarios``, ``agentpause-sim show ID``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .experiment import ExperimentConfig, run_experiment
from .export import write_result
from .scenario import list_scenarios, load_scenario


def _progress(done: int, total: int) -> None:
    if done == total or done % max(1, total // 20) == 0:
        print(f"\r  {done}/{total} episodes", end="" if done < total else "\n", file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentpause-sim", description="AgentPause simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run an experiment config (.toml or .json)")
    run.add_argument("config", type=Path)
    run.add_argument("--out", type=Path, default=None, help="Output directory (default: experiments/results/<name>)")
    run.add_argument("--episodes", type=int, default=None, help="Override the number of episodes")
    sub.add_parser("scenarios", help="List bundled scenarios")
    show = sub.add_parser("show", help="Print a scenario as JSON")
    show.add_argument("scenario_id")
    args = parser.parse_args(argv)

    if args.command == "scenarios":
        for scenario in list_scenarios():
            print(
                f"{scenario.id:10s} {scenario.name:22s} {len(scenario.steps)} steps, {len(scenario.assumptions)} assumptions"
            )
        return 0
    if args.command == "show":
        print(json.dumps(load_scenario(args.scenario_id).to_dict(), indent=2))
        return 0

    config = ExperimentConfig.from_file(args.config)
    if args.episodes is not None:
        config = ExperimentConfig.from_dict({**config.to_dict(), "episodes": args.episodes})
    out = args.out or Path("experiments/results") / config.name
    print(f"Running '{config.name}': {config.total_episodes} episodes (simulated)", file=sys.stderr)
    result = run_experiment(config, progress=_progress)
    paths = write_result(result, out)
    print(f"Done in {result.duration_s:.1f}s. Result hash {result.result_hash[:16]}", file=sys.stderr)
    for kind, path in paths.items():
        print(f"  {kind:8s} {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
