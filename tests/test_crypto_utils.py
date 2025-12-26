"""
Test cases for Cryptographic utilities
"""

import pytest
from core.crypto_utils import CryptoUtils


class TestCryptoUtils:
    
    def test_sha256_hash(self):
        """Test SHA-256 hashing"""
        data = "test data"
        hash1 = CryptoUtils.sha256_hash(data)
        hash2 = CryptoUtils.sha256_hash(data)
        
        assert hash1 == hash2  # Same input, same hash
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_different_inputs_different_hashes(self):
        """Test different inputs produce different hashes"""
        hash1 = CryptoUtils.sha256_hash("data1")
        hash2 = CryptoUtils.sha256_hash("data2")
        
        assert hash1 != hash2
    
    def test_generate_key_pair(self):
        """Test RSA key pair generation"""
        private_key, public_key = CryptoUtils.generate_key_pair()
        
        assert private_key is not None
        assert public_key is not None
    
    def test_sign_and_verify(self):
        """Test digital signature creation and verification"""
        private_key, public_key = CryptoUtils.generate_key_pair()
        
        data = "Test message"
        signature = CryptoUtils.sign_data(data, private_key)
        
        # Verify signature
        is_valid = CryptoUtils.verify_signature(data, signature, public_key)
        
        assert is_valid == True
    
    def test_verify_tampered_data(self):
        """Test signature verification fails for tampered data"""
        private_key, public_key = CryptoUtils.generate_key_pair()
        
        original_data = "Original message"
        signature = CryptoUtils.sign_data(original_data, private_key)
        
        # Verify with tampered data
        tampered_data = "Tampered message"
        is_valid = CryptoUtils.verify_signature(tampered_data, signature, public_key)
        
        assert is_valid == False
    
    def test_merkle_root_calculation(self):
        """Test Merkle tree root calculation"""
        items = ['item1', 'item2', 'item3', 'item4']
        root = CryptoUtils.calculate_merkle_root(items)
        
        assert root is not None
        assert len(root) == 64  # SHA-256 hex length
    
    def test_merkle_proof_generation(self):
        """Test Merkle proof generation"""
        items = ['course1', 'course2', 'course3', 'course4']
        item = 'course2'
        
        proof = CryptoUtils.generate_merkle_proof(items, item)
        
        assert proof is not None
        assert isinstance(proof, list)
    
    def test_merkle_proof_verification(self):
        """Test Merkle proof verification"""
        items = ['course1', 'course2', 'course3', 'course4']
        item = 'course2'
        
        root = CryptoUtils.calculate_merkle_root(items)
        proof = CryptoUtils.generate_merkle_proof(items, item)
        
        is_valid = CryptoUtils.verify_merkle_proof(item, proof, root)
        
        assert is_valid == True
