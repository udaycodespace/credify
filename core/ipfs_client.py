import requests
import json
import logging
from datetime import datetime
from pathlib import Path
import hashlib
import os

# FIXED: Import DATA_DIR from core package [web:42]
from . import DATA_DIR, PROJECT_ROOT  # [web:42]

logging.basicConfig(level=logging.INFO)


class IPFSClient:
    """IPFS client for storing credentials off-chain"""
    
    def __init__(self):
        # Try multiple IPFS endpoints
        self.endpoints = [
            'http://localhost:5001',  # Local IPFS node
            'https://ipfs.infura.io:5001',  # Infura IPFS
        ]
        self.current_endpoint = None
        # FIXED: Use DATA_DIR instead of relative path [web:72]
        self.storage_file = DATA_DIR / "ipfs_storage.json"
        self.local_storage = self.load_local_storage()
        self.find_working_endpoint()
    
    def find_working_endpoint(self):
        """Find a working IPFS endpoint"""
        for endpoint in self.endpoints:
            try:
                response = requests.get(f'{endpoint}/api/v0/version', timeout=5)
                if response.status_code == 200:
                    self.current_endpoint = endpoint
                    logging.info(f"Connected to IPFS at {endpoint}")
                    return
            except Exception as e:
                logging.debug(f"IPFS endpoint {endpoint} not available: {str(e)}")
        
        logging.warning("No IPFS endpoints available, using local storage fallback")
        self.current_endpoint = None
    
    def is_connected(self):
        """Check if connected to IPFS"""
        return self.current_endpoint is not None
    
    def add_json(self, data):
        """Add JSON data to IPFS"""
        if self.current_endpoint:
            return self._add_to_ipfs(data)
        else:
            return self._add_to_local_storage(data)
    
    def _add_to_ipfs(self, data):
        """Add data to actual IPFS network"""
        try:
            json_data = json.dumps(data, indent=2)
            files = {'file': ('credential.json', json_data, 'application/json')}
            
            response = requests.post(
                f'{self.current_endpoint}/api/v0/add',
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result['Hash']
                logging.info(f"Data added to IPFS with CID: {cid}")
                
                # Pin the content for persistence
                self.pin_content(cid)
                
                return cid
            else:
                logging.error(f"IPFS add failed: {response.text}")
                return self._add_to_local_storage(data)
                
        except Exception as e:
            logging.error(f"Error adding to IPFS: {str(e)}")
            return self._add_to_local_storage(data)
    
    def _add_to_local_storage(self, data):
        """Fallback to local storage when IPFS is unavailable"""
        try:
            # FIXED: Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # Generate a pseudo-CID for local storage
            data_string = json.dumps(data, sort_keys=True)
            pseudo_cid = f"local_{hashlib.sha256(data_string.encode()).hexdigest()[:16]}"
            
            self.local_storage[pseudo_cid] = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'size': len(data_string)
            }
            
            self.save_local_storage()
            logging.info(f"Data stored locally with pseudo-CID: {pseudo_cid}")
            return pseudo_cid
            
        except Exception as e:
            logging.error(f"Error storing locally: {str(e)}")
            return None
    
    def get_json(self, cid):
        """Retrieve JSON data from IPFS or local storage"""
        if cid.startswith('local_'):
            return self._get_from_local_storage(cid)
        elif self.current_endpoint:
            return self._get_from_ipfs(cid)
        else:
            return self._get_from_local_storage(cid)
    
    def _get_from_ipfs(self, cid):
        """Get data from actual IPFS network"""
        try:
            response = requests.post(
                f'{self.current_endpoint}/api/v0/cat',
                params={'arg': cid},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"IPFS get failed: {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting from IPFS: {str(e)}")
            return None
    
    def _get_from_local_storage(self, cid):
        """Get data from local storage"""
        try:
            if cid in self.local_storage:
                logging.info(f"Retrieved data from local storage: {cid}")
                return self.local_storage[cid]['data']
            else:
                logging.error(f"CID not found in local storage: {cid}")
                return None
        except Exception as e:
            logging.error(f"Error getting from local storage: {str(e)}")
            return None
    
    def load_local_storage(self):
        """Load local storage from data/ folder"""
        try:
            # FIXED: Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    storage = json.load(f)
                    logging.info(f"Local storage loaded from {self.storage_file} with {len(storage)} items")
                    return storage
            else:
                logging.info(f"No existing local storage found at {self.storage_file}")
                return {}
        except Exception as e:
            logging.error(f"Error loading local storage: {str(e)}")
            return {}
    
    def save_local_storage(self):
        """Save local storage to data/ folder"""
        try:
            # FIXED: Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_file, 'w') as f:
                json.dump(self.local_storage, f, indent=2)
            logging.info(f"Local storage saved to {self.storage_file}")
        except Exception as e:
            logging.error(f"Error saving local storage: {str(e)}")
    
    def pin_content(self, cid):
        """Pin content to ensure it stays available (IPFS only)"""
        if not self.current_endpoint or cid.startswith('local_'):
            return True  # Local storage doesn't need pinning
        
        try:
            response = requests.post(
                f'{self.current_endpoint}/api/v0/pin/add',
                params={'arg': cid},
                timeout=30
            )
            if response.status_code == 200:
                logging.info(f"Content pinned on IPFS: {cid}")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error pinning content: {str(e)}")
            return False
    
    def get_storage_stats(self):
        """Get storage statistics"""
        if self.current_endpoint:
            ipfs_stats = self._get_ipfs_stats()
        else:
            ipfs_stats = None
        
        local_stats = {
            'stored_items': len(self.local_storage),
            'total_size': sum(item.get('size', 0) for item in self.local_storage.values())
        }
        
        return {
            'ipfs_connected': self.is_connected(),
            'current_endpoint': self.current_endpoint,
            'ipfs_stats': ipfs_stats,
            'local_stats': local_stats
        }
    
    def _get_ipfs_stats(self):
        """Get IPFS node statistics"""
        try:
            response = requests.post(
                f'{self.current_endpoint}/api/v0/stats/repo',
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logging.debug(f"Could not get IPFS stats: {str(e)}")
        return None
