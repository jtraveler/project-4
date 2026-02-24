# PROJECT FILE STRUCTURE

**Last Updated:** February 18, 2026
**Project:** PromptFinder (Django 5.2.9)
**Current Phase:** Phase R1 + R1-D (complete), Phase 2B (complete), Phase N4 (~99%), Phase K (~96%)
**Total Tests:** ~657 passing (43% coverage, threshold 40%)

---

## Quick Statistics

| Category | Count | Location |
|----------|-------|----------|
| **Python Files** | 96 | Various directories |
| **HTML Templates** | 43 | templates/, prompts/templates/, about/templates/ |
| **CSS Files** | 9 | static/css/ |
| **JavaScript Files** | 9 | static/js/ (2 deleted in Session 61, 2 added in Session 86) |
| **SVG Icons** | 33 | static/icons/sprite.svg |
| **Migrations** | 58 | prompts/migrations/ (56), about/migrations/ (2) |
| **Test Files** | 19 | prompts/tests/ |
| **Management Commands** | 28 | prompts/management/commands/ |
| **Services** | 12 | prompts/services/ |
| **View Modules** | 12 | prompts/views/ |
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
│   ├── migrations/               # 2 migrations
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
│   ├── reports/                  # Phase/feature reports (21 files)
│   ├── specifications/
│   ├── CC_COMMUNICATION_PROTOCOL.md
│   ├── DESIGN_RELATED_PROMPTS.md           # Related prompts system reference (Phase 2B-9 complete)
│   ├── DESIGN_CATEGORY_TAXONOMY_REVAMP.md  # Phase 2B taxonomy revamp (Session 74)
│   ├── PHASE_2B_AGENDA.md                  # Phase 2B execution roadmap (Session 74)
│   └── PHASE_2B1-6_COMPLETION_REPORT.md    # 6 Phase 2B sub-phase completion reports (Phase 2B Session)
├── prompts/                      # Main Django app (100+ files)
│   ├── management/
│   │   └── commands/             # 28 management commands + __init__.py
│   ├── migrations/               # 54 migrations + __init__.py
│   ├── services/                 # 12 service modules
│   │   └── notifications.py      # Notification service (create, count, mark-read) (Session 86)
│   ├── signals/                   # Signal handlers (Session 86)
│   │   ├── __init__.py
│   │   └── notification_signals.py  # Notification signal handlers
│   ├── utils/                    # Utility modules (SEO filenames, related prompts scoring)
│   ├── storage_backends.py       # B2 storage backend + CDN (Phase L)
│   ├── templates/prompts/        # 23 templates
│   │   └── partials/             # Partial templates
│   │       ├── _masonry_grid.html
│   │       ├── _prompt_card.html
│   │       ├── _prompt_card_list.html   # Related prompts AJAX partial (Session 74)
│   │       ├── _notification_list.html  # Notification list AJAX partial (Session 86)
│   │       └── _collection_modal.html  # Collections modal (Phase K)
│   ├── templatetags/             # 3 template tag files
│   ├── tests/                    # 19 test files
│   └── views/                    # 12 view modules (refactored)
│       ├── __init__.py           # Package exports
│       ├── admin_views.py        # Admin dashboard views
│       ├── api_views.py          # REST API endpoints (Phase L)
│       ├── collection_views.py   # Collection API and page views (Phase K)
│       ├── generator_views.py    # AI generator category pages
│       ├── leaderboard_views.py  # Leaderboard functionality
│       ├── notification_views.py # Notification API + page views (Phase R1)
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
├── static_root/                  # Root-level files served by WhiteNoise (no hashing)
│   └── robots.txt                # Search engine crawl directives (Session 69)
├── static/                       # Source static files
│   ├── css/                      # 9 CSS files (~105KB total)
│   │   ├── components/
│   │   │   ├── icons.css         # SVG icon system styles
│   │   │   ├── masonry-grid.css
│   │   │   └── profile-tabs.css  # Shared tab component CSS (Session 86)
│   │   ├── pages/
│   │   │   ├── notifications.css # Notifications page styles (Session 86, ~350 lines)
│   │   │   ├── prompt-detail.css # Prompt detail page styles (1,515 lines, includes related prompts section)
│   │   │   └── prompt-list.css
│   │   ├── navbar.css
│   │   ├── upload.css            # Upload page styles (~920 lines, rewritten Session 66)
│   │   └── style.css
│   ├── icons/                    # SVG icon sprite (Phase J.2)
│   │   └── sprite.svg            # 33 icons from Lucide Icons
│   └── js/                       # 9 JavaScript files
│       ├── collections.js        # Collections modal interactions (Phase K, ~760 lines)
│       ├── like-button.js        # Centralized like button handler
│       ├── navbar.js             # Extracted navbar JavaScript (~650 lines) + notification polling (15s, Session 87)
│       ├── notifications.js      # Notifications page interactions (Session 86, ~300 lines)
│       ├── overflow-tabs.js      # Shared overflow tab scroll module (Session 86, 187 lines)
│       ├── prompt-detail.js      # Prompt detail page interactions
│       ├── upload-core.js        # File selection, drag-drop, B2 upload, preview
│       ├── upload-form.js        # Form handling, NSFW status display
│       └── upload-guards.js      # Navigation guards, idle timeout detection
├── staticfiles/                  # Collected static (production)
└── templates/                    # Global Django templates (18 files)
    ├── account/                  # 6 authentication templates
    ├── admin/                    # 11 admin customization templates (incl. prompts/prompt/ sub-dir)
    ├── registration/             # 1 template
    ├── base.html                 # Main template (~1400 lines after JS extraction)
    ├── 404.html
    └── 429.html
```

---

## Management Commands (28 total)

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
| `test_django_q` | Test Django-Q2 background task processing | Manual |
| `regenerate_video_thumbnails` | Regenerate Cloudinary video thumbnails with correct aspect ratio | Manual |
| `minify_assets` | Minify CSS/JS files in STATIC_ROOT (run after collectstatic) | Manual / CI |
| `backfill_categories` | Backfill subject categories for existing prompts (superseded by backfill_ai_content) | Manual |
| `backfill_ai_content` | Regenerate ALL AI content (title, description, tags, categories, descriptors, slug) for existing prompts. Supports `--tags-only`, `--under-tag-limit`, `--published-only` | Manual |
| `audit_tags` | Audit existing prompt tags for compound fragments, orphan fragments, and quality issues. Supports `--fix`, `--export`, `--prompt-id` | Manual |
| `remove_mandatory_tags` | Remove mandatory AI-related tags (ai-prompt, ai-art, ai-generated) from all prompts | Manual |
| `reorder_tags` | Reorder existing prompt tags per validation pipeline rules (demographic to end) | Manual |
| `run_pass2_review` | Run Pass 2 SEO expert review on published prompts (tags + description only) | Manual |
| `backfill_comment_anchors` | Idempotent backfill to add #comments anchor to existing comment notification links | Manual |

---

## Service Layer Architecture (12 modules)

```
prompts/services/
├── __init__.py              # Service exports
├── b2_presign_service.py    # B2 presigned URL generation (Phase L8-DIRECT)
├── b2_rename.py             # B2 file renaming via copy-verify-delete (Phase N4h)
├── b2_upload_service.py     # B2 upload orchestration (Phase L)
├── cloudinary_moderation.py # OpenAI Vision moderation for images and videos
├── content_generation.py    # GPT-4o content generation for uploads
├── image_processor.py       # Pillow image optimization (Phase L)
├── leaderboard.py           # Leaderboard calculations (Phase G)
├── notifications.py         # Notification service: create, count, mark-read, duplicate prevention (Phase R1)
├── openai_moderation.py     # OpenAI text moderation API
├── orchestrator.py          # Moderation orchestration (multi-layer)
├── profanity_filter.py      # Profanity detection and filtering
└── video_processor.py       # FFmpeg video processing, frame extraction for moderation (Phase M)

prompts/storage_backends.py  # B2 storage backend + CDN URLs (Phase L, at app root)

prompts/utils/
├── __init__.py              # Package init
├── related.py               # Related prompts IDF-weighted scoring (6-factor: tags 30%, categories 25%, descriptors 35%, generator 5%, engagement 3%, recency 2%; 275 lines)
└── seo.py                   # SEO filename generation (stop word removal, slug truncation, -ai-prompt suffix)
```

### Service Descriptions

| Service | Description | Cost |
|---------|-------------|------|
| **b2_presign_service** | Generates presigned URLs for direct browser-to-B2 uploads (L8-DIRECT) | N/A |
| **b2_rename** | Renames B2 files from UUID to SEO slugs via copy-verify-delete (Phase N4h) | N/A |
| **b2_upload_service** | Orchestrates B2 uploads with optimization | ~$0.005/GB |
| **cloudinary_moderation** | Cloudinary AI Vision for image/video moderation | ~$5-10/1000 images |
| **content_generation** | GPT-4o-mini for AI-generated titles, descriptions, tags | ~$0.00255/upload |
| **image_processor** | Pillow-based image optimization (thumb, medium, large, webp) | N/A |
| **leaderboard** | User ranking by views, activity, engagement | N/A |
| **notifications** | Notification service: create with 60s dedup, count unread, mark-read (Phase R1) | N/A |
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
├── notification_views.py # Notification API + page views (Phase R1)
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
| **notification_views** | ~6 | Notification API (unread-count, mark-read), notifications page, category filtering |
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
| `base.html` | Main template with navbar, footer, OG/Twitter block defaults (~2000 lines) |
| `404.html` | Not found error page |
| `429.html` | Rate limit error page (WCAG AA) |
| `account/*.html` | 6 authentication templates (login, signup, logout, password reset) |
| `admin/*.html` | 11 admin customization templates (incl. `seo_review_queue.html`, `trash_dashboard.html`) |
| `admin/prompts/prompt/*.html` | 2 prompt-specific admin templates (`change_form_object_tools.html`, `regenerate_confirm.html`) (Session 80) |
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
| `upload.html` | Single-page upload (Phase N - replaces step 1 & 2) |
| `collection_edit.html` | Collection edit form (Phase K - Session 64) |
| `notifications.html` | Notifications page with card layout, avatars, quotes, per-card mark-as-read (Phase R1/R1-D - Sessions 86-87) |
| `trash_bin.html` | User trash bin |

**Deleted in Session 61:**
| ~~upload_step1.html~~ | Old Step 1 - replaced by upload.html |
| ~~upload_step2.html~~ | Old Step 2 - replaced by upload.html |
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

## Test Files (19 files, ~657 tests)

| Test File | Tests | Focus Area |
|-----------|-------|------------|
| `test_b2_presign.py` | 22 | B2 presigned URL generation (Phase L8-DIRECT) |
| `test_user_profiles.py` | 56 | User profile CRUD operations |
| `test_user_profile_auth.py` | 20 | User profile authentication |
| `test_rate_limiting.py` | 25 | Rate limiting enforcement |
| `test_generator_page.py` | 26 | AI generator category pages |
| `test_url_migration.py` | 10 | Phase I URL redirects |
| `test_prompts_hub.py` | 18 | Prompts hub functionality |
| `test_inspiration.py` | 16 | Inspiration page tests |
| `test_follows.py` | 10 | Follow system |
| `test_email_preferences_safety.py` | 8 | Email preference safety |
| `test_user_profile_header.py` | 31 | Profile header UI |
| `test_user_profile_javascript.py` | 12 | Profile JavaScript |
| `test_video_processor.py` | 42 | Video processing tests |
| `test_tags_context.py` | 17 | Tag context enhancement: excerpt in GPT prompt, weighting rules, backfill queryset (Session 81) |
| `test_validate_tags.py` | 150 | Tag validation pipeline: 8 checks, compound splitting, GPT self-check, demographic reorder, stop-word discard (Sessions 81, 83) |
| `test_backfill_hardening.py` | 44 | Backfill hardening: quality gate, fail-fast download, URL pre-check, tag preservation (Session 82) |
| `test_pass2_seo_review.py` | 65 | Pass 2 SEO system: queue, review, PROTECTED_TAGS, GPT prompt (Session 85) |
| `test_admin_actions.py` | 23 | Admin actions: two-button system, bulk actions, tag ordering (Session 85) |
| `test_notifications.py` | 62 | Notification system: model, signals, service, API, page views, bell dropdown, dedup edge cases (Sessions 86-87) |

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
| `models.py` | ~2,200 | Database models (Prompt, UserProfile, SubjectCategory, SubjectDescriptor, SlugRedirect, Notification, etc.) + `seo_pass2_at` field + `ordered_tags()` method |
| `admin.py` | ~2,300 | Django admin (PromptAdmin with two-button system, SEO Review + Rebuild actions, M2M ordering) |
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
├── navbar.css           # 1,136 lines - Extracted navbar styles + notification badge (Session 86)
├── style.css            # ~1,800 lines - Main stylesheet + shared media container component (Session 66)
├── upload.css           # ~880 lines - Upload page styles, warning toast, error card (rewritten S66, expanded S68)
├── components/
│   ├── icons.css        # ~250 lines - SVG icon system (Phase J.2)
│   ├── masonry-grid.css # 255 lines - Masonry grid component
│   └── profile-tabs.css # ~200 lines - Shared tab component (Session 86)
└── pages/
    ├── notifications.css # ~350 lines - Notifications page styles, card layout, per-card mark-as-read (Sessions 86-87)
    ├── prompt-detail.css # 1,515 lines - Prompt detail page + related prompts section (Phase J.1, Session 74)
    └── prompt-list.css   # 304 lines - Prompt list page styles
```

**Total CSS:** ~6,440 lines across 9 files

**Shared CSS Components (Session 66):**
- `.media-container-shell` / `.media-container` - Shared image/video container used by upload preview and prompt detail
- `--media-container-padding` CSS variable in `:root`
- `var(--radius-lg)` replaces all hardcoded `border-radius: 12px` values

**CSS Specificity Notes (Session 73):**
- `masonry-grid.css` loads AFTER `style.css` in `base.html` (line 62 vs 58)
- `.video-play-icon { pointer-events: none; }` in masonry-grid.css (line 139) wins specificity ties against style.css
- Trash video styles use `.trash-prompt-wrapper .trash-video-play` (specificity 0,2,0) to override masonry-grid.css (0,1,0)
- Mobile trash cards disable `.card-link` via `pointer-events: none` to allow play icon taps

---

## CI/CD Configuration

### GitHub Actions Pipeline (`.github/workflows/django-ci.yml`)

**Triggers:** Push to main/develop, Pull requests to main

| Job | Purpose | Timeout |
|-----|---------|---------|
| **test** | Django tests with PostgreSQL, coverage ≥40% | 15 min |
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
├── upload-form.js        # ~700+ lines - Form handling, ProcessingModal (Phase N4)
└── upload-guards.js      # ~410 lines - Navigation guards, idle detection (Phase N)

# DELETED in Session 61:
# - processing.js (replaced by ProcessingModal in upload-form.js)
# - upload-step1.js (old step-based upload, deprecated)
```

### JavaScript Files

| File | Lines | Purpose |
|------|-------|---------|
| **collections.js** | ~760 | Collections modal, API integration, thumbnail grids |
| **navbar.js** | ~750 | Dropdowns, search, mobile menu, scroll, notification polling (15s) + keyboard nav + bell sync dispatch (Phase R1/R1-D) |
| **notifications.js** | ~300 | Notifications page mark-as-read, category filtering, event delegation, bell sync listener (Phase R1/R1-D) |
| **overflow-tabs.js** | ~187 | Shared overflow tab scroll with auto-center options (Phase R1) |
| **prompt-detail.js** | ~400 | Like toggle, copy button, comments, delete modal |
| **like-button.js** | ~155 | Centralized like handler with optimistic UI |
| **upload-core.js** | ~640 | B2 presigned upload, drag-drop, local preview, orphan cleanup, 30s warning toast (Phase N) |
| **upload-form.js** | ~1020 | Form validation, NSFW status, ProcessingModal, video ai_job_id, error message card (Phase N4) |
| **upload-guards.js** | ~410 | Navigation guards, idle timeout, cleanup beacon (Phase N) |

**Deleted in Session 61:**
| File | Lines | Reason |
|------|-------|--------|
| ~~processing.js~~ | ~300 | Replaced by ProcessingModal in upload-form.js |
| ~~upload-step1.js~~ | ~768 | Old step-based upload flow removed |

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

**Total JavaScript:** ~4,160 lines across 9 files (after Session 61 cleanup, 2 added in Session 86)
**Extraction Benefit:** base.html reduced from ~2000 lines to ~1400 lines

---

## SVG Icon System (Phase J.2)

PromptFinder uses a custom SVG sprite system for icons, replacing Font Awesome for improved performance and consistency.

### Files

| File | Location | Purpose |
|------|----------|---------|
| `sprite.svg` | static/icons/ | SVG sprite with 33 icon definitions |
| `icons.css` | static/css/components/ | Icon utility classes |

### Available Icons (33 total)

**Phase 1 Icons (Navigation) - 5 icons:**
- `icon-image` - Photos filter indicator
- `icon-video` - Videos filter indicator
- `icon-search` - Search dropdown icon
- `icon-trophy` - Leaderboard dropdown icon
- `icon-lightbulb` - Prompts dropdown icon

**Phase 2 Icons (Actions) - 12 icons:**
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
- `icon-square-check-big` - Mark as read checkmark (Session 87)

**Phase 3 Icons (Profile) - 3 icons:**
- `icon-user` - User profile
- `icon-user-pen` - Edit profile
- `icon-mail` - Email/contact

**Phase K Icons (Collections) - 13 icons:**
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
- `icon-rotate-ccw` - Restore button (Session 70)
- `icon-clock` - Trash "deleted X days ago" indicator (Session 74)

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
| `/collections/<slug>/restore/` | `collection_restore` | Restore deleted collection (Session 70) |
| `/collections/<slug>/delete-forever/` | `collection_permanent_delete` | Permanently delete collection (Session 70) |
| `/collections/trash/empty/` | `empty_collections_trash` | Empty all trashed collections (Session 70) |

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

#### Video Upload Flow (Updated Session 61)
```
1. GET /api/upload/b2/presign/
   └─ Sets: b2_pending_upload (file_key, filename, content_type='video/*')

2. Browser uploads directly to B2 via presigned URL

3. POST /api/upload/b2/complete/
   └─ Reads: b2_pending_upload
   └─ Sets: b2_video_url, b2_video_thumb_url, direct_upload_is_video=True
   └─ Sets: ai_job_id (NEW: for video AI processing)
   └─ Queues: AI content generation using video thumbnail
   └─ Note: No variant generation for videos (stored as-is)

4. User fills out form (single-page upload)
   └─ Reads: b2_video_url, b2_video_thumb_url, direct_upload_is_video
   └─ Frontend receives: ai_job_id for polling

5. POST /upload/submit/
   └─ Reads: b2_video_url, b2_video_thumb_url, direct_upload_is_video
   └─ Shows: ProcessingModal while polling for AI completion
   └─ Polls: ai_job_id status
   └─ Saves: prompt.b2_video_url, prompt.b2_video_thumb_url
   └─ Clears: All upload session keys via clear_upload_session()

6. Redirect to prompt detail page
```

**Session Keys for Video (Session 61):**
```python
# Set in b2_upload_complete for videos:
request.session['direct_upload_urls'] = urls  # {'original': ..., 'thumb': ...}
request.session['direct_upload_filename'] = filename
request.session['direct_upload_is_video'] = True
request.session['upload_b2_video'] = urls['original']
request.session['upload_b2_video_thumb'] = urls['thumb']
request.session['ai_job_id'] = ai_job_id  # NEW: For video AI processing
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
| **Web Dyno** | Eco dyno ($5/month) |
| **Worker Dyno** | Standard-1X ($25/mo) for Django-Q (`python manage.py qcluster`) - configured Session 64 |
| **Database** | Heroku PostgreSQL Mini ($5/month) |
| **Scheduler** | Heroku Scheduler (free) |
| **Total Cost** | ~$10/month (covered by credits) |

### Procfile

```
web: gunicorn prompts_manager.wsgi
worker: python manage.py qcluster
```

The `worker` process runs Django-Q2 background task processing (AI content generation). Without a worker dyno scaled up, background tasks won't execute.

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

- **Total Tests:** ~657 passing (12 skipped - Selenium)
- **Pass Rate:** 100% in CI
- **Coverage:** ~43% (enforced minimum: 40%)
- **Note:** `prompts/tests.py` (stale stub) was deleted in Session 83 — conflicted with `prompts/tests/` directory discovery
- **Priority Areas:** CRUD, authentication, rate limiting, URL migration
- **CI Integration:** Tests run on every push/PR via GitHub Actions

---

## Phase N4 Files (Optimistic Upload Flow)

### Implementation Status (Session 69)

| Sub-Phase | Status | What Was Done |
|-----------|--------|---------------|
| **N4a** | ✅ Complete | Model fields added |
| **N4b** | ✅ Complete | Django-Q2 configured |
| **N4c** | ✅ Complete | Admin fieldsets updated |
| **N4d** | ✅ Complete | Processing page view + template conditionals |
| **N4e** | ✅ Complete | AI job queuing for videos (uses thumbnail) |
| **N4f** | ✅ Complete | ProcessingModal in upload-form.js |
| **N4 Cleanup** | ✅ Complete | Removed old upload code |
| **SEO Meta** | ✅ Complete | OG/Twitter blocks, Schema.org JSON-LD + VideoObject |
| **AI Quality** | ✅ Complete | Style-first titles, description truncation fix, race/ethnicity |
| **SEO Enhance** | ✅ Complete | Race/ethnicity, enhanced alt tags, Schema.org VideoObject (Session 64) |
| **N4g Video Fix** | ✅ Resolved | Video submit session key mismatch fixed (Session 64) |
| **Upload Polish** | ✅ Complete | File input reset, visibility toggle, native aspect ratio (Session 66) |
| **CSS Architecture** | ✅ Complete | Shared media container, 22 border-radius unified (Session 66) |
| **SEO Overhaul** | ✅ Complete | 72→95/100: JSON-LD, OG, Twitter, canonical, headings, noindex (Session 66) |
| **SEO Headings** | ✅ Complete | Fixed heading hierarchy (H1→H2→H3), visual breadcrumbs with focus-visible (Session 67) |
| **N4h File Rename** | ✅ Complete | B2 SEO file renaming: seo.py, B2RenameService, background task (Session 67) |
| **Admin Improvements** | ✅ Complete | Prompt ID, B2 URLs fieldset, expanded fieldsets (Session 68) |
| **Upload UX** | ✅ Complete | 30-second warning toast, friendly error message card (Session 68) |
| **Perf: Backend** | ✅ Complete | select_related/prefetch_related, materialized likes/comments, ~60-70% query reduction (Session 68) |
| **Perf: Caching** | ✅ Complete | Template fragment caching for tags + more_from_author, 5-min TTL (Session 68) |
| **Perf: Indexes** | ✅ Complete | Composite indexes (status,created_on) + (author,status,deleted_at) - migration pending (Session 68) |
| **Perf: Frontend** | ✅ Complete | Critical CSS inlining, async CSS, LCP preload, preconnect, JS defer (Session 68) |
| **SEO: robots.txt** | ✅ Complete | robots.txt via WHITENOISE_ROOT, preconnect cleanup, font optimization (Session 69) |
| **A11y Fixes** | ✅ Complete | h3→h2 headings, aria-label pluralize fixes (Session 69) |
| **Asset Minification** | ✅ Complete | minify_assets command targeting STATIC_ROOT, csscompressor + rjsmin (Session 69) |

### Files Created

```
docs/
└── PHASE_N4_UPLOAD_FLOW_REPORT.md    # Comprehensive planning document ✅
```

### Files Deleted (Session 61 Cleanup)

```
prompts/templates/prompts/
├── upload_step1.html                  # DELETED - replaced by upload.html
└── upload_step2.html                  # DELETED - replaced by upload.html

static/js/
├── processing.js                      # DELETED - replaced by ProcessingModal
└── upload-step1.js                    # DELETED - old step-based upload (~768 lines)

prompts/templates/prompts/
└── prompt_detail.html                 # MODIFIED - removed is_processing conditionals
```

### Files Modified (Session 66 - SEO + Upload + CSS)

```
prompts/templates/prompts/
└── prompt_detail.html                 # Complete SEO overhaul: JSON-LD, OG, Twitter, canonical,
                                       # heading hierarchy, tag links, noindex drafts (72→95/100)

prompts/templates/prompts/
└── upload.html                        # Two-column grid redesign, card form, visibility toggle

templates/
└── base.html                          # Dynamic copyright year ({% now "Y" %})

static/css/
├── style.css                          # Shared .media-container-shell/.media-container, --media-container-padding,
│                                      # 8 border-radius replacements with var(--radius-lg)
├── upload.css                         # Complete rewrite: modern card design, native aspect ratio
├── components/masonry-grid.css        # 3 border-radius replacements
└── pages/
    ├── prompt-detail.css              # Media container variable usage
    └── prompt-list.css                # 1 border-radius replacement

static/js/
├── upload-core.js                     # File input reset on validation error
└── upload-form.js                     # initVisibilityToggle(), SVG checkmark NSFW approved

docs/reports/
├── SEO_AUDIT_PROMPT_DETAIL_PAGE.md    # NEW - Initial audit (72/100)
├── SEO_REAUDIT_PROMPT_DETAIL_PAGE.md  # NEW - Re-audit (88/100)
├── SEO_TIER1_FIXES_REPORT.md         # NEW - Tier 1 fixes (~92/100)
├── SEO_TIER2_FIXES_REPORT.md         # NEW - Tier 2 enhancements (~95/100)
└── SEO_VALIDATION_REPORT.md          # NEW - Final validation (READY FOR PRODUCTION)
```

### Files Created (Session 67 - N4h B2 File Renaming)

```
prompts/utils/
├── __init__.py                        # NEW - Utils package init
└── seo.py                             # NEW - SEO filename generation (stop words, slug truncation, -ai-prompt suffix)

prompts/services/
└── b2_rename.py                       # NEW - B2RenameService (copy → head_object verify → delete pattern)
```

### Files Modified (Session 67 - SEO Headings + N4h)

```
prompts/
└── tasks.py                           # Added rename_prompt_files_for_seo() task + async_task queuing
                                       # in _update_prompt_with_ai_content (per-field immediate DB save)

prompts/templates/prompts/
└── upload.html                        # Heading hierarchy fixes, visual breadcrumbs, accessibility

static/css/
└── upload.css                         # Breadcrumb styles, focus-visible, heading updates

static/js/
├── upload-core.js                     # Minor upload flow updates
└── upload-form.js                     # Minor form handling updates
```

### Files Modified (Session 68 - Admin + Upload UX + Performance)

```
prompts/
├── admin.py                          # Prompt ID display, B2 Media URLs fieldset, all fieldsets expanded
├── models.py                         # Composite indexes: (status,created_on), (author,status,deleted_at)
└── views/
    └── prompt_views.py               # select_related/prefetch_related optimization, materialized likes/comments

prompts/templates/prompts/
└── prompt_detail.html                # Template fragment caching (tags, more_from_author), critical CSS,
                                       # async CSS loading, LCP preload with imagesrcset, preconnect hints

static/css/
└── upload.css                         # Warning toast styles, error message card styles

static/js/
├── upload-core.js                     # 30-second upload warning timer, toast show/hide/dismiss
└── upload-form.js                     # Improved error message display, warning toast dismiss in modal
```

### Files Created (Session 69 - SEO + A11y + Minification)

```
static_root/
└── robots.txt                        # NEW - Search engine crawl directives via WHITENOISE_ROOT

prompts/management/commands/
└── minify_assets.py                  # NEW - CSS/JS minification command (targets STATIC_ROOT, --dry-run)
```

### Files Modified (Session 69 - SEO + A11y + Minification)

```
prompts_manager/
└── settings.py                       # Added WHITENOISE_ROOT = BASE_DIR / 'static_root'

prompts_manager/
└── urls.py                           # Removed robots.txt RedirectView, added WHITENOISE_ROOT comment

templates/
└── base.html                         # Removed stale preconnects (Cloudinary, cdnjs), reduced font weights
                                       # (300,400,500,700 → 400,500,700), deferred icons.css + noscript fallback

prompts/templates/prompts/
└── prompt_detail.html                # h3→h2 headings (5 instances), aria-label pluralize fixes (like buttons, see all)

requirements.txt                       # Added csscompressor>=0.9.5, rjsmin>=1.2.0
```

### Files Modified (Session 59-63)

```
prompts/
├── models.py                          # Added processing_uuid, processing_complete ✅
├── urls.py                            # Added processing page route ✅
├── tasks.py                           # AI prompt rewrite, max_tokens 1000, description max_length 2000 (uncommitted)
└── views/
    ├── upload_views.py                # Added prompt_processing view ✅
    ├── api_views.py                   # AI job queuing for videos (uncommitted)
    └── __init__.py                    # Exported prompt_processing ✅

prompts/services/
└── content_generation.py              # max_tokens 1000, filename 5 keywords, alt tag format (S63)

prompts/templates/prompts/
└── prompt_detail.html                 # OG/Twitter block overrides, Schema.org JSON-LD, canonical (S63)

templates/
└── base.html                          # Added {% block og_tags %}, {% block twitter_tags %} (S63)

static/js/
└── upload-form.js                     # Added ProcessingModal, video ai_job_id (uncommitted)

static/css/pages/
└── prompt-detail.css                  # Added processing spinner + modal styles ✅

prompts_manager/
└── settings.py                        # Django-Q config + domain allowlist fix (uncommitted)

requirements.txt                       # Added django-q2 ✅
Procfile                               # Added worker process for Django-Q ✅
```

### Files Still Pending

```
prompts/
├── sitemaps.py                        # XML sitemap for SEO
└── views/
    └── api_views.py                   # Add prompt_processing_status endpoint (N4f)
```

**Note:** `rename_b2_files_for_seo()` in `tasks.py` was implemented in Session 67 (moved from pending to complete).

### URL Routes

| URL | View | Status |
|-----|------|--------|
| `/prompt/processing/<uuid>/` | `prompt_processing` | ✅ Implemented |
| `/api/prompt/status/<uuid>/` | `prompt_processing_status` | ⏳ N4f pending |
| `/sitemap.xml` | Django sitemap | ⏳ Future |

### Database Fields (Prompt model)

| Field | Type | Status |
|-------|------|--------|
| `processing_uuid` | UUIDField | ✅ Added (N4a) |
| `processing_complete` | BooleanField | ✅ Added (N4a) |

---

## Phase 2B Files (Category Taxonomy Revamp)

### Files Created (Phase 2B Session — Feb 9-10, 2026)

```
prompts/management/commands/
└── backfill_ai_content.py            # NEW - Full AI content regeneration (--dry-run, --limit, --prompt-id, --batch-size, --delay, --skip-recent)

prompts/migrations/
├── 0048_create_subject_descriptor.py  # NEW - SubjectDescriptor model + Prompt.descriptors M2M
├── 0049_populate_descriptors.py       # NEW - Seed 109 descriptors across 10 types
├── 0050_update_subject_categories.py  # NEW - Expand to 46 categories (add 19, rename 2, remove 1)
├── 0051_fix_descriptor_type_duplicate_index.py  # NEW - Index fix for descriptor_type
└── 0052_alter_subjectcategory_slug.py # NEW - SubjectCategory.slug max_length 200

docs/
├── PHASE_2B1_COMPLETION_REPORT.md     # NEW - Model + data setup completion
├── PHASE_2B2_COMPLETION_REPORT.md     # NEW - AI prompt updates completion
├── PHASE_2B3_COMPLETION_REPORT.md     # NEW - Upload flow completion
├── PHASE_2B4_COMPLETION_REPORT.md     # NEW - Scoring update completion
├── PHASE_2B5_COMPLETION_REPORT.md     # NEW - Full AI backfill completion
└── PHASE_2B6_COMPLETION_REPORT.md     # NEW - SEO demographic strengthening completion
```

### Files Modified (Phase 2B Session)

```
prompts/
├── models.py                          # SubjectDescriptor model, Prompt.descriptors M2M, slug max_length 200
├── admin.py                           # SubjectDescriptorAdmin with read-only enforcement
├── tasks.py                           # Three-tier taxonomy AI prompt, demographic SEO rules, banned ethnicity tags, mandatory AI tags
└── views/
    ├── upload_views.py                # Descriptor assignment from cache/session
    └── prompt_views.py                # Tag filter (?tag= exact matching with .distinct()), video B2-first visibility

prompts/utils/
└── related.py                         # 6-factor scoring (30/25/35/5/3/2 — IDF-weighted, 90% content relevance, 10% tiebreakers)

prompts/templates/prompts/
├── prompt_list.html                   # Tag links: ?search= → ?tag=
└── prompt_detail.html                 # Tag links: ?search= → ?tag=

docs/
└── DESIGN_RELATED_PROMPTS.md          # Updated scoring weights for 6-factor system
```

### Database Fields (Phase 2B)

| Field | Type | Status |
|-------|------|--------|
| `Prompt.descriptors` | ManyToManyField → SubjectDescriptor | ✅ Added (2B-1) |
| `Prompt.slug` | SlugField(max_length=200) | ✅ Updated from 50 (2B-6) |
| `SubjectDescriptor.name` | CharField(max_length=100) | ✅ Added (2B-1) |
| `SubjectDescriptor.slug` | SlugField(max_length=100) | ✅ Added (2B-1) |
| `SubjectDescriptor.descriptor_type` | CharField(max_length=20, choices=10 types) | ✅ Added (2B-1) |
| `SubjectCategory.slug` | SlugField(max_length=200) | ✅ Updated (0052) |

---

## Sessions 80-81 Files (Admin Metadata + Security + Tag Pipeline)

### Files Created (Session 80 — Admin Metadata & Security)

```
prompts/migrations/
└── 0053_add_slug_redirect.py             # NEW - SlugRedirect model for SEO-safe slug editing

templates/admin/prompts/prompt/
├── change_form_object_tools.html         # NEW - "Regenerate AI Content" button in admin
└── regenerate_confirm.html               # NEW - Confirmation page for AI regeneration

prompts/management/commands/
└── remove_mandatory_tags.py              # NEW - Remove mandatory AI-related tags from all prompts
```

### Files Created (Session 81 — Tag Pipeline)

```
prompts/migrations/
└── 0054_rename_3d_photo_category.py      # NEW - Rename "3D Photo / Forced Perspective" to include Facebook 3D

prompts/management/commands/
└── audit_tags.py                         # NEW - Audit tags for compound fragments, orphans, quality issues (315 lines)

prompts/tests/
├── test_tags_context.py                  # NEW - 17 tests for tag context (excerpt in GPT, weighting rules, backfill queryset)
└── test_validate_tags.py                 # NEW - 113 tests for tag validation pipeline (7 checks, compound splitting)

# Root-level audit scripts
audit_nsfw_tags.py                        # NEW - NSFW tag audit script
audit_tags_vs_descriptions.py             # NEW - Tag vs description mismatch audit script

docs/
└── SESSION_REPORT_TAGS_AND_SEO_PROMPT_FIXES.md  # NEW - Session 81 completion report (863 lines)
```

### Files Modified (Session 80 — Admin Metadata & Security)

```
prompts/
├── models.py                             # SlugRedirect model (old_slug, prompt, created_at)
├── admin.py                              # Enhanced PromptAdmin: full metadata editing, B2 preview,
│                                         # XSS safeguards, char limits, dynamic weights, regenerate button,
│                                         # tag autocomplete, slug protection (~500+ lines rewritten)
└── views/
    ├── prompt_views.py                   # SlugRedirect lookup, @login_required + @require_POST on delete/toggle
    └── admin_views.py                    # regenerate_ai_content view

prompts/utils/
└── related.py                            # Dynamic weight reading for admin, hardcoded percentages audited

prompts/templates/prompts/
└── prompt_detail.html                    # CSRF POST form for delete button (was GET link)

prompts_manager/
├── settings.py                           # INSTALLED_APPS additions for admin
└── urls.py                               # Admin regenerate URL

static/js/
└── prompt-detail.js                      # Delete uses POST form
```

### Files Modified (Session 81 — Tag Pipeline)

```
prompts/
├── tasks.py                              # _validate_and_fix_tags() 8-check pipeline,
│                                         # TAG_RULES_BLOCK shared constant (~76 lines),
│                                         # _should_split_compound(), SPLIT_THESE_WORDS set (30 words),
│                                         # PRESERVE_DESPITE_STOP_WORDS, PRESERVE_SINGLE_CHAR_COMPOUNDS (12),
│                                         # ALLOWED_AI_TAGS (5), DEMOGRAPHIC_TAGS (16), GENERIC_TAGS (32),
│                                         # COMPOUND TAG RULE + WEIGHTING RULES in GPT prompt,
│                                         # GPT self-check (rule 7 + compounds_check chain-of-thought),
│                                         # excerpt parameter in _call_openai_vision_tags_only(),
│                                         # tags-only backfill support
├── admin.py                              # Minor tag-related fixes
└── views/
    └── upload_views.py                   # Tag validation on upload submit

prompts/management/commands/
├── backfill_ai_content.py                # --tags-only, --under-tag-limit, --published-only flags (~214 lines added)
└── cleanup_old_tags.py                   # Rewritten: orphan detection + capitalized duplicate merge (~157 lines rewritten)
```

### Database Fields (Sessions 80-81)

| Field | Type | Status |
|-------|------|--------|
| `SlugRedirect.old_slug` | SlugField(max_length=200, unique=True) | ✅ Added (0053) |
| `SlugRedirect.prompt` | ForeignKey → Prompt | ✅ Added (0053) |
| `SlugRedirect.created_at` | DateTimeField(auto_now_add=True) | ✅ Added (0053) |

---

## Session 85 Files (Pass 2 SEO System + Admin UX + Tag Ordering)

### Files Created (Session 85)

```
prompts/migrations/
└── 0055_add_seo_pass2_at.py             # NEW - seo_pass2_at DateTimeField for tracking Pass 2 runs

prompts/management/commands/
├── reorder_tags.py                       # NEW - Reorder existing tags per validation rules (demographic to end)
└── run_pass2_review.py                   # NEW - Run Pass 2 SEO review on published prompts (131 lines)

prompts/tests/
├── test_pass2_seo_review.py             # NEW - 60+ tests for Pass 2 SEO system (1045 lines)
└── test_admin_actions.py                # NEW - 23 tests for admin actions, button labels, tag ordering

templates/admin/prompts/prompt/
└── change_form.html                     # NEW - Admin change form with two-button layout + help text

docs/
├── REPORT_ADMIN_ACTIONS_AGENT_REVIEW.md # NEW - Admin actions review report
└── REPORT_DEMOGRAPHIC_TAG_ORDERING_FIX.md # NEW - Tag ordering fix report

# Root-level docs reorganized from docs/
AGENT_TESTING_SYSTEM.md                   # Moved to root (was in docs/)
HANDOFF_TEMPLATE_STRUCTURE.md             # Renamed from HANDOFF_TEMPLATE_STRUCTURE/ (was in docs/)
PHASE_N_DETAILED_OUTLINE.md               # Moved to root (was in docs/)
```

### Files Modified (Session 85)

```
prompts/
├── tasks.py                              # Pass 2 SEO system: queue_pass2_review(), _run_pass2_seo_review(),
│                                         # PROTECTED_TAGS constant, GENDER_LAST_TAGS constant,
│                                         # rewritten Pass 2 GPT system prompt (~550 lines added)
├── models.py                             # seo_pass2_at DateTimeField, ordered_tags() method
├── admin.py                              # Two-button system (SEO Review + Rebuild), button labels updated,
│                                         # _apply_ai_m2m_updates tag ordering (clear() + add()),
│                                         # updated success messages, bulk action labels
└── views/
    ├── prompt_views.py                   # ordered_tags() in detail/edit contexts
    └── upload_views.py                   # ordered_tags() in create context

prompts/templates/prompts/
├── prompt_detail.html                    # escapejs on tag onclick, ordered_tags usage
├── prompt_create.html                    # ordered_tags usage
└── prompt_edit.html                      # ordered_tags usage

prompts/tests/
└── test_validate_tags.py                 # Expanded with tag ordering tests (+266 lines)

templates/admin/prompts/prompt/
└── change_form_object_tools.html         # Updated button labels (Optimize Tags & Description / Rebuild All Content),
                                          # rounded styling (border-radius: 20px)

CC_COMMUNICATION_PROTOCOL.md              # Reorganized to project root, content refresh
```

### Database Fields (Session 85)

| Field | Type | Status |
|-------|------|--------|
| `Prompt.seo_pass2_at` | DateTimeField(null=True, blank=True) | ✅ Added (0055) |

---

## Session 86 Files (Phase R1 — User Notifications)

### Files Created (Session 86)

```
prompts/services/
└── notifications.py                     # NEW - Notification service: create, count, mark-read, 60s dedup

prompts/signals/
├── __init__.py                          # NEW - Signals package init
└── notification_signals.py              # NEW - Signal handlers for comment, like, follow, collection save

prompts/views/
└── notification_views.py                # NEW - Notification API (unread-count, mark-all-read, mark-read) + page

prompts/templates/prompts/
├── notifications.html                   # NEW - Notifications page with category tabs, empty states
└── partials/
    └── _notification_list.html          # NEW - AJAX notification list partial

prompts/tests/
└── test_notifications.py                # NEW - 54 notification tests (model, signals, service, API, page views)

prompts/migrations/
└── 0056_add_notification_model.py       # NEW - Notification model (6 types, 5 categories, 3 indexes)

static/js/
├── overflow-tabs.js                     # NEW - Shared overflow tab scroll module (187 lines)
└── notifications.js                     # NEW - Notifications page JS (mark-as-read, category filtering)

static/css/
├── components/
│   └── profile-tabs.css                 # NEW - Shared tab component CSS (used by 3 templates)
└── pages/
    └── notifications.css                # NEW - Notifications page styles
```

### Files Modified (Session 86)

```
prompts/
├── models.py                            # Notification model (6 types, 5 categories, 3 DB indexes)
├── apps.py                              # Notification signals registration
├── urls.py                              # Notification URL patterns (page + API endpoints)
└── templatetags/
    └── notification_tags.py             # Notification template tags

templates/
└── base.html                            # Bell icon dropdown (pexels dropdown), notification polling JS

static/js/
└── navbar.js                            # Notification polling (60s), keyboard nav (WAI-ARIA roving focus),
                                          # badge updates via aria-live

static/css/
└── navbar.css                           # Notification badge styles, bell icon positioning

prompts/templates/prompts/
├── user_profile.html                    # Migrated to shared profile-tabs system (overflow-tabs.js)
└── collections_profile.html             # Migrated to shared profile-tabs system, removed 75 lines inline CSS
```

### Database Fields (Session 86)

| Field | Type | Status |
|-------|------|--------|
| `Notification.recipient` | ForeignKey → User | ✅ Added (0056) |
| `Notification.sender` | ForeignKey → User (nullable) | ✅ Added (0056) |
| `Notification.notification_type` | CharField (6 choices) | ✅ Added (0056) |
| `Notification.category` | CharField (5 choices, auto-derived) | ✅ Added (0056) |
| `Notification.message` | TextField | ✅ Added (0056) |
| `Notification.is_read` | BooleanField (default=False) | ✅ Added (0056) |
| `Notification.related_prompt` | ForeignKey → Prompt (nullable) | ✅ Added (0056) |
| `Notification.created_at` | DateTimeField(auto_now_add=True) | ✅ Added (0056) |

---

## Related Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| CLAUDE.md | Root | Master project documentation |
| CC_COMMUNICATION_PROTOCOL.md | Root | Agent usage requirements |
| UI_STYLE_GUIDE.md | design-references/ | UI/UX standards |
| PROJECT_FILE_STRUCTURE_AUDIT_REPORT.md | docs/reports/ | Latest audit findings |
| L8_TIMEOUT_COMPLETION_REPORT.md | docs/reports/ | L8-TIMEOUT implementation details |
| PHASE_N4_UPLOAD_FLOW_REPORT.md | docs/ | Phase N4 comprehensive planning |
| DESIGN_RELATED_PROMPTS.md | docs/ | Related Prompts system reference (Phase 2B-9 complete) |
| DESIGN_CATEGORY_TAXONOMY_REVAMP.md | docs/ | Phase 2B category taxonomy revamp (Session 74) |
| PHASE_2B_AGENDA.md | docs/ | Phase 2B execution roadmap (Session 74) |
| PHASE_2B1-6_COMPLETION_REPORT.md | docs/ | Phase 2B sub-phase completion reports (Phase 2B Session) |
| SESSION_REPORT_TAGS_AND_SEO_PROMPT_FIXES.md | docs/ | Session 81 tag pipeline completion report (Session 81) |

---

**END OF PROJECT_FILE_STRUCTURE.md**

*This document is updated after major structural changes. Last audit: January 9, 2026.*

**Version:** 3.20
**Audit Date:** February 18, 2026
**Maintained By:** Mateo Johnson - Prompt Finder

### Changelog

**v3.20 (February 18, 2026 - Session 87 End-of-Session Docs Update):**
- Updated total test count: ~649→~657 (actual method count, 5 new dedup tests + corrected baseline)
- Added `backfill_comment_anchors.py` management command (count 27→28)
- Added `reorder_tags` and `run_pass2_review` to management commands table (were missing from Session 85)
- Added `test_pass2_seo_review.py` and `test_admin_actions.py` to test files table (were missing from Session 85)
- Updated all test file counts from "Multiple" to actual method counts
- Added `icon-square-check-big` to SVG icons (count 32→33)
- Updated `test_notifications.py` test count: 54→62 (corrected from actual file)
- Updated `notifications.html` description: card-based redesign with avatars, quotes, per-card mark-as-read
- Updated `notifications.css` line count: ~150→~350 (card layout, button styles, unread tint)
- Updated `notifications.js` line count: ~200→~300 (event delegation, bell sync listener)
- Updated `navbar.js` description: polling 60s→15s, bell sync dispatch
- Updated current phase in header to include R1-D (complete)
- Fixed stale counts: CSS files 8→9, test files tree 16→19, management commands heading 26→28, SVG tree 30→33, services heading 11→12

**v3.19 (February 17, 2026 - Session 86 End-of-Session Docs Update):**
- Updated total test count: ~595→~649
- Added `notifications.py` service (count 11→12)
- Added `notification_views.py` view module (count 11→12)
- Added `signals/` package with `notification_signals.py`
- Added migration 0056 (count 57→58)
- Added `test_notifications.py` (54 tests) to test files (count 18→19)
- Added `overflow-tabs.js` and `notifications.js` to JS files (count 7→9)
- Added `profile-tabs.css` and `notifications.css` to CSS files (count 7→9)
- Added `notifications.html` and `_notification_list.html` to templates
- Added Session 86 Files section with all created/modified files and database fields
- Updated `models.py` description: added Notification model (~2,100→~2,200 lines)
- Updated `navbar.js` description: notification polling + keyboard nav (~650→~750 lines)
- Updated current phase in header to include Phase R1 (complete)

**v3.18 (February 16, 2026 - Session 85 End-of-Session Docs Update):**
- Updated total test count: ~498→~595
- Added `reorder_tags.py` and `run_pass2_review.py` management commands (count 25→27)
- Added migration 0055 (count 56→57)
- Added `test_pass2_seo_review.py` (60+ tests) and `test_admin_actions.py` (23 tests) to test files (count 16→18)
- Added Session 85 Files section with all created/modified files and database fields
- Updated `models.py` description: `seo_pass2_at` field, `ordered_tags()` method
- Updated `admin.py` description: two-button system, ~2,300 lines
- Updated CC_COMMUNICATION_PROTOCOL.md location from docs/ to Root
- Added `change_form.html` admin template

**v3.17 (February 14, 2026 - Session 83 End-of-Session Docs Update):**
- Updated total test count: ~472→~498
- Updated `test_validate_tags.py` from 113 → 200 tests (8-check pipeline, GPT self-check, demographic reorder)
- Updated `tasks.py` description with new constants: TAG_RULES_BLOCK, ALLOWED_AI_TAGS, PRESERVE_SINGLE_CHAR_COMPOUNDS, DEMOGRAPHIC_TAGS, GENERIC_TAGS (32 entries)
- Noted `prompts/tests.py` deletion (stale stub conflicting with tests/ directory)
- Updated test statistics section with deletion note

**v3.16 (February 13, 2026 - Session 82 End-of-Session Docs Update):**
- Added `test_backfill_hardening.py` (44 tests) to test files (count 15→16)
- Updated total test count: ~427→~472
- Added Session 82 committed block to CLAUDE.md
- Updated CLAUDE_CHANGELOG.md with Session 82 entry
- Updated CLAUDE_PHASES.md with Session 82 sub-phase rows

**v3.15 (February 12, 2026 - Sessions 80-81 End-of-Session Docs Update):**
- Added `audit_tags.py` and `remove_mandatory_tags.py` management commands (count 23→25)
- Added migrations 0053-0054 (count 53→56 total: 54 prompts + 2 about)
- Added `test_tags_context.py` (17 tests) and `test_validate_tags.py` (113 tests) to test files (count 13→15)
- Updated total test count: 298→~427
- Added Sessions 80-81 Files section with all created/modified files and database fields
- Added `SlugRedirect` model to models.py description
- Added 2 admin prompt templates (`change_form_object_tools.html`, `regenerate_confirm.html`)
- Updated admin templates count (8→11, corrected pre-existing undercount)
- Added `SESSION_REPORT_TAGS_AND_SEO_PROMPT_FIXES.md` to Related Documentation
- Updated test files list: added `test_user_profile_auth.py`, `test_video_processor.py` (previously missing from docs)

**v3.14 (February 10, 2026 - Phase 2B-9 Documentation Update):**
- Updated `related.py` description to reflect IDF-weighted scoring and 276-line count
- Updated `DESIGN_RELATED_PROMPTS.md` description (full rewrite as system reference)
- Updated current phase in header to include Phase 2B-9

**v3.13 (February 10, 2026 - Phase 2B End-of-Session Docs Update):**
- Added `backfill_ai_content.py` management command (count 21→23, also added test_django_q)
- Added migrations 0048-0052 (count 42→52)
- Added Phase 2B Files section with created/modified files and database fields
- Updated `related.py` description to reflect 6-factor scoring (descriptors added)
- Updated `models.py` description to mention SubjectDescriptor model
- Updated Prompt.slug max_length documentation (50→200)
- Added 6 Phase 2B completion reports to docs/ structure
- Added PHASE_2B1-6_COMPLETION_REPORT.md to Related Documentation table
- Updated current phase in header

**v3.12 (February 9, 2026 - Session 74 End-of-Session Docs Update):**
- Added `backfill_categories.py` management command (count 20→21)
- Added migrations 0046, 0047 (count 40→42)
- Added 3 design docs to docs/ directory structure (count 33→36)
- Updated `related.py` description to reflect 5-factor scoring (categories added)
- Updated `prompt-detail.css` line count (1,063→1,515)
- Updated total CSS lines (~5,638→~6,090)
- Updated `models.py` description to mention SubjectCategory model
- Added design docs to Related Documentation table
- Updated audit date and version

**v3.11 (February 7, 2026 - Session 74 End-of-Session):**
- Added `prompts/utils/related.py` - Related prompts scoring algorithm (4-factor)
- Added `prompts/templates/prompts/partials/_prompt_card_list.html` - AJAX partial for related prompts
- Updated SVG icon count: 31→32 (added `icon-clock` for trash "deleted X days ago")
- Updated Phase K icons count: 12→13 (added `icon-clock`)
- Updated audit date and version

**v3.10 (February 7, 2026 - Session 73 End-of-Session):**
- Updated Phase K status from ~98% to ~96% (video bugs documented)
- Added CSS Specificity Notes section documenting masonry-grid.css load order issue
- Documented `.trash-prompt-wrapper .trash-video-play` specificity override pattern (0,2,0 vs 0,1,0)
- Updated audit date and version

**v3.9 (February 6, 2026 - Session 70 End-of-Session):**
- Updated Phase K status from ~95% to ~98% (trash integration complete)
- Added `icon-rotate-ccw` to SVG icons (31 total, Phase K icons 11→12)
- Added 3 collections trash endpoints to Collections API section
- Updated user_views.py and user_profile.html in files documentation
- Added style.css trash collection footer styles documentation

**v3.8 (February 4, 2026 - Session 69 End-of-Session):**
- Updated Phase N4 status from ~90% to ~99% (Lighthouse 96/100/100/100)
- Added `static_root/` directory with `robots.txt` to directory structure
- Added `minify_assets.py` management command (count 19→20)
- Added Session 69 files created/modified sections
- Added 3 new N4 Implementation Status items (SEO, A11y, Minification)

**v3.7 (February 4, 2026 - Session 68 End-of-Session):**
- Updated Phase N4 status from ~97% to ~90% (SEO score regression, indexes migration pending)
- Added Session 68 files modified section (admin, upload UX, performance optimization)
- Updated N4 Implementation Status with 7 new Session 68 items
- Updated upload-core.js description (30s warning toast, ~488→~640 lines)
- Updated upload-form.js description (error message card, ~700→~1020 lines)
- Updated upload.css line count (~750→~880 lines, warning toast + error card styles)

**v3.6 (February 3, 2026 - Session 67 End-of-Session):**
- Updated Phase N4 status from ~95% to ~97% (B2 file renaming built)
- Added `prompts/utils/` package (seo.py for SEO filename generation)
- Added `prompts/services/b2_rename.py` (B2RenameService - copy-verify-delete)
- Updated service count from 10 to 11
- Added Session 67 files created/modified sections
- Updated N4 Implementation Status with 2 new Session 67 items (SEO Headings, N4h File Rename)
- Updated Files Still Pending: removed rename_b2_files_for_seo (now implemented)

**v3.5 (February 3, 2026 - Session 66 End-of-Session):**
- Updated Phase N4 status from ~90% to ~95% (SEO done, upload redesigned)
- Added Session 66 files modified section (SEO overhaul, upload redesign, CSS architecture)
- Added 5 SEO report files to docs/reports/ (audit → validation pipeline)
- Updated CSS architecture section with shared media container component
- Updated upload.css line count (~780 → ~750)
- Updated N4 Implementation Status with 3 new Session 66 items
- Updated docs/reports count (16 → 21 files)

**v3.4 (January 31, 2026 - Session 64 End-of-Session):**
- Added `collection_edit.html` to Prompts App Templates
- Updated `upload.css` description (complete rewrite, ~500→~780 lines)
- Updated CI/CD coverage threshold from 45% to 40%
- Updated test statistics (298 tests, 43% coverage)
- Updated worker dyno status: configured Standard-1X ($25/mo)
- Updated Phase N4 status from ~95% to ~90% (upload page bugs remaining)
- Updated N4 Implementation Status header to Session 64

**v3.3 (January 31, 2026 - Session 64):**
- Updated Phase N4 status: all 3 blockers resolved, worker dyno needed
- Added Procfile documentation to Deployment Structure section
- Added worker dyno to Heroku Configuration table
- Updated N4 Implementation Status with Session 64 SEO enhancements

**v3.2 (January 28, 2026 - Session 63):**
- Updated Phase N4 status to ~95% complete
- Added Session 63 SEO/AI content changes to Files Modified section
- Added base.html and content_generation.py to modified files list
- Updated N4 Implementation Status table with SEO and AI Quality items

**v3.1 (January 27, 2026 - Session 61):**
- Updated Phase N4 to ~90% complete (video submit blocker)
- Documented Session 61 file deletions: processing.js, upload-step1.js, step templates
- Updated video upload flow with ai_job_id session key
- Updated JavaScript files section (7 files now, down from 9)
- Added uncommitted changes note for video support files

**v3.0 (January 27, 2026):**
- Updated Phase N4 section to reflect Session 59 implementation
- N4a-N4d complete: processing page view, template conditionals, processing.js
- Added processing.js to JavaScript Architecture section (9 files now)
- Corrected: processing.html was NOT created (DRY - reused prompt_detail.html)
- Updated file counts and line totals

**v2.9 (January 26, 2026):**
- Added Phase N4 files section (Optimistic Upload Flow)
- Documented new files to create: tasks.py, sitemaps.py, processing.html, processing.js
- Documented files to modify: models.py, urls.py, views, settings.py
- Added new URL routes and database fields
- Added PHASE_N4_UPLOAD_FLOW_REPORT.md to Related Documentation

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
