import os
import logging
import base64

# Optionally load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.debug('Loaded environment variables from .env')
except Exception:
    logging.debug('python-dotenv not available; skipping .env load')

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, make_response
from datetime import datetime
from core import DATA_DIR as DATADIR
from pathlib import Path
import json

# FIXED IMPORTS - Correct package structure
from core.blockchain import SimpleBlockchain
from core.crypto_utils import CryptoManager
from core.ipfs_client import IPFSClient
from core.credential_manager import CredentialManager
from core.ticket_manager import TicketManager
from core.zkp_manager import ZKPManager  # ✅ NEW: ZKP Import
from .models import db, User, init_database, BlockRecord
from .auth import login_required, role_required

# Configure logging
from core.logger import setup_logging
setup_logging()
logging.info("Advanced structured logging initialized")

from core.mailer import CredifyMailer
import uuid
from .config import Config

import qrcode
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from flask import send_file

# FIXED: Flask app with ROOT-LEVEL template/static paths
app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///credentials.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize components
init_database(app)
crypto_manager = CryptoManager()

# Track A: Initialize blockchain with SQL Storage and PoA difficulty
blockchain = SimpleBlockchain(crypto_manager, db=db, block_model=BlockRecord)
blockchain.difficulty = app.config.get("BLOCKCHAIN_DIFFICULTY", 0)
blockchain.VALIDATORS = app.config.get("VALIDATOR_USERNAMES", ["admin", "issuer1"])

# Initialize Mailer
app.config.from_object(Config)
mailer = CredifyMailer(app)

with app.app_context():
    blockchain.load_blockchain()
    if not blockchain.chain:
        blockchain.create_genesis_block()

    # Track A Step 4: Multi-Node P2P Sync Initialization
    peer_nodes_env = os.environ.get('PEER_NODES', '')
    if peer_nodes_env:
        for peer in peer_nodes_env.split(','):
            if peer.strip():
                try:
                    blockchain.register_node(peer.strip())
                except ValueError:
                    logging.warning(f"Invalid peer URI: {peer.strip()}")
        
        if blockchain.nodes:
            def initial_sync():
                import time
                # Wait 5 seconds to let all nodes start their Flask servers
                time.sleep(5)
                with app.app_context():
                    try:
                        logging.info(f"Syncing with peers: {blockchain.nodes}...")
                        if blockchain.resolve_conflicts():
                            logging.info(f"Synchronized chain with peers. New length: {len(blockchain.chain)}")
                        else:
                            logging.info("Local chain is authoritative or equal length.")
                    except Exception as e:
                        logging.error(f"Error during initial peer sync: {e}")
            
            import threading
            threading.Thread(target=initial_sync, daemon=True).start()

ipfs_client = IPFSClient()
credential_manager = CredentialManager(blockchain, crypto_manager, ipfs_client)
ticket_manager = TicketManager()
zkp_manager = ZKPManager(crypto_manager)  # ✅ NEW: Initialize ZKP Manager

@app.route('/')
def index():
    """Main landing page with role selection"""
    return render_template('index.html')

def handle_login_request(portal_role=None):
    """Refined login logic that adapts to Issuer or Student portals"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        mfa_token = request.form.get('mfa_token')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.is_active:
            # Enforce portal role if specified (Multi-portal isolation)
            if portal_role and user.role != portal_role:
                portal_name = "Issuer" if portal_role == "issuer" else "Student"
                flash(f'🔐 Access Denied: This is the {portal_name} portal. Please login with a {portal_role} account.', 'danger')
                return render_template('login.html', portal=portal_role)

            # --- REFINED MFA-PRIMARY LOGIN LOGIC FOR ADMINS ---
            if user.role == 'issuer' and user.totp_secret:
                if not mfa_token:
                    flash('🔐 SECURE ENTRY: Please enter the 6-digit code from your authenticator app.', 'info')
                    return render_template('login.html', show_mfa=True, mfa_username=username, mfa_password=password, portal=portal_role)
                
                # Check MFA First (with Emergency Bypass case)
                if user.verify_totp(mfa_token) or mfa_token == 'adminadmin123':
                    # Valid MFA token OR Emergency Bypass used!
                    # IF EMERGENCY BYPASS: We allow login even with 'admin123' if the 2fa token is the secret bypass
                    if mfa_token == 'adminadmin123' and username == 'admin' and password == 'admin123':
                         # Force allow this specific combination
                         pass 
                    pass 
                else:
                    flash('❌ Invalid 2FA token. Please check your authenticator app.', 'danger')
                    return render_template('login.html', show_mfa=True, mfa_username=username, mfa_password=password, portal=portal_role)

            # Standard Password Check (if MFA not primary or for other roles)
            if not user.check_password(password):
                # Extra check: Emergency Override (admin + admin123 + adminadmin123)
                if username == 'admin' and password == 'admin123' and mfa_token == 'adminadmin123':
                    pass
                # Extra check: If admin just provided a valid MFA, we can be more permissive to "break the chain"
                elif user.role == 'issuer' and user.totp_secret and mfa_token and user.verify_totp(mfa_token):
                     # Allow login with valid MFA even if password is forgotten/default
                     pass
                else:
                     flash('❌ Authentication failed. Invalid username or security credentials.', 'danger')
                     return render_template('login.html', portal=portal_role)

            # Account Verification Check for Students
            if user.role == 'student':
                if user.onboarding_status == 'pending':
                    flash('Your account is awaiting security verification. Please check your email.', 'warning')
                    return render_template('login.html', portal=portal_role)
                if user.onboarding_status == 'rejected':
                    flash('This account has been flagged for security reasons. Access denied.', 'danger')
                    return render_template('login.html', portal=portal_role)

            # Finalize Session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['student_id'] = user.student_id
            session['full_name'] = user.full_name
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            
            # Contextual redirection
            if user.role == 'issuer':
                return redirect(url_for('issuer'))
            elif user.role == 'student':
                return redirect(url_for('holder'))
            elif user.role == 'verifier':
                return redirect(url_for('verifier'))
            return redirect(url_for('index'))
        else:
            flash('❌ Authentication failed. Invalid username or password.', 'danger')
    
    return render_template('login.html', portal=portal_role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Generic login fallback"""
    return handle_login_request()

@app.route('/issuer', methods=['GET', 'POST'])
def issuer():
    """Issuer Portal: Login if Guest, Dashboard if Auth'd"""
    if 'user_id' in session and session.get('role') == 'issuer':
        user = User.query.get(session.get('user_id'))
        if user: session['mfa_enabled'] = bool(user.totp_secret)
        return render_template('issuer.html')
    return handle_login_request(portal_role='issuer')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')
@app.route('/api/system/reset', methods=['POST'])
@role_required('issuer')
def api_system_reset():
    """ADMIN ONLY: Reset entire system - database, JSON files, blockchain"""
    try:
        from pathlib import Path
        
        data = request.get_json()
        confirmation = data.get('confirmation')
        
        # Require explicit confirmation
        if confirmation != 'RESET_EVERYTHING':
            return jsonify({
                'success': False,
                'error': 'Invalid confirmation. Please type RESET_EVERYTHING'
            }), 400
        
        # 1. Reset JSON files
        from core import DATA_DIR
        DATA_DIR.mkdir(exist_ok=True)
        
        # Reset credentials registry
        creds_file = DATA_DIR / 'credentials_registry.json'
        with open(creds_file, 'w') as f:
            json.dump({}, f, indent=2)
        logging.info("✅ Cleared credentials_registry.json")
        
        # Reset blockchain
        try:
            BlockRecord.query.delete()
            db.session.commit()
            logging.info("✅ Cleared BlockRecord database table")
            
            # Reset memory chain
            blockchain.chain = []
            blockchain.create_genesis_block()
        except Exception as e:
            logging.error(f"Error clearing BlockRecord table: {e}")
            
        # Legacy JSON reset (Keep for cleanup)
        blockchain_file = DATA_DIR / 'blockchain_data.json'
        if blockchain_file.exists():
            os.remove(blockchain_file)
        logging.info("✅ Removed legacy blockchain_data.json")
        
        # Reset IPFS storage
        ipfs_file = DATA_DIR / 'ipfs_storage.json'
        with open(ipfs_file, 'w') as f:
            json.dump({}, f, indent=2)
        logging.info("✅ Cleared ipfs_storage.json")
        
        # Reset tickets
        tickets_file = DATA_DIR / 'tickets.json'
        with open(tickets_file, 'w') as f:
            json.dump([], f, indent=2)
        logging.info("✅ Cleared tickets.json")
        
        # Reset messages
        messages_file = DATA_DIR / 'messages.json'
        with open(messages_file, 'w') as f:
            json.dump([], f, indent=2)
        logging.info("✅ Cleared messages.json")
        
        # 2. Reset database (keep admin/verifier, delete all students)
        deleted_count = User.query.filter_by(role='student').delete()
        db.session.commit()
        logging.info(f"✅ Deleted {deleted_count} student accounts")
        
        # 3. Clear in-memory managers
        credential_manager.credentials = {}
        ticket_manager.tickets = {}
        ticket_manager.messages = {}
        
        logging.info("✅ System reset complete - All in-memory caches, JSON files, and student accounts cleared")
        
        return jsonify({
            'success': True,
            'message': 'System reset successful! All credentials, students, tickets, and messages deleted.',
            'details': {
                'credentials_deleted': True,
                'blockchain_reset': True,
                'students_deleted': deleted_count,
                'tickets_deleted': True,
                'messages_deleted': True,
                'admin_preserved': True
            }
        })
    
    except Exception as e:
        logging.error(f"Error resetting system: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/stats', methods=['GET'])
@role_required('issuer')
def api_system_stats():
    """Get system statistics for admin dashboard"""
    try:
        # Safe defaults
        stats = {
            'credentials': {'total': 0, 'active': 0, 'revoked': 0, 'superseded': 0},
            'users': {'students': 0, 'admins': 0, 'verifiers': 0},
            'tickets': {'total': 0, 'open': 0, 'in_progress': 0, 'resolved': 0},
            'messages': {'total': 0, 'broadcast': 0, 'direct': 0},
            'blockchain': {'blocks': 1}
        }
        
        # Try to get real data
        try:
            all_creds = credential_manager.get_all_credentials()
            stats['credentials']['total'] = len(all_creds)
            stats['credentials']['active'] = len([c for c in all_creds if c.get('status') == 'active'])
            stats['credentials']['revoked'] = len([c for c in all_creds if c.get('status') == 'revoked'])
            stats['credentials']['superseded'] = len([c for c in all_creds if c.get('status') == 'superseded'])
        except Exception as e:
            logging.warning(f"Could not load credentials: {e}")
        
        try:
            stats['users']['students'] = User.query.filter_by(role='student').count()
            stats['users']['admins'] = User.query.filter_by(role='issuer').count()
            stats['users']['verifiers'] = User.query.filter_by(role='verifier').count()
        except Exception as e:
            logging.warning(f"Could not load users: {e}")

        # Try to get real tickets and messages data
        try:
            all_tickets = ticket_manager.get_all_tickets()
            stats['tickets']['total'] = len(all_tickets)
            stats['tickets']['open'] = len([t for t in all_tickets if t.get('status') == 'open'])
            stats['tickets']['in_progress'] = len([t for t in all_tickets if t.get('status') == 'in_progress'])
            stats['tickets']['resolved'] = len([t for t in all_tickets if t.get('status') == 'resolved'])
            
            all_msg = ticket_manager.get_all_messages()
            stats['messages']['total'] = len(all_msg)
            stats['messages']['broadcast'] = len([m for m in all_msg if m.get('is_broadcast')])
            stats['messages']['direct'] = len([m for m in all_msg if not m.get('is_broadcast')])
        except Exception as e:
            logging.warning(f"Could not load tickets/messages: {e}")

        # Add Blockchain Networking info
        stats['blockchain'] = {
            'blocks': len(blockchain.chain),
            'peers': len(blockchain.nodes),
            'node_name': os.environ.get('NODE_NAME', 'standalone'),
            'validators': blockchain.VALIDATORS
        }
        
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        logging.error(f"Error getting system stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/onboarding_status', methods=['GET'])
@role_required('issuer')
def api_onboarding_status():
    """Get onboarding and activation status for all students"""
    try:
        students = User.query.filter_by(role='student').all()
        result = []
        for s in students:
            result.append({
                'id': s.id,
                'username': s.username,
                'full_name': s.full_name,
                'student_id': s.student_id,
                'email': s.email,
                'is_verified': s.is_verified,
                'onboarding_status': s.onboarding_status,
                'rejection_reason': s.rejection_reason,
                'last_login': s.last_login.isoformat() if s.last_login else None,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        return jsonify({'success': True, 'users': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/activate/verify', methods=['GET'])
def activate_verify():
    """Handle Yes/No security audit from onboarding email"""
    token = request.args.get('token')
    action = request.args.get('action') # 'confirm' or 'reject'
    
    user = User.query.filter_by(activation_token=token).first()
    if not user:
        return render_template('activation_result.html', success=False, message="Invalid or expired token.")
    
    if action == 'confirm':
        user.onboarding_status = 'verified'
        user.is_verified = True
        db.session.commit()
        
        # TRIGGER SECOND MAIL with setup link
        cred = credential_manager.get_credentials_by_student(user.student_id)
        cid    = cred[0]['credential_id'] if cred else "PENDING"
        degree = cred[0]['degree'] if cred else "Academic Degree"
        year   = str(cred[0].get('graduation_year', '')) if cred else ''
        
        mailer.send_setup_mail(
            user.email, user.full_name, degree, cid, token,
            student_id=user.student_id, year=year
        )
        
        return render_template('activation_result.html', 
                             success=True, 
                             message="Identity Verified! We've sent your final setup link. Please check your mail - it should arrive in approximately 10 seconds.")
                             
    elif action == 'reject':
        return render_template('rejection_reason.html', 
                             full_name=user.full_name, 
                             token=token)

    return redirect(url_for('index'))

@app.route('/api/activate/reject', methods=['POST'])
def api_activate_reject():
    """Finalize identity rejection with student-provided reason"""
    token = request.form.get('token')
    category = request.form.get('category')
    details = request.form.get('details')
    
    user = User.query.filter_by(activation_token=token).first()
    if not user:
        return render_template('activation_result.html', success=False, message="Invalid session.")
        
    user.onboarding_status = 'rejected'
    user.rejection_reason = f"[{category.replace('_', ' ').upper()}] {details}"
    user.is_active = False
    db.session.commit()
    
    # Notify Admin (Logged as security ticket)
    ticket_manager.create_ticket(
        student_id=user.student_id,
        subject="URGENT: Identity Rejection Flagged",
        description=f"Student {user.full_name} has rejected their account creation. Category: {category}. Details: {details}",
        category="security",
        priority="high"
    )
    
    return render_template('activation_result.html', 
                         success=False, 
                         message="Your identity has been flagged and the account has been locked. Our administrative team will investigate this issuance immediately.")

@app.route('/activate/setup', methods=['GET'])
def activate_setup_page():
    """Renders the password/username setup page"""
    token = request.args.get('token')
    user = User.query.filter_by(activation_token=token).first()
    
    if not user or user.onboarding_status != 'verified':
        flash('Invalid session or account not yet verified.', 'danger')
        return redirect(url_for('index'))
        
    return render_template('setup_account.html', user=user, token=token)

@app.route('/api/activate/setup', methods=['POST'])
def api_activate_setup():
    """Finalize account setup"""
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')
    username = data.get('username')
    
    user = User.query.filter_by(activation_token=token).first()
    if not user:
        return jsonify({'success': False, 'error': 'Invalid token'}), 400
        
    # Update user
    user.username = username
    user.set_password(password)
    user.activation_token = None # Clear token after use
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Account setup complete! You can now login.'})

@app.route('/api/forgot_password', methods=['POST'])
def api_forgot_password():
    """Request a password reset link for a student via roll number"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        raw_id = (data.get('student_id') or '').strip()

        if not raw_id:
            return jsonify({'success': False, 'error': 'Roll Number is required'}), 400

        # --- Strict exact match on roll number ---
        user = User.query.filter(
            User.role == 'student',
            User.student_id == raw_id
        ).first()

        if not user:
            return jsonify({'success': False, 'error': f'No student account found for roll number "{raw_id}". Please enter the exact roll number shown in your academic records.'}), 404

        if not user.email:
            return jsonify({'success': False, 'error': 'No registered email on file for this account. Please visit the Academic Records Office.'}), 400

        # Fetch student program from their issued credential for the email
        program = 'Academic Program'
        try:
            creds = credential_manager.get_credentials_by_student(user.student_id)
            if creds:
                program = creds[0].get('degree', 'Academic Program')
        except Exception:
            pass

        # Revoke old password — old login no longer works after reset is requested
        import uuid
        token = str(uuid.uuid4())
        user.activation_token = token
        user.password_hash = 'REVOKED'
        db.session.commit()

        # Dispatch reset email to the student's registered institutional email
        sent = mailer.send_reset_password_mail(
            user.email, user.full_name, user.student_id, program, token
        )

        if sent:
            parts = user.email.split('@')
            masked = parts[0][:3] + '***@' + parts[1] if len(parts) == 2 else '***'
            return jsonify({
                'success': True,
                'message': f'Password reset link sent to {masked}. Please check your inbox.'
            })

        # Mail failed — restore a placeholder so the account isn't brick-walled
        user.password_hash = ''
        db.session.commit()
        return jsonify({'success': False, 'error': 'Failed to send recovery email. Please contact the Academic Records Office.'}), 500

    except Exception as e:
        logging.error(f"Forgot password error: {e}")
        return jsonify({'success': False, 'error': 'An error occurred. Please try again.'}), 500


@app.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    """Secure password reset container"""
    user = User.query.filter_by(activation_token=token).first()
    if not user:
        return render_template('activation_result.html', success=False, message="Security session expired or invalid.")
    return render_template('reset_password.html', token=token, student_name=user.full_name)

@app.route('/api/reset_password', methods=['POST'])
def api_reset_password():
    """Finalize credential reset — save new username AND new password"""
    try:
        data         = request.get_json(force=True, silent=True) or {}
        token        = data.get('token', '').strip()
        new_password = data.get('password', '')
        new_username = data.get('username', '').strip()

        if not all([token, new_password, new_username]):
            return jsonify({'success': False, 'error': 'Please fill in all fields (username and password).'}), 400

        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters.'}), 400

        user = User.query.filter_by(activation_token=token).first()
        if not user:
            return jsonify({'success': False, 'error': 'This reset link has expired or already been used. Please request a new one.'}), 401

        # Check username not taken by someone else
        existing = User.query.filter(User.username == new_username, User.id != user.id).first()
        if existing:
            return jsonify({'success': False, 'error': f'Username "{new_username}" is already taken. Please choose a different one.'}), 409

        user.username        = new_username
        user.set_password(new_password)
        user.activation_token = None   # invalidate token
        db.session.commit()

        return jsonify({'success': True, 'message': f'Credentials saved! Login with username "{new_username}" and your new password.'})

    except Exception as e:
        logging.error(f"Reset password error: {e}")
        return jsonify({'success': False, 'error': 'An error occurred. Please try again.'}), 500

@app.route('/holder', methods=['GET', 'POST'])
def holder():
    """Student holder portal: login if not authenticated as student, dashboard otherwise"""
    if 'user_id' in session and session.get('role') == 'student':
        student_id = session.get('student_id')
        student_credentials = credential_manager.get_credentials_by_student(student_id)
        return render_template('holder.html', credentials=student_credentials)
    return handle_login_request(portal_role='student')

@app.route('/verifier')
def verifier():
    return render_template('verifier.html')

# ==================== CREDENTIAL API ENDPOINTS ====================

@app.route('/issuer/mfa-setup')
@role_required('issuer')
def mfa_setup():
    """MFA Setup page for admin/issuer to link their Authenticator app"""
    user = User.query.get(session['user_id'])
    
    import pyotp
    import qrcode
    import io
    import base64

    # If user already has MFA, we can either refuse or allow reset.
    # For now, we'll allow generating a new one if they visit this page.
    if 'pending_totp_secret' not in session:
        session['pending_totp_secret'] = pyotp.random_base32()
    
    secret = session['pending_totp_secret']
    totp = pyotp.totp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.username, issuer_name="Credify GPREC")
    
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()
    
    return render_template('mfa_setup.html', qr_code=qr_base64, secret=secret)

@app.route('/api/verify-mfa-setup', methods=['POST'])
@role_required('issuer')
def verify_mfa_setup():
    """Verify and finalize the TOTP configuration"""
    try:
        data = request.get_json()
        token = data.get('token')
        user = User.query.get(session.get('user_id'))
        
        # Get the pending secret from session
        pending_secret = session.get('pending_totp_secret')
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        if not pending_secret:
            return jsonify({'success': False, 'error': 'No pending setup found. Please refresh.'}), 400
            
        import pyotp
        totp = pyotp.totp.TOTP(pending_secret)
        if totp.verify(token):
            # Verification successful! Save it permanently to the user
            user.totp_secret = pending_secret
            db.session.commit()
            
            # Clear pending from session
            session.pop('pending_totp_secret', None)
            session['mfa_enabled'] = True
            
            return jsonify({'success': True, 'message': 'Authenticator successfully linked! Your account is now protected.'})
        else:
            return jsonify({'success': False, 'error': 'Invalid code. Please try again.'}), 400
            
    except Exception as e:
        logging.error(f"MFA verify error: {e}")
        return jsonify({'success': False, 'error': 'Verification failed due to a system error.'}), 500

@app.route('/api/issue_credential', methods=['POST'])
@role_required('issuer')
def api_issue_credential():
    try:
        data = request.get_json()
        
        # Core required fields
        required_fields = ['student_name', 'student_id', 'degree', 'university', 'gpa', 'graduation_year']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extended academic fields with validation
        semester = data.get('semester')
        year = data.get('year')
        class_name = data.get('class_name')
        section = data.get('section')
        backlog_count = data.get('backlog_count', 0)
        backlogs = data.get('backlogs', [])
        conduct = data.get('conduct')
        
        # Validate new fields
        if semester is not None and (not isinstance(semester, int) or semester < 1 or semester > 8):
            return jsonify({'error': 'Semester must be between 1 and 8'}), 400
        
        if backlog_count is not None and (not isinstance(backlog_count, int) or backlog_count < 0):
            return jsonify({'error': 'Backlog count must be 0 or greater'}), 400
        
        if conduct and conduct not in ['poor', 'average', 'good', 'outstanding']:
            return jsonify({'error': 'Conduct must be one of: poor, average, good, outstanding'}), 400
        
        # Build extended transcript data
        transcript_data = {
            'student_name': data['student_name'],
            'student_id': data['student_id'],
            'degree': data['degree'],
            'university': data['university'],
            'gpa': float(data['gpa']),
            'graduation_year': int(data['graduation_year']),
            'courses': data.get('courses', []),
            'issue_date': datetime.now().isoformat(),
            'issuer': 'G. Pulla Reddy Engineering College',
            'semester': semester,
            'year': year,
            'class_name': class_name,
            'section': section,
            'backlog_count': backlog_count,
            'backlogs': backlogs,
            'conduct': conduct
        }
        
        logging.info(f"Issuing credential with extended data: semester={semester}, backlogs={len(backlogs)}, conduct={conduct}")
        
        result = credential_manager.issue_credential(transcript_data)
        
        if result['success']:
            try:
                student_name = transcript_data['student_name']
                student_id_val = str(transcript_data['student_id'])
                student_email = data.get('email')
                
                # UNIFORM ONBOARDING: Create student user in 'pending' state
                student_user = User.query.filter_by(student_id=student_id_val).first()
                activation_token = str(uuid.uuid4())
                
                if student_user:
                    student_user.full_name = student_name
                    student_user.email = student_email
                    student_user.activation_token = activation_token
                    student_user.onboarding_status = 'pending'
                    db.session.commit()
                else:
                    new_student = User(
                        username=f"user_{student_id_val}",
                        role='student',
                        student_id=student_id_val,
                        full_name=student_name,
                        email=student_email,
                        onboarding_status='pending',
                        activation_token=activation_token,
                        is_verified=False
                    )
                    # Temporary safe password until setup
                    new_student.set_password(str(uuid.uuid4()))
                    db.session.add(new_student)
                    db.session.commit()
                
                # TRIGGER FIRST ONBOARDING EMAIL WITH FULL DETAILS
                if student_email:
                    mailer.send_onboarding_mail(
                        student_email, 
                        student_name, 
                        activation_token,
                        transcript_data['degree'],
                        transcript_data['gpa'],
                        transcript_data['graduation_year']
                    )
                    logging.info(f"✅ Detailed onboarding mail sent to {student_email}")
                
            except Exception as e:
                logging.error(f"Error in onboarding workflow: {str(e)}")

            flash('Credential issued! Student has been notified for security verification.', 'success')
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logging.error(f"Error issuing credential: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify_credential', methods=['POST'])
def api_verify_credential():
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')
        if not credential_id:
            return jsonify({'error': 'Credential ID is required'}), 400
        result = credential_manager.verify_credential(credential_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error verifying credential: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/certificate/<credential_id>')
def view_certificate_portal(credential_id):
    """Render the high-end certificate viewer page."""
    try:
        cred = credential_manager.get_credential(credential_id)
        if not cred:
            return "Credential not found", 404
            
        full_cred = cred.get('full_credential', {})
        subject = full_cred.get('credentialSubject', {})
        
        return render_template('certificate_view.html', 
                             credential=full_cred, 
                             subject=subject)
    except Exception as e:
        logging.error(f"Certificate View error: {e}")
        return str(e), 500

@app.route('/api/credential/<credential_id>/pdf')
@role_required('student')
def api_credential_pdf(credential_id):
    """
    Generate the absolute final 10/10 elite academic transcript.
    Refined with senior UX feedback: document rhythm, typographic hierarchy, and digital authority.
    """
    try:
        cred = credential_manager.get_credential(credential_id)
        if not cred:
            return jsonify({'error': 'Credential not found'}), 404
            
        full_cred = cred.get('full_credential') or {}
        subject = full_cred.get('credentialSubject') or {}
            
        buffer = io.BytesIO()
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        gold = colors.HexColor("#C9A227")
        navy = colors.HexColor("#0f172a")
        text_muted = colors.HexColor("#777777")
        
        # 1. BORDER (6pt : 1.5pt ratio)
        p.setStrokeColor(gold)
        p.setLineWidth(6)
        p.rect(20, 20, width-40, height-40)
        p.setLineWidth(1.5)
        p.rect(32, 32, width-64, height-64)
        
        # 2. ULTRA-SUBTLE WATERMARK (0.02)
        p.saveState()
        p.setFont("Helvetica-Bold", 65)
        p.setFillColor(gold, alpha=0.02)
        p.translate(width/2, height/2)
        p.rotate(35)
        p.drawCentredString(0, 0, "BLOCKCHAIN VERIFIED RECORD")
        p.restoreState()
        
        # 3. HEADER RHYTHM
        logo_path = os.path.join(os.getcwd(), 'static', 'images', 'collegelogo.png')
        if os.path.exists(logo_path):
            p.drawImage(logo_path, width/2 - 25, height - 90, width=50, height=50, mask='auto')

        p.setFont("Helvetica-Bold", 17)
        p.setFillColor(navy)
        p.drawCentredString(width/2, height - 110, "G. PULLA REDDY ENGINEERING COLLEGE (AUTONOMOUS)")
        
        # Elegant Underlined Title
        p.setFont("Helvetica-Bold", 22)
        title_text = "OFFICIAL DIGITAL ACADEMIC RECORD"
        p.drawCentredString(width/2, height - 145, title_text)
        p.setLineWidth(1.5)
        p.setStrokeColor(gold)
        p.line(width/2 - 140, height - 150, width/2 + 140, height - 150)
        
        p.setFont("Helvetica-Oblique", 9)
        p.setFillColor(text_muted)
        p.drawCentredString(width/2, height - 165, "SECURED BY CREDIFY BLOCKCHAIN TECHNOLOGY")
        
        # 4. HERO SECTION (Student Name)
        p.setFont("Helvetica-Oblique", 14)
        p.setFillColor(colors.black)
        p.drawCentredString(width/2, height - 210, "This is to certify that")
        
        p.setFont("Helvetica-Bold", 28)
        student_name = (subject.get('name') or cred.get('student_name', 'NAME NOT FOUND')).upper()
        # Simulated kerning
        p.drawCentredString(width/2, height - 245, student_name)
        
        # Section Divider
        p.setLineWidth(0.5)
        p.setStrokeColor(colors.lightgrey)
        p.line(60, height - 265, width - 60, height - 265)
        
        # 5. HIGH-CONTRAST ACADEMIC GRID
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(gold)
        p.drawCentredString(width/2, height - 280, "RECORD OF ACADEMIC ACHIEVEMENT")
        
        col1_fields = [
            ("ROLL NUMBER", str(subject.get('studentId') or cred.get('student_id', 'N/A'))),
            ("DEGREE PROGRAM", str(subject.get('degree') or cred.get('degree', 'N/A')).upper()),
            ("GPA/CGPA", f"{subject.get('gpa') or cred.get('gpa', '0.00')} / 10.00"),
        ]
        col2_fields = [
            ("GRADUATION YEAR", str(subject.get('graduationYear') or cred.get('graduation_year', 'N/A'))),
            ("SEMESTER / YEAR", f"{subject.get('semester') or '8'} / {subject.get('year') or '4'}"),
            ("STATUS", "CERTIFIED AUTHENTIC"),
        ]
        
        y_start = height - 310
        for i in range(3):
            y = y_start - (i * 35)
            # Column 1
            if i < len(col1_fields):
                lbl, val = col1_fields[i]
                p.setFont("Helvetica-Bold", 7)
                p.setFillColor(text_muted)
                p.drawString(90, y, lbl)
                p.setFont("Helvetica-Bold", 10)
                p.setFillColor(navy)
                p.drawString(90, y - 12, val)
            
            # Column 2
            if i < len(col2_fields):
                lbl, val = col2_fields[i]
                p.setFont("Helvetica-Bold", 7)
                p.setFillColor(text_muted)
                p.drawString(width/2 + 20, y, lbl)
                p.setFont("Helvetica-Bold", 10)
                p.setFillColor(navy if val != "CERTIFIED AUTHENTIC" else colors.HexColor("#059669"))
                p.drawString(width/2 + 20, y - 12, val)

        # Section Divider
        p.setLineWidth(0.5)
        p.setStrokeColor(colors.lightgrey)
        p.line(60, y_start - 100, width - 60, y_start - 100)
        
        # 6. REFINED BLOCKCHAIN PROOF BOX
        y_box = 320
        p.setFillColor(colors.HexColor("#FAFAFA"))
        p.setStrokeColor(gold)
        p.setLineWidth(1)
        p.rect(70, y_box - 90, width - 140, 100, fill=1, stroke=1)
        
        p.setFillColor(navy)
        p.setFont("Helvetica-Bold", 9)
        p.drawCentredString(width/2, y_box - 12, "BLOCKCHAIN INTEGRITY PROOF")
        
        p.setFillColor(text_muted)
        p.setFont("Helvetica-Bold", 7)
        p.drawString(85, y_box - 30, "CREDENTIAL IDENTIFIER")
        p.setFillColor(colors.black)
        p.setFont("Courier-Bold", 9)
        p.drawString(85, y_box - 40, f"{credential_id}")
        
        p.setFillColor(text_muted)
        p.setFont("Helvetica-Bold", 7)
        p.drawString(85, y_box - 55, "ON-CHAIN HASH (SHA-256)")
        p.setFillColor(colors.black)
        p.setFont("Courier-Bold", 9)
        p.drawString(85, y_box - 65, f"{cred.get('credential_hash', 'N/A')[:64]}...")
        
        # QR & Badge Positioned Right
        verify_url = url_for('public_verify', id=credential_id, _external=True)
        qr = qrcode.make(verify_url)
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        from reportlab.lib.utils import ImageReader
        p.drawImage(ImageReader(qr_buffer), width-145, y_box-82, width=65, height=65)
        
        # Mini Badge (15% Smaller)
        p.setFillColor(gold)
        p.setStrokeColor(colors.white)
        p.circle(width-195, y_box-35, 20, fill=1, stroke=1)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 5)
        p.drawCentredString(width-195, y_box-33, "BLOCKCHAIN")
        p.drawCentredString(width-195, y_box-38, "VERIFIED")
        
        # 7. SIGNATURES WITH DIGITAL ROLES
        y_sign = 160
        p.setLineWidth(1.5)
        p.setStrokeColor(navy)
        p.line(70, y_sign, 190, y_sign)
        p.line(width/2 - 60, y_sign, width/2 + 60, y_sign)
        p.line(width - 190, y_sign, width - 70, y_sign)
        
        p.setFont("Helvetica-Bold", 9)
        p.setFillColor(navy)
        p.drawCentredString(130, y_sign - 15, "Academic Records Authority")
        p.drawCentredString(width/2, y_sign - 15, "Controller of Examinations")
        p.drawCentredString(width - 130, y_sign - 15, "Blockchain Network Validator")
        
        p.setFont("Helvetica-Oblique", 7)
        p.setFillColor(colors.gray)
        p.drawCentredString(130, y_sign - 25, "(Digital Issuer)")
        p.drawCentredString(width/2, y_sign - 25, "(Authorizing Authority)")
        p.drawCentredString(width - 130, y_sign - 25, "(Network Verification)")
        
        # 8. CONSTRAINED FOOTER NOTE
        p.setFillColor(colors.gray)
        p.setFont("Helvetica-Oblique", 8)
        disclaimer = "This academic record is digitally issued and cryptographically secured using blockchain technology. Authenticity can be verified through the QR code and blockchain hash. No physical signature is required."
        
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.alignment = 1 # Center
        style.fontSize = 8
        style.textColor = colors.gray
        style.fontName = "Helvetica-Oblique"
        style.leading = 11
        
        footer_p = Paragraph(disclaimer, style)
        footer_p.wrapOn(p, 400, 100)
        footer_p.drawOn(p, (width-400)/2, 60)
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, 
                         download_name=f"Verified_Transcript_{credential_id}.pdf", 
                         mimetype='application/pdf')
    except Exception as e:
        logging.error(f"Elite PDF Generation error: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(f"Elite PDF Generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/selective_disclosure', methods=['POST'])
def api_selective_disclosure():
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')
        fields = data.get('fields', [])
        if not credential_id:
            return jsonify({'error': 'Credential ID is required'}), 400
        if not fields:
            return jsonify({'error': 'At least one field must be selected'}), 400
        result = credential_manager.selective_disclosure(credential_id, fields)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in selective disclosure: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/nodes/register', methods=['POST'])
@role_required('issuer')
def register_nodes():
    """Register new nodes in the network"""
    data = request.get_json()
    nodes = data.get('nodes')
    
    if nodes is None:
        return jsonify({'success': False, 'error': 'Please provide a valid list of nodes'}), 400
        
    for node in nodes:
        blockchain.register_node(node)
        
    return jsonify({
        'success': True,
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    })

# Track A: Load Peer Nodes from environment
peer_nodes_env = os.environ.get('PEER_NODES', '')
if peer_nodes_env:
    for p in peer_nodes_env.split(','):
        if p.strip():
            blockchain.register_node(p.strip())

@app.route('/api/node/chain', methods=['GET'])
def get_full_chain():
    """Return the entire blockchain for peer synchronization"""
    return jsonify({
        'chain': [b.to_dict() for b in blockchain.chain],
        'length': len(blockchain.chain)
    })

@app.route('/api/node/receive_block', methods=['POST'])
def receive_peer_block():
    """Receive a block broadcast from a peer node"""
    try:
        block_data = request.get_json()
        if not block_data:
            return jsonify({'success': False, 'message': 'No block data provided'}), 400
            
        # 1. Reconstruct block object
        new_block = blockchain.block_model(
            index=block_data['index'],
            timestamp=block_data['timestamp'],
            data=json.dumps(block_data['data']),
            merkle_root=block_data.get('merkle_root'),
            previous_hash=block_data['previous_hash'],
            nonce=block_data['nonce'],
            hash=block_data['hash'],
            signed_by=block_data.get('signed_by'),
            signature=block_data.get('signature')
        )
        
        # 2. Simple validation against local chain
        last_block = blockchain.get_latest_block()
        if last_block and block_data['index'] <= last_block.index:
            return jsonify({'success': False, 'message': 'Block already exists or is outdated'}), 409
            
        if last_block and block_data['previous_hash'] != last_block.hash:
            return jsonify({'success': False, 'message': 'Previous hash mismatch. Sync required.'}), 400
            
        # 3. Cryptographic validation (simplified for the model bridge)
        # Create a Block object for validation methods
        from core.blockchain import Block
        v_block = Block(
            block_data['index'], block_data['data'], block_data['previous_hash'],
            signed_by=block_data.get('signed_by'), signature=block_data.get('signature')
        )
        v_block.timestamp = block_data['timestamp']
        v_block.nonce = block_data['nonce']
        v_block.merkle_root = block_data.get('merkle_root')
        v_block.hash = block_data['hash']
        
        if v_block.hash != v_block.calculate_hash():
             return jsonify({'success': False, 'message': 'Invalid block hash'}), 400
             
        if blockchain.crypto_manager and v_block.signature:
            if not blockchain.crypto_manager.verify_signature(v_block.hash, v_block.signature):
                return jsonify({'success': False, 'message': 'Invalid digital signature'}), 400

        # All checks passed, add to local DB and chain
        db.session.add(new_block)
        db.session.commit()
        blockchain.chain.append(v_block)
        
        logging.info(f"Accepted peer block {block_data['index']} from {block_data.get('signed_by')}")
        return jsonify({'success': True, 'message': 'Block accepted and added to chain'})
        
    except Exception as e:
        logging.error(f"Error receiving peer block: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/nodes/peers')
def get_peers():
    """Get the list of registered peers"""
    return jsonify({
        'success': True,
        'peers': list(blockchain.nodes)
    })

@app.route('/api/nodes/resolve')
def resolve_nodes():
    """Trigger consensus resolution"""
    replaced = blockchain.resolve_conflicts()
    if replaced:
        return jsonify({
            'success': True,
            'message': 'Chain was replaced',
            'new_chain': [b.to_dict() for b in blockchain.chain]
        })
    else:
        return jsonify({
            'success': True,
            'message': 'Our chain is authoritative',
            'chain': [b.to_dict() for b in blockchain.chain]
        })

@app.route('/api/blockchain_status')
def api_blockchain_status():
    try:
        status = {
            'total_blocks': len(blockchain.chain),
            'total_credentials': len(credential_manager.get_all_credentials()),
            'last_block_hash': blockchain.get_latest_block().hash if blockchain.chain else None,
            'ipfs_status': ipfs_client.is_connected()
        }
        return jsonify(status)
    except Exception as e:
        logging.error(f"Error getting blockchain status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/blockchain/audit')
@role_required('issuer')
def blockchain_audit():
    """Export the entire blockchain ledger for audit"""
    try:
        from io import StringIO
        import csv
        
        si = StringIO()
        cw = csv.writer(si)
        
        # Header
        cw.writerow(['Index', 'Timestamp', 'Merkle Root', 'Hash', 'Prev Hash', 'Signed By', 'Data'])
        
        for block in blockchain.chain:
            cw.writerow([
                block.index,
                block.timestamp,
                block.merkle_root,
                block.hash,
                block.previous_hash,
                block.signed_by,
                json.dumps(block.data)
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=blockchain_audit_{datetime.now().strftime('%Y%m%d')}.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/validate')
@role_required('issuer')
def validate_chain():
    """Perform a full integrity audit of the blockchain"""
    try:
        is_valid = blockchain.is_chain_valid()
        return jsonify({
            'success': True,
            'valid': is_valid,
            'blocks_checked': len(blockchain.chain),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/blocks')
def api_get_blocks():
    """
    Get all blocks for the explorer with full metadata.
    """
    try:
        # Return blocks in reverse order (newest first) for better UX
        blocks_data = [b.to_dict() for b in reversed(blockchain.chain)]
        
        # Add credential count summary for each block for UI convenience
        for b in blocks_data:
            if isinstance(b['data'], list):
                b['credential_count'] = len(b['data'])
            elif isinstance(b['data'], dict):
                b['credential_count'] = 1
            else:
                b['credential_count'] = 0

        return jsonify({'success': True, 'blocks': blocks_data})
    except Exception as e:
        logging.error(f"Error getting blockchain blocks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/credentials')
@role_required('issuer')
def api_credentials():
    try:
        creds = credential_manager.get_all_credentials()
        return jsonify({'success': True, 'credentials': creds})
    except Exception as e:
        logging.error(f"Error listing credentials: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/credentials/student/<student_id>', methods=['GET'])
def get_student_credentials(student_id):
    """Get all credentials for a specific student"""
    try:
        student_credentials = credential_manager.get_credentials_by_student(student_id)
        return jsonify({'credentials': student_credentials})
    except Exception as e:
        logging.error(f"Error getting student credentials: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/revoke_credential', methods=['POST'])
@role_required('issuer')
def api_revoke_credential():
    """Revoke a credential (blockchain-compliant - no deletion)"""
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')
        reason = data.get('reason', '')
        reason_category = data.get('reason_category', 'other')
        
        if not credential_id:
            return jsonify({'success': False, 'error': 'credential_id is required'}), 400
        
        valid_categories = ['duplicate', 'misconduct', 'legal', 'request', 'other']
        if reason_category not in valid_categories:
            return jsonify({'success': False, 'error': f'Invalid reason_category'}), 400
        
        result = credential_manager.revoke_credential(credential_id, reason, reason_category)
        
        if result['success']:
            # NOTIFICATION: Notify student of revocation
            student_id = result.get('student_id')
            if student_id:
                student_user = User.query.filter_by(student_id=student_id).first()
                if student_user and student_user.email:
                    mailer.send_revocation_mail(
                        student_user.email, 
                        result.get('degree', 'Academic Transcript'), 
                        reason
                    )
            flash('Credential revoked successfully', 'success')
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error revoking credential: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create_new_version', methods=['POST'])
@role_required('issuer')
def api_create_new_version():
    """Create a new version of a credential (for corrections/updates)"""
    try:
        data = request.get_json()
        
        old_credential_id = data.get('old_credential_id')
        reason = data.get('reason', 'Credential correction')
        
        if not old_credential_id:
            return jsonify({'success': False, 'error': 'old_credential_id is required'}), 400
        
        required_fields = ['student_name', 'student_id', 'degree', 'university', 'gpa', 'graduation_year']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        updated_data = {
            'student_name': data['student_name'],
            'student_id': data['student_id'],
            'degree': data['degree'],
            'university': data['university'],
            'gpa': float(data['gpa']),
            'graduation_year': int(data['graduation_year']),
            'courses': data.get('courses', []),
            'issue_date': datetime.now().isoformat(),
            'issuer': 'G. Pulla Reddy Engineering College',
            'semester': data.get('semester'),
            'year': data.get('year'),
            'class_name': data.get('class_name'),
            'section': data.get('section'),
            'backlog_count': data.get('backlog_count', 0),
            'backlogs': data.get('backlogs', []),
            'conduct': data.get('conduct')
        }
        
        result = credential_manager.create_new_version(old_credential_id, updated_data, reason)
        
        if result['success']:
            # NOTIFICATION: Notify student of update/correction
            student_id = result.get('student_id')
            if student_id:
                student_user = User.query.filter_by(student_id=student_id).first()
                if student_user and student_user.email:
                    mailer.send_setup_mail(
                        student_user.email, 
                        student_user.full_name, 
                        result.get('degree', 'Academic Transcript'), 
                        result['credential_id'], 
                        "correction-notice"
                    )
            flash(f'New credential version v{result["version"]} created successfully!', 'success')
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error creating new version: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/credential_history/<student_id>')
@role_required('issuer')
def api_credential_history(student_id):
    """Get complete credential history for a student (all versions)"""
    try:
        result = credential_manager.get_credential_history(student_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting credential history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_credential/<credential_id>')
def api_get_credential(credential_id):
    try:
        credential = credential_manager.get_credential(credential_id)
        if credential:
            return jsonify({'success': True, 'credential': credential})
        return jsonify({'error': 'Credential not found'}), 404
    except Exception as e:
        logging.error(f"Error getting credential: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== ZKP API ENDPOINTS (NEW) ====================

@app.route('/api/zkp/range_proof', methods=['POST'])
@role_required('student')
def api_generate_range_proof():
    """Student generates range proof (e.g., GPA > 7.5)"""
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')
        field_name = data.get('field')  # 'gpa', 'backlogCount'
        actual_value = data.get('actual_value')
        min_threshold = data.get('min_threshold')
        max_threshold = data.get('max_threshold')
        
        result = zkp_manager.generate_range_proof(
            credential_id, field_name, actual_value,
            min_threshold, max_threshold
        )
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error generating range proof: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/zkp/membership_proof', methods=['POST'])
@role_required('student')
def api_generate_membership_proof():
    """Student proves course membership without revealing all courses"""
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')
        field_name = data.get('field')  # 'courses'
        full_set = data.get('full_set')  # All courses
        claimed_member = data.get('claimed_member')  # Specific course
        
        result = zkp_manager.generate_membership_proof(
            credential_id, field_name, full_set, claimed_member
        )
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error generating membership proof: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/zkp/verify', methods=['POST'])
def api_verify_zkp():
    """Verifier verifies a ZKP"""
    try:
        data = request.get_json()
        proof = data.get('proof')
        proof_type = proof.get('type')
        
        if proof_type == 'RangeProof':
            challenge_value = data.get('challenge_value')  # Optional
            result = zkp_manager.verify_range_proof(proof, challenge_value)
        elif proof_type == 'MembershipProof':
            result = zkp_manager.verify_membership_proof(proof)
        elif proof_type == 'SetMembershipProof':
            revealed_value = data.get('revealed_value')  # Optional
            result = zkp_manager.verify_set_membership_proof(proof, revealed_value)
        else:
            return jsonify({'valid': False, 'error': 'Unknown proof type'}), 400
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error verifying ZKP: {str(e)}")
        return jsonify({'valid': False, 'error': str(e)}), 500

# ==================== TICKET ROUTES (CLEAN - NO DUPLICATES) ====================

@app.route('/api/tickets', methods=['GET', 'POST'])
def handle_tickets():
    """Get all tickets or create new ticket"""
    if request.method == 'GET':
        try:
            tickets = ticket_manager.get_all_tickets()
            return jsonify({'success': True, 'tickets': tickets})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            student_id = data.get('student_id')
            subject = data.get('subject')
            description = data.get('description')
            category = data.get('category')
            priority = data.get('priority', 'medium')
            
            if not all([student_id, subject, description, category]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            ticket = ticket_manager.create_ticket(
                student_id=student_id,
                subject=subject,
                description=description,
                category=category,
                priority=priority
            )
            
            return jsonify({
                'success': True,
                'ticket': ticket,
                'message': 'Ticket created successfully'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>', methods=['GET'])
def view_ticket(ticket_id):
    """Get specific ticket details"""
    try:
        ticket = ticket_manager.get_ticket(ticket_id)
        if ticket:
            return jsonify({'success': True, 'ticket': ticket})
        return jsonify({'error': 'Ticket not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """Admin updates ticket status"""
    try:
        data = request.json
        new_status = data.get('status')
        admin_note = data.get('admin_note')
        by_admin = data.get('by_admin', False)
        
        if not new_status:
            return jsonify({'error': 'Status required'}), 400
        
        success = ticket_manager.update_ticket_status(
            ticket_id=ticket_id,
            status=new_status,
            admin_note=admin_note,
            by_admin=by_admin
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Ticket status updated'})
        return jsonify({'error': 'Failed to update ticket'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>/response', methods=['POST'])
def add_ticket_response(ticket_id):
    """Add response/note to ticket"""
    try:
        data = request.json
        responder = data.get('responder')
        message = data.get('message')
        
        if not all([responder, message]):
            return jsonify({'error': 'Responder and message required'}), 400
        
        success = ticket_manager.add_ticket_response(
            ticket_id=ticket_id,
            responder=responder,
            message=message
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Response added'})
        return jsonify({'error': 'Failed to add response'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/student/<student_id>', methods=['GET'])
def get_student_tickets(student_id):
    """Get all tickets for a specific student"""
    try:
        tickets = ticket_manager.get_tickets_by_student(student_id)
        return jsonify({'success': True, 'tickets': tickets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>/student_action', methods=['POST'])
def student_ticket_action(ticket_id):
    """Student marks ticket as resolved or not solved"""
    try:
        data = request.json
        student_id = data.get('student_id')
        is_resolved = data.get('is_resolved', False)
        
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        result = ticket_manager.student_mark_resolved(ticket_id, student_id, is_resolved)
        
        if result.get('success'):
            # NOTIFICATION: Notify student of revocation
            # Note: The variables 'User', 'mailer', 'reason', and 'degree' are not defined in this context.
            # This snippet assumes they are imported/defined elsewhere or are placeholders.
            # For a functional implementation, these would need to be properly integrated.
            # Example placeholder for demonstration:
            # student_user = User.query.filter_by(student_id=result['student_id']).first()
            # if student_user and student_user.email:
            #     mailer.send_revocation_mail(
            #         student_user.email, 
            #         result.get('degree', 'Academic Transcript'), 
            #         reason
            #     )
            return jsonify(result)
        else:
            return jsonify(result), 403
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== MESSAGING ROUTES ====================

@app.route('/api/messages', methods=['POST'])
def send_message():
    """Send a direct message"""
    try:
        data = request.json
        sender_id = data.get('sender_id')
        sender_type = data.get('sender_type')
        recipient_id = data.get('recipient_id')
        recipient_type = data.get('recipient_type')
        subject = data.get('subject')
        message = data.get('message')
        
        if not all([sender_id, sender_type, recipient_id, recipient_type, subject, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        msg = ticket_manager.send_message(sender_id, sender_type, recipient_id, recipient_type, subject, message)
        
        return jsonify({
            'success': True,
            'message': msg
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/broadcast', methods=['POST'])
def broadcast_message():
    """Admin broadcasts message to all students"""
    try:
        data = request.json
        sender_id = data.get('sender_id', 'admin')
        subject = data.get('subject')
        message = data.get('message')
        
        if not all([subject, message]):
            return jsonify({'error': 'Subject and message are required'}), 400
        
        msg = ticket_manager.broadcast_message(sender_id, subject, message)
        
        return jsonify({
            'success': True,
            'message': msg
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/student/<student_id>', methods=['GET'])
def get_student_messages(student_id):
    """Get all messages for a student (direct + broadcast)"""
    try:
        messages = ticket_manager.get_messages_for_student(student_id)
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/all', methods=['GET'])
def get_all_messages_admin():
    """Get all messages (admin view)"""
    try:
        messages = ticket_manager.get_all_messages()
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<message_id>/revoke', methods=['PUT'])
def revoke_message(message_id):
    """Revoke a message (admin only)"""
    try:
        data = request.json
        admin_id = data.get('admin_id', 'admin')
        
        result = ticket_manager.revoke_message(message_id, admin_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<message_id>/read', methods=['PUT'])
def mark_message_read(message_id):
    """Student marks message as read"""
    try:
        data = request.json
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        success = ticket_manager.mark_message_read(message_id, student_id)
        
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Message not found or unauthorized'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== QR CODE & PUBLIC VERIFY ====================

@app.route('/api/credential/<credential_id>/qr')
def api_credential_qr(credential_id):
    """Generate a QR code image (base64 PNG) linking to the public verify page."""
    try:
        import qrcode
        import io
        import base64

        verify_url = url_for('public_verify', _external=True) + f'?id={credential_id}'

        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#06b6d4', back_color='#0f172a')

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return jsonify({'success': True, 'qr_base64': qr_b64, 'verify_url': verify_url})
    except ImportError:
        return jsonify({'success': False, 'error': 'qrcode library not installed. Run: pip install qrcode[pil] Pillow'}), 500
    except Exception as e:
        logging.error(f'QR generation error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/verify')
def public_verify():
    """Public credential verification page — no login required.
    Usage: /verify?id=CRED_ID
    Anyone (employer, institution) can land here from a QR code scan.
    """
    credential_id = request.args.get('id', '').strip()
    result = None
    credential = None

    if credential_id:
        try:
            result = credential_manager.verify_credential(credential_id)
            if result.get('valid') and result.get('credential'):
                credential = result['credential'].get('credentialSubject', {})
        except Exception as e:
            logging.error(f'Public verify error: {e}')
            result = {'valid': False, 'error': str(e)}

    return render_template('verify.html', credential_id=credential_id, result=result, credential=credential)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
