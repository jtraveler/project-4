# Cloudinary Codebase Audit Report
**Date:** March 13, 2026
**Type:** Read-only audit — no code changes made

---

## Summary

PromptFinder has migrated new uploads to Backblaze B2 + Cloudflare CDN, but Cloudinary
remains deeply integrated across models, services, templates, views, and settings. Most
active references fall into two categories: (1) legitimate legacy support for older prompts
still stored in Cloudinary, and (2) the misnamed `cloudinary_moderation.py` service which
actually uses OpenAI Vision API and has no Cloudinary dependency. Several management commands
that were Cloudinary-only (orphan detection, URL fixer, thumbnail regeneration) are now
stale candidates for removal or disablement.

---

## Category A — Intentional Legacy (Keep)

These references are expected and correct. They exist to display images for older prompts
that were uploaded before the B2 migration. Do not remove.

| File | Line(s) | Reference | Why It's Intentional |
|------|---------|-----------|----------------------|
| `prompts/models.py` | 62 | `CloudinaryField` on `Profile.avatar` | Avatar storage for pre-migration accounts |
| `prompts/models.py` | 767 | `CloudinaryField` on `Prompt.featured_image` | Legacy prompt image field; B2 prompts use `b2_image_url` |
| `prompts/models.py` | 776 | `CloudinaryField` on `Prompt.featured_video` | Legacy prompt video field; B2 prompts use `b2_video_url` |
| `prompts/models.py` | 1059, 1075 | `cloudinary.uploader.destroy` in delete signal | Needed to delete Cloudinary files when legacy prompts are hard-deleted |
| `prompts/templates/prompts/prompt_list.html` | 3, 11–14 | `{% load cloudinary_tags %}`, `display_medium_url`, `cloudinary_transform` | B2-first fallback pattern; falls back to Cloudinary for legacy prompts |
| `prompts/templates/prompts/prompt_detail.html` | 3, 241 | `{% load cloudinary_tags %}`, `cloudinary_transform` | Same B2-first fallback for legacy prompt detail page |
| `prompts/templates/prompts/user_profile.html` | 3–4, 1034 | `{% load cloudinary %}`, `{% load cloudinary_tags %}`, `cloudinary_transform` | Legacy prompt display in profile grid |
| `prompts/templates/prompts/trash_bin.html` | 3–4, 100 | `{% load cloudinary %}`, `{% load cloudinary_tags %}`, `cloudinary_transform` | Legacy prompt display in trash |
| `prompts/templates/prompts/partials/_prompt_card.html` | 4–5, 197 | `{% load cloudinary %}`, `{% load cloudinary_tags %}`, `cloudinary_transform` | Legacy prompt card display across all gallery views |
| `prompts/templates/prompts/edit_profile.html` | 2, 49 | `{% load cloudinary %}`, `{% cloudinary %}` tag | Avatar display/upload for `Profile.avatar` (CloudinaryField) |
| `prompts/templates/prompts/inspiration_index.html` | 3–4 | `{% load cloudinary %}`, `{% load cloudinary_tags %}` | Legacy prompt display |
| `prompts/templates/prompts/collection_detail.html` | 3–4 | `{% load cloudinary %}`, `{% load cloudinary_tags %}` | Legacy prompt display in collections |
| `prompts/templates/prompts/collections_profile.html` | 3–4 | `{% load cloudinary %}`, `{% load cloudinary_tags %}` | Legacy prompt display in collections profile |
| `templates/base.html` | 685, 694, 707, 716, 729 | Hardcoded `res.cloudinary.com/dj0uufabo` URLs | Static marketing images on landing page hero section (not prompt images) |
| `prompts/templates/prompts/upload.html` | 66 | `<input type="hidden" name="cloudinary_id" id="b2FileKey">` | Field ID retained from legacy upload; now holds B2 file key but name unchanged for compatibility |

---

## Category B — Active Service Code (Investigate)

These references are in active service files or tasks and may still be executing Cloudinary
API calls. Needs human review before any removal.

| File | Line(s) | Reference | What It Does | Risk Level |
|------|---------|-----------|--------------|------------|
| `prompts/services/cloudinary_moderation.py` | 83+ | `class VisionModerationService` | **MISNAMED FILE**: Uses OpenAI Vision API, NOT Cloudinary API. No Cloudinary imports. Actively used throughout codebase for NSFW moderation. Safe functionally, misleading by name. | Low (functional) / Medium (naming confusion) |
| `prompts/services/content_generation.py` | 416–425 | `cloudinary.api.resource`, `cloudinary.CloudinaryVideo` | Fetches video metadata + thumbnail URL from Cloudinary for videos stored there. Called during content generation for legacy Cloudinary-stored videos. | Medium — still executes Cloudinary API calls for legacy video prompts |
| `prompts/views/upload_views.py` | 214–215, 262, 356, 367, 383, 499–511 | `cloudinary_cloud_name`, `cloudinary_upload_preset`, `cloudinary_id` | Legacy Cloudinary upload path code still present in active views file. Current uploads use B2, but this code path exists alongside B2 logic. `upload_views.py` passes `cloudinary_cloud_name` in config context on line 214. | Medium — dead code path in active file; risk of confusion |
| `prompts/views/upload_views.py` | 740–758 | `cloudinary.uploader.destroy` | Legacy cleanup endpoint that deletes a Cloudinary file by public_id. Called if legacy upload is rolled back. | Low — only triggers for legacy Cloudinary uploads |
| `prompts/views/admin_views.py` | 13 | `import cloudinary.api` | Imported at module level; powers moderation dashboard `cloudinary_status` context variable. Executes Cloudinary API check on page load. | Medium — live API call in admin dashboard |
| `prompts/views/prompt_views.py` | 882–918 | `clear_cloudinary_fields(p)` helper | Clears Cloudinary model fields (`featured_image`, `featured_video`) during a migration-utility flow. Only reachable via a specific admin action. | Low — intentional migration utility |
| `prompts/tasks.py` | 79, 82 | `VisionModerationService` import + instantiation | Active NSFW moderation task. Imports from `cloudinary_moderation.py` (misnamed but functional — uses OpenAI Vision). | Low — fully functional, no actual Cloudinary call |
| `prompts/views/api_views.py` | 31, 65, 868–869, 1137–1139, 1353 | Multiple `VisionModerationService` usages | Active moderation in upload flow — image moderate, video frame moderate, manual re-moderate. All go through OpenAI Vision. | Low — functional, no actual Cloudinary call |
| `prompts_manager/settings.py` | (CLOUDINARY_STORAGE block) | `DEFAULT_FILE_STORAGE`, `CLOUDINARY_STORAGE`, `cloudinary.config(secure=True)` | Active configuration. Required for `CloudinaryField` on `Profile.avatar` and legacy `Prompt` fields to read/write. Removing this would break avatar uploads and legacy image reads. | High — must remain while CloudinaryField fields exist |

---

## Category C — Stale / Unused Code (Candidate for Removal)

These references appear to be leftover from the migration and are no longer
called or imported anywhere active.

| File | Line(s) | Reference | Evidence It's Unused |
|------|---------|-----------|----------------------|
| `prompts/management/commands/detect_orphaned_files.py` | 1–524 (whole file) | Full Cloudinary orphan scanner | Scans Cloudinary API only — non-functional for B2 files. Replaced by `detect_b2_orphans` (Session 123). 524 lines. Still references Heroku Scheduler but B2 detection is now the correct tool. |
| `prompts/management/commands/regenerate_video_thumbnails.py` | (whole file) | `res.cloudinary.com/dxjxk7c09` hardcoded URL | Hardcodes a specific Cloudinary cloud name (`dxjxk7c09`). One-off migration utility. New videos use B2. |
| `prompts/management/commands/fix_cloudinary_urls.py` | (whole file) | Cloudinary URL fixer | One-off migration utility for fixing malformed Cloudinary URLs. Still referenced in `templates/admin/trash_dashboard.html` as a runbook command, but functionally stale for new content. |
| `prompts/management/commands/test_moderation.py` | 13, 97 | `VisionModerationService` test command | Tests the misnamed moderation service (which uses OpenAI Vision, not Cloudinary). Functional but named misleadingly; no callers in production flow. |
| `prompts/services/__init__.py` | 12, 37 | `from .cloudinary_moderation import VisionModerationService` | Exports `VisionModerationService` from package `__init__` — not stale, but contributes to naming confusion. |

---

## Category D — Configuration / Settings

| File | Line | Setting | Status |
|------|------|---------|--------|
| `requirements.txt` | — | `cloudinary==1.36.0` | Active — required by `CloudinaryField`, `cloudinary.api`, `cloudinary.uploader` |
| `requirements.txt` | — | `dj3-cloudinary-storage==0.0.6` | Active — provides `DEFAULT_FILE_STORAGE` for `CloudinaryField` |
| `prompts_manager/settings.py` | — | `import cloudinary; cloudinary.config(secure=True)` | Active — configures SDK at startup |
| `prompts_manager/settings.py` | — | `CLOUDINARY_STORAGE = {'CLOUD_NAME': ..., 'API_KEY': ..., 'API_SECRET': ...}` | Active — required for any Cloudinary field read/write |
| `prompts_manager/settings.py` | — | `DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'` | Active — sets default storage backend; used by `CloudinaryField` fields |
| `prompts_manager/settings.py` | — | CSP `connect-src`, `img-src` with `*.cloudinary.com res.cloudinary.com` | Active — allows browser to load images from Cloudinary CDN |
| `Procfile` | — | No Cloudinary references | Cloudinary not in Procfile |

---

## Category E — Scheduled Tasks (Manual Check Required)

| Command | Scheduled | Notes |
|---------|-----------|-------|
| `detect_orphaned_files` | **Unknown — check Heroku Scheduler dashboard manually** | Cloudinary-only, non-functional for B2. If still scheduled, should be removed from Heroku Scheduler. `detect_b2_orphans` is the B2-aware replacement (built Session 123). |
| `fix_cloudinary_urls` | Likely not scheduled | One-off migration utility; referenced in `trash_dashboard.html` runbook but unlikely to be on Scheduler |

---

## Django Shell Commands to Run in Production

Run these in the Heroku console (`heroku run python manage.py shell`) to get data counts
before planning any cleanup:

```python
# How many Prompt records still have a Cloudinary URL set?
from prompts.models import Prompt
print("Prompts with cloudinary_url:", Prompt.all_objects.filter(cloudinary_url__isnull=False).exclude(cloudinary_url='').count())

# How many Prompt records still use CloudinaryField (featured_image stored in Cloudinary)?
# These have a featured_image but no b2_image_url
print("Prompts with featured_image (Cloudinary) but no B2 URL:", Prompt.all_objects.filter(b2_image_url='').exclude(featured_image='').count())

# How many Profile records have a Cloudinary avatar?
from prompts.models import Profile
print("Profiles with Cloudinary avatar:", Profile.objects.exclude(avatar='').count())

# How many Prompt records have a Cloudinary video?
print("Prompts with Cloudinary video:", Prompt.all_objects.exclude(featured_video='').count())
```

---

## Recommended Next Steps

**Priority order — human review required before any action:**

1. **Check Heroku Scheduler (immediate):** Verify whether `detect_orphaned_files` is still
   scheduled. If so, remove it and replace with `detect_b2_orphans`. Running the Cloudinary
   orphan scanner silently produces misleading results (scans Cloudinary, misses all B2 files).

2. **Rename `cloudinary_moderation.py` → `vision_moderation.py` (low risk, high clarity):**
   The file has zero Cloudinary imports or calls — it uses OpenAI Vision API only. The misleading
   name causes unnecessary confusion in audits and onboarding. All import sites
   (`api_views.py`, `tasks.py`, `orchestrator.py`, `services/__init__.py`, `views_admin.py`,
   `test_moderation.py`) would need updating. No behavior change.

3. **Run Django shell counts (before any field removal):** Use the commands above to determine
   how many Prompts and Profiles still have Cloudinary-stored files. This determines the urgency
   and scope of a future migration-or-keep decision for the `CloudinaryField` model fields.

4. **Evaluate `detect_orphaned_files.py` for deletion:** It is 524 lines of Cloudinary-only code
   with no B2 support. `detect_b2_orphans` replaces its core purpose. Consider deleting (or
   archiving) this command once the Scheduler entry is removed. Keep `fix_cloudinary_urls.py`
   accessible as a runbook command until the DB count confirms zero legacy Cloudinary URLs remain.

5. **Assess legacy Cloudinary upload path in `upload_views.py`:** Lines 214, 262, 356, 383,
   499–511, 740–758 contain a complete Cloudinary upload flow alongside the current B2 path.
   Determine whether any active upload route still reaches this code, then remove if dead.
   Requires reading `upload_views.py` in full context before touching.

---

## Audit Verification

- [x] Step 1 — Broad sweep (`.py`, `.html`, `.js`, `.css`, `.txt`) — all run
- [x] Step 2 — Settings and configuration — confirmed
- [x] Step 3 — Models — CloudinaryField locations confirmed
- [x] Step 4 — Active service files — VisionModerationService usage mapped
- [x] Step 5 — Views and tasks — Cloudinary references located
- [x] Step 6 — Management commands — stale commands identified
- [x] Step 7 — Heroku Scheduler — not in Procfile; manual dashboard check flagged
- [x] Step 8 — Templates — all template references catalogued
- [x] Step 9 — `prompts/admin.py` — no Cloudinary references (admin_views.py has one import)
- [x] Step 10 — B2-first fallback pattern confirmed present; Django shell commands documented
- [x] No code changed
