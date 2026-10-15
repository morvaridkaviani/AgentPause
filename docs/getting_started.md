# Getting started

This guide installs AgentPause from source, starts the API server and the web app, makes a
first SDK call, and runs a first simulation. Every command is run from the repository root
unless stated otherwise.

AgentPause decides, for each action an AI agent proposes, whether the agent should
**CONTINUE**, **CLARIFY** an assumption, **ASK_HUMAN** for approval, **DEFER** a question to a
later moment, or **BLOCK**. See [architecture.md](architecture.md) for how the parts fit
together.

## Prerequisites

| Tool | Version | Used for |
|---|---|---|
| Python | 3.11 or later (`requires-python = ">=3.11"` in every `pyproject.toml`) | SDK, simulator, backend, experiments |
| Node.js | 20.9 or later (`engines` in the root `package.json`) | Web app and TypeScript SDK |
| npm | The version bundled with Node.js | JavaScript workspaces |
| Docker with Compose v2 | Optional | Containerized setup |

## Package names

| Folder | Distribution name | Import name | Dependencies |
|---|---|---|---|
| `sdk/python` | `agentpause-toolkit` | `agentpause` | None (standard library only) |
| `simulator` | `agentpause-simulator` | `agentpause_sim` | `agentpause-toolkit`; optional `figures` extra (matplotlib) |
| `backend` | `agentpause-server` | `app` | `agentpause-toolkit`, `agentpause-simulator`, FastAPI, Uvicorn, Pydantic, SQLAlchemy; optional `postgres` and `dev` extras |
| `sdk/typescript` | `@agentpause/sdk` (npm) | — | See [`sdk/typescript/README.md`](../sdk/typescript/README.md) |
| `frontend` | `@agentpause/frontend` (private) | — | Next.js, React |

> **Note on the Python package name.** The Python distribution is called
> `agentpause-toolkit`, while the import name is `agentpause`. The name `agentpause` on PyPI
> may belong to an unrelated project, so do not `pip install agentpause`. None of the
> AgentPause packages are published to PyPI or npm yet. Install them from this repository as
> shown below.

## Install

### Python packages

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e sdk/python -e simulator -e "backend[dev]"
```

Install all three packages in one `pip` command. The simulator and backend depend on
`agentpause-toolkit==0.1.0`, which is not on PyPI, so pip must find it among the local
packages in the same command.

Optional extras:

```bash
pip install -e "simulator[figures]"   # matplotlib, for experiments/generate_figures.py
pip install -e "backend[postgres]"    # psycopg, for DATABASE_URL=postgresql+psycopg://...
```

For a full development setup, `pip install -r requirements-dev.txt` installs the three
packages in editable mode with the `figures` and `dev` extras, plus Ruff and mypy.
`make install` creates `.venv`, runs that, and runs `npm install`. Run `make help` to list
the other Makefile targets.

Check the installation:

```bash
python -c "import agentpause, agentpause_sim, app; print(agentpause.__version__)"
```

The install also puts two commands on your `PATH`: `agentpause-sim` (the simulator CLI) and
`agentpause-claude-hook` (the Claude Code hook adapter, see [sdk.md](sdk.md#claude-code-pretooluse-hook)).

### JavaScript packages

```bash
npm install
```

The root `package.json` defines two npm workspaces, `frontend` and `sdk/typescript`, and
`npm install` at the root installs both.

## Run the backend

```bash
uvicorn app.main:app --app-dir backend --reload
```

- The API listens on `http://localhost:8000`. All endpoints are under `/api/v1`.
- Interactive OpenAPI documentation is at `http://localhost:8000/docs` (Swagger UI) and
  `http://localhost:8000/redoc`. The schema is at `/api/v1/openapi.json`.
- By default the server uses SQLite at `./data/agentpause.db`, relative to the directory you
  start it from. Tables are created on startup.
- Configuration comes from environment variables, for example `DATABASE_URL`,
  `AGENTPAUSE_ADMIN_TOKEN` and `CORS_ORIGINS`. `.env.example` lists them all. The server
  reads them from the process environment and does not load a `.env` file itself. Docker
  Compose reads `.env` for variable substitution. When you run Uvicorn directly, export the
  variables, for example with `cp .env.example .env`, edit it, then
  `set -a; . ./.env; set +a`. The full list is in [api.md](api.md#configuration).

Quick check:

```bash
curl http://localhost:8000/api/v1/health
```

## Run the web app

```bash
cd frontend
npm run dev                           # or, from the repository root: npm run dev
```

Open `http://localhost:3100`. The browser only talks to the Next.js app. Next.js rewrites
`/api/*`, `/docs` and `/redoc` to the backend, so no CORS configuration is needed. The
backend address comes from `BACKEND_URL`, which defaults to `http://localhost:8000`:

```bash
BACKEND_URL=http://127.0.0.1:9000 npm run dev
```

`BACKEND_URL` is read when the dev server starts. For `npm run build`, it is read at build
time and compiled into the rewrites, so set it before building.

To start both the backend and the web app with one command, run `scripts/dev.sh`. It uses
`.venv/bin/python` and ports 8000 and 3100, which you can override with `PY`, `API_PORT` and
`WEB_PORT`. Ctrl+C stops both.

Pages:

| Path | Page |
|---|---|
| `/` | Landing page |
| `/demo` | Interactive demo: a simulated agent works through a scenario and you answer its interventions |
| `/lab` | Decision lab: change the signals of one action and watch the decision and its counterfactuals |
| `/compare` | Policy comparison on simulated episodes |
| `/preferences` | Autonomy preferences (used by the `user_customized` policy) |
| `/dashboard` | Research dashboard with filters |
| `/experiments`, `/experiments/[id]` | Experiment runner and results |
| `/events` | Event log with live tail and export |
| `/study`, `/study/admin` | Participant flow and study administration |
| `/about` | Methodology, limitations, citations |

## Run with Docker

```bash
docker compose up --build          # or: make docker
```

`docker-compose.yml` and the multi-stage `Dockerfile` at the repository root define two
services:

- **`backend`** on port 8000. API documentation is at `http://localhost:8000/docs`.
  - SQLite is stored in the named volume `agentpause-data`, at `/data/agentpause.db`.
  - The service reports healthy once `/api/v1/health` answers.
- **`frontend`** on host port 3100 (container port 3000). It is built with `BACKEND_URL=http://backend:8000`, and it
  starts after the backend is healthy.

Open `http://localhost:3100` once both are running.

Compose takes `DATABASE_URL`, `CORS_ORIGINS`, `AGENTPAUSE_ADMIN_TOKEN`, `AGENTPAUSE_ENV`
(default `production` in Compose) and `MAX_EXPERIMENT_EPISODES` from your shell or from
`.env` (see [api.md](api.md#configuration)). For PostgreSQL, start the optional `postgres`
service with `docker compose --profile postgres up --build`, and set `DATABASE_URL` and
`POSTGRES_PASSWORD` accordingly. To supply licensed questionnaire items, uncomment the
`INSTRUMENTS_LOCAL_DIR` lines in `docker-compose.yml` (see
[experiments.md](experiments.md#questionnaire-instruments)).

## First SDK call

```python
from agentpause import AgentPause

pause = AgentPause(policy="adaptive")          # one instance per agent task
decision = pause.evaluate(
    action="send_email",
    description="Send the drafted reply to Professor Smith",
    consequence="external_communication",
    reversible=False,
    intent_confidence=0.72,
    agent_confidence=0.86,
)

print(decision.decision.value)      # ASK_HUMAN
print(decision.should_ask)          # True
print(decision.explanation)         # plain-language reason, built from reason codes
print(decision.timing.why_now)      # timing explanation
for factor in decision.top_factors():
    print(factor.label, factor.display, factor.provenance.value)

if decision.should_ask:
    # Show decision.questions to the user, then record the answer:
    pause.respond(decision, "approve")
```

Signals you do not pass (here `severity`, `task_progress`, `at_breakpoint` and
`cognitive_load`) are filled with documented defaults. Each default is tagged with
provenance `default`, and the decision carries the reason code `MISSING_SIGNAL_DEFAULTED`.
The full API is in [sdk.md](sdk.md). How the decision is computed is in
[policies.md](policies.md).

## First simulation

The simulator runs scripted agent tasks with injected mistakes and a simulated user. All
actions are simulated: nothing sends email, spends money, or deletes files.

```bash
agentpause-sim scenarios                     # list the six bundled scenarios
agentpause-sim show travel                   # print one scenario as JSON
agentpause-sim run experiments/configs/baseline.toml --episodes 20 --out results/baseline-quick
```

`agentpause-sim run CONFIG [--out DIR] [--episodes N]` runs an experiment config (`.toml` or
`.json`). Without `--out`, results go to `experiments/results/<name>` relative to the current
directory. Each run writes `records.csv`, `episodes.csv`, `summary.json` and `config.json`,
and prints a result hash. Running the same config again gives the same hash.

The same from Python:

```python
from agentpause_sim import ExperimentConfig, run_experiment, write_result

config = ExperimentConfig.from_dict({
    "name": "quickstart",
    "policies": ["always_confirm", "fixed_threshold", "adaptive"],
    "scenarios": ["email", "travel"],
    "episodes": 20,
    "seed": 314159,
})
result = run_experiment(config)                       # SIMULATED results
for row in result.aggregates:
    print(f"{row['policy']:16s} interventions={row['interventions']:.2f} harm={row['harm']:.3f}")
print("hash", result.result_hash[:16])
write_result(result, "results/quickstart")            # records.csv, episodes.csv, summary.json, config.json
```

The experiment scripts in `experiments/` wrap the bundled configs and print tables:

```bash
python experiments/compare_policies.py --episodes 20   # quick run of the main comparison
python experiments/reproduce_all.py --quick            # every config, 20 episodes per cell
python scripts/check_reproducibility.py --quick        # compare result hashes with the reference
```

Notes:

- `compare_policies.py` includes the experimental `learned` policy, which loads the weights
  bundled with the SDK.
- `reproduce_all.py` first retrains those weights, and `--quick` writes to
  `experiments/results/quick` and `experiments/figures/quick`.
- See [experiments.md](experiments.md) for configs, metrics, and reproducibility. Simulated
  results are not evidence about human users.

## Run the tests

```bash
.venv/bin/pytest            # SDK, simulator and backend tests (testpaths in pyproject.toml)
npm test                    # all JavaScript workspaces (frontend and sdk/typescript)
npm test --workspace frontend
make test                   # both of the above
```

Lint and type-check settings for Python (Ruff, mypy) are in the root `pyproject.toml`. Ruff
and mypy are installed by `requirements-dev.txt`, but not by the `dev` extra alone. Run them
with `make lint` and `make typecheck`, which also run ESLint and `tsc`, or directly with
`ruff check .` and `mypy`.

## Examples

[`examples/`](../examples/README.md) contains short runnable programs:

- a Python agent loop with a deferred question;
- the guard decorator;
- the HTTP client;
- the REST API with curl;
- the TypeScript client;
- a Claude Code hook configuration.

## Next steps

- [sdk.md](sdk.md): the Python SDK, the guard decorator, the REST client, and the Claude Code hook.
- [policies.md](policies.md): every policy, the expected-value model, and its parameters.
- [api.md](api.md): REST endpoints.
- [experiments.md](experiments.md): simulator, experiment configs, reproducibility, and the human-study mode.
- [research.md](research.md): research questions, contributions, and limitations.

## Online demo (GitHub Pages)

The web app is published at **https://morvaridkaviani.github.io/AgentPause/** by [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) on every push to `main`. It has no server: the real FastAPI backend runs in the visitor's browser.

- Python runs as WebAssembly through [Pyodide](https://pyodide.org), loaded from the jsDelivr CDN.
- It runs in a Web Worker ([`frontend/public/py-worker.js`](../frontend/public/py-worker.js)), with an in-memory SQLite database.
- The web app passes each API request to the worker instead of the network ([`frontend/lib/browser-api.ts`](../frontend/lib/browser-api.ts)).

Differences from a normal installation:

- **Start-up.** The first visit downloads about 20 MB (the Python runtime and libraries). Later visits use the browser cache.
- **Nothing persists.** Reloading the page starts with an empty database. Use exports to keep results.
- **Inline experiments.** Browsers cannot start threads, so experiments run inline. Episode limits are lower (3,000 per experiment, 1,200 per comparison).
- **No live API docs.** The Swagger/ReDoc pages are not available; see [api.md](api.md).

To build and preview the static site locally:

```bash
python scripts/static_demo/build_bundle.py            # Python packages -> frontend/public/py/
STATIC_EXPORT=1 NEXT_PUBLIC_STATIC_DEMO=1 NEXT_PUBLIC_BASE_PATH=/AgentPause \
  npm run build --workspace frontend                  # static files -> frontend/out/
mkdir -p /tmp/site && ln -sfn "$PWD/frontend/out" /tmp/site/AgentPause
python3 -m http.server 8080 --directory /tmp/site     # http://localhost:8080/AgentPause/
```

For a fork, enable **Settings → Pages → Source: GitHub Actions**. The base path follows the repository name.

