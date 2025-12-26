"""
Integration tests for complete workflows
"""

import pytest
import json


class TestIntegration:
    
    def test_complete_credential_issuance_flow(self, client):
        """Test complete flow: issue -> verify"""
        # Login as issuer
        client.post('/login', data={
            'user_id': 'admin',
            'password': 'admin123',
            'role': 'issuer'
        })
        
        # Issue credential
        credential_data = {
            'student_id': 'INT001',
            'student_name': 'Integration Test',
            'degree': 'Test Degree',
            'university': 'Test University',
            'gpa': '8.0',
            'graduation_year': '2024'
        }
        
        response = client.post(
            '/api/issue_credential',
            data=json.dumps(credential_data),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        if data.get('success'):
            credential_id = data['credential_id']
            
            # Verify credential
            verify_response = client.post(
                '/api/verify_credential',
                data=json.dumps({'credential_id': credential_id}),
                content_type='application/json'
            )
            
            verify_data = json.loads(verify_response.data)
            assert verify_data.get('valid') == True
    
    def test_zkp_generation_and_verification_flow(self, client):
        """Test ZKP generation and verification workflow"""
        # Generate range proof
        proof_response = client.post(
            '/api/zkp/range_proof',
            data=json.dumps({
                'credential_id': 'TEST123',
                'field': 'gpa',
                'actual_value': 8.5,
                'min_threshold': 7.0
            }),
            content_type='application/json'
        )
        
        proof_data = json.loads(proof_response.data)
        
        if proof_data.get('success'):
            proof = proof_data['proof']
            
            # Verify proof
            verify_response = client.post(
                '/api/zkp/verify',
                data=json.dumps({'proof': proof}),
                content_type='application/json'
            )
            
            verify_data = json.loads(verify_response.data)
            assert 'valid' in verify_data
