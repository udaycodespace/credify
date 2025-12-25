import json
import os
from datetime import datetime
import uuid

class TicketManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.tickets_file = os.path.join(data_dir, 'tickets.json')
        self.messages_file = os.path.join(data_dir, 'messages.json')
        self.tickets = self._load_tickets()
        self.messages = self._load_messages()
    
    def _load_tickets(self):
        """Load tickets from file"""
        if os.path.exists(self.tickets_file):
            with open(self.tickets_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_tickets(self):
        """Save tickets to file"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.tickets_file, 'w') as f:
            json.dump(self.tickets, f, indent=2)
    
    def _load_messages(self):
        """Load messages from file"""
        if os.path.exists(self.messages_file):
            with open(self.messages_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_messages(self):
        """Save messages to file"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.messages_file, 'w') as f:
            json.dump(self.messages, f, indent=2)
    
    def create_ticket(self, student_id, subject, description, category, priority='medium'):
        """Create a new ticket"""
        ticket_id = str(uuid.uuid4())[:8]
        
        ticket = {
            'ticket_id': ticket_id,
            'student_id': student_id,
            'subject': subject,
            'description': description,
            'category': category,
            'priority': priority,
            'status': 'open',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'responses': [],
            'can_resolve': False  # Student can only resolve when admin moves to last column
        }
        
        self.tickets[ticket_id] = ticket
        self._save_tickets()
        
        return ticket
    
    def get_tickets_by_student(self, student_id):
        """Get all tickets for a student"""
        return [t for t in self.tickets.values() if t['student_id'] == student_id]
    
    def get_all_tickets(self):
        """Get all tickets"""
        return list(self.tickets.values())
    
    def get_ticket(self, ticket_id):
        """Get a specific ticket"""
        return self.tickets.get(ticket_id)
    
    def update_ticket_status(self, ticket_id, status, admin_note=None, by_admin=False):
        """Update ticket status"""
        if ticket_id in self.tickets:
            old_status = self.tickets[ticket_id]['status']
            self.tickets[ticket_id]['status'] = status
            self.tickets[ticket_id]['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Enable student resolve option only when admin moves to 'in_progress' or 'resolved'
            if by_admin and status in ['in_progress', 'resolved']:
                self.tickets[ticket_id]['can_resolve'] = True
            elif status == 'open':
                self.tickets[ticket_id]['can_resolve'] = False
            
            if admin_note:
                response = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'responder': 'admin',
                    'message': admin_note,
                    'action': f'Status changed: {old_status} → {status}'
                }
                self.tickets[ticket_id]['responses'].append(response)
            
            self._save_tickets()
            return True
        return False
    
    def student_mark_resolved(self, ticket_id, student_id, is_resolved):
        """Student marks ticket as resolved or not resolved"""
        if ticket_id in self.tickets:
            ticket = self.tickets[ticket_id]
            
            # Check if student owns the ticket
            if ticket['student_id'] != student_id:
                return {'success': False, 'error': 'Unauthorized'}
            
            # Check if student can resolve (admin must have moved it first)
            if not ticket.get('can_resolve', False):
                return {'success': False, 'error': 'Admin has not processed this ticket yet'}
            
            if is_resolved:
                ticket['status'] = 'resolved'
                ticket['resolved_by_student'] = True
                action = 'Student marked as RESOLVED ✓'
            else:
                ticket['status'] = 'open'
                ticket['can_resolve'] = False
                action = 'Student marked as NOT SOLVED - Re-ticketed'
            
            response = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'responder': 'student',
                'message': 'Ticket status updated by student',
                'action': action
            }
            ticket['responses'].append(response)
            ticket['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            self._save_tickets()
            return {'success': True, 'ticket': ticket}
        
        return {'success': False, 'error': 'Ticket not found'}
    
    def add_ticket_response(self, ticket_id, responder, message):
        """Add a response to a ticket"""
        if ticket_id in self.tickets:
            response = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'responder': responder,
                'message': message
            }
            self.tickets[ticket_id]['responses'].append(response)
            self.tickets[ticket_id]['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            self._save_tickets()
            return True
        return False
    
    def send_message(self, sender_id, sender_type, recipient_id, recipient_type, subject, message, is_broadcast=False):
        """Send a message"""
        message_id = str(uuid.uuid4())[:8]
        
        msg = {
            'message_id': message_id,
            'sender_id': sender_id,
            'sender_type': sender_type,
            'recipient_id': recipient_id,
            'recipient_type': recipient_type,
            'subject': subject,
            'message': message,
            'is_broadcast': is_broadcast,
            'read': False,
            'revoked': False,
            'revoked_at': None,
            'revoked_by': None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.messages[message_id] = msg
        self._save_messages()
        
        return msg
    
    def broadcast_message(self, sender_id, subject, message):
        """Broadcast message to all students"""
        message_id = str(uuid.uuid4())[:8]
        
        msg = {
            'message_id': message_id,
            'sender_id': sender_id,
            'sender_type': 'admin',
            'recipient_id': 'all_students',
            'recipient_type': 'broadcast',
            'subject': subject,
            'message': message,
            'is_broadcast': True,
            'read': False,
            'revoked': False,
            'revoked_at': None,
            'revoked_by': None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.messages[message_id] = msg
        self._save_messages()
        
        return msg
    
    def get_messages_for_student(self, student_id):
        """Get all messages for a specific student (direct + broadcast)"""
        student_messages = []
        for msg in self.messages.values():
            # Direct messages to this student
            if msg['recipient_id'] == student_id and msg['recipient_type'] == 'student':
                student_messages.append(msg)
            # Broadcast messages
            elif msg['is_broadcast']:
                student_messages.append(msg)
        
        # Sort by timestamp (newest first)
        student_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return student_messages
    
    def get_all_messages(self):
        """Get all messages (admin view)"""
        messages = list(self.messages.values())
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return messages
    
    def mark_message_read(self, message_id, student_id):
        """Mark a message as read"""
        if message_id in self.messages:
            msg = self.messages[message_id]
            # Check if student can read this message
            if msg['recipient_id'] == student_id or msg['is_broadcast']:
                self.messages[message_id]['read'] = True
                self._save_messages()
                return True
        return False
    
    def revoke_message(self, message_id, admin_id):
        """Revoke a message (admin only)"""
        if message_id in self.messages:
            self.messages[message_id]['revoked'] = True
            self.messages[message_id]['revoked_at'] = datetime.utcnow().isoformat() + 'Z'
            self.messages[message_id]['revoked_by'] = admin_id
            self._save_messages()
            return {'success': True, 'message': 'Message revoked'}
        return {'success': False, 'error': 'Message not found'}
