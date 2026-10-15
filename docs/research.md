# Research framing

AgentPause is **research infrastructure and an open-source toolkit for studying adaptive
human intervention timing in AI-agent systems**. It asks when an agent should continue
autonomously, and when it should pause and involve the human: clarify an assumption, ask for
approval, defer a question to a better moment, or stop.

> **Status: Not yet evaluated with human participants.** All results produced by the
> simulator, the experiment scripts, `/compare` and `/experiments` are simulated, and are
> labelled "SIMULATED RESULTS. Not evaluated with human participants." The human-study mode
> is implemented but has not been used to collect data.

## Documents

| Document | Contents |
|---|---|
| [research/research_questions.md](../research/research_questions.md) | Research questions RQ1–RQ6, pre-specified hypotheses H1a–H6, variables, experimental conditions A–E, study design |
| [research/research_gap.md](../research/research_gap.md) | Which parts of the problem prior work already covers, what remains open within the reviewed literature, and what is not claimed |
| [research/prior_art.md](../research/prior_art.md) | Review of about 250 papers, products and repositories (HCI, ML/NLP, agent frameworks, explanations, questionnaire licensing) |
| [research/literature_notes/](../research/literature_notes/) | Working notes from the five search threads, kept for auditability |
| [research/metrics.md](../research/metrics.md) | Formal metric definitions used by the simulator and the dashboard |
| [policies.md](policies.md) | The policies and the expected-value model, with every parameter and its assumptions |
| [experiments.md](experiments.md) | Simulator, ground truth, experiment configs, reproducibility, study mode, instruments, ethics, power analysis |

## Research questions

The questions isolate what remains open after the prior-art review. Prior work already shows
that adaptive asking *in general* can outperform fixed strategies. Summarized from
[research_questions.md](../research/research_questions.md):

| | Question | Answerable in |
|---|---|---|
| **RQ1** | Timing: does a trajectory-aware policy (ask now, defer and batch, or never ask) reduce unnecessary interruptions without increasing missed interventions or harm, compared with fixed strategies and with a myopic expected-value policy? | Simulation and human study |
| **RQ2** | Signals: which contextual signals carry the value of the decision? | Simulation ablation (under the simulator's assumptions only) and human data |
| **RQ3** | Human outcomes: perceived control, trust, workload, oversight effectiveness, task time | Human study |
| **RQ4** | Understanding: do counterfactual timing explanations ("why not earlier / later") improve understanding over factor-only explanations? | Human study |
| **RQ5** | Acceptance without over-reliance: do timing explanations increase acceptance of autonomy without increasing approval of erroneous actions? | Human study |
| **RQ6** | User customization: do user-authored preferences reduce interruptions, and at what cost in oversight? | Simulation and human study |

## Contributions

The contributions are listed in decreasing order of how defensible we consider them (see
[research_gap.md](../research/research_gap.md), §3).

1. **An open, deterministic testbed with baselines from prior work.** The testbed consists of:
   - six scripted scenarios with injected errors and wrong assumptions, each with a
     commitment point;
   - a parametric simulated user who habituates;
   - formally defined unnecessary, missed and late-intervention metrics;
   - paired comparisons on common random numbers, with result hashes;
   - an experiment runner and dashboard;
   - a study mode that runs the same scenarios with participants.

   The baselines are simplified re-implementations of designs from prior work and products,
   not faithful reproductions:
   - never ask (AutoGen `NEVER`, OpenHands `NeverConfirm`);
   - always confirm (AutoGen `ALWAYS`, OpenHands `AlwaysConfirm`);
   - a fixed risk threshold (OpenHands `ConfirmRisky`, Mastra);
   - reversibility × confidence rules (Magentic-UI, ask-or-act);
   - a confidence threshold (KnowNo, Warp);
   - a myopic expected-value policy (in the spirit of Horvitz 1999 and Dong et al. 2026).

   See [experiments.md](experiments.md) and [policies.md](policies.md#baseline-policies).
2. **Counterfactual timing explanations for human-intervention decisions.** For each
   decision to involve (or not involve) the human, AgentPause answers *why now*, *why not
   earlier* and *why not later*.
   - *Earlier* is read from what the policy actually computed at earlier steps of the same
     trajectory.
   - *Later* comes from the policy's evaluation of the planned future steps.
   - The text comes from deterministic templates over the policy's own reason codes and
     terms, not from a language model.
   - The explainer treats the policy as a black box, so it works for any policy that
     implements the `InterventionPolicy` interface.

   The temporal contrastive question form itself comes from planning (Krarup et al. 2021,
   FQ7; Fox, Long & Magazzeni 2017). See [sdk.md](sdk.md#explanations).
3. **A trajectory-aware timing model.** The `adaptive` policy builds on an expected-value
   core adapted from Horvitz (1999). For each open question it chooses among *ask now*,
   *defer* to a natural breakpoint or to a confirmation that will happen anyway (batching),
   and *never ask*. Deferral is bounded in two ways:
   - **hard**, by the question's reversibility deadline: the first dependent action that
     cannot be undone;
   - **soft**, by expected rework and by information-type decay: goal and constraint
     questions are not deferred, following Gulati et al. (2026).

   The model also includes habituation-aware catch probability and history weighting that
   discounts approvals given under fatigue. See [policies.md](policies.md#the-adaptive-policy).

## What is not claimed

- AgentPause is **not** the first adaptive or decision-theoretic "when to ask" system.
  Expected-value asking, deferral to less disruptive moments, breakpoint-based interruption
  management, and user-adjustable autonomy all have prior work. That work is cited as the
  foundation, and several of its ideas are implemented as baselines.
- The parameter values (interruption-cost weights, habituation rates, category severities,
  signal defaults) are **documented priors, not empirically calibrated values**. Calibrating
  them requires human data.
- The simulator's ground truth is **not** a model of what real users consider a necessary
  intervention. It encodes the scenario authors' judgement, so that comparisons are
  reproducible.
- Simulation results do **not** support claims about human outcomes (RQ3–RQ5). Any
  simulated result shows how policies compare **under the simulator's assumptions**,
  including where timing does not help.
- The `learned` policy is trained on simulated labels and is not evidence about real users.
- "Not found" statements about prior work are limited to the literature and systems that
  were reviewed.

## Citing

Citation metadata is in [`CITATION.cff`](../CITATION.cff). When you report results produced
with AgentPause, state whether they are simulated.
