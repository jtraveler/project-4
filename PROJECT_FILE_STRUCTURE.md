# PROJECT FILE STRUCTURE

**Last Updated:** December 27, 2025
**Project:** PromptFinder (Django 5.2.9)
**Current Phase:** Phase K Collections (~60% Complete)
**Total Tests:** 234 passing (46% coverage)

---

## Quick Statistics

| Category | Count | Location |
|----------|-------|----------|
| **Python Files** | 92 | Various directories |
| **HTML Templates** | 42 | templates/, prompts/templates/, about/templates/ |
| **CSS Files** | 6 | static/css/ |
| **JavaScript Files** | 4 | static/js/ |
| **SVG Icons** | 30 | static/icons/sprite.svg |
| **Migrations** | 40 | prompts/migrations/ (39), about/migrations/ (1) |
| **Test Files** | 12 | prompts/tests/ |
| **Management Commands** | 17 | prompts/management/commands/ |
| **Services** | 7 | prompts/services/ |
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
│   ├── migrations/               # 39 migrations + __init__.py
│   ├── services/                 # 7 service modules
│   ├── templates/prompts/        # 23 templates
│   │   └── partials/             # Partial templates
│   │       ├── _masonry_grid.html
│   │       ├── _prompt_card.html
│   │       └── _collection_modal.html  # Collections modal (Phase K)
│   ├── templatetags/             # 3 template tag files
│   ├── tests/                    # 12 test files
│   └── views/                    # 12 view modules (refactored)
│       ├── __init__.py           # Package exports
│       ├── admin_views.py        # Admin dashboard views
│       ├── auth_views.py         # Authentication views
│       ├── collection_views.py   # Collection API and page views (Phase K)
│       ├── comment_views.py      # Comment CRUD operations
│       ├── core_views.py         # Homepage, detail, list views
│       ├── leaderboard_views.py  # Leaderboard functionality
│       ├── moderation_views.py   # Content moderation views
│       ├── profile_views.py      # User profile views
│       ├── settings_views.py     # User settings views
│       ├── social_views.py       # Follow, like, share views
│       └── upload_views.py       # Upload workflow views
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

## Management Commands (17 total)

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

---

## Service Layer Architecture (7 modules)

```
prompts/services/
├── __init__.py              # Service exports
├── cloudinary_moderation.py # Cloudinary AI moderation (AWS Rekognition)
├── content_generation.py    # GPT-4o content generation for uploads
├── leaderboard.py           # Leaderboard calculations (Phase G)
├── openai_moderation.py     # OpenAI text moderation API
├── orchestrator.py          # Moderation orchestration (multi-layer)
└── profanity_filter.py      # Profanity detection and filtering
```

### Service Descriptions

| Service | Description | Cost |
|---------|-------------|------|
| **cloudinary_moderation** | Cloudinary AI Vision for image/video moderation | ~$5-10/1000 images |
| **content_generation** | GPT-4o-mini for AI-generated titles, descriptions, tags | ~$0.00255/upload |
| **leaderboard** | User ranking by views, activity, engagement | N/A |
| **openai_moderation** | OpenAI text moderation API | FREE |
| **orchestrator** | Multi-layer moderation coordination | Combined |
| **profanity_filter** | Custom profanity word detection | N/A |

---

## Views Package Architecture (12 modules)

*Refactored December 2025 - Previously a single 3,929-line views.py file*

```
prompts/views/
├── __init__.py           # Package exports (all public views)
├── admin_views.py        # Admin dashboard, debug pages, bulk actions
├── auth_views.py         # Login, logout, registration helpers
├── collection_views.py   # Collection API and page views (Phase K)
├── comment_views.py      # Comment CRUD, moderation actions
├── core_views.py         # PromptList, prompt_detail, homepage
├── leaderboard_views.py  # Leaderboard rankings, filters
├── moderation_views.py   # Content review, appeals, flags
├── profile_views.py      # User profiles, settings, avatar
├── settings_views.py     # Notification preferences, account settings
├── social_views.py       # Follow/unfollow, likes, shares
└── upload_views.py       # Two-step upload, AI generation, validation
```

### Module Descriptions

| Module | Functions | Purpose |
|--------|-----------|---------|
| **admin_views** | ~15 | Admin dashboards, media issues, trash management |
| **auth_views** | ~5 | Authentication helpers, session management |
| **collection_views** | ~8 | Collection CRUD, API endpoints (add/remove prompts) |
| **comment_views** | ~8 | Comment CRUD, approval, deletion |
| **core_views** | ~12 | Homepage, prompt detail, list views, search |
| **leaderboard_views** | ~4 | Rankings, time filters, user stats |
| **moderation_views** | ~10 | Review queues, appeals, content flags |
| **profile_views** | ~8 | Profile pages, edit forms, stats |
| **settings_views** | ~6 | Email preferences, account settings |
| **social_views** | ~10 | Follow system, likes, shares, reports |
| **upload_views** | ~12 | Step 1/2 upload, AI generation, validation |

---

## Templates (42 total)

### Global Templates (templates/) - 18 files

| Template | Purpose |
|----------|---------|
| `base.html` | Main template with navbar, footer (~2000 lines) |
| `404.html` | Not found error page |
| `429.html` | Rate limit error page (WCAG AA) |
| `account/*.html` | 6 authentication templates (login, signup, logout, password reset) |
| `admin/*.html` | 8 admin customization templates |
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
| And 8 more... | Confirmation modals, reports, etc. |

### About App Templates (about/templates/about/) - 1 file

| Template | Purpose |
|----------|---------|
| `about.html` | About page |

---

## Test Files (12 files, 234 tests)

| Test File | Tests | Focus Area |
|-----------|-------|------------|
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
| `constants.py` | ~241 | AI generator metadata |
| `email_utils.py` | ~100 | Email helper functions |

---

## CSS Architecture

```
static/css/
├── navbar.css           # 1,136 lines - Extracted navbar styles
├── style.css            # 1,789 lines - Main stylesheet
├── components/
│   ├── icons.css        # ~250 lines - SVG icon system (Phase J.2)
│   └── masonry-grid.css # 255 lines - Masonry grid component
└── pages/
    ├── prompt-detail.css # 1,063 lines - Prompt detail page (Phase J.1)
    └── prompt-list.css   # 304 lines - Prompt list page styles
```

**Total CSS:** ~4,797 lines across 6 files

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
└── prompt-detail.js      # ~400 lines - Prompt detail interactions (Phase J.1)
```

### JavaScript Files

| File | Lines | Purpose |
|------|-------|---------|
| **collections.js** | ~760 | Collections modal, API integration, thumbnail grids |
| **navbar.js** | ~650 | Dropdowns, search, mobile menu, scroll |
| **prompt-detail.js** | ~400 | Like toggle, copy button, comments, delete modal |
| **like-button.js** | ~155 | Centralized like handler with optimistic UI |

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

**Total JavaScript:** ~1,965 lines across 4 files
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

---

**END OF PROJECT_FILE_STRUCTURE.md**

*This document is updated after major structural changes. Last audit: December 27, 2025.*

**Version:** 2.3
**Audit Date:** December 27, 2025
**Maintained By:** Mateo Johnson - Prompt Finder
