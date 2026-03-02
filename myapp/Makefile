.PHONY: run dev test lint format migrate clean help

# ── Variables ─────────────────────────────────────────────────────
PYTHON ?= python
APP    ?= myapp

# ── Development ───────────────────────────────────────────────────

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

run: ## Start development server with hot-reload
	aq run

dev: ## Start development server (alias for run)
	aq run --mode=dev

prod: ## Start production server
	aq run --mode=prod

# ── Testing ───────────────────────────────────────────────────────

test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest tests/ --cov=$(APP) --cov-report=term-missing

# ── Database ──────────────────────────────────────────────────────

migrate: ## Apply database migrations
	aq db migrate

makemigrations: ## Generate new migration
	aq db makemigrations

# ── Code Quality ──────────────────────────────────────────────────

lint: ## Run linter
	$(PYTHON) -m ruff check .

format: ## Auto-format code
	$(PYTHON) -m ruff format .

# ── Build & Deploy ────────────────────────────────────────────────

compile: ## Compile workspace artifacts
	aq compile

freeze: ## Freeze artifacts for deployment
	aq freeze

docker-build: ## Build Docker image
	docker build -t $(APP) .

docker-run: ## Run in Docker container
	docker compose up

# ── Housekeeping ──────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf artifacts/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage
	@echo "Cleaned."

doctor: ## Diagnose workspace issues
	aq doctor
