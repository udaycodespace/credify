# reset_system.py - COMPLETE SYSTEM RESET (No default students)
import os
import json
from pathlib import Path
from app.models import db, User
from app.app import app

def reset_everything():
    """Complete system reset - Only creates admin & verifier, NO students"""
    
    print("🔄 Starting complete system reset...\n")
    
    with app.app_context():
        # 1. DROP ALL DATABASE TABLES
        print("1️⃣ Dropping all database tables...")
        db.drop_all()
        db.create_all()
        print("✅ Database reset complete!\n")
        
        # 2. RESET JSON FILES
        print("2️⃣ Resetting JSON files...")
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Reset credentials registry
        creds_file = data_dir / 'credentials_registry.json'
        with open(creds_file, 'w') as f:
            json.dump({}, f, indent=2)
        print("   ✅ credentials_registry.json reset")
        
        # Reset blockchain
        blockchain_file = data_dir / 'blockchain_data.json'
        genesis_block = {
            "chain": [
                {
                    "index": 0,
                    "timestamp": "2025-01-01T00:00:00Z",
                    "data": "Genesis Block",
                    "previous_hash": "0",
                    "hash": "genesis_hash_000"
                }
            ]
        }
        with open(blockchain_file, 'w') as f:
            json.dump(genesis_block, f, indent=2)
        print("   ✅ blockchain_data.json reset")
        
        # Reset IPFS storage
        ipfs_file = data_dir / 'ipfs_storage.json'
        with open(ipfs_file, 'w') as f:
            json.dump({}, f, indent=2)
        print("   ✅ ipfs_storage.json reset")
        
        # Reset tickets
        tickets_file = data_dir / 'tickets.json'
        with open(tickets_file, 'w') as f:
            json.dump([], f, indent=2)
        print("   ✅ tickets.json reset")
        
        # Reset messages
        messages_file = data_dir / 'messages.json'
        with open(messages_file, 'w') as f:
            json.dump([], f, indent=2)
        print("   ✅ messages.json reset\n")
        
        # 3. CREATE ONLY ADMIN & VERIFIER (NO STUDENTS)
        print("3️⃣ Creating system users (admin & verifier only)...")
        
        # Create admin/issuer
        admin = User(
            username='admin',
            role='issuer',
            student_id=None,
            full_name='System Administrator',
            email='admin@gprec.edu'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("   ✅ Admin/Issuer created (username: admin, password: admin123)")
        
        # Create verifier
        verifier = User(
            username='verifier',
            role='verifier',
            student_id=None,
            full_name='Credential Verifier',
            email='verifier@gprec.edu'
        )
        verifier.set_password('verifier123')
        db.session.add(verifier)
        print("   ✅ Verifier created (username: verifier, password: verifier123)")
        
        db.session.commit()
        print("\n✅ System users created!\n")
        
        # 4. VERIFY USERS
        print("4️⃣ Verifying created users...")
        all_users = User.query.all()
        print(f"\n{'USERNAME':<20} {'ROLE':<10} {'STUDENT ID':<15} {'ACTIVE':<10}")
        print("=" * 60)
        for user in all_users:
            print(f"{user.username:<20} {user.role:<10} {str(user.student_id or 'N/A'):<15} {str(user.is_active):<10}")
        
        print("\n" + "="*60)
        print("🎉 SYSTEM RESET COMPLETE!")
        print("="*60)
        print("\n📝 LOGIN CREDENTIALS:")
        print("-" * 60)
        print("ADMIN/ISSUER:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nVERIFIER:")
        print("  Username: verifier")
        print("  Password: verifier123")
        print("-" * 60)
        print("\n💡 NOTE:")
        print("  Students will be AUTO-CREATED when you issue credentials!")
        print("  Login: student_name / student_id")
        print("-" * 60)

if __name__ == '__main__':
    reset_everything()
