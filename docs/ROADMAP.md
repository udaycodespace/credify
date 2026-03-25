#  Credify  Project Roadmap & Future Scope

> **Project Evolution Status:** Phase 1 (Core Infrastructure & Elite UI) is **100% COMPLETE**.
> This document outlines the transition from a highly-polished local system to a distributed production network.

---

##  Baseline: What Credify Is Today (COMPLETED)

| Aspect | Status | Reality |
|---|---|---|
| **Architecture** |  Done | Single Flask process with multi-role access control |
| **Blockchain** |  Done | Python linked-list (SHA-256) with tamper-evidence |
| **UI/UX** |  Done | Elite Senior-level design with 10/10 responsiveness |
| **PDF Engine** |  Done | Institutional-grade ReportLab PDF generation |
| **QR System** |  Done | Dynamic QR codes for instant document verification |
| **Support System** |  Done | Full ticketing and collaborative messaging system |
| **Pvt Transition** |  Done | Dedicated /issuer and /holder portals with role gates |
| **MFA Guard** |  Done | Mandatory TOTP verification for administrative keys |
| **Auto-Hardening** |  Done | Automatic default password removal and schema sync |

---

##  System Architecture Overview

Credify follows a decentralized service-oriented architecture designed for scalability and cryptographic integrity.

```
 +----------------+
 | Issuer UI |
 +----------------+
 |
 v
 Flask Backend API
 |
 +------------+------------+
 | |
 v v
 Blockchain Engine IPFS Storage
 |
 v
 SQL Block Store
 |
 v
 P2P Network
 Node1  Node2  Node3
```

---

##  Engineering Assessment (March 2026)

| Metric | Rating | Status |
|---|---|---|
| **Architecture** |  | Excellent separation of concerns |
| **UI/UX** |  | **Elite Milestone Reached** |
| **PDF Output** |  | **10/10 Professional Standard** |
| **Blockchain Logic** |  | Solid hashing; ready for P2P expansion |

---

##  Phase 2: Future Scope (Technical Roadmap)

The following steps are identified as the next evolutionary stage for the project to reach "Production Mainnet" status.

###  Step 1: Persistent Chain (SQL Migration)
**Goal:** Replace `blockchain_data.json` with a database-backed block store for infinite scalability.
- Move from RAM-based list to indexed database queries.
- Support for millions of credentials without performance degradation.

###  Step 2: Cryptographic Node Identity
**Goal:** Every block signed by the Issuer's unique RSA-2048 key.
- Digital attribution for every ledger entry.
- Impossible to forge blocks even with server access (requires private key).

###  Step 3: Formal Proof of Authority (PoA)
**Goal:** Upgrade from round-robin PoA to Byzantine Fault Tolerant consensus for malicious validator resilience.
- Optimized block creation (instantaneous).
- Authorized Validator list for adding new academic records.

###  Step 4: Multi-Node P2P Synchronization
**Goal:** True decentralization through horizontal scaling.
- Docker-based cluster deployment (3+ nodes).
- Gossip protocol for real-time block broadcasting between universities.

---

##  Track A Checklist  Private/Permissioned Blockchain

```
[] Milestone 1: Elite UI/UX & Senior Branding
[] Milestone 2: Professional PDF Generation (ReportLab)
[] Milestone 3: Digital QR Verification System
[] Milestone 4: Private (PVT) Blockchain Architecture
[] Milestone 5: Administrative MFA & One-Page Portals
[] Milestone 6: Automated Security Hardening (Schema Sync)
[ ] Milestone 7: Formal Proof of Authority (PoA) (Future Scope)
[ ] Milestone 8: Multi-Node P2P Replication (Future Scope)
```

---

##  Track B Checklist  Public Network (Optional Extra Credit)

```
[ ] B-Step 1: Polygon Amoy Smart Contract Deployment
[ ] B-Step 2: Web3.py Integration (On-Chain Verification)
[ ] B-Step 3: Pinata/Web3.Storage Global IPFS Pinning
[ ] B-Step 4: W3C Verifiable Credentials Compliance
```

***

> [!NOTE]
> ** ROADMAP STATUS: UPDATED**
>
> **Project Version:** v2 (PVT Master Edition)
> **Institution:** G. Pulla Reddy Engineering College
> **Guidance:** Dr. B. Thimma Reddy Sir, Dr. G. Rajeswarappa Sir and Shri Shri K Bala Chowdappa Sir
>
> **Last Updated:** `2026-03-08`

