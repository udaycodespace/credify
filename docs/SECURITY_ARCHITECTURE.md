#  Credify Security Architecture

Credify implements a multi-layer security model built on permissioned blockchain principles to ensure integrity, confidentiality, and availability of academic credentials.

## 1. Validator-Based Permissioning Layer

- **Pre-Authorized Validators**: Only members of the validator set (`admin`, `issuer1`, `System`) can propose blocks
- **Node Authorization**: Validator nodes must be registered in `NODE_VALIDATORS` before participating in consensus
- **Signature Verification**: Each block must be signed by an authorized validator using RSA-2048
- **Non-Repudiation**: Block field `signed_by` identifies the validator, preventing denial of participation

## 2. Cryptographic Layer

- **Hashing**: SHA-256 for block linking and integrity checks
- **Asymmetric Encryption**: RSA-2048 for institutional digital signatures ensuring block provenance
- **Merkle Trees**: Efficient proof of data integrity within each block
- **Block Finality**: Hash-linked blocks make all past modifications immediately detectable

## 3. Consensus & Finality Layer

- **Deterministic Consensus**: Round-robin leader selection (height % num_validators) ensures predictable block creation
- **Immediate Finality**: Difficulty=0 means blocks are final upon acceptance (no confirmation delays)
- **Propagation Safety**: Idempotency checks prevent duplicate block storage; source tracking prevents loops
- **Validator Participation**: All validator nodes must acknowledge quorum before finalization

## 4. Identity & Access Control

- **Portal Isolation**: Physical URL separation between `/issuer`, `/holder`, and `/verifier` with role-specific gatekeepers
- **Multi-Factor Authentication**: Mandatory 6-digit TOTP verification for the `issuer` role (RFC 6238)
- **Session Security**: Custom Flask session management with MFA challenges
- **Master Emergency Override**: Hardened "break-glass" credential for administrative recovery

## 5. Data Privacy & Disclosure

- **Selective Disclosure**: Students can choose which transcript fields to reveal to verifiers using disclosure proofs
- **IPFS Content Addressing**: Full credential data is stored via content-addressed network, only hash is on blockchain
- **Local Persistent Fallback**: If IPFS is unavailable, credentials fall back to local encrypted storage
- **Field-Level Privacy**: ZKP-based commitments allow proving attributes without full data revelation

## 6. Ledger Integrity

- **Append-Only Blocks**: Ensures no deletion or reordering of historical credentials
- **Tamper-Evidence**: Any modification to past blocks creates detectable hash chain breaks
- **Audit Trail**: Complete timestamp and digital signature history of all credentials
- **Block Validation**: Startup utility validates chain integrity from genesis to head

***
**Permissioned Private Blockchain Model**: Trust is placed in a pre-authorized set of validators rather than anonymous consensus mechanisms. Suitable for institutional credential systems where issuers are known entities.

**G. Pulla Reddy Engineering College (Autonomous)**
**Guidance:** Dr. B. Thimma Reddy Sir, Dr. G. Rajeswarappa Sir and Shri Shri K Bala Chowdappa Sir
**Updated:** 2026-03-25

