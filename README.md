<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/credify-logo-white.svg">
  <img src="assets/credify-logo.svg" alt="Credify logo: a graduation cap with a chain link and a check threaded through it" width="96" height="96">
</picture>

# Credify

Is that degree real? Stop emailing the registrar. Check the proof.

![Solo project](https://img.shields.io/badge/Solo_project-Yes-111827?style=for-the-badge&logo=github&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_build-0f766e?style=for-the-badge)
![Blockchain](https://img.shields.io/badge/Blockchain-Permissioned-7c3aed?style=for-the-badge&logo=hyperledger&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![IPFS](https://img.shields.io/badge/IPFS-65C2CB?style=for-the-badge&logo=ipfs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
[![GitHub](https://img.shields.io/badge/udaycodespace-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/udaycodespace)

</div>

## About

Credify is a permissioned blockchain for academic credential verification. It is built for institutions that issue credentials, students who hold them, and verifiers who need to trust them.

An institution signs a credential and anchors its hash on the chain. The student shares a QR code or a link. The verifier checks the proof directly, so tampering is obvious and nobody has to wait for an email reply.

I built it solo to make credentials easier to issue, harder to fake, and faster to verify.

## The problem

Academic certificates travel as PDFs, and a PDF can be copied or edited. Checking one usually means an email thread, a manual check, and a wait. The records themselves sit in different systems.

Credify keeps the whole flow in one place and gives the verifier something concrete to check.

```mermaid
flowchart LR
    A[Email threads]:::bad --> X
    B[Manual checks]:::bad --> X
    C[Scattered records]:::bad --> X
    X{{Credify}}:::hub --> Y[Student shares a QR or link]:::good --> Z[Verifier checks the proof]:::done

    classDef bad fill:#fecaca,stroke:#111827,color:#111827,stroke-width:2px
    classDef hub fill:#7c3aed,stroke:#111827,color:#ffffff,stroke-width:3px
    classDef good fill:#ddd6fe,stroke:#111827,color:#111827,stroke-width:2px
    classDef done fill:#bbf7d0,stroke:#111827,color:#111827,stroke-width:2px
```

| Problem | What usually happens | What Credify does |
|:-:|:-|:-|
| Fake certificates | PDFs get copied or edited. | Signs records and anchors them on the chain. |
| Slow verification | Staff have to respond manually. | Lets verifiers check the proof directly. |
| Scattered records | Data lives across different systems. | Keeps the record flow structured. |
| Trust gaps | There is no clear way to confirm where a record came from. | Uses permissions, hashes and signatures. |

## How it works

An admin creates and signs a credential. The payload goes to IPFS and its hash is anchored on the blockchain. Once the block is finalized, the student receives the proof. A verifier scans the QR code or opens the link and runs three checks.

```mermaid
flowchart TD
    A[Admin creates credential]:::step --> B[Sign record]:::step
    B --> C[Store payload in IPFS]:::step
    C --> D{{Anchor hash on blockchain}}:::hub
    D --> E[Finalize block]:::step
    E --> F[Student receives proof]:::good
    F --> G[Verifier scans QR or link]:::good
    G --> H[Check signature]:::done
    G --> I[Check blockchain anchor]:::done
    G --> J[Check revocation]:::done

    classDef step fill:#f3f4f6,stroke:#111827,color:#111827,stroke-width:2px
    classDef hub fill:#7c3aed,stroke:#111827,color:#ffffff,stroke-width:3px
    classDef good fill:#ddd6fe,stroke:#111827,color:#111827,stroke-width:2px
    classDef done fill:#bbf7d0,stroke:#111827,color:#111827,stroke-width:2px
```

```mermaid
sequenceDiagram
    participant Admin
    participant IPFS
    participant Chain
    participant Student
    participant Verifier

    Admin->>IPFS: Upload credential payload
    Admin->>Chain: Store hash and metadata
    Chain-->>Student: Credential is finalized
    Student->>Verifier: Share QR or proof link
    Verifier->>Chain: Validate anchor
    Verifier->>IPFS: Validate payload
    Verifier-->>Student: Return result
```

## What's inside

| Part | What it handles |
|:-:|:-|
| ![Issuance](https://img.shields.io/badge/Issuance-7c3aed?style=flat-square) | Creates and signs credentials. |
| ![Storage](https://img.shields.io/badge/Storage-65C2CB?style=flat-square) | Stores payloads through IPFS. |
| ![Blockchain](https://img.shields.io/badge/Blockchain-1d4ed8?style=flat-square) | Anchors hashes and keeps the ledger consistent. |
| ![Verification](https://img.shields.io/badge/Verification-0f766e?style=flat-square) | Checks the signature, the anchor and the revocation status. |
| ![Access control](https://img.shields.io/badge/Access_control-111827?style=flat-square) | Uses OTP-based privileged access for issuer actions. |

## Features

| Feature | How it works |
|:-:|:-|
| Permissioned network | Validation stays controlled, and only approved nodes take part. |
| Finalized blocks | Once a block is finalized, tampering with it is obvious. |
| Independent verification | A verifier checks the proof without asking the institution, so there is less manual follow-up. |
| Selective disclosure | The holder shares only what is needed. |
| Cryptographic proof | RSA signatures and SHA-256 hashes give the verifier something concrete to check. |
| QR or link sharing | The student shares one QR code or proof link, and the verifier opens it. |
| Revocation check | Verification includes the credential's revocation status. |
| OTP for issuer actions | Privileged actions need a one-time code. |
| Role boundaries | Admin, student and verifier each get their own access. |

## Who it helps

| If you are... | Credify gives you... |
|:-:|:-|
| A student | A portable credential proof you can share quickly. |
| An institution | A cleaner issuance and verification flow. |
| A verifier | A direct way to confirm authenticity. |
| A recruiter | A faster check than email-based validation. |

## Tech stack

| Layer | Choice | What it does here |
|:-|:-:|:-|
| Backend | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/-Flask-000000?style=flat-square&logo=flask&logoColor=white) | The application server. SQLAlchemy handles the database layer. |
| Security | ![RSA](https://img.shields.io/badge/-RSA-7c3aed?style=flat-square) ![SHA-256](https://img.shields.io/badge/-SHA--256-111827?style=flat-square) | RSA signs records. SHA-256 hashes them so any change shows up. |
| Storage | ![IPFS](https://img.shields.io/badge/-IPFS-65C2CB?style=flat-square&logo=ipfs&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) | IPFS holds credential payloads. SQLite and PostgreSQL are used for database storage. |
| Deployment | ![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=docker&logoColor=white) | One image to run the app, and Docker Compose for the validator nodes. |
| Automation | ![GitHub Actions](https://img.shields.io/badge/-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white) | Workflows that run on the repo. |

## Quick start

### Docker

```bash
docker pull udaycodespace/credify:latest
docker run -d -p 5000:5000 udaycodespace/credify:latest
```

### Local setup

```bash
git clone https://github.com/udaycodespace/credify.git
cd credify
python -m venv venv

# Windows
venv\Scripts\activate

# Linux or macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Validator nodes

```bash
docker-compose up -d
```

| Node | Endpoint |
|:-:|:-|
| Validator 1 | http://localhost:5001 |
| Validator 2 | http://localhost:5002 |
| Validator 3 | http://localhost:5003 |

## Security

| Control | Purpose |
|:-:|:-|
| OTP access | Protects issuer actions. |
| RSA signatures | Proves a record is authentic. |
| SHA-256 hashing | Detects tampering. |
| Role boundaries | Separates admin, student and verifier. |
| Finalized ledger | Makes verification easier to trust. |

## Roadmap

| Next step | What it adds |
|:-:|:-|
| PBFT-style consensus | A stronger validation model. |
| DID support | Better identity interoperability. |
| ZK proofs | More privacy for sensitive data. |
| Governance controls | Cleaner validator management. |
| Audit dashboards | Easier monitoring and traceability. |

## License

Copyright (c) 2026 Uday. All rights reserved.

<div align="center">

Built solo. Kept practical. Focused on trust, not hype.

Made by [udaycodespace](https://github.com/udaycodespace)

</div>
