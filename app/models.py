import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pathlib import Path


# FIXED: Import DATA_DIR from project root for database path
try:
    from core import DATA_DIR, PROJECT_ROOT  # Import from sibling package
except ImportError:
    # Fallback for direct imports
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"


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
    
    # NEW: Relationships for Tickets and Messages
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
    """Initialize database with app context and proper data/ path"""
    # FIXED: Ensure DATA_DIR exists before DB creation
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create default admin/issuer account if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                role='issuer',
                full_name='System Administrator',
                email='admin@gprec.ac.in'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create a sample issuer account
            issuer = User(
                username='issuer1',
                role='issuer',
                full_name='Dr. Academic Dean',
                email='dean@gprec.ac.in'
            )
            issuer.set_password('issuer123')
            db.session.add(issuer)
            
            # Create sample student account
            student = User(
                username='Sample Student',
                role='student',
                student_id='SAMPLE001',
                full_name='Sample Student',
                email='student@gprec.ac.in'
            )
            student.set_password('SAMPLE001')
            db.session.add(student)
            
            # Create sample verifier account
            verifier = User(
                username='verifier1',
                role='verifier',
                full_name='HR Manager',
                email='hr@company.com'
            )
            verifier.set_password('verifier123')
            db.session.add(verifier)
            
            db.session.commit()
            print("✅ Default users created successfully!")
            print(f"📁 Database file: {DATA_DIR / 'credentials.db'}")
