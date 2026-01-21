# Product Requirements Document: Idea Farm

> Keep this document up to date as the project evolves.

## Overview

Idea Farm is a personal knowledge capture and research assistant. It allows users to save links, articles, videos, books, movies, and text-based ideas for later consumption. The app automatically enriches saved items with AI-generated summaries and suggested links for further exploration, organizing everything by topic.

## Problem Statement

Information overload is a common challenge. Users frequently encounter interesting content (articles, videos, book recommendations) but lack a way to capture and revisit them meaningfully. Existing read-it-later apps store content but do not help users understand or explore topics further.

Idea Farm solves this by:
- Providing a quick way to capture ideas from any device
- Automatically summarizing content and researching related material
- Organizing ideas by topic without manual effort

## Target Users

- Individuals who consume content from multiple sources (web, social media, podcasts, conversations)
- Lifelong learners who want to explore topics in depth
- Busy professionals who want to defer reading without losing context

## Critical User Journeys (CUJs)

### CUJ 1: Capture an Idea

**Scenario**: User finds an interesting article on their phone and wants to save it for later.

**Flow**:
1. User opens Idea Farm on their device
2. User pastes a URL or types a text-based idea
3. User submits the idea
4. System acknowledges receipt and begins background processing
5. User continues with their day

**Success Criteria**: Idea is saved within seconds; user sees confirmation.

### CUJ 2: View Processed Ideas

**Scenario**: User has free time and wants to explore saved ideas.

**Flow**:
1. User opens Idea Farm
2. User sees a list of saved ideas organized by topic
3. User selects an idea
4. User sees:
   - Original content (link or text)
   - AI-generated one-page summary
   - Suggested links for further exploration
5. User clicks a suggested link to learn more

**Success Criteria**: Summary is accurate and digestible; suggested links are relevant.

### CUJ 3: Browse Ideas by Topic

**Scenario**: User wants to explore all ideas related to a specific topic.

**Flow**:
1. User opens Idea Farm
2. User views topic categories
3. User selects a topic
4. User sees all ideas within that topic

**Success Criteria**: Topics are coherent and ideas are correctly categorized.

## Functional Requirements

### P0 (Must Have)

| ID | Requirement | Notes |
|----|-------------|-------|
| F01 | Capture ideas via URL | Support web articles, videos (YouTube), and general links |
| F02 | Capture ideas via plain text | Free-form text input for ideas heard in conversation |
| F03 | Generate one-page summary | AI summarizes the content or researches the topic |
| F04 | Suggest related links | AI provides 3-5 links for further exploration |
| F05 | Automatic topic categorization | AI assigns topics without user input |
| F06 | List view of all ideas | Display ideas grouped by topic |
| F07 | Detail view for each idea | Show overview, deep analysis, and link to Google Drive file |
| F08 | Cross-platform access | Works on mobile and desktop browsers |
| F09 | User authentication | Secure access to personal data |

### P1 (Should Have)

| ID | Requirement | Notes |
|----|-------------|-------|
| F10 | Search across ideas | Full-text search of ideas and summaries |
| F11 | Reminder system | Periodic nudges to revisit unread ideas |
| F14 | Detailed Analysis | Generate a 1-2 page deep dive + overview |
| F15 | Save to Drive | Client-side "Save to Drive" button for Markdown export |

### P2 (Nice to Have)

| ID | Requirement | Notes |
|----|-------------|-------|
| F12 | Browser extension for quick capture | One-click save from the browser |
| F13 | Share ideas via link | Generate a public link to share an idea |

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NF01 | Response time for idea capture | Less than 2 seconds |
| NF02 | Background processing time | Less than 2 minutes for summary generation |
| NF03 | Availability | 99% uptime |
| NF04 | Mobile responsiveness | Fully usable on screens 375px and wider |
| NF05 | Data privacy | Single-user data isolation; no data sharing |
| NF06 | Security | HTTPS; secure authentication; encrypted storage at rest |

## Out of Scope

The following are explicitly excluded from the initial release:
- Voice input
- Collaborative features (sharing with other users)
- Browser extension (P2)
- Native mobile apps (PWA approach covers mobile access)
- Offline mode

## Success Metrics

| Metric | Target |
|--------|--------|
| Ideas captured per week | 10+ |
| Summary accuracy (subjective) | User finds summaries useful 80% of the time |
| Topic accuracy | Ideas are correctly categorized 90% of the time |

## Glossary

- **Idea**: Any captured content, whether a URL or plain text
- **One-pager**: A concise AI-generated summary of the idea
- **Suggested links**: Related content for further exploration
- **Topic**: An AI-assigned category for organizing ideas
