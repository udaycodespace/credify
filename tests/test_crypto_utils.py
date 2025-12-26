"""
Tests for cryptographic utilities
"""
import pytest
from core.crypto_utils import CryptoManager


def test_generate_keys(crypto_manager):
    """Test RSA key generation"""
    # ✅ FIXED: generate_keys() doesn't return tuple, just generates keys
    crypto_manager.generate_keys()
    
    assert crypto_manager.private_key is not None
    assert crypto_manager.public_key is not None


def test_sign_and_verify(crypto_manager):
    """Test signing and verification"""
    data = "Test credential data"
    signature = crypto_manager.sign_data(data)
    
    assert signature is not None
    assert crypto_manager.verify_signature(data, signature)


def test_verify_invalid_signature(crypto_manager):
    """Test verification with invalid signature"""
    data = "Test data"
    signature = crypto_manager.sign_data(data)
    
    tampered_data = "Tampered data"
    assert not crypto_manager.verify_signature(tampered_data, signature)


def test_hash_data(crypto_manager):
    """Test SHA-256 hashing"""
    data = "Test data"
    hash1 = crypto_manager.hash_data(data)
    hash2 = crypto_manager.hash_data(data)
    
    assert hash1 == hash2
    assert len(hash1) == 64


def test_hash_different_data(crypto_manager):
    """Test that different data produces different hashes"""
    hash1 = crypto_manager.hash_data("Data 1")
    hash2 = crypto_manager.hash_data("Data 2")
    
    assert hash1 != hash2
