import os
import json
import base64
import hashlib
import logging
from pathlib import Path
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

# FIXED: Import DATA_DIR from core package [web:42]
from . import DATA_DIR, PROJECT_ROOT

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
        """Generate new RSA key pair (Upgraded to 4096 bits for Phase 4)"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,  # UPGRADED
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
                encryption_algorithm=serialization.NoEncryption(),
            )

            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            keys_data = {"private_key": private_pem.decode("utf-8"), "public_key": public_pem.decode("utf-8")}

            with open(self.key_file, "w") as f:
                json.dump(keys_data, f, indent=2)
            logging.info(f"Cryptographic keys saved to {self.key_file}")
        except Exception as e:
            logging.error(f"Error saving keys: {str(e)}")
            raise

    def load_keys(self):
        """Load keys from data/ folder"""
        try:
            with open(self.key_file, "r") as f:
                keys_data = json.load(f)

            private_pem = keys_data["private_key"].encode("utf-8")
            public_pem = keys_data["public_key"].encode("utf-8")

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

            data_bytes = data_string.encode("utf-8")

            signature = self.private_key.sign(
                data_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )

            return base64.b64encode(signature).decode("utf-8")
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

            data_bytes = data_string.encode("utf-8")
            signature_bytes = base64.b64decode(signature.encode("utf-8"))

            self.public_key.verify(
                signature_bytes,
                data_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            return True
        except Exception as e:
            logging.debug(f"Signature verification failed: {str(e)}")
            return False

    @staticmethod
    def _compact_json(data):
        """Serialize JSON without extra whitespace for shorter QR payloads."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _jws_hash_algorithm():
        return hashes.SHA256()

    @classmethod
    def _jws_standard_salt_length(cls):
        return cls._jws_hash_algorithm().digest_size

    def sign_jws(self, data):
        """Create a JWS-compact style signature (Header.Payload.Signature)"""
        try:
            header = {"alg": "PS256", "typ": "JWS"}
            header_b64 = base64.urlsafe_b64encode(self._compact_json(header).encode()).decode().rstrip("=")

            if isinstance(data, dict):
                payload_string = self._compact_json(data)
            else:
                payload_string = str(data)
            payload_b64 = base64.urlsafe_b64encode(payload_string.encode()).decode().rstrip("=")

            signing_input = f"{header_b64}.{payload_b64}"

            signature = self.private_key.sign(
                signing_input.encode(),
                padding.PSS(mgf=padding.MGF1(self._jws_hash_algorithm()), salt_length=self._jws_standard_salt_length()),
                self._jws_hash_algorithm(),
            )
            signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

            return f"{header_b64}.{payload_b64}.{signature_b64}"
        except Exception as e:
            logging.error(f"JWS signing failed: {str(e)}")
            return None

    def verify_jws(self, jws_string):
        """Verify a JWS-compact style signature"""
        try:
            parts = jws_string.split(".")
            if len(parts) != 3:
                return False, None

            header_b64, payload_b64, signature_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}"

            # Pad b64
            def pad_b64(s):
                return s + "=" * (4 - len(s) % 4)

            signature = base64.urlsafe_b64decode(pad_b64(signature_b64))
            payload_json = json.loads(base64.urlsafe_b64decode(pad_b64(payload_b64)).decode())

            last_error = None
            for salt_length in (self._jws_standard_salt_length(), padding.PSS.MAX_LENGTH):
                try:
                    self.public_key.verify(
                        signature,
                        signing_input.encode(),
                        padding.PSS(mgf=padding.MGF1(self._jws_hash_algorithm()), salt_length=salt_length),
                        self._jws_hash_algorithm(),
                    )
                    return True, payload_json
                except Exception as verify_error:
                    last_error = verify_error

            raise last_error or ValueError("JWS verification failed")
        except Exception as e:
            logging.debug(f"JWS verification failed: {str(e)}")
            return False, None

    def hash_data(self, data):
        """Create SHA-256 hash of data"""
        if isinstance(data, dict):
            data_string = json.dumps(data, sort_keys=True)
        else:
            data_string = str(data)

        return hashlib.sha256(data_string.encode("utf-8")).hexdigest()

    def get_public_key_pem(self):
        """Get public key in PEM format"""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_pem.decode("utf-8")

    def create_merkle_root(self, leaf_hashes):
        """
        Create Merkle root from a list of hashes.
        Leaf hashes should be pre-computed.
        """
        if not leaf_hashes:
            return None

        current_hashes = sorted(leaf_hashes)  # Sort for consistency

        while len(current_hashes) > 1:
            next_level = []
            for i in range(0, len(current_hashes), 2):
                if i + 1 < len(current_hashes):
                    combined = current_hashes[i] + current_hashes[i + 1]
                else:
                    combined = current_hashes[i] + current_hashes[i]  # Duplicate if odd number
                next_level.append(self.hash_data(combined))
            current_hashes = next_level

        return current_hashes[0]

    def create_proof_for_fields(self, all_fields, selected_fields, field_salts):
        """
        Create a ELITE salted Merkle proof for selective disclosure using PRE-STORED salts.
        Collision-safe construction: hash(salt + "|" + field + "|" + value)
        """
        import secrets

        # 1. Compute salted hashes for all fields (The Leaves) using provided salts
        leaf_hashes = []
        for field, value in all_fields.items():
            salt = field_salts.get(field)
            if not salt:
                # Fallback purely for safety, shouldn't happen with stored salts
                salt = secrets.token_hex(16)

            # COLLISION-SAFE Construction [Security Fix #1]
            leaf_content = f"{salt}|{field}|{value}"
            leaf_hashes.append(self.hash_data(leaf_content))

        # 2. Create Merkle root of all (blinded) fields
        merkle_root = self.create_merkle_root(leaf_hashes)

        # 3. Construct the disclosure proof
        proof = {
            "type": "MerkleStoreDisclosure",
            "merkle_root": merkle_root,
            "disclosed_salts": {field: field_salts[field] for field in selected_fields},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "nonce": secrets.token_hex(8),
        }

        # 4. Sign the whole proof structure
        proof["signature"] = self.sign_data(proof)

        return proof
