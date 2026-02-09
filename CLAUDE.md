# CLAUDE.md - PromptFinder Project Documentation (1 of 3)

## ⚠️ IMPORTANT: This is Part 1 of 3

**Before proceeding, also read:**
- **CLAUDE_PHASES.md** - Phase specs, unfinished work details
- **CLAUDE_CHANGELOG.md** - Session history, recent changes

These three files together replace the original CLAUDE.md.
Do NOT edit or reference this document without reading all three.

---

**Last Updated:** February 9, 2026
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
| **Phase N4** | 🔄 ~99% Complete | Optimistic Upload Flow | XML sitemap, indexes migration, final testing |
| **Phase N3** | 🔄 ~95% | Single-Page Upload | Final testing, deploy to prod |

### What's Paused (Don't Forget!)

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase K** | ⏸️ ~96% | Collections ("Saves") | Trash video bugs (3), K.2: Download tracking, virtual collections; K.3: Premium limits |

### Recently Completed

| Phase | When | What It Was |
|-------|------|-------------|
| Subject Categories P2 | Feb 9, 2026 | AI-assigned prompt classification (25 categories, cache-first logic) |
| Related Prompts P1 | Feb 7, 2026 | "You Might Also Like" section on prompt detail (scoring algorithm, AJAX Load More) |
| Phase L | Jan 2026 | Media Infrastructure (moved from Cloudinary to B2 + Cloudflare) |
| Phase M | Jan 2026 | Video NSFW Moderation (FFmpeg frame extraction + OpenAI Vision) |
| Phase J | Dec 2025 | Prompt Detail Page Redesign |

---

## 🚀 Current Phase: N4 - Optimistic Upload Flow

**Status:** ~99% Complete - Lighthouse 96/100/100/100, All Core Features Done
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
| **Upload Polish** | ✅ Complete | File input reset fix, visibility toggle, native aspect ratio preview (Session 66) |
| **CSS Architecture** | ✅ Complete | Shared media container component, 22 border-radius unified to var(--radius-lg) (Session 66) |
| **SEO Overhaul** | ✅ Complete | Comprehensive SEO: JSON-LD, OG/Twitter, canonical, headings, noindex drafts (72→95/100) (Session 66) |
| **SEO Headings** | ✅ Complete | Fixed heading hierarchy (H1→H2→H3), visual breadcrumbs with focus-visible (Session 67) |
| **N4h File Rename** | ✅ Complete | B2 SEO file renaming: seo.py utility, B2RenameService, background task in tasks.py (Session 67) |
| **Admin Improvements** | ✅ Complete | Prompt ID display, B2 Media URLs fieldset, all fieldsets expanded (Session 68) |
| **Upload UX** | ✅ Complete | 30-second soft warning toast, improved error message with friendly copy (Session 68) |
| **Perf: Backend** | ✅ Complete | select_related/prefetch_related optimization, materialized likes/comments, query reduction ~60-70% (Session 68) |
| **Perf: Caching** | ✅ Complete | Template fragment caching for tags and more_from_author (5-min TTL) (Session 68) |
| **Perf: Indexes** | ✅ Complete | Composite indexes: (status,created_on), (author,status,deleted_at) - migration pending (Session 68) |
| **Perf: Frontend** | ✅ Complete | Critical CSS inlining, async CSS loading, LCP preload with imagesrcset, preconnect hints, JS defer (Session 68) |
| **SEO: robots.txt** | ✅ Complete | Created robots.txt served via WHITENOISE_ROOT (HTTP 200, no redirect) (Session 69) |
| **Perf: CSS Optim** | ✅ Complete | Removed stale preconnects, reduced font weights (4→3), deferred icons.css with noscript fallback (Session 69) |
| **A11y Fixes** | ✅ Complete | Fixed heading hierarchy (h3→h2), aria-label mismatches with pluralize filter (Session 69) |
| **Asset Minification** | ✅ Complete | Management command for CSS/JS minification targeting STATIC_ROOT (Session 69) |

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

### Current Blockers

| Issue | Description | Impact |
|-------|-------------|--------|
| **N4h rename not triggering** | `rename_prompt_files_for_seo` task is coded but not generating SEO filenames in production | Files keep UUID names instead of SEO slugs |
| **Indexes migration pending** | Composite indexes added to models.py but `makemigrations` not yet run | Indexes not active in database |

**N4h Root Cause (Suspected):** The rename task queues after AI content generation completes, but may not be triggering due to Django-Q worker configuration or the task not being picked up. Needs investigation.

**Resolved in Session 69:** SEO score regression (92→100) fixed via robots.txt + preconnect cleanup + font optimization.

### Phase K Known Bugs (Session 73)

| Bug | Description | Impact |
|-----|-------------|--------|
| Video poster aspect ratio | Poster images may crop to wrong aspect ratio with `object-fit: cover` | Visual glitch |
| Mobile play icon resize | Play icon doesn't reappear after desktop→mobile resize | Minor UX |
| Videos at ≤768px | Videos disappear on homepage/gallery at mobile breakpoint | Needs investigation |

### Related Prompts Feature (Session 74)

"You Might Also Like" section on prompt detail pages.

| Component | Details |
|-----------|---------|
| **Scoring algorithm** | `prompts/utils/related.py` — 5-factor weighted scoring |
| **Weights** | 35% tags, 35% categories, 10% generator, 10% engagement, 10% recency |
| **Pre-filter** | Must share at least 1 tag OR same AI generator (max 500 candidates) |
| **AJAX endpoint** | `/prompt/<slug>/related/` — 18 per page, 60 max |
| **Layout** | CSS `column-count` responsive grid (4→3→2→1 columns) |
| **Video autoplay** | IntersectionObserver on desktop (skip mobile/reduced-motion) |
| **Load More** | Reinitializes video observer after appending new cards |

### Subject Categories Feature (Session 74)

AI-assigned subject categories for prompt classification.

| Component | Details |
|-----------|---------|
| **Model** | `SubjectCategory` — name, slug, description, display_order |
| **Relationship** | `Prompt.categories` M2M field (1-3 categories per prompt) |
| **AI assignment** | During upload via OpenAI Vision prompt, written to cache at 90% progress |
| **Categories** | 25 predefined (Portrait, Sci-Fi, Fantasy, Anime, Abstract, etc.) |
| **Migrations** | `0046_add_subject_categories.py`, `0047_populate_subject_categories.py` |
| **Backfill** | `python manage.py backfill_categories` — exists but DO NOT RUN until Phase 2B completes |
| **Admin** | `SubjectCategoryAdmin` with read-only enforcement (no add/delete) |

### Phase 2B: Category Taxonomy Revamp (Planned)

Full design in `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md`, execution roadmap in `docs/PHASE_2B_AGENDA.md`.

- Expand to 43 subject categories (from 25)
- Add `SubjectDescriptor` model (~108 descriptors across 10 types: gender, ethnicity, age, features, profession, mood, color, holiday, season, setting)
- Tag limit increase: 5 → 10
- Category limit increase: 3 → 5
- Anti-hallucination 4-layer AI prompt strategy
- SEO synonym rules for descriptions and tags
- Backfill all existing prompts + Cloudinary → B2 media migration

### Technical Patterns (Session 74)

**CSS `!important` cascade:**
- `masonry-grid.css` uses `!important` on many properties
- Overrides in page-specific CSS must also use `!important`
- NEVER use `!important` on properties JS controls inline (like `opacity`) — it blocks JS from toggling

**B2-aware thumbnails:**
- Always use `display_thumb_url` / `display_medium_url` properties (B2 → video thumb → Cloudinary fallback)
- NEVER use `get_thumbnail_url()` — it's Cloudinary-only and returns None for B2 prompts

**Video autoplay pattern:**
- IntersectionObserver with threshold `[0, 0.3, 0.5]`
- Skip on mobile (`window.innerWidth <= 768`) and `prefers-reduced-motion`
- CSS uses `data-initialized="true"` attribute + adjacent sibling selector to switch thumbnail from `position: relative` to `position: absolute`
- Disconnect observer before recreating (memory leak prevention)

**Cache-first categories:**
- AI writes all data (including categories) to cache at 90% progress
- `upload_views.py` checks cache before session — if cache has title, use ALL cache data
- Session fallback only when cache is truly empty

### Trash Prompts Architecture (Session 73)

The trash prompts grid uses a **self-contained card approach** with CSS columns instead of JavaScript masonry:

- **Why:** Homepage masonry JS isn't initialized on trash page, and `_prompt_card.html` video elements break in trash context
- **Solution:** Self-contained cards in `user_profile.html` (lines ~1267-1480) with `column-count` CSS layout
- **CSS:** Styles in `static/css/style.css` under "Trash video styling" section (~line 2555-2590)
- **Specificity Note:** `.trash-prompt-wrapper .trash-video-play` uses specificity 0,2,0 to beat `masonry-grid.css` `.video-play-icon` (0,1,0) which loads later

### Resolved Blockers (Session 64-66)

| Issue | Resolution | Session |
|-------|------------|---------|
| Change File button | Moved outside preview overlay, always visible | 66 |
| Privacy toggle | Redesigned as visibility toggle, defaults to Public | 66 |
| SEO score 72/100 | Comprehensive overhaul: JSON-LD, OG, Twitter, canonical, headings | 66 |
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
| `prompts/tasks.py` | AI prompt rewrite, `max_tokens` 500→1000, `rename_prompt_files_for_seo` task, domain allowlist, race/ethnicity (S64-S67) |
| `prompts/views/api_views.py` | AI job queuing for videos |
| `prompts/views/upload_views.py` | `.strip()` on excerpt assignment (S64) |
| `prompts_manager/settings.py` | Domain allowlist fix |
| `prompts/services/content_generation.py` | `max_tokens` 500→1000, filename 3→5 keywords, alt tag format, race/ethnicity, video description fix (S64) |
| `prompts/templates/prompts/collection_edit.html` | New template - collection edit form (S64) |
| `prompts/utils/__init__.py` | NEW - Utils package init (S67) |
| `prompts/utils/seo.py` | NEW - SEO filename generation utility (S67) |
| `prompts/services/b2_rename.py` | NEW - B2 file rename service (copy-verify-delete) (S67) |
| `prompts/templates/prompts/upload.html` | Heading hierarchy fixes, visual breadcrumbs, accessibility (S67) |
| `prompts/admin.py` | ID display, B2 Media URLs fieldset, expanded fieldsets (S68) |
| `prompts/views/prompt_views.py` | Query optimization: select_related, prefetch_related, materialized likes/comments (S68) |
| `prompts/models.py` | Composite indexes: (status,created_on), (author,status,deleted_at) (S68) |
| `prompts/templates/prompts/prompt_detail.html` | Template fragment caching, critical CSS, async loading, preconnect hints (S68) |
| `static/js/upload-core.js` | 30-second upload warning timer (S67-S68) |
| `static/js/upload-form.js` | Improved error message display, warning toast dismiss (S67-S68) |
| `static/css/upload.css` | Warning toast styles, error card styles, breadcrumb styles (S67-S68) |
| `static_root/robots.txt` | NEW - Search engine crawl directives served via WHITENOISE_ROOT (S69) |
| `prompts_manager/settings.py` | Added WHITENOISE_ROOT = BASE_DIR / 'static_root' (S69) |
| `templates/base.html` | Removed stale preconnects, reduced font weights (4→3), deferred icons.css with noscript (S69) |
| `prompts/templates/prompts/prompt_detail.html` | Fixed h3→h2 headings, aria-label mismatches with pluralize filter (S69) |
| `prompts/management/commands/minify_assets.py` | NEW - CSS/JS minification command targeting STATIC_ROOT (S69) |
| `requirements.txt` | Added csscompressor>=0.9.5, rjsmin>=1.2.0 (S69) |
| `prompts/utils/related.py` | NEW - Related prompts scoring algorithm (4-factor: tags, generator, engagement, recency) (S74) |
| `prompts/templates/prompts/partials/_prompt_card_list.html` | NEW - AJAX partial for related prompts Load More (S74) |
| `prompts/views/prompt_views.py` | Added related_prompts_ajax view, get_related_prompts import, context updates (S74) |
| `prompts/urls.py` | Added /prompt/<slug>/related/ AJAX endpoint (S74) |
| `prompts/templates/prompts/prompt_detail.html` | Added "You Might Also Like" section with masonry grid + Load More JS (S74) |
| `static/css/pages/prompt-detail.css` | Related prompts section styles (S74) |
| `prompts/templates/prompts/user_profile.html` | Trash page polish: tap-to-toggle, card-link, clock icon, bookmark removal, FOUC fix (S74) |
| `static/css/style.css` | --radius-pill variable, trash badge styles, FOUC fix (S74) |
| `static/icons/sprite.svg` | Added icon-clock for trash "deleted X days ago" (S74) |
| `docs/DESIGN_RELATED_PROMPTS.md` | NEW - Related Prompts Phase 1 & 2 design document (S74) |
| `prompts/models.py` | Added SubjectCategory model, Prompt.categories M2M (S74) |
| `prompts/admin.py` | Added SubjectCategoryAdmin with read-only enforcement (S74) |
| `prompts/tasks.py` | Added category assignment in AI prompt, writes to cache at 90% (S74) |
| `prompts/management/commands/backfill_categories.py` | NEW - Backfill categories for existing prompts (S74) |
| `prompts/migrations/0046_add_subject_categories.py` | NEW - SubjectCategory model + M2M (S74) |
| `prompts/migrations/0047_populate_subject_categories.py` | NEW - Seed 25 categories (S74) |
| `prompts/views/collection_views.py` | B2-aware thumbnail URLs replacing Cloudinary-only get_thumbnail_url() (S74) |
| `prompts/views/user_views.py` | B2-aware thumbnail URLs for trash collections (S74) |
| `prompts/templates/prompts/collection_detail.html` | Grid column fix, video autoplay observer, CSS overrides (S74) |
| `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md` | NEW - Phase 2B taxonomy revamp full design (S74) |
| `docs/PHASE_2B_AGENDA.md` | NEW - Phase 2B execution roadmap (S74) |

**Committed in Session 66** (commit `806dd5b`):
- `prompts/templates/prompts/prompt_detail.html` - Complete SEO overhaul (JSON-LD, OG, Twitter, canonical, headings, tag links, noindex)
- `prompts/templates/prompts/upload.html` - Two-column grid redesign
- `templates/base.html` - OG/Twitter blocks + dynamic copyright year
- `static/css/upload.css` - Complete rewrite with modern card design
- `static/css/style.css` - Media container component, border-radius variables
- `static/css/pages/prompt-detail.css` - Media container + SEO updates
- `static/js/upload-core.js` - File input reset fix
- `static/js/upload-form.js` - Visibility toggle, modal handlers

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
static/css/upload.css    # All upload page styles (~920 lines, rewritten S66, expanded S68)

BACKEND:
prompts/views/api_views.py           # API endpoints (1374+ lines)
prompts/services/b2_presign_service.py    # Generates presigned URLs for B2
prompts/services/b2_upload_service.py     # B2 upload utilities
prompts/services/b2_rename.py        # B2 file renaming (copy-verify-delete)
prompts/utils/seo.py                 # SEO filename generation
prompts/tasks.py                     # Background tasks (AI generation, SEO rename)
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
| `docs/DESIGN_RELATED_PROMPTS.md` | Related Prompts Phase 1 & 2 design |
| `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md` | Phase 2B category taxonomy revamp design |
| `docs/PHASE_2B_AGENDA.md` | Phase 2B execution roadmap (7 phases) |

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

**Version:** 4.6 (Session 74 - Related Prompts P1, Subject Categories P2, Collection Fixes, Video Autoplay)
**Last Updated:** February 9, 2026
