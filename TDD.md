# Technical Design Document: Idea Farm

> Keep this document up to date as the project evolves.

## Overview

This document describes the technical architecture, stack choices, and implementation decisions for Idea Farm - a personal knowledge capture and research assistant.

## Architecture (Decided)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (PWA)                             │
│                     React + TypeScript                          │
└───────────┬─────────────────────────────────┬───────────────────┘
            │                                 │
            │ Direct Firestore                │ HTTPS (Auth)
            │ Reads/Writes                    │
            ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│      Firestore        │         │    Firebase Auth      │
│      (Database)       │         │    (Authentication)   │
└───────────┬───────────┘         └───────────────────────┘
            │
            │ onCreate Trigger
            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cloud Functions (2nd Gen, Python)                  │
│                Async Event Handlers (Triggers)                  │
└───────────┬─────────────────────────────────┬───────────────────┘
            │                                 │
            ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│    Google Drive       │         │     Gemini API        │
│    (Blob Storage)     │         │     (AI / Summary)    │
└───────────────────────┘         └───────────────────────┘
```

## Technology Stack

### Frontend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | React 18 + TypeScript | Industry standard; strong PWA support via Vite |
| Build Tool | Vite | Fast dev server; native PWA plugin; modern tooling |
| Styling | Vanilla CSS | Maximum flexibility; no framework lock-in |
| State | React Context + useReducer | Simple state needs; no external library required |
| PWA | vite-plugin-pwa | Service worker generation; offline caching |
| HTTP Client | fetch API | Native; no dependencies |

**Alternatives Considered**:
- Vue.js: Simpler learning curve but smaller ecosystem for specific integrations
- Next.js: Overkill for a single-user app; SSR not needed
- Svelte: Less ecosystem maturity; smaller community

### Backend (Decided: Firebase + Google Cloud)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Python 3.10 + Firebase Functions SDK | Event-driven architecture; simpler than full FastAPI app |
| Hosting | Firebase Hosting | CDN; custom domain; SSL included; rewrite rules to backend |
| Backend | Cloud Functions (2nd Gen) | Native Python support; built on Cloud Run; scales to zero |
| Database | Firestore | NoSQL; simpler ops; real-time updates; auto-scaling |
| Blob Storage | Google Drive | Built-in indexing; familiar UI; 15 GB free |
| Job Queue | Cloud Tasks | Managed; triggers Cloud Functions; no server needed |
| Authentication | Firebase Auth | Managed JWT; email/password; OAuth providers |

**Alternatives Considered but Rejected**:
- PostgreSQL + Redis + RQ: More complex ops; requires managing servers
- Vercel/Netlify + Railway: Multiple providers; fragmented billing
- Cloud Storage: No built-in search/indexing; less user-accessible

### AI Integration Strategy: Genkit vs. Firebase AI Logic

We evaluated two Firebase-native approaches for AI integration:

| Feature | Genkit (Open Source Framework) | Firebase AI Logic (Client SDKs) |
|---------|--------------------------------|---------------------------------|
| **Primary Use Case** | Server-side orchestration, complex flows, custom models | Client-side features (chat, personalization) |
| **Execution Environment** | Server (Node.js/Go/Python) | Client (Browser/Mobile) |
| **Control** | Full backend control, secure, observable | Fast feedback, less infra, but less control |
| **Model Support** | Broad (Google, OpenAI, Anthropic, Custom) | Vertex AI (Gemini, Imagen) |
| **Data Handling** | Good for complex RAG, scraping, heavy processing | Good for direct user interaction |

**Decision: Server-Side Logic (Python Cloud Functions)**

We chose a **Server-Side approach** (functionally similar to Genkit, implemented via Python SDKs) for the following reasons:

1.  **Content Extraction Requirement**: The core feature involves scraping third-party URLs (`trafilatura`), which requires server-side execution to bypass CORS and handle heavy parsing.
2.  **Tech Stack Match**: The backend is built in **Python**. While Genkit supports Python (experimental), using the native `google-cloud-aiplatform` (Vertex AI) SDK provides a stable, idiomatic Python experience.
3.  **Security**: API keys and complex logic are hidden from the client.
4.  **Async/Event-Driven**: The "Process New Idea" flow is asynchronous (triggered by DB write), fitting perfectly with Cloud Functions.

**Note**: If we migrate to Node.js in the future, **Genkit** would be the natural choice for standardizing these flows.

### AI Layer Implementation (Current)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| LLM Provider | **Vertex AI (Gemini Pro)** | Enterprise-grade reliability, IAM auth (no API keys), Python SDK |
| Content Extraction | Trafilatura | Python library for extracting article content from URLs |
| Video Transcripts | youtube-transcript-api | Python library for YouTube transcript extraction |
| **Bot Filter Bypass** | **Requests + User-Agent Spoofing** | Many sites (e.g., OpenAI, NYT) block default Python user agents. We use `requests` with a browser-mimicking UA to fetch HTML before passing to Trafilatura. |
| **Error Handling** | **System Prompt fallback** | If extraction fails (e.g., persistent 403), the error is injected into the AI prompt so the summary explicitly states "Content Extraction Failed" rather than hallucinating. |

**Alternatives Considered**:
- **Firebase AI Logic (Client SDK)**: Rejected because client-side scraping is not feasible due to CORS.
- **Genkit**: Rejected for V1 because the project is Python-based (Genkit is TS-first).
- **OpenAI GPT-4**: More expensive; Gemini offers comparable quality for summarization.

### Storage Layer: Google Drive as Blobstore (Decided)

Google Drive serves as the blobstore for storing original content (extracted articles, transcripts, PDFs). This keeps Firestore lean (metadata only) while leveraging Drive's built-in indexing and providing a familiar interface for the user.

**Architecture with Drive:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         Firestore                               │
│            (metadata, topics, summaries, suggested links)       │
│                        idea.driveFileId ────────────────────┐   │
└─────────────────────────────────────────────────────────────│───┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Google Drive                              │
│              (original content, extracted text, PDFs)           │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  /IdeaFarm/                                             │   │
│   │    ├── idea-{uuid}.txt   (extracted article text)       │   │
│   │    ├── idea-{uuid}.json  (video transcript)             │   │
│   │    └── idea-{uuid}.pdf   (saved webpage snapshot)       │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Indexing Strategy for Search (P1):**

Google Drive offers multiple indexing mechanisms:

| Method | Description | Limit |
|--------|-------------|-------|
| Automatic Indexing | Drive indexes text files, PDFs, images with OCR | Common file types only |
| `indexableText` | Hidden metadata field for searchable keywords | 128 KB per file |
| Custom Properties | Key-value pairs attached to files | 124 properties; 128 bytes/key |
| Drive API `files.list` | Query by name, mimeType, properties | Full query syntax |

**Implementation:**

1. Store extracted content as `.txt` files in a dedicated `/IdeaFarm` folder
2. Set `indexableText` with the AI-generated summary + key topics
3. Add custom properties: `topic`, `ideaId`, `createdAt`
4. For search, combine:
   - Drive API `fullText contains "query"` for content search
   - Firestore queries for metadata/topic filtering

**Pros of Google Drive as Blobstore:**

| Benefit | Description |
|---------|-------------|
| 15 GB Free Storage | Generous free tier; 100 GB for $2/month if needed |
| Built-in Indexing | Automatic full-text search for common file types |
| Google Ecosystem | Native integration with Google Workspace MCP |
| Familiar Interface | User can browse files directly in Drive UI |
| Backup/Export | Easy manual backup; no vendor lock-in for raw data |
| Version History | Drive maintains file revision history |

**Cons of Google Drive as Blobstore:**

| Drawback | Description |
|----------|-------------|
| API Rate Limits | 500,000 requests/day; 20,000/100 seconds (generous for personal use) |
| Latency | Slightly higher latency than Cloud Storage for file operations |
| Not a True Database | No transactions; eventual consistency for indexing |
| Search Limitations | Full-text search less powerful than Algolia/Typesense |
| Quota Sharing | Uses same quota as personal Drive storage |

**Recommendation:**

Use Google Drive as the blobstore for original content. This approach:

1. Keeps Firestore documents small (metadata + summary only)
2. Provides free full-text search via Drive API
3. Allows user to browse raw content in familiar Drive interface
4. Simplifies backup (content is in user's Drive)

For P1 search feature, combine:
- Drive API `fullText` search for content
- Firestore queries for topic/date filtering
- Merge results in the backend

## Data Model (Firestore)

### Ideas Collection

```javascript
// Collection: ideas
// Document ID: auto-generated
{
  userId: "firebase-auth-uid",        // Firebase Auth UID
  inputType: "url" | "text",          // Type of input
  originalContent: "https://...",     // URL or raw text
  driveFileId: "1abc...",             // Google Drive file ID for extracted content
  summary: "AI-generated summary...", // One-pager summary
  suggestedLinks: [                   // Array of related links
    { title: "...", url: "...", description: "..." }
  ],
  topic: "Technology",                // AI-assigned topic
  status: "pending" | "processing" | "ready" | "failed",
  createdAt: Timestamp,
  updatedAt: Timestamp
}

// Composite index: userId + topic (for topic filtering)
// Composite index: userId + createdAt (for chronological listing)
```

### Users Collection (Optional - Firebase Auth handles most user data)

```javascript
// Collection: users
// Document ID: Firebase Auth UID
{
  email: "user@example.com",
  displayName: "User Name",
  driveRootFolderId: "1xyz...",  // IdeaFarm folder in user's Drive
  createdAt: Timestamp
}
```

**Note:** Firebase Auth manages authentication. The users collection stores app-specific preferences only.

## API Endpoints

### Authentication (Firebase Auth - Client-Side SDK)

Firebase Auth handles authentication client-side. No custom auth endpoints needed.

```javascript
// Frontend uses Firebase Auth SDK directly
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
```

### Ideas (Direct Firestore Access)

The frontend interacts directly with Firestore for all CRUD operations. No HTTP API needed for basic tasks.

| Operation | Firestore Action | Rules Coverage |
|-----------|------------------|----------------|
| Create | `addDoc('ideas', data)` | `allow create` if authenticated & UID matches |
| List | `query('ideas', where('userId', '==', uid))` | `allow read` if owner (Composite Index required) |
| Get | `getDoc('ideas', id)` | `allow read` if owner |
| Delete | `deleteDoc('ideas', id)` | `allow delete` if owner |

### Google Drive (Offline/Server-Side via User Credentials)

We implement **Offline Access** to allow the backend (Cloud Functions) to act on behalf of the user without constant client-side interaction.

**Flow**:
1.  **Auth (Frontend)**: User logs in and grants `drive.file` scope + `offline_access`.
2.  **Code Exchange**: Frontend sends the **Auth Code** to a Cloud Function (`exchange_auth_code`).
3.  **Token Storage**: Backend exchanges code for **Access Token** + **Refresh Token**.
4.  **Encryption**: Refresh Token is **Encrypted** (AES-GCM) using a key from Google Cloud Secret Manager (or ENV for MVP) and stored in a secure Firestore collection (`users/{uid}/params/secrets`).
5.  **Background Operation**:
    - `process_new_idea` retrieves the encrypted token.
    - Decrypts and refreshes access token.
    - Uploads file and updates `idea.driveFileId`.

**Security Constraints**:
- `users/{uid}/params/secrets` must have `allow read, write: if false;` in Firestore Rules (Backend Admin SDK only).
- Encryption Key must never be committed to repo.

| Trigger | Function Name | Description |
|---------|---------------|-------------|
| `onDocumentCreated` | `process_new_idea` | Triggered when a new doc is added to `ideas`. Orchestrates extraction, Drive upload, and Gemini summarization. |

### P1 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /ideas/search?q={query} | Full-text search across ideas |
| GET | /reminders | Get ideas due for reminder |

## Background Processing Flow

```
1. User submits idea (URL or text)
         │
         ▼
2. Client writes Firestore doc with status='pending'
         │
         ▼
3. Cloud Function `on_document_created` triggered
         │
         ▼
4. Function sets status='processing'
         │
         ├─── If URL ──────────────────────────┐
         │                                     ▼
         │                        Extract content (Trafilatura)
         │                        or transcript (YouTube API)
         │                                     │
         ├─────────────────────────────────────┘
         │
         ▼
5. Upload extracted content to Google Drive
   - Create file in /IdeaFarm folder
   - Set indexableText for search
   - Store driveFileId in Firestore
         │
         ▼
6. Send content to Gemini API:
   - Generate summary
   - Assign topic
   - Suggest related links
         │
         ▼
7. Update Firestore doc with results, status='ready'
```

## Project Structure

```
idea-farm/
├── frontend/                      # React PWA (deployed to Firebase Hosting)
│   ├── src/
│   │   ├── components/
│   │   │   ├── IdeaList.tsx
│   │   │   ├── IdeaDetail.tsx
│   │   │   ├── IdeaForm.tsx
│   │   │   └── TopicNav.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── hooks/
│   │   │   └── useAuth.ts
│   │   ├── lib/
│   │   │   ├── firebase.ts        # Firebase client config
│   │   │   └── api.ts             # API client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── functions/                     # Cloud Functions (Python)
│   ├── main.py                    # Function entry points
│   ├── services/
│   │   ├── ai_service.py          # Gemini API integration
│   │   ├── content_extractor.py   # URL content extraction
│   │   └── drive_service.py       # Google Drive operations
│   └── requirements.txt
├── firebase.json                  # Firebase config (hosting, rewrites)
├── firestore.rules               # Firestore security rules
├── firestore.indexes.json        # Composite indexes
├── .firebaserc                   # Firebase project alias
├── PRD.md
├── TDD.md
├── README.md
└── LICENSE
```

## Deployment

### Development

```bash
# Start Firebase emulators (Firestore, Functions, Hosting)
firebase emulators:start

# Start frontend dev server (with emulator connection)
cd frontend && npm run dev
```

**Emulator Ports:**
- Firestore: localhost:8080
- Functions: localhost:5001
- Hosting: localhost:5000
- Emulator UI: localhost:4000

### Production (Decided: Firebase)

Firebase is the decided deployment platform for the following reasons:

1. User already has Firebase projects set up
2. Single-user app does not require complex SQL queries
3. Simpler deployment and operations
4. Firebase Auth simplifies authentication implementation
5. Generous free tier covers personal use

**Deployment Commands:**

```bash
# Deploy everything
firebase deploy

# Deploy only frontend
firebase deploy --only hosting

# Deploy only functions
firebase deploy --only functions
```

**Firebase Project Configuration:**

```
idea-farm/
├── firebase.json          # Hosting config, rewrites
├── firestore.rules        # Security rules
├── firestore.indexes.json # Composite indexes
└── functions/             # Cloud Functions (Python)
```

### Considered but Rejected: Multi-Provider Approach

| Component | Considered Option |
|-----------|-------------------|
| Frontend | Vercel or Netlify |
| Backend | Railway, Render, or Cloud Run |
| Database | Railway PostgreSQL or Supabase |
| Queue | Railway Redis or Upstash |

**Why Rejected:**

- Multiple providers to manage with fragmented billing
- More complex deployment pipeline
- PostgreSQL's SQL advantages not needed for single-user app
- User prefers unified Google ecosystem

## Security Considerations

1. **Authentication**: JWT tokens with short expiration (15 min access, 7 day refresh)
2. **Password Storage**: bcrypt with salt rounds of 12
3. **API Security**: CORS configured for frontend origin only
4. **Data Isolation**: All queries filtered by user_id
5. **HTTPS**: Required in production
6. **Environment Variables**: Secrets stored in env vars, not code

## Performance Considerations

1. **Idea Capture**: Synchronous; returns immediately after database insert
2. **AI Processing**: Asynchronous via job queue; user polls for status
3. **List View**: Paginated (20 items per page)
4. **Caching**: Topic list cached in Redis (5 min TTL)

## Future Considerations (Out of Scope for V1)

- Full-text search with PostgreSQL tsvector (P1)
- Reminder notifications via email or push (P1)
- Browser extension for quick capture (P2)
- Offline PWA support with sync
- Browser extension for quick capture (P2)

## Lessons Learned (V1 MVP)

1.  **Bot Filters & Content Extraction**:
    - Simple `trafilatura.fetch_url` is insufficient for major sites (OpenAI, NYT).
    - **Solution**: Use `requests` with a browser User-Agent header to download HTML, then pass to `trafilatura.extract`.
    - **Future**: Need proxies or dedicated scraping API for robust access.

2.  **AI JSON Reliability**:
    - `gemini-pro` and `flash` models can truncate JSON if `max_output_tokens` is too low (default 1024).
    - **Solution**: Increased tokens to 8192 and enforced `response_mime_type="application/json"`.

3.  **Real-Time UI**:
    - Users expect instant updates for async background processes.
    - **Solution**: Replaced one-time `getDocs` fetch with Firestore `onSnapshot` listeners in React.

4.  **Python Cloud Functions**:
    - Managing Python dependencies requires careful `requirements.txt` curation. 
    - **Vertex AI**: Requires `google-cloud-aiplatform` (not `google-generativeai`).

5.  **Google Drive & Service Accounts**:
    - **Lesson**: Service Accounts cannot upload files to personal Gmail accounts because they have 0 bytes of storage and assume ownership of created files.
    - **Solution**: Use Client-Side Uploads involved the user's own OAuth credentials.

