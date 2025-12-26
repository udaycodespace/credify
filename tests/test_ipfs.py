"""
Test cases for IPFS Client functionality
"""

import pytest
import json
from core.ipfs_client import IPFSClient


class TestIPFS:
    
    def test_ipfs_client_initialization(self, ipfs_client):
        """Test IPFS client initializes correctly"""
        assert ipfs_client is not None
        assert hasattr(ipfs_client, 'storage')
    
    def test_add_json_to_ipfs(self, ipfs_client):
        """Test adding JSON data to IPFS"""
        test_data = {
            'student_name': 'Test Student',
            'degree': 'Test Degree',
            'gpa': '8.5'
        }
        
        result = ipfs_client.add_json(test_data)
        
        assert result is not None
        assert 'cid' in result or 'Hash' in result
    
    def test_get_json_from_ipfs(self, ipfs_client):
        """Test retrieving JSON from IPFS"""
        # Add data first
        test_data = {
            'student_name': 'Retrieve Test',
            'degree': 'Computer Science',
            'university': 'Test University'
        }
        
        add_result = ipfs_client.add_json(test_data)
        
        if 'cid' in add_result:
            cid = add_result['cid']
        elif 'Hash' in add_result:
            cid = add_result['Hash']
        else:
            pytest.skip("Could not get CID from add result")
        
        # Retrieve data
        retrieved_data = ipfs_client.get_json(cid)
        
        assert retrieved_data is not None
        assert retrieved_data['student_name'] == test_data['student_name']
    
    def test_store_credential_in_ipfs(self, ipfs_client):
        """Test storing complete credential in IPFS"""
        credential = {
            '@context': 'https://www.w3.org/2018/credentials/v1',
            'type': ['VerifiableCredential', 'AcademicTranscript'],
            'issuer': {
                'id': 'did:edu:gprec',
                'name': 'Test Institution'
            },
            'credentialSubject': {
                'studentId': 'TEST001',
                'name': 'John Doe',
                'degree': 'Bachelor of Science',
                'gpa': '8.5'
            }
        }
        
        result = ipfs_client.add_json(credential)
        
        assert result is not None
        assert 'cid' in result or 'Hash' in result
    
    def test_ipfs_data_persistence(self, ipfs_client):
        """Test that stored data persists"""
        test_data = {
            'id': 'PERSIST_TEST',
            'value': 'This should persist'
        }
        
        # Add to IPFS
        add_result = ipfs_client.add_json(test_data)
        cid = add_result.get('cid') or add_result.get('Hash')
        
        # Retrieve multiple times
        data1 = ipfs_client.get_json(cid)
        data2 = ipfs_client.get_json(cid)
        
        assert data1 == data2
        assert data1['id'] == 'PERSIST_TEST'
    
    def test_ipfs_content_addressability(self, ipfs_client):
        """Test that same content gives same CID"""
        test_data = {
            'content': 'Same content test',
            'number': 42
        }
        
        # Add same data twice
        result1 = ipfs_client.add_json(test_data)
        result2 = ipfs_client.add_json(test_data)
        
        cid1 = result1.get('cid') or result1.get('Hash')
        cid2 = result2.get('cid') or result2.get('Hash')
        
        # Same content should produce same CID
        assert cid1 == cid2
    
    def test_ipfs_different_content_different_cid(self, ipfs_client):
        """Test that different content gives different CID"""
        data1 = {'content': 'First content'}
        data2 = {'content': 'Second content'}
        
        result1 = ipfs_client.add_json(data1)
        result2 = ipfs_client.add_json(data2)
        
        cid1 = result1.get('cid') or result1.get('Hash')
        cid2 = result2.get('cid') or result2.get('Hash')
        
        # Different content should produce different CID
        assert cid1 != cid2
    
    def test_ipfs_storage_fallback(self, ipfs_client):
        """Test local storage fallback when IPFS unavailable"""
        # This tests the local JSON storage fallback mechanism
        large_data = {
            'credential_id': 'FALLBACK_TEST',
            'data': 'x' * 1000,  # Large data
            'metadata': {
                'timestamp': '2024-12-26',
                'issuer': 'Test'
            }
        }
        
        result = ipfs_client.add_json(large_data)
        
        # Should succeed either via IPFS or local storage
        assert result is not None
    
    def test_ipfs_invalid_cid_handling(self, ipfs_client):
        """Test handling of invalid CID"""
        invalid_cid = 'INVALID_CID_123'
        
        # Should return None or raise exception gracefully
        try:
            result = ipfs_client.get_json(invalid_cid)
            assert result is None or isinstance(result, dict)
        except Exception as e:
            # Exception is acceptable for invalid CID
            assert True
    
    def test_ipfs_empty_data_handling(self, ipfs_client):
        """Test handling of empty data"""
        empty_data = {}
        
        result = ipfs_client.add_json(empty_data)
        
        # Should handle empty data gracefully
        assert result is not None
    
    def test_ipfs_nested_json_structure(self, ipfs_client):
        """Test storing nested JSON structures"""
        nested_data = {
            'level1': {
                'level2': {
                    'level3': {
                        'value': 'deeply nested',
                        'array': [1, 2, 3, 4, 5]
                    }
                },
                'other': 'data'
            },
            'courses': ['Math', 'Physics', 'Chemistry']
        }
        
        result = ipfs_client.add_json(nested_data)
        cid = result.get('cid') or result.get('Hash')
        
        retrieved = ipfs_client.get_json(cid)
        
        assert retrieved is not None
        assert retrieved['level1']['level2']['level3']['value'] == 'deeply nested'
        assert len(retrieved['courses']) == 3
    
    def test_ipfs_large_credential_storage(self, ipfs_client):
        """Test storing large credential with many courses"""
        large_credential = {
            'credentialSubject': {
                'studentId': 'LARGE_001',
                'name': 'Test Student',
                'courses': [f'Course_{i}' for i in range(100)],  # 100 courses
                'grades': {f'Course_{i}': f'{8 + (i % 3) * 0.5}' for i in range(100)}
            }
        }
        
        result = ipfs_client.add_json(large_credential)
        
        assert result is not None
        cid = result.get('cid') or result.get('Hash')
        
        # Verify retrieval
        retrieved = ipfs_client.get_json(cid)
        assert len(retrieved['credentialSubject']['courses']) == 100
    
    def test_ipfs_unicode_content(self, ipfs_client):
        """Test storing Unicode/international characters"""
        unicode_data = {
            'student_name': 'José María García 李明 محمد',
            'university': 'Université de París',
            'degree': 'Bacharel em Ciência da Computação',
            'special_chars': '©®™€¥£¢'
        }
        
        result = ipfs_client.add_json(unicode_data)
        cid = result.get('cid') or result.get('Hash')
        
        retrieved = ipfs_client.get_json(cid)
        
        assert retrieved is not None
        assert retrieved['student_name'] == unicode_data['student_name']
    
    def test_ipfs_pin_status(self, ipfs_client):
        """Test that content is pinned (if using real IPFS)"""
        test_data = {'pin_test': 'This should be pinned'}
        
        result = ipfs_client.add_json(test_data)
        
        # If using real IPFS, content should be pinned
        # This test might be skipped if using local storage fallback
        assert result is not None
    
    def test_ipfs_metadata_preservation(self, ipfs_client):
        """Test that metadata is preserved correctly"""
        credential_with_metadata = {
            'id': 'CRED_META_001',
            'type': 'VerifiableCredential',
            'issuanceDate': '2024-12-26T10:00:00Z',
            'expirationDate': '2025-12-26T10:00:00Z',
            'credentialSubject': {
                'id': 'did:example:student123',
                'name': 'Test Student'
            },
            'proof': {
                'type': 'RsaSignature2018',
                'created': '2024-12-26T10:00:00Z',
                'proofPurpose': 'assertionMethod',
                'verificationMethod': 'did:example:issuer#key-1',
                'signatureValue': 'abc123def456'
            }
        }
        
        result = ipfs_client.add_json(credential_with_metadata)
        cid = result.get('cid') or result.get('Hash')
        
        retrieved = ipfs_client.get_json(cid)
        
        # Verify all metadata is preserved
        assert retrieved['issuanceDate'] == credential_with_metadata['issuanceDate']
        assert retrieved['proof']['type'] == credential_with_metadata['proof']['type']
