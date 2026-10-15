# Contributing to AgentPause

Thank you for helping. AgentPause is research infrastructure, so contributions are judged on two things: does the code work, and does it keep the research honest.

## Ground rules

- **No fabricated results.** Simulated results are always labelled as simulated. Nothing is described as a human-study finding unless it comes from a human study with ethics approval.
- **No unlicensed questionnaires.** Do not add item text of published instruments unless the licence allows redistribution. Add metadata and a source link instead, and let researchers supply the items locally (`INSTRUMENTS_LOCAL_DIR`, see [docs/experiments.md](docs/experiments.md)).
- **No real side effects.** Demo and simulator actions stay simulated. Do not add integrations that send email, spend money, or delete data.
- **No personal data.** AgentPause works on action metadata. Do not log message bodies, credentials, payment details, or identifiers of participants beyond random codes.
- **Claims match evidence.** Avoid "first", "novel", or "state of the art" unless a citation supports it. See [research/novelty_audit.md](research/novelty_audit.md).

## Development setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
npm install
make test lint typecheck
```

`make help` lists all targets. [docs/getting_started.md](docs/getting_started.md) has details.

## Before you open a pull request

```bash
ruff check . && ruff format --check .
mypy                       # strict
pytest
npm run lint && npm run typecheck && npm test && npm run build
```

If you change the decision model, a policy, a scenario, or the simulator, simulated results will change. Run

```bash
python scripts/check_reproducibility.py --quick
```

If hashes differ on purpose, regenerate the results (`python experiments/reproduce_all.py` and `--quick`), copy the new hashes and summaries to `experiments/results/reference/`, and explain the change in the pull request and in `CHANGELOG.md`.

## What to contribute

- **Scenarios**: JSON files in `simulator/src/agentpause_sim/scenarios/`. Each step needs metadata, ground truth (`necessary` conditions, injected mistakes, assumptions), and a plain-language preview. Validation runs in `simulator/tests/test_scenarios.py`.
- **Policies**: subclass `InterventionPolicy` and register it (see [docs/policies.md](docs/policies.md)). Add tests and, if it is a baseline from the literature, cite it.
- **Integrations**: adapters for agent frameworks that call the SDK or REST API. Keep them dependency-free or optional.
- **Instruments**: metadata and licensing information for questionnaires.
- **Documentation and translations** of the participant-facing study text.

## Style

- Python: ruff (format + lint), strict mypy, type hints everywhere, small pure functions in the decision model.
- TypeScript: strict mode, ESLint (Next.js config), no `any` in public types.
- Tests next to the package (`*/tests`, `frontend/tests`, `sdk/typescript/test`).
- Commit messages: imperative mood, explain *why*.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately as described in [SECURITY.md](SECURITY.md).
