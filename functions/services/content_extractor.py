"""
Content Extraction Service

Handles extraction of text from web pages (via Trafilatura) 
and video transcripts (via YouTube API).
"""

import logging
import requests
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def extract_content(url: str) -> str | None:
    """
    Extracts content from a URL.
    Detects if it's a YouTube video or a regular web page.
    """
    if not url:
        return None

    try:
        # Check for YouTube
        video_id = _get_youtube_video_id(url)
        if video_id:
            logger.info(f"Detected YouTube video: {video_id}")
            return _get_youtube_transcript(video_id)
        
        # Default to web page extraction
        logger.info(f"Extracting web page: {url}")
        return _extract_web_page(url)
    except Exception as e:
        logger.error(f"Extraction failed for {url}: {e}")
        return None

def _get_youtube_video_id(url: str) -> str | None:
    """Parses YouTube video ID from URL."""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path[1:]
    if parsed.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
    return None

def _get_youtube_transcript(video_id: str) -> str:
    """Fetches transcript for a YouTube video."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        # Combine text parts
        full_text = " ".join([entry['text'] for entry in transcript_list])
        return f"YouTube Transcript:\n\n{full_text}"
    except Exception as e:
        logger.warning(f"Could not get transcript for {video_id}: {e}")
        return None

def _extract_web_page(url: str) -> str:
    """
    Extracts main text content from a web page using Trafilatura.
    Uses requests with a browser-like User-Agent to bypass basic bot filters.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    
    downloaded = None
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response Status: {response.status_code}")
        response.raise_for_status()
        downloaded = response.text
        logger.info(f"Downloaded RAW content length: {len(downloaded) if downloaded else 0}")
    except Exception as e:
        logger.warning(f"Requests failed for {url}: {e}. Retrying with Trafilatura fetch...")
        # Fallback to Trafilatura's internal fetcher
        downloaded = trafilatura.fetch_url(url)
    
    if not downloaded:
        raise ValueError("Failed to fetch URL content")
    
    text = trafilatura.extract(downloaded, include_comments=False)
    if not text:
        logger.error(f"Trafilatura extraction returned empty for {url}")
        raise ValueError("No text extracted from content")
        
    logger.info(f"Extracted Text Preview (First 500 chars): {text[:500]}")
    return text
