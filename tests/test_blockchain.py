"""
Tests for blockchain functionality — Updated for Track A (PoA + SQL Storage)
"""
import pytest
from core.blockchain import SimpleBlockchain, Block
from app.models import db, BlockRecord

def test_blockchain_initialization(blockchain):
    """Test blockchain initializes with genesis block and SQL backing"""
    assert len(blockchain.chain) >= 1
    genesis = blockchain.chain[0]
    assert genesis.index == 0
    assert genesis.signed_by == "System"

def test_add_block_with_poa(blockchain):
    """Test adding a block with Proof of Authority validation"""
    initial_length = len(blockchain.chain)
    data = {'credential_id': 'TEST123', 'action': 'issue'}
    
    # Authorized signer
    block = blockchain.add_block(data, signed_by="admin")
    
    assert len(blockchain.chain) == initial_length + 1
    assert block.signed_by == "admin"
    assert block.signature is not None
    assert block.previous_hash == blockchain.chain[-2].hash

def test_add_block_unauthorized(blockchain):
    """Test that unauthorized signers are rejected (PoA)"""
    data = {'credential_id': 'HACKER'}
    
    with pytest.raises(PermissionError):
        blockchain.add_block(data, signed_by="hacker_user")

def test_block_merkle_root(blockchain):
    """Test that Merkle roots are calculated for block data"""
    data = {'id': 1, 'name': 'test', 'hash': 'abc'}
    block = blockchain.add_block(data)
    
    assert block.merkle_root is not None
    assert len(block.merkle_root) == 64 # SHA-256

def test_sql_persistence(blockchain, app):
    """Test that blocks are actually saved to the SQL database"""
    initial_db_count = 0
    with app.app_context():
        initial_db_count = BlockRecord.query.count()
        
    blockchain.add_block({'test': 'sql_storage'})
    
    with app.app_context():
        final_db_count = BlockRecord.query.count()
        assert final_db_count == initial_db_count + 1
        last_record = BlockRecord.query.order_by(BlockRecord.index.desc()).first()
        assert last_record.signed_by == "admin"

def test_is_chain_valid(blockchain):
    """Test full chain integrity validation"""
    blockchain.add_block({'data': 'valid_block_1'})
    blockchain.add_block({'data': 'valid_block_2'})
    
    assert blockchain.is_chain_valid() is True

def test_tamper_detection(blockchain):
    """Test that tampering with data invalidates the chain"""
    blockchain.add_block({'data': 'secure_data'})
    
    # Tamper with the internal chain memory
    blockchain.chain[1].data = {'data': 'TAMPERED_DATA'}
    
    assert blockchain.is_chain_valid() is False
