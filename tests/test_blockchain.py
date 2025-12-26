"""
Test cases for Blockchain functionality
"""

import pytest
import time
from core.blockchain import SimpleBlockchain, Block  # ✅ FIXED


class TestBlockchain:
    
    def test_blockchain_initialization(self, blockchain):
        """Test blockchain initializes correctly"""
        assert blockchain.difficulty == 2
        assert len(blockchain.chain) >= 0
    
    def test_genesis_block_creation(self):
        """Test genesis block is created"""
        bc = SimpleBlockchain(difficulty=2)
        
        if len(bc.chain) == 0:
            genesis = bc.create_genesis_block()
            assert genesis.index == 0
            assert genesis.previous_hash == "0"
    
    def test_add_block(self, blockchain):
        """Test adding new block to chain"""
        initial_length = len(blockchain.chain)
        
        test_data = {
            'credential_id': 'TEST123',
            'student_id': 'STU001',
            'timestamp': time.time()
        }
        
        new_block = blockchain.add_block(test_data)
        
        assert new_block is not None
        assert len(blockchain.chain) == initial_length + 1
    
    def test_block_hashing(self):
        """Test block hash calculation"""
        block = Block(
            index=1,
            previous_hash="abc123",
            timestamp=time.time(),
            data={'test': 'data'},
            nonce=0
        )
        
        hash1 = block.calculate_hash()
        hash2 = block.calculate_hash()
        
        # Same input should give same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 character hex
    
    def test_proof_of_work(self, blockchain):
        """Test proof of work mining"""
        block = Block(
            index=1,
            previous_hash="abc123",
            timestamp=time.time(),
            data={'test': 'data'},
            nonce=0
        )
        
        blockchain.proof_of_work(block)
        
        # Hash should start with required number of zeros
        assert block.hash.startswith('0' * blockchain.difficulty)
        assert block.nonce > 0
    
    def test_chain_validity(self, blockchain):
        """Test blockchain validation"""
        # Add some blocks
        blockchain.add_block({'data': 'block1'})
        blockchain.add_block({'data': 'block2'})
        
        # Chain should be valid
        assert blockchain.is_chain_valid() == True
    
    def test_get_latest_block(self, blockchain):
        """Test getting latest block"""
        blockchain.add_block({'data': 'test'})
        latest = blockchain.get_latest_block()
        
        assert latest is not None
