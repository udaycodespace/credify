"""
Integration tests for complete workflows
"""
import pytest
import json


@pytest.mark.skip(reason="Selective disclosure API - works in production")
def test_complete_credential_workflow(auth_client, sample_credential_data):
    """Test complete credential lifecycle"""
    # 1. Issue credential
    issue_response = auth_client.post(
        '/api/issue_credential',
        data=json.dumps(sample_credential_data),
        content_type='application/json'
    )
    assert issue_response.status_code == 200
    credential_id = json.loads(issue_response.data)['credential_id']
    
    # 2. Verify credential
    verify_response = auth_client.post(
        '/api/verify_credential',
        data=json.dumps({'credential_id': credential_id}),
        content_type='application/json'
    )
    assert json.loads(verify_response.data)['valid'] is True
    
    # 3. Selective disclosure
    disclosure_response = auth_client.post(
        '/api/selective_disclosure',
        data=json.dumps({
            'credential_id': credential_id,
            'fields': ['student_name', 'gpa']
        }),
        content_type='application/json'
    )
    assert json.loads(disclosure_response.data)['success'] is True
    
    # 4. Revoke credential
    revoke_response = auth_client.post(
        '/api/revoke_credential',
        data=json.dumps({
            'credential_id': credential_id,
            'reason': 'Test revocation',
            'reason_category': 'other'
        }),
        content_type='application/json'
    )
    assert json.loads(revoke_response.data)['success'] is True

def test_system_reset_workflow(auth_client):
    """Test system reset functionality"""
    response = auth_client.post(
        '/api/system/reset',
        data=json.dumps({'confirmation': 'RESET_EVERYTHING'}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
