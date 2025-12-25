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
    
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = datetime.now().isoformat()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate the hash of the block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
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
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class SimpleBlockchain:
    """Simple blockchain implementation for storing credential hashes"""
    
    def __init__(self):
        # FIXED: Use DATA_DIR instead of relative path [web:72]
        self.chain = []
        self.difficulty = 2  # Simple proof of work difficulty
        self.storage_file = DATA_DIR / "blockchain_data.json"  # FIXED: Proper data/ path
        self.load_blockchain()
        
        # Create genesis block if chain is empty
        if not self.chain:
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        genesis_block = Block(0, "Genesis Block - Academic Transcript Blockchain", "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_blockchain()
        logging.info("Genesis block created")
    
    def get_latest_block(self):
        """Get the most recent block in the chain"""
        return self.chain[-1] if self.chain else None
    
    def add_block(self, data):
        """Add a new block to the blockchain"""
        previous_block = self.get_latest_block()
        new_index = len(self.chain)
        new_block = Block(new_index, data, previous_block.hash if previous_block else "0")
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.save_blockchain()
        logging.info(f"New block added with hash: {new_block.hash}")
        return new_block
    
    def is_chain_valid(self):
        """Validate the integrity of the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if current block points to previous block
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
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
                        block_data['previous_hash']
                    )
                    block.timestamp = block_data['timestamp']
                    block.nonce = block_data['nonce']
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
