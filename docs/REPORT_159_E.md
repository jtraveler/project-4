# REPORT_159_E — Remove Cloudinary Code (Partial — Blocked by Model Fields)

## Section 1 — Overview

The spec called for full removal of all Cloudinary code and the `cloudinary` package
from `requirements.txt`. Investigation revealed that Cloudinary is deeply integrated
into the codebase — 3 model fields use `CloudinaryField`, 8 templates use the
`cloudinary_tags` templatetag, signal handlers call `cloudinary.uploader.destroy()`,
and the video moderation service uses Cloudinary for frame extraction.

Full removal requires a multi-step migration spec (not a one-session housekeeping task).
Only the unused top-level import in `vision_moderation.py` was safely removed.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| All Cloudinary imports removed | ❌ Blocked — model fields depend on CloudinaryField |
| `cloudinary` removed from `requirements.txt` | ❌ Blocked — models.py imports CloudinaryField |
| `django-cloudinary-storage` removed | ❌ Blocked — in INSTALLED_APPS, referenced by settings |
| Circular import in vision_moderation.py resolved | ✅ Met — unused top-level import removed |
| B2/Backblaze configuration untouched | ✅ Met |

## Section 3 — Changes Made

### prompts/services/vision_moderation.py
- Line 31: Removed unused `import cloudinary.uploader` (top-level import never referenced —
  the file uses local `import cloudinary` inside `_get_video_frame_url()` and
  `get_video_frame_from_id()` methods instead)

## Section 4 — Issues Encountered and Resolved

**Issue:** Spec assumed Cloudinary could be fully removed without a migration. Investigation
revealed 3 model fields (`avatar`, `featured_image`, `featured_video`) use
`cloudinary.models.CloudinaryField`. Removing the `cloudinary` package would break
Django model loading entirely.

**Root cause:** The B2 migration migrated *data* (image URLs) but did not migrate the
*field types*. `CloudinaryField` is still the declared field type in `models.py` even
though all actual values are B2 URLs.

**Impact:** Cannot remove `cloudinary` from `requirements.txt`, `INSTALLED_APPS`, or
`settings.py` Cloudinary configuration without first:
1. Creating a Django migration to change `CloudinaryField` → `CharField` for all 3 fields
2. Updating 8 templates that `{% load cloudinary_tags %}` and use `|cloudinary_transform`
3. Removing `cloudinary.uploader.destroy()` calls in signal handlers (models.py lines
   1068, 1084, 2257, 2276) and pre-delete signal
4. Removing Cloudinary methods in `vision_moderation.py` (lines 675-712)
5. Removing `content_generation.py` Cloudinary video thumbnail code (lines 416-425)
6. Removing `detect_orphaned_files.py` management command (Cloudinary-only, 524 lines)
7. Removing `fix_cloudinary_urls.py` management command (dead utility)
8. Removing `cloudinary_tags.py` templatetag (after template updates)
9. Removing Cloudinary CSP directives from `settings.py`

## Section 5 — Remaining Issues

**Issue:** Full Cloudinary removal requires a dedicated migration spec.
**Recommended fix:** Create a 2-part spec:
- Part 1: Migration to replace `CloudinaryField` → `CharField(max_length=255)` for
  `UserProfile.avatar`, `Prompt.featured_image`, `Prompt.featured_video`
- Part 2: Remove all Cloudinary imports, settings, templatetags, signal handlers,
  management commands, and CSP directives
**Priority:** P2 — technical debt, no functional impact
**Reason not resolved:** Scope exceeds a housekeeping spec. Requires migration + template
  changes across 8 files + 🔴 Critical file edits (models.py, tasks.py).

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `cloudinary` package (v1.36.0) and `dj3-cloudinary-storage` (v0.0.6)
remain in `requirements.txt`. They add ~2MB to the deployment slug and import ~50 modules
on startup. This is wasted overhead.

**Impact:** Slow startup, unnecessary dependency surface area, potential security patches
needed for an unused package.

**Recommended action:** Prioritize the migration spec before the next major deployment.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 9/10 | Correctly identified scope limitation | N/A — finding documented |
| 1 | @docs-architect | 9/10 | Report structure accurate | N/A |
| **Average** | | **9.0/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

@django-pro would be valuable for the future migration spec to verify field type
compatibility between CloudinaryField and CharField.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py check  # Expected: 0 issues
python manage.py test --verbosity=0  # Expected: 1270 tests, 0 failures
```

**Manual verification:**
```bash
grep -n "import cloudinary.uploader" prompts/services/vision_moderation.py
# Expected: 0 results (top-level import removed)
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| (pending) | chore: remove unused cloudinary import from vision_moderation.py |

## Section 11 — What to Work on Next

1. **Create migration spec** to replace `CloudinaryField` → `CharField(max_length=255)`
   for `avatar`, `featured_image`, `featured_video` fields
2. After migration: remove all Cloudinary imports, settings, templatetags, and commands
3. Remove `cloudinary` and `dj3-cloudinary-storage` from `requirements.txt`
4. Remove Cloudinary CSP directives from `settings.py`
