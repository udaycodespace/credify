"""
Tests for Zero-Knowledge Proof system
"""
import pytest


def test_generate_range_proof(zkp_manager):
    """Test generating a range proof"""
    proof = zkp_manager.generate_range_proof(
        credential_id='TEST123',
        field_name='gpa',
        actual_value=8.5,
        min_threshold=7.5,
        max_threshold=10.0
    )
    
    assert proof['success'] is True
    assert proof['proof']['type'] == 'RangeProof'


def test_verify_range_proof(zkp_manager):
    """Test verifying a range proof"""
    # Generate proof
    proof_result = zkp_manager.generate_range_proof(
        credential_id='TEST123',
        field_name='gpa',
        actual_value=8.5,
        min_threshold=7.5,
        max_threshold=10.0
    )
    
    # Verify proof
    verify_result = zkp_manager.verify_range_proof(proof_result['proof'])
    
    assert verify_result['valid'] is True


def test_generate_membership_proof(zkp_manager):
    """Test generating a membership proof"""
    courses = ['Data Structures', 'Algorithms', 'DBMS']
    
    proof = zkp_manager.generate_membership_proof(
        credential_id='TEST123',
        field_name='courses',
        full_set=courses,
        claimed_member='Algorithms'
    )
    
    assert proof['success'] is True
    assert proof['proof']['type'] == 'MembershipProof'


def test_verify_membership_proof(zkp_manager):
    """Test verifying a membership proof"""
    courses = ['Data Structures', 'Algorithms', 'DBMS']
    
    # Generate proof
    proof_result = zkp_manager.generate_membership_proof(
        credential_id='TEST123',
        field_name='courses',
        full_set=courses,
        claimed_member='Algorithms'
    )
    
    # Verify proof
    verify_result = zkp_manager.verify_membership_proof(proof_result['proof'])
    
    assert verify_result['valid'] is True
