"""Fixed baselines: full autonomy vs always confirm.

Usage (from the repository root)::

    python experiments/run_baseline.py [--episodes N] [--config PATH] [--out DIR]

SIMULATED: results are not evaluated with human participants.
"""

from __future__ import annotations

from _common import parse_args, print_comparisons, print_table, run_config


def main() -> None:
    args = parse_args("baseline.toml")
    result = run_config(args.config, episodes=args.episodes, out=args.out)
    print_table(result)
    if result.comparisons:
        print_comparisons(result)


if __name__ == "__main__":
    main()
