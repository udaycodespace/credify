import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from core.blockchain import SimpleBlockchain
from core.crypto_utils import CryptoManager
import logging

def test_blockchain_integrity():
    print("🚀 Starting Blockchain Regression Suite...")
    
    crypto = CryptoManager()
    blockchain = SimpleBlockchain(crypto)
    
    # 1. Test Block Addition
    print("Testing block addition...")
    initial_len = len(blockchain.chain)
    blockchain.add_block({"test": "data"}, signed_by="admin")
    
    if len(blockchain.chain) != initial_len + 1:
        print("❌ Block addition failed!")
        return False
    print("✅ Block addition passed")
    
    # 2. Test Integrity Validation
    print("Testing chain validation...")
    if not blockchain.is_chain_valid():
        print("❌ Chain validation failed!")
        return False
    print("✅ Chain validation passed")
    
    # 3. Test Merkle Root
    print("Testing Merkle Root consistency...")
    latest = blockchain.get_latest_block()
    if latest.merkle_root != latest.calculate_merkle_root():
        print("❌ Merkle Root mismatch!")
        return False
    print("✅ Merkle Root passed")
    
    # 4. Test Signature
    print("Testing Signature verification...")
    if not crypto.verify_signature(latest.hash, latest.signature):
        print("❌ Signature verification failed!")
        return False
    print("✅ Signature passed")
    
    print("\n💯 ALL TESTS PASSED! Blockchain is stable.")
    return True

if __name__ == "__main__":
    test_blockchain_integrity()
