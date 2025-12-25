# Troubleshooting Guide

## Network Error When Verifying Credentials

If you're getting a network error when verifying credentials, follow these steps:

### Step 1: Check if the Server is Running

Make sure your Flask server is running. You should see:
```
* Running on http://0.0.0.0:5000
* Running on http://127.0.0.1:5000
```

If not, start it with:
```bash
python main.py
```

### Step 2: Set the SESSION_SECRET Environment Variable

The application requires a session secret key. Before running the server:

**Windows (Command Prompt):**
```cmd
set SESSION_SECRET=my-super-secret-key-12345
python main.py
```

**Windows (PowerShell):**
```powershell
$env:SESSION_SECRET="my-super-secret-key-12345"
python main.py
```

**macOS/Linux:**
```bash
export SESSION_SECRET=my-super-secret-key-12345
python main.py
```

### Step 3: Check Browser Console for Detailed Errors

1. Open your browser's Developer Tools (Press F12)
2. Go to the "Console" tab
3. Try verifying a credential again
4. Look for error messages - they will now show detailed information

### Step 4: Verify the Files Exist

Make sure these files are present in your project folder:
```
- app.py
- blockchain.py
- credential_manager.py
- crypto_utils.py
- ipfs_client.py
- main.py
- templates/
  - base.html
  - verifier.html
  - issuer.html
  - holder.html
- static/
  - app.js
  - style.css
```

### Step 5: Check if Credential was Actually Issued

Before verifying, make sure you've issued at least one credential:
1. Go to http://localhost:5000/issuer
2. Fill out the form with student information
3. Click "Issue Credential"
4. Copy the Credential ID that appears
5. Go to http://localhost:5000/verifier
6. Paste the Credential ID and verify

### Step 6: Clear Browser Cache

Sometimes the browser caches old JavaScript files:
1. Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
2. Clear cached images and files
3. Refresh the page (Ctrl+F5 or Cmd+Shift+R)

### Step 7: Test with a Valid Credential ID

After issuing a credential, the system will display a credential ID like:
```
25407c36-ad60-4ba1-a6ec-c1cae2bb121a
```

Use this exact ID to test verification.

### Common Error Messages and Solutions

#### "Credential not found in registry"
- Make sure you copied the credential ID correctly
- Check that credentials_registry.json file exists

#### "Could not retrieve credential from IPFS"
- This is normal - the system uses local storage fallback
- Check that ipfs_storage.json file exists

#### "Network error occurred"
- Check if the server is running on port 5000
- Make sure SESSION_SECRET is set
- Check browser console for detailed errors

### Still Having Issues?

1. Stop the server (Ctrl+C)
2. Delete these files if they exist:
   - credentials_registry.json
   - blockchain_data.json
   - ipfs_storage.json
   - issuer_keys.pem
3. Restart the server: `python main.py`
4. Try issuing a new credential and verifying it

### Testing the System Step-by-Step

1. **Start the server:**
   ```bash
   set SESSION_SECRET=test-key-123
   python main.py
   ```

2. **Issue a credential:**
   - Open http://localhost:5000/issuer
   - Fill in:
     - Student Name: John Doe
     - Student ID: CST001
     - Degree: B.Tech Computer Science
     - University: G. Pulla Reddy Engineering College
     - GPA: 8.5
     - Graduation Year: 2025
   - Click "Issue Credential"
   - Copy the credential ID

3. **Verify the credential:**
   - Open http://localhost:5000/verifier
   - Paste the credential ID
   - Click "Verify Credential"
   - You should see success message with student details

If you still see errors, check the browser console (F12) for detailed error messages.
