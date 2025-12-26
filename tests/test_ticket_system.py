"""
Test cases for Ticket System
"""

import pytest
from core.ticket_manager import TicketManager


class TestTicketSystem:
    
    def test_create_ticket(self, ticket_manager):
        """Test ticket creation"""
        result = ticket_manager.create_ticket(
            student_id='TEST001',
            subject='Test Issue',
            description='Test description',
            category='technical',
            priority='medium'
        )
        
        assert result['success'] == True
        assert 'ticket_id' in result
    
    def test_get_student_tickets(self, ticket_manager):
        """Test retrieving student tickets"""
        # Create ticket
        ticket_manager.create_ticket(
            student_id='TEST001',
            subject='Test',
            description='Test',
            category='technical',
            priority='low'
        )
        
        # Get tickets
        tickets = ticket_manager.get_student_tickets('TEST001')
        
        assert len(tickets) >= 1
    
    def test_update_ticket_status(self, ticket_manager):
        """Test updating ticket status"""
        # Create ticket
        result = ticket_manager.create_ticket(
            student_id='TEST001',
            subject='Test',
            description='Test',
            category='technical',
            priority='low'
        )
        
        ticket_id = result['ticket_id']
        
        # Update status
        update_result = ticket_manager.update_ticket_status(
            ticket_id,
            'in_progress'
        )
        
        assert update_result['success'] == True
