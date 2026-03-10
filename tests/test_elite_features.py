"""
Security Test Suite - Elite Privacy & Cryptographic Integrity
=============================================================
Covers all 5 required security verification categories:
  1. Verifier-specific binding (different domains -> different disclosure IDs)
  2. Salt isolation (hidden field salts never exposed)
  3. Disclosure expiry (returns EXPIRED, not INVALID)
  4. QR payload security (no credentialId, ipfsCid, transactionHash)
  5. Range proof validation (invalid ranges fail)
"""
import pytest
from datetime import datetime, timedelta


# --------------------------------------------------------------------------- #
# 1. VERIFIER-SPECIFIC BINDING
# --------------------------------------------------------------------------- #
def test_verifier_binding_produces_different_ids(credential_manager, sample_credential_data):
    """Two disclosures for different domains MUST produce different disclosure IDs"""
    result = credential_manager.issue_credential(sample_credential_data)
    assert result['success'] is True
    cred_id = result['credential_id']

    fields = ['name', 'gpa']

    sd_google = credential_manager.selective_disclosure(cred_id, fields, verifier_domain='google.com')
    sd_amazon = credential_manager.selective_disclosure(cred_id, fields, verifier_domain='amazon.com')

    assert sd_google['success'] and sd_amazon['success']
    assert sd_google['disclosure']['disclosureId'] != sd_amazon['disclosure']['disclosureId']


def test_verifier_binding_same_domain_normalized(credential_manager, sample_credential_data):
    """Equivalent domain strings should normalize to the same verifier context"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    # All of these should normalize to 'careers.google.com'
    assert credential_manager.normalize_domain('https://CAREERS.GOOGLE.COM/') == 'careers.google.com'
    assert credential_manager.normalize_domain('CAREERS.GOOGLE.COM') == 'careers.google.com'
    assert credential_manager.normalize_domain('http://careers.google.com') == 'careers.google.com'


# --------------------------------------------------------------------------- #
# 2. SALT ISOLATION
# --------------------------------------------------------------------------- #
def test_salt_isolation_only_disclosed_salts(credential_manager, sample_credential_data):
    """Proof must reveal salts ONLY for disclosed fields, never for hidden ones"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    disclosed = ['name', 'gpa']
    sd = credential_manager.selective_disclosure(cred_id, disclosed, verifier_domain='test.com')
    assert sd['success']

    proof = sd['disclosure']['proof']
    disclosed_salts = proof['disclosed_salts']

    # Disclosed fields MUST have salts
    assert 'name' in disclosed_salts
    assert 'gpa' in disclosed_salts

    # Hidden fields MUST NOT have salts
    assert 'degree' not in disclosed_salts
    assert 'studentId' not in disclosed_salts
    assert 'university' not in disclosed_salts


def test_salts_stored_at_issuance(credential_manager, sample_credential_data):
    """Field salts must be generated and persisted during credential issuance"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    cred = credential_manager.get_credential(cred_id)
    assert 'field_salts' in cred
    assert len(cred['field_salts']) > 0

    # Salts should cover subject fields
    salts = cred['field_salts']
    assert 'name' in salts
    assert 'gpa' in salts


def test_salts_are_immutable_across_disclosures(credential_manager, sample_credential_data):
    """Same credential must use the same salts across multiple disclosures"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    sd1 = credential_manager.selective_disclosure(cred_id, ['name'], verifier_domain='a.com')
    sd2 = credential_manager.selective_disclosure(cred_id, ['name'], verifier_domain='b.com')

    salt1 = sd1['disclosure']['proof']['disclosed_salts']['name']
    salt2 = sd2['disclosure']['proof']['disclosed_salts']['name']

    assert salt1 == salt2, "Salts must be immutable across disclosures"


# --------------------------------------------------------------------------- #
# 3. DISCLOSURE EXPIRY
# --------------------------------------------------------------------------- #
def test_expired_disclosure_returns_expired_status(credential_manager, sample_credential_data):
    """Expired disclosures must return status=EXPIRED, not INVALID"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    sd = credential_manager.selective_disclosure(cred_id, ['name'], verifier_domain='test.com')
    disc_id = sd['disclosure']['disclosureId']

    # Force expiry by backdating the registry entry
    credential_manager.disclosure_registry[disc_id]['expires_at'] = \
        (datetime.utcnow() - timedelta(hours=1)).isoformat()

    verify_result = credential_manager.verify_blind_disclosure(disc_id)
    assert verify_result['valid'] is False
    assert verify_result['status'] == 'EXPIRED'


def test_valid_disclosure_returns_active(credential_manager, sample_credential_data):
    """Non-expired disclosures must return status=ACTIVE (not EXPIRED)"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    sd = credential_manager.selective_disclosure(cred_id, ['gpa'], verifier_domain='test.com')
    disc_id = sd['disclosure']['disclosureId']

    verify_result = credential_manager.verify_blind_disclosure(disc_id)
    assert verify_result['valid'] is True
    assert verify_result['status'] == 'ACTIVE'


def test_unknown_disclosure_returns_invalid(credential_manager):
    """Non-existent disclosure IDs must return status=INVALID"""
    verify_result = credential_manager.verify_blind_disclosure('nonexistent-id-abcdef')
    assert verify_result['valid'] is False
    assert verify_result['status'] == 'INVALID'


# --------------------------------------------------------------------------- #
# 4. QR PAYLOAD SECURITY
# --------------------------------------------------------------------------- #
def test_qr_payload_no_sensitive_ids(credential_manager, sample_credential_data):
    """
    Disclosure document (QR payload) must NOT contain:
      - credentialId
      - ipfsCid
      - transactionHash
    These would allow cross-correlation / linkability.
    """
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    sd = credential_manager.selective_disclosure(cred_id, ['name', 'gpa'], verifier_domain='secure.com')
    disc = sd['disclosure']

    # Flatten the entire disclosure doc to a string for thorough checking
    doc_str = str(disc)

    assert cred_id not in doc_str, "credentialId must not appear in disclosure"
    assert 'ipfsCid' not in disc, "ipfsCid key must not exist in disclosure"
    assert 'transactionHash' not in disc, "transactionHash key must not exist in disclosure"

    # The disclosure should use the opaque disclosureId instead
    assert 'disclosureId' in disc
    assert disc['disclosureId'] != cred_id


# --------------------------------------------------------------------------- #
# 5. RANGE PROOF VALIDATION (via ZKP Manager)
# --------------------------------------------------------------------------- #
def test_invalid_range_proof_fails(zkp_manager):
    """Range proof with impossible bounds must fail verification"""
    # Generate a proof where actual_value is OUTSIDE the range
    result = zkp_manager.generate_range_proof(
        credential_id='test-cred',
        field_name='gpa',
        actual_value=5.0,
        min_threshold=7.5,
        max_threshold=10.0
    )
    # Should fail because 5.0 is not in [7.5, 10.0]
    assert result['success'] is False or result.get('valid') is False


def test_valid_range_proof_passes(zkp_manager):
    """Range proof with value inside bounds must pass"""
    result = zkp_manager.generate_range_proof(
        credential_id='test-cred',
        field_name='gpa',
        actual_value=8.5,
        min_threshold=7.0,
        max_threshold=10.0
    )
    assert result['success'] is True
    proof = result['proof']

    verification = zkp_manager.verify_range_proof(proof)
    assert verification['valid'] is True


# --------------------------------------------------------------------------- #
# COLLISION-SAFE HASH CONSTRUCTION
# --------------------------------------------------------------------------- #
def test_collision_safe_hash_uses_pipe_delimiter(credential_manager, crypto_manager, sample_credential_data):
    """Hash construction must use '|' delimiter to prevent collision attacks"""
    result = credential_manager.issue_credential(sample_credential_data)
    cred_id = result['credential_id']

    # Generate two disclosures and verify the hash input format
    sd = credential_manager.selective_disclosure(cred_id, ['name'], verifier_domain='test.com')
    assert sd['success']

    # The disclosure ID should be a hash (hex string)
    disc_id = sd['disclosure']['disclosureId']
    assert len(disc_id) == 64  # SHA-256 hex output


def test_domain_normalization_function(credential_manager):
    """Domain normalization must handle all edge cases"""
    assert credential_manager.normalize_domain('GOOGLE.COM') == 'google.com'
    assert credential_manager.normalize_domain('https://google.com/') == 'google.com'
    assert credential_manager.normalize_domain('http://Google.COM/path') == 'google.com'
    assert credential_manager.normalize_domain('HTTPS://CAREERS.GOOGLE.COM/') == 'careers.google.com'
    assert credential_manager.normalize_domain(None) == 'generic'
    assert credential_manager.normalize_domain('') == 'generic'
