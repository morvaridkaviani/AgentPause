# Intervention policies

A policy decides, for one proposed action, whether the agent should **CONTINUE**,
**CLARIFY** an assumption, **ASK_HUMAN** for approval, **DEFER** a question to a later step,
or **BLOCK**. This page documents every policy in the registry, the expected-value model
behind the `adaptive` and `myopic_voi` policies, and how to add a policy.

The source is `sdk/python/src/agentpause/policies/` and `sdk/python/src/agentpause/model.py`.
Every number on this page is a default from the code. All defaults are documented priors,
not calibrated estimates (see [Assumptions and limitations](#assumptions-and-limitations)).

Contents:

- [Registry](#registry)
- [Behaviour shared by all policies](#behaviour-shared-by-all-policies)
- [Baseline policies](#baseline-policies)
- [The expected-value model](#the-expected-value-model)
- [The adaptive policy](#the-adaptive-policy)
- [Catastrophic BLOCK rule](#catastrophic-block-rule)
- [The myopic ablation (`myopic_voi`)](#the-myopic-ablation-myopic_voi)
- [User-customized (`user_customized`)](#user-customized-user_customized)
- [`learned` (experimental)](#learned-experimental)
- [Adding a policy](#adding-a-policy)
- [Assumptions and limitations](#assumptions-and-limitations)

## Registry

Create a policy by name with `create_policy(name, parameters=..., preferences=..., **config)`
or `AgentPause(policy=name, **config)`. Names are case-insensitive, and hyphens or spaces
are read as underscores.

| Name | Aliases | Class | Study code | Configuration (defaults) | Design origin (`POLICY_INFO`) |
|---|---|---|---|---|---|
| `full_autonomy` | `never`, `autonomy` | `FullAutonomyPolicy` | A | — | AutoGen `human_input_mode=NEVER`; OpenHands `NeverConfirm` |
| `always_confirm` | `always` | `AlwaysConfirmPolicy` | B | `include_read_only=False` | AutoGen `ALWAYS`; OpenHands `AlwaysConfirm` |
| `fixed_threshold` | `threshold`, `fixed_risk_threshold` | `ThresholdPolicy` | C | `threshold=0.35`, `mode="consequence"` | OpenHands `ConfirmRisky`; Mastra classifier ≥ τ |
| `adaptive` | `agentpause`, `adaptive_agentpause` | `AdaptivePolicy` | D | `timing=True`, `block_catastrophic=True`, `name=None` | This project, building on Horvitz 1999, Iqbal & Bailey, Gulati et al. 2026 |
| `user_customized` | `customized` | `UserCustomizedPolicy` | E | `base="adaptive"`, plus keyword arguments for the base policy | Adaptive plus user rules (cf. Ask4Help preference conditioning; Yan 2026) |
| `myopic_voi` | `voi` | `MyopicVOIPolicy` | — | `block_catastrophic=True` | Ablation in the spirit of Horvitz 1999 and Dong et al. 2026 |
| `rule_based` | `rules` | `RuleBasedPolicy` | — | `confidence_threshold=0.8`, `block_catastrophic=True` | Magentic-UI action guards; ask-or-act rules |
| `confidence_threshold` | `confidence` | `ConfidenceThresholdPolicy` | — | `threshold=0.8` | KnowNo-style "ask when uncertain" (non-conformal); Warp "Agent decides" |
| `learned` | — | `LearnedPolicy` | — | `threshold=0.5`, `block_catastrophic=True`, `weights_path=None`, `model=None` | Logistic model on simulated logs (experimental) |

Every policy also accepts `parameters` (a `ModelParameters` or a dict of overrides) and
`preferences` (`UserPreferences` or dict). The study codes A–D are the four core conditions
of the planned user study, and E is optional (see
[research_questions.md](../research/research_questions.md)). `available_policies()` and
`GET /api/v1/policies` return this registry with the metadata.

The baselines are simplified re-implementations of designs from prior work and products.
They are not faithful reproductions of those systems (see
[prior_art.md](../research/prior_art.md)).

## Behaviour shared by all policies

1. **Signal resolution.** Every policy starts from the same `ResolvedSignals`: missing values
   are filled with defaults, values are clamped, provenance is recorded, and intent
   confidence is combined with open assumptions and the user's history. See
   [sdk.md](sdk.md#signal-resolution-and-provenance).
2. **Hard constraint.** If `requires_human_input` is set, every policy returns BLOCK with
   reason `REQUIRES_HUMAN_INPUT` and intervention kind `takeover`.
3. **Purity.** `decide(context, state)` reads the session state but never modifies it, and
   uses neither randomness nor wall-clock time. The explainer relies on this: it calls
   `decide` many times on hypothetical inputs to compute factors, counterfactuals and
   stability.
4. **Explanations** are added afterwards by the `Explainer` and work for every policy. Only
   the adaptive policy plans future moments, so only its "why not later" text refers to
   specific later steps.
5. **Data-quality codes.** `MISSING_SIGNAL_DEFAULTED` and `CONTRADICTORY_SIGNALS` are added to
   any decision whose inputs had missing or contradictory values.

## Baseline policies

In the table, *risk* means the consequence risk `C_err(sev, r)` defined in
[the expected-value model](#the-expected-value-model). *c_a* is agent confidence and *c_i*
is resolved intent confidence.

| Policy | Rule | Score |
|---|---|---|
| `full_autonomy` | Always CONTINUE (except the shared hard constraint). | 0 |
| `always_confirm` | ASK_HUMAN before every action whose category is not `read_only`, with the action question plus any unresolved assumptions the action depends on. With `include_read_only=True`, read-only actions are confirmed too. | 1 (asks), 0 (read-only) |
| `fixed_threshold` | ASK_HUMAN if risk ≥ `threshold`, else CONTINUE. `mode="consequence"` uses risk alone and ignores uncertainty, which is how most risk-gated products work. `mode="expected_harm"` multiplies risk by `p_err = 1 − c_a·c_i`. | `risk` (clamped to [0, 1]) |
| `confidence_threshold` | CONTINUE if `min(c_a, c_i) ≥ threshold`, regardless of stakes. Otherwise CLARIFY if some unresolved assumption has confidence below the threshold and `c_i ≤ c_a`, else ASK_HUMAN. | `1 − min(c_a, c_i)` |
| `rule_based` | In order: catastrophic → BLOCK; `read_only` or `internal_draft` → CONTINUE; recoverability < 0.5 (`commitment_recoverability`) or external effects → ASK_HUMAN; `c_a ≥ τ` and `c_i ≥ τ` → CONTINUE; uncertain assumptions while `c_a ≥ τ` → CLARIFY; otherwise ASK_HUMAN. τ = `confidence_threshold`. | 0 or 1 |

None of the baselines plan ahead, so none of them returns DEFER. Only `rule_based` (and
`adaptive`, `myopic_voi`, `learned`) apply the [catastrophic BLOCK rule](#catastrophic-block-rule).

> The fixed-threshold risk is `severity · [(1 − r) + r · ρ]` with ρ = 0.15, not exactly
> `severity × (1 − recoverability)`. A fully reversible action of severity 1 therefore still
> has risk 0.15.

## The expected-value model

The model is an expected-value-of-asking formulation in the tradition of Horvitz (1999,
*Principles of Mixed-Initiative User Interfaces*) and Horvitz et al. (2003, attention-sensitive
alerting), adapted to multi-step tool-using agents. It is not a new decision theory. All
quantities share one scale: 1.0 is the worst outcome the deployment cares about.

For a question `q` that could be asked at step `t`, while the agent is at step `i`:

```text
V(q, t) = p(q) · C_err(q) · e  −  C_int(t)  −  RW(q, i→t)
          └──── benefit B ────┘    └ cost ┘    └ cost of waiting ┘
```

Terms, as implemented in `model.py` and `policies/adaptive.py`:

```text
Probability that proceeding is wrong
  approval of the current action:  p_act   = 1 − c_a · c_i,res
  an assumption a:                 p_wrong = 1 − confidence(a)
  (BLOCK rule, learned features):  p_err   = 1 − c_a · c_i

Harm if the wrong action executes
  C_err(sev, r) = sev · [(1 − r) + r · ρ]

Habituation and catch probability
  h = 1 − exp(−λ · n_recent)            n_recent = interruptions in the last W steps
  e = e₀ · (1 − η · h)                  η = habituation_effect

Interruption cost
  C_int = c₀ · π · (1 + γ · load) · β(breakpoint) · (1 + κ · h) · μ(kind)
          β = 1 at a breakpoint, 1.5 mid-task, 1.25 unknown
          μ = 0.8 for a clarification, 1 for a confirmation
          π = preference multiplier: 2.5 fewer_interruptions, 1 balanced, 0.25 maximum_control

Rework from waiting
  RW(a, i→t) = p_wrong(a) · Σ over dependent steps d with i ≤ step(d) < t of (r_step + ρ · sev_d)

Score
  score = B / (B + C)        (0 if B + C ≤ 0)
```

- `c_i,res` is the *residual* intent confidence: the part not attached to an explicit
  assumption. The approval question uses it so that ambiguity already represented by an
  assumption question is not counted twice.
- `p_err` treats agent errors and intent mismatches as independent.
- A fully recoverable mistake still costs `ρ · sev`, the effort of undoing it.
- `e` falls with habituation, because repeated prompts produce rubber-stamping (Böhme &
  Köpsell 2010; Anderson et al. 2015).
- `C_int` grows with cognitive load and outside natural breakpoints (Adamczyk & Bailey 2004;
  Iqbal & Bailey 2005–2010).
- The score is above 0.5 exactly when the net value `B − C` is positive.

### Default parameters (`ModelParameters`)

| Parameter | Symbol | Default | Meaning |
|---|---|---|---|
| `interruption_cost` | c₀ | 0.02 | Cost of one interruption at a breakpoint with zero load, in harm units. With 0.02, a user would accept about 50 interruptions to prevent one worst-case error |
| `load_weight` | γ | 1.0 | `C_int` scales with `(1 + γ · load)` |
| `non_breakpoint_multiplier` | β | 1.5 | Interrupting mid-subtask costs more than at a task boundary |
| `unknown_breakpoint_multiplier` | β | 1.25 | Used when breakpoint information is missing |
| `clarification_cost_multiplier` | μ | 0.8 | A clarification (pick an option) is assumed lighter than reviewing an action |
| `batch_marginal_cost` | m | 0.35 | Fraction of the cost paid by each additional question in an interruption that happens anyway |
| `habituation_annoyance` | κ | 0.5 | `C_int` scales with `(1 + κ · h)` |
| `base_catch_probability` | e₀ | 0.9 | Probability that an attentive user catches a problem shown to them |
| `habituation_rate` | λ | 0.12 | `h = 1 − exp(−λ · n_recent)` |
| `habituation_window` | W | 8 | Number of recent steps counted for habituation |
| `habituation_effect` | η | 0.5 | Maximum relative reduction of the catch probability. Also the discount on approvals given while habituated |
| `undo_cost_fraction` | ρ | 0.15 | Undoing a recoverable mistake still costs this fraction of its severity |
| `rework_cost_per_step` | r_step | 0.01 | Fixed cost of redoing one reversible step built on a wrong assumption |
| `commitment_recoverability` | r_commit | 0.5 | Actions with recoverability below this are commitment points |
| `anticipated_agent_confidence` | ĉ_a | 0.9 | Agent confidence assumed for planned steps when predicting whether they will need a confirmation anyway |
| `deferrable_kinds` | — | `{input, context}` | Assumption kinds that may be deferred |
| `history_prior_strength` | n₀ | 4.0 | Pseudo-observations given to the agent's own intent estimate when shrinking it toward the user's observed disagreement rate |
| `block_severity` | — | 0.9 | Catastrophic BLOCK: minimum severity |
| `block_max_recoverability` | — | 0.15 | Catastrophic BLOCK: maximum recoverability |
| `block_min_error_probability` | — | 0.6 | Catastrophic BLOCK: minimum `p_err` |

Override any of them per policy:

```python
from agentpause import AgentPause, ModelParameters

pause = AgentPause("adaptive", parameters={"interruption_cost": 0.03, "habituation_rate": 0.2})
# or: AgentPause("adaptive", parameters=ModelParameters(interruption_cost=0.03))
```

`ModelParameters.from_dict` rejects unknown keys. `GET /api/v1/model` returns the defaults
together with the category priors and reason codes.

Signal defaults used when a value is missing are agent confidence 0.8, intent confidence
0.85, cognitive load 0.3, and task progress 0.5 (inferred from the plan when possible).
`reversible=True` maps to recoverability `max(prior, 0.9)` and `reversible=False` to
`min(prior, 0.1)`. Category priors for severity and recoverability are listed in
[sdk.md](sdk.md#consequence-categories).

### Learning from history

The user's responses to earlier actions with the same `action_key` shift intent confidence.
Disagreements (`edit`, `reject`, `takeover`, `cancel_task`) count 1. Approvals (`approve`,
`answer`, `override`) count `1 − η · h`, where `h` is the habituation level when the
decision was made. With `w` the total weight and `d` the disagreement rate:

```text
p_intent' = (n₀ · (1 − c_i) + w · d) / (n₀ + w)        c_i' = 1 − p_intent'
```

The same shrinkage is applied to the residual intent confidence. Approvals given while
habituated count for less, because they may be rubber stamps.

### Worked example

`send_email`, `external_communication`, `reversible=False`, `agent_confidence=0.86`,
`intent_confidence=0.72`, no other signals, first step of a session:

| Term | Value |
|---|---|
| severity (category prior), recoverability (`min(0.05, 0.1)`) | 0.45, 0.05 |
| `p_act = 1 − 0.86 · 0.72` | 0.3808 |
| `C_err = 0.45 · (0.95 + 0.05 · 0.15)` | 0.4309 |
| `e = 0.9 · (1 − 0.5 · 0)` | 0.9 |
| `B = p_act · C_err · e` | 0.1477 |
| `C_int = 0.02 · 1 · (1 + 0.3) · 1.25 · 1 · 1` (load default 0.3, breakpoint unknown) | 0.0325 |
| `V = B − C_int` | 0.1152 > 0 → ASK_HUMAN |
| `score = B / (B + C_int)` | 0.82 |

These values appear in `decision.terms` (`p_error_action`, `error_cost`,
`catch_probability`, `benefit_action`, `interruption_cost_now`, `value_action`).

## The adaptive policy

`AdaptivePolicy` (`adaptive`) applies the model over the trajectory. For the proposed action
at step `i`:

### 1. Hard constraints

BLOCK if `requires_human_input` is set. BLOCK by the [catastrophic rule](#catastrophic-block-rule)
if `block_catastrophic=True`.

### 2. Approval of the current action

`V_act = p_act · C_err(sev, r) · e − C_int(i, confirmation)`. Its deadline is now: once the
action runs, approval is moot.

### 3. Clarification questions

For every unresolved assumption that the current action or a planned action depends on (via
`depends_on`), the policy computes:

- **Dependents**: the current action (if it depends on the assumption) and the planned steps
  that do, in step order. Planned steps use their own severity and recoverability, or
  category priors.
- **Commitment point**: the first dependent with recoverability below `commitment_recoverability`.
  Asking after it cannot prevent the harm, so it is the question's **deadline**. The harm
  term is `C_err` at the commitment point. If no dependent is a commitment point, the deadline
  is the last dependent step and the harm is the largest `C_err` among dependents.
- **Benefit**: `p_wrong(a) · harm · e`.

#### Deferrable information types

A question is *deferrable* only if all three hold:

- timing is enabled (`timing=True`);
- its kind is in `deferrable_kinds` (by default `input` and `context`);
- its deadline is after the current step.

Goal and constraint questions lose most of their value early in a trajectory (Gulati et al.
2026, *Ask Early, Ask Late, Ask Right*), so by default they are asked now or not at all.

#### Candidate moments

A non-deferrable question has one candidate: now. A deferrable question also gets every
planned step `t` with `i < t ≤ deadline` that is:

- a natural breakpoint (`at_breakpoint=True`); or
- the deadline itself; or
- an **anticipated confirmation**: a planned step whose own approval is expected to be
  worth asking for. A planned step `j` is anticipated when
  `(1 − ĉ_a) · C_err(sev_j, r_j) · e > C_int(j, confirmation)`, with `ĉ_a` =
  `anticipated_agent_confidence` = 0.9. The agent's future confidence is unknown, so this
  assumption stands in for it.

For each candidate, the policy computes:

- **Interruption cost**: `C_int(t, clarification)`, using the planned step's load (or the
  current load) and breakpoint flag.
- **Batching**: if `t` is not now and is either an anticipated confirmation or the target of
  another scheduled question, the cost is multiplied by `batch_marginal_cost` (0.35). The
  question rides along with an interruption that happens anyway.
- **Rework**: `RW(a, i→t)`, the expected cost of redoing dependent reversible steps executed
  before `t` if the guess is wrong.

The best moment is the candidate with the highest `V`, with ties going to the earliest. If
the best `V` is not positive, the question is never asked.

### 4. Assembly

- **Interrupt now** if any item's best moment is now. The item with the highest value now is
  the primary question and pays the full interruption cost.
- **Piggybacking**: when interrupting, other questions are added at marginal cost
  (`cost × batch_marginal_cost`):
  - the action approval, if `B_act − m · C_act > 0`;
  - an assumption question, if its marginal value now is positive and at least its value at
    its own best moment.
- **Decision type**:
  - If any question is asked now and one of them is the action approval, the result is
    **ASK_HUMAN**.
  - If questions are asked now but none is the approval, the result is **CLARIFY**.
  - If nothing is asked now but some question's best moment is later, the result is **DEFER**.
    The current action proceeds, and the question is listed in `decision.deferred` with its
    target and deadline.
  - Otherwise **CONTINUE**.
- `recommended_intervention` is `batched_review` when more than one question is asked.
- **Score** is the largest `B / (B + C)` over the approval and the assumption questions,
  evaluated now at full cost.

### Timing semantics

- **DEFER never runs a step that commits a deferred assumption.** A question is deferrable
  only while its deadline (the first hard-to-undo dependent step) is after the current step.
- **The schedule is re-planned at every step.** After each recorded decision, the session's
  pending list (`pause.pending_questions`) is replaced by that decision's deferred questions,
  minus those that were asked or resolved. At the deadline step, the question has only one
  candidate (now), so by its deadline a question is either asked or judged not worth asking
  at all.
- **Reason codes.** DEFER carries `DEFERRED_TO_BREAKPOINT`, and where they apply
  `REVERSIBLE_ACTION`, `MID_TASK`, `HIGH_COGNITIVE_LOAD` and `BATCHED_QUESTIONS`.
  Questions asked at a commitment point carry `COMMITMENT_POINT`, or `DEPENDENT_COMMITMENT`
  when a later dependent step is the commitment point.
- **Simplifications.**
  - Habituation (`h`) and the catch probability (`e`) for future candidates are evaluated at
    the current level; the policy does not forecast them.
  - The anticipated-confirmation check uses agent error only, not intent ambiguity.
  - Planning uses only the steps in `plan`. Without a plan there are no later candidates,
    and the policy behaves like `myopic_voi`.

## Catastrophic BLOCK rule

```text
BLOCK  if  severity ≥ 0.9  and  recoverability ≤ 0.15  and  p_err ≥ 0.6
```

`p_err = 1 − c_a · c_i` uses the full intent confidence, including open assumptions and
history. The thresholds are `block_severity`, `block_max_recoverability` and
`block_min_error_probability`. The decision has score 1, intervention kind `takeover`, and
reason codes `CATASTROPHIC_RISK`, `IRREVERSIBLE_ACTION` and `HIGH_SEVERITY`.

The rule applies to `adaptive`, `myopic_voi`, `rule_based`, `learned`, and `user_customized`
through its base policy. Disable it with `block_catastrophic=False`. It does not apply to
`full_autonomy`, `always_confirm`, `fixed_threshold` or `confidence_threshold`.

## The myopic ablation (`myopic_voi`)

`MyopicVOIPolicy` is `AdaptivePolicy` with `timing=False`:

- no planned candidates and no anticipated confirmations;
- every question is asked now or never;
- it never returns DEFER.

It still piggybacks questions onto an interruption that happens anyway, and it uses the same
parameters and the same BLOCK rule. Comparing `adaptive` with `myopic_voi` therefore isolates
the contribution of re-timing questions (hypothesis H1b in
[research_questions.md](../research/research_questions.md)). It is a simplified per-step
analogue of value-of-information asking (Dong et al. 2026). It is not a reimplementation of
their belief-state method.

## User-customized (`user_customized`)

`UserCustomizedPolicy` applies the user's rules (`UserPreferences`, see
[sdk.md](sdk.md#userpreferences)) on top of a base policy (default `adaptive`). The profile
is passed to the base policy and scales its interruption cost. Precedence, highest first:

| # | Rule | Result | Reason code |
|---|---|---|---|
| 0 | `requires_human_input` | BLOCK | `REQUIRES_HUMAN_INPUT` |
| 1 | Category in `block_categories` | BLOCK | `USER_RULE_BLOCK` |
| 2 | Base policy returns BLOCK (e.g. catastrophic) | BLOCK | base codes |
| 3 | Category in `always_ask_categories`; or `ask_before_irreversible` and recoverability < 0.5 (non-read-only); or `ask_before_external` and external effects | ASK_HUMAN, with the action question plus the base policy's questions; score ≥ 0.5 | `USER_RULE_ALWAYS_ASK`, `USER_RULE_IRREVERSIBLE`, `USER_RULE_EXTERNAL` |
| 4 | Base returns ASK_HUMAN or CLARIFY, and: category in `never_ask_categories`; or `allow_low_risk_autonomy` and risk < `low_risk_threshold`; or the task's interruption count ≥ `max_interruptions_per_task` | CONTINUE, score ≤ 0.49 | `USER_RULE_NEVER_ASK`, `USER_RULE_LOW_RISK_AUTONOMY`, `INTERRUPTION_BUDGET_EXHAUSTED` |
| 5 | Otherwise | The base decision | base codes |

The base policy's terms and item timings are kept on the decision for inspection.
Preferences are a research variable (RQ6). In Yan (2026), 114 of 140 user-authored rules were
"ask" rules, and user-authored policies blocked less overreach, so user rules are not
assumed to improve outcomes.

```python
from agentpause import AgentPause

pause = AgentPause("user_customized", preferences={
    "profile": "fewer_interruptions",
    "always_ask_categories": ["data_sharing"],
    "block_categories": ["data_deletion"],
    "ask_before_irreversible": True,
    "max_interruptions_per_task": 3,
})
print(pause.evaluate("share_doc", consequence="data_sharing").decision.value)    # ASK_HUMAN
print(pause.evaluate("empty_trash", consequence="data_deletion").decision.value) # BLOCK
```

## `learned` (experimental)

`LearnedPolicy` is a logistic model that predicts `p(intervention needed | features)`.

- **Rule**: CONTINUE if the predicted probability is below `threshold` (0.5). Otherwise
  CLARIFY when there are unresolved assumptions and `1 − c_i > 1 − c_a`, else ASK_HUMAN. The
  catastrophic BLOCK rule applies first. The policy never returns DEFER.
- **Features** (11, available at decision time): `p_agent_error`, `p_intent_error`,
  `severity`, `irreversibility`, `error_cost`, `expected_harm`, `cognitive_load`,
  `not_breakpoint`, `habituation`, `external`, `task_progress`. The predicted probability
  and the feature values are in `decision.terms`.
- **Training** (`python experiments/train_learned_policy.py`, implemented in
  `agentpause_sim/learning.py`):
  - Each bundled scenario is run under a recording policy that always continues, so every
    step is observed once and the data do not depend on which policy chose to ask.
  - Training uses seed 1001 (120 episodes per scenario). The test set uses seed 2002 (60
    episodes per scenario).
  - The label is `intervention_needed`: at this step a pending injected mistake is visible,
    or the step depends on a wrong assumption. This is simulator ground truth and is never a
    feature.
  - The model is a class-balanced logistic regression on standardized features, fit by batch
    gradient descent (L2 = 1e-3, 1500 iterations, learning rate 0.5).
  - Evaluation: leave-one-scenario-out AUC on the training data, and AUC on the test seed.
  - The script writes the weights to `sdk/python/src/agentpause/policies/learned_weights.json`
    (bundled with the SDK) and a report to `experiments/results/learned_policy/report.json`.
- **Custom weights**: `create_policy("learned", weights_path="my_weights.json")` or
  `model=LogisticModel(...)`. The weights file must list the features in the order above.

**Caveats.**

- The labels come from the simulator's own generative assumptions, so the model can at best
  rediscover them. This is circular and is **not evidence about real users**. Its legitimate
  uses are as a worked example of plugging a learned model into the `InterventionPolicy`
  interface, and as a pipeline that becomes meaningful once real study logs exist.
- Because the recording policy never interrupts, habituation is always 0 in the training
  data, and the bundled model gives it a weight of 0.
- The threshold of 0.5 is not cost-sensitive. The policy does not plan timing.
- `experiments/reproduce_all.py` retrains the model first and overwrites the bundled weights
  file.

## Adding a policy

Subclass `InterventionPolicy`, implement `decide`, and register it. The policy then works
with explanations (factors, counterfactuals, timing, stability), the simulator, experiment
configs, and the REST API in the same process.

```python
from agentpause import (
    ActionContext, AgentPause, DecisionType, InterventionPolicy, SessionState, register_policy,
)
from agentpause.explain.reasons import ReasonCode
from agentpause.policies.base import action_question


class SeverityOnlyPolicy(InterventionPolicy):
    """Ask whenever the resolved severity is at least `cutoff`."""

    name = "severity_only"
    summary = "Asks when severity ≥ cutoff, ignoring everything else."

    def __init__(self, parameters=None, preferences=None, *, cutoff: float = 0.5):
        super().__init__(parameters, preferences)
        self.cutoff = cutoff

    def config(self):                       # recorded by describe(), used by from_dict()
        return {"cutoff": self.cutoff}

    def decide(self, context: ActionContext, state: SessionState):
        signals = self.resolve(context, state)          # defaults, clamping, provenance
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:                            # requires_human_input → BLOCK
            return hard
        if signals.severity >= self.cutoff:
            return self.make_decision(
                context, state, signals, DecisionType.ASK_HUMAN, score=signals.severity,
                reasons=[ReasonCode.HIGH_SEVERITY], questions=[action_question(context)],
                terms={"severity": signals.severity, "cutoff": self.cutoff},
            )
        return self.make_decision(context, state, signals, DecisionType.CONTINUE,
                                  score=signals.severity, reasons=[ReasonCode.LOW_RISK_ACTION])


register_policy("severity_only", SeverityOnlyPolicy,
                info={"label": "Severity only", "core": False, "study_code": None, "origin": "example"})

pause = AgentPause("severity_only", cutoff=0.4)
decision = pause.evaluate("purchase", consequence="payment")
print(decision.decision.value, decision.explanation)
```

Requirements and helpers:

- The factory is called as `factory(parameters, preferences, **config)`.
- `decide` must be pure and deterministic (see
  [shared behaviour](#behaviour-shared-by-all-policies)). Use `self.resolve()` so that
  defaults and provenance are handled consistently.
- Return decisions through `self.make_decision(...)`. It adds the data-quality reason codes,
  the resolved signals and the default intervention kind.
- Helpers on the base class: `hard_constraint`, `is_catastrophic`, `catastrophic_block`,
  `risk`, `error_cost`, `step_of`, `config`, `describe`.
- Helpers in `agentpause.policies.base`: `action_question`, `assumption_question`,
  `consequence_reasons`, `uncertainty_reasons`, `autonomy_reasons`,
  `unresolved_dependency_questions`.
- To provide "why not later" timing explanations, fill `decision.item_timings` and
  `decision.deferred` the way the adaptive policy does.
- Registration is per process. The backend and the simulator only see policies that were
  registered in their own process, and `AgentPause.from_dict` can only restore a policy that
  is registered under the name it was saved with.
- For simulation, `ExperimentConfig` policies are created through the same registry, so a
  registered policy can be used by name in a config run from Python.

## Assumptions and limitations

- **Parameters are documented priors, not calibrated estimates.** This covers the
  interruption-cost weights, the habituation rate and effect, the catch probability, the
  breakpoint and clarification multipliers, the undo and rework costs, the category priors,
  and the signal defaults. They were chosen by the authors. The default
  `interruption_cost = 0.02` was chosen on the development seed (20261014) as the knee of
  the simulated harm-versus-interruption frontier. None of the parameters has been fitted to
  human data. Calibrating them is part of RQ2 and needs a human study.
- **Comparisons should use frontiers, not one operating point.** Every parameterized policy
  trades harm against interruptions. `experiments/configs/frontier.toml` sweeps
  `interruption_cost` for `adaptive` and `myopic_voi` and the thresholds for
  `fixed_threshold` and `confidence_threshold`.
- **Independence.** `p_err` assumes that agent errors and intent mismatches are independent.
  Assumption confidences are multiplied as if independent.
- **Signals are only as good as their sources.** Agent confidence is often poorly calibrated.
  Severity and recoverability default to coarse category priors. Cognitive load and
  breakpoints usually have to be estimated. Provenance makes visible which values were
  measured and which were defaulted.
- **The habituation model** is a saturating function of the interruption count in a window,
  motivated by the warning-habituation literature. It has not been fitted for agent
  approvals.
- **Timing needs a plan.** DEFER and batching need `plan` and `depends_on`. The policy trusts
  the plan, and does not model plan changes beyond re-evaluating at every step.
- **Scale.** All costs share one harm scale (1 = worst outcome the deployment cares about).
  Mapping real harms onto it is a deployment decision.
- **Simulation is not evidence about people.** Results from the simulator test the policies
  under the simulator's assumptions only (see [experiments.md](experiments.md)). No
  human-participant study has been run yet.
