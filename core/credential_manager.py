import json
import uuid
from datetime import datetime
import logging
from pathlib import Path
import hashlib

# FIXED: Import DATA_DIR from core package
from . import DATA_DIR, PROJECT_ROOT

logging.basicConfig(level=logging.INFO)


class CredentialManager:
    """Manages verifiable credentials using blockchain and IPFS with complete versioning support"""
    
    def __init__(self, blockchain, crypto_manager, ipfs_client):
        self.blockchain = blockchain
        self.crypto_manager = crypto_manager
        self.ipfs_client = ipfs_client
        self.credentials_file = DATA_DIR / "credentials_registry.json"
        self.credentials_registry = self.load_credentials_registry()
    
    def _calculate_version_for_student(self, student_id):
        """
        CRITICAL FIX: Calculate version per student ID, not globally
        
        Args:
            student_id: Student roll number
            
        Returns:
            Next version number for THIS student (v1, v2, v3...)
        """
        existing_versions = []
        for cred_id, registry_entry in self.credentials_registry.items():
            if registry_entry.get('student_id') == student_id:
                existing_versions.append(registry_entry.get('version', 1))
        
        if not existing_versions:
            return 1  # First credential for this student
        
        return max(existing_versions) + 1
    
    def _get_latest_active_credential(self, student_id):
        """
        Get the latest ACTIVE credential for a student
        
        Returns:
            credential_id or None
        """
        active_credentials = []
        for cred_id, registry_entry in self.credentials_registry.items():
            if (registry_entry.get('student_id') == student_id and 
                registry_entry.get('status') == 'active'):
                active_credentials.append(registry_entry)
        
        if not active_credentials:
            return None
        
        # Return the one with highest version
        latest = max(active_credentials, key=lambda x: x.get('version', 1))
        return latest['credential_id']
    
    def _auto_revoke_previous_active(self, student_id, new_credential_id):
        """
        CRITICAL FIX: Auto-revoke all ACTIVE credentials before issuing new one
        Only ONE ACTIVE credential allowed per student at any time
        
        Args:
            student_id: Student whose old credentials should be superseded
            new_credential_id: The new credential replacing them
        """
        superseded_count = 0
        for cred_id, registry_entry in self.credentials_registry.items():
            if (registry_entry.get('student_id') == student_id and 
                registry_entry.get('status') == 'active' and 
                cred_id != new_credential_id):
                
                # Mark as superseded
                registry_entry['status'] = 'superseded'
                registry_entry['superseded_by'] = new_credential_id
                registry_entry['superseded_date'] = datetime.utcnow().isoformat()
                superseded_count += 1
                
                logging.info(f"Auto-superseded credential {cred_id} (v{registry_entry.get('version')})")
        
        return superseded_count
    
    def _generate_credential_hash(self, credential_data):
        """Generate SHA-256 hash of credential (for integrity)"""
        canonical_json = json.dumps(credential_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode()).hexdigest()
    
    def _generate_issuer_id(self):
        """Generate DID-style issuer identifier"""
        return "did:edu:gprec"
    
    def _generate_holder_id(self, student_id):
        """Generate DID-style holder identifier"""
        return f"did:edu:gprec:student:{student_id}"
    
    def issue_credential(self, transcript_data, replaces=None):
        """
        Issue a new verifiable credential with COMPLETE metadata
        
        FIXED BEHAVIOR:
        - Version calculated per student ID
        - Auto-revokes previous ACTIVE credentials
        - Includes 15+ mandatory metadata fields
        
        Args:
            transcript_data: Student academic data
            replaces: (OPTIONAL) credential_id of previous version
        """
        try:
            student_id = transcript_data['student_id']
            
            # CRITICAL FIX 1: Calculate version per student ID
            version = self._calculate_version_for_student(student_id)
            
            # Generate unique credential ID
            credential_id = str(uuid.uuid4())
            
            # Get previous credential ID for chain linking
            previous_credential_id = self._get_latest_active_credential(student_id)
            
            # Current timestamp (UTC)
            issued_at = datetime.utcnow().isoformat() + 'Z'
            
            # Create verifiable credential structure (W3C compliant)
            credential = {
                '@context': [
                    'https://www.w3.org/2018/credentials/v1',
                    'https://example.org/academic/v1'
                ],
                'id': f'urn:uuid:{credential_id}',
                'type': ['VerifiableCredential', 'AcademicTranscript'],
                'version': version,
                'replaces': previous_credential_id,
                'issuer': {
                    'id': self._generate_issuer_id(),
                    'name': 'G. Pulla Reddy Engineering College',
                    'department': 'Computer Science Engineering'
                },
                'issuanceDate': issued_at,
                'credentialSubject': {
                    'id': self._generate_holder_id(student_id),
                    'name': transcript_data['student_name'],
                    'studentId': transcript_data['student_id'],
                    'degree': transcript_data['degree'],
                    'university': transcript_data['university'],
                    'gpa': transcript_data['gpa'],
                    'graduationYear': transcript_data['graduation_year'],
                    'courses': transcript_data.get('courses', []),
                    'issueDate': transcript_data['issue_date'],
                    'semester': transcript_data.get('semester'),
                    'year': transcript_data.get('year'),
                    'className': transcript_data.get('class_name'),
                    'section': transcript_data.get('section'),
                    'backlogCount': transcript_data.get('backlog_count', 0),
                    'backlogs': transcript_data.get('backlogs', []),
                    'conduct': transcript_data.get('conduct')
                }
            }
            
            # METADATA FIX 1: Generate credential hash (before signing)
            credential_hash = self._generate_credential_hash(credential)
            
            # METADATA FIX 2: Create digital signature
            signature = self.crypto_manager.sign_data(credential)
            if not signature:
                return {'success': False, 'error': 'Failed to create digital signature'}
            
            # Add proof to credential
            credential['proof'] = {
                'type': 'RsaSignature2018',
                'created': issued_at,
                'verificationMethod': f'{self._generate_issuer_id()}#keys-1',
                'signatureValue': signature
            }
            
            # Store full credential on IPFS
            ipfs_cid = self.ipfs_client.add_json(credential)
            if not ipfs_cid:
                return {'success': False, 'error': 'Failed to store credential on IPFS'}
            
            # METADATA FIX 3: Create blockchain record with COMPLETE metadata
            blockchain_data = {
                'credential_id': credential_id,
                'ipfs_cid': ipfs_cid,
                'credential_hash': credential_hash,
                'signature': signature,
                'issuer': credential['issuer']['name'],
                'issuer_id': self._generate_issuer_id(),
                'holder_id': self._generate_holder_id(student_id),
                'subject_id': student_id,
                'subject_name': transcript_data['student_name'],
                'issue_date': issued_at,
                'version': version,
                'previous_credential_id': previous_credential_id,
                'type': 'credential_issuance',
                'schema_type': 'AcademicTranscriptCredential',
                'schema_version': '1.0'
            }
            
            # Add to blockchain
            block = self.blockchain.add_block(blockchain_data)
            block_number = block.index
            transaction_hash = block.hash
            
            # CRITICAL FIX 2: Auto-revoke previous ACTIVE credentials
            superseded_count = self._auto_revoke_previous_active(student_id, credential_id)
            
            # METADATA FIX 4: Update local registry with COMPLETE 15+ fields
            self.credentials_registry[credential_id] = {
                # Identity fields
                'credential_id': credential_id,
                'issuer_id': self._generate_issuer_id(),
                'holder_id': self._generate_holder_id(student_id),
                
                # Cryptographic fields
                'credential_hash': credential_hash,
                'signature': signature,
                'issuer_signature': signature,
                'issuer_public_key_id': 'rsa-key-2048',
                
                # Storage fields
                'ipfs_cid': ipfs_cid,
                
                # Blockchain fields
                'tx_hash': transaction_hash,
                'block_hash': block.hash,
                'block_number': block_number,
                'network_id': 'local-dev-chain',
                
                # Versioning & lifecycle fields
                'version': version,
                'status': 'active',
                'previous_credential_id': previous_credential_id,
                'replaces': previous_credential_id,
                'superseded_by': None,
                
                # Timestamps
                'issued_at': issued_at,
                'issuance_date': issued_at,
                'created_at': issued_at,
                
                # Schema fields
                'credential_schema': 'AcademicTranscriptCredential',
                'credential_type': 'AcademicTranscript',
                'schema_version': '1.0',
                
                # Student data
                'student_name': transcript_data['student_name'],
                'student_id': student_id,
                'degree': transcript_data['degree'],
                'gpa': transcript_data['gpa'],
                'issue_date': issued_at,
                
                # Extended academic fields
                'semester': transcript_data.get('semester'),
                'year': transcript_data.get('year'),
                'class_name': transcript_data.get('class_name'),
                'section': transcript_data.get('section'),
                'backlog_count': transcript_data.get('backlog_count', 0),
                'backlogs': transcript_data.get('backlogs', []),
                'conduct': transcript_data.get('conduct'),
                
                # Revocation fields (empty for new credentials)
                'revoked_at': None,
                'revocation_reason': None,
                'revocation_category': None
            }
            
            self.save_credentials_registry()
            
            logging.info(f"✅ Credential v{version} issued for student {student_id}")
            logging.info(f"   Superseded {superseded_count} previous credential(s)")
            
            return {
                'success': True,
                'credential_id': credential_id,
                'version': version,
                'ipfs_cid': ipfs_cid,
                'block_hash': block.hash,
                'block_number': block_number,
                'transaction_id': transaction_hash,
                'tx_hash': transaction_hash,
                'credential_hash': credential_hash,
                'superseded_count': superseded_count,
                'student_id': student_id,
                'message': f'Credential v{version} issued successfully (superseded {superseded_count} old version(s))'
            }
            
        except Exception as e:
            logging.error(f"❌ Error issuing credential: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_new_version(self, old_credential_id, updated_data, reason):
        """
        Create a new version of a credential (for corrections/updates)
        
        Args:
            old_credential_id: The credential being replaced
            updated_data: New/corrected transcript data
            reason: Reason for reissue
        """
        try:
            old_cred_id = self._normalize_credential_id(old_credential_id)
            
            if old_cred_id not in self.credentials_registry:
                return {'success': False, 'error': 'Original credential not found'}
            
            old_credential = self.credentials_registry[old_cred_id]
            
            if old_credential['status'] == 'superseded':
                return {'success': False, 'error': 'Cannot create new version of superseded credential'}
            
            result = self.issue_credential(updated_data, replaces=old_cred_id)
            
            if result['success']:
                version_record = {
                    'type': 'credential_versioning',
                    'old_credential_id': old_cred_id,
                    'new_credential_id': result['credential_id'],
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'old_version': old_credential.get('version', 1),
                    'new_version': result['version']
                }
                self.blockchain.add_block(version_record)
                
                logging.info(f"✅ New version created: v{result['version']} - Reason: {reason}")
                
                result['reason'] = reason
                result['old_version'] = old_credential.get('version', 1)
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error creating new version: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_credential(self, credential_id):
        """Verify the authenticity of a credential"""
        try:
            credential_id = self._normalize_credential_id(credential_id)
            
            if credential_id not in self.credentials_registry:
                return {'valid': False, 'error': 'Credential not found in registry'}
            
            registry_entry = self.credentials_registry[credential_id]
            
            status = registry_entry.get('status', 'unknown')
            if status == 'revoked':
                return {
                    'valid': False, 
                    'error': 'Credential has been revoked',
                    'status': 'revoked',
                    'revocation_reason': registry_entry.get('revocation_reason'),
                    'revocation_date': registry_entry.get('revoked_at')
                }
            
            if status == 'superseded':
                return {
                    'valid': False,
                    'error': 'Credential has been superseded by a newer version',
                    'status': 'superseded',
                    'superseded_by': registry_entry.get('superseded_by'),
                    'superseded_date': registry_entry.get('superseded_date')
                }
            
            credential = self.ipfs_client.get_json(registry_entry['ipfs_cid'])
            if not credential:
                return {'valid': False, 'error': 'Could not retrieve credential from IPFS'}
            
            block = self.blockchain.find_credential_block(credential_id)
            if not block:
                return {'valid': False, 'error': 'Credential block not found in blockchain'}
            
            if not self.blockchain.is_chain_valid():
                return {'valid': False, 'error': 'Blockchain integrity compromised'}
            
            current_hash = self._generate_credential_hash(credential)
            if current_hash != registry_entry.get('credential_hash'):
                return {'valid': False, 'error': 'Credential has been tampered with'}
            
            signature = credential.get('proof', {}).get('signatureValue')
            if not signature:
                return {'valid': False, 'error': 'No digital signature found'}
            
            credential_without_proof = credential.copy()
            del credential_without_proof['proof']
            
            if not self.crypto_manager.verify_signature(credential_without_proof, signature):
                return {'valid': False, 'error': 'Digital signature verification failed'}
            
            logging.info(f"✅ Credential verified: {credential_id} (v{registry_entry.get('version')})")
            
            return {
                'valid': True,
                'credential': credential,
                'status': 'active',
                'version': registry_entry.get('version', 1),
                'block_number': registry_entry.get('block_number'),
                'tx_hash': registry_entry.get('tx_hash'),
                'verification_details': {
                    'blockchain_verified': True,
                    'signature_verified': True,
                    'hash_verified': True,
                    'verification_date': datetime.utcnow().isoformat() + 'Z'
                }
            }
            
        except Exception as e:
            logging.error(f"❌ Error verifying credential: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def selective_disclosure(self, credential_id, selected_fields):
        """Create a selective disclosure of credential fields"""
        try:
            credential_id = self._normalize_credential_id(credential_id)
            
            verification_result = self.verify_credential(credential_id)
            if not verification_result['valid']:
                return {'success': False, 'error': verification_result['error']}
            
            credential = verification_result['credential']
            subject_data = credential['credentialSubject']
            
            disclosed_data = {}
            for field in selected_fields:
                if field in subject_data:
                    disclosed_data[field] = subject_data[field]
                else:
                    return {'success': False, 'error': f'Field "{field}" not found in credential'}
            
            proof = self.crypto_manager.create_proof_for_fields(subject_data, disclosed_data)
            
            disclosure_doc = {
                '@context': [
                    'https://www.w3.org/2018/credentials/v1',
                    'https://example.org/academic/v1'
                ],
                'type': 'SelectiveDisclosure',
                'originalCredentialId': credential_id,
                'disclosedFields': disclosed_data,
                'proof': proof,
                'issuer': credential['issuer'],
                'issuanceDate': credential['issuanceDate'],
                'disclosureDate': datetime.utcnow().isoformat() + 'Z'
            }
            
            logging.info(f"✅ Selective disclosure created for credential: {credential_id}")
            
            return {
                'success': True,
                'disclosure': disclosure_doc,
                'message': f'Selective disclosure created with {len(selected_fields)} fields'
            }
            
        except Exception as e:
            logging.error(f"❌ Error creating selective disclosure: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_all_credentials(self):
        """Get all credentials in the registry"""
        credentials = []
        for cred_id, registry_entry in self.credentials_registry.items():
            full_credential = self.ipfs_client.get_json(registry_entry['ipfs_cid'])
            if full_credential:
                registry_entry['full_credential'] = full_credential['credentialSubject']
            credentials.append(registry_entry)
        return credentials
    
    def get_credential(self, credential_id):
        """Get a specific credential by ID"""
        credential_id = self._normalize_credential_id(credential_id)
        if credential_id in self.credentials_registry:
            registry_entry = self.credentials_registry[credential_id]
            full_credential = self.ipfs_client.get_json(registry_entry['ipfs_cid'])
            if full_credential:
                registry_entry['full_credential'] = full_credential
            return registry_entry
        return None
    
    def get_credential_history(self, student_id):
        """Get complete credential history for a student (all versions)"""
        try:
            history = []
            
            for cred_id, registry_entry in self.credentials_registry.items():
                if registry_entry.get('student_id') == student_id:
                    history.append(registry_entry)
            
            history.sort(key=lambda x: x.get('version', 1))
            
            logging.info(f"✅ Found {len(history)} credential version(s) for student {student_id}")
            
            return {
                'success': True,
                'student_id': student_id,
                'total_versions': len(history),
                'credentials': history
            }
            
        except Exception as e:
            logging.error(f"❌ Error getting credential history: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def revoke_credential(self, credential_id, reason="", reason_category="other"):
        """Revoke a credential (mark as revoked)"""
        try:
            credential_id = self._normalize_credential_id(credential_id)
            if credential_id not in self.credentials_registry:
                return {'success': False, 'error': 'Credential not found'}
            
            current_status = self.credentials_registry[credential_id].get('status')
            
            if current_status == 'superseded':
                return {'success': False, 'error': 'Cannot revoke superseded credential. Revoke the active version instead.'}
            
            if current_status == 'revoked':
                return {'success': False, 'error': 'Credential is already revoked'}
            
            revoked_at = datetime.utcnow().isoformat() + 'Z'
            
            self.credentials_registry[credential_id]['status'] = 'revoked'
            self.credentials_registry[credential_id]['revoked_at'] = revoked_at
            self.credentials_registry[credential_id]['revocation_reason'] = reason
            self.credentials_registry[credential_id]['revocation_category'] = reason_category
            
            revocation_data = {
                'credential_id': credential_id,
                'type': 'credential_revocation',
                'reason': reason,
                'reason_category': reason_category,
                'revoked_at': revoked_at,
                'revoked_by': 'issuer'
            }
            
            block = self.blockchain.add_block(revocation_data)
            
            self.save_credentials_registry()
            
            logging.info(f"✅ Credential revoked: {credential_id} - Reason: {reason_category}")
            
            return {
                'success': True,
                'message': 'Credential revoked successfully',
                'revocation_block': block.hash,
                'revoked_at': revoked_at
            }
            
        except Exception as e:
            logging.error(f"❌ Error revoking credential: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load_credentials_registry(self):
        """Load credentials registry from data/ folder"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    registry = json.load(f)
                    logging.info(f"✅ Credentials registry loaded: {len(registry)} entries")
                    return registry
            else:
                logging.info(f"⚠️  No existing credentials registry found")
                return {}
        except Exception as e:
            logging.error(f"❌ Error loading credentials registry: {str(e)}")
            return {}
    
    def save_credentials_registry(self):
        """Save credentials registry to data/ folder"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(self.credentials_file, 'w') as f:
                json.dump(self.credentials_registry, f, indent=2)
            logging.info(f"✅ Credentials registry saved: {len(self.credentials_registry)} entries")
        except Exception as e:
            logging.error(f"❌ Error saving credentials registry: {str(e)}")
    
    def _normalize_credential_id(self, credential_id):
        """Normalize credential ID (handle URN formats)"""
        if not credential_id:
            return credential_id
        try:
            cid = str(credential_id)
            if cid.startswith('urn:uuid:'):
                return cid.split('urn:uuid:')[-1]
            if cid.startswith('urn:'):
                return cid.split(':')[-1]
            return cid
        except Exception:
            return credential_id
