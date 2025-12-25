import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from core.credential_manager import CredentialManager
from core.blockchain import SimpleBlockchain
from core.crypto_utils import CryptoManager
from core.ipfs_client import IPFSClient

@pytest.fixture
def mock_components():
    blockchain = Mock(spec=SimpleBlockchain)
    crypto = Mock(spec=CryptoManager)
    ipfs = Mock(spec=IPFSClient)
    return blockchain, crypto, ipfs

@pytest.fixture
def credential_manager(mock_components):
    blockchain, crypto, ipfs = mock_components
    return CredentialManager(blockchain, crypto, ipfs)

def test_issue_credential_success(credential_manager, mock_components):
    """Test successful credential issuance with all fields"""
    blockchain, crypto, ipfs = mock_components
    
    # Mock responses
    crypto.sign_data.return_value = "mock_signature"
    crypto.hash_data.return_value = "mock_hash"
    ipfs.add_json.return_value = "Qm_mock_ipfs_cid"
    
    block_mock = Mock()
    block_mock.hash = "mock_block_hash"
    blockchain.add_block.return_value = block_mock
    
    # Test data with extended fields
    transcript_data = {
        'student_name': 'John Doe',
        'student_id': '12345',
        'degree': 'B.Tech CS',
        'university': 'GPREC',
        'gpa': 8.5,
        'graduation_year': 2026,
        'semester': 5,
        'year': 3,
        'class_name': 'B.Tech',
        'section': 'A',
        'backlog_count': 1,
        'backlogs': ['DBMS'],
        'conduct': 'good',
        'issue_date': datetime.now().isoformat()
    }
    
    result = credential_manager.issue_credential(transcript_data)
    
    assert result['success'] is True
    assert 'credential_id' in result
    assert result['ipfs_cid'] == 'Qm_mock_ipfs_cid'
    assert result['block_hash'] == 'mock_block_hash'

def test_extended_fields_stored_correctly(credential_manager, mock_components):
    """Verify extended fields are stored in registry"""
    # Setup mocks (same as above)
    blockchain, crypto, ipfs = mock_components
    crypto.sign_data.return_value = "signature"
    crypto.hash_data.return_value = "hash"
    ipfs.add_json.return_value = "cid"
    block_mock = Mock(hash="block_hash")
    blockchain.add_block.return_value = block_mock
    
    transcript_data = {
        'student_name': 'Test Student',
        'student_id': 'TEST001',
        'degree': 'B.Tech',
        'university': 'Test Uni',
        'gpa': 8.0,
        'graduation_year': 2025,
        'semester': 6,
        'backlog_count': 2
    }
    
    result = credential_manager.issue_credential(transcript_data)
    credential_id = result['credential_id']
    
    # Verify registry contains extended fields
    registry_entry = credential_manager.credentials_registry[credential_id]
    assert registry_entry['semester'] == 6
    assert registry_entry['backlog_count'] == 2

def test_validation_handles_null_fields(credential_manager, mock_components):
    """Test optional fields work correctly"""
    # Remove optional fields
    transcript_data = {
        'student_name': 'Jane Doe',
        'student_id': '67890',
        'degree': 'B.Tech',
        'university': 'GPREC',
        'gpa': 7.8,
        'graduation_year': 2026,
        'issue_date': datetime.now().isoformat()
    }
    
    # Mocks setup
    blockchain, crypto, ipfs = mock_components
    crypto.sign_data.return_value = "sig"
    ipfs.add_json.return_value = "cid"
    block_mock = Mock(hash="hash")
    blockchain.add_block.return_value = block_mock
    
    result = credential_manager.issue_credential(transcript_data)
    assert result['success'] is True
