# 🛡️ Credify Security Architecture

Credify implements a multi-layer security model to ensure the integrity, confidentiality, and availability of academic credentials.

## 1. Cryptographic Layer
- **Hashing:** SHA-256 for block linking and integrity checks.
- **Asymmetric Encryption:** RSA-2048 for institutional digital signatures.
- **Signatures:** Every block is signed by the University's Private Key ensuring non-repudiation.
- **MFA (TOTP):** Time-based One-Time Passwords (RFC 6238) for all institutional actors.

## 2. Ledger Integrity & Hardening
- **Append-Only:** Blocks are cryptographically linked to previous hashes.
- **Auto-Schema Migration:** Startup utility that automatically hardens the database schema (e.g., adding `totp_secret`) without data loss.
- **Zero-Trust Defaults:** System detects and randomizes default "admin123" credentials on startup to prevent chain-based attacks.
- **Proof of Work (Simulated):** Rate-limits block creation to prevent spam and mimic decentralized cost models.

## 3. Identity & Access Control
- **Portal Isolation:** Physical URL separation between `/issuer` and `/holder` with role-specific gatekeepers.
- **Multi-Factor Shield**: Mandatory 6-digit TOTP verification for the `issuer` role.
- **Master Emergency Override**: A hardened "break-glass" credential (`adminadmin123`) for administrative recovery.

## 4. Data Privacy & Fallback
- **Selective Disclosure:** Students can choose which parts of their transcript to reveal to verifiers using ZKP-based proofs.
- **IPFS Storage:** Full credential data is stored in a content-addressed network (IPFS), while only the hash is stored on the ledger.

***
**G. Pulla Reddy Engineering College (Autonomous)**
**Guidance:** Dr. B. Thimma Reddy Sir, Dr. G. Rajeswarappa Sir and Shri Shri K Bala Chowdappa Sir
**Dated:** 2026-03-08
