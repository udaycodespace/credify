# Blockchain-Based Verifiable Credential System for Academic Transcripts

A decentralized, privacy-preserving platform for issuing, storing, and verifying academic credentials using blockchain and cryptography.

---

## 📌 Overview

Academic credential verification is traditionally centralized, slow, and prone to forgery, with little to no privacy protection for students.  
This project introduces a **trustless, tamper-proof, and privacy-first credential verification system** where academic transcripts are issued digitally, stored securely, and verified instantly without relying on intermediaries.

Using **Blockchain, IPFS, Cryptography, and W3C Verifiable Credential standards**, the system enables:

- Universities to issue authentic digital credentials  
- Students to control and selectively disclose their data  
- Employers to verify credentials instantly without contacting the issuing institution  

**Live Deployment:** https://blockchain-academic-credential-system.onrender.com/  
**Prototype (UI-only):** https://blockcred-frontend.onrender.com/

---

## 🎯 Aim & Objectives

- Prevent academic certificate forgery  
- Enable privacy-preserving verification via selective disclosure  
- Decentralize transcript storage while maintaining integrity  
- Provide instant, cryptographically verifiable proof of authenticity  

---

## ✨ Features

### User Features
- Secure digital academic transcript issuance  
- Student-owned credentials with full control  
- Selective disclosure of academic data (e.g., GPA only)  
- Instant credential verification for employers  

### System Features
- Permissioned blockchain for credential hash anchoring  
- IPFS-based off-chain storage for transcripts  
- Cryptographic signatures and hash verification  
- W3C Verifiable Credential–aligned data model  
- Role-based workflows for Issuer, Holder, and Verifier  

---

## 🧰 Tech Stack

- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python, Flask  
- **Database:** SQLite / PostgreSQL  
- **Blockchain:** Custom Permissioned Blockchain  
- **Storage:** IPFS (with local fallback)  
- **Cryptography:** RSA-2048, SHA-256, Merkle Proofs  
- **Testing:** pytest  
- **Tools & Platforms:** Docker, Render  

---

## 🏗️ Architecture / Workflow

1. University issues a digitally signed academic credential  
2. Full transcript is stored on IPFS; its hash is recorded on the blockchain  
3. Student receives and controls the credential  
4. Student selectively discloses required data to a verifier  
5. Employer verifies authenticity via blockchain, IPFS hash, and cryptographic signature  

---

## 📁 Project Structure

```

├── app/
│   ├── app.py              # Flask application entry
│   ├── auth.py             # Authentication & role guards
│   ├── models.py           # Database models
│
├── core/
│   ├── blockchain.py       # Permissioned blockchain logic
│   ├── credential_manager.py
│   ├── crypto_utils.py     # Cryptography & signatures
│   └── ipfs_client.py      # IPFS + local fallback storage
│
├── data/                   # Runtime JSON storage
├── static/                 # CSS & JavaScript
├── templates/              # Jinja2 HTML templates
├── tests/                  # Automated test suite
│
├── Dockerfile
├── requirements.txt
├── main.py
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.x  
- Docker (optional, for containerized deployment)  

### Setup Steps
1. Install dependencies using `requirements.txt`  
2. Configure environment variables if required  

### Run Commands
- Start the Flask application:
  ```bash
  python main.py
  ```
- Run tests:
  ```bash
  pytest tests/
  ```

---

## ▶️ Usage

- Universities log in to issue and sign academic credentials  
- Students access and manage their credentials  
- Employers verify credentials by submitting a Credential ID or proof  
- Verification is performed instantly without contacting the university  

---

## 📸 Screenshots / Demo

_To be added_ (Will be added soon...)

---

## 📊 Results / Outcomes

- Tamper-proof academic credential issuance  
- Elimination of fake certificates  
- Instant verification without intermediaries  
- Strong privacy guarantees through selective disclosure  

---

## 🔮 Future Enhancements

- DID registry integration  
- Mobile credential wallet  
- Zero-knowledge proof optimization  
- Enterprise blockchain integration  
- MPC-based privacy enhancements  

---

## 👥 Team Members

- **SHASHI** – Frontend Design, UI Integration, IPFS Handling  
- **UDAY** – Backend Architecture, Blockchain Logic, Cryptography, Deployment  
- **TEJA VARSHITH** – System Analysis, Test Case Design, Validation & Documentation  

---

## 🙏 Credits & Acknowledgements

We sincerely thank:

- **👨‍🏫 Dr. B. Thimma Reddy** — Project Guide  
- **👨‍🏫 Dr. G. Rajeswarappa** — Faculty In-Charge, CST-A  
- **👨‍🏫 Dr. K. Bala Chowdappa** — Mentor  
- G. Pulla Reddy Engineering College (Autonomous), Kurnool  
- Open-source blockchain and cryptography communities 
- W3C Verifiable Credentials specifications  

for their continuous guidance, encouragement, and support throughout the successful completion of this project.

---

## 📄 License

Developed as a **B.Tech Final Year Project**  
**v1.0.0 — Final Academic Submission**
