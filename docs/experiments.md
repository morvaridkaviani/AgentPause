# Experiments, simulation, and the human-study mode

This page covers the simulator (`simulator/src/agentpause_sim`), the experiment configs and
scripts (`experiments/`), reproducibility, and the human-study mode of the backend.

> **Simulated results are not evidence about people.** The simulator compares policies
> under stated, scripted assumptions. Every result file and printed table is labelled
> "SIMULATED RESULTS. Not evaluated with human participants." No human-participant study has
> been run yet.

Contents:

- [Scenarios](#scenarios)
- [Ground truth and error injection](#ground-truth-and-error-injection)
- [Simulated agent](#simulated-agent)
- [Simulated user](#simulated-user)
- [Metrics](#metrics)
- [Experiment configs](#experiment-configs)
- [Scripts and outputs](#scripts-and-outputs)
- [Reproducibility](#reproducibility)
- [Human-study mode](#human-study-mode)
- [Questionnaire instruments](#questionnaire-instruments)
- [Ethics checklist](#ethics-checklist)
- [Power analysis](#power-analysis)

## Scenarios

A scenario is a scripted task. It has a user instruction, the **intent assumptions** the
agent has to make, a sequence of **steps**, and **mistakes** that can be injected. Every
action is simulated. Six scenarios are bundled (`agentpause-sim scenarios`,
`GET /api/v1/scenarios`):

| Id | Name | Steps | Assumptions (kinds) | Mistakes | Hard-to-undo steps (recoverability < 0.5) | Notes |
|---|---|---|---|---|---|---|
| `travel` | Travel booking | 8 | 4 (input, constraint, context) | 4 | `purchase_ticket`, `send_itinerary` | `send_itinerary` is skipped depending on an answer |
| `email` | Email communication | 8 | 3 (input) | 2 | `send_email` | |
| `shopping` | Online shopping | 7 | 3 (input, constraint) | 2 | `place_order` | `verify_payment` requires human input (always BLOCK) |
| `files` | File management | 8 | 3 (input, context) | 2 | `empty_trash` | |
| `calendar` | Calendar scheduling | 7 | 4 (input, context, goal) | 3 | `send_invites`, `share_agenda`, `post_in_channel` | `post_in_channel` is skipped depending on an answer |
| `research` | Research assistant | 7 | 4 (input, goal) | 2 | `send_summary_email` | |

Inspect one scenario with `agentpause-sim show travel` or `GET /api/v1/scenarios/travel`.

### Scenario file format

Scenarios are JSON files in `simulator/src/agentpause_sim/scenarios/`. They are validated
when loaded. Only bundled scenarios can be referenced by id from experiment configs, so add
new scenarios to that folder. `load_scenario_file(path)` loads a file from anywhere for use
in your own code.

| Object | Fields (defaults) |
|---|---|
| Scenario | `id` (required), `name`, `agent_name`, `domain`, `icon`, `goal`, `brief`, `description`, `assumptions`, `steps` (≥ 1), `mistakes`. `brief` and step texts can contain `{assumption_id}` placeholders |
| Step | `id` (required, unique), `action` (= id), `label`, `description`, `subtask`, `category`, `severity` and `recoverability` (category priors), `agent_confidence` (0.9), `intent_confidence` (0.97, residual ambiguity not attached to an assumption), `depends_on`, `breakpoint` (false), `load` (0.3), `duration_s` (5.0), `consequence`, `undo`, `what_could_go_wrong`, `preview`, `alternatives`, `requires_human_input` (false), `external` (category prior), `skip_if` (`{assumption_id: value}`) |
| Assumption | `id`, `description`, `confidence`, `agent_value`, `alternatives` (≥ 1) are required. Optional: `kind` (`input`), `wrong_probability` (1 − confidence), `introduced_at` (first step), `if_wrong`, `severity` (the harm step's severity) |
| Mistake | `id`, `step`, `description`, `probability` are required. Optional: `severity` and `recoverability` (the harm step's), `visible_at` (`[step]`), `harm_at` (`step`), `preview` (`{step_id: {field: value}}`, card fields that change when the mistake is present) |

Validation rejects a file when:

- a value is outside [0, 1], or a step id is duplicated;
- an assumption has no alternative, is never used, or is used before it is introduced;
- a step refers to an unknown assumption, or a `skip_if` value is not an option;
- a mistake refers to an unknown step, or its `harm_at` comes before its own step.

## Ground truth and error injection

At the start of an episode, the engine samples the ground truth. It depends only on
`(seed, scenario, episode)`:

- **Wrong assumptions.** Each assumption is wrong with probability `wrong_probability`. If
  it is wrong, the user's true value is drawn from `alternatives`, while the agent keeps
  acting on `agent_value`.
  - A wrong assumption causes harm at its **commitment point**: the first dependent step with
    recoverability below 0.5. If there is none, it causes harm at the last dependent step.
  - It is visible to the human from the step that introduces it up to the harm step,
    whenever an intervention asks about it.
- **Mistakes.** Each mistake occurs with its `probability`. It changes the card preview at
  its `visible_at` steps, and causes harm at `harm_at` if it has not been corrected by then.

Every intervention and error is labelled from this ground truth:

| Label | Definition |
|---|---|
| **Necessary intervention** | At that moment, the card showed the human at least one pending error event. A visible mistake counts on cards with an action confirmation (ASK_HUMAN, BLOCK). A wrong assumption counts when the card asks about it, or, for BLOCK, when the step depends on it. A step that requires human input also counts |
| **Unnecessary intervention** | Any other intervention |
| **Caught** | The error was corrected before it caused harm. Mistakes are corrected by `edit`, `takeover`, or a `reject` while visible. Assumptions are corrected by an answer equal to the true value |
| **Harm** | The error reached its harm step uncorrected. Its cost is `C_err(severity, recoverability)` with the default `undo_cost_fraction`, the same yardstick for every policy |
| **Missed intervention** | The error caused harm without ever having been shown |
| **Human miss** (oversight failure) | The error was shown but approved or confirmed anyway, and caused harm |
| **Averted** | The task ended, or was cancelled, before the error caused harm, or the step was skipped |
| **Rework** | Steps executed on a wrong assumption that had to be redone after a late correction. Each redone step adds its duration to the simulated clock. A mistake caught after its own step adds one rework step |
| `error_present` (per decision) | At this step, a pending mistake is visible or the step depends on a wrong assumption |

Scripted ground truth makes comparisons reproducible, but it encodes the scenario authors'
judgement of what is "necessary". Human annotators agree poorly on this (see
[research_gap.md](../research/research_gap.md)).

## Simulated agent

The engine (`EpisodeEngine`) builds the `ActionContext` for each step from the scenario, with
signals tagged `simulated`, `estimated` or `inferred`. It passes the remaining steps as the
`plan` and introduces assumptions at their `introduced_at` step. The agent's reported
confidence depends on the injected mistakes, according to `EngineConfig`:

| `EngineConfig` field | Default | Meaning |
|---|---|---|
| `calibration` | 0.7 | How strongly a mistake made at this step lowers the reported confidence (drop = `calibration × confidence_drop`) |
| `confidence_drop` | 0.3 | Maximum confidence drop |
| `propagated_calibration` | 0.35 | How strongly an earlier mistake that is visible at this step lowers confidence. 0 = the agent never notices upstream mistakes |
| `confidence_noise` | 0.03 | Uniform noise on the reported confidence |
| `max_attempts` | 2 | After more rejections of the same step than this, the user takes over the step (45 s) |
| `commitment_recoverability` | 0.5 | Threshold for commitment points in the ground truth |

The same engine runs batch experiments (with a simulated user) and the interactive demo and
study sessions (with a person). Its state is serializable JSON, so a web session can be
resumed between requests.

```python
from agentpause import AgentPause, ResponseType
from agentpause_sim import (
    ConditionSpec, EpisodeEngine, HumanResponse, PolicySpec, load_scenario, run_episode,
)

# One episode with the simulated user.
engine = run_episode("travel", PolicySpec("adaptive"), ConditionSpec(), seed=314159, episode=0)
print(engine.outcome())
for record in engine.state.records:
    print(record["step_id"], record["decision"], record["intervention"], record["necessary"])

# The same engine driven step by step, with responses supplied by your own code.
engine = EpisodeEngine(load_scenario("email"), AgentPause("adaptive"), seed=1, episode=0)
while not engine.done:
    engine.step()
    if engine.state.status == "awaiting_human":
        card = engine.public_pending()               # ground-truth fields removed
        allowed = card["allowed_responses"]
        choice = "answer" if "answer" in allowed else allowed[0]
        engine.respond(HumanResponse(ResponseType(choice), source="human"))
print(engine.outcome()["status"])
```

After a CLARIFY answer, the agent proposes the same step again with the answers applied.

## Simulated user

`SimulatedUser` answers every card. It is a modelling device for comparing policies under
stated assumptions. It does not stand in for human-participant data.

| `SimulatedUserParams` field | Default | Meaning |
|---|---|---|
| `approval_vigilance` | 0.85 | P(catch a visible mistake on an approval card) when not habituated |
| `clarification_accuracy` | 0.95 | P(correcting a wrong assumption when asked about it) when not habituated |
| `habituation_rate` | 0.12 | `h = 1 − exp(−rate · recent interruptions)` |
| `habituation_effect` | 0.5 | Attention = `1 − effect · h`. It multiplies both probabilities above |
| `habituation_window` | 8 | Steps counted as "recent" |
| `false_reject_rate` | 0.03 | P(rejecting a correct action) |
| `block_override_rate` | 0.7 | When a correct action is blocked: P(override) instead of taking over |
| `base_response_s`, `per_question_s`, `load_response_s` | 4.0, 2.5, 4.0 | Response time = `(base + per_question · max(1, n_questions) + load_response · load) · exp(N(0, response_noise))` |
| `response_noise` | 0.25 | Log-normal noise on response time |
| `edit_s`, `takeover_s` | 10.0, 45.0 | Extra time for an edit or a takeover |

Behaviour per card:

- **Clarifications.** A wrong value is corrected with probability `clarification_accuracy · attention`. Otherwise the shown value is confirmed, which may be a rubber stamp.
- **BLOCK.** The user takes over if the step needs their input or something is wrong; otherwise they override with probability `block_override_rate`.
- **Confirmations.** With a visible mistake, the user edits with probability `approval_vigilance · attention`. Without one, they reject with probability `false_reject_rate`. Otherwise they approve.

The simulated user's habituation parameters can be set **differently** from the adaptive
policy's internal parameters. This tests robustness under model misspecification
(`experiments/configs/sensitivity.toml`).

## Metrics

Formal definitions are in [research/metrics.md](../research/metrics.md). The simulator
computes the metrics in `agentpause_sim.metrics.METRICS`. Each is tagged:

- **objective**: computable from logs;
- **ground_truth**: needs labelled errors;
- **simulated**: a modelling proxy that exists only in simulation.

| Key | Label | Kind |
|---|---|---|
| `task_success` | Task success rate (completed without any harmful error) | ground_truth |
| `task_duration_s` | Task completion time (s, simulated, incl. human response and rework time) | objective |
| `interventions` | Interventions per episode (CLARIFY, ASK_HUMAN, BLOCK cards) | objective |
| `questions` | Questions per episode (a batched card counts each question) | objective |
| `deferrals` | DEFER decisions per episode | objective |
| `unnecessary_rate` | Unnecessary interventions / interventions | ground_truth |
| `missed_rate` | Errors that caused harm without being shown / all errors | ground_truth |
| `recovery_rate` | Errors caught before harm / all errors | ground_truth |
| `harm` | Expected harm per episode (sum of error costs of harmful errors) | ground_truth |
| `human_miss_rate` | Errors shown but approved anyway / errors shown | ground_truth |
| `agent_error_rate` | Injected mistakes plus wrong assumptions per step | ground_truth |
| `human_error_rate` | (Errors approved despite being shown + rejections of correct actions) / responses | ground_truth |
| `override_rate` | Responses that changed the proposal (edit, reject, takeover, override) / responses | objective |
| `acceptance_rate` | Responses that accepted the proposal unchanged / responses | objective |
| `rework_steps` | Executed steps redone after a late correction | ground_truth |
| `decision_latency_ms` | Mean wall-clock time of `AgentPause.evaluate` (machine-dependent) | objective |
| `human_time_s` | Simulated time spent responding | simulated |
| `workload_proxy` | Σ over interventions of `(1 + load) · (1 + 0.5 · (questions − 1))`. **Not** a measure of human workload | simulated |

Aggregation:

- **Aggregates** are computed per `(condition, policy)`. Rates are pooled: the sum of
  numerators over the sum of denominators.
- **Confidence intervals** are 95% percentile bootstrap intervals over episodes, with
  `bootstrap` resamples and the config seed (deterministic).
- **Per-scenario aggregates** have no intervals.
- **Paired comparisons** (`paired_comparison`) give the mean per-episode difference
  *treatment − baseline* on identical `(condition, scenario, seed, episode)` cells, which see
  the same injected errors. They come with a 95% bootstrap interval and the share of pairs
  where the treatment is lower, for `interventions`, `unnecessary`, `missed_interventions`,
  `harm`, `task_duration_s` and `rework_steps`. Here `unnecessary` and
  `missed_interventions` are per-episode counts, not rates. In `run_experiment`, the treatment is the
  policy keyed `adaptive` if present, otherwise the last policy, and it is compared with every
  other policy.

## Experiment configs

An experiment is `scenarios × policies × conditions × episodes`. Configs are TOML or JSON and
are parsed by `ExperimentConfig.from_file` / `from_dict`:

| Key | Type | Default | Meaning |
|---|---|---|---|
| `name` | string | `"experiment"` | Output folder name |
| `description` | string | `""` | Free text |
| `policies` | list (≥ 1) | required | Policy names, or tables (see below) |
| `scenarios` | list or string | `["all"]` | Scenario ids, or `"all"` for the six bundled scenarios |
| `episodes` | int ≥ 1 | 50 | Episodes per scenario × policy × condition |
| `seed` | int | 20261014 | Base seed (20261014 is the development seed; see [Reproducibility](#reproducibility)) |
| `conditions` | list of tables | one `default` condition | Simulated-world settings shared by all policies |
| `explain` | `"none"`, `"light"`, `"full"` | `"none"` | Explanation level during simulation |
| `keep_records` | bool | true | Keep per-decision records |
| `bootstrap` | int | 500 | Bootstrap resamples for confidence intervals (0 disables them) |

Policy table (`[[policies]]`):

| Key | Meaning |
|---|---|
| `name` | Registry name or alias |
| `config` | Policy keyword arguments, e.g. `{ threshold = 0.35 }` |
| `parameters` | `ModelParameters` overrides, e.g. `{ interruption_cost = 0.03 }` |
| `preferences` | `UserPreferences`, e.g. `{ profile = "balanced", ask_before_irreversible = true }` |
| `ablate` | Signals to hide from the policy: `agent_confidence`, `intent`, `severity`, `recoverability`, `at_breakpoint`, `cognitive_load`, `habituation`, `history`, `plan`. Hidden signals fall back to defaults, as for an agent that cannot measure them |
| `label` | Name in the results. Default: the name, or `<name>-no_<signals>` when ablating |

Condition table (`[[conditions]]`):

| Key | Meaning |
|---|---|
| `name` | Condition name |
| `user` | `SimulatedUserParams` overrides |
| `engine` | `EngineConfig` overrides |
| `parameters` | `ModelParameters` overrides applied to every policy (e.g. a misspecified habituation rate). Policy-level `parameters` take precedence |

Example:

```toml
name = "my_experiment"
description = "Adaptive vs. a fixed threshold, with a careless simulated user."
scenarios = ["travel", "email"]
episodes = 100
seed = 314159
bootstrap = 500

[[policies]]
name = "fixed_threshold"
label = "fixed_threshold@0.35"
config = { threshold = 0.35 }

[[policies]]
name = "adaptive"

[[policies]]
name = "adaptive"
ablate = ["plan"]                  # timing lookahead removed

[[conditions]]
name = "default"

[[conditions]]
name = "careless_user"
user = { approval_vigilance = 0.6, clarification_accuracy = 0.8 }
```

Run it with `agentpause-sim run my_experiment.toml` or `python experiments/<script>.py --config my_experiment.toml`.

Bundled configs (`experiments/configs/`). All use seed 314159:

| Config | Policies | Conditions | Episodes | Purpose |
|---|---|---|---|---|
| `baseline.toml` | `full_autonomy`, `always_confirm` | default | 200 | Fixed baselines |
| `fixed_threshold.toml` | `fixed_threshold` at τ = 0.15, 0.25, 0.35, 0.50, 0.65 | default | 200 | Threshold sweep |
| `adaptive.toml` | `myopic_voi`, `adaptive`, `user_customized` labelled `adaptive+irreversible_floor` (`ask_before_irreversible = true`) | default | 200 | Timing ablation (H1b) and a safety-floor variant |
| `compare_policies.toml` | `full_autonomy`, `always_confirm`, `fixed_threshold` (0.35), `rule_based`, `confidence_threshold` (0.8), `myopic_voi`, `adaptive`, `user_customized` (balanced, ask before irreversible), `learned` | default | 200 (bootstrap 1000) | Main comparison (RQ1: H1a, H1b) |
| `frontier.toml` | `full_autonomy`, `always_confirm`, `rule_based`; `adaptive` and `myopic_voi` at `interruption_cost` 0.005–0.08 (7 values each); `fixed_threshold` at τ 0.10–0.50 (5); `confidence_threshold` at τ 0.70–0.90 (4) | default | 150 (no bootstrap) | Harm-vs-interruption frontiers, so that policies are not compared at one cherry-picked operating point |
| `ablation.toml` | `adaptive`, plus `adaptive` with each of the 9 signals hidden | default | 200 | Signal ablation (RQ2, under the simulator's assumptions only) |
| `sensitivity.toml` | `always_confirm`, `rule_based`, `myopic_voi`, `adaptive` | `default`, `uncalibrated_agent`, `unaware_of_upstream_mistakes`, `well_calibrated_agent`, `fast_habituating_user`, `non_habituating_user`, `careless_user` | 150 (bootstrap 300) | Robustness to simulator assumptions and model misspecification. The policies keep their default parameters; only the simulated world changes |

## Scripts and outputs

Run the scripts from the repository root. All `run_*.py` scripts and `compare_policies.py`
accept `--config PATH` (default: their bundled config), `--episodes N` (override, for quick
runs) and `--out DIR` (default: `experiments/results/<name>`). They print a table of
aggregates labelled as simulated, and the paired differences.

| Script | Config | What it does |
|---|---|---|
| `run_baseline.py` | `baseline.toml` | Runs the fixed baselines |
| `run_fixed_threshold.py` | `fixed_threshold.toml` | Runs the threshold sweep |
| `run_adaptive.py` | `adaptive.toml` | Runs adaptive vs. myopic (H1b) |
| `compare_policies.py` | `compare_policies.toml` | Runs the main comparison. Prints point-estimate checks of H1a and H1b and writes them to `hypotheses.json` in the output folder. Read the confidence intervals before drawing conclusions |
| `run_frontier.py` | `frontier.toml` | Runs the frontier sweeps |
| `run_ablation.py` | `ablation.toml` | Runs the signal ablation |
| `run_sensitivity.py` | `sensitivity.toml` | Runs the sensitivity conditions |
| `train_learned_policy.py` | — | Trains the experimental learned policy (see [policies.md](policies.md#learned-experimental)). Writes `sdk/python/src/agentpause/policies/learned_weights.json` and `experiments/results/learned_policy/report.json` |
| `generate_figures.py [--results DIR] [--figures DIR]` | — | Reads `<results>/<experiment>/summary.json` (and `compare_policies/records.csv`), and writes PNG and PDF figures plus a CSV table per figure to `<figures>`. The defaults are `experiments/results` and `experiments/figures`. Experiments that have not been run are skipped. Needs matplotlib (`pip install -e "simulator[figures]"`). See [Figures](#figures) |
| `reproduce_all.py [--quick]` | all | Trains the learned policy, runs every config (and writes `hypotheses.json` for `compare_policies`), generates the figures, and writes the result hashes to `hashes.json` in the results folder. `--quick` uses 20 episodes per cell and writes to `experiments/results/quick` and `experiments/figures/quick` |
| `../scripts/check_reproducibility.py [--quick] [--only NAME ...]` | all or a subset | Re-runs configs in a temporary directory and compares their hashes with the committed reference (see [Reproducibility](#reproducibility)) |

The Makefile wraps the most common runs: `make experiments` (`reproduce_all.py`),
`make experiments-quick`, `make figures` and `make check-repro`.

### Outputs

Each run writes four files to its output folder:

- **`records.csv`**: one row per decision. Columns: `participant_id` (`sim-0000`…),
  `scenario`, `policy`, `condition`, `seed`, `episode`, `step_index`, `attempt`, `step_id`,
  `action`, `category`, `decision`, `score`, `decision_confidence`, `reason_codes`,
  `intervention`, `necessary`, `error_present`, `n_questions`, `n_deferred`, `severity`,
  `recoverability`, `agent_confidence`, `intent_confidence`, `cognitive_load`,
  `external_effects`, `at_breakpoint`, `task_progress`, `habituation`,
  `decision_latency_ms`, `sim_time_s`, `user_response`, `response_time_s`, `task_success`,
  `task_duration_s`, `subjective_rating` (always empty in simulation).
- **`episodes.csv`**: one row per episode, with the counts behind every metric
  (interventions, confirmations, clarifications, blocks, deferrals, questions, batched
  interventions, necessary/unnecessary, error counts by status, responses, overrides, rework,
  harm, durations, workload proxy) and the per-episode rates.
- **`summary.json`**: the config, `aggregates` with confidence intervals, `by_scenario`,
  paired `comparisons`, `duration_s`, `result_hash`, and the simulated-results `note`.
- **`config.json`**: the fully resolved config.

The `experiments/results/` and `experiments/figures/` folders are git-ignored, except for
their `reference/` subfolders. Those hold the committed reference outputs:

- `experiments/results/reference/<experiment>/` contains `config.json` and `summary.json`
  (and `hypotheses.json` for `compare_policies`). It does not contain the per-decision CSVs.
- `experiments/results/reference/` also contains `hashes.json`, `hashes_quick.json` and the
  learned-policy report.
- `experiments/figures/reference/` contains the reference figures and tables.

### Figures

`generate_figures.py` produces these files. Each figure comes with a CSV table holding the
same numbers:

| File | Source | Shows |
|---|---|---|
| `frontier_harm.png`, `frontier_missed.png` (`table_frontier.csv`) | `frontier` | Harm, and missed-intervention rate, against interruptions per episode. One point per parameter value; the default is ringed |
| `compare_policies.png` (`table_compare_policies.csv`, `table_paired_differences.csv`) | `compare_policies` | Interruptions, unnecessary rate, missed rate, harm, rework and task time per policy, as means with 95% bootstrap intervals; paired differences |
| `decision_mix.png` (`table_decision_mix.csv`) | `compare_policies/records.csv` | Share of decisions by type per policy |
| `timing.png` (`table_timing.csv`) | `compare_policies/records.csv` | Interruptions per episode by task-progress quarter, for `always_confirm`, `rule_based`, `myopic_voi` and `adaptive` |
| `reasons_adaptive.png` (`table_reasons_adaptive.csv`) | `compare_policies/records.csv` | Reason codes behind the adaptive policy's non-CONTINUE decisions |
| `ablation.png` (`table_ablation.csv`) | `ablation` | Change in each metric when one signal is hidden, relative to the full adaptive policy |
| `sensitivity.png` (`table_sensitivity.csv`) | `sensitivity` | Harm against interruptions per policy, for each simulated-world condition |

The figures follow a few design rules:

- one y-axis per chart;
- at most three hues per line chart, with direct labels;
- a policy family keeps the same colour across figures: adaptive is blue, myopic value of
  asking orange, fixed threshold aqua, confidence threshold yellow, and each family also has
  its own marker shape;
- reference policies are grey and labelled with text;
- every figure carries the label "SIMULATED results; not evaluated with human participants."

## Reproducibility

- **Deterministic policies.** Policies use no randomness or wall-clock time. The explainer's
  stability estimate uses a fixed seed.
- **Deterministic simulation.**
  - Every random draw comes from a stream derived with SHA-256 from a key, for example
    `(seed, scenario, episode, "mistake", id)` or `(seed, scenario, episode, "confidence",
    step, attempt)`. A draw does not depend on how many other draws happened before it.
  - An episode is therefore a pure function of: the scenario, the policy configuration, the
    seed, the episode index, the simulated-user parameters, and the engine configuration.
- **Common random numbers.** Injected mistakes and wrong assumptions depend only on
  `(seed, scenario, episode)`, so every policy faces the same errors. This is what makes the
  paired comparisons valid.
- **Result hash.** `result_hash` is a SHA-256 over all episode summaries and records,
  excluding `decision_latency_ms`, which is the only machine-dependent field in them. The run
  time `duration_s` is not hashed either. Running the same config with the same code gives
  the same hash, so a different hash means that the code, the scenarios or the config
  differ.
- **`experiments/reproduce_all.py`** re-runs everything in a fixed order and writes all
  hashes to `experiments/results/hashes.json` (or `experiments/results/quick/hashes.json`
  with `--quick`):
  1. train the learned policy;
  2. run `baseline`, `fixed_threshold`, `adaptive`, `compare_policies`, `frontier`,
     `ablation`, `sensitivity`;
  3. generate the figures.

  Hashes from `--quick` runs differ from full runs, because the episode counts differ.
- **`scripts/check_reproducibility.py`** re-runs the configs in a temporary directory, so
  committed results are not touched. It compares each result hash with
  `experiments/results/reference/hashes.json` (or `hashes_quick.json` with `--quick`), and
  prints `OK` or `MISMATCH` per experiment.
  - `--only NAME ...` restricts it to a subset.
  - The exit code is 0 if every hash matches, 1 on a mismatch, and 2 if the reference file is
    missing.
  - A mismatch points to local changes, or to different Python or package versions.
- **Development and evaluation seeds.**
  - The default seed in `ExperimentConfig` (20261014) is the **development** seed. It was
    used while designing the policies and choosing default parameters such as
    `interruption_cost = 0.02`.
  - All bundled configs use the held-out **evaluation** seed 314159. Do not tune anything on
    it.
  - The learned policy trains on seed 1001 and is tested on seed 2002.
  - Study sessions use `seed_base + 100 · participant number + block position`.
- **Versioned inputs.** Configs (`experiments/configs/`), scenarios (bundled JSON) and model
  defaults (`ModelParameters`) are part of the repository. `GET /api/v1/model` reports the
  defaults of a running server.

## Human-study mode

The backend includes a study mode for running the same scenarios with real participants. It
implements the design in [research_questions.md](../research/research_questions.md) (§3–5).
**It has not yet been used to collect data.**

### Design

- **Policy** is a within-subjects factor. Each participant gets one block per condition in
  `StudyConfig.conditions` (default: `full_autonomy`, `always_confirm`, `fixed_threshold`,
  `adaptive`, i.e. conditions A–D).
- **Order** is counterbalanced with a balanced Latin square (Williams 1949). For an even
  number of conditions, each condition precedes every other equally often across the n rows.
  For an odd number, the mirrored rows are appended (2n rows). Participant index
  i = k − 1 (k = participant number) uses row `i mod rows`; write `cycle = i div rows`.
- **Practice.** A practice block comes first, using `practice_scenario` (default `files`)
  under `always_confirm`. It is marked `practice: true` and should be excluded from analysis.
- **Scenarios** rotate across blocks. The scenario for block position p is
  `scenarios[(p + cycle) mod len(scenarios)]`. Within every run of `rows` consecutive
  participants each policy meets each scenario equally often (exactly once when there are as
  many scenarios as conditions), and the offset shifts every run, so scenarios are not tied to
  block positions.
- **Seeds**: block seeds are `seed_base + 100 · k + p`, so injected errors are reproducible
  per participant and block.
- **Explanation condition** is a between-subjects factor:
  `explanation_modes[(i mod rows + cycle) mod len(explanation_modes)]`. Consecutive
  participants rotate through the modes, and each mode receives every condition order once
  every `rows × modes` participants (16 with the defaults), so order is crossed with, not
  confounded with, explanation type. The default has four modes (none, placebo, factors,
  full), matching research_questions.md §3.1.
- **Embedded problematic actions** are the scenarios' injected mistakes and wrong
  assumptions, so oversight effectiveness can be scored objectively from the logs.

> **Check the plans before collecting data.** Enrol test participants
> (`POST /api/v1/study/participants`) and inspect their `plan`s for your configuration.
> `backend/tests/test_api_study.py` checks the balance properties above for the default
> configuration.

### Explanation conditions

The participant's explanation mode controls what the study API returns for each decision
(`present_decision` in `backend/app/services/common.py`). The full decision is still
stored for analysis.

| Mode | Participant sees |
|---|---|
| `full` | Everything: narrative explanation, reason codes, factors, feature counterfactuals, timing explanation ("why now / why not earlier / why not later") |
| `factors` | Narrative explanation, reason codes, factors and feature counterfactuals. The timing explanation and timing counterfactuals are removed. The response still contains `terms` and `item_timings`, which the web app does not display |
| `placebo` | Only a content-free justification on cards that ask: "AgentPause paused here because it needs your input before continuing." This is the placebic control after Eiband et al. (2019). No reasons, factors, counterfactuals or timing |
| `none` | No explanation at all |

In study mode, ground-truth fields (`necessary`, `error_present`, `shown_errors`, `harm`,
`wrong_basis`) are removed from everything the participant can fetch. Session outcomes are
reduced to status and duration.

### Flow

The participant pages (`/study`) and the researcher page (`/study/admin`) of the web app
implement this flow. The API calls are listed in [api.md](api.md#study-mode).

1. The researcher configures the study (`PUT /study/config`, token) and sets
   `AGENTPAUSE_ADMIN_TOKEN` on the server.
2. The participant is enrolled (`POST /study/participants`) and receives a random code.
3. Consent is recorded (`PATCH /study/participants/{code}` with `{"consented": true}`).
   Blocks cannot start before this (403).
4. For each block, the participant starts a session (`POST /study/sessions`) and works
   through it (`POST /session/{id}/step`, `POST /intervention`). Response times are measured
   on the server.
5. After each block, the participant answers the post-task instruments, and at the end the
   final instruments (`POST /study/responses`).
6. Completion is recorded (`PATCH ... {"completed": true}`).
7. The researcher exports the data: `GET /study/export`, `GET /events?format=csv`, and
   `GET /metrics?source=sessions&mode=study`.

## Questionnaire instruments

Instrument definitions live in `backend/app/instruments/*.json`. Each one records its
citation, DOI or source, license, whether it may be redistributed, whether it is validated,
its scale, and its scoring method. Item text is bundled **only** where the license allows
redistribution.

| Id | Instrument | When | Scale | Scoring | Item text bundled | License (as recorded in the definition) | Validated |
|---|---|---|---|---|---|---|---|
| `agentpause_post_task` | AgentPause post-task probe (7 single items: control, timing, earlier/later, annoyance, understanding, trust, responsibility) | post-task | Likert 1–7 | Mean and per-item subscales; `earlier_later` and `annoyance` reverse-coded | Yes | MIT (written for this project) | **No**: ad-hoc items for piloting and manipulation checks |
| `nasa_tlx_raw` | NASA Task Load Index, Raw TLX (Hart & Staveland 1988; Hart 2006) | post-task | Slider 0–100, step 5 | Unweighted mean of the 6 subscales | Yes | NASA states the TLX is "open source" and may be used and modified without permission; no endorsement implied | Yes |
| `timing_comprehension` | Intervention-timing comprehension check (H4) | final | Multiple choice | Number correct and accuracy | Yes (4 example items) | MIT (written for this project) | **No**: adapt to your conditions and pre-register |
| `sus` | System Usability Scale (Brooke 1996) | post-task | Likert 1–5 | SUS: odd items score − 1, even items 5 − score, sum × 2.5; needs all 10 items (`q1`…`q10`) | **No** | Free to use with acknowledgement of the source; form © Digital Equipment Corporation 1986. Item text is not bundled | Yes |
| `koerber_tia` | Trust in Automation (Körber 2019) | post-task | Likert 1–5 | Mean and subscales; items 5, 7, 10, 15, 16 reverse-coded (mark them in your local file) | **No** | CC BY-SA 4.0 per the author's repository. Not bundled, to keep ShareAlike material out of the MIT code tree. The English version is not yet validated | Yes |
| `hoffman_explanation_satisfaction` | Explanation Satisfaction Scale (Hoffman et al. 2023) | final | Likert 1–5 | Mean | **No** | CC BY 4.0 (2023 article). Use the 2023 wording and check the item count in the article (Table 3) | Yes |
| `jian_trust` | Trust between People and Automation (Jian, Bisantz & Drury 2000) | post-task | Likert 1–7 | Mean | **No** | No reuse license found; reference only. Obtain the items from the original publication | Yes |

Licensing notes are the project's reading of the sources at the time of the review (see
[prior_art.md](../research/prior_art.md), §2.10). They are not legal advice. Check the terms
yourself before use.

An instrument without item text has `ready: false` in `GET /study/instruments`, and
responses to it are rejected (409). The default study configuration uses only bundled
instruments: `agentpause_post_task` and `nasa_tlx_raw` after each block, and
`timing_comprehension` at the end. Report the two project-written instruments as
non-validated, and pair them with a validated instrument of your choice.

### Supplying licensed items (`INSTRUMENTS_LOCAL_DIR`)

For instruments you are entitled to use but that are not bundled:

1. Create a folder **outside the repository**, or make sure it is git-ignored, so that the
   item text is never committed.
2. Add one file per instrument, named `<instrument_id>.json`, containing an `items` list.
   Only `items` is read from this file; everything else comes from the bundled definition.
3. Start the backend with `INSTRUMENTS_LOCAL_DIR=/path/to/folder`. The instrument then reports
   `items_source: "local"` and `ready: true`.

Item fields:

- `id` (required) and `text`;
- for mean scoring, optionally `reverse: true` and `subscale`;
- for choice items, `options` and `correct`;
- for SUS, the ids must be `q1` to `q10`.

```json
{
  "items": [
    {"id": "q1", "text": "<item 1 text from your licensed copy>"},
    {"id": "q2", "text": "<item 2 text from your licensed copy>"}
  ]
}
```

Responses outside the instrument's scale are rejected (422).

## Ethics checklist

Before collecting data with the study mode:

- [ ] **Approval.** Obtain approval from your institution's ethics committee or IRB. The
  study mode implements a protocol; it does not replace review.
- [ ] **Pre-registration.** Pre-register hypotheses (H1c–H6), primary outcomes,
  non-inferiority margins, exclusion criteria, the analysis plan, and the sample size.
- [ ] **Consent.** Adapt `consent_text` to your approved wording. The API refuses to start
  blocks before consent is recorded. Make sure participants can stop at any time.
- [ ] **Deception and debriefing.** The scenarios contain scripted errors, and one condition
  shows placebic reasons. Debrief participants about both.
- [ ] **Simulation only.** All agent actions are simulated. Do not connect the study to real
  email, payment, file or calendar systems.
- [ ] **No personal data.** Participants are identified only by random codes. Do not add
  fields that collect names or contact details. If you need a link to payment or recruitment
  records, keep it outside AgentPause.
  - The database stores no IP addresses, but Uvicorn's access log prints client addresses to
    the console. Run it with `--no-access-log`, or handle those logs under your
    data-protection plan.
- [ ] **Access control.** Set `AGENTPAUSE_ADMIN_TOKEN`, serve over HTTPS (for example behind
  a reverse proxy), and restrict `CORS_ORIGINS`.
- [ ] **Retention and withdrawal.** Define how long data are kept and how a participant's data
  are deleted on request. `DELETE /session/{id}` deletes sessions. There is no endpoint for
  deleting participants or questionnaire responses; remove them in the database.
- [ ] **Instruments.** Use only instruments you are licensed to use. Report non-validated
  items as such.
- [ ] **Burden.** Pilot the session length. Each block is a full scenario plus
  questionnaires.
- [ ] **Reporting.** Report simulated results and human results separately, and label
  simulated results as such.

## Power analysis

There are no pilot data yet, so this documentation does not assume any effect sizes. Plan
the sample size with the procedure below.

**Procedure.**

1. **Fix the primary outcome of each hypothesis** before any data are collected. For example:
   - perceived control for H1c;
   - workload for H3a;
   - catch rate of embedded problematic actions for H3b;
   - comprehension accuracy for H4.
2. **Fix the smallest effect size of interest** (SESOI), or the non-inferiority margin for
   H1c, preferably on substantive grounds. If it has to be informed by the pilot, treat the
   pilot's observed effect as highly uncertain and use a conservative value, such as the
   lower confidence bound. Pilot effect estimates are imprecise and, when studies are
   selected for promising pilots, biased upward.
3. **Run a pilot** with the study mode, and export `GET /study/export` and
   `GET /events?format=csv`. From it, estimate only nuisance parameters:
   - the outcome's standard deviation;
   - the correlation between a participant's scores under two conditions (ρ);
   - for binary outcomes, the baseline rate and the between-participant variance.

   Use a conservative value, such as the upper confidence limit of the pilot SD.
4. **Compute n** with the formulas below, or by simulation for mixed models.
5. **Round up** so that counterbalancing is complete: a multiple of the number of
   Latin-square rows, and of the number of explanation modes (see the counterbalancing note
   above). Then add the expected attrition and exclusions.

**Formulas** (normal approximation; use exact t-based tools such as G\*Power or
`statsmodels.stats.power` for the final number):

```text
Within-subjects comparison of two policies (paired):
  d_z = δ / σ_diff,     σ_diff = σ · sqrt(2 · (1 − ρ))
  n   ≈ ((z_{1−α/2} + z_{1−β}) / d_z)²  +  z_{1−α/2}² / 2

Non-inferiority, paired (H1c: adaptive not worse than always_confirm by more than margin M > 0):
  n   ≈ ((z_{1−α} + z_{1−β}) · σ_diff / (δ + M))²        δ = assumed true difference (often 0)

Between-subjects comparison of two explanation conditions (H4), per group:
  n_g ≈ 2 · ((z_{1−α/2} + z_{1−β}) / d)²,   d = δ / σ
  With m planned contrasts, replace α by α/m (Bonferroni) or plan for Holm.
```

- **Binary outcomes and mixed models.** Each participant meets only a few embedded
  problematic actions per block, so catch-rate outcomes (H3b) are best analysed with a
  mixed-effects logistic model (random intercepts for participant, and possibly scenario).
  For such models, estimate power by simulation: generate data from the pilot's variance
  components and the SESOI, fit the planned model, and count rejections.
- **Context.** Comparable within-subjects studies used N = 48 (Zhou et al., CHI 2026;
  Chen et al. 2026; see [prior_art.md](../research/prior_art.md)). That number is not a
  power calculation for this design.
- **Simulation.** Power is not a concern for simulation experiments. Increasing `episodes`
  only reduces Monte Carlo error, which the bootstrap intervals show.
