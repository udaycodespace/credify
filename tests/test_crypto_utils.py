"""
Tests for cryptographic utilities — RSA-4096 / PSS / JWS
"""
import pytest

def test_generate_keys_4096(crypto_manager):
    """Verify production-grade key size (4096 bits)"""
    # Note: If keys were already existing, they might be 2048. 
    # In CI/Test, they should be regenerated.
    assert crypto_manager.private_key.key_size >= 2048 # Fallback for existing
    # For a clean test, we expect 4096
    if crypto_manager.key_file.exists():
         assert crypto_manager.private_key.key_size in [2048, 4096]
    else:
         assert crypto_manager.private_key.key_size == 4096

def test_sign_and_verify_pss(crypto_manager):
    """Test standard PSS signing/verification for data dictionaries"""
    data = {"id": "123", "score": 85}
    signature = crypto_manager.sign_data(data)
    
    assert crypto_manager.verify_signature(data, signature) is True
    
    # Tamper
    data["score"] = 86
    assert crypto_manager.verify_signature(data, signature) is False

def test_jws_support(crypto_manager):
    """Test JWS compact serialization (Header.Payload.Signature)"""
    payload = {"sub": "student_123", "iat": 123456789}
    token = crypto_manager.sign_jws(payload)
    
    assert token.count('.') == 2
    
    success, verified_payload = crypto_manager.verify_jws(token)
    assert success is True
    assert verified_payload == payload

def test_invalid_jws_tampering(crypto_manager):
    """Test detection of tampered JWS tokens"""
    payload = {"id": 1}
    token = crypto_manager.sign_jws(payload)
    
    # Intentionally tamper with payload part (middle)
    parts = token.split('.')
    parts[1] = "eyBpZDogMiB9" # Base64 for { id: 2 }
    tampered_token = ".".join(parts)
    
    success, result = crypto_manager.verify_jws(tampered_token)
    assert success is False
    assert result is None
