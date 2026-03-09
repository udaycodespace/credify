"""
Tests for P2P Networking and Peer Synchronization
"""
import pytest
import json

def test_peer_registration(blockchain):
    """Test correctly parsing and registering peer addresses"""
    blockchain.register_node("http://192.168.1.10:5000")
    blockchain.register_node("http://node2:5000")
    
    assert "192.168.1.10:5000" in blockchain.nodes
    assert "node2:5000" in blockchain.nodes

def test_fetch_chain_api(client):
    """Test the /api/node/chain endpoint used for synchronization"""
    from app.app import blockchain as app_blockchain
    # Add some dummy blocks
    app_blockchain.add_block({"p2p": "test"})
    
    response = client.get('/api/node/chain')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'chain' in data
    assert data['length'] == len(app_blockchain.chain)
    assert data['chain'][-1]['data'] == {"p2p": "test"}

def test_receive_block_unauthorized_signature(client, blockchain):
    """Test rejecting a block broadcast with an invalid signature"""
    # Mock a block from a peer
    bad_block = {
        "index": 1,
        "timestamp": "2026-03-07T00:00:00",
        "data": {"stolen": "identity"},
        "previous_hash": blockchain.chain[0].hash,
        "nonce": 0,
        "hash": "some_fake_hash",
        "signed_by": "hacker",
        "signature": "fake_signature"
    }
    
    response = client.post(
        '/api/node/receive_block',
        data=json.dumps(bad_block),
        content_type='application/json'
    )
    
    # Rejection status (400 or 403)
    assert response.status_code in [400, 401, 403, 409]
    # Verify chain length didn't change (still 1 - genesis)
    assert len(blockchain.chain) == 1

def test_receive_block_valid_workflow(client, crypto_manager):
    """Test accepting a valid block broadcast (simulating peer-to-peer relay)"""
    from app.app import blockchain as app_blockchain
    # Create a valid block manually for "node2"
    index = len(app_blockchain.chain)
    data = {"peer_relay": "success"}
    prev_hash = app_blockchain.get_latest_block().hash
    from core.blockchain import Block
    
    valid_peer_block = Block(index, data, prev_hash, signed_by="admin")
    valid_peer_block.mine_block(0)
    valid_peer_block.signature = crypto_manager.sign_data(valid_peer_block.hash)
    
    response = client.post(
        '/api/node/receive_block',
        data=json.dumps(valid_peer_block.to_dict()),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    assert json.loads(response.data)['success'] is True
    assert len(app_blockchain.chain) == index + 1
