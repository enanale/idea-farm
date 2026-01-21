
import os
import logging
from cryptography.fernet import Fernet
from firebase_admin import firestore
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# NOTE: Set this via firebase functions:config:set or environment variable
# Check: os.environ.get("FERNET_KEY")
# If missing, we should probably fail hard in a real app, but for now we might error.

def get_fernet_key() -> bytes:
    key = os.environ.get("FERNET_KEY")
    if not key:
        raise ValueError("FERNET_KEY environment variable not set. Application cannot encrypt/decrypt tokens.")
    return key.encode() if isinstance(key, str) else key

def encrypt_token(token: str) -> str:
    """Encrypts a raw token string."""
    try:
        f = Fernet(get_fernet_key())
        return f.encrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts an encrypted token string."""
    try:
        f = Fernet(get_fernet_key())
        return f.decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise

def get_user_credentials(user_id: str) -> Credentials | None:
    """
    Retrieves the refresh token from Firestore, decrypts it, and returns
    a valid (refreshed if needed) Credentials object.
    """
    db = firestore.client()
    doc_ref = db.collection("users").document(user_id).collection("params").document("secrets")
    doc = doc_ref.get()

    if not doc.exists:
        logger.warning(f"No secrets found for user {user_id}")
        return None

    data = doc.to_dict()
    encrypted_refresh_token = data.get("google_drive_refresh_token")
    
    if not encrypted_refresh_token:
        logger.warning(f"No refresh token found for user {user_id}")
        return None

    try:
        refresh_token = decrypt_token(encrypted_refresh_token)
        
        # We need Client ID and Secret to refresh
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
             logger.error("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET env vars")
             return None

        creds = Credentials(
            None, # Access token (will be refreshed)
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Verify/Refresh immediately to ensure it works
        if not creds.valid:
             creds.refresh(Request())
             
        return creds

    except Exception as e:
        logger.error(f"Failed to create credentials for user {user_id}: {e}")
        return None
