import os
import logging
import base64
import re
import hmac
import hashlib
import gzip
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

# Optionally load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.debug('Loaded environment variables from .env')
except Exception:
    logging.debug('python-dotenv not available; skipping .env load')

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, make_response
from flask_cors import CORS
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
from core.zkp_manager import ZKPManager  #  NEW: ZKP Import
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
from qrcode.constants import ERROR_CORRECT_L
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from PyPDF2 import PdfReader, PdfWriter
from flask import send_file

# FIXED: Flask app with ROOT-LEVEL template/static paths
app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Allow external verifier frontends (e.g., GitHub Pages/mobile web apps) to call public APIs.
cors_origins = os.environ.get("CORS_ORIGINS", "*")
CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=False)


def _qr_signing_key():
    """Derive a stable signing key for QR secret payloads."""
    return (os.environ.get("QR_SECRET_KEY") or app.secret_key or "credify-qr-secret").encode("utf-8")


def _generate_qr_secret_token(credential_id, payload_hash=None):
    """Create tamper-evident token embedded inside QR URLs for qr-web-app use."""
    issued_ts = int(datetime.utcnow().timestamp())
    payload = {
        "cid": credential_id,
        "ts": issued_ts,
        "v": 2,
        "iss": "did:edu:gprec",
    }
    if payload_hash:
        payload["pd"] = payload_hash

    # Primary format: JWS (offline verifiable using issuer public key).
    signed_jws = crypto_manager.sign_jws(payload)
    if signed_jws:
        return signed_jws

    # Legacy fallback (kept for resiliency if signing fails unexpectedly).
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(_qr_signing_key(), payload_json.encode("utf-8"), digestmod="sha256").hexdigest()
    return f"{payload_b64}.{sig}"


def _verify_qr_secret_token(token, expected_cid=None, expected_qd=None):
    """Validate token integrity and return parsed payload for trusted QR disclosures."""
    try:
        if not token or "." not in token:
            return None

        payload = None
        # New format: JWS compact token header.payload.signature
        if token.count(".") == 2:
            valid, parsed_payload = crypto_manager.verify_jws(token)
            if valid and isinstance(parsed_payload, dict):
                payload = parsed_payload
        else:
            # Legacy format: payload.signature (HMAC)
            payload_b64, provided_sig = token.split(".", 1)
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
            expected_sig = hmac.new(_qr_signing_key(), payload_json.encode("utf-8"), digestmod="sha256").hexdigest()
            if hmac.compare_digest(expected_sig, provided_sig):
                payload = json.loads(payload_json)

        if not payload or not payload.get("cid"):
            return None

        if expected_cid and str(payload.get("cid")) != str(expected_cid):
            return None

        # If qd is provided, bind token to payload digest (for v2 tokens).
        if expected_qd and payload.get("pd"):
            qd_hash = _hash_qr_hidden_payload(expected_qd)
            if not qd_hash or qd_hash != payload.get("pd"):
                return None

        return payload
    except Exception:
        return None


def _generate_qr_hidden_payload(credential_id):
    """Create an offline-decodable QR payload with credential details for qr-web-app."""
    cred = credential_manager.get_credential(credential_id)
    if not cred:
        return None

    full_cred = cred.get('full_credential') or {}
    subject = full_cred.get('credentialSubject') or {}

    payload = {
        'v': 1,
        'cid': credential_id,
        'name': subject.get('name'),
        'studentId': subject.get('studentId'),
        'degree': subject.get('degree'),
        'department': subject.get('department'),
        'studentStatus': subject.get('studentStatus'),
        'college': subject.get('college'),
        'university': subject.get('university'),
        'cgpa': subject.get('cgpa') or subject.get('gpa'),
        'graduationYear': subject.get('graduationYear'),
        'batch': subject.get('batch'),
        'conduct': subject.get('conduct'),
        'backlogCount': subject.get('backlogCount'),
        'courses': subject.get('courses') or [],
        'backlogs': subject.get('backlogs') or [],
        'issueDate': subject.get('issueDate'),
        'semester': subject.get('semester'),
        'year': subject.get('year'),
        'section': subject.get('section'),
        'ipfsCid': cred.get('ipfs_cid'),
    }

    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    # Compress payload to reduce QR density and improve phone scan reliability.
    payload_bytes = gzip.compress(payload_json.encode('utf-8'), compresslevel=9)
    return base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')


def _hash_qr_hidden_payload(qr_data):
    """Hash base64url-decoded hidden payload for token-payload binding."""
    if not qr_data:
        return None
    padded = qr_data + "=" * (-len(qr_data) % 4)
    payload_bytes = base64.urlsafe_b64decode(padded.encode("utf-8"))

    # Backward-compatible decode: old QR stored raw JSON; new QR stores gzip-compressed JSON.
    if payload_bytes[:2] == b"\x1f\x8b":
        payload_json = gzip.decompress(payload_bytes).decode("utf-8")
    else:
        payload_json = payload_bytes.decode("utf-8")

    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def _build_verify_url(credential_id):
    """Build the canonical verify URL used by all QR generation paths."""
    qr_data = _generate_qr_hidden_payload(credential_id)
    qr_token = _generate_qr_secret_token(credential_id, _hash_qr_hidden_payload(qr_data))
    verifier_base_url = (
        os.environ.get("QR_VERIFIER_BASE_URL")
        or "https://udaycodespace.github.io/credify-verify/result.html"
    ).strip()

    if not verifier_base_url:
        verifier_base_url = url_for('public_verify', _external=True)

    parsed = urlsplit(verifier_base_url)
    existing_query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    existing_query.update({
        "id": credential_id,
        "qk": qr_token,
    })
    if qr_data:
        existing_query["qd"] = qr_data

    verify_url = urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path or "/",
        urlencode(existing_query),
        parsed.fragment,
    ))
    return {
        'verify_url': verify_url,
        'qr_token': qr_token,
        'qr_data': qr_data,
    }


def _apply_no_cache_headers(response):
    """Prevent stale certificate/PDF responses from being reused by the browser."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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
zkp_manager = ZKPManager(crypto_manager)  #  NEW: Initialize ZKP Manager

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
                flash(f' Access Denied: This is the {portal_name} portal. Please login with a {portal_role} account.', 'danger')
                return render_template('login.html', portal=portal_role)

            # 1. Standard Password Check for all roles (Base Auth)
            if not user.check_password(password):
                flash(' Authentication failed. Invalid username or credentials.', 'danger')
                return render_template('login.html', portal=portal_role)

            # 2. MFA Requirement Logic for Issuers (Step 2 Auth)
            if user.role == 'issuer':
                if not mfa_token:
                    # Password is correct! Now generate & send Email OTP
                    import secrets
                    import string
                    from datetime import timedelta
                    
                    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
                    user.mfa_email_code = otp
                    user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=10)
                    db.session.commit()
                    
                    # Send to User's specific email (or requested debug email)
                    target_email = "udaysomapuram@gmail.com" # As per user requirement
                    masked_email = target_email[:2] + "***" + "@" + target_email.split('@')[1][:5] + "***.com"
                    try:
                        mailer.send_security_otp(
                            to_email=target_email,
                            full_name=user.full_name,
                            otp=otp
                        )
                        flash(f' MFA_CHALLENGE: Enter the security code sent to {masked_email}.', 'info')
                    except Exception as e:
                        logging.error(f"MFA Email failed: {e}")
                        flash(' MFA_CHALLENGE: Email notification failed, but code generated for verification.', 'warning')
                    
                    return render_template('login.html', show_mfa=True, mfa_username=username, mfa_password=password, portal=portal_role, masked_email=masked_email)
                
                # Verify Step 2 MFA token (Email OTP only)
                mfa_valid = False
                if user.mfa_email_code == mfa_token and user.mfa_code_expires > datetime.utcnow():
                    mfa_valid = True
                    user.mfa_email_code = None
                    db.session.commit()
                
                if not mfa_valid:
                    flash(' Access Denied. Invalid or expired security code.', 'danger')
                    return render_template('login.html', show_mfa=True, mfa_username=username, mfa_password=password, portal=portal_role)

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
            flash(' Authentication failed. Invalid username or password.', 'danger')
    
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
@app.route('/api/system/reset/request', methods=['POST'])
@role_required('issuer')
def api_system_reset_request():
    """ADMIN ONLY: Request a system reset OTP"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        import secrets
        import string
        from datetime import timedelta
        
        otp = ''.join(secrets.choice(string.digits) for _ in range(6))
        user.mfa_email_code = otp
        user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        
        target_email = "udaysomapuram@gmail.com"
        try:
            mailer.send_email(
                to_email=target_email,
                subject=" CRITICAL: System Reset Initiation Code",
                body=f"SYSTEM RESET AUTHORIZATION REQUIRED\n\nHello {user.full_name},\n\nA request has been made to permanently RESET the Credify System.\nThis action will delete ALL credentials, block records, and USER ACCOUNTS.\n\nYOUR AUTHORIZATION CODE: {otp}\n\nThis code expires in 15 minutes.\nIf you did NOT initiate this, please secure your account immediately.\n\nSecurely yours,\nCredify Security Engine"
            )
            return jsonify({'success': True, 'message': 'Reset authorization code sent to registered email.'})
        except Exception as e:
            logging.error(f"Reset OTP Email failed: {e}")
            return jsonify({'success': False, 'error': 'Failed to send authorization email.'}), 500
            
    except Exception as e:
        logging.error(f"System reset request error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/reset', methods=['POST'])
@role_required('issuer')
def api_system_reset():
    """ADMIN ONLY: Reset entire system - database, JSON files, blockchain"""
    try:
        data = request.get_json()
        confirmation = data.get('confirmation')
        otp = data.get('otp')
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)

        # 1. Verification Logic
        if confirmation != 'RESET_EVERYTHING':
            return jsonify({'success': False, 'error': 'Invalid confirmation text.'}), 400
            
        # [Test Bypass] Allow reset without OTP during automated testing
        is_testing = app.config.get('TESTING', False)
        
        if not is_testing:
            if not otp:
                return jsonify({'success': False, 'error': 'Authorization code required.'}), 400
                
            if user.mfa_email_code != otp or user.mfa_code_expires < datetime.utcnow():
                return jsonify({'success': False, 'error': 'Invalid or expired authorization code.'}), 400

        # Clear the OTP immediately after use
        user.mfa_email_code = None
        db.session.commit()

        # 2. Gather Comprehensive Data for Report
        all_creds = credential_manager.get_all_credentials()
        all_students = User.query.filter_by(role='student').all()
        all_admins = User.query.filter_by(role='issuer').all()
        all_verifiers = User.query.filter_by(role='verifier').all()
        all_tickets = ticket_manager.get_all_tickets()
        all_messages = ticket_manager.get_all_messages()
        
        stats = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'issuer': user.full_name,
            'credentials': len(all_creds),
            'students': len(all_students),
            'admins': len(all_admins),
            'verifiers': len(all_verifiers),
            'tickets': len(all_tickets) if isinstance(all_tickets, list) else len(all_tickets.values()) if isinstance(all_tickets, dict) else 0,
            'messages': len(all_messages) if isinstance(all_messages, list) else len(all_messages.values()) if isinstance(all_messages, dict) else 0,
            'blocks': len(blockchain.chain)
        }

        # 3. Generate Comprehensive PDF Report
        report_buffer = io.BytesIO()
        c = canvas.Canvas(report_buffer, pagesize=letter)
        y = 10.5 * inch
        
        def new_page():
            nonlocal y
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 10.5 * inch
        
        def write_line(text, font="Helvetica", size=10, indent=1):
            nonlocal y
            if y < 1 * inch:
                new_page()
            c.setFont(font, size)
            c.drawString(indent * inch, y, text)
            y -= size * 1.5 / 72 * inch + 2
        
        # Page 1: Header + Summary
        c.setFont("Helvetica-Bold", 18)
        c.drawString(1*inch, y, "CREDIFY SYSTEM RESET REPORT")
        y -= 0.4 * inch
        write_line(f"Date: {stats['timestamp']}", "Helvetica", 11)
        write_line(f"Authorized By: {stats['issuer']}", "Helvetica", 11)
        y -= 0.2 * inch
        c.line(1*inch, y + 0.1*inch, 7.5*inch, y + 0.1*inch)
        y -= 0.3 * inch
        
        write_line("DELETED ASSETS SUMMARY:", "Helvetica-Bold", 12)
        write_line(f"  Verified Credentials: {stats['credentials']}", indent=1.3)
        write_line(f"  Student Accounts: {stats['students']}", indent=1.3)
        write_line(f"  Admin Accounts: {stats['admins']}", indent=1.3)
        write_line(f"  Verifier Accounts: {stats['verifiers']}", indent=1.3)
        write_line(f"  Support Tickets: {stats['tickets']}", indent=1.3)
        write_line(f"  Messages: {stats['messages']}", indent=1.3)
        write_line(f"  Blockchain Depth: {stats['blocks']} blocks", indent=1.3)
        
        # Page 2+: Student Details
        y -= 0.3 * inch
        write_line("STUDENT ACCOUNTS:", "Helvetica-Bold", 13)
        if all_students:
            for i, student in enumerate(all_students, 1):
                write_line(f"  #{i}. {student.full_name or 'N/A'} | @{student.username} | {student.email or 'N/A'}", indent=1.2)
                write_line(f"       Status: {student.onboarding_status or 'unknown'} | Verified: {student.is_verified}", "Helvetica", 9, indent=1.2)
        else:
            write_line("  (No student accounts found)", "Helvetica-Oblique")
        
        # Credential Details
        y -= 0.3 * inch
        write_line("ALL CREDENTIALS:", "Helvetica-Bold", 13)
        if all_creds:
            for i, cred in enumerate(all_creds, 1):
                student_name = cred.get('student_name', 'Unknown')
                student_id = cred.get('student_id', 'N/A')
                degree = cred.get('degree', 'N/A')
                status = cred.get('status', 'unknown')
                version = cred.get('version', '1')
                cred_id = cred.get('credential_id', 'N/A')[:20]
                write_line(f"  #{i}. {student_name} ({student_id}) - {degree}", indent=1.2)
                write_line(f"       ID: {cred_id}... | Status: {status} | Version: {version}", "Helvetica", 9, indent=1.2)
        else:
            write_line("  (No credentials found)", "Helvetica-Oblique")
        
        # Tickets
        y -= 0.3 * inch
        write_line("SUPPORT TICKETS:", "Helvetica-Bold", 13)
        ticket_list = all_tickets if isinstance(all_tickets, list) else list(all_tickets.values()) if isinstance(all_tickets, dict) else []
        if ticket_list:
            for i, ticket in enumerate(ticket_list, 1):
                if isinstance(ticket, dict):
                    subj = ticket.get('subject', 'No Subject')
                    status = ticket.get('status', 'unknown')
                    write_line(f"  #{i}. {subj} [{status}]", indent=1.2)
        else:
            write_line("  (No tickets found)", "Helvetica-Oblique")
        
        # Messages
        y -= 0.3 * inch
        write_line("SYSTEM MESSAGES:", "Helvetica-Bold", 13)
        msg_list = all_messages if isinstance(all_messages, list) else list(all_messages.values()) if isinstance(all_messages, dict) else []
        if msg_list:
            for i, msg in enumerate(msg_list, 1):
                if isinstance(msg, dict):
                    subj = msg.get('subject', 'No Subject')
                    to = msg.get('to', 'N/A')
                    write_line(f"  #{i}. To: {to} | {subj}", indent=1.2)
        else:
            write_line("  (No messages found)", "Helvetica-Oblique")
        
        # Final note
        y -= 0.4 * inch
        write_line("Post-reset, the system will be reverted to its genesis state.", "Helvetica-Oblique", 9)
        write_line("Default admin accounts will be recreated automatically.", "Helvetica-Oblique", 9)
        
        c.showPage()
        c.save()
        
        # 4. Password Protect PDF
        report_buffer.seek(0)
        reader = PdfReader(report_buffer)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        writer.encrypt(otp) # Use the same OTP as password
        
        protected_buffer = io.BytesIO()
        writer.write(protected_buffer)
        protected_buffer.seek(0)
        
        # 5. Send Report Email
        target_email = "udaysomapuram@gmail.com"
        try:
            mailer.send_nuke_report(
                to_email=target_email,
                stats=stats,
                pdf_data=protected_buffer.getvalue()
            )
            logging.info(f"Nuke report sent to {target_email} with PDF")
        except Exception as e:
            logging.error(f"Failed to send/attach nuke report: {e}")
        
        # 6. Execute actual cleanup
        # Reset JSON files
        from core import DATA_DIR
        DATA_DIR.mkdir(exist_ok=True)
        
        # Reset credentials registry
        creds_file = DATA_DIR / 'credentials_registry.json'
        with open(creds_file, 'w') as f:
            json.dump({}, f, indent=2)
            
        # Reset blockchain
        try:
            BlockRecord.query.delete()
            db.session.commit()
            blockchain.chain = []
            blockchain.create_genesis_block()
        except Exception as e:
            logging.error(f"Error clearing BlockRecord: {e}")
            
        # IPFS/Tickets/Messages JSON
        for filename in ['ipfs_storage.json', 'tickets.json', 'messages.json']:
            with open(DATA_DIR / filename, 'w') as f:
                json.dump([] if 'json' in filename and filename != 'ipfs_storage.json' else {}, f, indent=2)
        
        # Database cleanup - WIPE EVERYTHING (All users included)
        User.query.delete()
        db.session.commit()
        
        # Recreate the default users so the admin can log in again
        from app.models import create_default_users
        create_default_users()
        
        # Clear in-memory
        credential_manager.credentials_registry = {}
        ticket_manager.tickets = {}
        ticket_manager.messages = {}
        
        # Logout FORCEFULLY
        session.clear()
        
        return jsonify({
            'success': True, 
            'message': 'SYSTEM NUKED. All users, data, and blocks deleted. PDF report sent to your email. You have been logged out.'
        })
        
    except Exception as e:
        logging.error(f"System reset error: {e}")
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

        # Revoke old password  old login no longer works after reset is requested
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

        # Mail failed  restore a placeholder so the account isn't brick-walled
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
    """Finalize credential reset  save new username AND new password"""
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

        def _split_list(value):
            """Normalize comma/newline separated values into a clean list."""
            if value is None:
                return []
            if isinstance(value, list):
                items = value
            else:
                text = str(value).replace('\n', ',')
                items = text.split(',')
            return [str(item).strip() for item in items if str(item).strip()]

        def _is_empty_backlog_token(token):
            return token.strip().upper() in {'N/A', 'NIL', 'NILL', 'NONE', '0', 'O', ''}
        
        # Core required fields
        required_fields = ['student_name', 'student_id', 'degree', 'department', 'student_status', 'college', 'university', 'issue_date']
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Additional validations
        if data.get('student_status') == 'graduated' and not data.get('graduation_year'):
            return jsonify({'error': 'Graduation year is required for graduated students'}), 400
            
        cgpa = data.get('cgpa')
        if cgpa is not None:
            try:
                cgpa = float(cgpa)
            except ValueError:
                return jsonify({'error': 'CGPA must be a valid number'}), 400
            if cgpa < 0 or cgpa > 10:
                return jsonify({'error': 'CGPA must be between 0.00 and 10.00'}), 400
        
        raw_backlogs = _split_list(data.get('backlogs', []))
        clean_backlogs = [c for c in raw_backlogs if not _is_empty_backlog_token(c)]
        raw_courses = _split_list(data.get('courses', []))
        clean_courses = [c for c in raw_courses if str(c).strip().upper() not in ['N/A', 'NILL', 'NIL', 'NONE', '']]

        backlog_count_val = int(data.get('backlog_count') or 0)
        if backlog_count_val < 0:
            backlog_count_val = 0
        if clean_backlogs:
            backlog_count_val = len(clean_backlogs)
        
        grad_year = data.get('graduation_year')
        if not grad_year and data.get('batch') and '-' in data.get('batch'):
            grad_year = data.get('batch').split('-')[1].strip()

        # For pursuing students, derive expected graduation year from batch to avoid null/N/A in certificates.
        if data.get('student_status') == 'pursuing' and not grad_year and data.get('batch') and '-' in data.get('batch'):
            grad_year = data.get('batch').split('-')[1].strip()
            
        # Build extended transcript data
        transcript_data = {
            'student_name': data['student_name'].strip(),
            'student_id': data['student_id'].strip().upper(),
            'degree': data['degree'],
            'department': data['department'],
            'student_status': data['student_status'],
            'semester': data.get('semester'),
            'year': data.get('year'),
            'graduation_year': grad_year,
            'batch': data.get('batch'),
            'section': data.get('section'),
            'college': data.get('college'),
            'university': data.get('university'),
            'cgpa': cgpa,
            'gpa': cgpa,  # Backward compatibility
            'conduct': data.get('conduct', 'N/A'),
            'backlog_count': backlog_count_val,
            'courses': clean_courses,
            'backlogs': clean_backlogs,
            'issued_by': data.get('issued_by', 'G. Pulla Reddy Engineering College'),
            'issue_date': data['issue_date'],
            'issuer': data.get('issued_by', 'G. Pulla Reddy Engineering College') # Backward compatibility
        }
        
        logging.info(f"Issuing credential with data: status={data['student_status']}, department={data['department']}")
        
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
                
                # TRIGGER FIRST ONBOARDING EMAIL WITH FULL DETAILS (ASYNCHRONOUS)
                if student_email:
                    import threading
                    def send_async():
                        with app.app_context():
                            try:
                                mailer.send_onboarding_mail(
                                    student_email, 
                                    student_name, 
                                    activation_token,
                                    transcript_data['degree'],
                                    transcript_data.get('cgpa'),
                                    transcript_data.get('graduation_year', 'N/A')
                                )
                                logging.info(f" Detailed onboarding mail sent to {student_email}")
                            except Exception as em:
                                logging.error(f"Async mail error: {em}")
                    
                    threading.Thread(target=send_async, daemon=True).start()
                
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
        privacy_mode = data.get('privacy_mode', False) # If true, don't return full data
        
        if not credential_id:
            return jsonify({'error': 'Credential ID is required'}), 400
            
        result = credential_manager.verify_credential(credential_id)
        
        #  PRIVACY PROTECTION: Strip sensitive data if in privacy_mode
        if privacy_mode and result.get('valid'):
            # Only return essential proof info, not the actual student data
            stripped_result = {
                'valid': result['valid'],
                'status': result['status'],
                'verification_details': result.get('verification_details'),
                'registry_entry': {
                    'issuer_id': result['registry_entry'].get('issuer_id'),
                    'issue_date': result['registry_entry'].get('issue_date'),
                    'status': result['registry_entry'].get('status')
                }
            }
            return jsonify(stripped_result)
            
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error verifying credential: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify_blind_disclosure', methods=['POST'])
def api_verify_blind_disclosure():
    """
    ELITE: Privacy-preserving verification proxy.
    Checks if a temporary disclosure_id is valid without revealing original ID.
    """
    try:
        data = request.get_json()
        disclosure_id = data.get('disclosure_id')
        if not disclosure_id:
            return jsonify({'valid': False, 'error': 'Disclosure ID is required'}), 400
            
        result = credential_manager.verify_blind_disclosure(disclosure_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error verifying blind disclosure: {str(e)}")
        return jsonify({'valid': False, 'error': str(e)}), 500

@app.route('/certificate/<credential_id>')
def view_certificate_portal(credential_id):
    """Render the high-end certificate viewer page."""
    try:
        cred = credential_manager.get_credential(credential_id)
        if not cred:
            return "Credential not found", 404
            
        full_cred = cred.get('full_credential', {})
        subject = full_cred.get('credentialSubject', {})
        
        qr_payload = _build_verify_url(credential_id)
        pdf_version = (
            cred.get('updated_at')
            or cred.get('issued_at')
            or cred.get('issuance_date')
            or full_cred.get('issuanceDate')
            or datetime.utcnow().isoformat() + 'Z'
        )
        response = make_response(render_template(
            'certificate_view.html',
            credential=full_cred,
            subject=subject,
            qr_token=qr_payload['qr_token'],
            qr_data=qr_payload['qr_data'],
            verify_url=qr_payload['verify_url'],
            pdf_download_url=url_for('api_credential_pdf', credential_id=credential_id, v=pdf_version)
        ))
        return _apply_no_cache_headers(response)
    except Exception as e:
        logging.error(f"Certificate View error: {e}")
        return str(e), 500

@app.route('/api/credential/<credential_id>/pdf')
@role_required('student')
def api_credential_pdf(credential_id):
    try:
        cred = credential_manager.get_credential(credential_id)
        if not cred:
            return jsonify({'error': 'Credential not found'}), 404
            
        full_cred = cred.get('full_credential') or {}
        subject = full_cred.get('credentialSubject') or {}

        subject_name = subject.get('name') or cred.get('student_name') or 'Student'
        roll_number = str(subject.get('studentId') or cred.get('student_id') or 'N/A')
        degree_name = str(subject.get('degree') or cred.get('degree') or 'N/A')
        department_name = str(subject.get('department') or cred.get('department') or 'N/A')
        cgpa_value = str(subject.get('cgpa') or subject.get('gpa') or cred.get('cgpa') or cred.get('gpa') or '0.00')
        conduct_value = str(subject.get('conduct') or cred.get('conduct') or 'N/A')
        batch_value = str(subject.get('batch') or cred.get('batch') or 'N/A')
        semester_value = str(subject.get('semester') or cred.get('semester') or 'N/A')
        year_value = str(subject.get('year') or cred.get('year') or 'N/A')
        backlog_count = str(subject.get('backlogCount') or cred.get('backlog_count') or '0')
        graduation_year = str(subject.get('graduationYear') or cred.get('graduation_year') or 'N/A')
        courses = subject.get('courses') or cred.get('courses') or []
        backlogs = subject.get('backlogs') or cred.get('backlogs') or []

        buffer = io.BytesIO()
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.utils import simpleSplit, ImageReader
        
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        gold = colors.HexColor("#c9a227")
        navy = colors.HexColor("#18233a")
        muted = colors.HexColor("#6b7280")
        surface = colors.HexColor("#fbfbfa")
        border = colors.HexColor("#e7e5df")
        success_bg = colors.HexColor("#e8f6ef")
        success_text = colors.HexColor("#0f8a5f")
        danger_text = colors.HexColor("#b91c1c")

        def draw_panel(x, y, w, h, title):
            p.setFillColor(colors.white)
            p.setStrokeColor(border)
            p.setLineWidth(1)
            p.roundRect(x, y, w, h, 10, fill=1, stroke=1)
            p.setFont("Helvetica-Bold", 8)
            p.setFillColor(gold)
            p.drawString(x + 12, y + h - 18, title.upper())

        def draw_detail_rows(x, y_top, width_value, rows, row_gap=22):
            y = y_top
            for label, value, value_color in rows:
                p.setStrokeColor(border)
                p.setLineWidth(0.7)
                p.line(x, y - 10, x + width_value, y - 10)
                p.setFont("Helvetica-Bold", 7.5)
                p.setFillColor(muted)
                p.drawString(x, y, label)
                p.setFont("Helvetica-Bold", 9)
                p.setFillColor(value_color)
                p.drawString(x + 92, y, value)
                y -= row_gap

        p.setFillColor(surface)
        p.rect(0, 0, width, height, fill=1, stroke=0)

        p.setStrokeColor(gold)
        p.setLineWidth(6)
        p.rect(18, 18, width - 36, height - 36)
        p.setLineWidth(1.5)
        p.rect(30, 30, width - 60, height - 60)

        p.saveState()
        p.setFont("Helvetica-Bold", 72)
        p.setFillColor(gold, alpha=0.02)
        p.translate(width/2, height/2)
        p.rotate(32)
        p.drawCentredString(0, 0, "CREDIFY VERIFIED")
        p.restoreState()

        logo_path = os.path.join(os.getcwd(), 'static', 'images', 'collegelogo.png')
        if os.path.exists(logo_path):
            p.drawImage(logo_path, width/2 - 20, height - 92, width=40, height=40, mask='auto')

        p.setFillColor(navy)
        p.setFont("Helvetica-Bold", 15)
        p.drawCentredString(width/2, height - 126, "G. PULLA REDDY ENGINEERING COLLEGE (AUTONOMOUS)")
        p.setFont("Helvetica-Bold", 22)
        p.drawCentredString(width/2, height - 160, "OFFICIAL DIGITAL ACADEMIC RECORD")
        p.setStrokeColor(gold)
        p.setLineWidth(1.3)
        p.line(width/2 - 120, height - 166, width/2 + 120, height - 166)
        p.setFont("Helvetica-Oblique", 9)
        p.setFillColor(muted)
        p.drawCentredString(width/2, height - 178, "Issued via Credify Blockchain Credential Verification System")
        p.setFont("Helvetica-Oblique", 14)
        p.drawCentredString(width/2, height - 220, "This is to certify that")
        p.setFont("Helvetica-Bold", 30)
        p.setFillColor(colors.black)
        p.drawCentredString(width/2, height - 257, subject_name.upper())

        pill_w = 100
        pill_h = 20
        pill_x = (width - pill_w) / 2
        pill_y = height - 286
        p.setFillColor(success_bg)
        p.setStrokeColor(colors.HexColor("#d5eee0"))
        p.roundRect(pill_x, pill_y, pill_w, pill_h, 6, fill=1, stroke=1)
        p.setFillColor(success_text)
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(width/2, pill_y + 6.5, "CERTIFIED AUTHENTIC")

        panel_y = height - 455
        panel_h = 140
        panel_gap = 12
        panel_w = (width - 96 - panel_gap) / 2

        draw_panel(48, panel_y, panel_w, panel_h, "Student Details")
        draw_panel(48 + panel_w + panel_gap, panel_y, panel_w, panel_h, "Academic Record")

        draw_detail_rows(60, panel_y + panel_h - 38, panel_w - 24, [
            ("Name", subject_name, navy),
            ("Roll Number", roll_number, navy),
            ("Degree / Program", degree_name, navy),
            ("Department", department_name, navy)
        ], row_gap=24)

        draw_detail_rows(60 + panel_w + panel_gap, panel_y + panel_h - 38, panel_w - 24, [
            ("CGPA", f"{cgpa_value} / 10.00", navy),
            ("Conduct", conduct_value, navy),
            ("Batch", batch_value, navy),
            ("Current Semester / Year", f"{semester_value} / {year_value}", navy),
            ("Backlog Count", backlog_count, navy),
            ("Graduation Year", graduation_year, navy)
        ], row_gap=19)

        small_panel_y = panel_y - 72
        small_panel_h = 54
        draw_panel(48, small_panel_y, panel_w, small_panel_h, "Coursework")
        draw_panel(48 + panel_w + panel_gap, small_panel_y, panel_w, small_panel_h, "Outstanding Subjects")

        p.setFont("Helvetica-Bold", 8)
        p.setFillColor(muted)
        p.drawString(60, small_panel_y + 16, "Subjects")
        p.setFillColor(navy)
        p.drawString(132, small_panel_y + 16, ", ".join(str(course) for course in courses) if courses else "N/A")

        p.setFillColor(muted)
        p.drawString(60 + panel_w + panel_gap, small_panel_y + 16, "Backlogs")
        p.setFillColor(danger_text if backlogs else navy)
        p.drawString(132 + panel_w + panel_gap, small_panel_y + 16, ", ".join(str(backlog) for backlog in backlogs) if backlogs else "None")

        proof_box_bottom = 190
        proof_box_height = 120
        draw_panel(48, proof_box_bottom, width - 96, proof_box_height, "Blockchain Verification")
        p.setFont("Helvetica", 8.5)
        p.setFillColor(muted)
        p.drawString(60, proof_box_bottom + proof_box_height - 36, "This credential is packaged with an offline verifiable QR payload and a signed issuer proof.")
        p.setFont("Helvetica-Bold", 7)
        p.drawString(60, proof_box_bottom + proof_box_height - 56, "CREDENTIAL ID")
        p.drawString(60, proof_box_bottom + proof_box_height - 86, "ON-CHAIN HASH (SHA-256)")
        p.drawString(60, proof_box_bottom + proof_box_height - 116, "VERIFICATION")
        p.setFillColor(navy)
        p.setFont("Courier-Bold", 7.5)
        p.drawString(60, proof_box_bottom + proof_box_height - 68, credential_id)
        hash_preview = str(cred.get('credential_hash', 'N/A'))
        hash_preview = hash_preview if len(hash_preview) <= 58 else f"{hash_preview[:58]}..."
        p.drawString(60, proof_box_bottom + proof_box_height - 98, hash_preview)
        p.drawString(60, proof_box_bottom + proof_box_height - 128, "Blockchain Verified Record")

        qr_payload = _build_verify_url(credential_id)
        verify_url = qr_payload['verify_url']
        qr_obj = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_L,
            box_size=8,
            border=4,
        )
        qr_obj.add_data(verify_url)
        qr_obj.make(fit=True)
        qr = qr_obj.make_image(fill_color='black', back_color='white')
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_size = 88
        qr_x = width - 156
        qr_y = proof_box_bottom + 28
        p.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)

        p.setFillColor(gold)
        p.setStrokeColor(colors.white)
        badge_x = qr_x - 38
        badge_y = proof_box_bottom + 44
        p.circle(badge_x, badge_y, 13, fill=1, stroke=1)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 3.5)
        p.drawCentredString(badge_x, badge_y + 1.5, "BLOCKCHAIN")
        p.drawCentredString(badge_x, badge_y - 3.5, "VERIFIED")

        authority_y = 128
        draw_panel(48, authority_y, width - 96, 46, "Authorities")
        p.setFillColor(navy)
        p.setFont("Helvetica-Bold", 8.5)
        p.drawString(60, authority_y + 18, "Academic Records Authority")
        p.drawCentredString(width/2, authority_y + 18, "Controller of Examinations")
        p.drawRightString(width - 60, authority_y + 18, "Credify Network Validator")
        p.setFillColor(muted)
        p.setFont("Helvetica", 7.5)
        p.drawString(60, authority_y + 8, "Digital Issuer")
        p.drawCentredString(width/2, authority_y + 8, "Authorizing Authority")
        p.drawRightString(width - 60, authority_y + 8, "Verification Node")

        portal_y = 78
        draw_panel(48, portal_y, width - 96, 40, "Verification Portal")
        p.setFillColor(navy)
        p.setFont("Courier-Bold", 7)
        p.drawString(60, portal_y + 14, "https://udaycodespace.github.io/credify-verify/")
        p.setFont("Helvetica", 7.5)
        p.setFillColor(muted)
        p.drawString(60, portal_y + 5, "Scan the QR or enter the Credential ID to verify authenticity.")

        p.setFillColor(muted)
        p.setFont("Helvetica-Oblique", 6.8)
        disclaimer = (
            "Scan QR or enter Credential ID to verify authenticity. "
            "No physical signature is required because this document is digitally issued "
            "through the Credify blockchain credential verification system."
        )
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.alignment = 1
        style.fontSize = 6.8
        style.textColor = muted
        style.fontName = "Helvetica-Oblique"
        style.leading = 8.5
        footer_p = Paragraph(disclaimer, style)
        footer_p.wrapOn(p, 470, 22)
        footer_p.drawOn(p, (width - 470) / 2, 42)

        p.showPage()
        p.save()
        buffer.seek(0)
        response = send_file(buffer, as_attachment=True,
                             download_name=f"Verified_Transcript_{credential_id}.pdf",
                             mimetype='application/pdf')
        return _apply_no_cache_headers(response)
    except Exception as e:
        logging.error(f"Elite PDF Generation error: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(f"Elite PDF Generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify_zkp', methods=['POST'])
def api_verify_zkp():
    """
    Backend ZKP verification (Range Proof / Membership Proof)
    Ensures the student isn't lying about their GPA/Backlogs!
    """
    try:
        data = request.get_json()
        proof = data.get('proof')
        if not proof:
            return jsonify({'success': False, 'error': 'No proof provided'}), 400
            
        credential_id = proof.get('credentialId') or proof.get('credential_id')
        if not credential_id:
            masked_id = str(proof.get('maskedCredentialId') or '').strip()
            suffix = masked_id.replace('*', '')
            if suffix:
                matches = [
                    c.get('credential_id')
                    for c in credential_manager.get_all_credentials()
                    if str(c.get('credential_id', '')).endswith(suffix)
                ]
                if len(matches) == 1:
                    credential_id = matches[0]
        field = proof.get('field')

        if not credential_id:
            return jsonify({'success': False, 'error': 'Proof is missing credentialId'}), 400
        
        # 1. Fetch real data from the source of truth
        cred = credential_manager.get_credential(credential_id)
        if not cred:
            return jsonify({'success': False, 'error': 'Source credential not found'}), 404
            
        subject = cred.get('full_credential', {}).get('credentialSubject', {})
        
        # 2. Extract the actual value the student wants to prove something about
        actual_value = subject.get(field)
        
        # 3. Verify based on proof type
        is_verified = False
        
        if proof['type'] == 'RangeProof':
            # Support explicit numeric thresholds first; fallback to old claim text.
            min_threshold = proof.get('minThreshold')
            max_threshold = proof.get('maxThreshold')
            claim = proof.get('claim', '')
            try:
                numeric_actual = float(actual_value)

                if min_threshold is not None or max_threshold is not None:
                    min_val = float(min_threshold) if min_threshold is not None else None
                    max_val = float(max_threshold) if max_threshold is not None else None

                    is_verified = True
                    if min_val is not None:
                        is_verified = is_verified and (numeric_actual >= min_val)
                    if max_val is not None:
                        is_verified = is_verified and (numeric_actual <= max_val)
                elif '>=' in claim:
                    min_val = float(claim.split('>=')[-1].strip())
                    is_verified = numeric_actual >= min_val
                elif '<=' in claim:
                    max_val = float(claim.split('<=')[-1].strip())
                    is_verified = numeric_actual <= max_val
                elif 'between' in claim.lower():
                    nums = re.findall(r"[-+]?\d*\.?\d+", claim)
                    if len(nums) >= 2:
                        min_val = float(nums[0])
                        max_val = float(nums[1])
                        is_verified = min_val <= numeric_actual <= max_val
                    else:
                        return jsonify({'success': False, 'error': 'Invalid range claim format'}), 400
                else:
                    return jsonify({'success': False, 'error': 'Range proof must include min/max thresholds'}), 400
            except Exception as parse_error:
                logging.error(f"ZKP Claim Parsing error: {parse_error}")
                return jsonify({'success': False, 'error': 'Invalid claim format in proof'}), 400
        
        elif proof['type'] == 'MembershipProof':
            proof_category = str(proof.get('proofCategory') or '').strip().lower()
            claimed_item = str(proof.get('subject') or '').strip().lower()

            courses = [str(c).strip().lower() for c in (subject.get('courses') or [])]
            backlogs = [str(b).strip().lower() for b in (subject.get('backlogs') or [])]

            if proof_category == 'completed':
                is_verified = claimed_item in courses
            elif proof_category == 'has_backlog':
                is_verified = claimed_item in backlogs
            elif proof_category == 'no_backlog':
                is_verified = claimed_item not in backlogs
            else:
                # Backward-compatible generic membership path.
                field = field or 'courses'
                actual_value = subject.get(field)
                if isinstance(actual_value, list):
                    normalized = [str(v).strip().lower() for v in actual_value]
                    is_verified = claimed_item in normalized
                else:
                    is_verified = False
            
        return jsonify({
            'success': True,
            'verified': is_verified,
            'details': {
                'field': field,
                'status': 'verified' if is_verified else 'failed',
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logging.error(f"ZKP verification error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/selective_disclosure', methods=['POST'])
def api_selective_disclosure():
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')
        fields = data.get('fields', [])
        verifier_domain = data.get('verifier_domain') # Optional binding
        
        if not credential_id:
            return jsonify({'error': 'Credential ID is required'}), 400
        if not fields:
            return jsonify({'error': 'At least one field must be selected'}), 400
            
        result = credential_manager.selective_disclosure(credential_id, fields, verifier_domain)
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
def api_zkp_verify_legacy():
    """Verifier verifies a ZKP via Manager (Simulation)"""
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

        qr_payload = _build_verify_url(credential_id)
        verify_url = qr_payload['verify_url']

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_L,
            box_size=8,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        # Use black on white so uploaded/exported QR images remain scanner-friendly.
        img = qr.make_image(fill_color='black', back_color='white')

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return jsonify({
            'success': True,
            'qr_base64': qr_b64,
            'verify_url': verify_url,
            'verify_url_length': len(verify_url),
            'compression': 'gzip+base64url',
        })
    except ImportError:
        return jsonify({'success': False, 'error': 'qrcode library not installed. Run: pip install qrcode[pil] Pillow'}), 500
    except Exception as e:
        logging.error(f'QR generation error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/verify')
def public_verify():
    """Public credential verification page  no login required.
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


@app.route('/api/public/issuer_registry')
def api_public_issuer_registry():
    """Expose trusted issuer public keys for offline-capable scanner apps."""
    try:
        issuer_id = "did:edu:gprec"
        return jsonify({
            'success': True,
            'version': 1,
            'issuers': {
                issuer_id: {
                    'name': 'GPREC',
                    'algorithm': 'PS256',
                    'publicKeyPem': crypto_manager.get_public_key_pem(),
                }
            }
        })
    except Exception as e:
        logging.error(f'Issuer registry error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qr/secret_verify', methods=['POST'])
def api_qr_secret_verify():
    """Return full credential details only when a signed QR token is valid."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        token = data.get('qk')
        qr_data = (data.get('qd') or '').strip()
        credential_id = (data.get('credential_id') or '').strip()

        payload = _verify_qr_secret_token(token, expected_cid=credential_id or None, expected_qd=qr_data or None)
        if not payload:
            return jsonify({'success': False, 'status': 'fake', 'error': 'Invalid or tampered QR secret token'}), 400

        token_cid = str(payload.get('cid'))

        verification = credential_manager.verify_credential(token_cid)
        if not verification.get('valid'):
            return jsonify({'success': False, 'status': verification.get('status', 'invalid'), 'verification': verification}), 200

        credential = verification.get('credential', {})
        subject = credential.get('credentialSubject', {})
        registry = verification.get('registry_entry', {})

        return jsonify({
            'success': True,
            'status': 'real',
            'credential_id': token_cid,
            'issuer': payload.get('iss') or 'did:edu:gprec',
            'subject': subject,
            'ipfs_cid': registry.get('ipfs_cid'),
            'security_checks': {
                'blockchain_hash_integrity': True,
                'rsa_signature_valid': True,
                'not_revoked': registry.get('status') == 'active',
                'ipfs_reference_intact': bool(registry.get('ipfs_cid')),
            },
            'verification_details': verification.get('verification_details', {}),
        })
    except Exception as e:
        logging.error(f'QR secret verify error: {e}')
        return jsonify({'success': False, 'status': 'error', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
