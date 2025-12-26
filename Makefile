# Makefile for Credify Project

.PHONY: help install run test clean docker-build docker-run deploy

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:  ## Show this help message
	@echo "$(BLUE)Credify - Blockchain Credential System$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install:  ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

install-prod:  ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Production dependencies installed!$(NC)"

run:  ## Run the application
	@echo "$(BLUE)Starting application...$(NC)"
	python main.py

test:  ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest -v --tb=short

test-cov:  ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest -v --cov=app --cov=core --cov-report=html --cov-report=term

lint:  ## Run linting
	@echo "$(BLUE)Running linters...$(NC)"
	flake8 app core --count --statistics
	black --check app core
	isort --check-only app core

format:  ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	black app core
	isort app core
	@echo "$(GREEN)✅ Code formatted!$(NC)"

clean:  ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	@echo "$(GREEN)✅ Cleaned up!$(NC)"

reset-data:  ## Reset all data files
	@echo "$(RED)⚠️  Resetting all data...$(NC)"
	rm -rf data/*.json
	rm -rf instance/*.db
	python -c "from app.models import init_database; from app.app import app; init_database(app)"
	@echo "$(GREEN)✅ Data reset!$(NC)"

create-admin:  ## Create admin user
	@echo "$(BLUE)Creating admin user...$(NC)"
	python scripts/create_admin.py

docker-build:  ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t credify:latest .
	@echo "$(GREEN)✅ Docker image built!$(NC)"

docker-run:  ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -d -p 5000:5000 --name credify credify:latest
	@echo "$(GREEN)✅ Container running at http://localhost:5000$(NC)"

docker-stop:  ## Stop Docker container
	@echo "$(BLUE)Stopping Docker container...$(NC)"
	docker stop credify
	docker rm credify
	@echo "$(GREEN)✅ Container stopped!$(NC)"

docker-logs:  ## View Docker logs
	docker logs -f credify

deploy-check:  ## Check deployment readiness
	@echo "$(BLUE)Checking deployment readiness...$(NC)"
	@python -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'"
	@test -f requirements.txt || (echo "$(RED)❌ requirements.txt missing$(NC)" && exit 1)
	@test -f Dockerfile || (echo "$(RED)❌ Dockerfile missing$(NC)" && exit 1)
	@test -f main.py || (echo "$(RED)❌ main.py missing$(NC)" && exit 1)
	@echo "$(GREEN)✅ Deployment ready!$(NC)"

init-db:  ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	python -c "from app.models import init_database; from app.app import app; init_database(app)"
	@echo "$(GREEN)✅ Database initialized!$(NC)"

dev:  ## Run in development mode
	@echo "$(BLUE)Starting development server...$(NC)"
	export FLASK_ENV=development && python main.py

prod:  ## Run in production mode
	@echo "$(BLUE)Starting production server...$(NC)"
	export FLASK_ENV=production && python main.py
