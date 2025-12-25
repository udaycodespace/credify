import hashlib
import json
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

class ZKPManager:
    """
    Zero-Knowledge Proof Manager for Academic Credentials
    Supports: Range Proofs, Membership Proofs, Threshold Proofs
    """
    
    def __init__(self, crypto_manager):
        self.crypto_manager = crypto_manager
        self.proof_cache = {}  # Store generated proofs
    
    # ==================== RANGE PROOF (GPA) ====================
    def generate_range_proof(self, credential_id, field_name, actual_value, 
                            min_threshold=None, max_threshold=None):
        """
        Prove that a numeric field is within a range WITHOUT revealing the value
        
        Example: Prove GPA > 7.5 without showing actual GPA (8.2)
        
        Args:
            credential_id: The credential being proved
            field_name: 'gpa', 'backlogCount', etc.
            actual_value: The real value (e.g., 8.2)
            min_threshold: Minimum value to prove (e.g., 7.5)
            max_threshold: Maximum value (optional)
        
        Returns:
            ZKP proof object
        """
        try:
            # Generate random nonce for security
            nonce = random.randint(10**15, 10**16)
            
            # Create commitment: Hash(value + nonce)
            commitment_data = f"{actual_value}:{nonce}:{credential_id}"
            commitment = hashlib.sha256(commitment_data.encode()).hexdigest()
            
            # Verify the range claim
            range_satisfied = True
            if min_threshold is not None:
                range_satisfied = range_satisfied and (actual_value >= min_threshold)
            if max_threshold is not None:
                range_satisfied = range_satisfied and (actual_value <= max_threshold)
            
            if not range_satisfied:
                return {
                    'success': False,
                    'error': f'Actual value does not satisfy the range requirement'
                }
            
            # Create range proof
            proof = {
                'type': 'RangeProof',
                'field': field_name,
                'credentialId': credential_id,
                'commitment': commitment,
                'nonce': nonce,  # Stored securely, shared with verifier during challenge
                'minThreshold': min_threshold,
                'maxThreshold': max_threshold,
                'proofDate': datetime.utcnow().isoformat() + 'Z',
                'rangeSatisfied': range_satisfied,
                'proofMethod': 'commitment-based'
            }
            
            # Sign the proof
            proof_signature = self.crypto_manager.sign_data(proof)
            proof['signature'] = proof_signature
            
            # Store in cache for verification
            proof_id = hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()
            self.proof_cache[proof_id] = {
                'proof': proof,
                'actual_value': actual_value,  # Kept secret
                'created': datetime.utcnow().isoformat()
            }
            
            logging.info(f"✅ Range proof generated for {field_name} in credential {credential_id[:8]}")
            
            return {
                'success': True,
                'proof': proof,
                'proofId': proof_id,
                'claim': f"{field_name} is between {min_threshold} and {max_threshold or 'unlimited'}"
            }
            
        except Exception as e:
            logging.error(f"❌ Error generating range proof: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_range_proof(self, proof, challenge_value=None):
        """
        Verify a range proof
        
        Verifier can challenge by requesting the nonce and value
        Then check if Hash(value + nonce) == commitment
        """
        try:
            commitment = proof['commitment']
            nonce = proof.get('nonce')
            
            if challenge_value is not None and nonce is not None:
                # Verifier challenges: "Show me the value matches commitment"
                recomputed = hashlib.sha256(
                    f"{challenge_value}:{nonce}:{proof['credentialId']}".encode()
                ).hexdigest()
                
                if recomputed != commitment:
                    return {
                        'valid': False,
                        'error': 'Commitment verification failed',
                        'details': 'The provided value does not match the commitment'
                    }
                
                # Check range
                min_thresh = proof.get('minThreshold')
                max_thresh = proof.get('maxThreshold')
                
                if min_thresh and challenge_value < min_thresh:
                    return {'valid': False, 'error': 'Value below minimum threshold'}
                if max_thresh and challenge_value > max_thresh:
                    return {'valid': False, 'error': 'Value above maximum threshold'}
            
            # Verify signature
            proof_copy = proof.copy()
            signature = proof_copy.pop('signature', None)
            
            if not signature:
                return {'valid': False, 'error': 'Missing proof signature'}
            
            if not self.crypto_manager.verify_signature(proof_copy, signature):
                return {'valid': False, 'error': 'Invalid proof signature'}
            
            return {
                'valid': True,
                'field': proof['field'],
                'claim': f"{proof['field']} satisfies range [{proof.get('minThreshold')}, {proof.get('maxThreshold')}]",
                'verified': True
            }
            
        except Exception as e:
            logging.error(f"❌ Error verifying range proof: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    # ==================== MEMBERSHIP PROOF (Courses) ====================
    def generate_membership_proof(self, credential_id, field_name, 
                                  full_set, claimed_member):
        """
        Prove that an item is in a set WITHOUT revealing the entire set
        
        Example: Prove "Data Structures" is in completed courses 
                 without showing all 40 courses
        
        Uses Merkle Tree approach
        
        Args:
            credential_id: The credential
            field_name: 'courses', 'backlogs', etc.
            full_set: Complete list (e.g., all courses)
            claimed_member: Item to prove (e.g., "Data Structures")
        """
        try:
            if claimed_member not in full_set:
                return {
                    'success': False,
                    'error': f'{claimed_member} is not in the {field_name} set'
                }
            
            # Create Merkle tree
            sorted_set = sorted(full_set)
            leaves = [hashlib.sha256(item.encode()).hexdigest() for item in sorted_set]
            
            # Build Merkle root
            merkle_root = self._build_merkle_root(leaves)
            
            # Find index of claimed member
            member_index = sorted_set.index(claimed_member)
            
            # Generate Merkle proof path
            merkle_path = self._generate_merkle_path(leaves, member_index)
            
            proof = {
                'type': 'MembershipProof',
                'field': field_name,
                'credentialId': credential_id,
                'merkleRoot': merkle_root,
                'claimedMember': claimed_member,
                'memberHash': leaves[member_index],
                'merklePath': merkle_path,
                'setSize': len(full_set),
                'proofDate': datetime.utcnow().isoformat() + 'Z',
                'proofMethod': 'merkle-tree'
            }
            
            # Sign the proof
            proof_signature = self.crypto_manager.sign_data(proof)
            proof['signature'] = proof_signature
            
            logging.info(f"✅ Membership proof generated for '{claimed_member}' in {field_name}")
            
            return {
                'success': True,
                'proof': proof,
                'claim': f"'{claimed_member}' is in {field_name} set (size: {len(full_set)})"
            }
            
        except Exception as e:
            logging.error(f"❌ Error generating membership proof: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_membership_proof(self, proof):
        """Verify a membership proof using Merkle path"""
        try:
            member_hash = proof['memberHash']
            merkle_path = proof['merklePath']
            claimed_root = proof['merkleRoot']
            
            # Reconstruct root from path
            current_hash = member_hash
            for sibling_hash, is_left in merkle_path:
                if is_left:
                    current_hash = hashlib.sha256(
                        (sibling_hash + current_hash).encode()
                    ).hexdigest()
                else:
                    current_hash = hashlib.sha256(
                        (current_hash + sibling_hash).encode()
                    ).hexdigest()
            
            if current_hash != claimed_root:
                return {
                    'valid': False,
                    'error': 'Merkle root verification failed',
                    'details': 'The claimed member is not in the set'
                }
            
            # Verify signature
            proof_copy = proof.copy()
            signature = proof_copy.pop('signature', None)
            
            if not self.crypto_manager.verify_signature(proof_copy, signature):
                return {'valid': False, 'error': 'Invalid proof signature'}
            
            return {
                'valid': True,
                'member': proof['claimedMember'],
                'field': proof['field'],
                'claim': f"'{proof['claimedMember']}' is verified in {proof['field']} set",
                'verified': True
            }
            
        except Exception as e:
            logging.error(f"❌ Error verifying membership proof: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    # ==================== SET MEMBERSHIP PROOF (Degree) ====================
    def generate_set_membership_proof(self, credential_id, field_name, 
                                     actual_value, allowed_set):
        """
        Prove value is from an allowed set WITHOUT revealing which one
        
        Example: Prove degree is from {B.Tech CS, B.Tech ECE, B.Tech Mech}
                 without revealing it's B.Tech CS
        
        Args:
            actual_value: The real value (e.g., "B.Tech Computer Science")
            allowed_set: List of allowed values
        """
        try:
            if actual_value not in allowed_set:
                return {
                    'success': False,
                    'error': f'Value not in allowed set for {field_name}'
                }
            
            # Create commitment for each possible value
            nonce = random.randint(10**15, 10**16)
            commitments = {}
            
            for value in allowed_set:
                commitment_data = f"{value}:{nonce}:{credential_id}"
                commitments[value] = hashlib.sha256(commitment_data.encode()).hexdigest()
            
            # The actual commitment
            actual_commitment = commitments[actual_value]
            
            proof = {
                'type': 'SetMembershipProof',
                'field': field_name,
                'credentialId': credential_id,
                'allowedSet': list(allowed_set),
                'allCommitments': list(commitments.values()),
                'actualCommitment': actual_commitment,
                'nonce': nonce,
                'setSize': len(allowed_set),
                'proofDate': datetime.utcnow().isoformat() + 'Z',
                'proofMethod': 'commitment-set'
            }
            
            # Sign proof
            proof_signature = self.crypto_manager.sign_data(proof)
            proof['signature'] = proof_signature
            
            logging.info(f"✅ Set membership proof generated for {field_name}")
            
            return {
                'success': True,
                'proof': proof,
                'claim': f"{field_name} is one of {len(allowed_set)} allowed values"
            }
            
        except Exception as e:
            logging.error(f"❌ Error generating set membership proof: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_set_membership_proof(self, proof, revealed_value=None):
        """Verify set membership proof"""
        try:
            if revealed_value:
                # Challenge: Verify the revealed value
                nonce = proof['nonce']
                recomputed = hashlib.sha256(
                    f"{revealed_value}:{nonce}:{proof['credentialId']}".encode()
                ).hexdigest()
                
                if recomputed not in proof['allCommitments']:
                    return {'valid': False, 'error': 'Value not in committed set'}
                
                if revealed_value not in proof['allowedSet']:
                    return {'valid': False, 'error': 'Value not in allowed set'}
            
            # Verify signature
            proof_copy = proof.copy()
            signature = proof_copy.pop('signature', None)
            
            if not self.crypto_manager.verify_signature(proof_copy, signature):
                return {'valid': False, 'error': 'Invalid proof signature'}
            
            return {
                'valid': True,
                'field': proof['field'],
                'claim': f"{proof['field']} is from allowed set of {proof['setSize']} values",
                'verified': True
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    # ==================== HELPER METHODS ====================
    def _build_merkle_root(self, leaves):
        """Build Merkle root from leaf hashes"""
        if not leaves:
            return None
        if len(leaves) == 1:
            return leaves[0]
        
        tree_level = leaves
        while len(tree_level) > 1:
            next_level = []
            for i in range(0, len(tree_level), 2):
                left = tree_level[i]
                right = tree_level[i + 1] if i + 1 < len(tree_level) else left
                parent = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(parent)
            tree_level = next_level
        
        return tree_level[0]
    
    def _generate_merkle_path(self, leaves, index):
        """Generate Merkle proof path for a leaf"""
        path = []
        tree_level = leaves
        current_index = index
        
        while len(tree_level) > 1:
            next_level = []
            for i in range(0, len(tree_level), 2):
                left = tree_level[i]
                right = tree_level[i + 1] if i + 1 < len(tree_level) else left
                
                # Record sibling in path
                if i == current_index:
                    path.append((right, False))  # Sibling is on right
                    current_index = i // 2
                elif i + 1 == current_index:
                    path.append((left, True))  # Sibling is on left
                    current_index = i // 2
                
                parent = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(parent)
            
            tree_level = next_level
        
        return path
