"""Main policy comparison (RQ1: H1a, H1b) on the held-out evaluation seed.

Usage (from the repository root)::

    python experiments/compare_policies.py [--episodes N]

Prints aggregate metrics with 95% bootstrap CIs and paired differences between the adaptive
policy and every baseline, computed on identical seeds (common random numbers).

SIMULATED: results are not evaluated with human participants.
"""

from __future__ import annotations

import json

from _common import RESULTS, parse_args, print_comparisons, print_table, run_config

HYPOTHESES = """
Hypotheses tested here (pre-specified in research/research_questions.md):
  H1a  adaptive has a lower unnecessary-intervention rate than always_confirm and fixed_threshold,
       with a missed-intervention rate not higher than fixed_threshold.
  H1b  adaptive reaches equal or lower harm than myopic_voi with fewer interruptions.
"""


def check_hypotheses(aggregates: list[dict]) -> dict[str, object]:
    by = {row["policy"]: row for row in aggregates if row["condition"] == "default"}
    out: dict[str, object] = {}
    a = by.get("adaptive")
    if a is None:
        return out
    if "always_confirm" in by and "fixed_threshold" in by:
        out["H1a_unnecessary_lower_than_always_confirm"] = (
            a["unnecessary_rate"] < by["always_confirm"]["unnecessary_rate"]
        )
        out["H1a_unnecessary_lower_than_fixed_threshold"] = (
            a["unnecessary_rate"] < by["fixed_threshold"]["unnecessary_rate"]
        )
        out["H1a_missed_not_higher_than_fixed_threshold"] = a["missed_rate"] <= by["fixed_threshold"]["missed_rate"]
    if "myopic_voi" in by:
        out["H1b_fewer_interruptions_than_myopic"] = a["interventions"] < by["myopic_voi"]["interventions"]
        out["H1b_harm_not_higher_than_myopic"] = a["harm"] <= by["myopic_voi"]["harm"]
    return out


def main() -> None:
    args = parse_args("compare_policies.toml")
    result = run_config(args.config, episodes=args.episodes, out=args.out)
    print(HYPOTHESES)
    print_table(result)
    print_comparisons(result)
    verdicts = check_hypotheses(result.aggregates)
    print("\nPoint-estimate checks (see CIs above before drawing conclusions):")
    for key, value in verdicts.items():
        print(f"  {key:48s} {'supported' if value else 'NOT supported'}")
    out_dir = args.out or RESULTS / result.config.name
    (out_dir / "hypotheses.json").write_text(json.dumps(verdicts, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
