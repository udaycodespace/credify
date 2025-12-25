#!/usr/bin/env python3
"""Main entry point for the blockchain credential application."""

import os
from app.app import app  # [web:40]

if __name__ == '__main__':
    # Render.com requires binding to PORT env var (default 10000)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
