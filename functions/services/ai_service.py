"""
AI Service (Vertex AI)

Handles interaction with Google Gemini via the Google Gen AI SDK.
Uses Application Default Credentials (ADC).
"""

import logging
import os
import json
from google import genai
from google.genai.types import Tool, GoogleSearch, GenerateContentConfig, SafetySetting

logger = logging.getLogger(__name__)

default_prompt_template = """
Analyze the following text and provide a structured JSON response. The content is 
for a notebook for learning and inspiration.  Provide any supplemental information
that would be appriate. I do want you to process the text differently,
depending on the content.

- If it is the content of a website, I want you to focus on the content. provide
and interesting background information for someone wanting to learn more

- If it is a YouTube transcript, I want you to focus on the content. provide
and interesting background information about the content creator as well

-If it is an idea or short sentence or sentence fragment, do some research on
the topic and provide a primer on the topic

- If it is a recipe, I want you to focus on the ingredients and directions.
Do include a paragraph that summarizes the narrative.

- if it is an ecommerce site for a product, ignore the text related to the storefront
and focus on the product or item and its features.

for Suggested links, provide exact, clickable links that are relevant to the content and provide a 
brief description of why the link is relevant.

Text:
{content}  # Truncate

Output Format (JSON):
{{
    "overview": "A concise paragraph summary (3-5 sentences) suitable for quick reading.",
    "detailedAnalysis": "A comprehensive, 1-2 page deep dive into the content. Use Markdown formatting (## Headers, - bullets, **bold**). Highlight key insights, arguments, and context.",
    "topic": "Suggested Category",
    "suggestedLinks": [
        {{ "title": "Link Title", "url": "https://example.com", "description": "Why relevant" }}
    ]
}}
"""

class AIService:
    def __init__(self):
        self.client = None
        try:
            # Initialize Vertex AI Client
            project_id = os.environ.get('GCLOUD_PROJECT') or os.environ.get('GCP_PROJECT') or 'idea-farm-70752'
            location = os.environ.get('FUNCTION_REGION') or 'us-central1'
            
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            logger.info(f"AI Service initialized for project {project_id} in {location}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")

    def summarize(self, content: str, prompt_template: str = None) -> dict:
        """
        Generates a summary, topic, and suggested links.
        """
        if not content or not self.client:
            return {}

        template = prompt_template or default_prompt_template

        try:
           prompt = template.format(content=content[:10000])
        except Exception:
           prompt = template.replace("{content}", content[:10000])

        try:
            # Configure Google Search Grounding
            # Using the new SDK's Tool and GoogleSearch definitions
            search_tool = Tool(
                google_search=GoogleSearch()
            )

            # Define Safety Settings
            safety_settings = [
                SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_ONLY_HIGH",
                ),
                SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
                SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
                SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
            ]

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=GenerateContentConfig(
                    tools=[search_tool],
                    safety_settings=safety_settings,
                    temperature=1.0,
                    max_output_tokens=8192,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            text = response.text
            logger.info(f"🤖 [Vertex AI] Raw Response: {text}")

            text = text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)

        except Exception as e:
            logger.exception(f"❌ [Vertex AI] Summarization Critical Failure: {e}")
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
