import csv
import io
import json

import pytest

from agentpause_sim import (
    METRICS,
    ExperimentConfig,
    PolicySpec,
    SignalAblation,
    aggregate,
    build_policy,
    metric_catalog,
    paired_comparison,
    rows_to_csv,
    run_experiment,
    write_result,
)
from agentpause_sim.experiment import ConditionSpec
from agentpause_sim.learning import Dataset, auc, fit_logistic, generate_dataset

SMALL = {
    "name": "t",
    "scenarios": ["email", "files"],
    "episodes": 6,
    "seed": 99,
    "bootstrap": 50,
    "policies": [
        "full_autonomy",
        "always_confirm",
        {"name": "adaptive"},
        {"name": "adaptive", "ablate": ["recoverability"]},
    ],
}


@pytest.fixture(scope="module")
def result():
    return run_experiment(ExperimentConfig.from_dict(SMALL))


def test_config_parsing_and_validation(tmp_path):
    cfg = ExperimentConfig.from_dict(SMALL)
    assert cfg.total_episodes == 2 * 4 * 6
    assert [p.key for p in cfg.policies][-1] == "adaptive-no_recoverability"
    toml = tmp_path / "c.toml"
    toml.write_text('name = "x"\nepisodes = 2\n[[policies]]\nname = "adaptive"\n')
    assert ExperimentConfig.from_file(toml).episodes == 2
    with pytest.raises(ValueError):
        ExperimentConfig.from_dict({"name": "x", "policies": []})
    with pytest.raises(ValueError):
        ExperimentConfig.from_dict({**SMALL, "episodes": 0})
    with pytest.raises(KeyError):
        ExperimentConfig.from_dict({**SMALL, "scenarios": ["atlantis"]})


def test_results_are_reproducible(result):
    again = run_experiment(ExperimentConfig.from_dict(SMALL))
    assert again.result_hash == result.result_hash
    different = run_experiment(ExperimentConfig.from_dict({**SMALL, "seed": 100}))
    assert different.result_hash != result.result_hash


def test_aggregates_cover_every_policy_and_metric(result):
    policies = {row["policy"] for row in result.aggregates}
    assert policies == {"full_autonomy", "always_confirm", "adaptive", "adaptive-no_recoverability"}
    row = next(r for r in result.aggregates if r["policy"] == "always_confirm")
    for metric in METRICS:
        assert metric.key in row
    lo, hi = row["interventions_ci"]
    assert lo <= row["interventions"] <= hi
    autonomy = next(r for r in result.aggregates if r["policy"] == "full_autonomy")
    assert autonomy["interventions"] < row["interventions"]
    assert autonomy["unnecessary_rate"] is None or autonomy["unnecessary_rate"] == 0


def test_paired_comparisons_use_identical_seeds(result):
    comps = [c for c in result.comparisons if c["baseline"] == "always_confirm"]
    assert comps and comps[0]["pairs"] == 2 * 6
    diff = comps[0]["interventions"]["mean_diff"]
    assert diff < 0, "adaptive interrupts less than always-confirm"


def test_rate_metrics_are_pooled(result):
    rows = [s for s in result.summaries if s.policy == "always_confirm"]
    pooled = aggregate(rows, n_boot=0)[0]["unnecessary_rate"]
    assert pooled == pytest.approx(sum(r.unnecessary for r in rows) / sum(r.interventions for r in rows))


def test_export(tmp_path, result):
    paths = write_result(result, tmp_path / "out")
    reader = list(csv.DictReader(io.StringIO(paths["records"].read_text())))
    assert reader and {
        "participant_id",
        "scenario",
        "policy",
        "decision",
        "decision_latency_ms",
        "task_success",
    } <= set(reader[0])
    assert all(r["participant_id"].startswith("sim-") for r in reader)
    summary = json.loads(paths["summary"].read_text())
    assert summary["note"].startswith("SIMULATED")
    assert "records" not in summary
    assert rows_to_csv([]).strip()


def test_ablation_wrapper():
    policy = build_policy(PolicySpec("adaptive", ablate=("intent", "plan")), ConditionSpec())
    assert isinstance(policy, SignalAblation)
    assert policy.name == "adaptive-no_intent+plan"
    with pytest.raises(ValueError):
        SignalAblation(policy.base, ["telepathy"])


def test_conditions_change_the_simulated_world():
    cfg = ExperimentConfig.from_dict(
        {
            "name": "c",
            "scenarios": ["email"],
            "episodes": 8,
            "seed": 3,
            "bootstrap": 0,
            "policies": ["always_confirm"],
            "conditions": [
                {"name": "careful"},
                {"name": "careless", "user": {"approval_vigilance": 0.0, "clarification_accuracy": 0.0}},
            ],
        }
    )
    res = run_experiment(cfg)
    by = {r["condition"]: r for r in res.aggregates}
    assert by["careless"]["recovery_rate"] <= by["careful"]["recovery_rate"]


def test_metric_catalog_and_pairing_helper(result):
    assert {m["key"] for m in metric_catalog()} == {m.key for m in METRICS}
    assert paired_comparison(result.summaries, baseline="nope", treatment="adaptive") == []


# ------------------------------------------------------------------ learning
def test_auc_matches_known_values():
    assert auc([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1]) == pytest.approx(0.75)
    assert auc([1, 2, 3], [0, 0, 0]) is None
    assert auc([0.5, 0.5], [0, 1]) == pytest.approx(0.5)


def test_logistic_fit_separates_toy_data():
    x = [[i / 10, 0.0] for i in range(10)] * 3
    y = [int(row[0] > 0.45) for row in x]
    model = fit_logistic(Dataset([r + [0.0] * 9 for r in x], y, ["s"] * len(y)), iterations=300)
    scores = [model.predict(r + [0.0] * 9) for r in x]
    assert auc(scores, y) == pytest.approx(1.0)


def test_dataset_generation_is_aligned_and_labelled():
    data = generate_dataset(seed=5, episodes=2, scenarios=["email"])
    assert len(data.features) == len(data.labels) == len(data.scenarios)
    assert set(data.labels) <= {0, 1}
    assert len(data.features[0]) == 11
