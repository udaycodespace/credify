#!/usr/bin/env python3
"""
Create student user for Credify system
"""
import sys
import getpass
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import User, db, init_database
from app.app import app
from werkzeug.security import generate_password_hash


def create_student():
    """Create student user"""
    
    with app.app_context():
        # Initialize database
        init_database(app)
        
        print("\n" + "="*60)
        print("🎓 Credify Student User Creation")
        print("="*60 + "\n")
        
        # Get student details
        username = input("Enter roll number (username): ").strip()
        if not username:
            print("❌ Roll number is required!")
            return
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"\n❌ User '{username}' already exists!")
            print(f"   Role: {existing_user.role}")
            print(f"   Email: {existing_user.email}")
            return
        
        email = input("Enter student email: ").strip()
        if not email:
            print("❌ Email is required!")
            return
        
        # Default password is roll number
        use_default = input(f"Use roll number as password? (Y/n): ").strip().lower()
        if use_default in ['', 'y', 'yes']:
            password = username
            print(f"✅ Using default password: {username}")
        else:
            password = getpass.getpass("Enter password: ")
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Passwords don't match!")
                return
        
        full_name = input("Enter full name: ").strip()
        if not full_name:
            print("❌ Full name is required!")
            return
        
        # Create student user
        student = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='holder',
            full_name=full_name
        )
        
        try:
            db.session.add(student)
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ Student user created successfully!")
            print("="*60)
            print(f"📧 Username: {username}")
            print(f"📧 Email: {email}")
            print(f"👤 Full Name: {full_name}")
            print(f"🔐 Role: holder")
            print(f"🔑 Password: {password}")
            print("\n⚠️  Student should change password after first login!")
            print("="*60 + "\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating student user: {e}")
            return


if __name__ == '__main__':
    create_student()
