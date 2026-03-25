# Credify v2: Permissioned Private Blockchain for Academic Credential Verification

A permissioned private blockchain implementing deterministic consensus, validator-based participation, and finalized tamper-evident blocks for credential verification.

---

## Security Notice

This is an academic engineering project built for educational evaluation and portfolio demonstration.

- All sample data in documentation is illustrative.
- Secrets must be provided through environment variables.
- Do not deploy with default local-development settings.
- Use HTTPS/TLS and secure secret management for internet-facing deployments.

---

## Overview

Credify v2 addresses credential forgery, verification delay, and privacy exposure in traditional academic verification systems.

The platform combines:
- permissioned private blockchain state anchoring
- deterministic validator consensus
- finalized tamper-evident blocks
- IPFS-integrated storage with local fallback
- RSA-based signature verification
- ZKP-inspired selective disclosure

Stakeholder outcomes:
- Universities issue signed, verifiable credentials.
- Students retain controlled data sharing.
- Verifiers validate authenticity quickly without manual paperwork.

Extended documentation was consolidated into the main README and core engineering documents to improve clarity and reduce redundancy.

---

## Key Features

- Permissioned private blockchain ledger for institutional trust boundaries
- Deterministic round-robin validator selection
- Immediate block finality with tamper-evident hash-linking
- Validator-based network participation model
- Credential integrity verification via cryptographic signatures
- IPFS-backed storage with resilient local persistence fallback
- ZKP-inspired selective disclosure for privacy-aware proof sharing
- Multi-node propagation and synchronization support

---

## System Architecture

Credential lifecycle (high level):
1. Issuer creates and signs credential data.
2. Credential payload is stored in IPFS (or fallback storage).
3. Credential hash and metadata are anchored in a finalized block.
4. Holder shares proof or credential reference with verifier.
5. Verifier checks blockchain anchor, signature, and revocation state.

Architecture characteristics:
- permissioned validator set controls block proposal
- deterministic consensus avoids probabilistic confirmation delay
- finalized blocks create strong tamper-evidence guarantees
- propagation logic keeps validator nodes aligned

---

## System Evolution

### Phase 1: Prototype - BlockCred

Repository: https://github.com/uday-works/blockcred-system  
Live: https://blockcred-frontend.onrender.com/

This phase validated the core problem quickly.
It tested whether credentials could be anchored off-chain, hashed reliably, and shown through role-specific dashboards.
It confirmed feasibility, but exposed limits in trust control, deterministic state progression, and institutional-grade verification guarantees.
Those constraints made a redesign necessary.

Key foundations introduced:
- IPFS off-chain credential storage
- cryptographic hashing (SHA-256 / Keccak)
- React-based dashboards
- Dockerized deployment on Render

### Phase 2: Current System - Credify v2

Evolution delivered:
- permissioned private blockchain architecture
- deterministic consensus for predictable block production
- validator-based participation controls
- finalized tamper-evident block model
- multi-node propagation and synchronization

This redesign moved the project from proof-of-concept behavior to an auditable ledger model for academic institutions.
Deterministic consensus, validator controls, and block finality made verification defensible in real review settings.

### Phase 3: Verification Client

Repository: https://github.com/udaycodespace/credify-verify  
Live: https://udaycodespace.github.io/credify-verify/

Verification client characteristics:
- independent verification client
- QR and credential proof verification
- no backend dependency for verification flows
- explicit trust-boundary separation from issuance platform

This separation keeps verification independently testable and reduces coupling between issuance operations and public trust checks.

This progression reflects a deliberate engineering approach.
It starts with concept validation, evolves into a controlled blockchain system, and ends with verification in an independent trust boundary.

---

## Authentication & Access Model

The system uses a secure OTP-based access mechanism.
The model follows institutional onboarding patterns.
Identity provisioning is controlled by authorized academic administrators, not open signup flows.

### Admin / Issuer

- authenticated via OTP or environment-controlled access
- responsible for:
  - creating students
  - issuing credentials
  - interacting with blockchain records

Admin control centralizes onboarding accountability and preserves credential issuance integrity.

### Student

- created only by admin
- no self-registration
- can:
  - view credentials
  - share proofs

This prevents unauthorized identity creation and aligns with registrar-driven enrollment workflows.

### Verifier

- no login required
- verifies via:
  - QR scan
  - credential ID
  - proof validation

Public verifier access lowers friction while preserving trust through cryptographic and blockchain validation.

---

## Quick Start

### Docker Deployment (3-Node Validator Cluster)

```bash
git clone https://github.com/udaycodespace/credify.git
cd credify
docker-compose up -d
```

Validator endpoints:
- http://localhost:5001
- http://localhost:5002
- http://localhost:5003

---

## Local Development

```bash
git clone https://github.com/udaycodespace/credify.git
cd credify
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Application endpoint:
- http://localhost:5000

---

## Tech Stack

Backend and Core:
- Python 3.10+
- Flask
- SQLAlchemy
- Cryptography (RSA, SHA-256)

Blockchain and Storage:
- permissioned private blockchain engine
- deterministic validator consensus
- IPFS integration with local fallback

Frontend and UX:
- HTML/CSS/JavaScript
- Jinja2 templates
- responsive role-based dashboards

Quality and Delivery:
- pytest
- Docker and docker-compose
- GitHub Actions CI/CD

---

## Core Features

Security and Integrity:
- RSA-2048 digital signatures
- SHA-256 hashing and hash-linking
- finalized tamper-evident blocks
- revocation-aware verification

Blockchain Capability:
- validator-based network participation
- deterministic consensus sequencing
- propagation safety controls
- audit-oriented credential anchoring

Credential Experience:
- issuance and lifecycle management
- PDF credential generation
- QR verification flow
- ZKP-inspired selective disclosure

---

## Workflow

Operational workflow:
1. Issuer authenticates via OTP-based access.
2. Issuer creates credential payload.
3. Payload is stored and anchored to blockchain.
4. Holder receives credential and shares proof as needed.
5. Verifier validates via QR, credential ID, or proof.
6. Verification checks signature, anchor integrity, and revocation status.

---

## Project Structure

```text
credify/
├── app/                 # Flask app, routes, services
├── core/                # Blockchain, crypto, credential logic
├── data/                # Runtime data files and storage artifacts
├── docs/                # Technical documentation
├── static/              # Frontend assets
├── templates/           # HTML templates
├── tests/               # Automated tests
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Testing

Run tests:

```bash
pytest -v
```

Optional coverage:

```bash
pytest --cov=app --cov=core --cov-report=html
```

Coverage focus:
- authentication and access flows
- blockchain integrity and consensus behavior
- cryptographic utilities and verification paths

---

## DevOps

CI/CD and containerization:
- GitHub Actions for test/build/publish automation
- Docker multi-stage builds
- Docker image publishing to Docker Hub
- validator-cluster orchestration via docker-compose

Deployment posture:
- deployment-ready for academic demos and controlled environments
- configurable environment variables for node identity and peers

---

## Development Methodology (SDLC)

### Team

- Uday - Project Lead and Architect
- Shashi - Contributor
- Varshith - Contributor

### Approach

- Agile-style iterative development
- phase-based execution:
  1. Foundation (MVP)
  2. Distributed Architecture
  3. Feature Completeness
  4. Deployment and Polish
- continuous testing with pytest
- refactoring for stability and maintainability

This project followed an iterative SDLC approach.
Each phase informed architectural decisions in the next, leading to a stable and defensible final system.
Lessons from the prototype directly shaped redesign choices, and the final phase prioritized stabilization, validation, and explainability.

Engineering principle:
- The system prioritizes correctness, explainability, and controlled distributed behavior over full protocol complexity.
- The system is designed not to maximize decentralization, but to balance control, verifiability, and explainability in a permissioned environment.

---

## Security

Implemented controls:
- OTP-based privileged access model
- role-based access boundaries
- cryptographic signing and integrity checks
- tamper-evident finalized block model
- input validation and ORM-based query safety

Operational recommendations:
- keep secrets in environment variables only
- enforce HTTPS/TLS in deployed environments
- rotate secrets regularly
- monitor logs and verification failures

---

## Roadmap

Future enhancements:
- PBFT-style consensus upgrade for stronger Byzantine tolerance
- validator slashing and governance controls
- IPFS cluster adoption
- stronger ZKP-inspired selective disclosure evolution toward full zero-knowledge proof protocols
- DID interoperability for portable credential identity

---

## Team

Core contributors:
- Uday: architecture, backend, blockchain, integration
- Shashi: implementation support, UI contribution, validation
- Varshith: debugging support, testing support, documentation support

---

## Acknowledgements

Academic guidance and institutional support from:
- Dr. B. Thimma Reddy Sir
- Dr. G. Rajeswarappa Sir
- Shri K. Bala Chowdappa Sir
- G. Pulla Reddy Engineering College (Autonomous), Kurnool

Technical ecosystem acknowledgements:
- Python and Flask communities
- IPFS ecosystem contributors
- open-source contributors used by this project

---

## License

Project classification: B.Tech Final Year Project.

This repository is maintained for academic evaluation and portfolio demonstration by the core team.

For usage permissions, contact the maintainers:
- https://github.com/udaycodespace
- https://github.com/shashikiran47
- https://github.com/tejavarshith
