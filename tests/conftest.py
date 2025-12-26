"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app as flask_app
from app.models import db, User
from core.blockchain import SimpleBlockchain
from core.crypto_utils import CryptoManager
from core.ipfs_client import IPFSClient
from core.credential_manager import CredentialManager
from core.ticket_manager import TicketManager
from core.zkp_manager import ZKPManager


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    with flask_app.app_context():
        db.create_all()
        
        # Create test admin user
        admin = User(
            username='test_admin',
            role='issuer',
            full_name='Test Admin',
            email='admin@test.com',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create test student user
        student = User(
            username='test_student',
            role='student',
            student_id='TEST001',
            full_name='Test Student',
            email='student@test.com',
            is_active=True
        )
        student.set_password('student123')
        db.session.add(student)
        
        # Create test verifier user
        verifier = User(
            username='test_verifier',
            role='verifier',
            full_name='Test Verifier',
            email='verifier@test.com',
            is_active=True
        )
        verifier.set_password('verifier123')
        db.session.add(verifier)
        
        db.session.commit()
    
    yield flask_app
    
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands"""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client):
    """A test client with admin authentication"""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'test_admin'
        sess['role'] = 'issuer'
    return client


@pytest.fixture
def student_client(client):
    """A test client with student authentication"""
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = 'test_student'
        sess['role'] = 'student'
        sess['student_id'] = 'TEST001'
    return client


@pytest.fixture
def blockchain():
    """Create a test blockchain instance"""
    return SimpleBlockchain()


@pytest.fixture
def crypto_manager():
    """Create a test crypto manager instance"""
    return CryptoManager()


@pytest.fixture
def ipfs_client():
    """Create a test IPFS client instance"""
    return IPFSClient()


@pytest.fixture
def credential_manager(blockchain, crypto_manager, ipfs_client):
    """Create a test credential manager instance"""
    return CredentialManager(blockchain, crypto_manager, ipfs_client)


@pytest.fixture
def ticket_manager():
    """Create a test ticket manager instance"""
    return TicketManager()


@pytest.fixture
def zkp_manager(crypto_manager):
    """Create a test ZKP manager instance"""
    return ZKPManager(crypto_manager)


@pytest.fixture
def sample_credential_data():
    """Sample credential data for testing"""
    from datetime import datetime
    return {
        'student_name': 'John Doe',
        'student_id': 'TEST123',
        'degree': 'B.Tech Computer Science',
        'university': 'G. Pulla Reddy Engineering College',
        'gpa': 8.5,
        'graduation_year': 2024,
        'courses': ['Data Structures', 'Algorithms', 'DBMS'],
        'issue_date': datetime.now().isoformat(),  # ✅ ADDED THIS
        'issuer': 'G. Pulla Reddy Engineering College',
        'semester': 8,
        'year': 4,
        'class_name': 'B.Tech',
        'section': 'A',
        'backlog_count': 0,
        'backlogs': [],
        'conduct': 'good'
    }
