# Troubleshooting Guide

**Version 2.0** | Common issues and solutions for the Blockchain-Based Verifiable Credentials System

***

## 🔍 Quick Diagnosis

Before diving into specific issues, run this quick checklist:

- [ ] Flask server is running on port 5000
- [ ] Environment variables are properly configured
- [ ] All required files are present in the project directory
- [ ] Database is initialized
- [ ] At least one user account exists
- [ ] Browser cache is cleared

***

## 🚨 Common Issues \& Solutions

### Issue 1: Network Error When Verifying Credentials

**Symptoms:**

- "Network error occurred" message appears
- Verification fails immediately
- No response from server

**Solutions:**

#### Step 1: Verify Server is Running

Check your terminal for:

```
╔══════════════════════════════════════════════════════════════════
║  🎓 Blockchain Credential Verification System
║  🚀 Starting server...
║  📡 Host: 0.0.0.0
║  🔌 Port: 5000
║  🌍 Environment: Development
╚══════════════════════════════════════════════════════════════════

 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

If not running, start it:

```bash
python main.py
```


#### Step 2: Check Browser Console

1. Open Developer Tools (F12)
2. Navigate to "Console" tab
3. Look for error messages
4. Check "Network" tab for failed requests

**Common Console Errors:**

```javascript
// Error: Failed to fetch
// Solution: Server is not running or wrong port

// Error: 404 Not Found
// Solution: Incorrect API endpoint URL

// Error: 500 Internal Server Error
// Solution: Check server logs for Python errors
```


#### Step 3: Verify API Endpoints

Test if server is responding:

```bash
# Test health endpoint
curl http://localhost:5000/api/blockchain_status

# Expected response:
# {"success": true, "blockchain_length": X, ...}
```


***

### Issue 2: Authentication Problems

**Symptoms:**

- "Please login to access this page" message
- Redirected to login page unexpectedly
- Cannot access issuer/holder dashboards

**Solutions:**

#### A. Invalid Credentials

**Problem:** Username or password incorrect

**Solution:**

1. Verify you're using correct credentials
2. Check for typos (usernames are case-sensitive)
3. Ensure user account exists in database

**Reset Password:**

```bash
python scripts/reset_password.py
```


#### B. Session Expired

**Problem:** Session timeout or cookie cleared

**Solution:**

1. Log out completely
2. Close browser
3. Reopen and log in again

#### C. Missing SECRET_KEY

**Problem:** No session secret configured

**Error Message:**

```
RuntimeError: The session is unavailable because no secret key was set.
```

**Solution:**

Create or update `.env` file:

```bash
# .env
SECRET_KEY=your-strong-secret-key-here
SESSION_SECRET=your-session-secret-here
```

Restart the server after changes.

***

### Issue 3: Credential Issuance Failures

**Symptoms:**

- "Error issuing credential" message
- Form submission doesn't complete
- No credential ID returned

**Solutions:**

#### A. Missing Required Fields

**Problem:** Form validation failed

**Solution:**
Ensure all required fields are filled:

```
Required Fields:
├── Student Name (non-empty)
├── Student ID (unique)
├── Degree (non-empty)
├── University (non-empty)
├── GPA (0.0 - 10.0)
├── Graduation Year (valid year)
└── Issue Date (auto-generated)
```


#### B. Duplicate Student ID

**Problem:** Credential already exists for this student

**Error:** "Credential already exists for student ID"

**Solution:**

1. Use different student ID, or
2. Revoke existing credential first, or
3. Create new version of credential

#### C. Cryptographic Key Issues

**Problem:** Missing or corrupted RSA keys

**Error:** "Failed to sign credential"

**Solution:**

```bash
# Delete old keys
rm issuer_keys.pem
rm issuer_public_key.pem

# Restart server (will regenerate keys)
python main.py
```


***

### Issue 4: IPFS Connection Problems

**Symptoms:**

- "Could not store credential on IPFS" warning
- Slow credential issuance
- "Using local storage fallback" message

**Solutions:**

#### A. IPFS Node Not Running (Expected Behavior)

**This is NORMAL** - the system automatically uses local storage fallback.

**To verify fallback is working:**

1. Check for `data/ipfs_storage.json` file
2. Should contain credential data
3. System continues to function normally

#### B. Enable IPFS (Optional)

If you want to use actual IPFS:

**Install IPFS:**

```bash
# Download from https://ipfs.io/
# Or use package manager

# Windows (Chocolatey)
choco install ipfs

# Mac (Homebrew)
brew install ipfs

# Linux
sudo snap install ipfs
```

**Start IPFS Daemon:**

```bash
ipfs init
ipfs daemon
```

**Update `.env`:**

```bash
IPFS_ENABLED=True
```


***

### Issue 5: Database Errors

**Symptoms:**

- "Database is locked" error
- "Table doesn't exist" error
- "No such column" error

**Solutions:**

#### A. Database Not Initialized

**Error:** `sqlalchemy.exc.OperationalError: no such table: users`

**Solution:**

```bash
# Initialize database
python -c "from app.models import init_database; from app.app import app; init_database(app)"

# Or using Makefile
make init-db
```


#### B. Database Locked

**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**

```bash
# Stop all running instances of the app
# Delete database lock file
rm instance/credentials.db-journal

# Restart server
python main.py
```


#### C. Corrupted Database

**Last Resort Solution:**

```bash
# Backup existing database
cp instance/credentials.db instance/credentials.db.backup

# Delete and recreate
rm instance/credentials.db
python -c "from app.models import init_database; from app.app import app; init_database(app)"

# Create new admin user
python scripts/create_admin.py
```


***

### Issue 6: Verification Failures

**Symptoms:**

- "Credential not found" error
- "Invalid signature" error
- "Verification failed" message

**Solutions:**

#### A. Invalid Credential ID

**Problem:** Wrong or incomplete credential ID

**Solution:**

1. Credential IDs look like: `CRED_a1b2c3d4...`
2. Copy the complete ID (no spaces)
3. Try again with correct ID

#### B. Credential Not Yet Issued

**Problem:** Verifying before issuance completes

**Solution:**

1. Wait 2-3 seconds after issuing
2. Check issuer dashboard for confirmation
3. Verify credential appears in registry

#### C. Blockchain Integrity Check Failed

**Problem:** Blockchain data corrupted

**Solution:**

```bash
# Backup current data
cp data/blockchain_data.json data/blockchain_data.json.backup

# Reset blockchain (WARNING: deletes all records)
rm data/blockchain_data.json
python main.py
```


***

### Issue 7: Selective Disclosure Problems

**Symptoms:**

- "Failed to create proof" error
- Disclosed fields not showing
- Proof generation hangs

**Solutions:**

#### A. Invalid Field Selection

**Problem:** Requesting non-existent fields

**Solution:**
Only select fields that exist in the credential:

```
Valid Fields:
├── student_name
├── student_id
├── degree
├── university
├── gpa
├── graduation_year
└── courses (array)
```


#### B. Empty Field Selection

**Problem:** No fields selected

**Solution:**
Select at least one field before generating proof

#### C. Proof Format Error

**Problem:** Generated proof is malformed

**Solution:**

```bash
# Clear credential cache
rm data/credentials_registry.json

# Reissue credential
# Try selective disclosure again
```


***

### Issue 8: Port Already in Use

**Symptoms:**

- "Address already in use" error
- Server fails to start
- Port 5000 unavailable

**Solutions:**

#### Windows:

```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```


#### Mac/Linux:

```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9

# Or use different port
export PORT=5001
python main.py
```


***

### Issue 9: Static Files Not Loading

**Symptoms:**

- Page appears unstyled
- JavaScript not working
- 404 errors for CSS/JS files

**Solutions:**

#### A. Check File Structure

Verify files exist:

```
static/
├── css/
│   └── style.css
└── js/
    └── app.js
```


#### B. Clear Browser Cache

```
Chrome/Edge: Ctrl + Shift + Delete
Firefox: Ctrl + Shift + Delete
Safari: Cmd + Option + E
```


#### C. Hard Refresh

```
Windows: Ctrl + F5
Mac: Cmd + Shift + R
```


***

### Issue 10: Permission Denied Errors

**Symptoms:**

- Cannot write to data files
- Permission errors in logs
- Database creation fails

**Solutions:**

#### Windows:

```powershell
# Run as Administrator
# Or grant full permissions to project folder
```


#### Mac/Linux:

```bash
# Fix permissions
chmod -R 755 .
chmod -R 777 data/
chmod -R 777 logs/
```


***

## 🧪 System Health Check

Run this diagnostic script to check system status:

```bash
# Create health_check.py
python << 'EOF'
import os
import sys
from pathlib import Path

print("🔍 System Health Check\n")

# Check Python version
print(f"✓ Python Version: {sys.version.split()[^0]}")

# Check required files
required_files = [
    'main.py', 'requirements.txt', '.env',
    'app/app.py', 'app/models.py', 'app/auth.py',
    'core/blockchain.py', 'core/crypto_utils.py'
]

missing = []
for file in required_files:
    if Path(file).exists():
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - MISSING")
        missing.append(file)

# Check data directories
data_dirs = ['data', 'logs', 'static', 'templates', 'instance']
for dir in data_dirs:
    if Path(dir).exists():
        print(f"✓ {dir}/ directory")
    else:
        print(f"⚠ {dir}/ directory missing - will be created")

# Check environment variables
env_vars = ['SECRET_KEY', 'SESSION_SECRET']
for var in env_vars:
    if os.getenv(var):
        print(f"✓ {var} is set")
    else:
        print(f"⚠ {var} not set - using default")

if missing:
    print(f"\n❌ Missing {len(missing)} critical files")
    sys.exit(1)
else:
    print("\n✅ All critical files present")
    sys.exit(0)
EOF
```


***

## 📋 Testing Workflow

Follow this step-by-step process to verify system functionality:

### Step 1: Start Server

```bash
# Activate virtual environment (if using)
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Start server
python main.py
```

**Expected Output:**

```
✅ Application initialized successfully!

╔══════════════════════════════════════════════════════════════════
║  🎓 Blockchain Credential Verification System
║  🚀 Starting server...
...
 * Running on http://127.0.0.1:5000
```


### Step 2: Create Admin Account (First Time Only)

```bash
python scripts/create_admin.py
```

Follow prompts to set up administrator credentials.

### Step 3: Issue Test Credential

1. **Navigate to:** `http://localhost:5000`
2. **Login** with admin credentials
3. **Fill form:**

```
Student Name: Test Student
Student ID: TEST001
Degree: B.Tech Computer Science
University: G. Pulla Reddy Engineering College
GPA: 8.5
Graduation Year: 2025
```

4. **Click:** "Issue Credential"
5. **Copy:** Credential ID (e.g., `CRED_abc123...`)

### Step 4: Verify Credential

1. **Navigate to:** `http://localhost:5000/verifier`
2. **Paste:** Credential ID
3. **Click:** "Verify Credential"
4. **Expected:** ✅ Green success message with student details

### Step 5: Test Selective Disclosure

1. **Logout** from issuer
2. **Login** as student (username: TEST001)
3. **Navigate to:** Holder dashboard
4. **Click:** "Share" on credential
5. **Select:** Only GPA field
6. **Generate:** Proof
7. **Copy:** Proof JSON
8. **Verify:** Proof on verifier page
9. **Expected:** Only GPA visible, other fields hidden

***

## 🆘 Emergency Reset

If nothing else works, perform a complete system reset:

```bash
# CAUTION: This deletes ALL data

# Stop server (Ctrl+C)

# Delete data files
rm -rf data/*.json
rm -rf instance/*.db
rm -rf *.pem

# Delete cache
rm -rf __pycache__
rm -rf app/__pycache__
rm -rf core/__pycache__

# Reinstall dependencies
pip install -r requirements.txt

# Initialize fresh database
python -c "from app.models import init_database; from app.app import app; init_database(app)"

# Create new admin
python scripts/create_admin.py

# Restart server
python main.py
```


***

## 📞 Getting Help

If issues persist after following this guide:

### 1. Check Logs

```bash
# Server logs (in terminal)
# Look for stack traces and error messages

# Application logs
cat logs/app.log
```


### 2. Enable Debug Mode

In `.env`:

```bash
FLASK_ENV=development
DEBUG=True
```

**WARNING:** Never enable debug mode in production!

### 3. Contact Development Team

- **Backend Issues:** [@udaycodespace](https://github.com/udaycodespace)
- **Frontend Issues:** [@shashikiran47](https://github.com/shashikiran47)
- **Documentation Issues:** [@tejavarshith](https://github.com/tejavarshith)


### 4. Create GitHub Issue

Include:

- Error messages (full stack trace)
- Steps to reproduce
- System information (OS, Python version)
- Screenshots (if applicable)

***

## 📚 Additional Resources

- **README.md** - System overview and setup
- **AUTHENTICATION_GUIDE.md** - Login and user management
- **DESCRIPTION.md** - Technical architecture
- **API.md** - API endpoint documentation

***

<div align="center">

**Still stuck? Don't worry!**

**Open an issue on GitHub with detailed error logs**

***

*Troubleshooting guide last updated: December 26, 2025*
