# System Description \& Technical Architecture

**Version 2.1 (Elite UI/UX Overhaul)** | Blockchain-Based Verifiable Credentials System for Academic Transcripts

***

## 📋 Project Overview

This is a production-ready blockchain-based verifiable credential system designed specifically for academic transcript verification. The system implements **W3C Verifiable Credentials standards** combined with blockchain immutability, IPFS distributed storage, and advanced cryptographic verification protocols.

**Academic Context:**
Developed as a B.Tech Final Year Project for the Computer Science Engineering department at G. Pulla Reddy Engineering College (Autonomous), Kurnool.

**Problem Statement:**
Traditional academic credential verification is centralized, slow, prone to forgery, and lacks privacy protection. This system provides a decentralized, tamper-proof, privacy-preserving alternative.

**Solution:**
A comprehensive platform where universities issue cryptographically signed digital credentials, students maintain complete ownership and control, and employers verify authenticity instantly without intermediaries.

***

## 🏗️ System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Issuer   │  │ Student  │  │ Verifier │  │ Tutorial │       │
│  │ Portal   │  │ Portal   │  │ Portal   │  │ System   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │
┌───────┼─────────────┼─────────────┼─────────────┼──────────────┐
│       │      PRESENTATION LAYER (Flask + Jinja2)│              │
│       │             │             │             │              │
│  ┌────▼─────────────▼─────────────▼─────────────▼────┐         │
│  │           Flask Application (app.py)               │        │
│  │  • Route Handlers  • Session Management            │        │
│  │  • Authentication  • Role-Based Access Control     │        │
│  └────────────────────┬───────────────────────────────┘        │
└────────────────────────┼───────────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────── ──┐
│              BUSINESS LOGIC LAYER (core/)                     │
│                        │                                      │
│  ┌──────────────┬──────▼──────┬──────────────┬──────────────┐ │
│  │ Credential   │ Blockchain  │ Cryptography │ IPFS Client  │ │
│  │ Manager      │ Engine      │ Manager      │              │ │
│  │              │             │              │              │ │
│  │ • Issue      │ • Blocks    │ • RSA-2048   │ • Storage    │ │
│  │ • Verify     │ • Mining    │ • Signatures │ • Retrieval  │ │
│  │ • Revoke     │ • Hashing   │ • Keys       │ • Fallback   │ │
│  │ • Disclose   │ • Validate  │ • SHA-256    │              │ │
│  └──────┬───────┴──────┬──────┴──────┬───────┴──────┬───────┘ │
└─────────┼──────────────┼─────────────┼──────────────┼─────────┘
          │              │             │              │
┌─────────┼──────────────┼─────────────┼──────────────┼──────┐
│         │      DATA PERSISTENCE LAYER               │      │
│         │              │             │              │      │
│  ┌──────▼──────┐  ┌───▼────┐  ┌─────▼─────┐  ┌────▼──────┐ │
│  │ SQLite DB   │  │ IPFS   │  │Blockchain │  │   Keys    │ │
│  │ (Users,     │  │Network │  │   JSON    │  │   PEM     │ │
│  │ Sessions)   │  │Storage │  │   Store   │  │  Storage  │ │
│  └─────────────┘  └────────┘  └───────────┘  └───────────┘ │
└────────────────────────────────────────────────────────────┘
```


***

## 🎨 Frontend Architecture

### Technology Stack

**Framework:** Flask with Jinja2 templating engine
**UI Framework:** Custom Bootstrap-based dark theme
**Client-side Logic:** Vanilla JavaScript (ES6+)
**AJAX:** Asynchronous credential operations
**Icons:** Font Awesome for UI elements

### Design Pattern: Multi-Role Interface

```
┌─────────────────────────────────────────────────────┐
│              BASE TEMPLATE (base.html)              │
│  • Navigation Bar    • Authentication Status        │
│  • Common Styles     • Footer                       │
└─────┬───────────────┬───────────────┬───────────────┘
      │               │               │
┌─────▼──────┐  ┌────▼─────┐  ┌──────▼──────┐
│  ISSUER    │  │ STUDENT  │  │  VERIFIER   │
│  PORTAL    │  │ PORTAL   │  │   PORTAL    │
│            │  │          │  │             │
│ • Issue    │  │ • View   │  │ • Verify    │
│ • Revoke   │  │ • Share  │  │ • Validate  │
│ • Manage   │  │ • Proof  │  │ • Report    │
└────────────┘  └──────────┘  └─────────────┘
```


### User Interface Components

**1. Issuer Dashboard**

- Credential issuance form with validation
- Issued credentials list with search/filter
- Revocation management interface
- System statistics dashboard

**2. Student Portal**

- Personal credential gallery
- Detailed credential viewer with Hero-style branding
- Selective disclosure builder
- **Elite 10/10 PDF Export:** Institutional-grade transcript generation with blockchain hashes and QR codes.

**3. Verifier Interface**

- Quick verification input
- Real-time validation feedback
- Detailed verification report
- Blockchain proof display

**4. Tutorial System**

- Interactive step-by-step guide
- Role-specific tutorials
- Visual workflow diagrams
- Best practices documentation

***

## ⚙️ Backend Architecture

### Framework: Flask (Python 3.10+)

**Architecture Pattern:** Modular Component-Based Design
**Design Philosophy:** Separation of concerns with single responsibility principle

### Core Application Structure

```python
app/
├── app.py              # Main Flask application
│   ├── Route Definitions
│   ├── Request Handlers
│   ├── Response Formatting
│   └── Error Handling
│
├── auth.py             # Authentication & Authorization
│   ├── Login/Logout Logic
│   ├── Session Management
│   ├── Role-Based Decorators
│   └── Permission Checks
│
├── models.py           # Database Models
│   ├── User Model
│   ├── Credential Registry
│   └── Database Operations
│
└── config.py           # Configuration Management
    ├── Environment Variables
    ├── Security Settings
    └── Feature Flags
```


***

## 🔧 Core Components

### 1. Blockchain Engine (`core/blockchain.py`)

**Purpose:** Provides immutable, tamper-proof record keeping for credential hashes

**Implementation Details:**

```python
Class: SimpleBlockchain
- Genesis Block: Hardcoded initial block with hash '0'
- Consensus: Proof-of-Work with configurable difficulty
- Hashing: SHA-256 for block integrity
- Validation: Full chain integrity verification
```

**Key Features:**

- **Block Mining:** Proof-of-work algorithm finds valid nonce
- **Hash Calculation:** SHA-256(index + timestamp + data + previous_hash + nonce)
- **Chain Validation:** Recursive verification from genesis to current block
- **Persistence:** JSON-based storage with atomic writes

**Data Structure:**

```python
Block {
    index: int,
    timestamp: str (ISO 8601),
    data: dict (credential metadata),
    previous_hash: str (SHA-256 hex),
    hash: str (SHA-256 hex),
    nonce: int (proof-of-work)
}
```


***

### 2. Cryptographic Manager (`core/crypto_utils.py`)

**Purpose:** Handles all cryptographic operations for credential authenticity

**Implementation:**

- **Algorithm:** RSA-2048 with OAEP padding
- **Hashing:** SHA-256 for data integrity
- **Key Format:** PEM encoding for portability
- **Security:** Industry-standard encryption practices

**Key Operations:**

```python
Class: CryptoManager

Methods:
├── generate_keys()
│   └── Creates RSA-2048 key pair
│
├── sign_data(data: str) -> str
│   └── Creates digital signature with private key
│
├── verify_signature(data: str, signature: str) -> bool
│   └── Validates signature with public key
│
└── hash_data(data: str) -> str
    └── SHA-256 hash for integrity verification
```

**Security Features:**

- Private keys stored securely in PEM format
- Public keys distributed for verification
- Signature includes timestamp for replay attack prevention
- Hash-based message authentication

***

### 3. IPFS Client (`core/ipfs_client.py`)

**Purpose:** Decentralized storage for credential data with high availability

**Architecture:**

```
┌────────────────────────────────────────────┐
│        IPFS Client (ipfs_client.py)        │
├────────────────────────────────────────────┤
│  Primary:   Local IPFS Node (127.0.0.1)   │
│  Secondary: Infura IPFS Gateway            │
│  Fallback:  Local Encrypted Storage        │
└────────────────────────────────────────────┘
```

**Fallback Strategy:**

1. **First Attempt:** Local IPFS node (port 5001)
2. **Second Attempt:** Infura IPFS gateway (HTTPS)
3. **Final Fallback:** Local JSON storage (data/ipfs_storage.json)

**Features:**

- Content-addressed storage (CID-based)
- Automatic endpoint failover
- Data redundancy through multiple gateways
- Local caching for performance

**API Operations:**

```python
Class: IPFSClient

Methods:
├── add_json(data: dict) -> str (CID)
│   └── Stores JSON data, returns content ID
│
├── get_json(cid: str) -> dict
│   └── Retrieves data by content ID
│
├── is_connected() -> bool
│   └── Health check for IPFS availability
│
└── get_storage_stats() -> dict
    └── Returns storage metrics
```


***

### 4. Credential Manager (`core/credential_manager.py`)

**Purpose:** W3C Verifiable Credentials compliance and complete lifecycle management

**Standards Compliance:**

- W3C Verifiable Credentials Data Model 1.1
- JSON-LD context for semantic interoperability
- DID (Decentralized Identifiers) alignment

**Core Functionality:**

**A. Credential Issuance**

```python
def issue_credential(data: dict) -> dict:
    """
    Process:
    1. Validate input data
    2. Generate W3C compliant credential structure
    3. Create cryptographic signature
    4. Store full credential on IPFS
    5. Record credential hash on blockchain
    6. Update credential registry
    7. Return credential ID and metadata
    """
```

**B. Selective Disclosure**

```python
def selective_disclosure(credential_id: str, fields: list) -> dict:
    """
    Privacy-preserving data sharing:
    1. Retrieve full credential
    2. Extract only requested fields
    3. Create cryptographic proof
    4. Maintain signature validity
    5. Return minimal disclosure proof
    """
```

**C. Verification**

```python
def verify_credential(credential_id: str) -> dict:
    """
    Multi-layer verification:
    1. Retrieve from IPFS/local storage
    2. Verify cryptographic signature
    3. Check blockchain integrity
    4. Validate revocation status
    5. Return comprehensive verification result
    """
```

**D. Revocation**

```python
def revoke_credential(credential_id: str, reason: str) -> bool:
    """
    Credential lifecycle management:
    1. Mark credential as revoked
    2. Record revocation on blockchain
    3. Update credential registry
    4. Prevent future verifications
    """
```


***

### 5. Zero-Knowledge Proof Manager (`core/zkp_manager.py`)

**Purpose:** Privacy-preserving credential verification

**Implementations:**

**A. Range Proofs**

- Prove GPA is above threshold without revealing exact value
- Example: Prove GPA > 7.5 without disclosing actual 8.5 GPA

**B. Membership Proofs**

- Prove credential belongs to specific set
- Example: Prove degree is in ["B.Tech", "M.Tech"] without revealing which

**Cryptographic Technique:**

- Commitment schemes for data hiding
- Challenge-response protocols
- Zero-knowledge property: no information leakage

***

## 🗄️ Data Storage Solutions

### 1. Blockchain Storage

**Location:** `data/blockchain_data.json`

**Structure:**

```json
{
  "chain": [
    {
      "index": 0,
      "timestamp": "2024-01-01T00:00:00Z",
      "data": {"type": "genesis"},
      "previous_hash": "0",
      "hash": "abc123...",
      "nonce": 0
    }
  ],
  "difficulty": 4
}
```

**Characteristics:**

- Immutable append-only log
- Cryptographically linked blocks
- Proof-of-work consensus
- JSON serialization for portability

***

### 2. IPFS Distributed Storage

**Primary Storage:** IPFS Network (decentralized)
**Fallback Storage:** `data/ipfs_storage.json` (local)

**Content Addressing:**

```
CID = hash(credential_data)
Example: QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
```

**Benefits:**

- Deduplication (same content = same CID)
- Distributed availability
- Content integrity verification
- Censorship resistance

***

### 3. Credential Registry

**Location:** `data/credentials_registry.json`

**Purpose:** Fast credential lookup and metadata management

**Structure:**

```json
{
  "CRED_001": {
    "credential_id": "CRED_001",
    "student_id": "CST001",
    "ipfs_cid": "Qm...",
    "blockchain_hash": "abc123...",
    "issue_date": "2024-12-26T14:56:00Z",
    "issuer": "G. Pulla Reddy Engineering College",
    "status": "active",
    "version": 1
  }
}
```


***

### 4. User Database

**Technology:** SQLite (Development) / PostgreSQL (Production)
**ORM:** SQLAlchemy

**Schema:**

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL,
    student_id VARCHAR(50) UNIQUE,
    full_name VARCHAR(120),
    email VARCHAR(120) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```


***

## 🔄 Data Flow Architecture

### Credential Issuance Flow

```
┌──────────┐
│ ISSUER   │ (1) Enters student transcript data
│ (Admin)  │
└────┬─────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Credential Manager                    │
│  • Validates data                      │
│  • Generates W3C credential            │
│  • Creates unique ID                   │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Cryptographic Manager                 │ (2) Signs with RSA-2048
│  • Signs with private key              │
│  • Creates SHA-256 hash                │
└────┬───────────────────────────────────┘
     │
     ├─────────────┬─────────────────────┐
     │             │                     │
     ▼             ▼                     ▼
┌─────────┐  ┌──────────┐        ┌──────────────┐
│  IPFS   │  │Blockchain│  (3)   │   Registry   │
│ Storage │  │  Engine  │ Record │    JSON      │
│         │  │          │        │              │
│ Stores  │  │ Records  │        │  Metadata    │
│ Full    │  │  Hash    │        │   Index      │
│ Cred    │  └──────────┘        └──────────────┘
└────┬────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Response to Issuer                    │ (4) Success confirmation
│  • Credential ID: CRED_001             │
│  • IPFS CID: Qm...                     │
│  • Blockchain Block: #123              │
└────────────────────────────────────────┘
```


***

### Verification Flow

```
┌──────────┐
│ VERIFIER │ (1) Submits credential ID or proof
│(Employer)│
└────┬─────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Verification Engine                   │ (2) Multi-step validation
└────┬───────────────────────────────────┘
     │
     ├──────────┬──────────┬──────────┬──────────┐
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│  IPFS   ││Blockchain│Crypto   ││Registry ││Revoke  │
│Retrieve ││  Hash   │Signature││ Check   ││ Check  │
│         ││ Verify  │ Verify  ││         ││        │
│  ✓      ││   ✓     │   ✓     ││   ✓     ││   ✓    │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
     │          │          │          │          │
     └──────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
┌────────────────────────────────────────────────┐
│  Verification Result                           │
│  Status: ✅ VALID                              │
│  Issuer: G. Pulla Reddy Engineering College    │
│  Issue Date: 2024-12-26                        │
│  Blockchain Block: #123                        │
│  Signature: Valid RSA-2048                     │
│  Revocation Status: Not Revoked                │
└────────────────────────────────────────────────┘
```


***

### Selective Disclosure Flow

```
┌──────────┐
│ STUDENT  │ (1) Selects fields to share
│ (Holder) │     Example: Only GPA, not full transcript
└────┬─────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Selective Disclosure Engine           │
│  • Retrieve full credential            │
│  • Extract selected fields             │
│  • Create privacy-preserving proof     │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Generated Proof (JSON)                │
│  {                                     │
│    "credential_id": "CRED_001",        │
│    "disclosed_fields": {               │
│      "gpa": 8.5,                       │
│      "degree": "B.Tech CS"             │
│    },                                  │
│    "hidden_fields": ["dob", "marks"], │
│    "proof": "crypto_proof_here",       │
│    "timestamp": "2024-12-26..."        │
│  }                                     │
└────┬───────────────────────────────────┘
     │
     ▼
┌──────────┐
│ VERIFIER │ (2) Receives and verifies proof
│          │     Only sees disclosed fields
└──────────┘
```


***

## 📦 External Dependencies

### Core Python Libraries

```
Flask==3.0.0              # Web framework
cryptography==41.0.7      # RSA encryption
requests==2.31.0          # HTTP client for IPFS
SQLAlchemy==2.0.23        # Database ORM
Flask-Login==0.6.3        # Session management
```


### External Services

**1. IPFS Network**

- **Purpose:** Distributed credential storage
- **Endpoints:**
    - Local node: `http://127.0.0.1:5001`
    - Infura gateway: `https://ipfs.infura.io:5001`
- **Fallback:** Local JSON storage

**2. Bootstrap CDN**

- **Purpose:** UI framework and styling
- **CDN:** `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0`
- **Components:** Grid system, forms, buttons, modals

**3. Font Awesome**

- **Purpose:** Icon library
- **CDN:** `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0`

***

## 🚀 Deployment Strategy

### Development Environment

**Setup:**

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.models import init_database; from app.app import app; init_database(app)"

# Create admin user
python scripts/create_admin.py

# Run application
python main.py
```

**Configuration:**

- Debug mode: Enabled
- Port: 5000
- Host: 0.0.0.0 (all interfaces)
- Storage: Local file-based
- IPFS: Local fallback enabled

***

### Production Deployment

**Platform:** Render / AWS / Azure / Google Cloud

**Requirements:**

- Python 3.10+
- PostgreSQL (recommended) or SQLite
- IPFS node (optional, with fallback)
- HTTPS/TLS certificates

**Environment Variables:**

```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
PORT=5000
IPFS_ENABLED=True
```

**Docker Deployment:**

```bash
# Build image
docker build -t blockchain-credentials:v2.0 .

# Run container
docker run -d -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=$SECRET_KEY \
  blockchain-credentials:v2.0
```


***

## 🔒 Security Model

### Multi-Layer Security Architecture

```
┌──────────────────────────────────────────┐
│  Layer 1: Transport Security             │
│  • HTTPS/TLS encryption                  │
│  • Secure headers (HSTS, CSP)            │
└─────────────┬────────────────────────────┘
              ▼
┌──────────────────────────────────────────┐
│  Layer 2: Authentication & Authorization │
│  • Role-based access control (RBAC)      │
│  • Session management                    │
│  • Password hashing (PBKDF2-SHA256)      │
└─────────────┬────────────────────────────┘
              ▼
┌──────────────────────────────────────────┐
│  Layer 3: Cryptographic Security         │
│  • RSA-2048 digital signatures           │
│  • SHA-256 hashing                       │
│  • Secure key storage                    │
└─────────────┬────────────────────────────┘
              ▼
┌──────────────────────────────────────────┐
│  Layer 4: Data Integrity                 │
│  • Blockchain tamper detection           │
│  • IPFS content addressing               │
│  • Merkle tree proofs                    │
└─────────────┬────────────────────────────┘
              ▼
┌──────────────────────────────────────────┐
│  Layer 5: Privacy Protection             │
│  • Selective disclosure                  │
│  • Zero-knowledge proofs                 │
│  • Data minimization                     │
└──────────────────────────────────────────┘
```


### Cryptographic Specifications

**Digital Signatures:**

- Algorithm: RSA with 2048-bit keys
- Padding: OAEP with SHA-256
- Signature format: Base64-encoded

**Hashing:**

- Algorithm: SHA-256
- Output: 64-character hexadecimal
- Use cases: Blockchain, data integrity

**Key Management:**

- Storage: PEM format files
- Access control: OS-level permissions
- Rotation: Manual process (to be automated)

***

## 📞 Support \& Contact

### Development Team

For technical inquiries, contributions, or issues:

- **Backend Architecture & Blockchain:** [@udaycodespace](https://github.com/udaycodespace)
- **Frontend & IPFS Integration:** [@shashikiran47](https://github.com/shashikiran47)
- **Testing & Documentation:** [@tejavarshith](https://github.com/tejavarshith)

### 4. Technical Writers & QA
**[@tejavarshith](https://github.com/tejavarshith)** - Teja Varshith
- Comprehensive documentation suite
- Automated test scripts
- System health monitoring logic

***

> [!NOTE]
> **🚀 ARCHITECTURE DESCRIPTION: UPDATED**
> 
> **Architecture Version:** 2.1.0 (Elite Edition)
> 
> **Current Edited Date:** `2026-03-08`

### Resources

- **Documentation:** `/docs` folder
- **API Reference:** `/docs/API.md`
- **User Guide:** `/docs/USER_GUIDE.md`
- **Architecture:** This document

***

<div align="center">

**G. Pulla Reddy Engineering College (Autonomous)**

**Computer Science Engineering Department**

**B.Tech Final Year Project | Version 2.0**

***

*Building Trust in Academic Credentials*

</div>
