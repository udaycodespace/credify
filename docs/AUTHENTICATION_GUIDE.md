# Authentication System Guide

## Overview

The system now has a secure login-based authentication with three user roles:
- **Issuer** (University/Academic Institution)
- **Student** (Credential Holder)
- **Verifier** (Employer)

## Default Test Accounts

### 🔴 Issuer Account (University Admin)
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** Can issue credentials to students

### 🟢 Student Account
- **Username:** `CST001`
- **Password:** `student123`
- **Student ID:** CST001
- **Role:** Can view their credentials and create selective disclosures

### 🟡 Verifier Account (Employer/HR)
- **Username:** `verifier1`
- **Password:** `verifier123`
- **Role:** Can verify credentials (no login required, but login provides additional features)

## How It Works

### 1. **Issuer Login (University)**
- Only logged-in issuers can access the credential issuance page
- Must login with issuer credentials
- Can issue credentials to any student
- Protected by authentication - prevents unauthorized credential creation

### 2. **Student Login**
- Students login with their Student ID as username
- Can only see their own credentials (filtered by student ID)
- Can create selective disclosures to share with employers
- Privacy-protected - each student sees only their data

### 3. **Verifier Access**
- Verifier page is open to everyone (no login required)
- Anyone can verify credential authenticity
- This allows public verification of credentials

## Complete Workflow

### Step 1: Issue a Credential (As Issuer)
1. Go to http://localhost:5000
2. Click "Login" button (top right)
3. Login with:
   - Username: `admin`
   - Password: `admin123`
4. You'll be redirected to the Issuer page
5. Fill in student details:
   - Student Name: `John Doe`
   - Student ID: `CST001` (must match the student account)
   - Degree: `B.Tech Computer Science`
   - University: `G. Pulla Reddy Engineering College`
   - GPA: `8.5`
   - Graduation Year: `2025`
6. Click "Issue Credential"
7. Credential will be created and stored

### Step 2: View Credentials (As Student)
1. Logout from issuer account
2. Login as student:
   - Username: `CST001`
   - Password: `student123`
3. You'll see only your credentials (filtered by student ID CST001)
4. Click "View" to see full credential details
5. Click "Share" to create selective disclosure

### Step 3: Create Selective Disclosure
1. On student portal, click "Share" button
2. Select which fields to disclose (e.g., only GPA)
3. Click "Generate Proof"
4. Copy the generated JSON proof

### Step 4: Verify Credential (As Verifier)
1. No login required - directly go to http://localhost:5000/verifier
2. Paste the credential ID or selective disclosure proof
3. Click "Verify"
4. See verification results

## Security Features

### 1. **Role-Based Access Control**
- Issuer pages require issuer role
- Student pages require student role
- Verifier pages are open to all

### 2. **Session Management**
- Secure Flask sessions
- Automatic logout on session expiry
- Session data includes: user_id, username, role, student_id

### 3. **Password Security**
- Passwords are hashed using Werkzeug's password hashing
- Never stored in plain text
- Secure password verification

### 4. **Data Privacy**
- Students see only their credentials
- Credentials filtered by student_id
- Selective disclosure protects sensitive information

## File Structure

```
New Files Created:
├── models.py              # Database models (User table)
├── auth.py                # Authentication decorators
├── templates/login.html   # Login page
└── AUTHENTICATION_GUIDE.md

Modified Files:
├── app.py                 # Added login routes and authentication
├── templates/base.html    # Added login/logout buttons
└── templates/index.html   # Updated with login links
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL,           -- 'issuer', 'student', or 'verifier'
    student_id VARCHAR(50) UNIQUE,       -- For students only
    full_name VARCHAR(120),
    email VARCHAR(120) UNIQUE,
    created_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Adding New Users

### Option 1: Via Python Shell
```python
from app import app, db
from models import User

with app.app_context():
    # Create new student
    student = User(
        username='CST002',
        role='student',
        student_id='CST002',
        full_name='Jane Smith',
        email='jane@gprec.ac.in'
    )
    student.set_password('password123')
    db.session.add(student)
    db.session.commit()
```

### Option 2: Via SQL (Direct Database Access)
```sql
-- First, hash the password using Python:
-- from werkzeug.security import generate_password_hash
-- print(generate_password_hash('mypassword'))

INSERT INTO users (username, password_hash, role, student_id, full_name, email)
VALUES ('CST003', 'hashed_password_here', 'student', 'CST003', 'Bob Johnson', 'bob@gprec.ac.in');
```

## Common Issues & Solutions

### Issue 1: "Please login to access this page"
**Solution:** You're trying to access a protected page. Login with appropriate credentials.

### Issue 2: "Access denied. This page is only for issuers"
**Solution:** You're logged in with wrong role. Logout and login with issuer account.

### Issue 3: Student sees no credentials
**Solution:** 
- Make sure credentials were issued with the correct student_id
- The student_id in the credential must match the student's student_id in the database

### Issue 4: Can't issue credentials
**Solution:** 
- Make sure you're logged in as an issuer
- Check that all required fields are filled

## Testing Checklist

- [ ] Login as issuer (admin/admin123)
- [ ] Issue credential for student CST001
- [ ] Logout from issuer
- [ ] Login as student (CST001/student123)
- [ ] View issued credential
- [ ] Create selective disclosure (select only GPA)
- [ ] Copy the proof
- [ ] Logout from student
- [ ] Go to verifier page (no login needed)
- [ ] Verify the selective disclosure proof
- [ ] Confirm only GPA is visible, not full transcript

## Production Deployment Considerations

1. **Change Default Passwords:** All default passwords must be changed
2. **Use Strong Secret Key:** Set a strong SESSION_SECRET environment variable
3. **Enable HTTPS:** Use SSL/TLS for production
4. **Rate Limiting:** Add rate limiting to prevent brute force attacks
5. **Email Verification:** Add email verification for new accounts
6. **Password Reset:** Implement password reset functionality
7. **Audit Logging:** Log all authentication attempts and credential issuances

## Environment Variables Required

```bash
# Required for production
SESSION_SECRET=your-super-secret-key-change-this
DATABASE_URL=postgresql://user:password@host:port/database

# Optional
FLASK_ENV=production
```

## API Endpoints

### Public Endpoints (No Auth Required)
- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Login submission
- `GET /logout` - Logout
- `GET /verifier` - Verifier page
- `POST /api/verify_credential` - Verify credential
- `GET /api/blockchain_status` - System status

### Protected Endpoints
- `GET /issuer` - Requires issuer role
- `POST /api/issue_credential` - Requires issuer role
- `GET /holder` - Requires student role
- `POST /api/selective_disclosure` - Requires student role
- `GET /api/get_credential/<id>` - Requires authentication

## Support

For issues or questions:
1. Check the TROUBLESHOOTING.md file
2. Review server logs for errors
3. Check browser console for client-side errors
4. Ensure all environment variables are set correctly
