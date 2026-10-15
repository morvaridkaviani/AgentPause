"""Adaptive (timing-aware) vs myopic expected-value policy (H1b).

Usage (from the repository root)::

    python experiments/run_adaptive.py [--episodes N] [--config PATH] [--out DIR]

SIMULATED: results are not evaluated with human participants.
"""

from __future__ import annotations

from _common import parse_args, print_comparisons, print_table, run_config


def main() -> None:
    args = parse_args("adaptive.toml")
    result = run_config(args.config, episodes=args.episodes, out=args.out)
    print_table(result)
    if result.comparisons:
        print_comparisons(result)


if __name__ == "__main__":
    main()
