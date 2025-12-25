import os
from pathlib import Path

# FIXED: Import DATA_DIR from project structure [web:72]
try:
    from core import DATA_DIR, PROJECT_ROOT
except ImportError:
    # Fallback for standalone usage
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"


class Config:
    """Configuration settings for the application"""
    
    # FIXED: Ensure data directory exists
    DATA_DIR = DATA_DIR  # Reference to proper data/ path
    
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    DEBUG = True
    
    # IPFS settings
    IPFS_ENDPOINTS = [
        'http://localhost:5001',  # Local IPFS node
        'https://ipfs.infura.io:5001',  # Infura IPFS
    ]
    
    # Blockchain settings - FIXED paths
    BLOCKCHAIN_DIFFICULTY = 2
    BLOCKCHAIN_FILE = DATA_DIR / "blockchain_data.json"
    
    # Crypto settings - FIXED path
    KEY_FILE = DATA_DIR / "issuer_keys.pem"
    
    # Storage settings - FIXED paths
    CREDENTIALS_FILE = DATA_DIR / "credentials_registry.json"
    IPFS_STORAGE_FILE = DATA_DIR / "ipfs_storage.json"
    
    # University settings
    UNIVERSITY_NAME = 'G. Pulla Reddy Engineering College'
    DEPARTMENT_NAME = 'Computer Science Engineering'
    UNIVERSITY_DID = 'did:example:university'
    
    # Database settings - FIXED path
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'credentials.db'}"
    
    @classmethod
    def create_data_directory(cls):
        """Ensure data directory exists"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Data directory ready: {cls.DATA_DIR}")
        return cls.DATA_DIR
