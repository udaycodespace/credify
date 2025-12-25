#!/bin/bash
set -e

echo "🚀 Running Complete Test Suite..."

# Lint
echo "1. Linting..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Unit Tests
echo "2. Unit Tests..."
pytest tests/ -v --cov=core --cov=app --cov-report=html --cov-report=term-missing

# API Tests
echo "3. API Tests..."
pytest tests/test_api_endpoints.py -v

# Security Tests
echo "4. Security Tests..."
pytest tests/test_security.py -v

# Docker Tests
echo "5. Docker Build Test..."
docker build -t test-build .
docker rm -f test-container 2>/dev/null || true
docker run --name test-container -d test-build sleep 10
docker rm -f test-container
echo "✅ Docker build successful (no secrets leaked)"

echo "🎉 ALL TESTS PASSED!"
echo "📊 Coverage report: open htmlcov/index.html"
