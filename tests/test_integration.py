"""
Integration tests — Full Circuit Workflow (Issue -> Mine -> Sync -> Verify)
"""
import pytest
import json

def test_full_blockchain_workflow(auth_client, client, sample_credential_data):
    """
    Test the complete flow from issuing a credential to 
    it being anchored in the blockchain and verified publicly.
    """
    # 1. ISSUE
    issue_resp = auth_client.post(
        '/api/issue_credential',
        data=json.dumps(sample_credential_data),
        content_type='application/json'
    )
    assert issue_resp.status_code == 200
    res_data = json.loads(issue_resp.data)
    cred_id = res_data['credential_id']
    block_hash = res_data['block_hash']

    # 2. EXPLORE (Verify it exists in the ledger)
    explore_resp = client.get('/api/blockchain/blocks')
    blocks = json.loads(explore_resp.data)['blocks']
    
    # Latest block should match our issuance
    last_block = blocks[0] # Dashboard usually shows newest first
    assert last_block['hash'] == block_hash
    assert last_block['signed_by'] in ["admin", "test_admin"]

    # 3. PUBLIC VERIFY (Verify integrity via public endpoint)
    # This simulates a verifier/employer checking the transcript
    verify_resp = client.get(f'/verify?id={cred_id}')
    assert verify_resp.status_code == 200
    assert b'Credential Verified' in verify_resp.data or b'ACTIVE &amp; VALID' in verify_resp.data

    # 4. SYSTEM STATS
    stats_resp = auth_client.get('/api/system/stats')
    stats = json.loads(stats_resp.data)['stats']
    assert stats['blockchain']['blocks'] >= 2 # Genesis + our issuance
    assert stats['credentials']['total'] >= 1

def test_system_wipe_recovery(auth_client, client):
    """Verify system reset clears identity and ledger but preserves genesis"""
    # Wipe
    auth_client.post(
        '/api/system/reset',
        data=json.dumps({'confirmation': 'RESET_EVERYTHING'}),
        content_type='application/json'
    )
    
    # Check blockchain
    resp = client.get('/api/blockchain/blocks')
    blocks = json.loads(resp.data)['blocks']
    assert len(blocks) == 1 # Only genesis remains
    assert blocks[0]['index'] == 0
