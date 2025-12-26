"""
Test cases for Authentication
"""

import pytest


class TestAuthentication:
    
    def test_login_required_redirect(self, client):
        """Test that protected routes redirect to login"""
        response = client.get('/issuer', follow_redirects=False)
        assert response.status_code == 302  # Redirect
    
    def test_issuer_login_success(self, client):
        """Test successful issuer login"""
        response = client.post('/login', data={
            'user_id': 'admin',
            'password': 'admin123',
            'role': 'issuer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            assert session.get('role') == 'issuer'
    
    def test_logout(self, authenticated_session):
        """Test logout functionality"""
        response = authenticated_session.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        
        with authenticated_session.session_transaction() as session:
            assert 'user_id' not in session
