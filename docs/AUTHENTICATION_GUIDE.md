# 🔐 Authentication System Guide

**Version 2.2** | Hardened Multi-Portal Authentication for Private (PVT) Blockchain Infrastructure

***

## 📌 Overview

The Credify system has transitioned to a **Hardened Private Blockchain** architecture. Authentication is now isolated into dedicated role-specific portals to ensure maximum security and a premium user experience:

- **🏛️ Issuer Portal (`/issuer`)** — Academic Institutions & Network Controllers (MFA Enforced)
- **👨‍🎓 Student Portal (`/holder`)** — Credential Holders & Asset Managers
- **💼 Verifier Portal (`/verifier`)** — Public verification gateway (No login required)

Each role is strictly isolated via a **Multi-Portal Gatekeeper** to prevent unauthorized cross-portal access.

***

## 🔐 Authentication Architecture

### Identity Trust Tiers (ITT)

```
┌─────────────────────────────────────────────────────────────┐
│                 PRIVATE NETWORK ENTRANCE                    │
├─────────────────────────────────────────────────────────────┤
│  Request → Portal Detection → Role Context → Entry Process  │
└─────────────────────────────────────────────────────────────┘
                             ▼
         ┌───────────────────┴───────────────────┐
         │                                       │
    ┌────▼─────┐                           ┌─────▼─────┐
    │ ISSUER   │                           │ STUDENT   │
    │(/issuer) │                           │(/holder)  │
    └────┬─────┘                           └─────┬─────┘
         │                                       │
   ┌─────▼─────┐                           ┌─────▼─────┐
   │ MFA CHECK │                           │ JWT/SID   │
   │ (TOTP)    │                           │ VALIDATION│
   └─────┬─────┘                           └─────┬─────┘
         │                                       │
    HIGH-SECURITY                           ACADEMIC HUB
    DASHBOARD                               ACCESS
```

***

## 👥 Administrative Accounts

### 🏛️ Issuer Account (Production Grade)

> [!IMPORTANT]
> **Issuer accounts now require Multi-Factor Authentication (MFA).** Legacy default passwords like `admin123` are automatically randomized by the system during startup if MFA is active to "break the chain" of insecure access.

```
Access:   Credential Minting, Ledger Management, System Governance
Security: Username + Password + 6-Digit TOTP Token
```

### 👨‍🎓 Student Account (Verified Access)

```
Access:   On-Chain Asset Viewing, Selective Disclosure, Identity Sharing
Security: Student ID (Roll Number) + Password
```

***

## 🔄 Hardened Authentication Workflow

### Step 1: Administrator Entry (Issuer Role)

1. **Navigate to Issuer Portal**
   ```
   http://localhost:5000/issuer
   ```
2. **Standard Credentials**
   - Enter your authorized username and password.
3. **MFA Verification**
   - Provide the 6-digit rolling code from your Google Authenticator or Authy app.
   - **Emergency Bypass**: In case of lost phone, use the administrative secret: `adminadmin123` (Emergency use only).
4. **Administrative Dashboard**
   - Access the one-page responsive hub for credential management.

### Step 2: Student Entry (Holder Role)

1. **Navigate to Student Portal**
   ```
   http://localhost:5000/holder
   ```
2. **Roll Number Access**
   - Enter your Student Roll Number as the username.
   - Enter your secure password.
3. **Asset Dashboard**
   - Access your private academic record vault.

4. **Privacy Protection**
    - Only sees own credentials
    - Cannot access other students' data
    - Complete data ownership

***

### Step 3: Create Selective Disclosure (Student)

1. **Select Credential**
    - Navigate to credential in dashboard
    - Click "Share" button
2. **Choose Fields to Disclose**

```
Selective Disclosure Options:
├── ✅ Student Name
├── ✅ Degree
├── ✅ GPA (only)
├── ✅ University
├── ❌ Student ID (hidden)
├── ❌ Date of Birth (hidden)
└── ❌ Full Transcript (hidden)
```

3. **Generate Zero-Knowledge Proof**
    - Click "Generate Proof"
    - System creates cryptographic proof
    - Only selected fields included
4. **Share Proof**

```json
{
  "credential_id": "CRED_xxxxx",
  "disclosed_fields": {
    "student_name": "John Doe",
    "degree": "B.Tech Computer Science",
    "gpa": 8.5
  },
  "proof": "cryptographic_proof_data",
  "timestamp": "2024-12-26T14:51:00Z"
}
```

    - Copy JSON proof
    - Share with verifier via secure channel

***

### Step 4: Verify Credential (Verifier Role)

1. **Access Verifier Page**

```
Direct URL: http://localhost:5000/verifier
No authentication required (public access)
```

2. **Submit Verification Request**

```
Input Options:
├── Credential ID (full verification)
├── Selective Disclosure Proof (partial)
└── QR Code (future feature)
```

3. **Verification Process**

```
System Checks:
├── ✓ Blockchain hash validation
├── ✓ IPFS data retrieval
├── ✓ Cryptographic signature verification
├── ✓ Revocation status check
├── ✓ Issuer authenticity
└── ✓ Timestamp validation
```

4. **View Results**

```
Verification Response:
├── Status: Valid / Invalid / Revoked
├── Issuer: University name
├── Issue Date: Timestamp
├── Disclosed Data: Only shared fields
└── Verification Proof: Blockchain reference
```


***

## 🛡️ Security Features

### 1. Password Security

```python
# Implementation Details (Reference Only)
- Algorithm: Werkzeug PBKDF2-SHA256
- Iterations: 260,000+
- Salt: Random per user
- Storage: Hashed only, never plain text
```


### 2. Session Management

```python
Session Data Structure:
{
    'user_id': int,
    'username': str,
    'role': str,  # 'issuer', 'student', 'verifier'
    'student_id': str,  # For students only
    'created_at': timestamp,
    'expires_at': timestamp
}
```


### 3. Role-Based Access Control

```
Access Matrix:
┌──────────────┬─────────┬─────────┬──────────┐
│ Resource     │ Issuer  │ Student │ Verifier │
├──────────────┼─────────┼─────────┼──────────┤
│ Issue Cred   │   ✅    │   ❌    │    ❌   │
│ View Own     │   N/A    │   ✅    │    N/A  │
│ Revoke       │   ✅    │   ❌    │    ❌   │
│ Verify       │   ✅    │   ✅    │    ✅   │
│ Selective    │   ❌    │   ✅    │    ❌   │
└──────────────┴─────────┴─────────┴──────────┘
```


### 4. Data Privacy

- **Student Isolation:** Each student sees only their credentials
- **Filter by ID:** Automatic filtering by `student_id`
- **Selective Disclosure:** Students control data sharing
- **Encrypted Storage:** Sensitive data encrypted at rest

***

## 📁 System Architecture

### Modified/New Files

```
app/
├── models.py              ✅ User model & database schema
├── auth.py                ✅ Authentication decorators & middleware
└── config.py              ✅ Security configurations

templates/
├── login.html             ✅ Login interface
├── base.html              ✅ Updated with auth buttons
├── issuer.html            ✅ Protected issuer dashboard
├── holder.html            ✅ Protected student dashboard
└── verifier.html          ✅ Public verifier interface

docs/
└── AUTHENTICATION_GUIDE.md ✅ This document
```


***

## 🗄️ Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK(role IN ('issuer', 'student', 'verifier')),
    student_id VARCHAR(50) UNIQUE,
    full_name VARCHAR(120),
    email VARCHAR(120) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON
);

CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_student_id ON users(student_id);
CREATE INDEX idx_role ON users(role);
```


***

## 👤 User Management

### Creating New Users

#### Method 1: Python Script (Recommended)

```python
# scripts/create_user.py
from app.app import app
from app.models import db, User

with app.app_context():
    # Create new student
    student = User(
        username='CST002',
        role='student',
        student_id='CST002',
        full_name='Jane Smith',
        email='jane@example.edu'
    )
    student.set_password('secure_password_here')
    
    db.session.add(student)
    db.session.commit()
    print(f"✅ User {student.username} created successfully")
```


#### Method 2: Interactive Script

```bash
python scripts/create_admin.py
```

Follow the prompts to create users interactively.

***

## 🔌 API Endpoints

### Public Endpoints (No Authentication)

| Endpoint | Method | Description |
| :-- | :-- | :-- |
| `/` | GET | Home page |
| `/login` | GET | Login page |
| `/login` | POST | Login submission |
| `/logout` | GET | Logout \& session clear |
| `/verifier` | GET | Public verifier interface |
| `/api/verify_credential` | POST | Verify credential |
| `/api/blockchain_status` | GET | System statistics |

### Protected Endpoints (Authentication Required)

| Endpoint | Method | Role | Description |
| :-- | :-- | :-- | :-- |
| `/issuer` | GET | Issuer | Issuer dashboard |
| `/api/issue_credential` | POST | Issuer | Issue new credential |
| `/api/revoke_credential` | POST | Issuer | Revoke credential |
| `/holder` | GET | Student | Student dashboard |
| `/api/selective_disclosure` | POST | Student | Create disclosure proof |
| `/api/get_credential/<id>` | GET | Auth | Get credential details |


***

## ⚙️ Environment Configuration

### Required Environment Variables

```bash
# Security (REQUIRED)
SECRET_KEY=your-secret-key-change-in-production
SESSION_SECRET=your-session-secret-change-in-production

# Database
DATABASE_URL=sqlite:///credentials.db  # Development
# DATABASE_URL=postgresql://user:pass@host:port/db  # Production

# Flask Configuration
FLASK_ENV=development  # Change to 'production' for deployment
DEBUG=False  # Set to False in production

# Server
HOST=0.0.0.0
PORT=5000

# Optional Features
IPFS_ENABLED=False
ENABLE_EMAIL_VERIFICATION=False
```


### Security Best Practices

⚠️ **CRITICAL: Never expose these in version control:**

- `.env` file should be in `.gitignore`
- Use environment-specific configurations
- Rotate secrets regularly in production
- Use strong, randomly generated keys

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```


***

## 🐛 Troubleshooting

### Common Issues \& Solutions

#### Issue 1: "Please login to access this page"

**Cause:** Trying to access protected route without authentication
**Solution:** Login with appropriate credentials for the required role

#### Issue 2: "Access denied. This page is only for [role]"

**Cause:** Logged in with incorrect role
**Solution:** Logout and login with correct role credentials

#### Issue 3: Student sees no credentials

**Cause:** Student ID mismatch between credential and user account
**Solution:**

- Verify student ID in user profile
- Ensure credentials issued with correct student ID
- Check database for data consistency


#### Issue 4: Cannot issue credentials

**Cause:** Not logged in as issuer or missing required fields
**Solution:**

- Confirm login with issuer role
- Validate all required fields are filled
- Check browser console for JavaScript errors


#### Issue 5: Session expires unexpectedly

**Cause:** Short session timeout or browser cookie issues
**Solution:**

- Check `SESSION_COOKIE_SECURE` settings
- Increase `PERMANENT_SESSION_LIFETIME` in config
- Clear browser cookies and re-login

***

## ✅ Testing Checklist

Use this checklist to verify complete system functionality:

- [ ] **Issuer Workflow**
    - [ ] Login as issuer
    - [ ] Access issuer dashboard
    - [ ] Issue credential for test student
    - [ ] View issued credentials list
    - [ ] Logout successfully
- [ ] **Student Workflow**
    - [ ] Login as student
    - [ ] View only own credentials (data isolation)
    - [ ] Open credential details
    - [ ] Create selective disclosure (GPA only)
    - [ ] Copy generated proof
    - [ ] Logout successfully
- [ ] **Verifier Workflow**
    - [ ] Access verifier page (no login)
    - [ ] Paste credential ID
    - [ ] Verify full credential
    - [ ] Paste selective disclosure proof
    - [ ] Verify partial credential (only disclosed fields visible)
- [ ] **Security Testing**
    - [ ] Attempt to access issuer page as student (should fail)
    - [ ] Attempt to access student credentials as different student (should fail)
    - [ ] Verify session expires after timeout
    - [ ] Test logout clears session data

***

## 🚀 Production Deployment Checklist

Before deploying to production:

- [ ] **Change all default passwords**
- [ ] **Set strong SECRET_KEY and SESSION_SECRET**
- [ ] **Enable HTTPS/TLS (SSL certificates)**
- [ ] **Configure production database (PostgreSQL recommended)**
- [ ] **Set FLASK_ENV=production**
- [ ] **Disable DEBUG mode**
- [ ] **Implement rate limiting (Flask-Limiter)**
- [ ] **Add email verification for new accounts**
- [ ] **Set up password reset functionality**
- [ ] **Enable audit logging for all authentication events**
- [ ] **Configure secure session cookies**
- [ ] **Set up monitoring and alerting**
- [ ] **Perform security audit (OWASP guidelines)**
- [ ] **Configure firewall rules**
- [ ] **Set up automated backups**

***

## 📞 Support \& Contributions

### Getting Help

If you encounter issues not covered in this guide:

1. **Check Documentation:**
    - Review `/docs` folder for additional guides
    - See `TROUBLESHOOTING.md` for common issues
2. **Review Logs:**
    - Check server logs in `/logs` directory
    - Enable debug mode temporarily for detailed errors
    - Review browser console for client-side errors
3. **Contact Development Team:**
    - **Backend \& Authentication:** [@udaycodespace](https://github.com/udaycodespace)
    - **Frontend \& UI:** [@shashikiran47](https://github.com/shashikiran47)
    - **Testing \& Documentation:** [@tejavarshith](https://github.com/tejavarshith)
4. **Community Support:**
    - Open an issue on GitHub repository
    - Include error messages and logs
    - Provide steps to reproduce the issue

***

## 📚 Additional Resources

- **W3C Verifiable Credentials:** [https://www.w3.org/TR/vc-data-model/](https://www.w3.org/TR/vc-data-model/)
- **Flask Security Best Practices:** [https://flask.palletsprojects.com/en/latest/security/](https://flask.palletsprojects.com/en/latest/security/)
- **OWASP Authentication Cheat Sheet:** [https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

***

## 📄 Version History

**v2.0** (Current)

- Enhanced security features
- Improved session management
- Comprehensive documentation
- Production-ready configurations

**v1.0**

- Initial authentication implementation
- Basic role-based access control
- Core login/logout functionality

***

<div align="center">

**Security First | Privacy Preserved | Trust Verified**

</div>

***

> [!NOTE]
> **🔐 AUTHENTICATION GUIDE: UPDATED**
> 
> **Architecture Version:** 2.1.0
> 
> **Current Edited Date:** `2026-03-08`

