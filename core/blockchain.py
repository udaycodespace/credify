import hashlib
import json
from datetime import datetime
import os
import logging
from pathlib import Path

# FIXED: Import DATA_DIR from core package [web:42]
from . import DATA_DIR, PROJECT_ROOT  # [web:42]

logging.basicConfig(level=logging.INFO)


class Block:
    """Represents a single block in the blockchain"""
    
    def __init__(self, index, data, previous_hash, signed_by=None, signature=None):
        self.index = index
        self.timestamp = datetime.now().isoformat()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.signed_by = signed_by
        self.signature = signature
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()
    
    def calculate_merkle_root(self):
        """
        Calculate Merkle Root for the data in this block.
        For simplicity, if data is a dict, we hash its values.
        If it's a list, we hash each item.
        """
        if isinstance(self.data, dict):
            items = [str(v) for v in self.data.values()]
        elif isinstance(self.data, list):
            items = [str(i) for i in self.data]
        else:
            items = [str(self.data)]
            
        # Trivial Merkle implementation if not using complex library
        if not items:
            return hashlib.sha256(b"empty").hexdigest()
            
        hashes = [hashlib.sha256(item.encode()).hexdigest() for item in items]
        
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i+1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_hashes
            
        return hashes[0]

    def calculate_hash(self):
        """Calculate the hash of the block header and data"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty=2):
        """Simple proof of work mining"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        logging.info(f"Block mined: {self.hash}")
    
    def to_dict(self):
        """Convert block to dictionary for storage/API"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'merkle_root': self.merkle_root,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'signed_by': self.signed_by,
            'signature': self.signature
        }


class SimpleBlockchain:
    """Simple blockchain implementation for storing credential hashes"""
    
    # Authorized entities allowed to sign blocks
    VALIDATORS = ['admin', 'issuer1', 'System']
    
    def __init__(self, crypto_manager=None):
        self.chain = []
        self.difficulty = 2
        self.storage_file = DATA_DIR / "blockchain_data.json"
        
        # Inject crypto manager for block signing/verification
        self.crypto_manager = crypto_manager
        # Merkle Tree Integration
        self.nodes = set()
        
        self.load_blockchain()
        
        # Create genesis block if chain is empty
        if not self.chain:
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        genesis_block = Block(0, "Genesis Block - Academic Transcript Blockchain", "0", signed_by="System")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_blockchain()
        logging.info("Genesis block created")
    
    def get_latest_block(self):
        """Get the most recent block in the chain"""
        return self.chain[-1] if self.chain else None
    
    def register_node(self, address):
        """Add a new node to the list of peers"""
        from urllib.parse import urlparse
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def resolve_conflicts(self):
        """
        Consensus algorithm: replace our chain with the longest valid one in the network.
        """
        import requests
        neighbors = self.nodes
        new_chain = None
        
        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        
        # Grab and verify the chains from all the nodes in our network
        for node in neighbors:
            try:
                response = requests.get(f'http://{node}/api/blockchain/blocks')
                
                if response.status_code == 200:
                    data = response.json()
                    length = len(data['blocks'])
                    chain_data = data['blocks']
                    
                    # Check if the length is longer and the chain is valid
                    if length > max_length:
                        # Construct temporary blockchain to validate it
                        temp_chain = []
                        for block_data in chain_data:
                            block = Block(
                                block_data['index'],
                                block_data['data'],
                                block_data['previous_hash'],
                                signed_by=block_data.get('signed_by'),
                                signature=block_data.get('signature')
                            )
                            block.timestamp = block_data['timestamp']
                            block.nonce = block_data['nonce']
                            block.merkle_root = block_data.get('merkle_root')
                            block.hash = block_data['hash']
                            temp_chain.append(block)
                            
                        # Validate the temporary chain
                        if self._is_chain_valid_external(temp_chain):
                            max_length = length
                            new_chain = temp_chain
            except Exception as e:
                logging.error(f"Error connecting to node {node}: {str(e)}")
                
        # Replace our chain if we discovered a new, valid, longer chain
        if new_chain:
            self.chain = new_chain
            self.save_blockchain()
            return True
            
        return False

    def _is_chain_valid_external(self, chain):
        """Helper to validate an external chain"""
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.merkle_root != current_block.calculate_merkle_root():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
            
            if self.crypto_manager and current_block.signature:
                if current_block.signed_by not in self.VALIDATORS:
                    return False
                if not self.crypto_manager.verify_signature(current_block.hash, current_block.signature):
                    return False
        return True
    
    def broadcast_block(self):
        """Notify peers to resolve conflicts (sync)"""
        import requests
        for node in self.nodes:
            try:
                # We don't wait for response, just notify
                requests.get(f'http://{node}/api/nodes/resolve', timeout=0.5)
            except:
                pass

    def add_block(self, data, signed_by="admin"):
        """Add a new signed block to the blockchain"""
        previous_block = self.get_latest_block()
        new_index = len(self.chain)
        new_block = Block(new_index, data, previous_block.hash if previous_block else "0", signed_by=signed_by)
        new_block.mine_block(self.difficulty)
        
        # Sign the block hash if crypto_manager is provided
        if self.crypto_manager:
            new_block.signature = self.crypto_manager.sign_data(new_block.hash)
            
        self.chain.append(new_block)
        self.save_blockchain()
        logging.info(f"New block added with hash: {new_block.hash}")
        
        # PROPAGATION: Broadcast to peers
        self.broadcast_block()
        
        return new_block
    
    def is_chain_valid(self):
        """Validate the integrity, signatures, and Merkle roots of the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # 1. Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                logging.error(f"Invalid hash at block {i}")
                return False
            
            # 2. Check if Merkle root is valid
            if current_block.merkle_root != current_block.calculate_merkle_root():
                logging.error(f"Invalid Merkle root at block {i}")
                return False
            
            # 3. Check if current block points to previous block
            if current_block.previous_hash != previous_block.hash:
                logging.error(f"Chain broken at block {i}")
                return False
            
            # 4. Verify digital signature (Proof of Authority)
            if self.crypto_manager and current_block.signature:
                # First, check if the signer is authorized
                if current_block.signed_by not in self.VALIDATORS:
                    logging.error(f"Unauthorized signer {current_block.signed_by} at block {i}")
                    return False
                    
                is_valid = self.crypto_manager.verify_signature(
                    current_block.hash, 
                    current_block.signature
                )
                if not is_valid:
                    logging.error(f"Invalid signature at block {i}")
                    return False
            elif i > 0: # Genesis block (index 0) might not have signature in some cases, but subsequent must
                # In strict PoA, all blocks should be signed
                if current_block.signed_by not in self.VALIDATORS:
                    logging.error(f"Missing or unauthorized signature at block {i}")
                    return False
        
        return True

    def is_chain_valid_parallel(self):
        """Highly optimized parallel verification of digital signatures"""
        from concurrent.futures import ThreadPoolExecutor
        
        def verify_block(i):
            if i == 0: return True
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.merkle_root != current_block.calculate_merkle_root():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
            
            if self.crypto_manager and current_block.signature:
                if current_block.signed_by not in self.VALIDATORS:
                    return False
                if not self.crypto_manager.verify_signature(current_block.hash, current_block.signature):
                    return False
            return True

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(verify_block, range(len(self.chain))))
            
        return all(results)
    
    def save_blockchain(self):
        """Save blockchain to data/ folder"""
        try:
            # FIXED: Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            blockchain_data = [block.to_dict() for block in self.chain]
            with open(self.storage_file, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            logging.info(f"Blockchain saved to {self.storage_file}")
        except Exception as e:
            logging.error(f"Error saving blockchain: {str(e)}")
    
    def load_blockchain(self):
        """Load blockchain from data/ folder"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    blockchain_data = json.load(f)
                
                self.chain = []
                for block_data in blockchain_data:
                    block = Block(
                        block_data['index'],
                        block_data['data'],
                        block_data['previous_hash'],
                        signed_by=block_data.get('signed_by'),
                        signature=block_data.get('signature')
                    )
                    block.timestamp = block_data['timestamp']
                    block.nonce = block_data['nonce']
                    block.merkle_root = block_data.get('merkle_root')
                    block.hash = block_data['hash']
                    self.chain.append(block)
                
                logging.info(f"Blockchain loaded with {len(self.chain)} blocks from {self.storage_file}")
            else:
                logging.info("No existing blockchain file found")
        except Exception as e:
            logging.error(f"Error loading blockchain: {str(e)}")
            self.chain = []
    
    def get_credential_blocks(self):
        """Get all blocks containing credential data"""
        credential_blocks = []
        for block in self.chain:
            if isinstance(block.data, dict) and 'credential_id' in block.data:
                credential_blocks.append(block)
        return credential_blocks
    
    def find_credential_block(self, credential_id):
        """Find a specific credential block by ID"""
        for block in self.chain:
            if isinstance(block.data, dict) and block.data.get('credential_id') == credential_id:
                return block
        return None
