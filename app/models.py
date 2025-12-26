import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pathlib import Path

# ============================================================================
# FIXED: Database path configuration for Render compatibility
# ============================================================================

# Use environment variable for database URL (Render provides this)
# Fallback to /tmp on Render, local data/ directory for development
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Render or production environment
    if DATABASE_URL.startswith('postgres://'):
        # Fix for Render PostgreSQL URL
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    elif DATABASE_URL.startswith('sqlite:///'):
        # Ensure /tmp directory for SQLite on Render
        if not DATABASE_URL.startswith('sqlite:////tmp'):
            DATABASE_URL = 'sqlite:////tmp/credify.db'
else:
    # Local development - use data/ directory
    try:
        from core import DATA_DIR, PROJECT_ROOT
    except ImportError:
        PROJECT_ROOT = Path(__file__).parent.parent
        DATA_DIR = PROJECT_ROOT / "data"
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f'sqlite:///{DATA_DIR / "credentials.db"}'

# ============================================================================
# Database initialization
# ============================================================================

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication with role-based access"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # issuer, student, verifier
    student_id = db.Column(db.String(50), unique=True, nullable=True)  # For students
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships for Tickets and Messages
    tickets = db.relationship('Ticket', backref='student', lazy=True, foreign_keys='Ticket.student_user_id')
    sent_messages = db.relationship('Message', backref='sender', lazy=True, foreign_keys='Message.from_user_id')
    received_messages = db.relationship('Message', backref='recipient', lazy=True, foreign_keys='Message.to_user_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Ticket(db.Model):
    """Ticket model for student credential correction requests"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)  # TKT-001, TKT-002...
    student_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_roll_number = db.Column(db.String(50), nullable=False)
    
    # Ticket details
    issue_type = db.Column(db.String(50), nullable=False)  # roll_wrong, cgpa_update, name_wrong, etc.
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # urgent, medium, normal
    status = db.Column(db.String(20), default='todo')  # todo, in_progress, completed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Admin response
    admin_response = db.Column(db.Text, nullable=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Related credential
    credential_id = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<Ticket {self.ticket_number} - {self.status}>'
    
    def to_dict(self):
        """Convert ticket to dictionary for API responses"""
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'student_user_id': self.student_user_id,
            'student_roll_number': self.student_roll_number,
            'issue_type': self.issue_type,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'admin_response': self.admin_response,
            'admin_user_id': self.admin_user_id,
            'credential_id': self.credential_id
        }


class Message(db.Model):
    """Message model for admin-student communication"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = broadcast
    
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
    # Message type
    is_broadcast = db.Column(db.Boolean, default=False)  # True if sent to all students
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Related ticket (optional)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=True)
    
    def __repr__(self):
        return f'<Message {self.id} - {self.subject[:30]}>'
    
    def to_dict(self):
        """Convert message to dictionary for API responses"""
        return {
            'id': self.id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'subject': self.subject,
            'body': self.body,
            'is_broadcast': self.is_broadcast,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ticket_id': self.ticket_id
        }


def init_database(app):
    """Initialize database with app context"""
    # Configure database URL
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # For local development, ensure data directory exists
    if DATABASE_URL.startswith('sqlite:///') and not DATABASE_URL.startswith('sqlite:////tmp'):
        try:
            db_path = DATABASE_URL.replace('sqlite:///', '')
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️  Warning: Could not create database directory: {e}")
    
    db.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
            print(f"✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise
        
        # Create default users if not exists
        create_default_users()


def create_default_users():
    """Create default users for testing"""
    try:
        # Create default admin/issuer account if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("📝 Creating default user accounts...")
            
            # Admin account
            admin = User(
                username='admin',
                role='issuer',
                full_name='System Administrator',
                email='admin@gprec.ac.in'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Issuer account
            issuer = User(
                username='issuer1',
                role='issuer',
                full_name='Dr. Academic Dean',
                email='dean@gprec.ac.in'
            )
            issuer.set_password('issuer123')
            db.session.add(issuer)
            
            # Sample student account
            student = User(
                username='21131A05E9',
                role='student',
                student_id='21131A05E9',
                full_name='Sample Student',
                email='student@gprec.ac.in'
            )
            student.set_password('21131A05E9')
            db.session.add(student)
            
            # Verifier account
            verifier = User(
                username='verifier1',
                role='verifier',
                full_name='HR Manager',
                email='hr@company.com'
            )
            verifier.set_password('verifier123')
            db.session.add(verifier)
            
            db.session.commit()
            print(f"✅ Default user accounts created (4 users)")
            print(f"   ℹ️  Check README.md for login credentials")
        else:
            print("✅ Default users already exist")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not create default users: {e}")
        db.session.rollback()
