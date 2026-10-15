# Convenience targets. Run `make help`. Assumes a virtualenv at .venv (see docs/getting_started.md).
PY ?= .venv/bin/python
.DEFAULT_GOAL := help

.PHONY: help install dev backend frontend test test-py test-js lint typecheck build experiments experiments-quick figures check-repro docker

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## Create .venv and install Python + Node dependencies
	python3 -m venv .venv
	$(PY) -m pip install -r requirements-dev.txt
	npm install

dev: ## Run the API (:8000) and the web app (:3100) together
	./scripts/dev.sh

backend: ## Run the API on :8000 with reload
	$(PY) -m uvicorn app.main:app --app-dir backend --reload --port 8000

frontend: ## Run the web app on :3100 (expects the API on :8000)
	npm run dev

test: test-py test-js ## Run all tests

test-py: ## Python tests (SDK, simulator, backend)
	$(PY) -m pytest

test-js: ## Frontend + TypeScript SDK tests
	npm test

lint: ## Ruff + ESLint
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	npm run lint

typecheck: ## mypy (strict) + tsc
	$(PY) -m mypy
	npm run typecheck

build: ## Production build of the TypeScript SDK and the web app
	npm run build

experiments: ## Reproduce every simulated result and figure (a few minutes)
	$(PY) experiments/reproduce_all.py

experiments-quick: ## Smoke-test the experiment pipeline (results/quick, figures/quick)
	$(PY) experiments/reproduce_all.py --quick

figures: ## Regenerate figures from existing results
	$(PY) experiments/generate_figures.py

check-repro: ## Re-run experiments and compare result hashes with the reference
	$(PY) scripts/check_reproducibility.py

docker: ## Build and start backend + frontend
	docker compose up --build
