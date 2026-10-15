"""Train the EXPERIMENTAL learned policy on simulated episodes.

Usage (from the repository root)::

    python experiments/train_learned_policy.py

Writes:
  * sdk/python/src/agentpause/policies/learned_weights.json (the model bundled with the SDK)
  * experiments/results/learned_policy/report.json (cross-validation and test AUC)

The labels come from the simulator's ground truth, so the model can only rediscover the
simulator's assumptions. See agentpause_sim/learning.py for the leakage controls and caveats.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import RESULTS

from agentpause_sim.learning import train

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "sdk" / "python" / "src" / "agentpause" / "policies" / "learned_weights.json"


def main() -> None:
    print("Training the experimental learned policy on SIMULATED data…", file=sys.stderr)
    model, report = train()
    WEIGHTS.write_text(json.dumps(model.to_dict(), indent=2) + "\n", encoding="utf-8")
    out = RESULTS / "learned_policy"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("leave_one_scenario_out_auc", "test_auc")}, indent=2))
    print(f"Weights → {WEIGHTS.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
