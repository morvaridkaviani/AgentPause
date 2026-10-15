"""Generate the figures and tables for the SIMULATED experiments.

Usage (from the repository root, after running the experiments)::

    python experiments/generate_figures.py [--results DIR] [--figures DIR]

Reads ``<results>/<experiment>/summary.json`` (and ``records.csv`` for the decision mix,
timing, and reason figures) and writes PNG + PDF figures and CSV tables to ``<figures>``.
Experiments that have not been run are skipped with a message.

Design rules (see the dataviz notes in docs/experiments.md): one y-axis per chart; at most
three hues per line chart with direct labels; colour follows the policy across figures
(adaptive = blue, myopic value of asking = orange, fixed threshold = aqua, confidence
threshold = yellow); reference policies are grey with text labels; every figure has a CSV
table with the same numbers. Every figure is labelled as simulated.

Requires matplotlib: ``pip install -e "simulator[figures]"``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPERIMENTS = Path(__file__).resolve().parent

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
except ImportError:  # pragma: no cover - optional dependency
    sys.exit('generate_figures.py needs matplotlib: pip install -e "simulator[figures]"')

INK = "#1f2328"
INK_2 = "#59636e"
GRID = "#e6e8eb"
GREY = "#8c959f"
FAMILY_COLOR = {
    "adaptive": "#2a78d6",
    "myopic_voi": "#eb6834",
    "fixed_threshold": "#1baf7a",
    "confidence_threshold": "#eda100",
}
# Marker shapes give every policy family a second, non-colour identity cue.
FAMILY_MARKER = {"adaptive": "o", "myopic_voi": "^", "fixed_threshold": "D", "confidence_threshold": "v"}
DECISION_COLOR = {
    "CONTINUE": "#2a78d6",
    "DEFER": "#eb6834",
    "CLARIFY": "#1baf7a",
    "ASK_HUMAN": "#eda100",
    "BLOCK": "#e87ba4",
}
LABEL = {
    "full_autonomy": "Full autonomy",
    "always_confirm": "Always confirm",
    "fixed_threshold": "Fixed risk threshold",
    "adaptive": "Adaptive (AgentPause)",
    "user_customized": "User-customized",
    "myopic_voi": "Myopic value of asking",
    "rule_based": "Rule-based",
    "confidence_threshold": "Confidence threshold",
    "learned": "Learned (experimental)",
}
SIMULATED = "SIMULATED results; not evaluated with human participants."


def style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "font.family": "sans-serif",
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK_2,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.titlecolor": INK,
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": INK_2,
            "ytick.color": INK_2,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "legend.frameon": False,
            "lines.linewidth": 2,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
        }
    )


def label(policy: str) -> str:
    base, _, param = policy.partition("@")
    if base.startswith("adaptive-no_"):
        return "without " + base.removeprefix("adaptive-no_").replace("_", " ").replace("+", " + ")
    text = LABEL.get(base, base.replace("_", " "))
    return f"{text} @ {param}" if param else text


def family(policy: str) -> str:
    return policy.split("@", 1)[0]


def load_summary(results: Path, name: str) -> dict[str, Any] | None:
    path = results / name / "summary.json"
    if not path.exists():
        print(f"  skip {name}: {path} not found (run the experiment first)", file=sys.stderr)
        return None
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def load_records(results: Path, name: str) -> list[dict[str, str]]:
    path = results / name / "records.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def save(fig: Figure, out: Path, name: str) -> None:
    fig.text(0.0, -0.02, SIMULATED, fontsize=7.5, color=INK_2, ha="left", va="top", transform=fig.transFigure)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{name}.{ext}")
    plt.close(fig)
    print(f"  wrote {name}.png/.pdf", file=sys.stderr)


def write_table(out: Path, name: str, columns: list[str], rows: list[list[Any]]) -> None:
    with (out / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([f"{v:.4f}" if isinstance(v, float) else v for v in row])


def ci(row: dict[str, Any], key: str) -> tuple[float | None, float | None]:
    value = row.get(f"{key}_ci")
    if isinstance(value, list) and len(value) == 2:
        return value[0], value[1]
    return None, None


# ---------------------------------------------------------------- frontier


def frontier(results: Path, out: Path) -> None:
    summary = load_summary(results, "frontier")
    if summary is None:
        return
    rows = [r for r in summary["aggregates"] if r["condition"] == "default"] or summary["aggregates"]
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[family(row["policy"])].append(row)

    write_table(
        out,
        "table_frontier",
        ["policy", "interventions", "harm", "missed_rate", "unnecessary_rate", "rework_steps"],
        [
            [r["policy"], r["interventions"], r["harm"], r["missed_rate"], r["unnecessary_rate"], r["rework_steps"]]
            for r in rows
        ],
    )

    panels = [
        ("A. Adaptive vs myopic value of asking", ["adaptive", "myopic_voi"]),
        ("B. Adaptive vs fixed thresholds", ["adaptive", "fixed_threshold", "confidence_threshold"]),
    ]
    for metric, ylabel, name in (
        ("harm", "Harm per episode (lower is better)", "frontier_harm"),
        ("missed_rate", "Missed-intervention rate (lower is better)", "frontier_missed"),
    ):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True, constrained_layout=True)
        for ax, (title, families) in zip(axes, panels, strict=True):
            for fam in families:
                points = sorted(by_family.get(fam, []), key=lambda r: r["interventions"])
                if not points:
                    continue
                xs = [p["interventions"] for p in points]
                ys = [p[metric] for p in points]
                color = FAMILY_COLOR[fam]
                marker = FAMILY_MARKER[fam]
                ax.plot(
                    xs,
                    ys,
                    color=color,
                    marker=marker,
                    markersize=6,
                    markeredgecolor="white",
                    markeredgewidth=1.2,
                    label=LABEL[fam],
                    zorder=3,
                )
                default = next((p for p in points if p["policy"] in (f"{fam}@0.02", f"{fam}@0.35", f"{fam}@0.8")), None)
                if default is not None:
                    ax.plot(
                        [default["interventions"]],
                        [default[metric]],
                        marker="o",
                        markersize=12,
                        markerfacecolor="none",
                        markeredgecolor=color,
                        markeredgewidth=1.5,
                        zorder=4,
                    )
            for ref in ("full_autonomy", "always_confirm", "rule_based"):
                for point in by_family.get(ref, []):
                    ax.plot([point["interventions"]], [point[metric]], marker="s", markersize=6, color=GREY, zorder=3)
                    ax.annotate(
                        LABEL[ref],
                        (point["interventions"], point[metric]),
                        xytext=(5, -10),
                        textcoords="offset points",
                        fontsize=7.5,
                        color=INK_2,
                    )
            ax.set_title(title)
            ax.set_xlabel("Interruptions per episode")
            ax.legend(loc="upper right", fontsize=8)
        axes[0].set_ylabel(ylabel)
        fig.suptitle(
            "Harm–interruption frontiers (each point is one parameter value; ringed = default)",
            x=0.0,
            ha="left",
            fontsize=10,
            color=INK,
        )
        save(fig, out, name)


# ---------------------------------------------------------------- comparison


def comparison(results: Path, out: Path) -> None:
    summary = load_summary(results, "compare_policies")
    if summary is None:
        return
    rows = [r for r in summary["aggregates"] if r["condition"] == "default"] or summary["aggregates"]
    metrics = [
        ("interventions", "Interruptions per episode"),
        ("unnecessary_rate", "Unnecessary-interruption rate"),
        ("missed_rate", "Missed-intervention rate"),
        ("harm", "Harm per episode"),
        ("rework_steps", "Rework steps per episode"),
        ("task_duration_s", "Simulated task time (s)"),
    ]
    write_table(
        out,
        "table_compare_policies",
        ["policy"] + [f"{m}{suffix}" for m, _ in metrics for suffix in ("", "_ci_low", "_ci_high")],
        [[r["policy"]] + [v for m, _ in metrics for v in (r.get(m), *ci(r, m))] for r in rows],
    )
    order = sorted(rows, key=lambda r: r["interventions"])
    names = [label(r["policy"]) for r in order]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5), sharey=True, constrained_layout=True)
    for ax, (metric, title) in zip(axes.flat, metrics, strict=True):
        values = [r.get(metric) if r.get(metric) is not None else 0.0 for r in order]
        colors = [FAMILY_COLOR["adaptive"] if r["policy"] == "adaptive" else GREY for r in order]
        lows = [
            v - (ci(r, metric)[0] if ci(r, metric)[0] is not None else v) for r, v in zip(order, values, strict=True)
        ]
        highs = [
            (ci(r, metric)[1] if ci(r, metric)[1] is not None else v) - v for r, v in zip(order, values, strict=True)
        ]
        y = range(len(order))
        ax.barh(y, values, height=0.62, color=colors, edgecolor="white", linewidth=2)
        ax.errorbar(values, y, xerr=[lows, highs], fmt="none", ecolor=INK, elinewidth=1, capsize=0)
        ax.set_title(title)
        ax.grid(axis="y", visible=False)
        ax.set_yticks(list(y), names)
        ax.invert_yaxis()
    fig.suptitle(
        "Policy comparison on held-out seeds (bars: mean; lines: 95% bootstrap CI)",
        x=0.0,
        ha="left",
        fontsize=10,
        color=INK,
    )
    save(fig, out, "compare_policies")

    comparisons = [c for c in summary.get("comparisons", []) if c.get("treatment") == "adaptive"]
    if comparisons:
        keys = ["interventions", "unnecessary", "missed_interventions", "harm", "rework_steps", "task_duration_s"]
        write_table(
            out,
            "table_paired_differences",
            ["baseline", "treatment", "pairs"] + [f"{k}_{s}" for k in keys for s in ("mean_diff", "ci_low", "ci_high")],
            [
                [c["baseline"], c["treatment"], c["pairs"]]
                + [
                    v
                    for k in keys
                    for v in ((c[k]["mean_diff"], *c[k]["ci"]) if isinstance(c.get(k), dict) else (None, None, None))
                ]
                for c in comparisons
            ],
        )


# ---------------------------------------------------------------- decisions, timing, reasons


def decision_mix(results: Path, out: Path) -> None:
    records = load_records(results, "compare_policies")
    if not records:
        print("  skip decision mix: compare_policies/records.csv not found", file=sys.stderr)
        return
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in records:
        counts[row["policy"]][row["decision"]] += 1
    policies = sorted(counts, key=lambda p: counts[p]["CONTINUE"] / max(1, sum(counts[p].values())), reverse=True)
    decisions = [d for d in DECISION_COLOR if any(counts[p][d] for p in policies)]
    write_table(
        out,
        "table_decision_mix",
        ["policy", *decisions, "total"],
        [
            [p, *(counts[p][d] / max(1, sum(counts[p].values())) for d in decisions), sum(counts[p].values())]
            for p in policies
        ],
    )
    fig, ax = plt.subplots(figsize=(9, 4.2), constrained_layout=True)
    left = [0.0] * len(policies)
    for decision in decisions:
        shares = [counts[p][decision] / max(1, sum(counts[p].values())) for p in policies]
        ax.barh(
            range(len(policies)),
            shares,
            left=left,
            height=0.62,
            color=DECISION_COLOR[decision],
            edgecolor="white",
            linewidth=2,
            label=decision.replace("_", " ").title(),
        )
        left = [a + b for a, b in zip(left, shares, strict=True)]
    ax.set_yticks(range(len(policies)), [label(p) for p in policies])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", visible=False)
    ax.set_title("Share of decisions by type (all scenarios, held-out seeds)", pad=30)
    ax.legend(ncols=len(decisions), loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8)
    save(fig, out, "decision_mix")


def timing(results: Path, out: Path) -> None:
    records = load_records(results, "compare_policies")
    if not records:
        return
    policies = ["always_confirm", "rule_based", "myopic_voi", "adaptive"]
    bins = ["0–25%", "25–50%", "50–75%", "75–100%"]
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in records:
        if row["policy"] in policies and row["intervention"] == "True":
            progress = float(row["task_progress"] or 0.0)
            counts[row["policy"]][bins[min(3, int(progress * 4))]] += 1
    episodes: Counter[str] = Counter()
    seen: set[tuple[str, str, str]] = set()
    for row in records:
        key = (row["policy"], row["scenario"], row["episode"])
        if row["policy"] in policies and key not in seen:
            seen.add(key)
            episodes[row["policy"]] += 1
    write_table(
        out,
        "table_timing",
        ["policy", *bins],
        [[p, *(counts[p][b] / max(1, episodes[p]) for b in bins)] for p in policies],
    )
    fig, axes = plt.subplots(1, len(policies), figsize=(11, 2.8), sharey=True, constrained_layout=True)
    for ax, policy in zip(axes, policies, strict=True):
        values = [counts[policy][b] / max(1, episodes[policy]) for b in bins]
        color = FAMILY_COLOR.get(policy, GREY)
        ax.bar(range(len(bins)), values, width=0.7, color=color, edgecolor="white", linewidth=2)
        ax.set_xticks(range(len(bins)), bins, fontsize=7.5)
        ax.set_title(label(policy), fontsize=9)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Interruptions per episode")
    fig.suptitle(
        "When interruptions happen (task progress at the interruption)", x=0.0, ha="left", fontsize=10, color=INK
    )
    save(fig, out, "timing")


def reasons(results: Path, out: Path) -> None:
    records = load_records(results, "compare_policies")
    if not records:
        return
    counts: Counter[str] = Counter()
    for row in records:
        if row["policy"] == "adaptive" and row["decision"] != "CONTINUE":
            counts.update(code for code in row["reason_codes"].split(";") if code)
    top = counts.most_common(12)
    if not top:
        return
    write_table(out, "table_reasons_adaptive", ["reason_code", "count"], [list(t) for t in top])
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    ax.barh(
        range(len(top)),
        [c for _, c in top],
        height=0.62,
        color=FAMILY_COLOR["adaptive"],
        edgecolor="white",
        linewidth=2,
    )
    ax.set_yticks(range(len(top)), [code for code, _ in top], fontsize=8, fontfamily="monospace")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Non-CONTINUE decisions citing the reason")
    ax.set_title("Adaptive policy: reason codes behind non-CONTINUE decisions")
    save(fig, out, "reasons_adaptive")


# ---------------------------------------------------------------- ablation & sensitivity


def ablation(results: Path, out: Path) -> None:
    summary = load_summary(results, "ablation")
    if summary is None:
        return
    rows = summary["aggregates"]
    full = next((r for r in rows if r["policy"] == "adaptive"), None)
    if full is None:
        return
    others = [r for r in rows if r["policy"] != "adaptive"]
    metrics = [
        ("interventions", "Interruptions per episode"),
        ("harm", "Harm per episode"),
        ("missed_rate", "Missed-intervention rate"),
    ]
    write_table(
        out,
        "table_ablation",
        ["policy"] + [f"{m}{s}" for m, _ in metrics for s in ("", "_delta_vs_full")],
        [[r["policy"]] + [v for m, _ in metrics for v in (r[m], r[m] - full[m])] for r in [full, *others]],
    )
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True, constrained_layout=True)
    names = [label(r["policy"]) for r in others]
    for ax, (metric, title) in zip(axes, metrics, strict=True):
        deltas = [r[metric] - full[metric] for r in others]
        ax.barh(range(len(others)), deltas, height=0.62, color=GREY, edgecolor="white", linewidth=2)
        ax.axvline(0, color=INK, linewidth=1)
        ax.set_title(f"Δ {title.lower()}")
        ax.set_yticks(range(len(others)), names)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
    fig.suptitle(
        "Signal ablation: change vs the full adaptive policy when one signal is hidden (simulator assumptions apply)",
        x=0.0,
        ha="left",
        fontsize=10,
        color=INK,
    )
    save(fig, out, "ablation")


def sensitivity(results: Path, out: Path) -> None:
    summary = load_summary(results, "sensitivity")
    if summary is None:
        return
    rows = summary["aggregates"]
    conditions = sorted(dict.fromkeys(r["condition"] for r in rows), key=lambda c: (c != "default", c))
    write_table(
        out,
        "table_sensitivity",
        [
            "condition",
            "policy",
            "interventions",
            "harm",
            "harm_ci_low",
            "harm_ci_high",
            "missed_rate",
            "unnecessary_rate",
        ],
        [
            [
                r["condition"],
                r["policy"],
                r["interventions"],
                r["harm"],
                *ci(r, "harm"),
                r["missed_rate"],
                r["unnecessary_rate"],
            ]
            for r in rows
        ],
    )
    cols = 4
    nrows = (len(conditions) + cols - 1) // cols
    fig, axes = plt.subplots(
        nrows, cols, figsize=(13, 3.4 * nrows), sharex=True, sharey=True, constrained_layout=True, squeeze=False
    )
    markers = {"adaptive": "o", "myopic_voi": "^", "rule_based": "s", "always_confirm": "D"}
    for index, (ax, condition) in enumerate(zip(axes.flat, conditions, strict=False)):
        for row in (r for r in rows if r["condition"] == condition):
            color = FAMILY_COLOR.get(row["policy"], GREY) if row["policy"] in ("adaptive", "myopic_voi") else GREY
            marker = markers.get(row["policy"], "o")
            ax.plot(
                [row["interventions"]],
                [row["harm"]],
                linestyle="none",
                marker=marker,
                markersize=7,
                color=color,
                markeredgecolor="white",
                markeredgewidth=1.2,
                zorder=3,
                label=label(row["policy"]) if index == 0 else None,
            )
            low, high = ci(row, "harm")
            if low is not None and high is not None:
                ax.plot([row["interventions"]] * 2, [low, high], color=color, linewidth=1, zorder=2)
        ax.set_title(condition.replace("_", " "), fontsize=9)
        ax.tick_params(labelbottom=True)
        ax.set_xlabel("Interruptions per episode")
    for ax in list(axes.flat)[len(conditions) :]:
        ax.set_visible(False)
    fig.legend(loc="outside upper right", ncols=4, fontsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel("Harm per episode")
    fig.suptitle(
        "Sensitivity to simulator assumptions (policies fixed; the simulated world changes)",
        x=0.0,
        ha="left",
        fontsize=10,
        color=INK,
    )
    save(fig, out, "sensitivity")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--results", type=Path, default=EXPERIMENTS / "results")
    parser.add_argument("--figures", type=Path, default=EXPERIMENTS / "figures")
    args = parser.parse_args()
    args.figures.mkdir(parents=True, exist_ok=True)
    style()
    print(f"[figures] reading {args.results}, writing {args.figures}", file=sys.stderr)
    for fn in (frontier, comparison, decision_mix, timing, reasons, ablation, sensitivity):
        fn(args.results, args.figures)


if __name__ == "__main__":
    main()
