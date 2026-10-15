# Architecture

AgentPause is a monorepo with four independently usable layers. The core decision engine has
**no third-party dependencies**, so it can be embedded in any Python agent. Everything else is
built on top of it.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ frontend/  Next.js + TypeScript + Tailwind                               │
│   demo · decision lab · policy comparison · dashboard · experiments ·    │
│   event log · study mode · preferences · about                           │
└───────────────▲──────────────────────────────────────────────────────────┘
                │ REST (JSON) + Server-Sent Events, proxied under /api
┌───────────────┴──────────────────────────────────────────────────────────┐
│ backend/app  FastAPI + SQLAlchemy (SQLite default, PostgreSQL-compatible)│
│   routers → services → persistence; OpenAPI at /docs                     │
└───────▲───────────────────────────────▲──────────────────────────────────┘
        │                               │
┌───────┴────────────────────┐  ┌───────┴──────────────────────────────────┐
│ simulator/ agentpause_sim  │  │ sdk/typescript  @agentpause/sdk          │
│  scenarios (JSON) · episode│  │  typed REST client for JS/TS agents      │
│  engine · simulated user · │  └──────────────────────────────────────────┘
│  experiments · metrics ·   │
│  export · learned-policy   │
│  training · CLI            │
└───────▲────────────────────┘
        │
┌───────┴──────────────────────────────────────────────────────────────────┐
│ sdk/python  agentpause (pure Python ≥3.11, zero dependencies)            │
│  context & signals · intervention model · policies · explainer ·         │
│  timing counterfactuals · AgentPause session API · REST client ·         │
│  integrations (tool guard, Claude Code hook)                             │
└──────────────────────────────────────────────────────────────────────────┘
```

| Layer | Folder | Distribution | Import |
|---|---|---|---|
| Decision engine and SDK | `sdk/python` | `agentpause-toolkit` | `agentpause` |
| Simulator and experiment framework | `simulator` | `agentpause-simulator` | `agentpause_sim` |
| REST API, persistence, study mode | `backend` | `agentpause-server` | `app` |
| Web app | `frontend` | `@agentpause/frontend` (private) | — |
| TypeScript client | `sdk/typescript` | `@agentpause/sdk` | — |

Setup is described in [getting_started.md](getting_started.md).

## 1. Where AgentPause sits

```
USER ──instruction──► AI AGENT ──proposed action + context──► AGENTPAUSE
                                                                 │
             ┌──────────┬────────────┬──────────────┬──────────┴──┐
          CONTINUE   CLARIFY     ASK_HUMAN        DEFER          BLOCK
          execute    ask about   approval card    execute now,   do not execute;
                     an intent   for this action  ask at a later hand control
                     assumption                   step           back to the user
                                                                 │
                                                                 ▼
                                                            ENVIRONMENT
                                                            (simulated)
```

The agent describes each proposed action with **metadata**:

- category, severity and reversibility;
- its own confidence and the confidence that it understood the user's intent;
- the assumptions it depends on;
- its position in the plan.

AgentPause never needs the action's content (for example, an email body), which is a
deliberate privacy property. See [SECURITY.md](../SECURITY.md).

## 2. Core engine (`sdk/python/src/agentpause`)

| Module | Responsibility |
|---|---|
| `types.py` | Enums: `DecisionType`, `InterventionKind`, `Provenance`, `ConsequenceCategory`, `AssumptionKind`, `ResponseType`, `Level` |
| `context.py` | Input dataclasses: `ActionContext`, `Assumption`, `PlannedAction`, `UserPreferences`. `ActionContext.build` is the lenient constructor used by the SDK and the API |
| `categories.py` | Documented default priors per consequence category (severity, recoverability, external effects) and category aliases |
| `signals.py` | `resolve_signals` → `ResolvedSignals`: fills defaults, clamps ranges, records provenance, flags contradictions and missing data, combines intent confidence with open assumptions and user history |
| `state.py` | `SessionState`: step index, history (`HistoryEntry`), weighted approval statistics (`ActionStats`), interruption steps, assumptions, resolved assumptions, pending (deferred) questions, plan |
| `model.py` | The intervention value model: `ModelParameters`, error probability, error cost, habituation, catch probability, interruption cost, rework, commitment points, score. Pure functions |
| `decision.py` | `Decision`, `Factor`, `Question`, `DeferredQuestion`, `TimingCandidate`, `ItemTiming`, `Counterfactual`, `TimingNote`, `TimingExplanation` |
| `policies/` | `base.py` (interface and helpers), `baselines.py`, `adaptive.py` (adaptive and myopic), `customized.py`, `learned.py` (+ bundled `learned_weights.json`), `registry.py` (`create_policy`, `register_policy`, `available_policies`, `POLICY_INFO`, aliases) |
| `explain/` | `reasons.py` (reason codes and phrases), `narrative.py` (template explanations), `factors.py` (occlusion attribution), `counterfactual.py` (feature counterfactuals, decision stability), `timing.py` (timing counterfactuals); `Explainer` in `__init__.py` |
| `session.py` | `AgentPause`: the high-level SDK object (evaluate → respond → explain; assumptions, plan, persistence, guard) |
| `client.py` | `AgentPauseClient`: REST client using only the standard library |
| `integrations/` | `guard.py` (decorator for tool functions, with `InterventionRequired`, `ActionBlocked`, `ActionRejected`); `claude_code.py` (Claude Code `PreToolUse` hook adapter, console script `agentpause-claude-hook`) |

### Policy interface

```python
class InterventionPolicy(ABC):
    name: str = "base"
    summary: str = ""

    def __init__(self, parameters: ModelParameters | None = None,
                 preferences: UserPreferences | None = None) -> None: ...

    @abstractmethod
    def decide(self, context: ActionContext, state: SessionState) -> Decision: ...

    def config(self) -> dict: ...     # policy-specific hyperparameters (override)
    def describe(self) -> dict: ...   # name, summary, config, parameters, preferences
```

`decide` returns the *core* decision: type, score, reason codes, model terms and, for the
adaptive policy, the timing analysis (`item_timings`, `deferred`). It must be pure: it may
read the state but not modify it, and it may not use randomness or wall-clock time.

Explanations are added afterwards by the `Explainer`. It treats the policy as a black box and
calls `decide` on modified contexts and states. Factor attributions, feature counterfactuals,
stability, and the "why now / why not earlier" timing explanation therefore work for every
policy, including policies that researchers add later. "Why not later" refers to specific
future steps only for policies that fill `item_timings`, which is currently the adaptive
policy. For the others, the explanation says that they decide one step at a time.

| Policy (`name`) | Class | Origin of the design |
|---|---|---|
| `full_autonomy` | `FullAutonomyPolicy` | AutoGen `NEVER`, OpenHands `NeverConfirm` |
| `always_confirm` | `AlwaysConfirmPolicy` | AutoGen `ALWAYS`, OpenHands `AlwaysConfirm` |
| `fixed_threshold` | `ThresholdPolicy` | OpenHands `ConfirmRisky`, Mastra "classifier ≥ τ" |
| `confidence_threshold` | `ConfidenceThresholdPolicy` | KnowNo / Warp "ask when uncertain" (non-conformal simplification) |
| `rule_based` | `RuleBasedPolicy` | Magentic-UI irreversibility labels; ask-or-act rules |
| `myopic_voi` | `MyopicVOIPolicy` (an `AdaptivePolicy` with `timing=False`) | Horvitz 1999 / Dong et al. 2026: value of asking *now* only |
| `adaptive` | `AdaptivePolicy` | This project: trajectory-aware timing with DEFER and batching |
| `user_customized` | `UserCustomizedPolicy` | A base policy (default `adaptive`) plus user rules and profile |
| `learned` | `LearnedPolicy` | Experimental logistic model trained on simulator logs |

The adaptive policy evaluates, for each open question:

- the value of asking now;
- the value of asking at later planned moments, up to the question's commitment point (the
  first dependent step that is hard to undo). The later moments are natural breakpoints,
  steps whose own confirmation is expected anyway (*anticipated confirmations*), and the
  deadline itself.

Questions asked at a moment when an interruption happens anyway pay only a marginal cost
(batching). Only `input` and `context` assumptions may be deferred. The full description,
equations and defaults are in [policies.md](policies.md).

## 3. Simulator (`simulator/src/agentpause_sim`)

| Module | Responsibility |
|---|---|
| `scenario.py` | Scenario dataclasses, JSON parsing and validation, bundled scenario loading (`list_scenarios`, `load_scenario`, `load_scenario_file`) |
| `scenarios/*.json` | Six bundled scenarios: travel, email, shopping, files, calendar, research |
| `engine.py` | `EpisodeEngine`, `EngineConfig`, `EpisodeState`, `ErrorEvent`, `StepResult` |
| `user.py` | `SimulatedUser`, `SimulatedUserParams`, `CardTruth`, `HumanResponse` |
| `rng.py` | Order-independent random streams derived with SHA-256 from keys |
| `metrics.py` | `METRICS` catalog, `EpisodeSummary`, `summarize`, `aggregate` (bootstrap CIs), `paired_comparison` |
| `experiment.py` | `ExperimentConfig`, `PolicySpec`, `ConditionSpec`, `run_episode`, `run_experiment`, `ExperimentResult`, result hash |
| `ablation.py` | `SignalAblation`: hides signals from a policy (RQ2) |
| `export.py` | CSV/JSON export (`RECORD_COLUMNS`, `rows_to_csv`, `write_result`) |
| `learning.py` | Training pipeline for the experimental learned policy |
| `cli.py` | `agentpause-sim run | scenarios | show` |

- **Scenarios** are JSON files. Each has:
  - a goal and a brief;
  - intent **assumptions**, with kinds and "if wrong" consequences;
  - steps with category, severity, recoverability, breakpoint flag, load, previews, undo
    descriptions and alternatives;
  - **mistakes** with probabilities, visibility and harm steps.

  The schema is validated at load time.
- **`EpisodeEngine`** is a serializable state machine:
  - `step()` proposes the next action, asks AgentPause, and either executes it (simulated)
    or opens an intervention card;
  - `respond()` applies a human response. After a CLARIFY answer, the same step is proposed
    again.

  The same engine powers batch experiments (with a simulated user) and the interactive web
  demo and study mode (with a real person). Its state is stored as JSON between HTTP
  requests.
- **Seeding.** An episode's randomness derives from `(seed, scenario_id, episode)` plus a
  purpose key: injected mistakes, wrong assumptions, confidence noise, and simulated-user
  behaviour. Policies do not consume randomness, so all policies face **identical** injected
  errors (common random numbers). This makes paired comparison possible.
- **Simulated user.** It models vigilance, clarification accuracy, habituation, false
  rejections, block overrides, and response time. Its parameters can be set *differently*
  from the adaptive policy's internal assumptions, to test robustness under model
  misspecification.
- **Ground truth.** Because errors are scripted, each intervention can be labelled
  necessary or unnecessary, and each error as caught, harmful (missed or human miss) or
  averted.
- **Experiments.** An `ExperimentConfig` (TOML or JSON) goes into `run_experiment()`, which
  produces:
  - per-decision record dicts (columns in `RECORD_COLUMNS`) and per-episode
    `EpisodeSummary`s;
  - aggregate metrics with deterministic bootstrap confidence intervals;
  - paired comparisons and a result hash.

  `write_result` exports `records.csv`, `episodes.csv`, `summary.json` and `config.json`.

Details are in [experiments.md](experiments.md).

## 4. Backend (`backend/app`)

```
app/
  main.py            FastAPI app factory, CORS, routers; tables are created at startup
  config.py          Settings from environment variables (no .env file is loaded)
  db.py              SQLAlchemy engine/session (SQLite default; DATABASE_URL for PostgreSQL)
  deps.py            Dependencies: DB session, settings, researcher-token check
  models.py          ORM tables
  schemas/           Pydantic request/response models (OpenAPI)
  services/          sessions, experiments, metrics, study, instruments, common helpers
  routers/           meta, evaluate, sessions, research, study (all under /api/v1)
  instruments/       Questionnaire definitions (JSON)
```

ORM tables:

| Table | Holds |
|---|---|
| `sessions` | Interactive demo, study, and external-API sessions, with the serialized engine/session state |
| `events` | Append-only log of proposals, decisions, responses, executions, and outcomes. Denormalized filter columns (scenario, policy, participant, decision, risk level) |
| `interventions` | Pending and resolved human interventions, with response, answers, response time and "why" requests |
| `experiments` | Configuration, status, progress, and summary of batch simulation experiments |
| `experiment_episodes` | Per-episode summaries of simulation experiments |
| `experiment_records` | Flat per-decision records of simulation experiments |
| `participants` | Pseudonymous codes, counterbalanced plans, explanation condition, consent and completion. No PII |
| `questionnaire_responses` | Instrument responses and scores, keyed by participant code, block and policy |
| `study_config` | The active study configuration (JSON) |

- Long-running experiments run in a background thread. The client polls
  `GET /api/v1/experiments/{id}`; `?wait=true` runs synchronously.
- Live session events are available as Server-Sent Events at
  `GET /api/v1/session/{id}/stream`.
- Researcher endpoints (listing, exports, study configuration, deletion) require
  `Authorization: Bearer <AGENTPAUSE_ADMIN_TOKEN>` when that variable is set.

Endpoints and configuration are listed in [api.md](api.md).

## 5. Frontend (`frontend/`)

Next.js App Router with client components that talk to the backend through a typed API
client (`lib/api.ts`). Requests go to `/api/*`, which Next.js rewrites to the backend, so the
browser never needs CORS. `/docs` and `/redoc` are rewritten too. The backend address comes
from `BACKEND_URL` (default `http://localhost:8000`). It is read when the dev server starts,
or at build time for production builds.

| Path | Page |
|---|---|
| `/` | Landing |
| `/demo` | Interactive demo: live timeline, intervention card, explanation panel |
| `/lab` | Decision lab: move the signals and watch the decision and its counterfactuals |
| `/compare` | Policy comparison on simulated episodes |
| `/preferences` | Autonomy preferences |
| `/dashboard` | Research dashboard with filters |
| `/experiments`, `/experiments/[id]` | Experiment runner and results |
| `/events` | Event log with live tail and export |
| `/study` | Participant flow; `/study/admin` for researchers |
| `/about` | Methodology, limitations, citations |

## 6. Data flow of one interactive step

1. The UI calls `POST /api/v1/session/{id}/step`.
2. The backend loads the session's serialized `EpisodeEngine` from the database. This
   contains the episode state, the engine configuration, and the `AgentPause` session (policy
   description and `SessionState`).
3. The engine builds the `ActionContext` for the next scenario step. Injected mistakes lower
   the agent's reported confidence according to the calibration setting.
4. `AgentPause.evaluate()` runs the policy, then the explainer, and returns a `Decision`.
5. Depending on the decision:
   - for CONTINUE or DEFER, the engine executes the step (simulated) and records outcomes;
   - for CLARIFY, ASK_HUMAN, or BLOCK, it opens an intervention card and an `interventions`
     row is created.
6. Events are appended and the updated state is saved. The response carries the decision,
   any open card (without ground-truth fields), and the new events. In study mode, the
   decision is reduced according to the participant's explanation condition.
7. The participant responds through `POST /api/v1/intervention`, and the engine continues.
   After a clarification answer, it proposes the same step again.

For `api` sessions, your own agent calls `POST /api/v1/action` instead of `/step`, and the
backend keeps only the `AgentPause` state.

## 7. Reproducibility guarantees

- The core engine is deterministic: no wall-clock time or randomness enters a decision. The
  stability estimate uses a fixed internal seed.
- Each simulator episode is a pure function of: the scenario, the policy configuration, the
  seed, the episode index, the simulated-user parameters, and the engine configuration.
- `decision_latency_ms` is measured wall-clock time. It is the only machine-dependent field
  in records and episode summaries, and it is excluded from the result hash. The run time
  `duration_s` is not hashed either.
- Versioned configs live in `experiments/configs/`.
  - `experiments/reproduce_all.py` trains the learned policy, runs every config, generates
    the figures (`experiments/generate_figures.py`), and writes the result hashes to
    `experiments/results/hashes.json`.
  - `scripts/check_reproducibility.py` re-runs the configs in a temporary directory and
    compares their hashes with the committed reference hashes in
    `experiments/results/reference/`.
- The bundled configs use a held-out evaluation seed (314159), separate from the development
  seed (20261014) used to choose defaults.

## 8. Extension points

- **New policy.** Subclass `InterventionPolicy` and register it with
  `register_policy("name", factory)`. It immediately gets explanations, timing
  counterfactuals, simulation, and API support in the same process. See
  [policies.md](policies.md#adding-a-policy).
- **New scenario.** Add a JSON file under `simulator/src/agentpause_sim/scenarios/`. The schema
  is validated at load time. See [experiments.md](experiments.md#scenario-file-format).
- **New signal provider.** Compute a signal (for example a WebGuard or ToolEmu severity
  estimate, or a conformal confidence) and pass it with `provenance={"severity": "estimated"}`
  (or `inferred`).
- **New questionnaire.** Add an instrument definition JSON under `backend/app/instruments/`.
  Supply item text that may not be redistributed through `INSTRUMENTS_LOCAL_DIR`. See
  [experiments.md](experiments.md#questionnaire-instruments).

## 9. Deployment

- **Local development**: Uvicorn for the backend (port 8000) and `npm run dev` for the web
  app (port 3100), or both together with `scripts/dev.sh`. See
  [getting_started.md](getting_started.md).
- **Containers**: the multi-stage `Dockerfile` has a `backend` target (Python 3.13, Uvicorn,
  health check on `/api/v1/health`) and a `frontend` target (Next.js standalone server,
  Node 22). `docker compose up --build` starts the two services:
  - `backend` on port 8000, with SQLite in the `agentpause-data` volume;
  - `frontend` on host port 3100 (container port 3000), built with `BACKEND_URL=http://backend:8000`.

  An optional `postgres` service is available under the `postgres` profile.
- **Database**: SQLite by default (`./data/agentpause.db` locally, `/data/agentpause.db` in
  the container). Set `DATABASE_URL` for PostgreSQL (install the `postgres` extra; the
  container image includes it).
