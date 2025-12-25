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
            'responses': []
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
    
    def update_ticket_status(self, ticket_id, status, admin_note=None):
        """Update ticket status"""
        if ticket_id in self.tickets:
            self.tickets[ticket_id]['status'] = status
            self.tickets[ticket_id]['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            if admin_note:
                response = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'responder': 'admin',
                    'message': admin_note
                }
                self.tickets[ticket_id]['responses'].append(response)
            
            self._save_tickets()
            return True
        return False
    
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
    
    def send_message(self, sender_id, sender_type, recipient_id, recipient_type, subject, message):
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
            'read': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'replies': []
        }
        
        self.messages[message_id] = msg
        self._save_messages()
        
        return msg
    
    def get_messages_for_user(self, user_id, user_type):
        """Get all messages for a user (sent or received)"""
        user_messages = []
        for msg in self.messages.values():
            if (msg['sender_id'] == user_id and msg['sender_type'] == user_type) or \
               (msg['recipient_id'] == user_id and msg['recipient_type'] == user_type):
                user_messages.append(msg)
        
        # Sort by timestamp (newest first)
        user_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return user_messages
    
    def mark_message_read(self, message_id):
        """Mark a message as read"""
        if message_id in self.messages:
            self.messages[message_id]['read'] = True
            self._save_messages()
            return True
        return False
    
    def reply_to_message(self, message_id, sender_id, sender_type, reply_text):
        """Reply to a message"""
        if message_id in self.messages:
            reply = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'sender_id': sender_id,
                'sender_type': sender_type,
                'message': reply_text
            }
            self.messages[message_id]['replies'].append(reply)
            self._save_messages()
            return True
        return False
