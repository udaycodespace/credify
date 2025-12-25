# Blockchain-Based Verifiable Credentials System

## Overview

This is a comprehensive blockchain-based verifiable credential system designed for academic transcript verification. The system implements W3C Verifiable Credentials standards with blockchain integrity, IPFS storage, and cryptographic verification. It's built as a B.Tech final year project for G. Pulla Reddy Engineering College's Computer Science Engineering department.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap with dark theme
- **Client-side**: Vanilla JavaScript for real-time interactions
- **Design Pattern**: Multi-role interface with separate portals for issuers, holders, and verifiers

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Architecture Pattern**: Modular component-based design
- **Core Components**:
  - Blockchain engine for immutable record keeping
  - Cryptographic manager for RSA-2048 signatures
  - IPFS client for distributed storage
  - Credential manager for W3C compliant credentials

### Data Storage Solutions
- **Blockchain**: Custom implementation with proof-of-work consensus
- **IPFS**: Distributed storage for credential data with local fallback
- **Local Files**: JSON-based storage for development (credentials_registry.json, blockchain_data.json)
- **Cryptographic Keys**: PEM format for RSA key pairs

## Key Components

### 1. Blockchain Component (`blockchain.py`)
- **Purpose**: Provides immutable record keeping for credential hashes
- **Implementation**: Simple proof-of-work blockchain with configurable difficulty
- **Features**: Block mining, hash calculation, chain validation

### 2. Cryptographic Manager (`crypto_utils.py`)
- **Purpose**: Handles RSA-2048 digital signatures for credential authenticity
- **Features**: Key generation, digital signing, signature verification
- **Security**: Industry-standard RSA encryption with proper padding

### 3. IPFS Client (`ipfs_client.py`)
- **Purpose**: Decentralized storage for credential data
- **Fallback Strategy**: Multiple endpoints with local storage fallback
- **Endpoints**: Local IPFS node and Infura IPFS gateway

### 4. Credential Manager (`credential_manager.py`)
- **Purpose**: W3C Verifiable Credentials compliance and management
- **Features**: Credential issuance, selective disclosure, verification
- **Standards**: Full W3C Verifiable Credentials specification compliance

### 5. Web Interface (`app.py`, templates/)
- **Issuer Portal**: Academic institutions can issue credentials
- **Holder Portal**: Students manage and share credentials selectively
- **Verifier Portal**: Employers verify credential authenticity
- **Tutorial System**: Comprehensive guide for system usage

## Data Flow

### Credential Issuance Flow
1. Academic institution enters student transcript data
2. System generates W3C compliant verifiable credential
3. Credential is cryptographically signed with RSA-2048
4. Credential stored on IPFS (or local fallback)
5. Credential hash recorded on blockchain for integrity
6. Unique credential ID generated for reference

### Verification Flow
1. Verifier receives credential ID or selective disclosure proof
2. System retrieves credential from IPFS/local storage
3. Cryptographic signature is verified
4. Blockchain integrity check performed
5. Verification result presented with detailed proof

### Selective Disclosure Flow
1. Student selects specific fields to share (e.g., only GPA)
2. System creates privacy-preserving proof
3. Proof includes only selected fields with cryptographic integrity
4. Verifier can validate proof without accessing full transcript

## External Dependencies

### Core Dependencies
- **Flask**: Web framework for API and UI
- **cryptography**: RSA encryption and digital signatures
- **requests**: HTTP client for IPFS communication

### External Services
- **IPFS Network**: Distributed storage (with local fallback)
- **Infura IPFS**: Backup IPFS gateway
- **Bootstrap CDN**: UI framework and styling

### Optional Dependencies
- Local IPFS node for optimal performance
- External IPFS gateways for redundancy

## Deployment Strategy

### Development Environment
- **Local Development**: Flask development server
- **Port**: 5000 (configurable)
- **Debug Mode**: Enabled for development
- **Storage**: Local file-based storage for all components

### Production Considerations
- **IPFS**: Requires stable IPFS node or gateway access
- **Security**: Change default secret keys and implement proper authentication
- **Scalability**: Consider database backend for production scale
- **Monitoring**: Implement logging and monitoring for blockchain operations

### Configuration Management
- Environment-based configuration through `config.py`
- Configurable IPFS endpoints and blockchain parameters
- Flexible storage backends (local files with database migration path)

### Security Model
- RSA-2048 digital signatures for authenticity
- Blockchain proof-of-work for tamper detection
- Selective disclosure for privacy protection
- Cryptographic key management with secure storage