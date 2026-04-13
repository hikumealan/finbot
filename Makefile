.DEFAULT_GOAL := help
SHELL := /bin/bash

MODEL ?= $(shell grep -E '^FINBOT_OLLAMA_MODEL=' .env 2>/dev/null | cut -d= -f2- || echo "mistral:7b-instruct-v0.3-q4_K_M")
CMD ?=

# ============================================================
# Native (recommended for macOS — full GPU acceleration)
# ============================================================

.PHONY: setup
setup: ## One-command setup: Ollama + Python + onboarding
	bash scripts/bootstrap.sh

.PHONY: dev
dev: ## Start FastAPI + React dev server with auto-reload
	@if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then \
		echo "Starting Ollama..."; \
		ollama serve &>/dev/null & \
		sleep 2; \
	fi
	uv run finbot serve --reload &
	cd frontend && npm run dev

.PHONY: cli
cli: ## Run a finbot CLI command (e.g., make cli CMD="expenses --month 2025-03")
	uv run finbot $(CMD)

.PHONY: test
test: ## Run pytest (skips LLM tests by default)
	uv run pytest -m "not llm" --tb=short $(ARGS)

.PHONY: lint
lint: ## Run ruff linter
	uv run ruff check src/ tests/

.PHONY: format
format: ## Auto-format code with ruff
	uv run ruff format src/ tests/

.PHONY: status
status: ## Show Ollama status, model info, DB health
	@echo "--- Ollama ---"
	@curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1 \
		&& echo "  Status: running" \
		|| echo "  Status: NOT running"
	@ollama list 2>/dev/null | head -5 || true
	@echo ""
	@echo "--- FinBot ---"
	@uv run finbot doctor 2>/dev/null || echo "  finbot doctor failed — run 'make setup' first"

.PHONY: update
update: ## Update Ollama, Python deps, and model
	@if command -v brew &>/dev/null; then brew upgrade ollama 2>/dev/null || true; fi
	uv sync
	bash scripts/pull-model.sh

.PHONY: backup
backup: ## Create encrypted database backup
	uv run finbot backup

.PHONY: restore
restore: ## Restore database from a backup file
	@read -p "Backup file path: " FILE; \
	uv run finbot backup --restore "$$FILE"

.PHONY: reset
reset: ## Delete database only (preserves encryption key and config)
	@echo "This will delete the FinBot database but keep your encryption key."
	@read -p "Continue? [y/N] " CONFIRM; \
	if [ "$$CONFIRM" = "y" ] || [ "$$CONFIRM" = "Y" ]; then \
		rm -f data/finbot.db data/.key_hash; \
		echo "Database deleted. Run 'finbot setup' to reinitialize."; \
	else \
		echo "Cancelled."; \
	fi

# ============================================================
# Docker
# ============================================================

.PHONY: docker-build
docker-build: ## Build the FinBot Docker image
	docker compose build finbot-app

.PHONY: docker-up
docker-up: ## Start all services (with Ollama in Docker)
	docker compose --profile full up -d

.PHONY: docker-up-hybrid
docker-up-hybrid: ## Start FinBot container only (uses native Ollama on host)
	FINBOT_OLLAMA_HOST=http://host.docker.internal:11434 docker compose up -d finbot-app

.PHONY: docker-down
docker-down: ## Stop all services
	docker compose --profile full down

.PHONY: docker-pull
docker-pull: ## Pull LLM model inside the Ollama container
	DOCKER=1 bash scripts/pull-model.sh MODEL=$(MODEL)

.PHONY: docker-shell
docker-shell: ## Open a shell in the FinBot container
	docker compose exec finbot-app bash

.PHONY: docker-logs
docker-logs: ## Tail logs for all services
	docker compose --profile full logs -f

.PHONY: docker-test
docker-test: ## Run pytest inside the FinBot container
	docker compose exec finbot-app pytest -m "not llm" --tb=short

# ============================================================
# Common
# ============================================================

.PHONY: pull-model
pull-model: ## Pull/switch LLM model (accepts MODEL=name)
	bash scripts/pull-model.sh MODEL=$(MODEL)

.PHONY: doctor
doctor: ## Run finbot health check
	uv run finbot doctor

.PHONY: clean
clean: ## Remove build artifacts (safe — no data loss)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache .pytest_cache htmlcov dist build *.egg-info

.PHONY: clean-all
clean-all: ## Remove ALL data, containers, volumes (DESTRUCTIVE)
	@echo ""
	@echo "  WARNING: This will permanently delete:"
	@echo "    - data/finbot.db (your financial data)"
	@echo "    - Docker containers and volumes"
	@echo "    - Build artifacts"
	@echo ""
	@read -p "  Type 'DELETE' to confirm: " CONFIRM; \
	if [ "$$CONFIRM" = "DELETE" ]; then \
		rm -rf data/ .ruff_cache .pytest_cache __pycache__ dist build; \
		docker compose --profile full down -v 2>/dev/null || true; \
		echo "  All data removed."; \
	else \
		echo "  Cancelled."; \
	fi

.PHONY: help
help: ## Show this help
	@echo ""
	@echo "  FinBot — Local Offline LLM Financial Analyst"
	@echo ""
	@echo "  NATIVE (recommended for macOS):"
	@grep -E '^[a-z][a-z_-]+:.*##' $(MAKEFILE_LIST) | grep -v docker | grep -v clean-all | \
		awk 'BEGIN {FS = ":.*##"}; {printf "    \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  DOCKER:"
	@grep -E '^docker-[a-z_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*##"}; {printf "    \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  MAINTENANCE:"
	@grep -E '^clean[a-z_-]*:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*##"}; {printf "    \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
