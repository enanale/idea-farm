# Idea Farm

Idea Farm is a personal knowledge capture and research assistant. It helps you save links, articles, videos, book recommendations, and random ideas for later exploration.

## What It Does

When you save an idea, Idea Farm automatically:
- Summarizes the content into a digestible one-pager
- Assigns a topic for organization
- Suggests related links for further exploration

Access your ideas from any device through a responsive web interface.

## Who It Is For

- People who consume content from multiple sources and want a place to save ideas for later
- Lifelong learners who want to explore topics in depth
- Busy professionals who need to defer reading without losing context

## Features

- Save URLs (articles, YouTube videos, general links) or plain text ideas
- AI-generated summaries and related link suggestions
- Automatic topic categorization
- Cross-platform access (mobile and desktop)
- Secure single-user authentication

## Documentation

- [Product Requirements Document](PRD.md) - Functional requirements and user journeys
- [Technical Design Document](TDD.md) - Architecture, stack decisions, and implementation details

## Project Status

**Current Status**: Functional MVP (v1.0)
- ✅ URL Capture & Extraction (Trafilatura)
- ✅ Vertex AI Summarization (Gemini 2.5 Flash)
- ✅ Real-time UI Updates (Firestore Listeners)
- ✅ **Secure Offline Access**: Automatic background saving to Google Drive with synchronized deletion.
- ⚠️ Bot Protection: Basic User-Agent spoofing implemented; some sites (e.g. OpenAI) may still block extraction.

## Development Setup

1. **Prerequisites**: Node.js, Python 3.10+, Firebase CLI
2. **Install Dependencies**:
   ```bash
   cd frontend && npm install
   cd ../functions
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run Locally**:
   ```bash
   firebase emulators:start
   # In another terminal:
   cd frontend && npm run dev
   ```

## Deployment

```bash
firebase deploy
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
