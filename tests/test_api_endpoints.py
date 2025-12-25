import pytest
from flask.testing import FlaskClient
from app import app, db, User
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def issuer_session(client):
    """Login as issuer"""
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    return client

def test_issue_credential_extended_fields(client: FlaskClient, issuer_session):
    """Test API accepts and processes extended fields"""
    response = issuer_session.post('/api/issue_credential', 
        json={
            'student_name': 'Test Student',
            'student_id': 'TEST123',
            'degree': 'B.Tech CS',
            'university': 'GPREC',
            'gpa': '8.5',
            'graduation_year': 2026,
            'semester': 5,
            'year': 3,
            'class_name': 'B.Tech',
            'section': 'A',
            'backlog_count': 1,
            'backlogs': ['Maths'],
            'conduct': 'good'
        })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_extended_fields_validation(client: FlaskClient, issuer_session):
    """Test validation rejects invalid semester"""
    response = issuer_session.post('/api/issue_credential', 
        json={
            'student_name': 'Invalid',
            'student_id': '999',
            'degree': 'B.Tech',
            'university': 'Test',
            'gpa': '8.0',
            'graduation_year': 2025,
            'semester': 10  # Invalid semester
        })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'Semester must be between 1 and 8' in data['error']
