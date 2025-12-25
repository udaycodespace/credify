#!/usr/bin/env python3
"""Script to create student users for the blockchain credential system"""

import sys
import os
from pathlib import Path

# FIXED: Add project root to path for imports [web:26]
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# FIXED: Import with proper package structure [web:40]
from app.models import db, User  # [web:42]
from app.app import app         # [web:40]

# FIXED: Ensure data directory exists
try:
    from core import DATA_DIR, PROJECT_ROOT
except ImportError:
    PROJECT_ROOT = project_root
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def create_student(name, student_id):
    """Create a student user account"""
    with app.app_context():
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            user = User(
                username=name, 
                role='student', 
                student_id=student_id, 
                full_name=name,
                email=f"{student_id}@gprec.ac.in"
            )
            user.set_password(student_id)
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created student user: {user.username} (ID: {student_id})")
            print(f"   Login: {name}")
            print(f"   Password: {student_id}")
        else:
            print(f"ℹ️  Student already exists: {user.username} (ID: {student_id})")
            print(f"   Full name: {user.full_name}")
    return user

def main():
    """Main script execution"""
    print("🚀 Blockchain Credential System - Student Creator")
    print("=" * 50)
    
    # FIXED: Create default student if no args provided
    name = "Shashi Kiran"
    student_id = "CST47"
    
    if len(sys.argv) == 3:
        name = sys.argv[1]
        student_id = sys.argv[2]
        print(f"Creating student: {name} (ID: {student_id})")
    else:
        print(f"Creating default student: {name} (ID: {student_id})")
    
    try:
        create_student(name, student_id)
        print("\n✅ Script completed successfully!")
        print(f"📁 Database: {DATA_DIR / 'credentials.db'}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
