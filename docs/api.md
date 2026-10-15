# REST API

The backend (`backend/app`, FastAPI) serves the decision engine, interactive sessions, the
simulator, experiments, the event log, and the study mode over HTTP. Start it with
`uvicorn app.main:app --app-dir backend --reload` (see [getting_started.md](getting_started.md)).

- All endpoints are under **`/api/v1`**. The API version follows the SDK version (`0.1.0`).
- **OpenAPI**: Swagger UI at `/docs`, ReDoc at `/redoc`, and the schema at
  `/api/v1/openapi.json`. The web app proxies `/docs`, `/redoc` and `/api/*` to the backend,
  so the same paths work on port 3100.
- Every agent action in the bundled scenarios is **simulated**. Results from `/compare` and
  `/experiments` are simulated and are labelled as such in their responses (`note`).
- Send action **metadata** only. Never send passwords, tokens, or private message content.

The examples use these shell variables:

```bash
BASE=http://localhost:8000/api/v1
TOKEN=change-me            # only needed if AGENTPAUSE_ADMIN_TOKEN is set on the server
```

Contents:

- [Configuration](#configuration)
- [Authentication](#authentication)
- [Conventions](#conventions)
- [Endpoint overview](#endpoint-overview)
- [Meta](#meta)
- [Evaluate](#evaluate)
- [Sessions and interventions](#sessions-and-interventions)
- [Live events (SSE)](#live-events-sse)
- [Event log, metrics, comparisons, experiments](#event-log-metrics-comparisons-experiments)
- [Study mode](#study-mode)
- [Exports](#exports)

## Configuration

The backend reads these environment variables at startup (`backend/app/config.py`).
`.env.example` at the repository root lists them with comments. The backend does not load a
`.env` file itself: set the variables in the process environment. Docker Compose reads `.env`
for substitution into `docker-compose.yml`, which passes `DATABASE_URL`, `CORS_ORIGINS`,
`AGENTPAUSE_ADMIN_TOKEN`, `AGENTPAUSE_ENV` and `MAX_EXPERIMENT_EPISODES` to the backend
container.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/agentpause.db` | SQLAlchemy URL. The SQLite folder is created if missing (relative to the working directory). For PostgreSQL, install `backend[postgres]` and use e.g. `postgresql+psycopg://user:pass@host/db` |
| `CORS_ORIGINS` | `http://localhost:3100` | Comma-separated list of allowed browser origins. Not needed when the browser goes through the Next.js proxy |
| `AGENTPAUSE_ADMIN_TOKEN` | unset | If set, researcher endpoints require `Authorization: Bearer <token>`. See [Authentication](#authentication) |
| `MAX_EXPERIMENT_EPISODES` | `20000` | Maximum total episodes (scenarios × policies × conditions × episodes) for `POST /experiments` |
| `MAX_COMPARE_EPISODES` | `3000` | Maximum total episodes for `POST /compare` |
| `INSTRUMENTS_LOCAL_DIR` | unset | Folder with locally supplied questionnaire items for instruments that are not redistributed (see [experiments.md](experiments.md#questionnaire-instruments)) |
| `AGENTPAUSE_ENV` | `development` | Free-text environment label, reported by `/health` |

The web app reads `BACKEND_URL` (default `http://localhost:8000`) to know where to proxy
`/api/*`, `/docs` and `/redoc`. This value is compiled into production builds. The web app
also reads an optional `NEXT_PUBLIC_REPO_URL`, a link to the source repository that the app
shows on its pages.

## Authentication

There are no user accounts. One optional shared **researcher token** protects the
endpoints that list, export, configure or delete data:

| Protected endpoint | Purpose |
|---|---|
| `GET /sessions` | List all sessions |
| `DELETE /session/{session_id}` | Delete a session and its events |
| `GET /events` | Event log across sessions (JSON or CSV) |
| `GET /experiments/{experiment_id}/export` | Export experiment data |
| `DELETE /experiments/{experiment_id}` | Delete an experiment |
| `PUT /study/config` | Change the study configuration |
| `GET /study/export` | Export questionnaire data |

- If `AGENTPAUSE_ADMIN_TOKEN` is **unset**, these endpoints are open. This is meant for
  local, single-researcher use.
- If it is **set**, these endpoints require `Authorization: Bearer <token>`. Without it they
  return `401 {"detail": "Researcher token required"}`. The token comparison is
  constant-time.
- All other endpoints are open, including the participant-facing study endpoints and
  `GET /session/{id}`. Session ids and participant codes are random, but they are not
  secrets with access control.
- **Set a token before exposing the server to study participants.**
- `GET /health` reports `"auth": true` when a token is configured.

## Conventions

- Request and response bodies are JSON, except the CSV exports and the SSE stream.
- **Errors** use FastAPI's format `{"detail": ...}`:
  - `401`: researcher token missing or wrong;
  - `403`: study block started before consent was recorded;
  - `404`: unknown session, scenario, experiment, participant or instrument;
  - `409`: state conflict (e.g. stepping while a card is open, responding when nothing is
    pending, a stale `intervention_id`, an instrument without item text);
  - `422`: validation error (bad field, unknown policy, value outside [0, 1], disallowed
    response, episode limit exceeded).
- **Policy spec.** Wherever a policy is expected, pass a name (`"adaptive"`, or any alias) or
  an object:

  ```json
  {
    "name": "fixed_threshold",
    "config": {"threshold": 0.35},
    "parameters": {"undo_cost_fraction": 0.1},
    "preferences": {"profile": "balanced"},
    "label": "fixed@0.35"
  }
  ```

  - `config` holds policy keyword arguments.
  - `parameters` holds `ModelParameters` overrides. Unknown keys return 422.
  - `preferences` holds `UserPreferences`.
  - `label` renames the policy in results, sessions, and the event log. Sessions restore the
    policy by its registry name and keep the label.

  Policies and their parameters are described in [policies.md](policies.md).
- **Action context** (`ActionContextIn`) has the same fields as the SDK's `ActionContext`:
  - `action` (required, 1–128 characters), `description` (≤ 500 characters);
  - `consequence` or `category`;
  - `severity`, `reversible`, `recoverability`, `agent_confidence`, `intent_confidence`,
    `task_progress`, `at_breakpoint`, `cognitive_load`, `external_effects`,
    `requires_human_input`;
  - `assumptions` (`id`, `description`, `confidence`, `kind`, `options`, `agent_value`),
    `depends_on`, `plan` (`step`, `action`, `category`, `description`, `severity`,
    `recoverability`, `reversible`, `depends_on`, `at_breakpoint`, `cognitive_load`);
  - `step`, `action_key`, `provenance`.

  Numeric signals must be in [0, 1]. Missing signals use documented defaults (see
  [sdk.md](sdk.md#describing-an-action)).
- **Decision** (`DecisionOut`) is `Decision.to_dict()`: `decision`, `score`, `confidence`,
  `policy`, `action`, `step`, `reason_codes`, `explanation`, `recommended_intervention`,
  `should_ask`, `questions`, `deferred`, `factors`, `counterfactuals`, `timing`,
  `item_timings`, `terms`, `signals`, `warnings`, `latency_ms`. See
  [sdk.md](sdk.md#the-decision-object).

## Endpoint overview

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/health` | — | Service health |
| GET | `/policies` | — | Available intervention policies |
| GET | `/model` | — | Default model parameters, category priors, reason codes, metric definitions |
| GET | `/scenarios` | — | Bundled simulated scenarios |
| GET | `/scenarios/{scenario_id}` | — | Scenario definition |
| POST | `/evaluate` | — | Evaluate one proposed action (stateless) |
| POST | `/session` | — | Create a demo, study or api session |
| GET | `/session/{session_id}` | — | Session state and timeline |
| DELETE | `/session/{session_id}` | token | Delete a session and its events |
| GET | `/session/{session_id}/events` | — | Session events |
| POST | `/session/{session_id}/step` | — | Advance the simulated agent |
| GET | `/session/{session_id}/stream` | — | Live events (Server-Sent Events) |
| POST | `/intervention` | — | Respond to an intervention |
| POST | `/action` | — | Submit an action from your own agent (api sessions) |
| GET | `/sessions` | token | List sessions |
| GET | `/events` | token | Event log across sessions (JSON or CSV) |
| GET | `/metrics` | — | Aggregated research metrics and chart data |
| POST | `/compare` | — | Quick policy comparison (simulated, not stored) |
| POST | `/experiments` | — | Create and run an experiment |
| GET | `/experiments` | — | List experiments |
| GET | `/experiments/{experiment_id}` | — | Experiment status and results |
| GET | `/experiments/{experiment_id}/export` | token | Export experiment data (CSV or JSON) |
| DELETE | `/experiments/{experiment_id}` | token | Delete an experiment |
| GET | `/study/config` | — | Active study configuration |
| PUT | `/study/config` | token | Update the study configuration |
| POST | `/study/participants` | — | Enrol a participant |
| GET | `/study/participants/{code}` | — | Participant plan and progress |
| PATCH | `/study/participants/{code}` | — | Record consent or completion |
| POST | `/study/sessions` | — | Start the session for a plan block |
| GET | `/study/instruments` | — | Questionnaire instruments (definitions, licensing, readiness) |
| POST | `/study/responses` | — | Submit questionnaire responses |
| GET | `/study/export` | token | Export questionnaire data |

## Meta

### `GET /health`

Returns `status`, `version`, `environment`, `database` (URL scheme only), `auth` (whether a
researcher token is configured), and `simulated_actions_only` (always true).

```bash
curl $BASE/health
# {"status":"ok","version":"0.1.0","environment":"development","database":"sqlite","auth":false,"simulated_actions_only":true}
```

### `GET /policies`

Returns the policy registry. Each entry has `name`, `summary`, `label`, `core`, `study_code`
and `origin`.

```bash
curl $BASE/policies
```

### `GET /model`

Returns the model's documented assumptions:

- `parameters`: the `ModelParameters` defaults;
- `category_priors`: severity, recoverability, external and description per category;
- `reason_codes`: code → phrase;
- `metrics`: the simulator's metric catalog.

```bash
curl $BASE/model
```

### `GET /scenarios` and `GET /scenarios/{scenario_id}`

The list returns one summary per scenario: `id`, `name`, `agent_name`, `domain`, `icon`,
`goal`, `description`, `n_steps`, `n_assumptions`, `n_mistakes`, `irreversible_steps`. The
detail endpoint adds `brief`, `assumptions`, `steps` and `mistakes`. An unknown id returns 404.

```bash
curl $BASE/scenarios
curl $BASE/scenarios/travel
```

## Evaluate

### `POST /evaluate`

Evaluates one proposed action and returns a `DecisionOut`. Nothing is stored.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `context` | ActionContextIn | required | The proposed action |
| `policy` | string or policy spec | `"adaptive"` | Policy to use |
| `preferences` | object | `null` | `UserPreferences`, used if the policy spec has none |
| `explain` | `"full"`, `"light"`, `"none"` | `"full"` | Explanation level |
| `state` | object | `null` | A serialized `SessionState` (e.g. `AgentPause.to_dict()["state"]`) to evaluate against history |

```bash
curl -X POST $BASE/evaluate -H 'Content-Type: application/json' -d '{
  "context": {
    "action": "send_email",
    "description": "Send the drafted email to Professor Smith",
    "consequence": "external_communication",
    "reversible": false,
    "intent_confidence": 0.72,
    "agent_confidence": 0.86
  },
  "policy": "adaptive",
  "explain": "full"
}'
# {"decision": "ASK_HUMAN", "score": 0.82, "should_ask": true,
#  "reason_codes": ["LOW_INTENT_CONFIDENCE", "IRREVERSIBLE_ACTION", "EXTERNAL_CONSEQUENCE", "MISSING_SIGNAL_DEFAULTED"], ...}
```

With a policy spec and preferences:

```bash
curl -X POST $BASE/evaluate -H 'Content-Type: application/json' -d '{
  "context": {"action": "send_email", "consequence": "external_communication", "reversible": false,
              "intent_confidence": 0.95, "agent_confidence": 0.95},
  "policy": {"name": "user_customized", "preferences": {"profile": "maximum_control"}},
  "explain": "none"
}'
```

## Sessions and interventions

A **session** holds the state of one task: the policy, the session history (habituation, open
assumptions, deferred questions), and an append-only event log. There are three modes:

| `mode` | `kind` | Driven by | Use |
|---|---|---|---|
| `demo` | `simulated` | `POST /session/{id}/step` | A scripted agent works through a bundled scenario; a person answers the cards (web demo) |
| `study` | `simulated` | `POST /session/{id}/step` | As `demo`, with the participant's plan and explanation condition. Normally created through `POST /study/sessions` |
| `api` | `external` | `POST /action` | Your own agent submits actions; the server keeps the AgentPause state |

### `POST /session` (201)

| Field | Default | Meaning |
|---|---|---|
| `mode` | `"demo"` | `demo`, `study` or `api` |
| `scenario_id` | — | Required for `demo` and `study` |
| `policy` | `"adaptive"` | Name or policy spec |
| `preferences` | `null` | `UserPreferences` |
| `seed` | random | Stored for reproducibility. The same seed, scenario and policy reproduce the same injected errors |
| `episode` | `0` | Episode index (part of the random-stream key) |
| `explanation_mode` | `"full"` | `full`, `factors`, `placebo` or `none`. Applied to what is shown in study mode (see [experiments.md](experiments.md#explanation-conditions)) |
| `participant_code`, `block`, `condition` | `null` | Study bookkeeping |

Returns a `SessionOut` with:

- `id`, `mode`, `kind`, `policy`, `policy_spec`, `explanation_mode`;
- `scenario` (summary), `brief` (what the user "meant", for the demo), `status`
  (`running`, `awaiting_human`, `completed`, `cancelled`);
- `step_index`, `n_steps`, `steps`, `timeline`;
- `pending` (the open intervention card, if any), `pending_questions` (deferred questions);
- `outcome` (when finished), `participant_code`, `block`, `seed`, `episode`.

```bash
curl -X POST $BASE/session -H 'Content-Type: application/json' \
  -d '{"mode": "demo", "scenario_id": "travel", "policy": "adaptive", "seed": 7}'
```

### `GET /session/{session_id}`

Returns the current `SessionOut`. In **study** mode, the response is filtered:

- ground-truth fields are removed (`necessary`, `error_present`, `shown_errors`, `harm`,
  `wrong_basis`);
- decisions are reduced according to the participant's explanation condition;
- `outcome` contains only `status` and `task_duration_s`.

```bash
curl $BASE/session/$SESSION_ID
```

### `GET /session/{session_id}/events?since=-1`

Returns the events with `seq > since`, in order. Each `EventOut` has:

- `id`, `seq`, `session_id`, `created_at`, `type`, `mode`, `scenario_id`, `policy`;
- `participant_code`, `condition`, `step_index`, `action`, `decision`, `score`,
  `intervention`, `risk_level`, `user_response`, `latency_ms`;
- the full `payload`.

Event types are `session_created`, `decision`, `intervention`, `response`, `ask_why`,
`executed`, `skipped` and `completed`.

```bash
curl "$BASE/session/$SESSION_ID/events?since=2"
```

### `POST /session/{session_id}/step`

Lets the simulated agent propose its next action. AgentPause decides:

- CONTINUE and DEFER execute the step (simulated);
- CLARIFY, ASK_HUMAN and BLOCK open an intervention card.

Optional body: `{"until": "next" | "intervention" | "end"}` (default `next`).
`intervention` and `end` keep stepping until a card opens or the task ends, for at most 60
steps per call.

Returns a `StepOut` with `session`, `events`, `decision` (the last decision) and `card` (the
open card, without ground-truth fields). Returns 409 while a card is open, when the session
is finished, or for `api` sessions.

```bash
curl -X POST $BASE/session/$SESSION_ID/step -H 'Content-Type: application/json' -d '{"until": "intervention"}'
```

A card has these fields:

- `intervention_id`, `step_index`, `step_id`, `decision`, `has_confirmation`;
- `assumption_ids`, `recent_interruptions`;
- `action`: `label`, `description`, `category`, `consequence`, `undo`, `reversible`,
  `recoverability`, `severity`, `what_could_go_wrong`, `preview`, `alternatives`,
  `requires_human_input`, `agent_confidence`;
- `assumptions`: each with its `options` and `if_wrong`;
- `allowed_responses`.

### `POST /intervention`

Records the human's response to the open card.

| Field | Meaning |
|---|---|
| `session_id` | Required |
| `intervention_id` | Optional. If given, it must match the pending card (otherwise 409) |
| `response` | `approve`, `edit`, `reject`, `answer`, `takeover`, `override`, `cancel_task`, `ask_why` or `timeout` |
| `answers` | `{assumption_id: value}` for clarification questions |

Allowed responses depend on the card:

| Card | Allowed responses |
|---|---|
| CLARIFY | `answer`, `ask_why`, `cancel_task` |
| ASK_HUMAN | `approve`, `edit`, `reject`, `ask_why`, `cancel_task` |
| BLOCK | `takeover`, `override`, `ask_why`, `cancel_task` |

`timeout` is always accepted. Any other response returns 422.

Behaviour:

- `ask_why` changes no state. It only logs that an explanation was requested.
- After a CLARIFY answer, the agent proposes the same step again with the answers applied.
- In simulated sessions, the response time is measured on the server from when the card was
  opened, capped at 600 s.
- For `api` sessions, the response is recorded in the session's AgentPause state (user
  history and assumption resolution). Your agent then decides what to execute.

Returns a `StepOut` (`card` is null).

```bash
curl -X POST $BASE/intervention -H 'Content-Type: application/json' \
  -d "{\"session_id\": \"$SESSION_ID\", \"response\": \"answer\", \"answers\": {\"travel_date\": \"Fri 21 Nov\"}}"
```

### `POST /action`

For `api` sessions: evaluates an action from your own agent within the session, and returns
an `ActionOut` with `decision`, `intervention_id` and `session`. If the decision interrupts
(CLARIFY, ASK_HUMAN, BLOCK), an intervention is opened and the session waits for
`POST /intervention`. Further actions return 409 until then. Simulated sessions return 409.

```bash
SESSION_ID=$(curl -s -X POST $BASE/session -H 'Content-Type: application/json' \
  -d '{"mode": "api", "policy": "adaptive"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

curl -X POST $BASE/action -H 'Content-Type: application/json' -d "{
  \"session_id\": \"$SESSION_ID\",
  \"context\": {\"action\": \"send_email\", \"consequence\": \"external_communication\",
                \"reversible\": false, \"intent_confidence\": 0.72}
}"
# {"decision": {"decision": "ASK_HUMAN", ...}, "intervention_id": "<session id>-1", "session": {...}}

curl -X POST $BASE/intervention -H 'Content-Type: application/json' \
  -d "{\"session_id\": \"$SESSION_ID\", \"response\": \"approve\"}"
```

### `GET /sessions` (token)

Query parameters: `mode`, `scenario`, `policy`, `participant`, `status`, `offset` (≥ 0),
`limit` (1–500, default 50). Returns `{total, offset, limit, items}`, newest first.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/sessions?mode=study&limit=20"
```

### `DELETE /session/{session_id}` (token)

Deletes the session and its events. Returns 204.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE/session/$SESSION_ID
```

## Live events (SSE)

### `GET /session/{session_id}/stream?since=-1`

Streams the session's events as `text/event-stream`. The server polls the database every
0.5 s and sends each new event as:

```text
id: <seq>
event: <type>
data: <EventOut as JSON>
```

- During idle periods, a `: keep-alive` comment is sent about every 15 s.
- When the session is `completed` or `cancelled` and no new events remain, the server sends
  `event: end` with `data: {}` and closes the stream.
- Pass `since` (the last `seq` you have) to resume.
- In study mode, the payloads are filtered as for `GET /session/{id}`.

```bash
curl -N "$BASE/session/$SESSION_ID/stream"
```

```js
const source = new EventSource(`/api/v1/session/${id}/stream`);
source.addEventListener("decision", (e) => console.log(JSON.parse(e.data)));
source.addEventListener("end", () => source.close());
```

## Event log, metrics, comparisons, experiments

### `GET /events` (token)

A filterable log of every proposal, decision, response and execution, across sessions.

| Parameter | Meaning |
|---|---|
| `session_id`, `mode`, `scenario`, `policy`, `participant`, `decision`, `type` | Exact-match filters |
| `risk` | `low`, `medium` or `high`: consequence risk below 0.1, below 0.35, or above |
| `interventions_only` | Only decisions that interrupted |
| `offset`, `limit` | Paging for JSON (`limit` 1–1000, default 100) |
| `format` | `json` (default) returns `{total, offset, limit, items}`. `csv` returns **all** matching rows as a file |

The CSV columns are `id`, `seq`, `session_id`, `created_at`, `type`, `mode`, `scenario_id`,
`policy`, `participant_code`, `condition`, `step_index`, `action`, `decision`, `score`,
`intervention`, `risk_level`, `user_response` and `latency_ms`. Participants appear only as
pseudonymous codes.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/events?type=decision&decision=ASK_HUMAN&limit=50"
curl -H "Authorization: Bearer $TOKEN" "$BASE/events?format=csv" -o agentpause-events.csv
```

### `GET /metrics`

Returns aggregated metrics and chart data for the dashboard.

| Parameter | Meaning |
|---|---|
| `source` | `experiment` (default): a stored simulation experiment (`experiment_id`, default the latest completed one). `sessions`: completed interactive demo and study sessions (real human responses to simulated agents) |
| `experiment_id`, `scenario`, `policy`, `participant`, `condition`, `risk`, `mode` (`demo`/`study`) | Filters |

The response contains:

- `source`, `filters`, `n_episodes`;
- `aggregates`: per policy and condition, with the metrics listed in
  [experiments.md](experiments.md#metrics);
- `charts`: `policies`, `decisions_by_policy`, `intervention_timing`, `reasons`,
  `reasons_by_policy`, `risk`, `responses`, `uncertainty`, `summary`;
- `available`: filter values, including the completed experiments;
- `metric_definitions`;
- `note`, which states whether the data are simulated.

```bash
curl "$BASE/metrics?source=experiment&policy=adaptive"
curl "$BASE/metrics?source=sessions&mode=study"
```

### `POST /compare`

Runs a quick, unstored policy comparison on simulated episodes, plus one example trace per
policy.

| Field | Default | Meaning |
|---|---|---|
| `scenarios` | `["all"]` | Scenario ids, or `all` |
| `policies` | `["full_autonomy", "always_confirm", "fixed_threshold", "adaptive"]` | Names or policy specs |
| `episodes` | 30 (1–300) | Episodes per scenario × policy |
| `seed` | 314159 | Base seed |
| `user`, `engine` | `{}` | Simulated-user and engine overrides (see [experiments.md](experiments.md)) |
| `trace_scenario`, `trace_episode` | first scenario, 0 | Which episode to trace |

The total (scenarios × policies × episodes) must not exceed `MAX_COMPARE_EPISODES`. The
response has `note`, `episodes`, `seed`, `aggregates` (with 95% bootstrap intervals over 200
resamples), `by_scenario`, `comparisons` (paired differences against `adaptive`, if
included), `traces` and `trace_scenario`.

```bash
curl -X POST $BASE/compare -H 'Content-Type: application/json' \
  -d '{"scenarios": ["email", "travel"], "policies": ["always_confirm", "myopic_voi", "adaptive"], "episodes": 30}'
```

### `POST /experiments` (201)

Creates and runs a stored experiment. It runs in a background thread; poll
`GET /experiments/{id}`. With `?wait=true`, it runs synchronously, which is meant for small
experiments and tests.

| Field | Default | Meaning |
|---|---|---|
| `name` | required (1–128 chars) | Experiment name |
| `description` | `""` | Free text |
| `scenarios` | `["all"]` | Scenario ids or `all` |
| `policies` | required (≥ 1) | Names or policy specs |
| `episodes` | 50 (1–2000) | Episodes per scenario × policy × condition |
| `seed` | 314159 | Base seed |
| `conditions` | one `default` condition | List of `{name, user, engine, parameters}` (simulated-user overrides, engine overrides, model-parameter overrides for every policy) |
| `bootstrap` | 300 (0–5000) | Bootstrap resamples for confidence intervals (0 disables them) |

Signal ablation (`ablate`) is available in TOML configs only, not through this endpoint. The
total episode count must not exceed `MAX_EXPERIMENT_EPISODES`.

Returns an `ExperimentOut` with:

- `id`, `name`, `status` (`queued`, `running`, `completed`, `failed`);
- `created_at`, `finished_at`, `config`, `progress` (`{done, total}`);
- `result` (`config`, `aggregates`, `by_scenario`, `comparisons`, `duration_s`,
  `result_hash`, `note`);
- `error`.

```bash
curl -X POST "$BASE/experiments" -H 'Content-Type: application/json' -d '{
  "name": "cost-sweep",
  "scenarios": ["email", "travel"],
  "policies": ["always_confirm",
               {"name": "adaptive", "parameters": {"interruption_cost": 0.03}, "label": "adaptive@0.03"}],
  "episodes": 50,
  "conditions": [{"name": "default"}, {"name": "careless_user", "user": {"approval_vigilance": 0.6}}]
}'
```

### `GET /experiments?limit=50` and `GET /experiments/{experiment_id}`

The list returns the most recent experiments, newest first. The detail endpoint returns one
`ExperimentOut`, or 404.

```bash
curl $BASE/experiments
curl $BASE/experiments/$EXPERIMENT_ID
```

### `GET /experiments/{experiment_id}/export` (token)

| Parameter | Values |
|---|---|
| `table` | `records` (one row per decision; columns in [experiments.md](experiments.md#outputs)), `episodes` (one row per episode), `summary` (config and result as JSON) |
| `format` | `csv` (default) or `json` (`summary` is always JSON) |

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/experiments/$EXPERIMENT_ID/export?table=records&format=csv" -o records.csv
```

### `DELETE /experiments/{experiment_id}` (token)

Deletes the experiment and its stored episodes and records. Returns 204.

## Study mode

The design, explanation conditions and instruments are described in
[experiments.md](experiments.md#human-study-mode).

### `GET /study/config` and `PUT /study/config` (token for PUT)

`StudyConfig` fields and defaults:

| Field | Default |
|---|---|
| `title` | `"AgentPause study"` |
| `consent_text` | A short consent text stating that all actions are simulated and that no names or contact details are collected |
| `conditions` | `["full_autonomy", "always_confirm", "fixed_threshold", "adaptive"]` |
| `scenarios` | `["travel", "email", "shopping", "calendar"]` |
| `practice_scenario` | `"files"` (run under `always_confirm`; `null` disables the practice block) |
| `explanation_modes` | `["none", "placebo", "factors", "full"]` |
| `post_task_instruments` | `["agentpause_post_task", "nasa_tlx_raw"]` |
| `final_instruments` | `["timing_comprehension"]` |
| `seed_base` | `900000` |

`PUT` validates the configuration and returns 422 if:

- a condition is not a registered policy;
- a scenario does not exist;
- an instrument is unknown;
- `conditions`, `scenarios` or `explanation_modes` is empty.

Configure the study before enrolling participants. Existing plans are not changed.

```bash
curl $BASE/study/config
curl -X PUT -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' $BASE/study/config \
  -d '{"conditions": ["always_confirm", "fixed_threshold", "adaptive"], "scenarios": ["travel", "email", "shopping"],
       "explanation_modes": ["factors", "full"]}'
```

### `POST /study/participants` (201)

Takes no body. Enrols a participant with a random pseudonymous code (`P-` and 6
characters). It assigns a counterbalanced plan (a practice block, then one block per
condition) and an explanation condition. Returns a `ParticipantOut` with:

- `code`, `number`, `explanation_mode`;
- `plan`: a list of `{block, policy, scenario_id, seed, practice}`;
- `consented`, `completed`.

```bash
curl -X POST $BASE/study/participants
```

### `GET /study/participants/{code}` and `PATCH /study/participants/{code}`

`PATCH` accepts `{"consented": bool, "completed": bool}`. Both fields are optional.

```bash
curl -X PATCH $BASE/study/participants/P-ABC234 -H 'Content-Type: application/json' -d '{"consented": true}'
```

### `POST /study/sessions` (201)

Body: `{"participant_code": "...", "block": n}`. This creates the `study` session for that
block of the participant's plan, with the block's policy, scenario and seed and the
participant's explanation condition. Then drive it with `/session/{id}/step` and
`/intervention`. Returns 403 if consent has not been recorded, 422 for a block outside the
plan, and 404 for an unknown participant.

```bash
curl -X POST $BASE/study/sessions -H 'Content-Type: application/json' -d '{"participant_code": "P-ABC234", "block": 1}'
```

### `GET /study/instruments`

Returns the questionnaire definitions. Each has its `citation`, `license`,
`redistributable`, `validated`, `scale`, `scoring` and `items`, plus `items_source`
(`bundled`, `local` or `missing`) and `ready` (whether item text is available).

```bash
curl $BASE/study/instruments
```

### `POST /study/responses` (201)

Body: `{participant_code, instrument_id, session_id?, block?, responses: {item_id: value}}`.
The responses are scored on the server and the result is returned as
`{id, instrument_id, score}`. Errors:

- 409 for an instrument without item text (`ready: false`);
- 404 for an unknown instrument or participant;
- 422 for a value outside the scale.

```bash
curl -X POST $BASE/study/responses -H 'Content-Type: application/json' -d '{
  "participant_code": "P-ABC234", "instrument_id": "nasa_tlx_raw", "block": 1,
  "responses": {"mental": 55, "physical": 10, "temporal": 40, "performance": 30, "effort": 50, "frustration": 35}
}'
# {"id": 1, "instrument_id": "nasa_tlx_raw", "score": {"mean": 36.67, "answered": 6}}
```

### `GET /study/export?format=csv` (token)

Returns one row per questionnaire response, joined with the participant's data. The columns
are `participant_code`, `participant_number`, `explanation_mode`, `block`, `policy`,
`session_id`, `instrument_id`, `responses` (JSON), `score` (JSON) and `created_at`.
`format=json` returns the same rows as JSON.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/study/export?format=csv" -o agentpause-study.csv
```

## Exports

| Data | Endpoint | Formats |
|---|---|---|
| Event log (all sessions, filterable) | `GET /events?format=csv` | CSV, JSON |
| Per-session events | `GET /session/{id}/events` | JSON |
| Experiment records, episodes, summary | `GET /experiments/{id}/export?table=...&format=...` | CSV, JSON |
| Questionnaire responses | `GET /study/export?format=...` | CSV, JSON |

No table stores names, email addresses, IP addresses, credentials or message bodies.
Participants are identified only by random codes. See [SECURITY.md](../SECURITY.md).
