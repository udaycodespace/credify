"""
Test cases for Credential Management
"""

import pytest
from core.credential_manager import CredentialManager


class TestCredentialManager:
    
    def test_credential_creation(self, credential_manager, sample_credential_data):
        """Test creating a new credential"""
        result = credential_manager.issue_credential(sample_credential_data)
        
        assert result['success'] == True
        assert 'credential_id' in result
        assert result['credential_id'].startswith('CRED-')
    
    def test_credential_storage(self, credential_manager, sample_credential_data):
        """Test credential is stored in registry"""
        result = credential_manager.issue_credential(sample_credential_data)
        credential_id = result['credential_id']
        
        # Retrieve credential
        credential = credential_manager.get_credential(credential_id)
        
        assert credential is not None
        assert credential['student_id'] == sample_credential_data['student_id']
    
    def test_credential_hash_generation(self, credential_manager, sample_credential_data):
        """Test credential hash is generated"""
        result = credential_manager.issue_credential(sample_credential_data)
        credential_id = result['credential_id']
        
        credential = credential_manager.get_credential(credential_id)
        
        assert 'credential_hash' in credential
        assert len(credential['credential_hash']) == 64  # SHA-256
    
    def test_selective_disclosure(self, credential_manager, sample_credential_data):
        """Test selective disclosure functionality"""
        # Issue credential
        result = credential_manager.issue_credential(sample_credential_data)
        credential_id = result['credential_id']
        
        # Create selective disclosure
        fields = ['student_name', 'degree', 'gpa']
        disclosure = credential_manager.create_selective_disclosure(
            credential_id, 
            fields
        )
        
        assert disclosure is not None
        assert 'disclosedFields' in disclosure
        assert len(disclosure['disclosedFields']) == len(fields)
    
    def test_credential_revocation(self, credential_manager, sample_credential_data):
        """Test credential revocation"""
        # Issue credential
        result = credential_manager.issue_credential(sample_credential_data)
        credential_id = result['credential_id']
        
        # Revoke credential
        revoke_result = credential_manager.revoke_credential(
            credential_id,
            reason='Testing revocation'
        )
        
        assert revoke_result['success'] == True
        
        # Check status
        credential = credential_manager.get_credential(credential_id)
        assert credential['status'] == 'revoked'
    
    def test_get_student_credentials(self, credential_manager, sample_credential_data):
        """Test retrieving all credentials for a student"""
        student_id = sample_credential_data['student_id']
        
        # Issue multiple credentials
        credential_manager.issue_credential(sample_credential_data)
        credential_manager.issue_credential(sample_credential_data)
        
        # Get all credentials
        credentials = credential_manager.get_student_credentials(student_id)
        
        assert len(credentials) >= 2
