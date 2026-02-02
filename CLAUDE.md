# CLAUDE.md - PromptFinder Project Documentation (1 of 3)

## ⚠️ IMPORTANT: This is Part 1 of 3

**Before proceeding, also read:**
- **CLAUDE_PHASES.md** - Phase specs, unfinished work details
- **CLAUDE_CHANGELOG.md** - Session history, recent changes

These three files together replace the original CLAUDE.md.
Do NOT edit or reference this document without reading all three.

---

**Last Updated:** January 31, 2026
**Project Status:** Pre-Launch Development

**Owner:** Mateo Johnson - Prompt Finder

> **📚 Document Series:**
> - **CLAUDE.md** (1 of 3) - Core Reference ← YOU ARE HERE
> - **CLAUDE_PHASES.md** (2 of 3) - Phase Specifications & Unfinished Work
> - **CLAUDE_CHANGELOG.md** (3 of 3) - Session History

---

## 📋 Quick Status Dashboard

### What's Active Right Now

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase N4** | 🔄 ~90% Complete | Optimistic Upload Flow | Upload page bugs, final testing |
| **Phase N3** | 🔄 ~95% | Single-Page Upload | Final testing, deploy to prod |

### What's Paused (Don't Forget!)

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase K** | ⏸️ 95% | Collections ("Saves") | K.2: Download tracking, virtual collections; K.3: Premium limits |

### Recently Completed

| Phase | When | What It Was |
|-------|------|-------------|
| Phase L | Jan 2026 | Media Infrastructure (moved from Cloudinary to B2 + Cloudflare) |
| Phase M | Jan 2026 | Video NSFW Moderation (FFmpeg frame extraction + OpenAI Vision) |
| Phase J | Dec 2025 | Prompt Detail Page Redesign |

---

## 🚀 Current Phase: N4 - Optimistic Upload Flow

**Status:** ~90% Complete - Upload Page Bugs Remaining
**Detailed Spec:** See `docs/PHASE_N4_UPLOAD_FLOW_REPORT.md`

### Overview
Rebuilding upload flow to feel "instant" by:
- Processing images in background while user types
- Using dedicated processing page with polling
- Running AI analysis after submit
- Deferring file renaming for faster perceived performance

### Implementation Progress

| Sub-Phase | Status | What It Does |
|-----------|--------|--------------|
| **N4a** | ✅ Complete | Model fields: `processing_uuid`, `processing_complete` |
| **N4b** | ✅ Complete | Django-Q2 setup with PostgreSQL ORM broker |
| **N4c** | ✅ Complete | Admin fieldset updates for processing fields |
| **N4d** | ✅ Complete | Processing page template and view |
| **N4e** | ✅ Complete | AI job queuing for videos (uses thumbnail) |
| **N4f** | ✅ Complete | ProcessingModal in upload-form.js |
| **N4 Cleanup** | ✅ Complete | Removed old upload code (step templates, processing.js) |
| **SEO Meta** | ✅ Complete | OG/Twitter blocks, Schema.org JSON-LD + VideoObject, canonical URLs |
| **AI Quality** | ✅ Complete | Style-first titles, description truncation fix, race/ethnicity identification |
| **SEO Enhance** | ✅ Complete | Race/ethnicity in AI prompts, enhanced alt tags, Schema.org VideoObject (Session 64) |
| **N4g Video Fix** | ✅ Resolved | Video submit "Upload data missing" - session key mismatch fixed |
| **CI/CD Fixes** | ✅ Complete | Fixed 31 issues across 9 files, all 3 CI/CD jobs passing (Session 64) |
| **Worker Dyno** | ✅ Complete | Heroku worker dyno configured for Django-Q processing (Session 64) |
| **Collection Edit** | ✅ Complete | Created collection_edit.html, fixed 500 error on edit page (Session 64) |
| **Upload Redesign** | ✅ Complete | Complete visual redesign of upload page with modern card layout (Session 64) |

### Key Components
1. **Variant generation after NSFW** - Start thumbnails while user types
2. **Processing page** - `/prompt/processing/{uuid}/` with polling ✅ IMPLEMENTED
3. **Django-Q background tasks** - AI generation runs async
4. **Deferred file renaming** - SEO filenames applied after "ready"
5. **Fallback handling** - Graceful degradation on AI failure

### Target Performance
- Upload page → Submit: **0 seconds wait** (processing happens after)
- Processing page → Ready: **5-10 seconds**
- Total perceived improvement: **50-60% faster**

### Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Background tasks | Django-Q2 | Free, uses PostgreSQL, no Redis needed |
| Status updates | Polling (3s) | Simple, reliable, Heroku compatible |
| AI analysis ratio | 80% Vision / 20% Text | Users often write vague prompts |
| File cleanup | 5-30 day retention | Use existing trash system |

### Current Blockers (Session 64)

| Issue | Description | Impact |
|-------|-------------|--------|
| **Change File button** | Only visible on hover, needs always-visible state | UX issue on upload page |
| **Privacy toggle** | May not default to Public correctly | Upload form behavior |

### Resolved Blockers (Session 64)

| Issue | Resolution | Session |
|-------|------------|---------|
| Worker dyno | Configured Standard-1X worker dyno on Heroku | 64 |
| CI/CD pipeline | Fixed 31 issues across 9 files, all 3 jobs passing | 64 |
| Collection edit 500 | Created missing collection_edit.html template | 64 |
| N4g: Video submit fails | Session key mismatch fixed | 64 |
| Description truncation | `max_tokens` 500→1000, `max_length` 500→2000 | 63-64 |
| Video redirect delay | Self-resolved (was timing issue) | 64 |

### Production Infrastructure Notes

- **Heroku Worker Dyno**: Configured for Django-Q background processing
  - AI content generation tasks run asynchronously
  - Command: `heroku ps:scale worker=1 --app mj-project-4`
  - Current tier: Standard-1X ($25/month) - can downgrade to Basic ($7/month) for pre-launch
  - Procfile includes: `worker: python manage.py qcluster`

- **B2 CORS Configuration**: Must include all domains
  - `https://promptfinder.net`
  - `https://www.promptfinder.net` (CRITICAL - missing this breaks production uploads)
  - `https://mj-project-4-68750ca94690.herokuapp.com`
  - `http://localhost:8000` (development)
  - Operations: s3_put, s3_get, s3_head
  - Use B2 CLI to update: `b2 bucket update --cors-rules ...`

### Uncommitted Changes (Do Not Revert)

| File | Change |
|------|--------|
| `prompts/tasks.py` | AI prompt rewrite, `max_tokens` 500→1000, description `max_length` 500→2000, domain allowlist, race/ethnicity instructions (S64) |
| `prompts/views/api_views.py` | AI job queuing for videos |
| `prompts/views/upload_views.py` | `.strip()` on excerpt assignment (S64) |
| `prompts_manager/settings.py` | Domain allowlist fix |
| `static/js/upload-form.js` | Pass ai_job_id for videos, icon updates (S64) |
| `static/js/upload-core.js` | File input reset on validation error (S64) |
| `templates/base.html` | OG/Twitter `{% block %}` wrappers |
| `prompts/templates/prompts/upload.html` | Complete upload page redesign - new HTML structure (S64) |
| `prompts/templates/prompts/prompt_detail.html` | OG/Twitter overrides, Schema.org JSON-LD + VideoObject, canonical, `|linebreaks`, enhanced alt tags, video aria-label (S64) |
| `prompts/templates/prompts/collection_edit.html` | New template - collection edit form (S64) |
| `prompts/services/content_generation.py` | `max_tokens` 500→1000, filename 3→5 keywords, alt tag format, race/ethnicity instructions, video description prompt fix (S64) |
| `static/css/upload.css` | Complete rewrite - modern card layout, preview overlay with gradient (S64) |

---

## 🎯 What is PromptFinder?

### The Elevator Pitch

**PromptFinder** is like Pinterest for AI art prompts. Users share the text prompts they used to create AI-generated images and videos, and others can discover, save, and learn from them.

**Example:** Someone creates an amazing cyberpunk image using Midjourney. They upload it to PromptFinder along with the exact prompt: "cyberpunk samurai in neon-lit Tokyo alley, rain reflections, cinematic lighting --ar 16:9 --v 6". Now thousands of other users can find it, save it, and use that prompt for their own creations.

### Who Uses It?

| User Type | What They Do |
|-----------|--------------|
| **AI Artists** | Share their best work, build a following, get likes |
| **Content Creators** | Find prompt inspiration for client projects |
| **Hobbyists** | Learn prompting techniques from the community |
| **Beginners** | Copy working prompts instead of trial-and-error |

### How We Make Money (Planned)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 10 uploads/week, 10 collections, 2 private collections |
| **Premium** | $7/month | Unlimited uploads, unlimited collections, private prompts, analytics |

### Key URLs

| What | URL |
|------|-----|
| Production Site | https://mj-project-4-68750ca94690.herokuapp.com/ |
| Future Domain | https://promptfinder.net |

### Brand Language

- Users = "**Prompt Finders**"
- Community = "**Finder Community**"  
- Tagline = "**Find. Create. Share.**"

---

## 🛠️ Technical Stack

### Core Technologies

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| **Framework** | Django | 5.2.3 | Python web framework |
| **Language** | Python | 3.12 | Backend logic |
| **Database** | PostgreSQL | - | Hosted on Heroku |
| **Media Storage** | Backblaze B2 | - | Images, videos, thumbnails |
| **CDN** | Cloudflare | - | Serves B2 files globally |
| **AI** | OpenAI GPT-4o-mini | - | Content generation, NSFW moderation |
| **Hosting** | Heroku Eco Dyno | - | $5/month |
| **CI/CD** | GitHub Actions | - | Tests, linting, security scans |

### Frontend (No React/Vue)

| Technology | Usage |
|------------|-------|
| Django Templates | Server-side HTML rendering |
| Bootstrap 5 | CSS framework, responsive grid |
| Custom CSS | Component-based architecture (navbar.css, upload.css, etc.) |
| Vanilla JavaScript | No frameworks, just plain JS |
| Lucide Icons | SVG sprite system for icons |

### Authentication

- **Django Allauth** handles login/signup
- Social login ready (Google, Apple - not yet enabled)
- Email verification required

### Legacy Media (Being Phased Out)

Some older prompts still have images stored on **Cloudinary**. New uploads go to **B2**. Templates use "B2-first" pattern:

```python
# If B2 URL exists, use it. Otherwise fall back to Cloudinary.
{{ prompt.b2_image_url|default:prompt.cloudinary_url }}
```

---

## 💰 Current Costs

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Heroku Eco Dyno (web) | $5 | Covered by $248 credits (lasts until late 2026) |
| Heroku Standard-1X (worker) | $25 | Django-Q background tasks; can downgrade to Basic ($7) |
| Heroku PostgreSQL Mini | $5 | Covered by credits |
| Backblaze B2 | ~$0 | Free tier (10GB storage, 1GB/day downloads) |
| Cloudflare | $0 | Free tier |
| OpenAI API | ~$0.50 per 1000 uploads | Pay-as-you-go |
| **Total** | **~$35/month** | Web + DB covered by credits; worker is new cost |

### Why We Moved Away from Cloudinary

1. **NSFW Policy:** Cloudinary's AI flagged legitimate AI art as violations
2. **Cost at Scale:** B2 is ~70% cheaper than Cloudinary
3. **Direct Uploads:** Browser uploads directly to B2 (faster, no server bottleneck)

---

## 📁 Key File Locations

### Working on Uploads? (Phase N)

```
TEMPLATES:
prompts/templates/prompts/upload.html      # The main upload page

JAVASCRIPT (in static/js/):
upload-core.js      # File selection, drag-drop, B2 upload, preview
upload-form.js      # Form handling, NSFW status display  
upload-guards.js    # Navigation guards, idle timeout detection

CSS:
static/css/upload.css    # All upload page styles (~780 lines, rewritten S64)

BACKEND:
prompts/views/api_views.py           # API endpoints (1374+ lines)
prompts/services/b2_presign_service.py    # Generates presigned URLs for B2
prompts/services/b2_upload_service.py     # B2 upload utilities
```

> ⚠️ **CRITICAL: api_views.py is 1374+ lines**
> - Claude Code crashes (SIGABRT) when editing this file
> - ALL edits to api_views.py must be done MANUALLY by developer
> - Create specifications with exact line numbers for manual editing

### Working on Moderation?

```
prompts/services/cloudinary_moderation.py   # VisionModerationService (OpenAI Vision)
prompts/services/video_processor.py         # FFmpeg frame extraction
prompts/services/video_moderation.py        # Video NSFW checking
prompts/services/content_generation.py      # AI title/description/tag generation
```

### Working on Collections? (Phase K - ON HOLD)

```
prompts/models.py                                    # Collection, CollectionItem models
prompts/views/collection_views.py                    # Collections API endpoints
static/js/collections.js                             # Modal JavaScript
prompts/templates/prompts/partials/_collection_modal.html   # Modal HTML
```

### Views Package Structure

Views were split into a modular package for maintainability:

```
prompts/views/
├── __init__.py           # Exports all views
├── api_views.py          # API endpoints (1374 lines - TOO BIG FOR CC)
├── upload_views.py       # Upload page views  
├── admin_views.py        # Admin functions (ordering, bulk actions)
├── prompt_views.py       # Prompt CRUD operations
├── profile_views.py      # User profile pages
└── collection_views.py   # Collections API
```

---

## 🔄 How Upload Works

### Philosophy: "The Restaurant Analogy"

> At a restaurant, we don't ask customers to wash their own dishes. They're customers, not employees.

**Applied to PromptFinder:**
- Users upload content and provide the prompt they used
- WE handle SEO (tags, titles, descriptions, slugs) in the background
- Keep the form simple - minimum required fields only

| User Provides | We Generate (Background) |
|---------------|-------------------------|
| Image/Video | NSFW moderation |
| Prompt text (required) | AI-generated title |
| AI Generator (required) | AI-generated description |
| Visibility (draft/publish) | SEO-optimized tags & slug |

### The User Experience (Phase N - Current)

**Image Flow:**
```
1. User drags/drops an image
        ↓ INSTANT (no upload yet)
2. Preview appears from browser memory
        ↓ BACKGROUND (user doesn't wait)
3. File uploads directly to B2 via presigned URL
        ↓ BACKGROUND
4. Server generates thumbnail
        ↓ BACKGROUND
5. OpenAI Vision checks for NSFW content
        ↓
6. User fills out title, description, tags (while above happens)
        ↓
7. User clicks Submit → Modal shows "Processing content..."
        ↓
8. AI generates title/description/tags in background
        ↓
9. Prompt created → Redirect to detail page
```

**Video Flow (Session 61):**
```
1. User drags/drops a video
        ↓
2. Preview appears from browser memory
        ↓ BACKGROUND
3. Video uploads directly to B2 via presigned URL
        ↓ BACKGROUND
4. FFmpeg extracts frames for NSFW moderation
        ↓ BACKGROUND
5. OpenAI Vision checks frames for NSFW content
        ↓ BACKGROUND
6. AI job queued using video thumbnail
        ↓ (ai_job_id returned to frontend)
7. User fills out form (while above happens)
        ↓
8. User clicks Submit → Modal shows "Processing content..."
        ↓
9. Polls for AI completion using ai_job_id
        ↓
10. Prompt created → Redirect to detail page
```

### Key Principle: Optimistic UX

Users see instant feedback. All the slow stuff (B2 upload, AI processing, NSFW check) happens invisibly in the background.

### Upload Limits

| Limit | Value | Enforced Where |
|-------|-------|----------------|
| Uploads per hour | 20 | Backend (rate limit cache) |
| Image max size | 3 MB | Frontend + Backend |
| Video max size | 15 MB | Frontend + Backend |

### API Endpoints

| Endpoint | Method | What It Does |
|----------|--------|--------------|
| `/api/upload/b2/presign/` | POST | Get presigned URL for direct B2 upload |
| `/api/upload/b2/complete/` | POST | Confirm upload, generate thumbnail |
| `/api/upload/b2/moderate/` | POST | Run NSFW check |
| `/api/upload/b2/delete/` | POST | Delete orphaned file (cleanup) |
| `/upload/submit/` | POST | Final submission, create Prompt |

---

## 🛡️ NSFW Moderation

### How It Works

1. Image/video uploads to B2
2. OpenAI Vision API analyzes it
3. Returns severity level
4. We take action based on severity

### Severity Levels

| Severity | What It Means | What Happens |
|----------|---------------|--------------|
| **critical** | Clearly prohibited (minors, extreme) | REJECTED - upload blocked |
| **high** | Likely problematic | FLAGGED - needs admin review |
| **medium** | Borderline | APPROVED with internal note |
| **low/none** | Safe | APPROVED |

### Video Moderation (Phase M)

Videos get 3 frames extracted at 25%, 50%, 75% of duration using FFmpeg. Each frame is sent to OpenAI Vision. If ANY frame is critical → video rejected.

### What's Banned

- Explicit nudity/sexual content
- Minors in any suggestive context (ZERO TOLERANCE)
- Violence, gore, blood
- Hate symbols
- Satanic/occult imagery
- Medical/graphic content

---

## 🤖 Development Workflow

### The Micro-Spec Approach

We learned the hard way: **big specs fail**. Claude Code ignores details in long specs and gives misleading high ratings on broken code.

**Now we use micro-specs:**
- Each spec = 10-20 lines of code max
- Manual testing after each spec
- Agent validation required (8+/10)

### Dual Agent Quality System

| When | System | Tool |
|------|--------|------|
| During coding | System 1 | wshobson/agents in Claude Code |
| After coding | System 2 | Claude.ai review personas |

**Required:** 8+/10 average rating before committing

### File Size Warning for Claude Code

| File Size | Can CC Edit It? |
|-----------|-----------------|
| < 500 lines | ✅ Yes, safe |
| 500-1000 lines | ⚠️ Be careful |
| > 1000 lines | ❌ NO - edit manually |

**`api_views.py` is 1374 lines. NEVER let CC edit it directly.**

---

## 📊 Key Configuration Values

### Upload Config (in upload.html)

```javascript
window.uploadConfig = {
    maxFileSize: 3 * 1024 * 1024,      // 3MB for images
    maxVideoSize: 15 * 1024 * 1024,    // 15MB for videos
    allowedImageTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    allowedVideoTypes: ['video/mp4', 'video/quicktime', 'video/webm'],
    idleTimeout: 300000,               // 5 min until warning
    idleWarning: 60000,                // 1 min countdown
};
```

### Rate Limit Constants (in api_views.py)

```python
B2_UPLOAD_RATE_LIMIT = 20    # max uploads per window
B2_UPLOAD_RATE_WINDOW = 3600 # window = 1 hour (3600 seconds)
```

---

## 🔗 Related Documents

| Document | What It Contains |
|----------|------------------|
| **CLAUDE_PHASES.md** (2 of 3) | Detailed phase specs, especially Phase K unfinished work |
| **CLAUDE_CHANGELOG.md** (3 of 3) | Session history, what was done when |
| `docs/CC_COMMUNICATION_PROTOCOL.md` | Agent requirements for Claude Code |
| `docs/CC_SPEC_TEMPLATE.md` | Template for writing specs |
| `PROJECT_FILE_STRUCTURE.md` | Complete file tree |

---

## ✅ Quick Start Checklist for New Sessions

1. ☐ Read this document for overall context
2. ☐ Check **CLAUDE_PHASES.md** for current phase details and unfinished work
3. ☐ Check **CLAUDE_CHANGELOG.md** for what was done in recent sessions
4. ☐ Create micro-specs (not big specs) for any new work
5. ☐ Get 8+/10 agent ratings before committing
6. ☐ Don't let CC edit files > 1000 lines
7. ☐ Update CLAUDE_CHANGELOG.md at end of session

---

**Version:** 3.7 (Phase N4 Session 64 - CI/CD, Worker Dyno, Upload Redesign)
**Last Updated:** January 31, 2026
