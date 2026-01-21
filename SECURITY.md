# Security Architecture & Practices

This document outlines the security architecture of **Idea Farm**, focusing on authentication, authorization, and the secure management of sensitive user credentials (Offline Access Tokens).

## 1. Overview
Idea Farm employs a **Defense in Depth** strategy, leveraging managed services (Firebase/Google Cloud) for core security functions while implementing robust encryption for application-specific secrets.

### Core Principles
- **Least Privilege**: Components and users only have access to what they need.
- **Zero Trust**: We do not trust the client; all data is validated and authorized on the backend.
- **Encryption at Rest**: All sensitive tokens are encrypted before storage.
- **Secrets Management**: No hardcoded secrets in the codebase.

---

## 2. Authentication & Authorization

### User Identity (Firebase Auth)
*   **Provider**: Google Sign-In.
*   **Mechanism**: Users sign in via the frontend. Firebase issues a short-lived ID Token (JWT).
*   **Validation**: Every request to Firestore or Cloud Functions is validated against this ID Token to ensure the user is who they claim to be.

### Data Access (Firestore Security Rules)
We use Firestore Security Rules to enforce row-level security.
*   **Idea Access**: Users can only read/write documents where `resource.data.userId == request.auth.uid`.
*   **Secrets Isolation**: The `users/{uid}/params/secrets` collection is strictly locked (`allow read, write: if false;`). This ensures that **even the user themselves** cannot read their raw encrypted tokens from the frontend client. Only the Admin SDK (Backend) can access this data.

---

## 3. Detailed Implementation: Offline Access

To allow Idea Farm to save files to Google Drive in the background (Autonomous Mode), we improved the security posture by moving from Client-Side-Only to robust Server-Side Token Management.

### The Flow
1.  **Consent (Frontend)**:
    - User grants `offline_access` and `drive.file` scope.
    - Frontend receives a temporary **Auth Code**.
2.  **Exchange (Backend)**:
    - Frontend calls `exchange_auth_code` Cloud Function.
    - Function exchanges Auth Code for a **Refresh Token** directly with Google.
    - *Crucial*: This happens server-to-server; the Refresh Token is never exposed to the browser.
3.  **Encryption (Token Service)**:
    - The Refresh Token is encrypted using **Fernet (AES-128)**.
    - Key: A secret `FERNET_KEY` stored in Google Cloud Secret Manager.
4.  **Storage (Firestore)**:
    - The *Encrypted* token is stored in `users/{uid}/params/secrets`.
    - As noted above, this location is inaccessible to the public/frontend.
5.  **Usage (Background)**:
    - When `process_new_idea` runs, it retrieves the encrypted token.
    - It decrypts it in memory using the `FERNET_KEY`.
    - It generates a short-lived Access Token to perform the Drive upload.

---

## 4. Secrets Management

We use **Google Cloud Secret Manager** to store sensitive configuration. These values are injected into the Cloud Functions environment at runtime.

### Managed Secrets
| Secret Name | Purpose |
|-------------|---------|
| `GOOGLE_CLIENT_ID` | OAuth Client ID (Public identifier) |
| `GOOGLE_CLIENT_SECRET` | OAuth Client Secret (Used for code exchange) |
| `FERNET_KEY` | Symmetric key for encrypting user tokens |

### How it works
In `main.py`, functions declare their secret requirements:
```python
@https_fn.on_call(secrets=["FERNET_KEY", ...])
def sensitive_function(req):
    # Access via safe environment variable
    key = os.environ.get("FERNET_KEY")
```
This ensures secrets are only available to the specific functions that need them.

---

## 5. Security Checklist for Developers

- [ ] **Never commit `.env` files** or keys to Git.
- [ ] **Rotate Keys**: If `FERNET_KEY` is compromised, all stored tokens become invalid/unreadable. Generate a new key and require users to re-login (re-consent).
- [ ] **Review Rules**: Always test Firestore Rules after modification to ensure no leakage.
