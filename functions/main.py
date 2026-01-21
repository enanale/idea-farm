"""
Idea Farm - Cloud Functions Entry Point
"""

import json
import os
import logging
from firebase_functions import firestore_fn, https_fn, options
from firebase_admin import initialize_app, firestore
import requests

# Import services
from services.content_extractor import extract_content
from services.ai_service import get_ai_service
from services.drive_service import get_drive_service # Will reuse later
from services.token_service import encrypt_token

# Initialize Firebase Admin
initialize_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@firestore_fn.on_document_created(
    document="ideas/{ideaId}",
    memory=options.MemoryOption.MB_512,
    timeout_sec=540,
    secrets=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "FERNET_KEY"]
)
def process_new_idea(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
    """
    Triggered when a new idea is created.
    Orchestrates:
    1. Content Extraction (if URL)
    2. Storage (Firestore sub-collection for MVP)
    3. Gemini Summarization
    4. Update Firestore
    """
    if event.data is None:
        return

    idea_id = event.params["ideaId"]
    db = firestore.client()
    doc_ref = db.collection("ideas").document(idea_id)

    try:
        doc_snap = event.data
        idea = doc_snap.to_dict()
        
        logger.info(f"🚀 [process_new_idea] Triggered for Idea ID: {idea_id}")
        logger.info(f"📋 [process_new_idea] Idea Data: {json.dumps(idea, default=str)}")
        
        doc_ref.update({"status": "processing"})

        # 1. Content Extraction
        content = idea.get("originalContent", "")
        extracted_text = content # Default to original if text
        input_type = idea.get("inputType", "text")

        extraction_error_msg = None
        if input_type == "url":
            logger.info(f"🕷️ [process_new_idea] Extracting content from URL: {content}")
            try:
                extracted = extract_content(content)
                if extracted:
                    extracted_text = extracted
                    logger.info(f"✅ [process_new_idea] Extracted ({len(extracted_text)} chars)")
                else:
                    extraction_error_msg = "Extraction returned empty content."
                    logger.warning(f"⚠️ [process_new_idea] {extraction_error_msg}")
            except Exception as e:
                extraction_error_msg = f"Extraction failed: {str(e)}"
                logger.error(f"❌ [process_new_idea] {extraction_error_msg}")
        
        if extraction_error_msg:
             extracted_text = f"SYSTEM_NOTE: The content extraction failed with error: '{extraction_error_msg}'. Please summarize based on the URL itself, but START THE SUMMARY with: '⚠️ **Content Extraction Failed**'.\n\nURL: {content}"
        
        # 2. Storage (Firestore Sub-collection)
        if len(extracted_text) > 900000: 
            extracted_text = extracted_text[:900000] + "... (truncated)"
            
        db.collection("ideas").document(idea_id).collection("content").document("text").set({
            "fullText": extracted_text
        })
        logger.info("💾 [process_new_idea] Stored content in Firestore sub-collection")

        # 3. AI Summarization
        logger.info(f"🧠 [process_new_idea] Calling AI Service (Input len: {len(extracted_text)})")
        ai_service = get_ai_service()
        result = ai_service.summarize(extracted_text)
        
        logger.info(f"🤖 [process_new_idea] AI Result: {json.dumps(result)}")

        if "error" in result:
             logger.error(f"❌ [process_new_idea] AI reported error: {result['error']}")

        # 4. Drive Upload (Offline Access)
        detailed_analysis = result.get("detailedAnalysis")
        drive_file_id = None
        
        # Try to upload if we have the analysis and user has credentials
        if detailed_analysis:
            try:
                from services.token_service import get_user_credentials
                user_id = doc_snap.get("userId") # Assuming userId is on the idea 
                
                # Check if we have credentials
                creds = get_user_credentials(user_id)
                if creds:
                    logger.info("🔐 [process_new_idea] Found offline credentials. Attempting background upload...")
                    drive_service = get_drive_service(creds) # We need to update drive_service to accept creds
                    
                    filename = f"Idea Farm: {result.get('topic', 'Analysis')}.md"
                    drive_file_id = drive_service.upload_markdown(filename, detailed_analysis)
                    logger.info(f"✅ [process_new_idea] Background Upload Success: {drive_file_id}")
                else:
                     logger.info("ℹ️ [process_new_idea] No offline credentials found. Skipping background upload.")
            except Exception as e:
                logger.error(f"⚠️ [process_new_idea] Background upload failed: {e}")

        # 5. Update Firestore
        update_data = {
            "status": "ready" if "error" not in result else "failed",
            "summary": result.get("overview", result.get("summary")), # Fallback to summary
            "detailedAnalysis": detailed_analysis, 
            "driveFileId": drive_file_id, 
            "topic": result.get("topic", "Uncategorized"),
            "suggestedLinks": result.get("suggestedLinks", []),
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        if "error" in result:
             update_data["error"] = result["error"]

        doc_ref.update(update_data)
        logger.info(f"✨ [process_new_idea] Complete. Final Status: {update_data['status']}")

    except Exception as e:
        logger.exception(f"💥 [process_new_idea] UNHANDLED EXCEPTION: {e}")
        doc_ref.update({
            "status": "failed",
            "error": str(e)
        })

@https_fn.on_call(secrets=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "FERNET_KEY"])
def exchange_auth_code(req: https_fn.CallableRequest) -> dict:
    """
    Exchanges the Auth Code for a Refresh Token and stores it securely.
    """
    try:
        code = req.data.get("code")
        redirect_uri = req.data.get("redirect_uri") # Important for verification
        
        if not code:
            return {"error": "Missing auth code"}

        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
             return {"error": "Server misconfigured (missing ID/Secret)"}

        # Exchange code for tokens
        token_endpoint = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        resp = requests.post(token_endpoint, data=payload)
        token_data = resp.json()
        
        if "error" in token_data:
            logger.error(f"Token exchange failed: {token_data}")
            return {"error": token_data.get("error_description", "Token exchange failed")}
        
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            # If user has already granted offline access, Google might not return a refresh token again 
            # unless we ask with prompt='consent'.
            logger.warning("No refresh token returned. User might need to re-consent.")
            # We can try to prioritize the existing one if we have it? 
            # For now, let's error or just skip saving.
            return {"success": False, "message": "No refresh token returned. Try revoking app access and logging in again."}

        # Encrypt and Store
        encrypted_token = encrypt_token(refresh_token)
        
        db = firestore.client()
        # Store in users/{uid}/params/secrets
        user_id = req.auth.uid
        db.collection("users").document(user_id).collection("params").document("secrets").set({
            "google_drive_refresh_token": encrypted_token,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        logger.info(f"✅ [exchange_auth_code] Wrote secrets for user {user_id} to users/{user_id}/params/secrets")
        
        return {"success": True}

    except Exception as e:
        logger.error(f"Exchange failed: {e}")
        return {"error": str(e)}

@firestore_fn.on_document_deleted(
    document="ideas/{ideaId}",
    secrets=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "FERNET_KEY"]
)
def on_idea_deleted(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
    """
    Cleans up Google Drive file when an idea is deleted.
    """
    try:
        doc_snap = event.data
        if not doc_snap: 
            return

        idea = doc_snap.to_dict()
        drive_file_id = idea.get("driveFileId")
        user_id = idea.get("userId")

        if drive_file_id and user_id:
            logger.info(f"🗑️ [on_idea_deleted] Deleting Drive file {drive_file_id} for user {user_id}")
            from services.token_service import get_user_credentials
            
            creds = get_user_credentials(user_id)
            if creds:
                drive_service = get_drive_service(creds)
                success = drive_service.delete_file(drive_file_id)
                if success:
                    logger.info("✅ [on_idea_deleted] Drive file deleted.")
                else:
                    logger.warning("⚠️ [on_idea_deleted] Failed to delete Drive file.")
            else:
                logger.warning("ℹ️ [on_idea_deleted] No credentials found. Cannot delete Drive file.")
        
    except Exception as e:
        logger.error(f"💥 [on_idea_deleted] Error: {e}")
