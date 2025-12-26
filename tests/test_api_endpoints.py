"""
Tests for API endpoints
"""
import pytest
import json


def test_index_page(client):
    """Test landing page"""
    response = client.get('/')
    assert response.status_code == 200


def test_issue_credential_api(auth_client, sample_credential_data):
    """Test credential issuance API"""
    response = auth_client.post(
        '/api/issue_credential',
        data=json.dumps(sample_credential_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_verify_credential_api(auth_client, sample_credential_data):
    """Test credential verification API"""
    # Issue a credential first
    issue_response = auth_client.post(
        '/api/issue_credential',
        data=json.dumps(sample_credential_data),
        content_type='application/json'
    )
    credential_id = json.loads(issue_response.data)['credential_id']
    
    # Verify it
    response = auth_client.post(
        '/api/verify_credential',
        data=json.dumps({'credential_id': credential_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['valid'] is True


def test_blockchain_status_api(client):
    """Test blockchain status API"""
    response = client.get('/api/blockchain_status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'total_blocks' in data
    assert 'total_credentials' in data


def test_system_stats_api(auth_client):
    """Test system statistics API"""
    response = auth_client.get('/api/system/stats')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'stats' in data
    assert 'credentials' in data['stats']
    assert 'users' in data['stats']


def test_unauthorized_access(client):
    """Test unauthorized API access"""
    response = client.get('/api/credentials')
    assert response.status_code == 302  # Redirect to login
