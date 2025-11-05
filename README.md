# 🔐 Passkey Authentication Demo (WebAuthn + Deterministic Challenge)

A minimal, self-contained demo of passwordless authentication using **WebAuthn (Passkeys)** with a **deterministic client-generated challenge** derived from an API public key and timestamp.

Unlike typical WebAuthn implementations, this project:
- Creates **registration and login challenges entirely on the client side**
- Uses **SHA-256(pubkey + timestamp)** as the challenge during login
- Uses the **authenticator’s sign counter** and **timestamp replay rules** for protection against replay attacks
- Stores all data locally in a lightweight `db.py` module

---

## 📁 Project Structure

```
.
├── main.py            # FastAPI backend handling registration and login
├── db.py              # Simple in-memory or file-backed user store
├── static/
│   └── index.html     # Frontend: pure HTML + JavaScript WebAuthn logic
└── README.md
```

---

## 🚀 Features

✅ Fully local passkey registration and login  
✅ Deterministic challenges: `SHA256(api_key_pub + timestamp)`  
✅ Replay attack prevention (timestamp monotonicity + WebAuthn signCount)  
✅ Client-only challenge generation (no `/register/begin` or `/login/begin` endpoint)  
✅ Works with standard passkey authenticators (OS / browser native)

---

## ⚙️ Requirements

- **Python 3.9+**
- **Node / Browser supporting WebAuthn (e.g., Chrome, Safari, Edge)**
- Dependencies:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🧠 How It Works

### 1. Registration
- Client generates a random `userId` and sets it as both **user ID** and **challenge**.
- Authenticator creates a passkey bound to your RP (relying party) info.
- The backend verifies attestation using `verify_registration_response`.

### 2. Login
- Client generates:
  ```js
  const msg = apiKeyPublic + timestamp_bytes;
  const challenge = sha256(msg);
  ```
- Authenticator signs this challenge.
- Server reconstructs and verifies:
  ```python
  expected_challenge = sha256(api_key_public + timestamp.to_bytes(8, 'big'))
  verify_authentication_response(...)
  ```
- The backend rejects stale timestamps or repeated sign counts.

---

## 🖥️ Run Locally

### 1️⃣ Start the FastAPI backend
```bash
uvicorn main:app --reload
```

### 2️⃣ Open the demo page
Visit: [http://localhost:8000](http://localhost:8000)

### 3️⃣ Register & Login
- Enter a username (optional). **Note:** The username is not used on the server; it is only shown on the client to help the user identify and select a meaningful passkey when managing multiple credentials.  
- Click **Register** and approve passkey creation with your authenticator.  
- Click **Login** to sign the deterministic challenge and authenticate.

---

## 🗂 Example `db.py`

Simple local in-memory store (no persistence):

```python
# db.py
users = {}

def add_user(user_id: str, data: dict):
    users[user_id] = data

def get_user_by_id(user_id: str):
    return users.get(user_id)

def update_user(user_id: str, data: dict):
    if user_id in users:
        users[user_id].update(data)
```

For production, replace with persistent storage (e.g., SQLite, Redis, PostgreSQL).

---

## 🔐 Security Notes

- **Timestamp replay prevention:**  
  The backend rejects any login with a timestamp ≤ the last recorded timestamp. This also serves as a fallback for clients that do not persist the sign count.
- **Sign count replay prevention:**  
  The authenticator’s sign counter (`sign_count`) is validated when available. As some passkey client implementations do not store the sign count, the timestamp is relied upon to prevent replay attacks.
- **Clock drift:**  
  The backend tolerates ±60s difference between client and server clocks.
- **Local challenges:**  
  All challenges are generated and signed on the client; the backend only verifies.

---

## 🧩 Example Flow

```
[Browser] generate keypair + passkey
   ↓
[Browser] send attestation to FastAPI
   ↓
[FastAPI] verify registration, store user + pubkey + sign_count
   ↓
[Browser] login → build challenge = SHA256(api_key_pubkey || timestamp)
   ↓
[Authenticator] sign(challenge)
   ↓
[FastAPI] verify signature, sign_count, and timestamp freshness ✅
```

---

## 🧰 Configuration

In `main.py`:

```python
RP_ID = "localhost"          # Your relying party ID (domain)
RP_NAME = "My App"           # Display name for passkey creation
ORIGIN = "http://localhost:8000"  # Must match frontend URL
```

Change these values when deploying to production.

---

## 🧪 Testing

You can test using:
- Chrome: Settings → Password Manager → Passkeys
- macOS: Touch ID / iCloud Keychain
- Android: Google Password Manager
- YubiKey or any FIDO2 device

---

## ⚠️ Limitations

- Not meant for production as-is (no DB persistence, no rate limiting)
- Assumes minimal clock drift between client and server
- Replay protection depends on both sign count and timestamp freshness
- Challenge derivation (SHA256(pubkey + timestamp)) is deterministic — anyone with `apiKeyPublic` could reconstruct challenges, so ensure timestamps are short-lived and validated

---

## 🧩 License

MIT License © 2025 — For educational and experimental use.

---

### 👨‍💻 Author Notes

This demo was designed to show how WebAuthn can be simplified for decentralized or stateless environments — where servers don’t need to generate or track challenges per session.

Enjoy hacking! ⚡
