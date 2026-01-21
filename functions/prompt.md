Analyze the following text and provide a structured JSON response.

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
