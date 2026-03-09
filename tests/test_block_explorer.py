"""
Tests for Blockchain Explorer Dashboard components
"""
import pytest
import json

def test_explorer_block_metadata_exposure(client):
    """Test that all required fields are exposed to the explorer dashboard"""
    from app.app import blockchain as app_blockchain
    index = len(app_blockchain.chain)
    app_blockchain.add_block({"explorer_test": True})
    
    response = client.get('/api/blockchain/blocks')
    blocks = json.loads(response.data)['blocks']
    
    latest = blocks[0] # Usually dashboard prefers descending order
    
    required_fields = ['index', 'timestamp', 'hash', 'previous_hash', 'signed_by', 'signature', 'merkle_root']
    for field in required_fields:
        assert field in latest
    
    assert latest['index'] == index
    assert latest['signed_by'] == 'admin'

def test_explorer_sorting(client):
    """Test that explorer endpoint delivers blocks in reverse chronological order"""
    from app.app import blockchain as app_blockchain
    index1 = len(app_blockchain.chain)
    app_blockchain.add_block({"order": 1})
    index2 = len(app_blockchain.chain)
    app_blockchain.add_block({"order": 2})
    
    response = client.get('/api/blockchain/blocks')
    blocks = json.loads(response.data)['blocks']
    
    assert blocks[0]['index'] == index2
    assert blocks[1]['index'] == index1
    assert blocks[-1]['index'] == 0

def test_explorer_empty_chain_safety(client, auth_client):
    """Test explorer safety when system is reset"""
    # 1. Reset
    auth_client.post('/api/system/reset', data=json.dumps({'confirmation': 'RESET_EVERYTHING'}), content_type='application/json')
    
    # 2. Check blocks
    response = client.get('/api/blockchain/blocks')
    data = json.loads(response.data)
    
    assert len(data['blocks']) == 1 # Only Genesis remains
    assert data['blocks'][0]['index'] == 0
