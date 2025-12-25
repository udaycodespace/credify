import hashlib
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import base64
import os
import logging
from pathlib import Path
from datetime import datetime  # ADD THIS LINE

# FIXED: Import DATA_DIR from core package [web:42]
from . import DATA_DIR, PROJECT_ROOT  # [web:42]

logging.basicConfig(level=logging.INFO)


class CryptoManager:
    """Handles cryptographic operations for verifiable credentials"""
    
    def __init__(self):
        # FIXED: Use DATA_DIR instead of relative path [web:72]
        self.key_file = DATA_DIR / "issuer_keys.pem"
        self.private_key = None
        self.public_key = None
        self.load_or_generate_keys()
    
    def load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        try:
            # FIXED: Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            if self.key_file.exists():
                self.load_keys()
                logging.info(f"Cryptographic keys loaded from {self.key_file}")
            else:
                self.generate_keys()
                logging.info(f"New cryptographic keys generated and saved to {self.key_file}")
        except Exception as e:
            logging.error(f"Error with cryptographic keys: {str(e)}")
            self.generate_keys()
    
    def generate_keys(self):
        """Generate new RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        self.save_keys()
    
    def save_keys(self):
        """Save keys to data/ folder"""
        try:
            # FIXED: Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            keys_data = {
                'private_key': private_pem.decode('utf-8'),
                'public_key': public_pem.decode('utf-8')
            }
            
            with open(self.key_file, 'w') as f:
                json.dump(keys_data, f, indent=2)
            logging.info(f"Cryptographic keys saved to {self.key_file}")
        except Exception as e:
            logging.error(f"Error saving keys: {str(e)}")
            raise
    
    def load_keys(self):
        """Load keys from data/ folder"""
        try:
            with open(self.key_file, 'r') as f:
                keys_data = json.load(f)
            
            private_pem = keys_data['private_key'].encode('utf-8')
            public_pem = keys_data['public_key'].encode('utf-8')
            
            self.private_key = load_pem_private_key(private_pem, password=None)
            self.public_key = load_pem_public_key(public_pem)
            logging.info(f"Keys loaded successfully from {self.key_file}")
        except Exception as e:
            logging.error(f"Error loading keys from {self.key_file}: {str(e)}")
            raise
    
    def sign_data(self, data):
        """Sign data with private key"""
        try:
            if isinstance(data, dict):
                data_string = json.dumps(data, sort_keys=True)
            else:
                data_string = str(data)
            
            data_bytes = data_string.encode('utf-8')
            
            signature = self.private_key.sign(
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            logging.error(f"Error signing data: {str(e)}")
            return None
    
    def verify_signature(self, data, signature):
        """Verify signature with public key"""
        try:
            if isinstance(data, dict):
                data_string = json.dumps(data, sort_keys=True)
            else:
                data_string = str(data)
            
            data_bytes = data_string.encode('utf-8')
            signature_bytes = base64.b64decode(signature.encode('utf-8'))
            
            self.public_key.verify(
                signature_bytes,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logging.debug(f"Signature verification failed: {str(e)}")
            return False
    
    def hash_data(self, data):
        """Create SHA-256 hash of data"""
        if isinstance(data, dict):
            data_string = json.dumps(data, sort_keys=True)
        else:
            data_string = str(data)
        
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()
    
    def get_public_key_pem(self):
        """Get public key in PEM format"""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_pem.decode('utf-8')
    
    def create_merkle_root(self, data_list):
        """Create Merkle root for selective disclosure"""
        if not data_list:
            return None
        
        # Hash each piece of data
        hashes = [self.hash_data(item) for item in data_list]
        
        # Build Merkle tree
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]  # Duplicate if odd number
                next_level.append(self.hash_data(combined))
            hashes = next_level
        
        return hashes[0]
    
    def create_proof_for_fields(self, all_fields, selected_fields):
        """Create a proof that selected fields belong to the original credential"""
        # This is a simplified version - in production, use proper ZKP libraries
        proof = {
            'selected_fields': list(selected_fields.keys()),
            'field_hashes': {field: self.hash_data(str(selected_fields[field])) 
                           for field in selected_fields},
            'merkle_root': self.create_merkle_root(list(all_fields.values())),
            'timestamp': datetime.now().isoformat()  # Add import at top
        }
        
        # Sign the proof
        proof['signature'] = self.sign_data(proof)
        return proof
