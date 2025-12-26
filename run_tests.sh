#!/bin/bash

# ============================================
# Test Runner for Blockchain Credential System
# ============================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🧪 Running Test Suite                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    source venv/bin/activate
fi

# Create test directories if they don't exist
mkdir -p tests data logs

# Initialize test data files
echo -e "${BLUE}📁 Initializing test data files...${NC}"
echo '{"chain": [], "difficulty": 4}' > data/blockchain_data.json
echo '{}' > data/credentials_registry.json
echo '{}' > data/ipfs_storage.json
echo '{}' > data/tickets.json
echo '{}' > data/messages.json

# Run linting (optional - comment out if not needed)
echo -e "${BLUE}🔍 Running code linting...${NC}"
if command -v flake8 &> /dev/null; then
    flake8 app/ core/ --max-line-length=120 --exclude=venv,__pycache__ || echo -e "${YELLOW}⚠️  Linting issues found (non-blocking)${NC}"
else
    echo -e "${YELLOW}⚠️  flake8 not installed, skipping lint${NC}"
fi

# Run tests with pytest
echo -e "${BLUE}🧪 Running pytest...${NC}"
if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
    pytest tests/ -v --cov=app --cov=core --cov-report=html --cov-report=term-missing
    TEST_RESULT=$?
else
    echo -e "${YELLOW}⚠️  No tests found in tests/ directory${NC}"
    echo -e "${YELLOW}Creating sample test file...${NC}"
    
    cat > tests/test_app.py << 'EOF'
import pytest
from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    """Test that homepage loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_login_page(client):
    """Test that login page loads"""
    response = client.get('/login')
    assert response.status_code == 200
EOF
    
    pytest tests/ -v
    TEST_RESULT=$?
fi

# Display results
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ALL TESTS PASSED!                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ TESTS FAILED                          ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
fi

# Show coverage report location
if [ -f "htmlcov/index.html" ]; then
    echo -e "${BLUE}📊 Coverage report: htmlcov/index.html${NC}"
fi

exit $TEST_RESULT