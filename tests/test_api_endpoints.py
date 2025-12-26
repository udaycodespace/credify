"""
Test cases for API endpoints
"""

import pytest
import json


class TestAPIEndpoints:
    
    def test_home_page(self, client):
        """Test home page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_login_page(self, client):
        """Test login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_issuer_login(self, client):
        """Test issuer login"""
        response = client.post('/login', data={
            'user_id': 'admin',
            'password': 'admin123',
            'role': 'issuer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_get_credential_api(self, authenticated_session, sample_credential_data):
        """Test GET credential API"""
        # First issue a credential
        response = authenticated_session.post(
            '/api/issue_credential',
            data=json.dumps(sample_credential_data),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        if data.get('success'):
            credential_id = data['credential_id']
            
            # Get credential
            response = authenticated_session.get(f'/api/get_credential/{credential_id}')
            assert response.status_code == 200
    
    def test_verify_credential_api(self, client, sample_credential_data):
        """Test verify credential API"""
        response = client.post(
            '/api/verify_credential',
            data=json.dumps({'credential_id': 'TEST123'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'valid' in data
    
    def test_selective_disclosure_api(self, authenticated_session, sample_credential_data):
        """Test selective disclosure API"""
        # Issue credential first
        response = authenticated_session.post(
            '/api/issue_credential',
            data=json.dumps(sample_credential_data),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        if data.get('success'):
            credential_id = data['credential_id']
            
            # Create selective disclosure
            response = authenticated_session.post(
                '/api/selective_disclosure',
                data=json.dumps({
                    'credential_id': credential_id,
                    'fields': ['student_name', 'gpa']
                }),
                content_type='application/json'
            )
            
            assert response.status_code == 200
    
    def test_zkp_range_proof_api(self, authenticated_session):
        """Test ZKP range proof API"""
        response = authenticated_session.post(
            '/api/zkp/range_proof',
            data=json.dumps({
                'credential_id': 'TEST123',
                'field': 'gpa',
                'actual_value': 8.5,
                'min_threshold': 7.5
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data
    
    def test_zkp_verify_api(self, client):
        """Test ZKP verification API"""
        proof = {
            'type': 'RangeProof',
            'credentialId': 'TEST123',
            'field': 'gpa',
            'commitment': 'abc123',
            'minThreshold': 7.5
        }
        
        response = client.post(
            '/api/zkp/verify',
            data=json.dumps({'proof': proof}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
