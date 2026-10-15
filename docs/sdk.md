# Python SDK reference

The Python SDK (`sdk/python`, import name `agentpause`, distribution name
`agentpause-toolkit`) is the decision engine. It has no third-party dependencies and makes no
network calls, except for the optional REST client. Installation is described in
[getting_started.md](getting_started.md).

Contents:

- [Concepts](#concepts)
- [`AgentPause`: the session API](#agentpause-the-session-api)
- [Describing an action](#describing-an-action)
- [Signal resolution and provenance](#signal-resolution-and-provenance)
- [The `Decision` object](#the-decision-object)
- [Explanations](#explanations)
- [Recording human responses](#recording-human-responses)
- [Worked example: a deferred question](#worked-example-a-deferred-question)
- [Guard decorator](#guard-decorator)
- [Persistence](#persistence)
- [HTTP client](#http-client)
- [Claude Code PreToolUse hook](#claude-code-pretooluse-hook)
- [TypeScript SDK](#typescript-sdk)

## Concepts

- Keep **one `AgentPause` instance per agent task**. It remembers recent interruptions
  (habituation), open assumptions, scheduled (deferred) questions, and the user's earlier
  responses.
- Before each side-effecting step, the agent calls `evaluate()` with **metadata** about the
  action: category, severity, reversibility, confidences, the assumptions it relies on, and
  the remaining plan. AgentPause never needs the action's content, such as an email body.
- The returned `Decision` says what to do:

| `DecisionType` | `should_proceed` | `should_ask` | What the agent should do |
|---|---|---|---|
| `CONTINUE` | True | False | Execute the action. |
| `DEFER` | True | False | Execute the action. A question was scheduled for a later step (`decision.deferred`, `pause.pending_questions`). The deferral never passes the first hard-to-undo step that depends on the answer. |
| `CLARIFY` | False | True | Ask the clarification question(s) in `decision.questions`, record the answer with `respond(..., "answer", answers=...)`, then evaluate the action again. |
| `ASK_HUMAN` | False | True | Show an approval card for this action (and any batched questions), then record `approve`, `edit` or `reject`. |
| `BLOCK` | False | False | Do not execute. Hand control to the user (`takeover`, `override`, or `cancel_task`). |

- After the human answers, call `respond()`. This updates the user history and resolves
  assumptions.

## `AgentPause`: the session API

```python
from agentpause import AgentPause

pause = AgentPause(
    policy="adaptive",       # registry name or alias, or an InterventionPolicy instance
    preferences=None,        # UserPreferences or dict (used by user_customized and the profile multiplier)
    parameters=None,         # ModelParameters or dict of overrides, e.g. {"interruption_cost": 0.03}
    explain="full",          # "full" | "light" | "none"
    state=None,              # an existing SessionState to resume
    # any other keyword arguments go to the policy constructor, e.g. threshold=0.5
)
```

| Member | Description |
|---|---|
| `evaluate(action=None, *, context=None, record=True, **signals) -> Decision` | Evaluate a proposed action. Pass either an `ActionContext` (positionally or as `context=`) or an action name plus keyword signals, not both. With `record=False`, the decision is not added to the session ("what if" query). |
| `respond(decision, response, *, answers=None) -> None` | Record the human's response (a `ResponseType` or its string value). `answers` maps assumption ids to the user's answer for clarification questions. |
| `explain_timing(decision) -> TimingExplanation` | "Why now / why not earlier / why not later". Returns `decision.timing` if it was already computed (explain level `full`), otherwise computes it from the session history. |
| `declare_assumption(id, description, confidence, *, kind="input", options=(), agent_value=None) -> Assumption` | Declare an interpretation of the user's intent that later actions depend on. `kind` is `goal`, `constraint`, `input` or `context`. |
| `set_plan(plan) -> None` | Replace the remaining plan (a list of `PlannedAction` or dicts). The plan enables timing lookahead, and therefore DEFER. |
| `resolve_assumption(assumption_id, *, correct=True) -> None` | Mark an assumption as `confirmed` (`correct=True`) or `corrected`. Resolved assumptions no longer lower intent confidence and are no longer asked about. |
| `pending_questions` (property) | `list[DeferredQuestion]`: questions scheduled for a later step and not yet asked. |
| `reset() -> None` | Start a new task: clear state, decisions and contexts. |
| `to_dict()` / `AgentPause.from_dict(data)` | Serialize and restore the session. See [Persistence](#persistence). |
| `guard(**kwargs)` | Decorator for tool functions. See [Guard decorator](#guard-decorator). |
| `policy`, `explainer`, `state`, `decisions` | The policy instance, the `Explainer`, the `SessionState`, and the list of recorded decisions. |

Policies can also be created directly with `create_policy(name, parameters=..., preferences=..., **config)`.
`available_policies()` lists the registry, and `register_policy(name, factory)` adds a policy.
See [policies.md](policies.md).

### Step indices

If neither the context nor the keyword signals contain `step`, AgentPause uses an internal
counter (`pause.state.step`) that advances by one with each recorded decision. Pass `step`
explicitly when:

- your agent has its own step index;
- you pass a `plan` (planned actions use absolute step indices);
- you re-evaluate the same step after a clarification. Otherwise the re-evaluation counts as
  the next step.

## Describing an action

### Keyword signals and `ActionContext`

`evaluate(action, **signals)` builds an `ActionContext` with the lenient constructor
`ActionContext.build`. It accepts:

- `consequence` as an alias of `category` (string, enum, or friendly alias);
- `user_intent_confidence` as an alias of `intent_confidence`;
- plain dicts for `assumptions` and `plan`, and string provenances;
- any unknown keyword, which is stored in `context.metadata`.

Only `action` is required.

| Field | Type | When missing | Meaning |
|---|---|---|---|
| `action` | `str` | required | Action name, e.g. `"send_email"` |
| `description` | `str` | `""` | Human-readable description, used in question prompts |
| `category` (`consequence`) | `ConsequenceCategory` or string | `other` | Coarse consequence category. Supplies default severity, recoverability and external effects |
| `severity` | float in [0, 1] | category prior | Harm if the action is wrong and nobody intervenes (1 = worst outcome the deployment cares about) |
| `reversible` | bool | — | Shortcut for recoverability: `True` → `max(prior, 0.9)`, `False` → `min(prior, 0.1)` |
| `recoverability` | float in [0, 1] | category prior | How completely a wrong action can be undone (1 = trivially). Wins over `reversible` if both are given |
| `agent_confidence` | float in [0, 1] | 0.8 | Agent's confidence that it executes the action correctly |
| `intent_confidence` | float in [0, 1] | 0.85, or derived from assumptions | Confidence that the action matches what the user meant, *not* attached to an explicit assumption |
| `task_progress` | float in [0, 1] | inferred from `plan`, else 0.5 | Progress through the task |
| `at_breakpoint` | bool | unknown | Whether the user is between sub-tasks (cheaper to interrupt) |
| `cognitive_load` | float in [0, 1] | 0.3 | Estimated user load |
| `external_effects` | bool | category prior | Whether the action affects people or systems outside the task |
| `requires_human_input` | bool | `False` | The step cannot be done without the human (e.g. credentials). Every policy returns BLOCK |
| `assumptions` | list of `Assumption` or dicts | `()` | Assumptions introduced or used at this step |
| `depends_on` | list of assumption ids | `()` | Assumptions (declared now or earlier) this action depends on |
| `plan` | list of `PlannedAction` or dicts | session plan | Remaining planned steps. Replaces the session plan when given |
| `step` | int | session counter | Absolute step index |
| `action_key` | str | `action` | Grouping key for learning from the user's past responses to similar actions |
| `provenance` | dict signal → `Provenance` | `agent_provided` | Where each supplied value came from |
| `metadata` | dict | `{}` | Free-form data; never used by the policies |

### `Assumption`

An interpretation of the user's intent that the agent acts on. Intent ambiguity is attached
to explicit assumptions so that AgentPause can ask about something specific, find the first
hard-to-undo action that depends on it (its *commitment point*), and decide whether the
question can wait.

| Field | Default | Meaning |
|---|---|---|
| `id` | required | Stable identifier |
| `description` | required | E.g. `"'next Friday' means Fri 14 Nov"` |
| `confidence` | required | Probability that the assumption is right |
| `kind` | `AssumptionKind.INPUT` | `goal`, `constraint`, `input` or `context`. By default only `input` and `context` questions may be deferred (see [policies.md](policies.md#deferrable-information-types)) |
| `options` | `()` | Choices to show in a clarification |
| `agent_value` | `None` | The value the agent assumed. An answer equal to it counts as a confirmation |
| `provenance` | `agent_provided` | Provenance of the confidence |

### `PlannedAction`

A future step, used for timing lookahead only. Unknown fields fall back to category priors.
Fields: `step` (absolute index, required), `action` (required), `category`, `description`,
`severity`, `recoverability`, `reversible`, `depends_on`, `at_breakpoint`, `cognitive_load`.

> The dataclasses `ActionContext`, `Assumption` and `PlannedAction` accept plain strings and
> lists as well as enum members: `category="data_entry"`, `kind="input"`, `options=[...]`, and
> `provenance={"agent_confidence": "estimated"}` are converted on construction. Consequence
> categories also accept the aliases understood by `ActionContext.build`.

### `UserPreferences`

| Field | Default | Effect |
|---|---|---|
| `profile` | `"balanced"` | Interruption-cost multiplier: `fewer_interruptions` ×2.5, `balanced` ×1, `maximum_control` ×0.25. Used by `adaptive`, `myopic_voi` and `user_customized` |
| `always_ask_categories` | `()` | Always ask before these categories |
| `never_ask_categories` | `()` | Never ask before these categories (unless a block or always-ask rule applies) |
| `block_categories` | `()` | Always BLOCK these categories |
| `ask_before_irreversible` | `False` | Ask before any action with recoverability below `commitment_recoverability` (0.5), except read-only ones |
| `ask_before_external` | `False` | Ask before actions with external effects |
| `allow_low_risk_autonomy` | `False` | Do not ask when consequence risk is below `low_risk_threshold` |
| `low_risk_threshold` | `0.15` | Threshold for the rule above |
| `max_interruptions_per_task` | `None` | Interruption budget. Once used up, ask/clarify decisions become CONTINUE |

The rules are applied only by the `user_customized` policy. The precedence order is in
[policies.md](policies.md#user-customized-user_customized). `UserPreferences.from_dict` rejects unknown
profiles.

### Consequence categories

Each category has a documented prior. These are authors' choices, not measurements (see
`agentpause/categories.py`). Override them whenever you know better.

| Category | Severity | Recoverability | External | Description |
|---|---|---|---|---|
| `read_only` | 0.02 | 1.0 | no | Reads or searches; no side effects |
| `internal_draft` | 0.05 | 1.0 | no | Drafts or notes visible only to the user |
| `data_entry` | 0.15 | 0.9 | no | Fills in forms that are not yet submitted |
| `local_modification` | 0.25 | 0.8 | no | Changes local data that can usually be restored |
| `scheduling` | 0.30 | 0.6 | yes | Calendar changes that notify other people |
| `external_communication` | 0.45 | 0.05 | yes | Messages that leave the user's control |
| `account_change` | 0.50 | 0.4 | no | Settings, subscriptions, permissions |
| `data_deletion` | 0.60 | 0.2 | no | Permanent deletion of user data |
| `data_sharing` | 0.65 | 0.05 | yes | Disclosing personal or confidential data |
| `financial_transaction` | 0.80 | 0.1 | yes | Purchases, payments, bookings |
| `other` | 0.30 | 0.5 | no | Uncategorized action (neutral prior) |

`parse_category` accepts the value, the enum, variants with spaces or hyphens
(`"external communication"`), and aliases: `read`, `search`, `draft`, `email`, `message`,
`communication`, `external`, `payment`, `purchase`, `financial`, `delete`, `deletion`,
`share`, `privacy`, `calendar`, `schedule`, `form`, `modify`, `file`, `settings`, `account`.
Unknown values map to `other`; they do not raise an error.

## Signal resolution and provenance

Before a policy decides, `resolve_signals` turns the raw context into a complete
`ResolvedSignals`. The rules are documented because they affect research validity:

- **Missing signals** fall back to a documented default (category prior or constant), are
  tagged `default`, and are listed in `decision.signals["missing"]`. The decision gets the
  reason code `MISSING_SIGNAL_DEFAULTED`.
- **Out-of-range values** are clamped to [0, 1], with a warning in `decision.warnings`.
- **Contradictions** (e.g. `reversible=True` with `recoverability=0.1`) keep the explicit
  number. A `CONTRADICTORY_SIGNALS` warning and reason code are added.
- **Intent confidence** is the minimum of the scalar `intent_confidence` and the product of
  the confidences of the *unresolved* assumptions the action depends on. It is then shrunk
  toward the user's observed disagreement rate for this `action_key` (see
  [policies.md](policies.md#learning-from-history)). The scalar part alone, after the same
  shrinkage, is kept as `residual_intent_confidence`. The adaptive policy uses it for the
  approval question, so that ambiguity attached to an assumption is not counted twice.
- **Breakpoint**: if `at_breakpoint` is missing and `task_progress` is 0, the start of the task
  is treated as a breakpoint (`inferred`). Otherwise it stays unknown.
- **Habituation** is always inferred from the session: `h = 1 − exp(−λ · n)`, where `n` is the
  number of interruptions in the last `habituation_window` steps.

Every resolved signal carries a **provenance**. It is shown in factor explanations, logged
with every decision, and used by the stability estimate:

| `Provenance` | Value | Meaning |
|---|---|---|
| `AGENT_PROVIDED` | `agent_provided` | Reported by the agent (the default for any value you pass) |
| `USER_PROVIDED` | `user_provided` | Stated by the user. These values are never perturbed by the stability estimate |
| `ESTIMATED` | `estimated` | Computed by a model or heuristic, e.g. a severity classifier |
| `INFERRED` | `inferred` | Derived inside AgentPause from other signals or history |
| `SIMULATED` | `simulated` | Produced by the simulator |
| `DEFAULT` | `default` | Nothing was provided; a documented prior or constant was used |

Set provenance per signal:

```python
from agentpause import AgentPause

pause = AgentPause()
decision = pause.evaluate(
    "book_hotel", consequence="financial_transaction",
    severity=0.6, cognitive_load=0.7,
    provenance={"severity": "estimated", "cognitive_load": "user_provided"},
)
print(decision.signals["provenance"])
# {'severity': 'estimated', 'recoverability': 'default', 'agent_confidence': 'default', ...,
#  'cognitive_load': 'user_provided', 'external_effects': 'default', 'habituation': 'inferred'}
```

## The `Decision` object

| Field | Type | Description |
|---|---|---|
| `decision` | `DecisionType` | `CONTINUE`, `CLARIFY`, `ASK_HUMAN`, `DEFER` or `BLOCK` |
| `score` | float in [0, 1] | Intervention pressure. For value-based policies, `B / (B + C)`, so `> 0.5` means asking is worth more than it costs |
| `policy`, `action`, `step` | | Which policy decided, about which action, at which step |
| `reason_codes` | `list[str]` | Stable machine-readable `ReasonCode` values (e.g. `IRREVERSIBLE_ACTION`, `DEFERRED_TO_BREAKPOINT`) |
| `recommended_intervention` | `InterventionKind` | `none`, `clarification`, `confirmation`, `batched_review` (several questions), `takeover` (BLOCK), `scheduled` (DEFER) |
| `questions` | `list[Question]` | Questions to ask now. Each has `id`, `kind`, `prompt`, `assumption_id`, `options`, `agent_value`, `benefit`, `cost`, `value`, and `piggybacked` (added to an interruption that happens anyway) |
| `deferred` | `list[DeferredQuestion]` | Questions scheduled for later: `assumption_id`, `description`, `kind`, `created_step`, `target_step`, `target_action`, `deadline_step`, `deadline_action`, `value_now`, `value_at_target` |
| `item_timings` | `list[ItemTiming]` | Adaptive policy only: the candidate moments evaluated for each question, with benefit, interruption cost, rework and net value (`TimingCandidate`) |
| `terms` | dict | Model terms, e.g. `p_error_action`, `error_cost`, `catch_probability`, `interruption_cost_now`, `benefit_action`, `value_action`, and per-assumption timing |
| `signals` | dict | Resolved signals with `provenance`, `missing`, `warnings`, `habituation`, `unresolved_dependencies`, history statistics |
| `warnings` | `list[str]` | Clamping, contradictions, undeclared dependencies |
| `explanation` | str | Plain-language explanation (template-based) |
| `confidence` | float or None | **Decision stability**, not model confidence: the share of perturbed inputs that give the same decision |
| `factors` | `list[Factor]` | Per-signal attribution (see below) |
| `counterfactuals` | `list[Counterfactual]` | Feature counterfactuals and the two timing counterfactuals |
| `timing` | `TimingExplanation` or None | `why_now`, `why_not_earlier`, `why_not_later`, plus `earlier` and `later` notes |
| `latency_ms` | float | Wall-clock time of `evaluate`, including explanations. Machine-dependent |

Properties and helpers:

- `should_ask` is True for CLARIFY and ASK_HUMAN.
- `should_proceed` is True for CONTINUE and DEFER.
- `is_blocked` is True for BLOCK.
- `interrupts` is True for CLARIFY, ASK_HUMAN and BLOCK.
- `top_factors(n=3)` returns the strongest factors in the direction of the decision.
- `to_dict()` / `Decision.from_dict()` serialize to and from JSON-ready dicts (`to_dict` also
  includes `should_ask`).

The full list of reason codes and their phrases is in `agentpause/explain/reasons.py` and
is served by `GET /api/v1/model`.

## Explanations

The `Explainer` adds explanations after the policy has decided. It never changes the
decision. It treats the policy as a black box and calls `policy.decide()` on modified inputs.
Every policy is therefore explained the same way, including custom ones.

| Level | Contents | Typical use |
|---|---|---|
| `full` (default) | Narrative, factor attribution, feature counterfactuals, timing explanation and timing counterfactuals, decision stability | Interactive use, user studies |
| `light` | Narrative and reason codes only | Large batches, hooks |
| `none` | The policy's reason codes only | Simulations (`ExperimentConfig.explain` defaults to `none`) |

- **Narrative.** Deterministic templates over the reason codes the policy actually emitted.
  No language model is used, so the text cannot describe reasons the policy did not have.
- **Factors** (occlusion). Each signal's `contribution` is `score(actual) − score(signal set
  to a low-risk reference)`. The references are: confidences 0.95, severity 0.05,
  recoverability 1.0, no external effects, at a breakpoint, load 0.3, progress 0.5. State
  factors are also computed: open assumptions (confidence set to 0.95), recent interruptions
  (history cleared), and past decisions for this action key (statistics removed). This is a
  local, one-at-a-time attribution. Interactions are not decomposed, and contributions need
  not sum to the score. Each factor has `level` (LOW/MEDIUM/HIGH), `provenance` and
  `direction` (`toward_intervention`, `toward_autonomy`, `neutral`).
- **Feature counterfactuals.** For each of agent confidence, intent confidence, severity,
  recoverability (grid step 0.05), cognitive load (step 0.1) and breakpoint, the explainer
  finds the nearest value that changes the decision. At most 3 are kept, nearest first, e.g.
  *"If the action were easily undone (it is hard to undo), AgentPause would have let the
  agent continue."*
- **Timing explanation.** *Why now / why not earlier / why not later*:
  - *Earlier* is read from the session history, which stores what the policy computed at each
    earlier step: the net value of asking each open question, and whether it was scheduled.
    Nothing is re-imagined after the fact.
  - *Later* comes from the adaptive policy's evaluation of planned future moments: their
    interruption cost, rework, and the commitment-point deadline.
  - For policies that do not plan (all baselines), the text says that the policy decides one
    step at a time, instead of inventing a reason.
- **Stability** (`decision.confidence`). The decision is re-run 16 times with uniform
  perturbations of the signals that are not `user_provided`: ±0.05 on confidences (and
  assumption confidences), ±0.1 on severity and recoverability, ±0.15 on load. The
  perturbations use a fixed seed, so the value is reproducible.

## Recording human responses

`pause.respond(decision, response, answers=None)` takes a `ResponseType`:

| Response | Meaning | Effect on user history | Effect on assumptions asked in the decision |
|---|---|---|---|
| `approve` | Proceed as proposed | Approval, weighted by `1 − habituation_effect · h` | Confirmed, unless `answers` says otherwise |
| `answer` | Answered a clarification | Approval (weighted) | Confirmed if the answer equals `agent_value`, otherwise corrected. Without `answers`: confirmed |
| `edit` | Proceed with corrected parameters | Disagreement | Corrected, unless `answers` says otherwise |
| `reject` | Do not execute; propose an alternative | Disagreement | Corrected, unless `answers` says otherwise |
| `takeover` | The human does the step | Disagreement | Only those in `answers` |
| `override` | The human overrides a BLOCK | Approval (weighted) | Only those in `answers` |
| `cancel_task` | Abandon the task | Disagreement | Only those in `answers` |
| `timeout` | No answer in time | Counted, neither approval nor disagreement | Only those in `answers` |
| `ask_why` | Explanation requested | No change | No change |

Approvals given while the user was habituated count for less, because they may be rubber
stamps. AgentPause never treats "approved" as ground truth for "correct". `respond` updates
statistics only for decisions that were recorded (`record=True`).

## Worked example: a deferred question

The agent picks a flight in the middle of a sub-task. It guessed the seat preference, and the
guess only matters for the purchase two steps later. Asking now would interrupt mid-task.
Asking at the purchase, which needs a confirmation anyway, costs less. So the adaptive
policy defers the question and asks it no later than the purchase, the first step that
cannot be undone.

```python
from agentpause import AgentPause, Assumption, AssumptionKind

pause = AgentPause(policy="adaptive")

# What the agent expects to do after the current step (plain dicts are parsed leniently).
plan = [
    {"step": 2, "action": "enter_details", "category": "data_entry",
     "at_breakpoint": True, "depends_on": ["seat"]},
    {"step": 3, "action": "purchase_ticket", "category": "financial_transaction",
     "severity": 0.8, "recoverability": 0.05, "at_breakpoint": False, "depends_on": ["seat"]},
    {"step": 4, "action": "wrap_up", "category": "internal_draft", "at_breakpoint": True},
]
# An interpretation of the user's request that the agent had to guess.
seat = Assumption("seat", "you want an aisle seat", confidence=0.75,
                  kind=AssumptionKind.INPUT, options=("aisle", "window"), agent_value="aisle")

common = {"agent_confidence": 0.95, "intent_confidence": 0.98, "cognitive_load": 0.5}

d1 = pause.evaluate("select_flight", consequence="internal_draft", step=1,
                    recoverability=1.0, at_breakpoint=False,
                    assumptions=[seat], plan=plan, **common)
print(d1.decision.value)                                  # DEFER
for q in pause.pending_questions:
    print(f"ask about {q.assumption_id!r} at step {q.target_step}, deadline step {q.deadline_step}")

d2 = pause.evaluate("enter_details", consequence="data_entry", step=2,
                    at_breakpoint=True, depends_on=["seat"], plan=plan[1:], **common)
print(d2.decision.value)                                  # DEFER (still scheduled for step 3)

d3 = pause.evaluate("purchase_ticket", consequence="financial_transaction", step=3,
                    severity=0.8, recoverability=0.05, at_breakpoint=False,
                    depends_on=["seat"], plan=plan[2:], **common)
print(d3.decision.value, [q.id for q in d3.questions])   # ASK_HUMAN ['action:purchase_ticket', 'assumption:seat']
print(d3.timing.why_not_earlier)
pause.respond(d3, "edit", answers={"seat": "window"})    # the user corrects the guess
print(pause.state.resolved)                               # {'seat': 'corrected'}
```

With `policy="myopic_voi"`, the same first step returns CLARIFY: that policy only asks
"is asking worth it right now?".

## Guard decorator

`pause.guard(...)` (or `agentpause.integrations.guard(pause, ...)`) wraps a tool function.
Each call is evaluated before the function runs.

```python
from agentpause import AgentPause, ResponseType
from agentpause.integrations import ActionBlocked, ActionRejected, InterventionRequired

pause = AgentPause(policy="adaptive")

def ask_user(decision):
    print(decision.explanation)
    for question in decision.questions:
        print("-", question.prompt)
    return True        # True/False, or a response name: "approve", "edit", "reject", ...

@pause.guard(signals={"consequence": "read_only", "agent_confidence": 0.95})
def search_flights(destination: str) -> list[str]:
    return [f"flight to {destination}"]

@pause.guard(
    action="send_email",
    signals={"consequence": "external_communication", "reversible": False},
    context_fn=lambda to, body: {"intent_confidence": 0.9 if "@" in to else 0.7},
    on_ask=ask_user,
)
def send_email(to: str, body: str) -> str:
    return f"sent to {to}"

search_flights("Vienna")                         # CONTINUE: runs
send_email("prof.smith@example.org", "Draft")    # ASK_HUMAN: ask_user approves, then it runs

@pause.guard(action="post_publicly",
             signals={"consequence": "external_communication", "reversible": False,
                      "intent_confidence": 0.6})
def post_publicly(text: str) -> str:
    return "posted"

try:
    post_publicly("hello")
except InterventionRequired as err:              # no on_ask handler was given
    pause.respond(err.decision, ResponseType.REJECT)
```

| Argument | Meaning |
|---|---|
| `action` | Action name (default: the function name) |
| `signals` | Static signals for every call |
| `context_fn(*args, **kwargs)` | Returns dynamic signals computed from the call arguments. Return metadata only (e.g. a confidence), never secrets or message bodies |
| `on_ask(decision)` | Shows the intervention to the user and returns `True`/`False` or a response name. `True` maps to `approve`, `False` to `reject` |

Behaviour:

- CONTINUE and DEFER run the function.
- BLOCK raises `ActionBlocked` (`err.decision`).
- CLARIFY and ASK_HUMAN call `on_ask`. If no `on_ask` was given, they raise
  `InterventionRequired` (`err.decision`). Catch it in your agent loop, show the decision,
  call `pause.respond(...)`, and retry or skip.
- After `on_ask`, the response is recorded with `respond`. `approve`, `edit`, `answer` and
  `override` run the function. Any other response raises `ActionRejected` (`err.decision`,
  `err.response`).

## Persistence

`pause.to_dict()` returns `{"policy": policy.describe(), "explain": level, "state": state.to_dict()}`.
This is everything needed to resume a session in another process:

```python
import json
from agentpause import AgentPause

pause = AgentPause(policy="fixed_threshold", threshold=0.5)
pause.evaluate("send_email", consequence="email", reversible=False)

saved = json.dumps(pause.to_dict())                 # store it anywhere
restored = AgentPause.from_dict(json.loads(saved))
print(restored.policy.name, restored.policy.config(), restored.state.step)
# fixed_threshold {'threshold': 0.5, 'mode': 'consequence'} 1
```

`from_dict` re-creates the policy **by its registry name** (stored as `policy` in
`to_dict()["policy"]`), with its stored parameters, preferences and configuration, and then
restores any display label (e.g. `adaptive@0.03`) as `policy.name`. Restoring is
deterministic: a restored session makes the same decisions as the original. The `learned`
policy stores its `weights_path`, so custom weights are reloaded. Custom policies must be
registered with `register_policy` in the restoring process first.

`Decision`, `SessionState`, `ActionContext`, `Assumption`, `PlannedAction`,
`UserPreferences` and `ModelParameters` all have `to_dict` / `from_dict`.

## HTTP client

`AgentPauseClient` talks to a running AgentPause server (see [api.md](api.md)). It uses only
the standard library.

```python
from agentpause import AgentPauseAPIError, AgentPauseClient

client = AgentPauseClient("http://localhost:8000", token=None, timeout=15.0)
print(client.health()["status"])

# Stateless: nothing is stored on the server.
decision = client.evaluate(
    "send_email", policy="adaptive", explain="light",
    consequence="external_communication", reversible=False, intent_confidence=0.72,
)

# Stateful: the server keeps history, habituation and open assumptions for the session.
session = client.create_session(mode="api", policy="adaptive")
d = client.submit_action(session["id"], "send_email",
                         consequence="external_communication", reversible=False)
if d.should_ask:
    client.submit_intervention(session["id"], "approve")

try:
    client.get_session("does-not-exist")
except AgentPauseAPIError as err:
    print(err.status, err.detail)        # 404 Session does-not-exist not found
```

| Method | Endpoint |
|---|---|
| `health()` | `GET /api/v1/health` |
| `policies()` | `GET /api/v1/policies` |
| `evaluate(action, *, policy="adaptive", policy_config=None, preferences=None, explain="full", **signals) -> Decision` | `POST /api/v1/evaluate` |
| `create_session(**fields)` | `POST /api/v1/session` |
| `submit_action(session_id, action, **signals) -> Decision` | `POST /api/v1/action` |
| `submit_intervention(session_id, response, *, intervention_id=None, answers=None)` | `POST /api/v1/intervention` |
| `get_session(session_id)` | `GET /api/v1/session/{id}` |
| `get_events(session_id)` | `GET /api/v1/session/{id}/events` |
| `metrics(**filters)` | `GET /api/v1/metrics` |
| `create_experiment(config)` / `get_experiment(experiment_id)` | `POST /api/v1/experiments` / `GET /api/v1/experiments/{id}` |
| `request(method, path, body=None, params=None)` | Any endpoint |

`token` is sent as `Authorization: Bearer <token>`. It is only needed for the
researcher endpoints when the server has `AGENTPAUSE_ADMIN_TOKEN` set. HTTP errors raise
`AgentPauseAPIError` with `status` and `detail`.

## Claude Code PreToolUse hook

`agentpause-claude-hook` (module `agentpause.integrations.claude_code`) is an **example**
adapter that runs AgentPause as a Claude Code `PreToolUse` hook. It reads the hook event
JSON from stdin, classifies the tool call, evaluates it, and prints a permission decision.

Add it to `.claude/settings.json` (project) or `~/.claude/settings.json` (user). This is
[`examples/claude_code_settings.json`](../examples/claude_code_settings.json):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit|WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "agentpause-claude-hook",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- The matcher limits the hook to tools with side effects (plus `WebFetch`). Use
  `"matcher": "*"` to evaluate every tool call. Read-only tools are then classified as
  `read_only`, but each call still records a step in the session state.
- If the virtual environment is not on Claude Code's `PATH`, use the absolute path, e.g.
  `/path/to/AgentPause/.venv/bin/agentpause-claude-hook`.

Mapping of decisions:

| AgentPause | Claude Code `permissionDecision` |
|---|---|
| CONTINUE, DEFER | `allow` |
| CLARIFY, ASK_HUMAN | `ask` (the explanation is shown in the prompt) |
| BLOCK | `deny` (the explanation is returned to the model) |

The reason is returned in `permissionDecisionReason`, prefixed with `[AgentPause]`. Example
output for `git push origin main`:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
  "permissionDecisionReason": "[AgentPause] AgentPause asked for your confirmation because the action is difficult to undo and it affects people or systems outside this task. ..."}}
```

Tool classification (a heuristic over tool names and shell commands):

| Tool call | Signals |
|---|---|
| `Read`, `Grep`, `Glob`, `LS`, `WebSearch`, `WebFetch`, `TodoWrite`, `NotebookRead` | `read_only`, agent confidence 0.95 |
| `Write`, `Edit`, `MultiEdit`, `NotebookEdit` | `local_modification`, recoverability 0.8 |
| `Bash` with a destructive command (`rm -r`, `rm -f`, `git reset --hard`, `git clean`, `drop table`, `truncate table`, `mkfs`, `dd if=`) | `data_deletion`, recoverability 0.1, severity 0.7 |
| `Bash` with an external command (`git push`, `npm publish`, `twine upload`, `curl -X POST/PUT/DELETE`, `gh pr/issue create/comment/merge`, `kubectl apply/delete`, `terraform apply`) | `external_communication`, recoverability 0.2, severity 0.5 |
| `Bash` starting with a read-only command (`ls`, `cat`, `head`, `tail`, `grep`, `rg`, `find`, `pwd`, `echo`, `git status/diff/log/show`, `wc`, `which`) | `read_only` |
| Other `Bash` | `local_modification`, recoverability 0.6 |
| `mcp__*` tools whose name contains send, post, create, delete, update or publish | `external_communication` |
| Anything else | `other` |

Environment variables:

| Variable | Default | Effect |
|---|---|---|
| `AGENTPAUSE_POLICY` | `adaptive` | Policy to use. If it differs from the policy stored in a session's state file, the hook switches policy and keeps the session's history |
| `AGENTPAUSE_CACHE_DIR` | `~/.cache/agentpause/claude-code` | Folder for per-session state files (`<session_id>.json`). Only action metadata is stored, never file contents |

To set the policy, prefix the command, e.g.
`"command": "AGENTPAUSE_POLICY=rule_based /path/to/.venv/bin/agentpause-claude-hook"`.

Limitations:

- The tool-to-category mapping is coarse. It is **not a security boundary**. Keep Claude
  Code's own permission rules and sandboxing.
- A hook cannot postpone a question to a later step, so DEFER maps to `allow`.
- The hook uses explain level `light`.
- Input that is not valid JSON makes the hook exit with status 0 and no output, so Claude
  Code's own rules apply.

## TypeScript SDK

A typed REST client for JavaScript and TypeScript agents lives in `sdk/typescript`
(`@agentpause/sdk`). See [`sdk/typescript/README.md`](../sdk/typescript/README.md).
