"""Re-run the simulated experiments and compare result hashes with the committed reference.

Usage (from the repository root)::

    python scripts/check_reproducibility.py           # full configs (a few minutes)
    python scripts/check_reproducibility.py --quick   # 20 episodes per cell (about a minute)
    python scripts/check_reproducibility.py --only compare_policies frontier

Results are written to a temporary directory, so committed results are never touched.
Exit code 0 if every hash matches ``experiments/results/reference/hashes[_quick].json``.
Hashes cover every metric and record except decision latency (machine-dependent).
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from _common import CONFIGS, RESULTS, run_config  # noqa: E402
from reproduce_all import ORDER  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--quick", action="store_true", help="20 episodes per scenario×policy")
    parser.add_argument("--only", nargs="*", default=None, help=f"subset of {', '.join(ORDER)}")
    args = parser.parse_args()

    reference_path = RESULTS / "reference" / ("hashes_quick.json" if args.quick else "hashes.json")
    if not reference_path.exists():
        print(f"No reference hashes at {reference_path}. Run experiments/reproduce_all.py first.", file=sys.stderr)
        return 2
    reference: dict[str, str] = json.loads(reference_path.read_text(encoding="utf-8"))
    names = args.only or [name for name in ORDER if name in reference]

    failures = 0
    with tempfile.TemporaryDirectory(prefix="agentpause-repro-") as tmp:
        for name in names:
            result = run_config(CONFIGS / f"{name}.toml", episodes=20 if args.quick else None, out=Path(tmp) / name)
            expected = reference.get(name)
            ok = expected == result.result_hash
            failures += not ok
            status = "OK      " if ok else "MISMATCH"
            print(f"{status} {name:18s} {result.result_hash[:16]}  (reference {str(expected)[:16]})")
    if failures:
        print(f"\n{failures} experiment(s) did not reproduce. Check Python/package versions and local changes.")
        return 1
    print("\nAll simulated results reproduced exactly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
