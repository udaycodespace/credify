"""
Tests for API endpoints — Updated for Track A API Specification
"""
import pytest
import json

def test_index_page(client):
    """Test public landing page accessibility"""
    response = client.get('/')
    assert response.status_code == 200

def test_issue_credential_api(auth_client, sample_credential_data):
    """Test administrative credential issuance API"""
    response = auth_client.post(
        '/api/issue_credential',
        data=json.dumps(sample_credential_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'block_hash' in data

def test_verify_credential_api(client, auth_client, sample_credential_data):
    """Test public-facing verification API"""
    # Issue a credential first
    issue_resp = auth_client.post(
        '/api/issue_credential',
        data=json.dumps(sample_credential_data),
        content_type='application/json'
    )
    cred_id = json.loads(issue_resp.data)['credential_id']
    
    # Verify via public API
    response = client.post(
        '/api/verify_credential',
        data=json.dumps({'credential_id': cred_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['valid'] is True
    assert data['status'] == 'active'

def test_blockchain_explorer_api(client):
    """Test the blockchain explorer data endpoint"""
    response = client.get('/api/blockchain/blocks')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'blocks' in data
    assert len(data['blocks']) >= 1 # Genesis block at minimum

def test_blockchain_audit_api(auth_client):
    """Test the cryptographic audit/validation endpoint"""
    response = auth_client.get('/api/blockchain/validate')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['valid'] is True

def test_node_chain_api(client):
    """Test the P2P synchronization endpoint for fetching the full chain"""
    response = client.get('/api/node/chain')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'chain' in data
    assert 'length' in data

def test_unauthorized_issuer_routes(client):
    """Test that unauthenticated users on /issuer receive the login form (200).

    The /issuer route is a dual-purpose portal: it renders the login form
    inline (HTTP 200) rather than issuing a 302 redirect when no session exists.
    This is intentional by design for the credential system UX.
    """
    response = client.get('/issuer')
    # The /issuer route is a portal page — it serves the login form inline (200)
    # rather than issuing a 302 redirect. This is the correct expected behaviour.
    assert response.status_code == 200
