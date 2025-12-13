# PROJECT FILE STRUCTURE

**Last Updated:** December 13, 2025
**Project:** PromptFinder (Django 4.2.13)
**Current Phase:** Phase I (URL Migration) - Complete
**Total Tests:** 70+ passing

---

## Quick Statistics

| Category | Count | Location |
|----------|-------|----------|
| **Python Files** | 82 | Various directories |
| **HTML Templates** | 41 | templates/, prompts/templates/, about/templates/ |
| **CSS Files** | 4 | static/css/ |
| **Migrations** | 38 | prompts/migrations/ (37), about/migrations/ (1) |
| **Test Files** | 13 | prompts/tests/ |
| **Management Commands** | 17 | prompts/management/commands/ |
| **Services** | 7 | prompts/services/ |
| **Documentation (MD)** | 138 | Root (30), docs/ (33), archive/ (75) |

---

## Complete Directory Structure

```
live-working-project/
├── .claude/                      # Claude Code settings
├── .github/                      # GitHub templates
│   └── ISSUE_TEMPLATE/
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
│   ├── migrations/               # 37 migrations + __init__.py
│   ├── services/                 # 7 service modules
│   ├── templates/prompts/        # 22 templates
│   ├── templatetags/             # 3 template tag files
│   └── tests/                    # 13 test files
├── prompts_manager/              # Django project settings (7 files)
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reports/                      # Generated CSV reports
├── scripts/                      # Utility scripts (7 files)
├── static/                       # Source static files
│   └── css/                      # 4 CSS files (101KB total)
│       ├── components/
│       ├── pages/
│       ├── navbar.css
│       └── style.css
├── staticfiles/                  # Collected static (production)
└── templates/                    # Global Django templates (18 files)
    ├── account/                  # 6 authentication templates
    ├── admin/                    # 8 admin customization templates
    ├── registration/             # 1 template
    ├── base.html                 # Main template (69KB)
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

## Templates (41 total)

### Global Templates (templates/) - 18 files

| Template | Purpose |
|----------|---------|
| `base.html` | Main template with navbar, footer (~2000 lines) |
| `404.html` | Not found error page |
| `429.html` | Rate limit error page (WCAG AA) |
| `account/*.html` | 6 authentication templates (login, signup, logout, password reset) |
| `admin/*.html` | 8 admin customization templates |
| `registration/login.html` | Login page override |

### Prompts App Templates (prompts/templates/prompts/) - 22 files

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
| And 8 more... | Confirmation modals, reports, etc. |

### About App Templates (about/templates/about/) - 1 file

| Template | Purpose |
|----------|---------|
| `about.html` | About page |

---

## Test Files (13 total, 70+ tests)

| Test File | Tests | Focus Area |
|-----------|-------|------------|
| `test_user_profiles.py` | Multiple | User profile CRUD operations |
| `test_url_cleaning.py` | Multiple | URL validation and cleaning |
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
| `views.py` | ~3,929 | All view functions (NEEDS SPLITTING) |
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
│   └── masonry-grid.css # 255 lines - Masonry grid component
└── pages/
    └── prompt-list.css  # 304 lines - Prompt list page styles
```

**Total CSS:** ~3,484 lines across 4 files

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

| Issue | Impact | Recommended Action |
|-------|--------|-------------------|
| `views.py` at 147KB (~3,929 lines) | Maintenance difficulty | Split into 8-10 view modules |
| No CI/CD pipeline | Manual deployments | Set up GitHub Actions |
| No error monitoring | Blind to production errors | Add Sentry |
| 37 migrations | Slow migration runs | Squash before launch |
| Root directory clutter | 30+ MD files, 14 Python scripts | Move to /archive/ and /scripts/ |

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

- **Total Tests:** 70+
- **Pass Rate:** 100%
- **Coverage:** ~70% (estimated)
- **Priority Areas:** CRUD, authentication, rate limiting, URL migration

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

*This document is updated after major structural changes. Last audit: December 13, 2025.*

**Version:** 2.0
**Audit Date:** December 13, 2025
**Maintained By:** Project Owner
