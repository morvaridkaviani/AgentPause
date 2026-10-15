"""Reproduce every simulated result and figure in the repository.

Usage (from the repository root)::

    python experiments/reproduce_all.py            # full run (a few minutes)
    python experiments/reproduce_all.py --quick    # 20 episodes per cell, for smoke testing;
                                                   # writes to results/quick and figures/quick

Steps:
  1. train the experimental learned policy (needed by compare_policies);
  2. run every config in experiments/configs (and the point-estimate hypothesis checks);
  3. generate the figures and tables;
  4. write and print the result hashes. Re-running on any machine should produce identical hashes
     (decision latency is excluded from the hash because it is machine-dependent).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from _common import CONFIGS, EXPERIMENTS, FIGURES, RESULTS, run_config
from compare_policies import check_hypotheses

ORDER = ("baseline", "fixed_threshold", "adaptive", "compare_policies", "frontier", "ablation", "sensitivity")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="20 episodes per scenario×policy")
    args = parser.parse_args()
    episodes = 20 if args.quick else None
    results = RESULTS / "quick" if args.quick else RESULTS
    figures = FIGURES / "quick" if args.quick else FIGURES

    subprocess.run([sys.executable, str(EXPERIMENTS / "train_learned_policy.py")], check=True)
    hashes = {}
    for name in ORDER:
        result = run_config(CONFIGS / f"{name}.toml", episodes=episodes, out=results / name)
        hashes[name] = result.result_hash
        if name == "compare_policies":
            verdicts = check_hypotheses(result.aggregates)
            (results / name / "hypotheses.json").write_text(json.dumps(verdicts, indent=2) + "\n", encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(EXPERIMENTS / "generate_figures.py"),
            "--results",
            str(results),
            "--figures",
            str(figures),
        ],
        check=True,
    )
    (results / "hashes.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(hashes, indent=2))


if __name__ == "__main__":
    main()
