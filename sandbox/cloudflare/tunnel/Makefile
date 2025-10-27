# Makefile for Multi-Profile OAuth2 Handler
# Compatible with Windows make (GNU Make)

.PHONY: help install setup check run dev test clean status

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := uv run python
UV := uv
APP := oauth_multi_app_v2.py
TEST_CONFIG := test_config.py
ENV_FILE := .env
ENV_EXAMPLE := .env.example

help: ## Show this help message
	@echo ""
	@echo "Multi-Profile OAuth2 Handler - Makefile Commands"
	@echo "========================================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies with uv
	@echo "Installing dependencies from pyproject.toml..."
	$(UV) sync
	@echo "Done!"

setup: ## Copy .env.example to .env for configuration
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Creating .env from .env.example..."; \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo ""; \
		echo "Please edit .env with your credentials!"; \
		echo "Then run: make check"; \
	else \
		echo ".env already exists. Skipping."; \
	fi

check: ## Validate configuration
	@echo "Validating configuration..."
	@echo ""
	$(PYTHON) $(TEST_CONFIG)

run: ## Run the OAuth server
	@echo "Starting Multi-Profile OAuth2 Handler..."
	@echo ""
	$(PYTHON) $(APP)

dev: ## Run with auto-reload (for development)
	@echo "Starting in development mode with auto-reload..."
	@echo ""
	$(UV) run uvicorn oauth_multi_app_v2:app --reload --host 0.0.0.0 --port 8000

status: ## Check status of running server
	@echo "Checking server status..."
	@curl -s http://localhost:8000/status | $(PYTHON) -m json.tool || echo "Server not running on port 8000"

test: ## Test API endpoint (requires server running)
	@echo "Testing health check..."
	@curl -s http://localhost:8000/ || echo "Server not running on port 8000"

clean: ## Remove generated files and caches
	@echo "Cleaning up..."
	@rm -rf __pycache__ .pytest_cache
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "Done!"

# Cloudflare tunnel commands
tunnel: ## Start Cloudflare tunnel (requires cloudflared)
	@echo "Starting Cloudflare tunnel..."
	@echo ""
	@cloudflared tunnel --url http://localhost:8000

# Profile management
list-profiles: ## List all configured profiles
	@echo "Reading profiles from .env..."
	@echo ""
	@if [ -f $(ENV_FILE) ]; then \
		grep "^PROFILE_.*_CLIENT_ID" $(ENV_FILE); \
	else \
		echo ".env file not found. Run: make setup"; \
	fi

# Development helpers
format: ## Format code (requires black)
	@echo "Formatting code..."
	$(UV) run black *.py

lint: ## Lint code (requires ruff)
	@echo "Linting code..."
	$(UV) run ruff check *.py

# Installation helpers
install-cloudflared: ## Show instructions for installing cloudflared
	@echo ""
	@echo "To install Cloudflare Tunnel (cloudflared):"
	@echo ""
	@echo "Using Scoop (Windows):"
	@echo "  scoop install cloudflared"
	@echo ""
	@echo "Manual download:"
	@echo "  https://github.com/cloudflare/cloudflared/releases"
	@echo ""

# Quick start
quickstart: install setup ## Quick start: install and setup
	@echo ""
	@echo "========================================================"
	@echo "Quick start complete!"
	@echo "========================================================"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your UiPath credentials"
	@echo "  2. Run: make check"
	@echo "  3. Run: make run"
	@echo ""

# Full workflow
all: install setup check run ## Run full workflow: install, setup, check, and run

# Show environment info
info: ## Show environment information
	@echo ""
	@echo "Environment Information"
	@echo "========================================================"
	@echo "Python:"
	@$(PYTHON) --version
	@echo ""
	@echo "UV:"
	@$(UV) --version
	@echo ""
	@echo "Working Directory:"
	@pwd
	@echo ""
	@if [ -f $(ENV_FILE) ]; then \
		echo "Configuration: .env exists"; \
	else \
		echo "Configuration: .env NOT FOUND (run: make setup)"; \
	fi
	@echo ""
