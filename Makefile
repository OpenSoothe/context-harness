.PHONY: help install install-dev test test-cov lint format clean build docs

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
PACKAGE := context_harness
TEST_DIR := tests
COV_DIR := htmlcov

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "Context Harness - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev    # Install development dependencies"
	@echo "  make test           # Run all tests"
	@echo "  make lint           # Run all linters"
	@echo "  make format         # Format code with black and isort"

# =============================================================================
# Installation
# =============================================================================

venv: ## Create virtual environment
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
		echo "Virtual environment created at $(VENV)"; \
	else \
		echo "Virtual environment already exists"; \
	fi

install: venv ## Install production dependencies
	@echo "Installing production dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e .
	@echo "Production dependencies installed successfully"

install-dev: venv ## Install development dependencies
	@echo "Installing development dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e ".[dev]"
	@echo "Development dependencies installed successfully"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "Running tests..."
	$(VENV_PYTHON) -m pytest $(TEST_DIR) -v

test-cov: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	$(VENV_PYTHON) -m pytest $(TEST_DIR) --cov=$(PACKAGE) --cov-report=html --cov-report=term
	@echo "Coverage report generated at $(COV_DIR)/index.html"

test-quick: ## Run tests without verbose output (quick)
	@echo "Running quick tests..."
	$(VENV_PYTHON) -m pytest $(TEST_DIR) -q

test-failed: ## Run only failed tests from last run
	@echo "Running failed tests..."
	$(VENV_PYTHON) -m pytest $(TEST_DIR) --lf

test-specific: ## Run specific test file (usage: make test-specific TEST=test_thread.py)
	@echo "Running specific test: $(TEST)"
	$(VENV_PYTHON) -m pytest $(TEST_DIR)/$(TEST) -v

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run all linters (flake8, mypy)
	@echo "Running linters..."
	@echo "=== Flake8 ==="
	$(VENV_PYTHON) -m flake8 $(PACKAGE) $(TEST_DIR) --max-line-length=88 --extend-ignore=E203
	@echo "=== MyPy ==="
	$(VENV_PYTHON) -m mypy $(PACKAGE)
	@echo "Linting complete"

format: ## Format code with black and isort
	@echo "Formatting code..."
	$(VENV_PYTHON) -m black $(PACKAGE) $(TEST_DIR)
	$(VENV_PYTHON) -m isort $(PACKAGE) $(TEST_DIR)
	@echo "Code formatted successfully"

format-check: ## Check if code is formatted (no changes)
	@echo "Checking code formatting..."
	$(VENV_PYTHON) -m black --check $(PACKAGE) $(TEST_DIR)
	$(VENV_PYTHON) -m isort --check --diff $(PACKAGE) $(TEST_DIR)
	@echo "Format check complete"

# =============================================================================
# Build & Packaging
# =============================================================================

build: ## Build package distributions
	@echo "Building package..."
	$(VENV_PYTHON) -m pip install --upgrade build
	$(VENV_PYTHON) -m build
	@echo "Package built successfully"

dist: build ## Create distribution archives
	@echo "Distribution archives created in dist/"

clean-dist: ## Clean distribution archives
	@echo "Cleaning dist/ directory..."
	rm -rf dist/
	rm -rf *.egg-info
	@echo "Distribution archives cleaned"

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "Documentation available at docs/specs/ and docs/impl/"
	@ls -la docs/specs/*.md
	@ls -la docs/impl/*.md

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean all generated files
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf $(COV_DIR)
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	@echo "Generated files cleaned"

clean-all: clean clean-dist ## Clean everything including venv
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Everything cleaned"

# =============================================================================
# Development Utilities
# =============================================================================

check: lint test ## Run linters and tests (full check)
	@echo "=== Full check complete ==="

ci: format-check lint test-cov ## Simulate CI pipeline (format check + lint + coverage)
	@echo "=== CI simulation complete ==="

dev-setup: install-dev format lint test ## Full development setup
	@echo "=== Development environment ready ==="

reset: clean-all install-dev ## Reset development environment
	@echo "=== Environment reset complete ==="

# =============================================================================
# Package Info
# =============================================================================

info: ## Show package information
	@echo "Package: $(PACKAGE)"
	@$(VENV_PYTHON) -c "import $(PACKAGE); print('Version:', $(PACKAGE).__version__); print('Exports:', $(PACKAGE).__all__)"

tree: ## Show package structure
	@echo "Package structure:"
	@tree -I '__pycache__|*.pyc|venv|.venv' $(PACKAGE) 2>/dev/null || find $(PACKAGE) -type f -name "*.py" | head -20

# =============================================================================
# Special Targets
# =============================================================================

pre-commit: format lint test ## Run all checks before committing
	@echo "=== Pre-commit checks passed ==="

publish-test: build ## Publish to test PyPI (requires twine)
	@echo "Publishing to test PyPI..."
	$(VENV_PYTHON) -m twine upload --repository testpypi dist/*
	@echo "Package published to test.pypi.org"

publish: build ## Publish to PyPI (requires twine)
	@echo "Publishing to PyPI..."
	$(VENV_PYTHON) -m twine upload dist/*
	@echo "Package published to pypi.org"

version: ## Show current version
	@$(VENV_PYTHON) -c "import $(PACKAGE); print($(PACKAGE).__version__)"