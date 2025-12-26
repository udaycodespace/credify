"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.app import app
from core.blockchain import SimpleBlockchain, Block  # NOT Blockchain! # ✅ YOUR ACTUAL CLASSES
from core.credential_manager import CredentialManager
from core.ipfs_client import IPFSClient
from core.ticket_manager import TicketManager


@pytest.fixture
def flask_app():
    """Create Flask app for testing"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(flask_app):
    """Create test client"""
    return flask_app.test_client()


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    
    # Create test data files
    data_files = {
        'blockchain_data.json': '{"chain": [], "difficulty": 2}',
        'credentials_registry.json': '{}',
        'ipfs_storage.json': '{}',
        'tickets.json': '{}',
        'messages.json': '{}'
    }
    
    for filename, content in data_files.items():
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def blockchain():
    """Create fresh blockchain instance"""
    return SimpleBlockchain(difficulty=2)  # ✅ FIXED


@pytest.fixture
def credential_manager(blockchain):
    """Create credential manager instance"""
    return CredentialManager(blockchain)


@pytest.fixture
def ipfs_client():
    """Create IPFS client instance"""
    return IPFSClient()


@pytest.fixture
def ticket_manager():
    """Create ticket manager instance"""
    return TicketManager()


@pytest.fixture
def sample_credential_data():
    """Sample credential data for testing"""
    return {
        'student_id': 'TEST001',
        'student_name': 'John Doe',
        'degree': 'Bachelor of Computer Science',
        'university': 'Test University',
        'gpa': '8.5',
        'graduation_year': '2024',
        'semester': '8',
        'year': '4',
        'class_name': 'CS-A',
        'section': 'A',
        'backlog_count': '0',
        'conduct': 'excellent',
        'courses': ['Data Structures', 'Algorithms', 'Operating Systems'],
        'backlogs': []
    }


@pytest.fixture
def authenticated_session(client):
    """Create authenticated session"""
    with client.session_transaction() as session:
        session['user_id'] = 'admin'
        session['role'] = 'issuer'
    return client


@pytest.fixture
def student_session(client):
    """Create student session"""
    with client.session_transaction() as session:
        session['user_id'] = 'TEST001'
        session['role'] = 'student'
        session['student_id'] = 'TEST001'
    return client
