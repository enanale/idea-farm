"""
AI Service (Vertex AI)

Handles interaction with Google Gemini via Vertex AI.
Uses Application Default Credentials (ADC) - No API Key required.
"""

import logging
import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from google.auth import default

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.model = None
        try:
            # Initialize Vertex AI
            # Cloud Functions usually provide project_id in environment or metadata
            project_id = os.environ.get('GCLOUD_PROJECT') or os.environ.get('GCP_PROJECT') or 'idea-farm-70752'
            location = os.environ.get('FUNCTION_REGION') or 'us-central1'
            
            vertexai.init(project=project_id, location=location)
            
            self.model = GenerativeModel("gemini-2.5-flash")
            logger.info(f"AI Service initialized for project {project_id} in {location}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")

    def summarize(self, content: str) -> dict:
        """
        Generates a summary, topic, and suggested links.
        """
        if not content or not self.model:
            return {}

        prompt = f"""
        Analyze the following text and provide a structured JSON response.
        
        Text:
        {content[:10000]}  # Truncate
        
        Output Format (JSON):
        {{
            "summary": "One paragraph summary...",
            "topic": "Suggested Category",
            "suggestedLinks": [
                {{ "title": "Link Title", "url": "https://example.com", "description": "Why relevant" }}
            ]
        }}
        """

        try:
            responses = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 8192,
                    "top_p": 0.8,
                    "top_k": 40,
                    "response_mime_type": "application/json"
                },
                stream=False
            )
            
            text = responses.text
            logger.info(f"🤖 [Vertex AI] Raw Response: {text}")

            # Cleanup markdown (still safe to keep)
            text = text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(text)
        except Exception as e:
            logger.exception(f"❌ [Vertex AI] Summarization Critical Failure: {e}") # Full stack trace
            return {
                "summary": "AI Summarization failed.",
                "topic": "Uncategorized",
                "suggestedLinks": [],
                "error": str(e)
            }

# Singleton
_ai_service = None

def get_ai_service():
    global _ai_service
    if not _ai_service:
        _ai_service = AIService()
    return _ai_service
