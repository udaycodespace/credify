.PHONY: help install dev run test clean deploy lint format

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
PORT := 5000

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Blockchain Credential Verification System$(NC)"
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev: ## Setup development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Development environment ready!$(NC)"
	@echo "$(YELLOW)Activate with: source $(VENV)/bin/activate$(NC)"

run: ## Run the application locally
	@echo "$(GREEN)Starting application on port $(PORT)...$(NC)"
	$(PYTHON) main.py

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=app --cov=core

clean: ## Clean up generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

lint: ## Run code linting
	@echo "$(GREEN)Running linter...$(NC)"
	$(PYTHON) -m flake8 app/ core/ --max-line-length=120

format: ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	$(PYTHON) -m black app/ core/ --line-length=120

init-data: ## Initialize data files
	@echo "$(GREEN)Initializing data files...$(NC)"
	mkdir -p data logs
	@echo '{"chain": [], "difficulty": 4}' > data/blockchain_data.json
	@echo '{}' > data/credentials_registry.json
	@echo '{}' > data/ipfs_storage.json
	@echo '{}' > data/tickets.json
	@echo '{}' > data/messages.json
	@echo "$(GREEN)✅ Data files initialized!$(NC)"

deploy-check: ## Check if ready for deployment
	@echo "$(GREEN)Checking deployment readiness...$(NC)"
	@echo "$(YELLOW)1. Checking requirements.txt...$(NC)"
	@test -f requirements.txt && echo "$(GREEN)✅ requirements.txt exists$(NC)" || echo "$(YELLOW)❌ Missing requirements.txt$(NC)"
	@echo "$(YELLOW)2. Checking main.py...$(NC)"
	@test -f main.py && echo "$(GREEN)✅ main.py exists$(NC)" || echo "$(YELLOW)❌ Missing main.py$(NC)"
	@echo "$(YELLOW)3. Checking app structure...$(NC)"
	@test -d app && echo "$(GREEN)✅ app/ directory exists$(NC)" || echo "$(YELLOW)❌ Missing app/ directory$(NC)"
	@echo "$(GREEN)✅ Deployment check complete!$(NC)"

create-student: ## Create a sample student account
	@echo "$(GREEN)Creating sample student...$(NC)"
	$(PYTHON) create_student.py

logs: ## View application logs
	@echo "$(GREEN)Recent logs:$(NC)"
	@tail -f logs/*.log 2>/dev/null || echo "$(YELLOW)No logs found$(NC)"

shell: ## Start Python shell with app context
	@echo "$(GREEN)Starting Python shell...$(NC)"
	$(PYTHON) -i -c "from app.app import app; from core import *"
