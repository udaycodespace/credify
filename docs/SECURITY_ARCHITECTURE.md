# 🛡️ Credify Security Architecture

Credify implements a multi-layer security model to ensure the integrity, confidentiality, and availability of academic credentials.

## 1. Cryptographic Layer
- **Hashing:** SHA-256 for block linking.
- **Asymmetric Encryption:** RSA-2048 for digital signatures.
- **Signatures:** Every block is signed by the University's Private Key.

## 2. Ledger Integrity
- **Append-Only:** Blocks are cryptographically linked to previous hashes.
- **Tampering Detection:** Any modification to historical data invalidates the entire subsequent chain.
- **Proof of Work (Simulated):** Rate-limits block creation and mimics decentralized cost.

## 3. Data Privacy
- **Selective Disclosure:** Students can choose which parts of their transcript to reveal to verifiers.
- **Zero-Knowledge Proofs (Conceptual):** Verification of total credits without revealing individual grades.

## 4. Decentralized Fallback
- **IPFS Storage:** Critical data is pinned to IPFS to prevent loss due to central server failure.
- **CID Anchoring:** Even if the central UI is down, the data remains verifiable via the IPFS CID stored on the ledger.

---

## 👥 Roles & Permissions
- **SuperAdmin:** Full system control.
- **Issuer:** Authorized to create new blocks.
- **Holder:** Authorized to view and share their specific credentials.
- **Verifier:** Public-read access to specific verification reports.

***
**G. Pulla Reddy Engineering College (Autonomous)**
**Guidance:** Dr. B. Thimma Reddy Sir, Dr. G. Rajeswarappa Sir and Shri Shri K Bala Chowdappa Sir
**Dated:** 2026-03-08
