# Research Questions, Hypotheses, and Variables

This document turns the research gap ([research_gap.md](research_gap.md)) into testable questions.
Metric definitions are in [metrics.md](metrics.md). Each question is marked as answerable
**in simulation**, **with human participants**, or both. **No human-participant study has been
run yet.**

## 1. Research questions

The candidate questions from the project brief were revised after the literature review. Prior
work already shows that adaptive asking *in general* can beat fixed strategies (Dong et al. 2026;
Zhou et al. CHI 2026; Huq et al. 2026). The questions below therefore isolate what is still
open: **timing within a trajectory**, **explanations of timing**, and **human outcomes** of
both.

**RQ1: Timing (primary).** Compare a *trajectory-aware* policy, which decides *when* to involve
the human (ask now / defer to a breakpoint and batch / never), against:

- fixed strategies: never ask, always confirm, and a fixed risk threshold;
- a *myopic* expected-value policy, which only decides *whether* to ask at the current step.

Does the trajectory-aware policy reduce unnecessary interruptions without increasing missed
interventions or harm?
*Simulation (RQ1a, RQ1b) and human study (RQ1c).*

**RQ2: Signals.** Which contextual signals carry the value of the intervention decision?

- In simulation (ablation): how much does removing each signal (agent confidence, intent
  confidence, severity, reversibility, breakpoint structure, cognitive load, habituation,
  history) degrade the harm–interruption trade-off?
- With human data: which logged signals predict that an intervention was actually needed?

*Caveat: simulation can only show how much a signal matters **under the simulator's
assumptions**. Fitting a model to simulator output recovers those assumptions, which is
circular. RQ2 needs human data to answer substantively.*

**RQ3: Human outcomes.** How does adaptive timing affect participants? The outcomes measured are:

- perceived control and sense of agency;
- trust;
- workload;
- **oversight effectiveness** (whether participants catch injected problematic actions);
- task time.

*Human study only.*

**RQ4: Understanding.** Can users correctly explain why AgentPause interrupted, and why
*at that moment*? Do counterfactual timing explanations ("why not earlier / later") improve
this understanding over factor-only explanations?
*Human study only.*

**RQ5: Acceptance without over-reliance.** Do timing explanations increase acceptance of agent
autonomy (fewer overrides of correct CONTINUE/DEFER decisions, more willingness to delegate)
*without* increasing approval of erroneous actions?
*Human study only.*

**RQ6: User customization (secondary).** Do user-authored autonomy preferences reduce
interruptions relative to the adaptive default, and what does that cost in oversight
effectiveness? This is a replication target for the "preference–commitment gap" reported by
Yan (2026).
*Simulation (with scripted preference profiles) and human study.*

## 2. Hypotheses

All hypotheses are directional and should be pre-registered before any human data collection.
Simulation hypotheses are tested on held-out seeds that were not used during policy development
(see `experiments/README.md`).

| ID | Hypothesis | Test setting |
|---|---|---|
| H1a | ADAPTIVE has a lower unnecessary-intervention rate than ALWAYS_CONFIRM and FIXED_THRESHOLD, with a missed-intervention rate that is not higher than FIXED_THRESHOLD | Simulation, paired over seeds |
| H1b | ADAPTIVE (timing-aware) reaches equal or lower expected harm than MYOPIC_VOI with fewer interruption episodes. Batching combines questions, and DEFER avoids interrupting mid-subtask. This **isolates the timing contribution** | Simulation, paired over seeds |
| H1c | Perceived control under ADAPTIVE is non-inferior to ALWAYS_CONFIRM (margin pre-registered) and higher than FULL_AUTONOMY | Human study |
| H2 | Removing *reversibility* or *intent confidence* degrades the harm–interruption frontier more than removing other signals | Simulation ablation (prediction, not a finding) |
| H3a | Workload is lower under ADAPTIVE than under ALWAYS_CONFIRM | Human study |
| H3b | The catch rate of injected problematic actions is **higher** under ADAPTIVE than under ALWAYS_CONFIRM, because always-confirm habituates users | Human study |
| H4 | Comprehension accuracy is higher with factor + timing-counterfactual explanations than with factor-only explanations, which in turn is higher than no explanation and than placebic reasons. *Risk: why-not formats lowered understanding in Lim et al. 2009. The UI therefore leads with "why now" and shows "why not earlier/later" second* | Human study |
| H5 | With timing explanations, the override rate on correct CONTINUE/DEFER decisions drops, while the approval rate of erroneous actions does not rise. Measured as appropriate reliance: relative AI reliance and relative self-reliance (RAIR/RSR), after Schemmer et al. 2023 | Human study |
| H6 | User-customized profiles reduce interruptions relative to ADAPTIVE but lower the catch rate. This is the predicted preference–commitment gap | Simulation + human study |

## 3. Variables

### 3.1 Independent variables

| Variable | Levels | Manipulation |
|---|---|---|
| **Intervention policy** | `full_autonomy`, `always_confirm`, `fixed_threshold`, `adaptive` (+ `user_customized`; simulation-only extra baselines: `rule_based`, `confidence_threshold`, `myopic_voi`, `learned` [experimental]) | Within-subjects in the human study (4 core conditions, counterbalanced by Latin square). All levels in simulation |
| **Explanation type** | none / placebic reason (content-free justification, after Eiband et al. 2019) / factors + reason codes / factors + reason codes + timing counterfactuals | Between-subjects (avoids carry-over learning). The placebic control separates the effect of *content* from the effect of *giving a reason* |
| **Scenario** | travel, email, shopping, file management, calendar, research assistant | Within-subjects, crossed with policy |
| **Consequence level** | low vs. high stakes (scenario variants) | Blocking factor (Chen et al. 2026 report trust effects that reverse with consequence level) |

Simulation-only independent variables: agent calibration (how well confidence tracks errors),
simulated user vigilance and habituation rate, cognitive-load profile, and the interruption-cost
weight `c₀`.

### 3.2 Dependent variables

Grouped as in [metrics.md](metrics.md):

- **Objective, from logs:**
  - task success rate
  - task completion time
  - intervention count and rate
  - interruption episodes (after batching)
  - decision latency
  - human response time
  - user override rate
  - intervention acceptance rate
- **Ground-truth-dependent** (computable in simulation and in scripted study scenarios with injected errors):
  - unnecessary-intervention rate
  - missed-intervention rate
  - agent error rate
  - human error rate (approving an injected error, or rejecting a correct action)
  - recovery rate
  - intervention lateness (rework steps before a caught error)
  - expected harm
- **Subjective** (questionnaires; human study only):
  - perceived control / agency
  - trust
  - workload
  - usability
  - interruption annoyance
  - explanation satisfaction
  - comprehension accuracy (scored)
- **Simulated proxies** (labelled as such everywhere):
  - simulated workload proxy (accumulated interruption cost)
  - simulated human response time

### 3.3 Control variables

- **Scenario content and injected errors.** Fixed by seed. The same seed gives the same errors under every policy (common random numbers), so policy comparisons are paired.
- **User interface.** Identical across policy conditions. Only the decision source and, between subjects, the explanation type differ.
- **Agent behaviour.** Deterministic scripted agent: no live LLM, so no model variance between participants.
- **Order effects.** Latin-square counterbalancing of policy order; scenario-to-policy assignment rotated.
- **Covariates to collect.** Prior experience with AI agents, and propensity to trust automation (researcher-chosen validated instrument; see `docs/experiments.md` on instruments and licensing).
- **Practice.** One practice scenario, excluded from analysis.

## 4. Experimental conditions

| Code | Policy | Description |
|---|---|---|
| A | `full_autonomy` | Never interrupts unless an action is technically impossible (BLOCK still applies to hard constraints) |
| B | `always_confirm` | Asks before every *meaningful* action, i.e. every non-read-only action |
| C | `fixed_threshold` | Asks when `risk = severity × [(1 − recoverability) + ρ · recoverability] ≥ τ`, with undo-cost fraction ρ = 0.15 (default τ = 0.35) |
| D | `adaptive` | Trajectory-aware expected-value model with DEFER/batching (see `docs/policies.md`) |
| E | `user_customized` | D plus participant-authored preferences (optional fifth condition, or RQ6 follow-up) |

## 5. Study design summary

- **Design:** mixed. Policy is within-subjects (A–D). Explanation type is between-subjects (4 levels: none, placebic reason, factors, factors + timing).
- **Procedure:**
  1. consent;
  2. demographics and covariates (no PII);
  3. practice;
  4. four blocks (policy × scenario), each followed by short post-task measures;
  5. final preference ranking and comprehension test;
  6. debrief.
- **Embedded problematic actions:** each scenario contains scripted problematic actions (after Chen et al. 2026), so oversight effectiveness can be scored objectively.
- **Sample size:** not fixed. Comparable within-subjects studies used N = 48 (Zhou et al.; Chen et al.). A formal power analysis fixes the smallest effect size of interest (or non-inferiority margin) on substantive grounds before data collection, and uses a pilot mainly to estimate variances. `docs/experiments.md` describes the procedure with data exported by the study mode.

## 6. Expected contribution

1. **Artifact.** An open, reproducible testbed for intervention-timing research: simulator, policies, metrics, study mode.
2. **Method.** Counterfactual timing explanations computed by replaying any policy over the trajectory.
3. **Model.** A trajectory-aware intervention model that integrates signals studied separately in prior work, with DEFER/batching bounded by reversibility.
4. **Evidence.**
   - (a) Simulation results, labelled as simulated, showing under which simulator conditions timing helps *and where it does not*.
   - (b) A ready-to-run study protocol for RQ3–RQ5. Human results are **not yet available**.
