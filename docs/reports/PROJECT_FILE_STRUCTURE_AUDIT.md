# PROJECT FILE STRUCTURE AUDIT

**Audit Date:** December 13, 2025
**Project:** PromptFinder (Django 4.2.13)
**Current Phase:** Phase I (URL Migration) - Complete
**Auditor:** Claude Code with wshobson/agents

---

## Executive Summary

This audit provides a comprehensive inventory of all files in the PromptFinder project, comparing the current state against the existing `PROJECT_FILE_STRUCTURE.md` documentation. The audit identifies discrepancies, missing documentation, and provides recommendations for improvements.

---

## Agent Usage Report

### Agents Consulted

| Agent | Rating | Focus Area |
|-------|--------|------------|
| @code-reviewer | 8.2/10 | Overall structure, file organization |
| @django-pro | 7.5/10 | Django-specific patterns, refactoring |
| @devops-troubleshooter | 7.5/10 | Deployment, CI/CD, monitoring |

### Key Agent Findings

**@code-reviewer (8.2/10):**
- Service layer architecture is excellent (9/10)
- Root directory has too many files (5/10)
- Test organization is very good (9.5/10)
- views.py at 3,929 lines needs splitting

**@django-pro (7.5/10):**
- 37 migrations should be squashed before launch
- views.py should be split into 8-10 modules
- base.html has ~800 lines of inline JavaScript
- Service pattern is correctly implemented

**@devops-troubleshooter (7.5/10):**
- No CI/CD pipeline (critical gap)
- No error monitoring (Sentry recommended)
- No uptime monitoring (UptimeRobot recommended)
- Core deployment infrastructure is solid (9/10)

---

## File Count Summary

### By Category

| Category | Count | Location |
|----------|-------|----------|
| **Python Files** | 82 | Various |
| **HTML Templates** | 40 | templates/, app templates |
| **CSS Files** | 4 | static/css/ |
| **Migrations** | 39 | prompts/ (37), about/ (2) |
| **Test Files** | 12 | prompts/tests/ |
| **Management Commands** | 17 | prompts/management/commands/ |
| **Documentation (MD)** | 138 | Root (30), docs/ (33), archive/ (75) |
| **Services** | 6 | prompts/services/ |

---

## Directory Structure

### Top-Level Directories

```
live-working-project/
├── .claude/                  # Claude Code settings
├── .github/                  # GitHub templates (NOT CI/CD)
│   └── ISSUE_TEMPLATE/
├── .venv/                    # Python virtual environment
├── about/                    # Secondary Django app
├── archive/                  # Archived documentation
├── backups/                  # Email preferences backups
├── design-references/        # UI design assets
├── docs/                     # Active documentation
├── Lighthouse-Issues/        # Performance reports
├── prompts/                  # Main Django app
├── prompts_manager/          # Django project settings
├── reports/                  # Generated CSV reports
├── scripts/                  # Utility scripts
├── static/                   # Source static files
├── staticfiles/              # Collected static (production)
└── templates/                # Global Django templates
```

---

## Detailed File Inventory

### 1. Root Directory Files

**Python Files (14):**
| File | Size | Purpose |
|------|------|---------|
| manage.py | 671B | Django management |
| env.py | 693B | Environment config |
| audit.py | 2.1KB | Utility script |
| audit_fixed.py | 2.9KB | Utility script |
| cleanup_old_tags.py | 2.1KB | Tag cleanup |
| database_audit_script.py | 11KB | DB audit |
| debug_report_form.py | 3.9KB | Debug utility |
| investigate_cloudinary_urls.py | 3.9KB | Cloudinary debug |
| investigate_placeholders.py | 2.5KB | Placeholder debug |
| refactoring_proposal.py | 4.5KB | Code proposal |
| test_content_generation.py | 4.7KB | Test script |
| test_rate_limit.py | 4.6KB | Test script |
| verify_userprofile.py | 9.6KB | Verification |
| USERPROFILE_ENHANCEMENTS.py | 17KB | Enhancement script |

**Configuration Files:**
| File | Purpose |
|------|---------|
| Procfile | Heroku dyno config |
| requirements.txt | Python dependencies |
| .python-version | Python version (3.12) |
| .gitignore | Git exclusions |
| db.sqlite3 | Local SQLite database |

**Documentation (30 MD files):**
| File | Lines | Purpose |
|------|-------|---------|
| CLAUDE.md | 3,800+ | Master project docs |
| PROJECT_FILE_STRUCTURE.md | 601 | File structure docs |
| PHASE_A_E_GUIDE.md | 2,000+ | Implementation guide |
| README.md | ~200 | Project README |
| HEROKU_SCHEDULER_SETUP.md | 758 | Scheduler config |
| CC_SPEC_TEMPLATE.md | ~100 | CC specification template |
| + 24 other session/phase reports | Various | Historical docs |

---

### 2. prompts/ (Main Django App)

**Core Python Files (13):**
| File | Size | Lines | Purpose |
|------|------|-------|---------|
| models.py | 67KB | ~2,026 | Database models |
| views.py | 147KB | ~3,929 | View functions |
| admin.py | 48KB | ~1,293 | Admin configuration |
| forms.py | 26KB | ~700 | Django forms |
| urls.py | 4.7KB | ~120 | URL routing |
| constants.py | 13KB | ~350 | AI generator metadata |
| signals.py | 7KB | ~180 | Django signals |
| email_utils.py | 6.6KB | ~170 | Email helpers |
| middleware.py | 4KB | ~100 | Custom middleware |
| apps.py | 468B | ~12 | App config |
| tests.py | 60B | Empty | (Tests in tests/) |
| views_admin.py | 5.3KB | ~140 | Admin views |
| __init__.py | 0B | Empty | Package init |

**Services Directory (7 files):**
| File | Size | Purpose |
|------|------|---------|
| __init__.py | 598B | Service exports |
| cloudinary_moderation.py | 17KB | Cloudinary AI moderation |
| content_generation.py | 14KB | GPT-4o content generation |
| leaderboard.py | 12KB | Leaderboard calculations |
| openai_moderation.py | 7KB | OpenAI text moderation |
| orchestrator.py | 21KB | Moderation orchestration |
| profanity_filter.py | 7KB | Profanity detection |

**Template Tags (3 files):**
| File | Purpose |
|------|---------|
| __init__.py | Package init |
| cloudinary_tags.py | Cloudinary URL transformations |
| video_tags.py | Video handling filters |

**Management Commands (17 + __init__):**
| Command | Purpose |
|---------|---------|
| cleanup_deleted_prompts.py | Daily trash cleanup |
| detect_orphaned_files.py | Cloudinary orphan detection |
| backup_email_preferences.py | Data backup |
| restore_email_preferences.py | Data restore |
| auto_draft_no_media.py | Auto-draft prompts |
| create_bulk_data.py | Test data generation |
| create_test_users.py | Test user creation |
| diagnose_media.py | Media diagnostics |
| fix_admin_avatar.py | Avatar fixes |
| fix_cloudinary_urls.py | URL fixes |
| fix_ghost_prompts.py | Ghost prompt cleanup |
| fix_prompt_order.py | Order fixes |
| generate_slugs.py | Slug generation |
| initialize_prompt_order.py | Order initialization |
| moderate_prompts.py | Batch moderation |
| cleanup_old_tags.py | Tag cleanup |
| test_moderation.py | Moderation testing |

**Tests Directory (12 test files + __init__):**
| File | Size | Tests |
|------|------|-------|
| test_user_profiles.py | 36KB | User profile CRUD |
| test_url_cleaning.py | 26KB | URL validation |
| test_user_profile_header.py | 27KB | Profile UI |
| test_user_profile_auth.py | 21KB | Auth flows |
| test_rate_limiting.py | 19KB | Rate limiting (23 tests) |
| test_user_profile_javascript.py | 19KB | JS functionality |
| test_generator_page.py | 12KB | Generator pages |
| test_follows.py | 7KB | Follow system |
| test_prompts_hub.py | 8KB | Prompts hub |
| test_inspiration.py | 7KB | Inspiration page |
| test_url_migration.py | 6KB | URL redirects |
| test_email_preferences_safety.py | 5KB | Email safety |

**Migrations (37 files):**
- 0001_initial.py through 0037_add_view_rate_limit.py
- Latest 5: SiteSettings (0035-0037), DeletedPrompt (0033), AI gen indexes (0034)

**Templates (20 + 2 partials):**
| Template | Size | Purpose |
|----------|------|---------|
| prompt_list.html | 70KB | Homepage with masonry grid |
| user_profile.html | 59KB | User profile page |
| prompt_detail.html | 37KB | Prompt detail view |
| upload_step2.html | 29KB | Upload form |
| ai_generator_category.html | 18KB | AI generator pages |
| debug_no_media.html | 18KB | Admin debug |
| media_issues.html | 19KB | Admin media issues |
| leaderboard.html | 15KB | Leaderboard page |
| trash_bin.html | 15KB | Trash bin |
| prompt_edit.html | 13KB | Edit prompt |
| edit_profile.html | 13KB | Edit profile |
| prompt_create.html | 12KB | Create prompt |
| upload_step1.html | 10KB | Upload step 1 |
| settings_notifications.html | 8KB | Email settings |
| unsubscribe.html | 8KB | Unsubscribe |
| inspiration_index.html | 7KB | Prompts hub |
| collaborate.html | 5KB | Collaboration |
| prompt_gone.html | 4KB | 410 Gone page |
| prompt_temporarily_unavailable.html | 4KB | Temp unavailable |
| comment_edit.html | 647B | Comment editing |
| **Partials:** | | |
| _masonry_grid.html | 16KB | Grid partial |
| _prompt_card.html | 13KB | Card partial |

---

### 3. prompts_manager/ (Django Settings)

| File | Size | Purpose |
|------|------|---------|
| settings.py | ~15KB | Django configuration |
| urls.py | ~3KB | Root URL config |
| wsgi.py | ~400B | WSGI entry point |
| asgi.py | ~400B | ASGI entry point |
| __init__.py | 0B | Package init |
| urls_backup.py | ~3KB | URL backup |
| urls_test.py | ~3KB | Test URLs |

---

### 4. about/ (Secondary App)

| File | Size | Purpose |
|------|------|---------|
| models.py | ~1KB | About model |
| views.py | ~500B | About view |
| urls.py | ~200B | URL routing |
| admin.py | ~500B | Admin config |
| apps.py | ~200B | App config |
| tests.py | ~100B | Tests (empty) |
| __init__.py | 0B | Package init |
| migrations/ | 2 files | Schema migrations |
| templates/about/about.html | 4.6KB | About page |

---

### 5. templates/ (Global Templates)

| File | Size | Purpose |
|------|------|---------|
| base.html | 69KB | Base template with navbar |
| 404.html | 2KB | Not found page |
| 429.html | 2.8KB | Rate limit page |

**templates/account/ (6 files):**
- login.html, logout.html, signup.html
- password_reset.html, password_reset_done.html, base.html

**templates/admin/ (8 files):**
- base_site.html, custom_index.html, index.html
- moderation_dashboard.html, nav_sidebar.html
- profanity_bulk_import.html, profanity_word_changelist.html
- trash_dashboard.html

---

### 6. static/ Directory

**CSS Files (4 total):**
| File | Size | Purpose |
|------|------|---------|
| static/css/style.css | 60KB | Main styles |
| static/css/navbar.css | 29KB | Navbar styles |
| static/css/components/masonry-grid.css | 5.5KB | Grid component |
| static/css/pages/prompt-list.css | 6.3KB | Homepage styles |

**Images:**
- favicon.ico
- default.jpg, nobody.jpg
- about-page-image.jpg
- placeholder-prompt.svg
- for-readme/ (documentation images)

**staticfiles/ (200+ files):**
- Collected from Django admin, Cloudinary widget, etc.
- Generated by `collectstatic` command

---

### 7. docs/ Directory

**Root docs/ (17 files):**
- CC_COMMUNICATION_PROTOCOL.md
- DEPLOYMENT_CHECKLIST.md
- DJANGO_ORM_SOFT_DELETE_PATTERNS.md
- SEO_KEYWORD_RESEARCH_2025.md
- 301_REDIRECT_MIGRATION_PROTOCOL.md
- Various keyword and redirect guides

**docs/reports/ (16 files):**
- Phase G Part A/B/C reports
- Phase I documentation reports
- Profile edit bug fix reports
- Security hardening reports

**docs/guides/ (1 file):**
- HANDOFF_TEMPLATE_STRUCTURE.md

---

### 8. archive/ Directory (75+ files)

```
archive/
├── phase-e/                 # Phase E completion docs
│   ├── completion-reports/ (9 files)
│   ├── forms-implementation/ (4 files)
│   └── testing/ (3 files)
├── phase3-seo/              # Phase 3 SEO docs
├── bug-fixes/               # Bug fix reports (7 files)
├── feature-implementations/ # Feature docs (2 files)
├── rate-limiting/           # Rate limiting docs (3 files)
├── needs-review/            # Pending review (9 files)
└── marked-for-deletion/     # Deletion candidates (21 files)
```

---

## Comparison with Existing Documentation

### Discrepancies Found

| Category | Existing Doc | Actual | Difference |
|----------|-------------|--------|------------|
| Total Tests | 69+ | 70+ (Phase I) | +1 test |
| Migrations | "37" | 37 (correct) | None |
| Templates | "20+" | 40 | Undercounted |
| Python files | "30+" | 82 | Undercounted |
| Management Commands | 2 mentioned | 17 actual | Undercounted |
| Django Version | 4.2.13 | 4.2.13 | Correct |

### Missing from Existing Documentation

1. **Phase I files:**
   - test_prompts_hub.py
   - test_url_migration.py
   - test_inspiration.py (rewritten)
   - test_generator_page.py (updated)

2. **Services not fully documented:**
   - leaderboard.py (Phase G)
   - Full service architecture

3. **Recent templates:**
   - leaderboard.html
   - inspiration_index.html updates

4. **Root utility scripts:**
   - 14 Python scripts at root not documented

---

## Critical Issues Identified

### 1. Views.py Size (CRITICAL)

**Current:** 147KB, ~3,929 lines
**Recommendation:** Split into modules

```
prompts/views/
├── __init__.py          # Re-exports
├── prompt_views.py      # CRUD operations
├── upload_views.py      # Upload flow
├── user_views.py        # Profile, settings
├── social_views.py      # Follows, likes, comments
├── admin_views.py       # Admin operations
├── api_views.py         # AJAX endpoints
└── leaderboard_views.py # Leaderboard
```

### 2. Root Directory Clutter (HIGH)

**Problem:** 30 MD files + 14 Python scripts at root

**Recommendation:**
- Move Python scripts to `/scripts/`
- Move phase reports to `/docs/reports/`
- Keep only: CLAUDE.md, README.md, PROJECT_FILE_STRUCTURE.md

### 3. No CI/CD Pipeline (CRITICAL)

**Missing:** .github/workflows/ directory with test/deploy automation

**Recommendation:** Add GitHub Actions for:
- Running tests on PR
- Deployment to Heroku on merge
- Security scanning

### 4. No Error Monitoring (HIGH)

**Missing:** Sentry integration

**Recommendation:** Add sentry-sdk to requirements.txt

---

## Recommendations

### Immediate (This Week)

1. **Update PROJECT_FILE_STRUCTURE.md** with accurate counts
2. **Add runtime.txt** if missing
3. **Move root Python scripts** to `/scripts/`

### Short-Term (1-2 Weeks)

4. **Set up Sentry** for error monitoring
5. **Set up UptimeRobot** for availability monitoring
6. **Create CI/CD pipeline** with GitHub Actions

### Medium-Term (1 Month)

7. **Split views.py** into domain-based modules
8. **Squash migrations** before production launch
9. **Extract base.html JavaScript** to static files

---

## Appendix: Full File Tree

```
live-working-project/
├── .claude/
│   └── settings.local.json
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── user-story-template.md
├── about/
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_about_profile_image_alter_about_title.py
│   │   └── __init__.py
│   ├── templates/about/
│   │   └── about.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── archive/
│   ├── bug-fixes/ (7 files)
│   ├── feature-implementations/ (2 files)
│   ├── marked-for-deletion/ (21 files)
│   ├── needs-review/ (9 files)
│   ├── phase-e/ (16 files)
│   ├── phase3-seo/ (9 files)
│   ├── rate-limiting/ (3 files)
│   └── README.md
├── backups/
│   └── email_preferences_backup_*.json (4 files)
├── design-references/
│   ├── UI_STYLE_GUIDE.md
│   └── ui-design-*.png (7 images)
├── docs/
│   ├── archived/ (2 files)
│   ├── bug_reports/ (1 file)
│   ├── forms/ (2 files)
│   ├── guides/ (1 file)
│   ├── reports/ (16 files)
│   ├── specifications/ (1 file)
│   └── *.md (17 files)
├── Lighthouse-Issues/
│   └── *.json (1 file)
├── prompts/
│   ├── fixtures/
│   │   └── sample_prompts.json
│   ├── management/
│   │   └── commands/ (17 commands + READMEs)
│   ├── migrations/ (37 migrations)
│   ├── services/ (7 files)
│   ├── templates/prompts/ (20 + 2 partials)
│   ├── templatetags/ (3 files)
│   ├── tests/ (12 test files)
│   ├── admin.py
│   ├── apps.py
│   ├── constants.py
│   ├── email_utils.py
│   ├── forms.py
│   ├── middleware.py
│   ├── models.py
│   ├── signals.py
│   ├── urls.py
│   ├── views.py
│   └── views_admin.py
├── prompts_manager/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── urls_backup.py
│   ├── urls_test.py
│   └── wsgi.py
├── reports/
│   └── *.csv (4 reports)
├── scripts/
│   └── *.sh, *.py, *.html (7 files)
├── static/
│   ├── css/
│   │   ├── components/ (1 file)
│   │   ├── pages/ (1 file)
│   │   ├── navbar.css
│   │   └── style.css
│   ├── images/ (50+ files)
│   ├── js/ (empty)
│   └── favicon.ico
├── staticfiles/ (200+ collected files)
├── templates/
│   ├── account/ (6 files)
│   ├── admin/ (8 files)
│   ├── 404.html
│   ├── 429.html
│   └── base.html
├── .gitignore
├── .python-version
├── CC_SPEC_TEMPLATE.md
├── CLAUDE.md
├── db.sqlite3
├── manage.py
├── Procfile
├── PROJECT_FILE_STRUCTURE.md
├── PROJECT_FILE_STRUCTURE_AUDIT.md
├── README.md
├── requirements.txt
└── [30+ session/phase MD files]
```

---

## Audit Metadata

| Field | Value |
|-------|-------|
| **Audit Date** | December 13, 2025 |
| **Audit Tool** | Claude Code |
| **Agents Used** | @code-reviewer, @django-pro, @devops-troubleshooter |
| **Average Rating** | 7.7/10 |
| **Files Scanned** | 600+ |
| **Directories Scanned** | 40+ |
| **Documentation Created** | This file |

---

**END OF AUDIT**
