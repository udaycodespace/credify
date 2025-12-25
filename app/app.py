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
from .models import db, User, Ticket, Message, init_database  # NEW: Added Ticket, Message
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


# NEW: Revoke credential endpoint (REPLACES delete)
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


# NEW: Create new version endpoint (for corrections)
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


# NEW: Get credential history by student ID
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


# ==================== TICKET API ENDPOINTS ====================

@app.route('/api/tickets/create', methods=['POST'])
@login_required
def api_create_ticket():
    """Create a new ticket (student raises issue)"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user or user.role != 'student':
            return jsonify({'success': False, 'error': 'Only students can create tickets'}), 403
        
        data = request.get_json()
        
        required_fields = ['issue_type', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate ticket number
        last_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
        ticket_num = 1 if not last_ticket else last_ticket.id + 1
        ticket_number = f"TKT-{ticket_num:03d}"
        
        # Create ticket
        ticket = Ticket(
            ticket_number=ticket_number,
            student_user_id=user.id,
            student_roll_number=user.student_id or '',
            issue_type=data['issue_type'],
            description=data['description'],
            priority=data.get('priority', 'normal'),
            status='todo',
            credential_id=data.get('credential_id')
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        logging.info(f"Ticket created: {ticket_number} by student {user.student_id}")
        
        return jsonify({
            'success': True,
            'ticket': ticket.to_dict(),
            'message': f'Ticket {ticket_number} created successfully'
        })
        
    except Exception as e:
        logging.error(f"Error creating ticket: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tickets', methods=['GET'])
@role_required('issuer')
def api_list_tickets():
    """List all tickets (issuer view)"""
    try:
        status_filter = request.args.get('status')
        
        query = Ticket.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        tickets = query.order_by(Ticket.created_at.desc()).all()
        
        tickets_data = []
        for ticket in tickets:
            ticket_dict = ticket.to_dict()
            student = User.query.get(ticket.student_user_id)
            ticket_dict['student_name'] = student.full_name if student else 'Unknown'
            tickets_data.append(ticket_dict)
        
        return jsonify({
            'success': True,
            'tickets': tickets_data,
            'total': len(tickets_data)
        })
        
    except Exception as e:
        logging.error(f"Error listing tickets: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tickets/my', methods=['GET'])
@login_required
def api_my_tickets():
    """Get tickets for logged-in student"""
    try:
        user_id = session.get('user_id')
        
        tickets = Ticket.query.filter_by(student_user_id=user_id).order_by(Ticket.created_at.desc()).all()
        
        tickets_data = [ticket.to_dict() for ticket in tickets]
        
        return jsonify({
            'success': True,
            'tickets': tickets_data,
            'total': len(tickets_data)
        })
        
    except Exception as e:
        logging.error(f"Error getting student tickets: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
@role_required('issuer')
def api_update_ticket_status(ticket_id):
    """Update ticket status (Kanban workflow)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['todo', 'in_progress', 'completed']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()
        
        if new_status == 'completed':
            ticket.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        logging.info(f"Ticket {ticket.ticket_number} status updated to {new_status}")
        
        return jsonify({
            'success': True,
            'ticket': ticket.to_dict(),
            'message': f'Ticket status updated to {new_status}'
        })
        
    except Exception as e:
        logging.error(f"Error updating ticket status: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tickets/<int:ticket_id>/respond', methods=['POST'])
@role_required('issuer')
def api_respond_to_ticket(ticket_id):
    """Admin responds to ticket"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        response_text = data.get('response')
        if not response_text:
            return jsonify({'success': False, 'error': 'Response text is required'}), 400
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        ticket.admin_response = response_text
        ticket.admin_user_id = user_id
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logging.info(f"Admin responded to ticket {ticket.ticket_number}")
        
        return jsonify({
            'success': True,
            'ticket': ticket.to_dict(),
            'message': 'Response added successfully'
        })
        
    except Exception as e:
        logging.error(f"Error responding to ticket: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== MESSAGE API ENDPOINTS ====================

@app.route('/api/messages/send', methods=['POST'])
@role_required('issuer')
def api_send_message():
    """Send message to specific student"""
    try:
        from_user_id = session.get('user_id')
        data = request.get_json()
        
        required_fields = ['to_student_id', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        student = User.query.filter_by(student_id=data['to_student_id'], role='student').first()
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'}), 404
        
        message = Message(
            from_user_id=from_user_id,
            to_user_id=student.id,
            subject=data['subject'],
            body=data['body'],
            is_broadcast=False,
            ticket_id=data.get('ticket_id')
        )
        
        db.session.add(message)
        db.session.commit()
        
        logging.info(f"Message sent to student {data['to_student_id']}")
        
        return jsonify({
            'success': True,
            'message': message.to_dict(),
            'message_text': 'Message sent successfully'
        })
        
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/messages/broadcast', methods=['POST'])
@role_required('issuer')
def api_broadcast_message():
    """Broadcast message to all students"""
    try:
        from_user_id = session.get('user_id')
        data = request.get_json()
        
        required_fields = ['subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        message = Message(
            from_user_id=from_user_id,
            to_user_id=None,
            subject=data['subject'],
            body=data['body'],
            is_broadcast=True
        )
        
        db.session.add(message)
        db.session.commit()
        
        student_count = User.query.filter_by(role='student').count()
        
        logging.info(f"Broadcast message sent to {student_count} students")
        
        return jsonify({
            'success': True,
            'message': message.to_dict(),
            'recipients': student_count,
            'message_text': f'Broadcast sent to {student_count} students'
        })
        
    except Exception as e:
        logging.error(f"Error broadcasting message: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/messages/inbox', methods=['GET'])
@login_required
def api_get_inbox():
    """Get inbox messages for logged-in user"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role == 'student':
            messages = Message.query.filter(
                (Message.to_user_id == user_id) | (Message.is_broadcast == True)
            ).order_by(Message.created_at.desc()).all()
        else:
            messages = Message.query.filter_by(to_user_id=user_id).order_by(Message.created_at.desc()).all()
        
        messages_data = []
        for msg in messages:
            msg_dict = msg.to_dict()
            sender = User.query.get(msg.from_user_id)
            msg_dict['from_name'] = sender.full_name if sender else 'Unknown'
            messages_data.append(msg_dict)
        
        return jsonify({
            'success': True,
            'messages': messages_data,
            'total': len(messages_data),
            'unread': sum(1 for m in messages if not m.is_read)
        })
        
    except Exception as e:
        logging.error(f"Error getting inbox: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/messages/<int:message_id>/read', methods=['PUT'])
@login_required
def api_mark_message_read(message_id):
    """Mark message as read"""
    try:
        user_id = session.get('user_id')
        
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        
        if message.to_user_id != user_id and not message.is_broadcast:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        message.is_read = True
        message.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        })
        
    except Exception as e:
        logging.error(f"Error marking message as read: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
