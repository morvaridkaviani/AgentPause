# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-15

First public research release. All results are simulated; the toolkit has **not yet been evaluated with human participants**.

### Added
- Research documents: prior-art review, research gap, research questions and hypotheses, metric definitions, novelty audit, and a paper draft (`research/`).
- Python SDK (`agentpause-toolkit`, import `agentpause`): `AgentPause` session API, decision types CONTINUE / CLARIFY / ASK_HUMAN / DEFER / BLOCK, signal provenance, explanation engine (reason codes, factor attribution, feature and timing counterfactuals, stability), guard decorator, HTTP client, and a Claude Code PreToolUse hook.
- Policies: full autonomy, always confirm, fixed risk threshold, confidence threshold, rule-based, myopic value of asking, adaptive (trajectory-aware timing with DEFER and batching), user-customized, and an experimental learned policy.
- Simulator (`agentpause-simulator`): six scripted scenarios (travel, email, shopping, files, calendar, research), injected mistakes and wrong assumptions with ground-truth labels, a parametric simulated user with habituation, deterministic common-random-number seeding, metrics with bootstrap confidence intervals, signal ablation, and a CLI.
- Experiment scripts and configs with a one-command reproduction (`experiments/reproduce_all.py`), figures, and reference result hashes.
- REST API (FastAPI) with OpenAPI docs, SQLite/PostgreSQL persistence, sessions, event log, CSV/JSON export, metrics, background experiments, server-sent events, and a study mode (balanced Latin square, explanation conditions including a placebic control, questionnaires with licensing metadata).
- Web app (Next.js): landing page, interactive demo, decision lab, policy comparison, preferences, research dashboard, experiment runner, event log, study mode, and research/limitations page.
- TypeScript SDK (`@agentpause/sdk`).
- Docker images, docker compose, GitHub Actions CI, and documentation.
