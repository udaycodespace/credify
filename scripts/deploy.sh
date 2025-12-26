#!/bin/bash

# Deployment script for Render or other platforms

echo "🚀 Starting deployment..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python -c "from app.models import init_database; from app.app import app; init_database(app)"

# Create admin user if not exists
echo "👤 Creating default admin..."
python scripts/create_admin.py

echo "✅ Deployment complete!"
