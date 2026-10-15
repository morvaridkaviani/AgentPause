# Metric Definitions

This document defines every metric AgentPause reports. The implementation is
`simulator/src/agentpause_sim/metrics.py` (simulation) and `backend/app/services/metrics.py`
(interactive and study sessions). If this document and the code disagree, that is a bug; please
open an issue.

Each metric belongs to one of four kinds, and the kind is shown next to it in the API, the
dashboard, and the exported tables:

| Kind | Meaning | Available in |
|---|---|---|
| **Objective** | Computed from event logs only | Simulation, demo, study, API sessions |
| **Ground truth** | Needs labelled errors: which actions were wrong and which interventions were needed | Simulation, and scripted study scenarios with injected errors. **Not** available for arbitrary real agents |
| **Subjective** | Questionnaire responses | Human study only |
| **Simulated proxy** | A modelling quantity that exists only in the simulator | Simulation only. It is **not** a measurement of a human property |

Results computed from simulated users are labelled *simulated*. No metric here has yet been
measured with human participants.

---

## 1. Notation

An **episode** *e* is one run of one scenario under one policy with one seed. It has steps
*t = 1..T_e*. At each step the policy returns a decision
*d_t ∈ {CONTINUE, DEFER, CLARIFY, ASK_HUMAN, BLOCK}*.

- **Intervention (interruption).** A step whose decision shows the human a card:
  *I_e = {t : d_t ∈ {CLARIFY, ASK_HUMAN, BLOCK}}*. A batched card that contains several
  questions counts as **one** intervention.
- **Questions.** *Q_e* is the number of individual questions shown: every assumption question,
  plus the approval question, in every card.
- **Error events.** *E_e* is the set of error events injected by the scenario for that seed. It
  includes:
  - *mistakes*: a wrong action, which becomes visible at step `visible_at` and causes harm at
    step `harm_at` if not caught;
  - *wrong assumptions*: an interpretation of the user's intent that differs from the user's
    real intent, given in the scenario brief and hidden from the agent.

  Each error *ε* has a status in {caught, harm, pending}. It also records *shown(ε)*: whether
  any intervention displayed it while it was pending.
- **Error cost.** With severity *s* and recoverability *r* (1 = trivially undone):

  &nbsp;&nbsp;&nbsp;&nbsp;*cost(ε) = s · [(1 − r) + r · ρ]*, where *ρ = 0.15* is the undo-cost fraction (`ModelParameters.undo_cost_fraction`).

  Harm accounting uses the default *ρ* regardless of the policy under test, so policies cannot
  change how harm is measured.

## 2. Ground-truth labels for interventions

An intervention at step *t* is **necessary** if, at that moment, it showed the human at least
one pending error event, or if the step requires human input (for example a payment
credential). Otherwise it is **unnecessary**. Write *N_e* and *U_e* for the necessary and
unnecessary interventions (*|N_e| + |U_e| = |I_e|*).

A **missed intervention** is an error that caused harm without ever being shown to the human:
*M_e = {ε ∈ E_e : status(ε) = harm ∧ ¬shown(ε)}*.

Limitation: "necessary" is a modelling choice made by the scenario authors. People disagree
about when they want to be asked. An intervention labelled unnecessary may still be wanted by
some users, which is why the subjective measures matter.

## 3. Rates are pooled

Rates aggregate numerators and denominators over all episodes in a cell (scenario × policy ×
condition) and then divide. They are not means of per-episode ratios, which would be undefined
for episodes with zero interventions or zero errors. Per-episode quantities are averaged over
episodes. Confidence intervals are 95% percentile bootstrap intervals over episodes (500
resamples by default, fixed resampling seed).

## 4. Objective metrics

| Key | Name | Definition |
|---|---|---|
| `interventions` | Interruptions per episode | mean over episodes of *\|I_e\|* |
| `questions` | Questions per episode | mean of *Q_e* |
| `deferrals` | Deferrals per episode | mean of *\|{t : d_t = DEFER}\|* |
| `task_duration_s` | Task completion time | simulated clock at the end of the episode, including agent step time, human response time, and rework time. In a human study, wall-clock time from task start to completion |
| `override_rate` | User override rate | Σ responses in {edit, reject, takeover, override} / Σ responses |
| `acceptance_rate` | Intervention acceptance rate | Σ responses that accepted the proposal unchanged (approve, or an answer equal to the agent's guess) / Σ responses |
| `decision_latency_ms` | Decision latency | mean wall-clock time of one `evaluate` call. Machine-dependent, so it is excluded from result hashes |
| — | Human response time | time from card shown to response (human study). In simulation see `human_time_s` |

## 5. Ground-truth metrics

| Key | Name | Definition | Better |
|---|---|---|---|
| `unnecessary_rate` | Unnecessary-intervention rate | Σ_e \|U_e\| / Σ_e \|I_e\| | lower |
| `missed_rate` | Missed-intervention rate | Σ_e \|M_e\| / Σ_e \|E_e\| | lower |
| `recovery_rate` | Recovery rate | Σ_e \|{ε : status = caught}\| / Σ_e \|E_e\| | higher |
| `harm` | Expected harm per episode | mean over episodes of Σ_{ε: status = harm} cost(ε) | lower |
| `task_success` | Task success rate | share of episodes that completed with no harmful error | higher |
| `human_miss_rate` | Human oversight failure rate | Σ errors shown but approved and then harmful / Σ errors shown | lower |
| `human_error_rate` | Human error rate | (errors approved despite being shown + rejections of correct actions) / Σ responses | lower |
| `agent_error_rate` | Agent error rate | Σ_e \|E_e\| / Σ_e T_e | (descriptive) |
| `rework_steps` | Intervention lateness | mean number of executed steps that had to be redone because a wrong assumption was corrected after they ran | lower |

Paired comparisons (`comparisons` in every result) report the mean per-episode difference
*treatment − baseline* on identical scenario/seed/episode triples (common random numbers),
with a bootstrap interval over pairs (1000 resamples). In paired comparisons, `unnecessary` and
`missed_interventions` are per-episode **counts**, not rates.

## 6. Subjective metrics (human study only)

These are collected with questionnaires configured in study mode. Item text of licensed
instruments is not redistributed; see `docs/experiments.md` and `research/prior_art.md` §2.10.

| Construct | Instrument (researcher's choice) | Score |
|---|---|---|
| Workload | NASA-TLX, raw (unweighted) | mean of six 0–100 subscales |
| Usability | SUS (items supplied locally) | standard SUS score 0–100 |
| Trust in automation | Körber 2018 TiA, or Jian et al. 2000 (items supplied locally) | per published scoring |
| Explanation satisfaction | Hoffman et al. 2018 (items supplied locally) | mean |
| Perceived control, interruption annoyance, timing appropriateness | AgentPause **pilot items** (not validated, marked as such) | mean of 7-point items |
| Comprehension | AgentPause timing-comprehension check | proportion correct (`correct` scoring) |

**Appropriate reliance** (H5), after Schemmer et al. (2023). Let the human's response to an
intervention be *accept* or *override*, and let the ground truth say whether the agent's
proposal was correct.

- *RAIR* (relative AI reliance) = P(accept | the human would have overridden without the
  explanation, and the agent was correct). It is estimated between subjects as the difference
  in acceptance of correct proposals between explanation conditions.
- *RSR* (relative self-reliance) = the analogous difference in overriding incorrect proposals.

Because the study is between subjects on explanations, we report acceptance-of-correct and
override-of-incorrect rates per explanation condition. RAIR and RSR are differences relative
to the *none* condition, with bootstrap intervals over participants.

## 7. Simulated proxies (simulation only)

| Key | Definition | Caveat |
|---|---|---|
| `human_time_s` | simulated seconds the simulated user spent on cards: base time + 2.5 s per question + a load-dependent term (`SimulatedUserParams`), plus 45 s when the user must fix a step themselves after repeated rejections | depends entirely on the simulated-user parameters |
| `workload_proxy` | Σ over interventions of (1 + load_t) · (1 + 0.5 · (q_t − 1)), where *q_t* is the number of questions in the card | **not** a measure of human workload. Used only to check that batching is not "free" in the simulator |

The simulated user's habituation (the probability of noticing a shown error falls with recent
interruptions) is a model assumption taken from the warning-fatigue literature. It is not a
measurement. `experiments/configs/sensitivity.toml` varies it.

## 8. Reproducibility

Every experiment result carries a SHA-256 hash of all metrics and records, excluding decision
latency. Same code + same config + same seed gives the same hash on any machine
(`scripts/check_reproducibility.py`).
