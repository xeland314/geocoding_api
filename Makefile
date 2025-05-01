# Makefile for automating tasks in FastAPI

# Variables
PROJECT_NAME := pygeocoder
APP_MODULE := main
APP_NAME := app
RELOAD := --reload
HOST := 0.0.0.0
PORT := 8000

# Virtual Environment
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
ACTIVATE := source $(VENV_DIR)/bin/activate
UV := uv # Assumes uv is installed in the same venv

# Commands

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo "Available targets:"
	@grep -E '^\.PHONY: .*' Makefile | sed 's/\.PHONY: //' | column -t

.PHONY: set-env
set-env: ## (Optional) Runs a script to set up the environment if available
	@echo "Run the following command to configure the environment:"
	@echo "source ./scripts/set_env.sh"

.PHONY: venv
venv: check-uv ## Creates a virtual environment using uv
	@echo "Creating virtual environment with uv in $(VENV_DIR)..."
	@test -d "$(VENV_DIR)" || $(UV) venv $(VENV_DIR)
	@echo "Virtual environment created. Activate it with: source $(VENV_DIR)/bin/activate"

.PHONY: install
install: venv ## Installs dependencies
	@echo "Installing dependencies..."
	$(PIP) install -r pyproject.toml

.PHONY: runserver
runserver: ## Starts the development server
	@echo "Starting development server..."
	$(PYTHON) -m uvicorn $(APP_MODULE):$(APP_NAME) --host $(HOST) --port $(PORT) $(RELOAD)

.PHONY: test
test: ## Runs tests using unittest
	@echo "Running tests with unittest..."
	$(PYTHON) -m unittest discover -s tests -p "*.py"

.PHONY: lint
lint: ## Runs the linter (example: flake8)
	@echo "Running linter..."
	# @$(PYTHON) -m flake8 . --max-line-length=120
	@echo "No linter is configured. Install a linter (e.g. flake8) and set it up."

.PHONY: format
format: ## Formats code (example: black)
	@echo "Formatting code..."
	# @$(PYTHON) -m black .
	@echo "No formatter is configured. Install a formatter (e.g. black) and set it up."

.PHONY: check-uv
check-uv: ## Checks if uv is installed, installs if missing
	@echo "Checking uv installation..."
	@command -v $(UV) >/dev/null 2>&1 || \
	    (command -v pipx >/dev/null 2>&1 && pipx install uv) || \
	    (command -v curl >/dev/null 2>&1 && curl -LsSf https://astral.sh/uv/install.sh | sh) || \
	    (command -v wget >/dev/null 2>&1 && wget -qO- https://astral.sh/uv/install.sh | sh) || \
	    (echo "Error: Unable to install uv. pipx, curl, and wget are unavailable." && exit 1)
	@echo "uv is installed."

# Example usage:
# make runserver
# make env
# make venv
# make install
# make test
# make help
