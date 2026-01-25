# PROJECT FILE STRUCTURE

**Last Updated:** January 22, 2026
**Project:** PromptFinder (Django 5.2.9)
**Current Phase:** Phase N Upload Flow Optimization (~95% complete)
**Total Tests:** 298 passing (48% coverage)

---

## Quick Statistics

| Category | Count | Location |
|----------|-------|----------|
| **Python Files** | 96 | Various directories |
| **HTML Templates** | 43 | templates/, prompts/templates/, about/templates/ |
| **CSS Files** | 6 | static/css/ |
| **JavaScript Files** | 8 | static/js/ |
| **SVG Icons** | 30 | static/icons/sprite.svg |
| **Migrations** | 41 | prompts/migrations/ (40), about/migrations/ (1) |
| **Test Files** | 13 | prompts/tests/ |
| **Management Commands** | 18 | prompts/management/commands/ |
| **Services** | 10 | prompts/services/ |
| **View Modules** | 11 | prompts/views/ |
| **CI/CD Config Files** | 3 | .github/workflows/, root |
| **Documentation (MD)** | 138 | Root (30), docs/ (33), archive/ (75) |

---

## Complete Directory Structure

```
live-working-project/
├── .claude/                      # Claude Code settings
├── .github/                      # GitHub configuration
│   ├── ISSUE_TEMPLATE/           # Issue templates
│   └── workflows/
│       └── django-ci.yml         # CI/CD pipeline (3 jobs)
├── .flake8                       # Flake8 linting configuration
├── .bandit                       # Bandit security scan configuration
├── about/                        # Secondary Django app (7 files)
│   ├── migrations/               # 1 migration
│   ├── templates/about/          # 1 template
│   │   └── about.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── archive/                      # Archived documentation (75+ files)
│   ├── bug-fixes/
│   ├── feature-implementations/
│   ├── marked-for-deletion/
│   ├── needs-review/
│   ├── phase-e/
│   └── rate-limiting/
├── backups/                      # Email preferences backups
├── design-references/            # UI design assets
│   └── UI_STYLE_GUIDE.md
├── docs/                         # Active documentation (33+ files)
│   ├── bug_reports/
│   ├── implementation_reports/
│   ├── reports/                  # Phase/feature reports (16 files)
│   ├── specifications/
│   └── CC_COMMUNICATION_PROTOCOL.md
├── prompts/                      # Main Django app (100+ files)
│   ├── management/
│   │   └── commands/             # 17 management commands + __init__.py
│   ├── migrations/               # 40 migrations + __init__.py
│   ├── services/                 # 9 service modules
│   ├── storage_backends.py       # B2 storage backend + CDN (Phase L)
│   ├── templates/prompts/        # 23 templates
│   │   └── partials/             # Partial templates
│   │       ├── _masonry_grid.html
│   │       ├── _prompt_card.html
│   │       └── _collection_modal.html  # Collections modal (Phase K)
│   ├── templatetags/             # 3 template tag files
│   ├── tests/                    # 13 test files
│   └── views/                    # 11 view modules (refactored)
│       ├── __init__.py           # Package exports
│       ├── admin_views.py        # Admin dashboard views
│       ├── api_views.py          # REST API endpoints (Phase L)
│       ├── collection_views.py   # Collection API and page views (Phase K)
│       ├── generator_views.py    # AI generator category pages
│       ├── leaderboard_views.py  # Leaderboard functionality
│       ├── prompt_views.py       # Prompt detail, edit, delete views
│       ├── redirect_views.py     # URL redirects and legacy routes
│       ├── social_views.py       # Follow, like, share views
│       ├── upload_views.py       # Upload workflow views
│       ├── user_views.py         # User profile and settings views
│       └── utility_views.py      # Utility and helper views
├── prompts_manager/              # Django project settings (7 files)
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reports/                      # Generated CSV reports
├── scripts/                      # Utility scripts (7 files)
├── static/                       # Source static files
│   ├── css/                      # 6 CSS files (~105KB total)
│   │   ├── components/
│   │   │   ├── icons.css         # SVG icon system styles
│   │   │   └── masonry-grid.css
│   │   ├── pages/
│   │   │   ├── prompt-detail.css # Prompt detail page styles (1,063 lines)
│   │   │   └── prompt-list.css
│   │   ├── navbar.css
│   │   └── style.css
│   ├── icons/                    # SVG icon sprite (Phase J.2)
│   │   └── sprite.svg            # 30 icons from Lucide Icons
│   └── js/                       # 4 JavaScript files
│       ├── collections.js        # Collections modal interactions (Phase K, ~760 lines)
│       ├── like-button.js        # Centralized like button handler
│       ├── navbar.js             # Extracted navbar JavaScript (~650 lines)
│       └── prompt-detail.js      # Prompt detail page interactions
├── staticfiles/                  # Collected static (production)
└── templates/                    # Global Django templates (18 files)
    ├── account/                  # 6 authentication templates
    ├── admin/                    # 8 admin customization templates
    ├── registration/             # 1 template
    ├── base.html                 # Main template (~1400 lines after JS extraction)
    ├── 404.html
    └── 429.html
```

---

## Management Commands (19 total)

| Command | Purpose | Schedule |
|---------|---------|----------|
| `cleanup_deleted_prompts` | Automated trash cleanup (5/30 day retention) | Daily 3:00 UTC |
| `detect_orphaned_files` | Cloudinary orphan + missing image detection | Daily 4:00 UTC |
| `backup_email_preferences` | Backup user email preferences to JSON | Manual |
| `restore_email_preferences` | Restore email preferences from backup | Manual |
| `auto_draft_no_media` | Move prompts without media to draft | Manual |
| `cleanup_old_tags` | Remove unused tags from database | Manual |
| `create_bulk_data` | Generate test data for development | Manual |
| `create_test_users` | Create test user accounts | Manual |
| `diagnose_media` | Diagnose media file issues | Manual |
| `fix_admin_avatar` | Fix admin user avatar issues | Manual |
| `fix_cloudinary_urls` | Repair Cloudinary URL issues | Manual |
| `fix_ghost_prompts` | Remove ghost/orphan prompt records | Manual |
| `fix_prompt_order` | Repair prompt ordering | Manual |
| `generate_slugs` | Generate missing slugs for prompts | Manual |
| `initialize_prompt_order` | Initialize prompt ordering | Manual |
| `moderate_prompts` | Run moderation on prompts | Manual |
| `test_moderation` | Test moderation service | Manual |
| `test_api_latency` | Test B2 and OpenAI API response times | Manual |
| `regenerate_video_thumbnails` | Regenerate Cloudinary video thumbnails with correct aspect ratio | Manual |

---

## Service Layer Architecture (10 modules)

```
prompts/services/
├── __init__.py              # Service exports
├── b2_presign_service.py    # B2 presigned URL generation (Phase L8-DIRECT) ← NEW
├── b2_upload_service.py     # B2 upload orchestration (Phase L)
├── cloudinary_moderation.py # OpenAI Vision moderation for images and videos
├── content_generation.py    # GPT-4o content generation for uploads
├── image_processor.py       # Pillow image optimization (Phase L)
├── leaderboard.py           # Leaderboard calculations (Phase G)
├── openai_moderation.py     # OpenAI text moderation API
├── orchestrator.py          # Moderation orchestration (multi-layer)
├── profanity_filter.py      # Profanity detection and filtering
└── video_processor.py       # FFmpeg video processing, frame extraction for moderation (Phase M)

prompts/storage_backends.py  # B2 storage backend + CDN URLs (Phase L, at app root)
```

### Service Descriptions

| Service | Description | Cost |
|---------|-------------|------|
| **b2_presign_service** | Generates presigned URLs for direct browser-to-B2 uploads (L8-DIRECT) | N/A |
| **b2_upload_service** | Orchestrates B2 uploads with optimization | ~$0.005/GB |
| **cloudinary_moderation** | Cloudinary AI Vision for image/video moderation | ~$5-10/1000 images |
| **content_generation** | GPT-4o-mini for AI-generated titles, descriptions, tags | ~$0.00255/upload |
| **image_processor** | Pillow-based image optimization (thumb, medium, large, webp) | N/A |
| **leaderboard** | User ranking by views, activity, engagement | N/A |
| **openai_moderation** | OpenAI text moderation API | FREE |
| **orchestrator** | Multi-layer moderation coordination | Combined |
| **profanity_filter** | Custom profanity word detection | N/A |
| **video_processor** | FFmpeg-based video processing and thumbnail extraction (Phase L6) | N/A |
| **storage_backends** | B2StorageBackend + Cloudflare CDN URL generation (prompts/) | ~$0.005/GB |

---

## Views Package Architecture (11 modules)

*Refactored December 2025 - Previously a single 3,929-line views.py file*

```
prompts/views/
├── __init__.py           # Package exports (all public views)
├── admin_views.py        # Admin dashboard, debug pages, bulk actions
├── api_views.py          # REST API endpoints (B2 upload - Phase L)
├── collection_views.py   # Collection API and page views (Phase K)
├── generator_views.py    # AI generator category pages
├── leaderboard_views.py  # Leaderboard rankings, filters
├── prompt_views.py       # Prompt detail, edit, delete, list views
├── redirect_views.py     # URL redirects and legacy routes
├── social_views.py       # Follow/unfollow, likes, shares
├── upload_views.py       # Two-step upload, AI generation, validation
├── user_views.py         # User profiles, settings, avatar
└── utility_views.py      # Utility and helper views
```

### Module Descriptions

| Module | Functions | Purpose |
|--------|-----------|---------|
| **admin_views** | ~17 | Admin dashboards, media issues, trash management, SEO review queue |
| **api_views** | ~5 | REST API endpoints for B2 upload + presigned URLs (Phase L, L8-DIRECT) |
| **collection_views** | ~9 | Collection CRUD, API endpoints, profile tab, pagination |
| **generator_views** | ~5 | AI generator category pages with filtering |
| **leaderboard_views** | ~4 | Rankings, time filters, user stats |
| **prompt_views** | ~20 | Prompt detail, edit, delete, list, homepage views |
| **redirect_views** | ~3 | URL redirects, legacy route handling |
| **social_views** | ~10 | Follow system, likes, shares, reports |
| **upload_views** | ~12 | Step 1/2 upload, AI generation, validation |
| **user_views** | ~12 | User profiles, settings, email preferences |
| **utility_views** | ~8 | Utility and helper views |

---

## Templates (42 total)

### Global Templates (templates/) - 18 files

| Template | Purpose |
|----------|---------|
| `base.html` | Main template with navbar, footer (~2000 lines) |
| `404.html` | Not found error page |
| `429.html` | Rate limit error page (WCAG AA) |
| `account/*.html` | 6 authentication templates (login, signup, logout, password reset) |
| `admin/*.html` | 9 admin customization templates (incl. `seo_review_queue.html`) |
| `registration/login.html` | Login page override |

### Prompts App Templates (prompts/templates/prompts/) - 23 files

| Template | Purpose |
|----------|---------|
| `prompt_list.html` | Homepage with masonry grid (70KB) |
| `prompt_detail.html` | Single prompt view page |
| `prompt_edit.html` | Edit prompt form |
| `ai_generator_category.html` | AI generator landing pages |
| `inspiration_index.html` | Prompts hub / browse page |
| `user_profile.html` | User profile with tabs |
| `upload_step1.html` | Step 1: Drag-and-drop upload |
| `upload_step2.html` | Step 2: AI-generated details form |
| `trash_bin.html` | User trash bin |
| `settings_notifications.html` | Email preferences dashboard |
| `unsubscribe.html` | Unsubscribe confirmation |
| `leaderboard.html` | Community leaderboard (Phase G) |
| `partials/_masonry_grid.html` | Reusable masonry grid partial |
| `partials/_prompt_card.html` | Reusable prompt card partial |
| `partials/_collection_modal.html` | Collections modal (Phase K) |
| `collections_profile.html` | User collections tab page (Phase K) |
| And 8 more... | Confirmation modals, reports, etc. |

### About App Templates (about/templates/about/) - 1 file

| Template | Purpose |
|----------|---------|
| `about.html` | About page |

---

## Test Files (13 files, 298 tests)

| Test File | Tests | Focus Area |
|-----------|-------|------------|
| `test_b2_presign.py` | 22 | B2 presigned URL generation (Phase L8-DIRECT) ← NEW |
| `test_user_profiles.py` | Multiple | User profile CRUD operations |
| `test_rate_limiting.py` | 23 | Rate limiting enforcement |
| `test_generator_page.py` | 24 | AI generator category pages |
| `test_url_migration.py` | 12 | Phase I URL redirects |
| `test_prompts_hub.py` | Multiple | Prompts hub functionality |
| `test_inspiration.py` | 14 | Inspiration page tests |
| `test_follows.py` | Multiple | Follow system |
| `test_email_preferences_safety.py` | Multiple | Email preference safety |
| `test_user_profile_header.py` | Multiple | Profile header UI |
| `test_user_profile_javascript.py` | Multiple | Profile JavaScript |
| `test_models.py` | Multiple | Model tests |
| `test_views.py` | Multiple | View tests |

**Note:** 12 Selenium tests skipped in CI (require browser)

---

## Core Python Files

### Project Configuration (prompts_manager/)

| File | Purpose |
|------|---------|
| `settings.py` | Django settings (database, Cloudinary, middleware) |
| `urls.py` | Root URL configuration |
| `wsgi.py` | WSGI application entry point |
| `asgi.py` | ASGI application entry point |

### Main Application (prompts/)

| File | Lines | Purpose |
|------|-------|---------|
| `views/` | ~3,929 | View package (11 modules) ✅ REFACTORED |
| `models.py` | ~2,026 | Database models (Prompt, UserProfile, etc.) |
| `admin.py` | ~500 | Django admin configuration |
| `forms.py` | ~300 | Django forms |
| `urls.py` | ~200 | URL routing |
| `signals.py` | ~100 | Django signals (auto-create profiles) |
| `middleware.py` | ~67 | RatelimitMiddleware |
| `constants.py` | ~241 | AI generator metadata, OPENAI_TIMEOUT |
| `email_utils.py` | ~100 | Email helper functions |

---

## CSS Architecture

```
static/css/
├── navbar.css           # 1,136 lines - Extracted navbar styles
├── style.css            # 1,789 lines - Main stylesheet
├── upload.css           # ~500 lines - Upload page styles (Phase N3)
├── components/
│   ├── icons.css        # ~250 lines - SVG icon system (Phase J.2)
│   └── masonry-grid.css # 255 lines - Masonry grid component
└── pages/
    ├── prompt-detail.css # 1,063 lines - Prompt detail page (Phase J.1)
    └── prompt-list.css   # 304 lines - Prompt list page styles
```

**Total CSS:** ~5,297 lines across 7 files

---

## CI/CD Configuration

### GitHub Actions Pipeline (`.github/workflows/django-ci.yml`)

**Triggers:** Push to main/develop, Pull requests to main

| Job | Purpose | Timeout |
|-----|---------|---------|
| **test** | Django tests with PostgreSQL, coverage ≥45% | 15 min |
| **lint** | Flake8 code quality checks | 5 min |
| **security** | Bandit SAST + pip-audit dependency scan | 10 min |

### Configuration Files

| File | Purpose | Key Settings |
|------|---------|--------------|
| `.flake8` | Linting rules | max-line-length=120, exclude migrations |
| `.bandit` | Security scan | Skip B101 (assert), target prompts/ |
| `django-ci.yml` | Pipeline definition | Python 3.12, PostgreSQL 14 |

### Pipeline Features

- **Parallel Execution:** All 3 jobs run simultaneously
- **PostgreSQL Service:** Containerized test database
- **Coverage Artifacts:** Reports uploaded for 5 days
- **Fail-Fast:** Security issues block deployment

---

## JavaScript Architecture

```
static/js/
├── collections.js        # ~760 lines - Collections modal (Phase K)
├── like-button.js        # ~155 lines - Centralized like handler (Phase J.2)
├── navbar.js             # ~650 lines - Extracted from base.html
├── prompt-detail.js      # ~400 lines - Prompt detail interactions (Phase J.1)
├── upload-core.js        # ~488 lines - File selection, B2 upload, preview (Phase N)
├── upload-form.js        # ~624 lines - Form handling, NSFW status (Phase N)
├── upload-guards.js      # ~410 lines - Navigation guards, idle detection (Phase N)
└── upload-step1.js       # ~768 lines - Legacy Step 1 upload (deprecated)
```

### JavaScript Files

| File | Lines | Purpose |
|------|-------|---------|
| **collections.js** | ~760 | Collections modal, API integration, thumbnail grids |
| **navbar.js** | ~650 | Dropdowns, search, mobile menu, scroll |
| **prompt-detail.js** | ~400 | Like toggle, copy button, comments, delete modal |
| **like-button.js** | ~155 | Centralized like handler with optimistic UI |
| **upload-core.js** | ~488 | B2 presigned upload, drag-drop, local preview, orphan cleanup (Phase N) |
| **upload-form.js** | ~624 | Form validation, NSFW status display, submit handling (Phase N) |
| **upload-guards.js** | ~410 | Navigation guards, idle timeout, cleanup beacon (Phase N) |
| **upload-step1.js** | ~768 | Legacy Step 1 upload page (deprecated, kept for reference) |

### navbar.js Features

| Feature | Lines | Purpose |
|---------|-------|---------|
| Dropdown Management | ~150 | Open/close, click outside |
| Search Functionality | ~200 | Autocomplete, keyboard nav |
| Mobile Menu | ~100 | Hamburger toggle, responsive |
| Scroll Behavior | ~80 | Sticky navbar, scroll effects |
| Event Delegation | ~70 | Performance optimization |
| Utilities | ~50 | Debounce, focus trap |

### collections.js Features (Phase K)

| Feature | Lines | Purpose |
|---------|-------|---------|
| Modal State Management | ~100 | Open, close, escape key, body scroll lock |
| Collection Grid Rendering | ~200 | Dynamic thumbnail grids (1, 2, 3+ items) |
| API Integration | ~150 | Fetch collections, create, add/remove prompts |
| Create Panel | ~100 | Create collection form, validation |
| Visibility Toggle | ~50 | Public/private icons and hints |
| State Reset | ~60 | Reset modal state on close |
| Error Handling | ~100 | Loading states, error messages |

**Total JavaScript:** ~4,255 lines across 8 files
**Extraction Benefit:** base.html reduced from ~2000 lines to ~1400 lines

---

## SVG Icon System (Phase J.2)

PromptFinder uses a custom SVG sprite system for icons, replacing Font Awesome for improved performance and consistency.

### Files

| File | Location | Purpose |
|------|----------|---------|
| `sprite.svg` | static/icons/ | SVG sprite with 30 icon definitions |
| `icons.css` | static/css/components/ | Icon utility classes |

### Available Icons (30 total)

**Phase 1 Icons (Navigation) - 5 icons:**
- `icon-image` - Photos filter indicator
- `icon-video` - Videos filter indicator
- `icon-search` - Search dropdown icon
- `icon-trophy` - Leaderboard dropdown icon
- `icon-lightbulb` - Prompts dropdown icon

**Phase 2 Icons (Actions) - 11 icons:**
- `icon-comment` - Comment indicator
- `icon-heart` - Heart outline (unliked state)
- `icon-heart-filled` - Solid pink heart (liked state)
- `icon-flag` - Report prompt
- `icon-edit` - Edit prompt
- `icon-trash` - Delete prompt
- `icon-external-link` - External links
- `icon-calendar` - Date indicators
- `icon-copy` - Copy to clipboard
- `icon-login` - Sign in/out
- `icon-bell` - Notifications

**Phase 3 Icons (Profile) - 3 icons:**
- `icon-user` - User profile
- `icon-user-pen` - Edit profile
- `icon-mail` - Email/contact

**Phase K Icons (Collections) - 11 icons:**
- `icon-bookmark` - Save button (outline)
- `icon-bookmark-filled` - Saved state (pink fill)
- `icon-circle-check` - Already in collection
- `icon-circle-minus` - Remove from collection
- `icon-eye` - Public collection
- `icon-eye-off` - Private collection
- `icon-x` - Soft close button
- `icon-arrow-left` - Back navigation
- `icon-arrow-right` - Forward navigation
- `icon-download` - Download button
- `icon-share` - Share/copy link

### Usage Pattern

```html
<svg class="icon icon-sm">
  <use href="{% static 'icons/sprite.svg' %}#icon-name"/>
</svg>
```

### Size Classes

| Class | Size | Use Case |
|-------|------|----------|
| `.icon-xs` | 12px (0.75rem) | Inline text |
| `.icon-sm` | 22px (1.4rem) | Navigation (default) |
| `.icon-md` | 24px (1.5rem) | Action buttons |
| `.icon-lg` | 24px (1.5rem) | Larger contexts |

### Icon Source

All icons from [Lucide Icons](https://lucide.dev) - MIT License

---

## Collections CSS Variables (Phase K)

CSS custom properties for the Collections feature, defined in `static/css/style.css`:

### Modal Layout Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-modal-bg` | `#fff` | Modal background |
| `--collection-modal-padding` | `24px` | Modal inner padding |
| `--collection-modal-radius` | `16px` | Modal border radius |
| `--collection-modal-shadow` | `0 25px 50px -12px rgba(0,0,0,0.25)` | Modal drop shadow |

### Grid & Card Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-grid-gap` | `16px` | Gap between collection cards |
| `--collection-card-radius` | `12px` | Card border radius |
| `--collection-thumbnail-height` | `120px` | Thumbnail container height |
| `--collection-overlay-bg` | `rgba(0,0,0,0.5)` | Thumbnail overlay background |

### State & Interaction Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-accent` | `var(--brand-primary, #28a745)` | Primary accent color |
| `--collection-saved-color` | `#28a745` | Saved/added state (green) |
| `--collection-remove-color` | `#dc3545` | Remove hover state (red) |
| `--collection-transition` | `0.15s ease` | Standard transition timing |

### Form Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-input-border` | `#dee2e6` | Input border color |
| `--collection-input-focus` | `var(--brand-primary)` | Input focus border |
| `--collection-label-color` | `#6c757d` | Form label color |
| `--collection-hint-color` | `#6c757d` | Helper text color |

### Validation State Variables (Session 28)

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-error-color` | `#dc3545` | Error state border/text (blocking) |
| `--collection-warning-color` | `#ffc107` | Warning state border (confirmable) |
| `--collection-warning-bg` | `#fff3cd` | Warning background tint |
| `--collection-success-color` | `#28a745` | Success state (auto-clear) |

### Animation Variables (Session 28)

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-card-animation-duration` | `150ms` | Card fade-in duration |
| `--collection-card-animation-delay` | `50ms` | Staggered delay per card |
| `--collection-input-shake-duration` | `400ms` | Input shake animation duration |
| `--collection-thumbnail-size` | `120px` | Thumbnail container height |

### Keyframe Animations

```css
/* Card Entrance Animation */
@keyframes collectionCardFadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Input Validation Shake */
@keyframes inputShake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-10px); }
    40%, 80% { transform: translateX(10px); }
}
```

**Usage Pattern (Staggered Cards):**
```css
.collection-card {
    animation: collectionCardFadeIn var(--collection-card-animation-duration) ease-out forwards;
    animation-delay: calc(var(--card-index, 0) * var(--collection-card-animation-delay));
}
```

---

## Collections API Endpoints (Phase K)

API endpoints for the Collections feature, defined in `prompts/views/collection_views.py`:

### Public Endpoints (Authentication Required)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /api/collections/` | GET | List user's collections with item counts |
| `GET /api/collections/?prompt_id=123` | GET | List collections with membership status for prompt |
| `POST /api/collections/create/` | POST | Create a new collection |
| `POST /api/collections/<id>/add/` | POST | Add prompt to collection |
| `POST /api/collections/<id>/remove/` | POST | Remove prompt from collection |

### Page Views

| URL | View | Purpose |
|-----|------|---------|
| `/collections/` | `collections_list` | User's collections index |
| `/collections/<slug>/` | `collection_detail` | View collection contents |
| `/collections/<slug>/edit/` | `collection_edit` | Edit collection settings |
| `/collections/<slug>/delete/` | `collection_delete` | Delete collection (soft delete) |

### API Response Format

```json
// GET /api/collections/?prompt_id=123
{
  "success": true,
  "collections": [
    {
      "id": 1,
      "title": "My Favorites",
      "slug": "my-favorites-x7k2m",
      "is_private": false,
      "item_count": 15,
      "thumbnails": ["url1", "url2", "url3"],
      "has_prompt": true
    }
  ],
  "count": 1
}
```

---

## B2 Upload API Endpoints (Phase L)

API endpoints for B2 image upload and processing, defined in `prompts/views/api_views.py`:

### Upload Endpoints (Authentication Required)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `POST /api/upload/b2/` | POST | Upload image to B2 with all variants (standard mode) |
| `POST /api/upload/b2/?quick=true` | POST | Upload image with thumbnail only (quick mode) |
| `POST /api/upload/b2/variants/` | POST | Generate medium, large, WebP variants (background) |
| `GET /api/upload/b2/variants/status/` | GET | Poll for variant generation completion |
| `POST /api/upload/b2/moderate/` | POST | NSFW moderation check for uploaded images |
| `DELETE /api/upload/b2/delete/` | DELETE | Delete B2 object if moderation fails |

### Quick Mode Session Keys

| Key | Type | Purpose |
|-----|------|---------|
| `pending_variant_image` | string (base64) | Stored image for deferred variant generation |
| `pending_variant_filename` | string | Original filename |
| `variant_urls` | dict | Generated variant URLs (medium, large, webp) |
| `variants_complete` | boolean | Flag for polling completion |

### API Response Format (Quick Mode)

```json
// POST /api/upload/b2/?quick=true
{
  "success": true,
  "urls": {
    "original": "https://cdn.example.com/images/abc123.jpg",
    "thumb": "https://cdn.example.com/images/abc123_thumb.jpg"
  },
  "quick_mode": true,
  "variants_pending": true
}

// GET /api/upload/b2/variants/status/
{
  "complete": true,
  "urls": {
    "medium": "https://cdn.example.com/images/abc123_medium.jpg",
    "large": "https://cdn.example.com/images/abc123_large.jpg",
    "webp": "https://cdn.example.com/images/abc123.webp"
  }
}
```

---

## Upload Flow & Session Dependencies (Phase L - January 2026)

The multi-step upload flow uses Django session storage to pass data between endpoints. Understanding session key dependencies is critical for debugging upload issues.

### Complete Session Key Reference

| Key | Type | Set By | Used By | Purpose |
|-----|------|--------|---------|---------|
| `b2_pending_upload` | dict | `b2_presign_upload` | `b2_upload_complete` | Pending upload metadata (file_key, filename, content_type) |
| `b2_secure_url` | string | `b2_upload_complete` | `upload_step2`, `ai_suggestions`, `prompt_edit` | CDN URL for uploaded image |
| `b2_thumb_url` | string | `b2_upload_complete` | `upload_submit`, `prompt_edit` | Thumbnail URL (300x300) |
| `b2_medium_url` | string | `b2_generate_variants` | `upload_submit`, `prompt_edit` | Medium URL (600x600) |
| `b2_large_url` | string | `b2_generate_variants` | `upload_submit`, `prompt_edit` | Large URL (1200x1200) |
| `b2_webp_url` | string | `b2_generate_variants` | `upload_submit`, `prompt_edit` | WebP optimized URL |
| `pending_variant_url` | string | `b2_upload_complete` | `b2_generate_variants` | CDN URL for deferred variant generation (preferred) |
| `pending_variant_filename` | string | `b2_upload_complete` | `b2_generate_variants` | Original filename for variants |
| `pending_variant_image` | string (base64) | Legacy fallback | `b2_generate_variants` | Base64 image data (deprecated, Session 39) |
| `variant_urls` | dict | `b2_generate_variants` | `variants_status` | Generated variant URLs |
| `variants_complete` | boolean | `b2_generate_variants` | `variants_status`, `upload_step2` | Flag for polling completion |
| `cloudinary_id` | string | Legacy upload | `upload_submit` | Cloudinary public ID (fallback) |
| `cloudinary_secure_url` | string | Legacy upload | `ai_suggestions`, `upload_submit` | Cloudinary URL (fallback) |
| `is_video` | boolean | Upload detection | `upload_submit` | Media type flag |
| `b2_video_url` | string | `b2_upload_complete` (video) | `upload_submit` | B2 video CDN URL |
| `b2_video_thumb_url` | string | `b2_upload_complete` (video) | `upload_submit`, `upload_step2` | Video thumbnail URL |
| `direct_upload_is_video` | boolean | `b2_upload_complete` | `upload_step2`, `upload_submit` | Video detection flag for direct B2 uploads |

### Upload Flow Sequence

#### Image Upload Flow
```
1. GET /api/upload/b2/presign/
   └─ Sets: b2_pending_upload (file_key, filename, content_type)

2. Browser uploads directly to B2 via presigned URL

3. POST /api/upload/b2/complete/
   └─ Reads: b2_pending_upload
   └─ Sets: b2_secure_url, b2_thumb_url, pending_variant_url, pending_variant_filename

4. POST /api/upload/b2/variants/ (background)
   └─ Reads: pending_variant_url, pending_variant_filename
   └─ Sets: b2_medium_url, b2_large_url, b2_webp_url, variant_urls, variants_complete

5. GET /upload/details/ (Step 2 page)
   └─ Reads: b2_secure_url, b2_thumb_url, variants_complete

6. GET /api/upload/ai-suggestions/
   └─ Reads: b2_secure_url OR cloudinary_secure_url
   └─ Note: AI suggestions require b2_thumb_url for image analysis

7. POST /upload/submit/
   └─ Reads: All b2_* keys, cloudinary_* keys
   └─ Clears: All upload session keys via clear_upload_session()
```

#### Video Upload Flow
```
1. GET /api/upload/b2/presign/
   └─ Sets: b2_pending_upload (file_key, filename, content_type='video/*')

2. Browser uploads directly to B2 via presigned URL

3. POST /api/upload/b2/complete/
   └─ Reads: b2_pending_upload
   └─ Sets: b2_video_url, b2_video_thumb_url, direct_upload_is_video=True
   └─ Note: No variant generation for videos (stored as-is)

4. GET /upload/details/ (Step 2 page)
   └─ Reads: b2_video_url, b2_video_thumb_url, direct_upload_is_video

5. GET /api/upload/ai-suggestions/
   └─ Reads: b2_video_thumb_url (thumbnail used for AI analysis)
   └─ Fallback: Uses first frame extraction if no thumbnail

6. POST /upload/submit/
   └─ Reads: b2_video_url, b2_video_thumb_url, direct_upload_is_video
   └─ Saves: prompt.b2_video_url, prompt.b2_video_thumb_url
   └─ Clears: All upload session keys via clear_upload_session()
```

### Session Clearing Helper

**Location:** `prompts/views/upload_views.py`

```python
def clear_upload_session(request):
    """Clear all upload-related session keys to prevent data bleed."""
    keys_to_clear = [
        'b2_secure_url', 'b2_thumb_url', 'b2_medium_url', 'b2_large_url', 'b2_webp_url',
        'b2_pending_upload', 'pending_variant_image', 'pending_variant_filename',
        'variant_urls', 'variants_complete', 'cloudinary_id', 'cloudinary_secure_url', 'is_video'
    ]
    for key in keys_to_clear:
        request.session.pop(key, None)
```

### Variant Race Condition (Session 38-39)

**Status:** ✅ RESOLVED (January 8, 2026)

**Problem:** `/api/upload/b2/variants/` returned 400 Bad Request with "No pending upload found in session"

**Root Cause:** Session data unreliable for passing large image data between endpoints.

**Solution (Session 39):**
1. Replaced base64 session storage with URL-based session storage (`pending_variant_url`)
2. Added base64 encoding for OpenAI Vision API (CDN URLs were failing fetch)
3. Used hidden form fields to pass variant URLs through POST submission
4. Deprecated `pending_variant_image` in favor of `pending_variant_url` (legacy fallback retained)

---

## SEO Review Admin Routes (Phase L10c)

Admin routes for the SEO Review Queue feature, defined in `prompts/views/admin_views.py`:

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/seo-review/` | GET | Admin SEO Review Queue page |
| `/admin/seo-complete/<id>/` | POST | Mark prompt as SEO reviewed |

### Database Field

**Model:** `Prompt` (in `prompts/models.py`)

| Field | Type | Purpose |
|-------|------|---------|
| `needs_seo_review` | BooleanField | Flag for prompts that failed AI content generation |

### Template

| Template | Location | Purpose |
|----------|----------|---------|
| `seo_review_queue.html` | `prompts/templates/admin/` | Admin queue with title/description edit forms |

---

## Recent Additions (Phase I - December 2025)

### URL Migration Complete

- `/ai/` URLs redirected to `/prompts/` with 301 status
- `/inspiration/` URLs redirected to `/prompts/` with 301 status
- All 70 tests passing
- SEO preserved with permanent redirects

### Files Modified in Phase I

| File | Changes |
|------|---------|
| `prompts/urls.py` | New `/prompts/` namespace + legacy redirects |
| `prompts/views.py` | Added PromptView import |
| `templates/base.html` | Updated navigation links |
| `ai_generator_category.html` | Updated breadcrumbs, Schema.org |
| `inspiration_index.html` | Updated breadcrumbs, H1 |
| `prompt_list.html` | Updated platform dropdown link |
| `test_prompts_hub.py` | NEW - 24 tests |
| `test_url_migration.py` | Rewritten - 12 tests |
| `test_inspiration.py` | Rewritten - 14 tests |
| `test_generator_page.py` | Updated - 24 tests |

---

## Known Critical Issues

### Immediate Attention Required

| Issue | Impact | Status |
|-------|--------|--------|
| `views.py` at 147KB (~3,929 lines) | Maintenance difficulty | ✅ RESOLVED - Split into 11 modules |
| No CI/CD pipeline | Manual deployments | ✅ RESOLVED - GitHub Actions operational |
| No error monitoring | Blind to production errors | ✅ RESOLVED - Sentry integrated |
| 37 migrations | Slow migration runs | ⏳ Squash before launch |
| Root directory clutter | 30+ MD files, 14 Python scripts | ⏳ Move to /archive/ and /scripts/ |

---

## Deployment Structure

### Heroku Configuration

| Component | Configuration |
|-----------|---------------|
| **Dyno** | Eco dyno ($5/month) |
| **Database** | Heroku PostgreSQL Mini ($5/month) |
| **Scheduler** | Heroku Scheduler (free) |
| **Total Cost** | ~$10/month (covered by credits) |

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection
- `CLOUDINARY_URL` - Media storage
- `SECRET_KEY` - Django secret
- `ADMIN_EMAIL` - Notification recipient
- `DEBUG` - False in production
- `IP_HASH_PEPPER` - View tracking security (recommended)
- `SENTRY_DSN` - Error monitoring endpoint
- `DJANGO_ENV` - Environment identifier (production/staging)

### Scheduled Jobs

| Job | Schedule | Runtime |
|-----|----------|---------|
| `cleanup_deleted_prompts` | Daily 3:00 UTC | ~10-30 seconds |
| `detect_orphaned_files --days 7` | Daily 4:00 UTC | ~10-60 seconds |

---

## Testing Overview

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test prompts

# Run specific test file
python manage.py test prompts.tests.test_rate_limiting

# Run with verbosity
python manage.py test -v 2
```

### Test Statistics

- **Total Tests:** 234 passing (12 skipped - Selenium)
- **Pass Rate:** 100% in CI
- **Coverage:** 46% (enforced minimum: 45%)
- **Priority Areas:** CRUD, authentication, rate limiting, URL migration
- **CI Integration:** Tests run on every push/PR via GitHub Actions

---

## Related Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| CLAUDE.md | Root | Master project documentation |
| CC_COMMUNICATION_PROTOCOL.md | docs/ | Agent usage requirements |
| UI_STYLE_GUIDE.md | design-references/ | UI/UX standards |
| PROJECT_FILE_STRUCTURE_AUDIT_REPORT.md | docs/reports/ | Latest audit findings |
| L8_TIMEOUT_COMPLETION_REPORT.md | docs/reports/ | L8-TIMEOUT implementation details |

---

**END OF PROJECT_FILE_STRUCTURE.md**

*This document is updated after major structural changes. Last audit: January 9, 2026.*

**Version:** 2.8
**Audit Date:** January 22, 2026
**Maintained By:** Mateo Johnson - Prompt Finder

### Changelog

**v2.8 (January 22, 2026):**
- Added Phase N upload JavaScript files to documentation
- upload-core.js, upload-form.js, upload-guards.js, upload-step1.js
- Updated JavaScript file count (4 → 8)
- Updated total JavaScript lines (~1,965 → ~4,255)

**v2.7 (January 14, 2026):**
- Phase M Video Moderation complete
- Updated cloudinary_moderation.py description (OpenAI Vision)
- Updated video_processor.py description (frame extraction)
- Added UPLOAD_ISSUE_DIAGNOSTIC_REPORT.md to docs/reports/

**v2.6 (January 9, 2026):**
- Added SEO Review Admin Routes section (Phase L10c)
- Added `seo_review_queue.html` to admin templates (8 → 9)
- Updated admin_views.py function count (~15 → ~17)
- Documented `needs_seo_review` model field
- Updated version and audit date
