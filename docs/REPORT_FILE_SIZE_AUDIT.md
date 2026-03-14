# REPORT_FILE_SIZE_AUDIT.md
# Session 128 — March 14, 2026

## Summary

Audited all Python, JavaScript, HTML, and CSS files in the codebase. Total files
scanned: ~120+ across 6 directories. Found **7 files in the 🔴 Critical tier**
(2000+ lines, never edit directly), **8 files in the 🟠 High Risk tier**
(1200–1999 lines), **13 files in the 🟡 Caution tier** (800–1199 lines), and
several files in the ✅ Safe tier that are growing and should be watched.

---

## 🔴 Critical (2000+ lines) — Never Edit Directly

Strategy: Read-only access. All changes via new helper functions appended at bottom,
or create-new + rewrite-original. Use targeted greps for context.

### Python

| File | Lines | Notes |
|------|-------|-------|
| `prompts/tasks.py` | 3,451 | Core background tasks. Add new helpers at bottom; local imports only. |
| `prompts/models.py` | 3,087 | All Django models. str_replace with 5+ line anchors. Never reorganise. |
| `prompts/admin.py` | 2,366 | Admin configuration. str_replace with precise class/method anchors. |

### Test Files

| File | Lines | Notes |
|------|-------|-------|
| `prompts/tests/test_notifications.py` | 2,872 | Never edit existing tests — only append new test classes at bottom. |
| `prompts/tests/test_bulk_generator_views.py` | 2,210 | Same rule — append only. |

### CSS

| File | Lines | Notes |
|------|-------|-------|
| `static/css/style.css` | 4,466 | Global styles. Never edit directly. New overrides in page-specific CSS. |

### HTML

| File | Lines | Notes |
|------|-------|-------|
| `prompts/templates/prompts/user_profile.html` | 2,073 | Complex multi-section template. Read-only if possible; targeted str_replace with large anchors. |

---

## 🟠 High Risk (1200–1999 lines) — Avoid Direct Editing

Strategy: New file strategy preferred. If must edit, single precise str_replace only
(5+ line anchor). Never attempt structural reorganisation.

### Python

| File | Lines | Notes |
|------|-------|-------|
| `prompts/tests/test_bulk_generation_tasks.py` | 1,861 | Append new tests only. |
| `prompts/views/prompt_views.py` | 1,694 | Largest view file. Split candidates for future specs. |
| `prompts/tests/test_bulk_page_creation.py` | 1,621 | Append only. |

### HTML

| File | Lines | Notes |
|------|-------|-------|
| `prompts/templates/prompts/prompt_list.html` | 1,700 | Main gallery page. Targeted edits only. |

### CSS

| File | Lines | Notes |
|------|-------|-------|
| `static/css/pages/prompt-detail.css` | 1,549 | Large page CSS. Append new rules at end. |
| `static/css/pages/bulk-generator.css` | 1,484 | Bulk gen styles. Append only. |
| `static/css/navbar.css` | 1,268 | Navbar styles. Targeted str_replace with class anchors. |

### JavaScript

| File | Lines | Notes |
|------|-------|-------|
| `static/js/bulk-generator.js` | 1,367 | Input page JS for bulk generator (`bulk_generator.html`). Not part of JS-SPLIT-1 — that split `bulk-generator-job.js` (the job/results page). Actively used. |

---

## 🟡 Caution (800–1199 lines) — str_replace with Precision

Strategy: str_replace with multi-line anchor strings. Maximum 2–3 edits per spec.
Verify line count before spec begins.

### Python

| File | Lines | Notes |
|------|-------|-------|
| `prompts/tests/test_validate_tags.py` | 1,117 | Append new tests only. |
| `prompts/tests/test_pass2_seo_review.py` | 1,048 | Append new tests only. |
| `prompts/tests/test_user_profiles.py` | 991 | Append new tests only. |
| `prompts/services/vision_moderation.py` | 904 | Vision moderation service. Careful str_replace. |
| `prompts/views/upload_api_views.py` | 852 | New in Session 128. Already at caution tier. |
| `prompts/management/commands/detect_orphaned_files.py` | 798 | At the border (✅/🟡). Treat as caution. |

### CSS

| File | Lines | Notes |
|------|-------|-------|
| `static/css/pages/bulk-generator-job.css` | 1,179 | Job page CSS. Append only. |
| `static/css/upload.css` | 921 | Upload styles. Max 2 edits per spec. |

### JavaScript

| File | Lines | Notes |
|------|-------|-------|
| `static/js/upload-form.js` | 1,069 | Upload form JS. Careful str_replace. |
| `static/js/navbar.js` | 899 | Navbar JS. Max 2 edits. |
| `static/js/collections.js` | 1,108 | Collections modal JS. |

### HTML

| File | Lines | Notes |
|------|-------|-------|
| `prompts/templates/prompts/collections_profile.html` | 1,017 | Collections page. Targeted edits only. |
| `prompts/templates/prompts/prompt_detail.html` | 1,010 | Prompt detail. Careful str_replace. |

---

## ✅ Safe but Growing — Watch These Files

Files currently under 800 lines but frequently modified across recent sessions,
approaching the caution threshold.

| File | Lines | Why Flagged |
|------|-------|-------------|
| `prompts/views/upload_views.py` | 751 | Modified in Sessions 125, 127, 128A. Upload flow still active. |
| `prompts/views/collection_views.py` | 792 | At boundary. Modified in Sessions 74, 86. |
| `prompts/views/bulk_generator_views.py` | 721 | Active development. Bulk gen ongoing. |
| `prompts/views/user_views.py` | 630 | Modified in Sessions 74, 86. Growing. |
| `prompts/views/admin_views.py` | 577 | Admin additions ongoing. |
| `prompts/services/b2_upload_service.py` | 590 | B2 service grows with each upload feature. |
| `prompts/services/content_generation.py` | 528 | AI generation — grows with each AI spec. |
| `prompts/templates/prompts/bulk_generator.html` | 516 | Bulk gen UI still evolving. |
| `prompts/constants.py` | 451 | Grows as new model constants added. Monitor. |

---

## Already-Known Special Cases

| File | Lines | Current Strategy |
|------|-------|-----------------|
| `prompts/views/api_views.py` | 62 | Now a shim (Session 128C) — safe to edit |
| `prompts/views/moderation_api_views.py` | 340 | New in Session 128C — safe |
| `prompts/views/upload_api_views.py` | 852 | New in Session 128C — already 🟡 Caution |
| `prompts/views/social_api_views.py` | 111 | New in Session 128C — safe |
| `prompts/views/ai_api_views.py` | 298 | New in Session 128C — safe |
| `prompts_manager/settings.py` | 622 | Core settings — always approach carefully |
| `static/js/bulk-generator.js` | 1,367 | 🟠 High Risk — input page JS for `bulk_generator.html`. Separate from the 4 job-page modules created in JS-SPLIT-1. Actively loaded; do not delete. |

---

## Recommended Actions for Spec G (CLAUDE.md Update)

Copy the following tiers exactly into the CLAUDE.md constraints section:

**🔴 Critical (never edit directly):**
- `prompts/tasks.py` (3,451 lines)
- `prompts/models.py` (3,087 lines)
- `prompts/tests/test_notifications.py` (2,872 lines)
- `prompts/tests/test_bulk_generator_views.py` (2,210 lines)
- `prompts/admin.py` (2,366 lines)
- `static/css/style.css` (4,466 lines)
- `prompts/templates/prompts/user_profile.html` (2,073 lines)

**🟠 High Risk (avoid direct editing):**
- `prompts/views/prompt_views.py` (1,694 lines)
- `prompts/tests/test_bulk_generation_tasks.py` (1,861 lines)
- `prompts/tests/test_bulk_page_creation.py` (1,621 lines)
- `prompts/templates/prompts/prompt_list.html` (1,700 lines)
- `static/css/pages/prompt-detail.css` (1,549 lines)
- `static/css/pages/bulk-generator.css` (1,484 lines)
- `static/css/navbar.css` (1,268 lines)
- `static/js/bulk-generator.js` (1,367 lines) — input page JS, actively used

**🟡 Caution (str_replace with precision, max 2–3 edits):**
- `prompts/tests/test_validate_tags.py` (1,117 lines)
- `prompts/tests/test_pass2_seo_review.py` (1,048 lines)
- `prompts/tests/test_user_profiles.py` (991 lines)
- `prompts/services/vision_moderation.py` (904 lines)
- `prompts/views/upload_api_views.py` (852 lines)
- `prompts/management/commands/detect_orphaned_files.py` (798 lines)
- `static/css/pages/bulk-generator-job.css` (1,179 lines)
- `static/css/upload.css` (921 lines)
- `static/js/upload-form.js` (1,069 lines)
- `static/js/navbar.js` (899 lines)
- `static/js/collections.js` (1,108 lines)
- `prompts/templates/prompts/collections_profile.html` (1,017 lines)
- `prompts/templates/prompts/prompt_detail.html` (1,010 lines)

**✅ Safe but growing (watch):**
- `prompts/views/upload_views.py` (751) — modified 3 recent sessions
- `prompts/views/collection_views.py` (792) — at boundary
- `prompts/views/bulk_generator_views.py` (721) — active development

---

## Agent Ratings

| Agent | Score | Key Findings | Acted On? |
|-------|-------|--------------|-----------|
| @code-reviewer | 9.2/10 | Initial review 6.5 (3 issues found). Fixed: `bulk-generator.js` misidentified as stale artifact (it's the active input page JS), `collections.js` wrong tier (1,108 lines = Caution not High Risk), `upload-form.js` dual-listed in Safe but Growing. Re-review post-fixes scored 9.2/10. | Yes — all 3 issues corrected |
| Average | 9.2/10 | PASS (≥8.0) | — |
