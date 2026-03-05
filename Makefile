# ============================================
# 🦊 Zephyr — Project Commands
# ============================================

.PHONY: help dev test lint build clean install docker docker-up docker-down

PYTHON := python3
PIP := pip
NPM := npm

# Default target
help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Install ──────────────────────────────────

install: ## Install all dependencies (Python + Frontend)
	$(PIP) install -r requirements.txt
	playwright install chromium --with-deps
	@if [ -d "zephyr_ui" ]; then cd zephyr_ui && $(NPM) ci; fi
	@if [ -d "packages/zephyr-ui" ]; then cd packages/zephyr-ui && $(NPM) ci; fi

install-dev: install ## Install with dev/test dependencies
	$(PIP) install ruff pyright

# ── Development ──────────────────────────────

dev: ## Start backend dev server with auto-reload
	uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

dev-ui: ## Start frontend dev server
	cd zephyr_ui && $(NPM) run dev

dev-all: ## Start backend + frontend (requires tmux or 2 terminals)
	@echo "Terminal 1: make dev"
	@echo "Terminal 2: make dev-ui"
	@echo ""
	@echo "Or run both with: make dev & make dev-ui"

mcp: ## Start MCP server (for IDE integration)
	$(PYTHON) -m mcp_server

# ── Testing ──────────────────────────────────

test: ## Run all Python tests
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=. --cov-report=term-missing

test-ui: ## Run frontend tests
	@if [ -d "packages/zephyr-ui" ]; then cd packages/zephyr-ui && $(NPM) run test; fi

test-all: test test-ui ## Run all tests (backend + frontend)

# ── Linting ──────────────────────────────────

lint: ## Lint Python code with ruff
	ruff check .

lint-fix: ## Auto-fix lint issues
	ruff check --fix .

format: ## Format Python code
	ruff format .

typecheck: ## Type-check Python code
	pyright

# ── Build ────────────────────────────────────

build-ui: ## Build frontend for production
	cd zephyr_ui && $(NPM) run build

build-pkg: ## Build @zephyr/ui package
	cd packages/zephyr-ui && $(NPM) run build

build: build-ui build-pkg ## Build everything

# ── Docker ───────────────────────────────────

docker: ## Build Docker image
	docker build -t zephyr-intelligence .

docker-up: ## Start with docker-compose
	docker compose up -d

docker-down: ## Stop docker-compose
	docker compose down

docker-logs: ## Show docker logs
	docker compose logs -f

# ── Cleanup ──────────────────────────────────

clean: ## Remove build artifacts and caches
	rm -rf __pycache__ **/__pycache__ .pytest_cache .ruff_cache
	rm -rf zephyr_ui/dist packages/zephyr-ui/dist
	rm -rf reports/screenshots/*.png
	find . -name "*.pyc" -delete
