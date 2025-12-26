#!/usr/bin/env python3
"""
Main entry point for the Blockchain Credential Verification System
Designed for deployment on Render and local development
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.app import app
from app.config import Config

def initialize_app():
    """Initialize application data directories and files"""
    
    # Create necessary directories
    directories = [
        'data',
        'logs',
        'static',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize JSON files if they don't exist
    data_files = {
        'data/blockchain_data.json': '{"chain": [], "difficulty": 4}',
        'data/credentials_registry.json': '{}',
        'data/ipfs_storage.json': '{}',
        'data/tickets.json': '{}',
        'data/messages.json': '{}'
    }
    
    for filepath, default_content in data_files.items():
        file_path = Path(filepath)
        if not file_path.exists():
            file_path.write_text(default_content)
            print(f"✅ Created {filepath}")
    
    print("✅ Application initialized successfully!")

if __name__ == '__main__':
    # Initialize app
    initialize_app()
    
    # Get port from environment (Render sets this automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Get host from environment
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Determine if we're in production
    is_production = os.environ.get('RENDER', False)
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════════════════════════════            
    ║  🎓Blockchain Credential Verification System                                  
    ║  🚀Starting server...                                                          
    ║  📡Host: {host:<42}                                                            
    ║  🔌Port: {str(port):<42}                                                       
    ║  🌍Environment: {'Production (Render)' if is_production else 'Development':<32}
    ╚══════════════════════════════════════════════════════════════════════════════════════ 
    """)
    
    # Run the app
    app.run(
        host=host,
        port=port,
        debug=not is_production,
        threaded=True
    )
