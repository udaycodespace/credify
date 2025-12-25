import pytest
from app import app, db
from core.crypto_utils import CryptoManager

def test_crypto_key_generation():
    """Test cryptographic keys are generated securely"""
    crypto = CryptoManager()
    assert crypto.private_key is not None
    assert crypto.public_key is not None

def test_signature_verification():
    """Test signature creation and verification"""
    crypto = CryptoManager()
    test_data = {"name": "John", "id": "123"}
    
    signature = crypto.sign_data(test_data)
    assert signature is not None
    
    # Verify signature
    is_valid = crypto.verify_signature(test_data, signature)
    assert is_valid is True
    
    # Tamper test
    tampered_data = {"name": "Jane", "id": "123"}
    is_valid = crypto.verify_signature(tampered_data, signature)
    assert is_valid is False

def test_blockchain_integrity():
    """Test blockchain tamper detection"""
    from core.blockchain import SimpleBlockchain
    blockchain = SimpleBlockchain()
    
    # Add blocks
    blockchain.add_block({"test": "data1"})
    blockchain.add_block({"test": "data2"})
    
    assert blockchain.is_chain_valid() is True
    
    # Tamper with block
    blockchain.chain[1].data = {"test": "tampered"}
    assert blockchain.is_chain_valid() is False
