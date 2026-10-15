# Experiments

Scripts and configurations for the **simulated** experiments. They produce every number and
figure in `research/paper_draft.md`. None of these results come from people: **not yet
evaluated with human participants.**

## Quick start

From the repository root, with the Python packages installed (`pip install -r requirements-dev.txt`):

```bash
python experiments/reproduce_all.py --quick   # about 1 minute: 20 episodes per cell → results/quick, figures/quick
python experiments/reproduce_all.py           # a few minutes: the full configs → results/, figures/
python scripts/check_reproducibility.py       # re-run and compare hashes with results/reference
```

## Scripts

| Script | Config | What it answers |
|---|---|---|
| `run_baseline.py` | `configs/baseline.toml` | Never-ask and always-confirm reference points |
| `run_fixed_threshold.py` | `configs/fixed_threshold.toml` | Fixed risk threshold at several τ |
| `run_adaptive.py` | `configs/adaptive.toml` | Adaptive vs the same model without timing (`myopic_voi`, H1b), plus a variant with an always-ask-before-irreversible floor |
| `compare_policies.py` | `configs/compare_policies.toml` | All nine policies, paired comparisons, hypothesis checks (`hypotheses.json`) |
| `run_frontier.py` | `configs/frontier.toml` | Harm–interruption frontiers for every parameterized policy |
| `run_ablation.py` | `configs/ablation.toml` | RQ2: hide one signal at a time |
| `run_sensitivity.py` | `configs/sensitivity.toml` | Robustness to simulator assumptions (calibration, habituation, careless users) |
| `train_learned_policy.py` | — | Trains the experimental learned policy on separate seeds; writes `learned_policy/report.json` and the SDK's `learned_weights.json` |
| `generate_figures.py` | — | Figures (PNG + PDF) and CSV tables from the results |
| `reproduce_all.py` | — | Runs everything above in order and writes `hashes.json` |

Every script accepts `--episodes N` (a smaller run), `--config PATH`, and `--out DIR`.

## Outputs

Each run writes `results/<name>/`:

- `summary.json`: aggregates with 95% bootstrap CIs, per-scenario aggregates, paired comparisons, and the result hash;
- `episodes.csv`: one row per episode;
- `records.csv`: one row per decision, with signals, decision, ground truth, and the simulated response;
- `config.json`: the exact configuration.

`results/` and `figures/` are not committed except `reference/`. The reference copies hold the
summaries, configs, hypothesis checks, learned-policy report, hashes (full and quick), and the
figures and tables used in the paper draft.

## Seeds and held-out evaluation

- **Development seed `20261014`.** All policy design decisions and default parameters (e.g. the interruption cost `c₀ = 0.02`) were chosen on this seed.
- **Held-out seed `314159`.** Every reported result uses it. It was not used during development.
- **Learned policy.** Trained on seed `1001` and tested on seed `2002`.

All policies face identical episodes for a given seed (common random numbers). Comparisons are
therefore paired, and their intervals come from a bootstrap over pairs.

## Configuration format

```toml
name = "my_experiment"
description = "What this tests"
scenarios = ["all"]            # or ["travel", "email", ...]
episodes = 100                 # per scenario × policy × condition
seed = 314159
bootstrap = 500                # resamples for CIs (0 = off)

[[policies]]
name = "adaptive"              # registry name or alias
label = "adaptive@0.03"        # optional display name
parameters = { interruption_cost = 0.03 }   # ModelParameters overrides
# config = { ... }             # policy constructor options (e.g. threshold for fixed_threshold)
# preferences = { profile = "balanced", ask_before_irreversible = true }   # for user_customized
# ablate = ["intent"]          # hide signals (see agentpause_sim.ablation.ABLATABLE)

[[conditions]]                 # optional; default: one condition named "default"
name = "fast_habituating_user"
user = { habituation_rate = 0.35 }          # SimulatedUserParams overrides
engine = { calibration = 0.0 }              # EngineConfig overrides
# parameters = { ... }                      # ModelParameters overrides applied to every policy
```

The same format is accepted by `POST /api/v1/experiments` (JSON) and by the experiment runner
page in the web app.

## Reading the figures

Figures follow the same conventions throughout:

- **Colour follows the policy:** adaptive is blue, myopic value of asking orange, fixed threshold aqua, confidence threshold yellow, and reference policies grey with text labels.
- **Second encoding:** marker shapes identify policies without colour.
- **One y-axis per chart.**
- **Tables:** every figure has a CSV table with the same numbers (`figures/table_*.csv`).
- **Label:** every figure carries a "SIMULATED" note.

## Caveats

- The simulated user and the adaptive policy share functional forms (for example habituation). The sensitivity analysis varies these, and the conclusions change (see the paper draft §6.5).
- Ground truth ("necessary" interventions) is scripted by the scenario authors.
- Decision latency depends on the machine, so it is excluded from result hashes.
