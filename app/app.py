import os
import logging

# Optionally load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.debug('Loaded environment variables from .env')
except Exception:
    logging.debug('python-dotenv not available; skipping .env load')

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from datetime import datetime
import json

# FIXED IMPORTS - Correct package structure
from core.blockchain import SimpleBlockchain
from core.crypto_utils import CryptoManager
from core.ipfs_client import IPFSClient
from core.credential_manager import CredentialManager
from core.ticket_manager import TicketManager
from .models import db, User, init_database
from .auth import login_required, role_required

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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
blockchain = SimpleBlockchain()
crypto_manager = CryptoManager()
ipfs_client = IPFSClient()
credential_manager = CredentialManager(blockchain, crypto_manager, ipfs_client)
ticket_manager = TicketManager()

@app.route('/')
def index():
    """Main landing page with role selection"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for all user roles"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['student_id'] = user.student_id
            session['full_name'] = user.full_name
            
            flash(f'Welcome {user.full_name or user.username}!', 'success')
            
            if user.role == 'issuer':
                return redirect(url_for('issuer'))
            elif user.role == 'student':
                return redirect(url_for('holder'))
            elif user.role == 'verifier':
                return redirect(url_for('verifier'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

@app.route('/issuer')
@role_required('issuer')
def issuer():
    return render_template('issuer.html')

@app.route('/holder')
@role_required('student')
def holder():
    student_id = session.get('student_id')
    all_credentials = credential_manager.get_all_credentials()
    student_credentials = [cred for cred in all_credentials if cred.get('student_id') == student_id]
    return render_template('holder.html', credentials=student_credentials)

@app.route('/verifier')
def verifier():
    return render_template('verifier.html')

# ==================== CREDENTIAL API ENDPOINTS ====================

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
                student_user = User.query.filter_by(student_id=student_id_val).first()
                if student_user:
                    student_user.username = student_name
                    student_user.full_name = student_name
                    student_user.set_password(student_id_val)
                    db.session.commit()
                else:
                    conflict = User.query.filter_by(username=student_name).first()
                    username_to_use = f"{student_name} ({student_id_val})" if conflict else student_name
                    
                    new_student = User(
                        username=username_to_use,
                        role='student',
                        student_id=student_id_val,
                        full_name=student_name,
                        email=None
                    )
                    new_student.set_password(student_id_val)
                    db.session.add(new_student)
                    db.session.commit()
            except Exception as e:
                logging.error(f"Error creating/updating student user: {str(e)}")

            flash('Credential issued successfully with extended academic details!', 'success')
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
        all_credentials = credential_manager.get_all_credentials()
        student_credentials = [
            cred for cred in all_credentials 
            if cred.get('credentialSubject', {}).get('studentId') == student_id
        ]
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

# ==================== TICKET ROUTES ====================

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    """Create a new support ticket"""
    try:
        data = request.json
        student_id = data.get('student_id')
        subject = data.get('subject')
        description = data.get('description')
        category = data.get('category')
        priority = data.get('priority', 'medium')
        
        if not all([student_id, subject, description, category]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        ticket = ticket_manager.create_ticket(student_id, subject, description, category, priority)
        
        return jsonify({
            'success': True,
            'ticket': ticket
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/student/<student_id>', methods=['GET'])
def get_student_tickets(student_id):
    """Get all tickets for a student"""
    try:
        tickets = ticket_manager.get_tickets_by_student(student_id)
        return jsonify({'tickets': tickets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/all', methods=['GET'])
def get_all_tickets():
    """Get all tickets (admin only)"""
    try:
        tickets = ticket_manager.get_all_tickets()
        return jsonify({'tickets': tickets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get a specific ticket"""
    try:
        ticket = ticket_manager.get_ticket(ticket_id)
        if ticket:
            return jsonify({'ticket': ticket})
        return jsonify({'error': 'Ticket not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """Update ticket status (admin only)"""
    try:
        data = request.json
        status = data.get('status')
        admin_note = data.get('admin_note')
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        success = ticket_manager.update_ticket_status(ticket_id, status, admin_note)
        
        if success:
            return jsonify({'success': True, 'message': 'Ticket updated'})
        return jsonify({'error': 'Ticket not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>/respond', methods=['POST'])
def respond_to_ticket(ticket_id):
    """Add a response to a ticket"""
    try:
        data = request.json
        responder = data.get('responder')
        message = data.get('message')
        
        if not all([responder, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        success = ticket_manager.add_ticket_response(ticket_id, responder, message)
        
        if success:
            return jsonify({'success': True, 'message': 'Response added'})
        return jsonify({'error': 'Ticket not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ==================== ENHANCED TICKET ROUTES ====================

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
            return jsonify(result)
        else:
            return jsonify(result), 403
        
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
def mark_student_message_read(message_id):
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
    
# ==================== MESSAGING ROUTES ====================

@app.route('/api/messages', methods=['POST'])
def send_message():
    """Send a message"""
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

@app.route('/api/messages/user/<user_id>/<user_type>', methods=['GET'])
def get_user_messages(user_id, user_type):
    """Get all messages for a user"""
    try:
        messages = ticket_manager.get_messages_for_user(user_id, user_type)
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<message_id>/read', methods=['PUT'])
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        success = ticket_manager.mark_message_read(message_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Message not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<message_id>/reply', methods=['POST'])
def reply_to_message(message_id):
    """Reply to a message"""
    try:
        data = request.json
        sender_id = data.get('sender_id')
        sender_type = data.get('sender_type')
        reply_text = data.get('reply')
        
        if not all([sender_id, sender_type, reply_text]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        success = ticket_manager.reply_to_message(message_id, sender_id, sender_type, reply_text)
        
        if success:
            return jsonify({'success': True, 'message': 'Reply sent'})
        return jsonify({'error': 'Message not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
