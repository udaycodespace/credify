"""
Tests for authentication system — Role-Based Access Control Audit
"""
import pytest
from app.models import User, db

def test_user_password_security():
    """Verify that passwords are correctly hashed and never stored in plain text"""
    user = User(username='sec_test', role='student')
    user.set_password('complex_password_123')
    
    assert user.password_hash != 'complex_password_123'
    assert user.check_password('complex_password_123') is True
    assert user.check_password('123456') is False

def test_login_workflow(client):
    """Test standard login page rendering and submission"""
    # Page load
    resp = client.get('/login')
    assert resp.status_code == 200
    
    # Successful submission (Admin)
    resp = client.post('/login', data={
        'username': 'test_admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert resp.status_code == 200

def test_student_access_restriction(student_client):
    """Verify that students cannot access issuer routes"""
    resp = student_client.get('/issuer')
    assert resp.status_code in [302, 403] 

def test_admin_access_dashboard(auth_client):
    """Verify that admins can access their dashboard"""
    resp = auth_client.get('/issuer')
    assert resp.status_code == 200

def test_session_management(client):
    """Test that session state is correctly cleared on logout"""
    # 1. Login
    client.post('/login', data={'username': 'test_admin', 'password': 'admin123'})
    
    # 2. Logout
    client.get('/logout')
    
    # 3. Verify access is revoked
    resp = client.get('/issuer')
    assert resp.status_code == 302
