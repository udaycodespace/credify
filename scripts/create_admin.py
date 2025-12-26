#!/usr/bin/env python3
"""
Create admin user for Credify system
"""
import sys
import getpass
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import User, db, init_database
from app.app import app
from werkzeug.security import generate_password_hash


def create_admin():
    """Create admin user"""
    
    with app.app_context():
        # Initialize database
        init_database(app)
        
        print("\n" + "="*60)
        print("🎓 Credify Admin User Creation")
        print("="*60 + "\n")
        
        # Get admin details
        username = input("Enter admin username (default: admin): ").strip() or "admin"
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"\n❌ User '{username}' already exists!")
            print(f"   Role: {existing_user.role}")
            print(f"   Email: {existing_user.email}")
            
            overwrite = input("\nOverwrite existing user? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ Operation cancelled.")
                return
            
            db.session.delete(existing_user)
            db.session.commit()
            print(f"✅ Existing user '{username}' removed.")
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email is required!")
            return
        
        password = getpass.getpass("Enter admin password: ")
        if not password:
            print("❌ Password is required!")
            return
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords don't match!")
            return
        
        full_name = input("Enter full name (optional): ").strip() or "System Administrator"
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='issuer',
            full_name=full_name
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ Admin user created successfully!")
            print("="*60)
            print(f"📧 Username: {username}")
            print(f"📧 Email: {email}")
            print(f"👤 Full Name: {full_name}")
            print(f"🔐 Role: issuer")
            print("\n⚠️  Please keep credentials secure!")
            print("="*60 + "\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating admin user: {e}")
            return


if __name__ == '__main__':
    create_admin()
