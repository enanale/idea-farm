"""
Idea Farm - Cloud Functions Entry Point
"""

import json
import os
import logging
from firebase_functions import firestore_fn, options
from firebase_admin import initialize_app, firestore

# Import services
from services.content_extractor import extract_content
from services.ai_service import get_ai_service
from services.drive_service import get_drive_service # Not used in MVP V1 (using Firestore storage)

# Initialize Firebase Admin
initialize_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@firestore_fn.on_document_created(
    document="ideas/{ideaId}",
    memory=options.MemoryOption.MB_512,
    timeout_sec=540
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

        # 4. Update Firestore
        update_data = {
            "status": "ready" if "error" not in result else "failed",
            "summary": result.get("summary"),
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
