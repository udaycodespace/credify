"""
Test cases for Zero-Knowledge Proofs
"""

import pytest
from core.zkp_manager import ZKPManager


class TestZKP:
    
    def test_range_proof_generation(self):
        """Test range proof generation"""
        zkp = ZKPManager()
        
        credential_id = "TEST123"
        field = "gpa"
        actual_value = 8.5
        min_threshold = 7.5
        
        proof = zkp.generate_range_proof(
            credential_id, 
            field, 
            actual_value, 
            min_threshold
        )
        
        assert proof is not None
        assert proof['type'] == 'RangeProof'
        assert proof['field'] == field
        assert proof['minThreshold'] == min_threshold
    
    def test_range_proof_verification_pass(self):
        """Test valid range proof verification"""
        zkp = ZKPManager()
        
        # Generate proof
        proof = zkp.generate_range_proof(
            "TEST123", "gpa", 8.5, 7.5
        )
        
        # Verify proof
        result = zkp.verify_range_proof(proof)
        
        assert result['valid'] == True
    
    def test_range_proof_verification_fail(self):
        """Test invalid range proof verification"""
        zkp = ZKPManager()
        
        # Generate proof
        proof = zkp.generate_range_proof(
            "TEST123", "gpa", 6.5, 7.5  # actual < threshold
        )
        
        # Verify proof
        result = zkp.verify_range_proof(proof)
        
        assert result['valid'] == False
    
    def test_membership_proof_generation(self):
        """Test membership proof generation"""
        zkp = ZKPManager()
        
        courses = ['Math', 'Physics', 'Chemistry', 'Biology']
        claimed_course = 'Physics'
        
        proof = zkp.generate_membership_proof(
            "TEST123",
            "courses",
            courses,
            claimed_course
        )
        
        assert proof is not None
        assert proof['type'] == 'MembershipProof'
        assert proof['claimedMember'] == claimed_course
        assert 'merkleRoot' in proof
        assert 'merkleProof' in proof
    
    def test_membership_proof_verification_pass(self):
        """Test valid membership proof verification"""
        zkp = ZKPManager()
        
        courses = ['Math', 'Physics', 'Chemistry', 'Biology']
        claimed_course = 'Physics'
        
        # Generate proof
        proof = zkp.generate_membership_proof(
            "TEST123", "courses", courses, claimed_course
        )
        
        # Verify proof
        result = zkp.verify_membership_proof(proof)
        
        assert result['valid'] == True
    
    def test_membership_proof_verification_fail(self):
        """Test invalid membership proof verification"""
        zkp = ZKPManager()
        
        courses = ['Math', 'Physics', 'Chemistry']
        claimed_course = 'Biology'  # Not in list
        
        # Generate proof
        proof = zkp.generate_membership_proof(
            "TEST123", "courses", courses, claimed_course
        )
        
        # Verify proof (should fail)
        result = zkp.verify_membership_proof(proof)
        
        assert result['valid'] == False
    
    def test_commitment_generation(self):
        """Test cryptographic commitment generation"""
        zkp = ZKPManager()
        
        value = 8.5
        commitment = zkp.generate_commitment(value)
        
        assert commitment is not None
        assert len(commitment) == 64  # SHA-256
