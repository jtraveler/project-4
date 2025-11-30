# PROJECT FILE STRUCTURE

**Last Updated:** November 30, 2025
**Project:** PromptFinder (Django 4.2.13)
**Total Tests:** 69+ passing (46 core + 23 rate limiting)
**Phase:** E Complete, Phase F Complete, Draft Mode System Complete (Nov 29, 2025)

---

## Directory Structure

```
live-working-project/
├── about/                     # About app
│   ├── migrations/
│   ├── templates/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── docs/                      # Project documentation
│   ├── bug_reports/
│   ├── implementation_reports/
│   ├── specifications/
│   └── CC_COMMUNICATION_PROTOCOL.md
├── prompts/                   # Main Django app
│   ├── management/
│   │   └── commands/
│   │       ├── cleanup_deleted_prompts.py
│   │       ├── detect_orphaned_files.py
│   │       └── README_*.md
│   ├── migrations/
│   ├── templates/
│   │   └── prompts/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_forms.py
│   │   ├── test_rate_limiting.py
│   │   ├── test_user_profile_header.py
│   │   └── test_user_profile_javascript.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── constants.py           # AI generator metadata (Phase 3)
│   ├── email_utils.py
│   ├── forms.py
│   ├── middleware.py
│   ├── models.py
│   ├── signals.py
│   ├── urls.py
│   └── views.py
├── prompts_manager/           # Project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reports/                   # Generated reports (CSV)
│   └── *.csv
├── staticfiles/               # Collected static files (production)
├── templates/                 # Global templates
│   ├── 403.html
│   ├── 404.html
│   ├── 429.html
│   ├── 500.html
│   ├── account/
│   ├── base.html
│   └── index.html
├── .gitignore
├── CLAUDE.md
├── Procfile
├── PROJECT_FILE_STRUCTURE.md
├── README.md
├── manage.py
├── requirements.txt
└── runtime.txt
```

---

## Key Files by Category

### Core Configuration

#### `prompts_manager/settings.py`
Django settings including:
- Database configuration (PostgreSQL)
- Cloudinary media storage
- Installed apps (django-allauth, django-ratelimit, etc.)
- Middleware configuration (security, rate limiting)
- Authentication settings
- Static/media file handling
- Email configuration
- Rate limiting settings (RATELIMIT_VIEW)

#### `prompts_manager/urls.py`
Root URL configuration:
- Admin panel routing
- App URL includes (prompts, about, accounts)
- Media file serving (development only)

#### `requirements.txt`
Python dependencies including:
- Django 4.2.13
- cloudinary
- django-allauth
- django-ratelimit
- gunicorn
- whitenoise
- psycopg2

#### `Procfile`
Heroku deployment configuration:
- Web dyno command (gunicorn)
- Static file collection

### Main Application (prompts/)

#### `prompts/models.py`
Database models:
- **Prompt:** Core content model with soft delete (deleted_at, deleted_by, deletion_reason, original_status)
- **UserProfile:** User profile data (bio, avatar, social links)
- **EmailPreferences:** Notification preferences (8 toggles)
- **PromptReport:** Content reporting system
- **Comment:** User comments on prompts
- Custom managers (PromptManager for active, all_objects for deleted)

#### `prompts/views.py`
View functions and class-based views:
- Prompt CRUD operations (create, read, update, delete, restore)
- Upload flow (step1, step2, submit, cancel, extend)
- Trash bin management
- User profile pages
- Email preferences dashboard
- Unsubscribe handler
- Report submission
- **AI generator category pages (Phase 3):** ai_generator_category view with filtering/sorting
- Rate limiting error page (ratelimited view)
- Comment moderation
- **Draft Mode (Nov 2025):** `prompt_publish` view for publishing drafts

#### `prompts/middleware.py`
Custom Django middleware:
- **RatelimitMiddleware:** Intercepts Ratelimited exceptions from django-ratelimit 4.x and returns branded 429.html template
- Processes exceptions raised by @ratelimit decorator
- Returns TemplateResponse for testability
- Required because RATELIMIT_VIEW setting not auto-respected in 4.x

#### `prompts/forms.py`
Django forms:
- PromptForm (create/edit prompts)
- CommentForm (user comments)
- EmailPreferencesForm (notification settings)
- UserProfileForm (profile editing)
- PromptReportForm (content reporting)

#### `prompts/admin.py`
Django admin configuration:
- Prompt admin (list display, filters, actions)
- UserProfile admin (inline editing)
- EmailPreferences admin (organized fieldsets)
- PromptReport admin (moderation tools)
- Comment admin (moderation)
- **Draft Mode (Nov 2025):** `make_draft` bulk action for marking prompts as drafts

#### `prompts/signals.py`
Django signals:
- Auto-create UserProfile on user creation
- Auto-create EmailPreferences on user creation
- Cloudinary cleanup on prompt deletion

#### `prompts/constants.py`
AI generator metadata and validation (Phase 3 SEO):
- **AI_GENERATORS:** Dictionary mapping 11 AI generators to metadata
- Generator metadata: name, description, official_website, icon, choice_value
- Used by ai_generator_category view for validation and display
- Prevents hardcoding generator data across multiple files

#### `prompts/email_utils.py`
Email helper functions:
- should_send_email() - Check user preferences
- get_unsubscribe_url() - Generate unsubscribe links
- send_notification_email() - Wrapper for preference-aware emails

#### `prompts/urls.py`
URL routing for prompts app:
- Prompt CRUD endpoints
- Upload flow endpoints
- Trash bin endpoints
- User profile endpoints
- Email preferences endpoints
- Report endpoints
- **AI generator category endpoints (Phase 3):** `/ai/<slug:generator_slug>/`
- Rate limit error page endpoint

### Middleware

#### `prompts/middleware.py`
**Purpose:** Custom Django middleware for rate limiting exception handling

**Why Needed:** django-ratelimit 4.x raises Ratelimited exceptions that need to be caught and converted to branded 429 responses. The RATELIMIT_VIEW setting is not automatically respected in 4.x, requiring custom middleware.

**Implementation:**
- Intercepts `Ratelimited` exceptions in `process_exception()`
- Returns `TemplateResponse` with `templates/429.html`
- Uses TemplateResponse (not HttpResponse) for testability
- Must be placed in MIDDLEWARE list after SecurityMiddleware

**Key Code:**
```python
class RatelimitMiddleware:
    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            return TemplateResponse(request, '429.html', status=429)
```

**Added:** Session 4 (October 26, 2025)
**Lines:** 67 lines

### Tests

#### `prompts/tests/test_rate_limiting.py`
**Purpose:** Comprehensive rate limiting test suite

**Coverage:**
- Decorator application (23 tests)
- Middleware exception handling
- 429 template rendering
- Rate limit enforcement (unsubscribe view)
- TemplateResponse validation
- Security headers
- Edge cases (anonymous users, premium users)

**Key Test Categories:**
1. Middleware tests (exception handling, 429 responses)
2. View tests (ratelimited() view rendering)
3. Integration tests (decorator + middleware + template)
4. Unsubscribe rate limiting (3/min, 20/hour)
5. Template content validation

**Statistics:**
- 23 tests total
- 100% passing
- Added in Session 4 (October 26, 2025)
- Lines: 413 lines

**Why Important:** Ensures rate limiting works correctly after 3 critical bugs were discovered and fixed in Session 2. Tests verify:
- Decorator placement on correct functions
- Middleware catches exceptions
- 429.html template renders correctly
- Status codes are 429 (not 403)

#### `prompts/tests/test_models.py`
Tests for database models:
- Prompt model (CRUD, soft delete, restore, hard delete)
- UserProfile model (creation, updates)
- EmailPreferences model (defaults, preferences)
- Custom managers (objects vs all_objects)

#### `prompts/tests/test_views.py`
Tests for view functions:
- Upload flow (step1, step2, submit)
- Trash bin operations
- User profile pages
- Email preferences
- Report submission

#### `prompts/tests/test_forms.py`
Tests for form validation:
- Field validation
- Clean methods
- Form rendering

#### `prompts/tests/test_user_profile_header.py`
Tests for user profile header UI:
- Tab navigation
- Overflow arrow visibility
- Responsive design

#### `prompts/tests/test_user_profile_javascript.py`
Tests for profile JavaScript:
- Arrow visibility logic
- Scroll detection
- Keyboard navigation

### Templates

#### `templates/429.html`
**Purpose:** Branded rate limit exceeded error page

**Features:**
- User-friendly messaging ("Too Many Requests")
- Context explanation (rate limits maintain site performance)
- Font Awesome hourglass icon
- Retry-after information display
- Primary CTA: Return to Homepage
- Secondary CTA: Go Back
- Support link
- Mobile-responsive Bootstrap 5 layout
- WCAG 2.1 Level AA compliant
- Aria labels and screen reader support

**Why Needed:** django-ratelimit 4.x returns generic 429 errors without custom templates. This provides a branded, accessible experience when users hit rate limits.

**Variables Available:**
- `error_title` (default: "Too Many Requests")
- `error_message` (default: friendly explanation)
- `retry_after` (optional: time until retry allowed)

**Added:** Session 4 (October 26, 2025)
**Lines:** 64 lines

**Key Sections:**
```html
<div class="card shadow-sm" role="alert" aria-live="polite">
    <i class="fas fa-hourglass-half fa-4x text-warning"></i>
    <h1>{{ error_title|default:"Too Many Requests" }}</h1>
    <p>{{ error_message|default:"You've made too many requests..." }}</p>
    {% if retry_after %}
        <div class="alert alert-info">Please try again in: {{ retry_after }}</div>
    {% endif %}
</div>
```

#### `templates/base.html`
Base template with:
- Bootstrap 5 layout
- Navigation bar
- Alert messages section
- Footer
- Block structure for child templates

#### `templates/account/`
Django-allauth authentication templates:
- login.html
- signup.html
- logout.html
- password_reset.html

### Management Commands

#### `prompts/management/commands/cleanup_deleted_prompts.py`
**Purpose:** Automated trash cleanup (5 days free, 30 days premium)

**Features:**
- Deletes expired prompts from database
- Removes Cloudinary assets
- Email summaries to admins
- Dry-run mode for testing
- Comprehensive logging

**Schedule:** Daily at 3:00 AM UTC (Heroku Scheduler)
**Runtime:** ~10-30 seconds
**Lines:** 271 lines

#### `prompts/management/commands/detect_orphaned_files.py`
**Purpose:** Cloudinary orphan and missing image detection

**Features:**
- Scans for files without database entries (orphans)
- Scans for prompts without valid Cloudinary files (missing images)
- Date filtering (--days N or --all)
- CSV report generation
- API usage monitoring
- Two-section reporting (orphans + missing)
- Differentiates ACTIVE vs DELETED prompts

**Schedule:** Daily at 4:00 AM UTC (Heroku Scheduler)
**Runtime:** ~10-60 seconds
**Lines:** 899 lines

### Documentation

#### `CLAUDE.md`
Comprehensive project documentation:
- Project overview and goals
- Technical stack and infrastructure
- Development phases (A through I)
- Known issues and technical debt
- Decisions made
- Monetization strategy
- Content moderation policies
- Upload flow architecture
- SEO strategy
- User management
- Feature specifications

**Updated:** October 26, 2025 (Phase E completion)

#### `docs/CC_COMMUNICATION_PROTOCOL.md`
Communication standards for Claude Code sessions:
- Role and responsibilities
- Reading specifications
- When to ask questions
- Reporting results
- Testing requirements
- Error handling

#### `docs/bug_reports/`
Detailed bug reports:
- phase_e_task3_comment_field_fix.md
- Other historical bug documentation

#### `docs/specifications/`
Feature specifications:
- phase_e_arrow_visibility_spec.md
- phase_e_arrow_refinements_spec.md
- PHASE_E_SPEC.md

#### `docs/implementation_reports/`
Implementation summaries:
- phase_e_complete_report.md
- PHASE_E_IMPLEMENTATION_REPORT.md

---

## Recent Additions - Phase E Rate Limiting (Session 4)

**Date:** October 26, 2025
**Purpose:** Fix 3 critical rate limiting bugs discovered in Session 2

### New Files Created:

1. **prompts/middleware.py** (67 lines)
   - Custom RatelimitMiddleware class
   - Intercepts Ratelimited exceptions
   - Returns branded 429.html template
   - Required for django-ratelimit 4.x compatibility

2. **templates/429.html** (64 lines)
   - Branded rate limit error page
   - User-friendly messaging
   - Bootstrap 5 responsive design
   - WCAG 2.1 Level AA accessible
   - Retry-after information display

3. **prompts/tests/test_rate_limiting.py** (413 lines, 23 tests)
   - Comprehensive rate limiting test suite
   - Middleware exception handling tests
   - View rendering tests (ratelimited view)
   - Integration tests (decorator + middleware + template)
   - Unsubscribe rate limit enforcement tests
   - 100% passing

### Files Modified:

1. **prompts_manager/settings.py**
   - Added RatelimitMiddleware to MIDDLEWARE list
   - Added RATELIMIT_VIEW setting (points to prompts:ratelimited)

2. **prompts/views.py**
   - Created ratelimited() error view
   - Returns TemplateResponse with 429.html

3. **prompts/urls.py**
   - Added /rate-limited/ endpoint
   - Maps to prompts:ratelimited view

### Bugs Fixed:

1. **Missing ratelimited() view** - Created custom error view
2. **Decorator not triggering** - Created RatelimitMiddleware
3. **HTTP 403 instead of 429** - Fixed decorator placement and middleware implementation

### Testing Results:

- **Unit Tests:** 23/23 passing (rate limiting suite)
- **Integration Tests:** 46/46 passing (existing tests)
- **Total:** 69/69 passing (100% pass rate)
- **Manual Testing:** 6/6 browser tests passed
- **Agent Testing:** 9.5/10 average (@django-pro @security @code-quality)

---

## File Statistics

**Total Files:** 100+ files across project
**Core Python Files:** 30+ files
**Templates:** 20+ HTML files
**Tests:** 69+ tests across 7 test files
**Documentation:** 15+ markdown files
**Management Commands:** 2 commands with READMEs

**Lines of Code (Approximate):**
- Python: 8,000+ lines
- Templates: 3,000+ lines
- Tests: 2,000+ lines
- Documentation: 10,000+ lines

---

## Testing Overview

### Test Categories:

1. **Model Tests** (test_models.py)
   - Prompt CRUD operations
   - Soft delete functionality
   - Custom managers
   - User profile creation
   - Email preferences defaults

2. **View Tests** (test_views.py)
   - Upload flow endpoints
   - Trash bin operations
   - User profile pages
   - Email preferences
   - Authentication requirements

3. **Form Tests** (test_forms.py)
   - Field validation
   - Clean methods
   - Form rendering

4. **Rate Limiting Tests** (test_rate_limiting.py)
   - Middleware exception handling
   - 429 template rendering
   - Decorator application
   - Rate limit enforcement
   - Security headers

5. **UI Tests** (test_user_profile_header.py, test_user_profile_javascript.py)
   - Profile header layout
   - JavaScript functionality
   - Responsive design
   - Arrow visibility logic

### Test Execution:

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

### Coverage Goals:

- **Current:** 69+ tests passing
- **Coverage:** 70%+ (estimated)
- **Priority:** Critical paths covered (CRUD, auth, rate limiting)
- **Future:** Expand to 80%+ coverage in Phase F

---

## Deployment Structure

### Heroku Configuration:

**Dynos:**
- Web: Eco dyno ($5/month)
- Worker: None (scheduled tasks use web dyno hours)

**Add-ons:**
- Heroku PostgreSQL Mini ($5/month)
- Heroku Scheduler (free)

**Environment Variables:**
- DATABASE_URL (PostgreSQL connection)
- CLOUDINARY_URL (media storage)
- SECRET_KEY (Django secret)
- ADMIN_EMAIL (notification recipient)
- DEBUG (False in production)

**Scheduled Jobs:**
1. cleanup_deleted_prompts (daily 3:00 AM UTC)
2. detect_orphaned_files --days 7 (daily 4:00 AM UTC)

### Static Files:

- Collected by `python manage.py collectstatic`
- Served by WhiteNoise in production
- Cloudinary for media files (images/videos)

---

**END OF PROJECT_FILE_STRUCTURE.md**

*This document tracks all project files and their purposes. Update when adding new files or significant changes to structure.*

**Version:** 1.0
**Created:** October 26, 2025
**Last Updated:** October 26, 2025
**Maintained By:** Project Owner
