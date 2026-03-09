# 📟 Credify API Reference

This document provides detailed information about the endpoints available in the Credify system.

## 🔑 Base URL
`http://localhost:5000` (Local)
`https://credify-2026.onrender.com` (Production)

---

## 🏛️ Ledger Endpoints

### 1. View Blockchain
- **URL:** `/api/blockchain`
- **Method:** `GET`
- **Description:** Returns the complete chain of blocks.
- **Security:** Public-read.

---

### 2. Issue Credential
- **URL:** `/api/issue_credential`
- **Method:** `POST`
- **Description:** Encapsulates transcript data into a new block.
- **Body:**
```json
{
  "student_name": "UDAY",
  "roll_number": "229X1A0XXX",
  "program": "B.Tech CSE",
  "semester": "8th",
  "gpa": "9.8"
}
```
- **Security:** Requires Admin session.

---

### 3. Verify Credential
- **URL:** `/api/verify/<credential_id>`
- **Method:** `GET`
- **Description:** Validates a specific credential against the on-chain hash.

---

## 🔒 Authentication

### Login
- **URL:** `/auth/login`
- **Method:** `POST`
- **Params:** `username`, `password`

---

## 📦 Storage (IPFS)

### Upload to IPFS
- **URL:** `/api/ipfs_upload`
- **Method:** `POST`
- **Description:** Silently pins large transcript data to IPFS before anchoring the CID on the blockchain.

---

> [!TIP]
> Use the **Tutorial** page for visual walkthroughs of these endpoints.

***
**Developed by:** SHASHI • UDAY • VARSHITH
**Guidance:** Dr. B. Thimma Reddy Sir, Dr. G. Rajeswarappa Sir and Shri Shri K Bala Chowdappa Sir
**Dated:** 2026-03-08
