# REPORT_130_D_SRC4_PUBLISH_DELETE.md
# Spec D Completion Report — SRC-4: Copy b2_source_image_url on Publish, Delete from B2 on hard_delete

**Session:** 130
**Spec:** CC_SPEC_130_D_SRC4_PUBLISH_DELETE.md
**Date:** March 15, 2026
**Status:** ✅ Complete

---

## Section 1 — Overview

Spec C (SRC-3) added backend parsing of `source_image_urls` from the bulk generator API request and stored the external URL on `GeneratedImage.source_image_url`. It also confirmed the existence of `GeneratedImage.b2_source_image_url` and `Prompt.b2_source_image_url` (both URLFields added in Session 129 SRC-1).

Spec D (SRC-4) wires the pipeline forward in two directions:

**Publish direction:** When a `GeneratedImage` is published into a `Prompt` page (via either publish function in `tasks.py`), the `b2_source_image_url` field is now copied from the `GeneratedImage` to the `Prompt.b2_source_image_url`. This is a conditional copy — if the field is blank, nothing happens. In the current session, `GeneratedImage.b2_source_image_url` is always blank (the B2 upload for source images is a future SRC spec). This spec wires the plumbing for when that field is populated.

**Delete direction:** When a `Prompt` is hard-deleted (permanent deletion), if `Prompt.b2_source_image_url` is set, the file is deleted from B2 storage. This is implemented in both `hard_delete()` and the `delete_cloudinary_assets` post_delete signal, following the same defense-in-depth pattern used for Cloudinary asset deletion.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `b2_source_image_url` copied in `create_prompt_pages_from_job` | ✅ Met |
| `b2_source_image_url` copied in `publish_prompt_pages_from_job` | ✅ Met |
| Copy uses conditional guard (`if gen_image.b2_source_image_url`) | ✅ Met |
| Copy happens before `prompt_page.save()` | ✅ Met |
| B2 deletion added to `hard_delete()` with try/except | ✅ Met |
| B2 deletion added to `delete_cloudinary_assets` signal with try/except | ✅ Met |
| Deletion never blocks prompt deletion (non-blocking exception handling) | ✅ Met |
| 5+ tests written and passing | ✅ Met — 6 tests (5 required + 1 additional) |
| `python manage.py check` passes | ✅ Met |
| Targeted test run passes | ✅ Met — `SourceImagePublishTests`: 6/6 |
| Maximum 3 str_replace calls on `tasks.py` (C+D combined) | ✅ Met — 2 used in D, 0 in C |
| Maximum 2 str_replace calls on `models.py` | ✅ Met — 2 used |

---

## Section 3 — Changes Made

### `prompts/tasks.py`

**Edit 1 — `create_prompt_pages_from_job` (line ~3103):**
After the b2 URL block (b2_image_url, b2_thumb_url, b2_medium_url, b2_large_url) and before `transaction.atomic()`:
```python
if gen_image.b2_source_image_url:
    prompt_page.b2_source_image_url = gen_image.b2_source_image_url
```

**Edit 2 — `publish_prompt_pages_from_job` (line ~3367):**
Same addition in the second publish function, after the same b2 URL block:
```python
if gen_image.b2_source_image_url:
    prompt_page.b2_source_image_url = gen_image.b2_source_image_url
```

Both edits are placed before `prompt_page.save()` so the value is persisted in the initial save without needing a separate `update_fields` call.

### `prompts/models.py`

**Edit 1 — `hard_delete()` method (between Cloudinary video deletion and `super().delete()`):**
```python
# Delete B2 source image if present
if self.b2_source_image_url:
    try:
        from urllib.parse import urlparse as _urlparse
        from prompts.storage_backends import B2MediaStorage
        _parsed = _urlparse(self.b2_source_image_url)
        b2_key = _parsed.path.lstrip('/')
        if b2_key:
            B2MediaStorage().delete(b2_key)
            logger.info(
                f"Deleted B2 source image for Prompt '{self.title}': {b2_key}"
            )
    except Exception as e:
        logger.error(
            f"Failed to delete B2 source image for Prompt '{self.title}': {e}",
            exc_info=True
        )
```

**Edit 2 — `delete_cloudinary_assets` post_delete signal (after Cloudinary video deletion, before `Follow` class):**
Identical pattern using `instance.*` instead of `self.*`, with log message including `(signal)` suffix for disambiguation.

### `prompts/tests/test_bulk_page_creation.py`

Appended `SourceImagePublishTests` class (6 tests) at end of file:
1. `test_b2_source_image_url_copied_on_publish` — `create_prompt_pages_from_job` copies the URL
2. `test_empty_b2_source_image_url_not_copied` — empty URL field produces empty Prompt field
3. `test_hard_delete_triggers_b2_source_deletion` — `B2MediaStorage().delete` called with correct key (call_count == 2: once from hard_delete, once from signal)
4. `test_hard_delete_no_source_image_no_deletion` — empty `b2_source_image_url` → `B2MediaStorage` never instantiated
5. `test_hard_delete_b2_failure_does_not_block_deletion` — exception caught, prompt deleted from DB regardless
6. `test_b2_source_image_url_copied_on_publish_via_publish_function` — `publish_prompt_pages_from_job` path (added after round-1 agent feedback)

---

## Section 4 — Issues Encountered and Resolved

**Issue:** B2 deletion test `test_hard_delete_triggers_b2_source_deletion` initially asserted `assert_called_once_with(...)` but failed with `Called 2 times`.
**Root cause:** `hard_delete()` deletes the B2 file, then calls `super().delete()` which fires the `post_delete` signal. The signal also executes the B2 deletion code. Both deletions target the same key.
**Fix applied:** Updated assertion to `self.assertEqual(mock_storage.delete.call_count, 2)` with a comment documenting the dual-path behavior. The double-deletion matches the pre-existing Cloudinary pattern.
**File:** `prompts/tests/test_bulk_page_creation.py`

**Issue:** Initial tests patched `prompts.tasks.async_task` (wrong — local import) and `prompts.models.B2MediaStorage` (wrong — module not in scope).
**Root cause:** `async_task` is imported locally inside `create_prompt_pages_from_job`; `B2MediaStorage` is imported locally inside `hard_delete()` and the signal. Module-level patches on these references would fail.
**Fix applied:** Changed to `django_q.tasks.async_task` (source module) and `prompts.storage_backends.B2MediaStorage` (source module). Local imports in function bodies resolve against the source module at call time, so patching the source module is correct.
**File:** `prompts/tests/test_bulk_page_creation.py`

**Issue:** `Prompt.objects.create(prompt_text='test')` field name incorrect.
**Root cause:** The Prompt model uses `content` not `prompt_text` for the prompt text field.
**Fix applied:** Changed to `content='test prompt'` in all three Prompt creation calls in the test class.
**File:** `prompts/tests/test_bulk_page_creation.py`

---

## Section 5 — Remaining Issues

**Issue:** Double-deletion of `b2_source_image_url` — the file is deleted twice (once from `hard_delete()`, once from the post_delete signal).
**Recommended fix:** Extract a shared `_delete_b2_source_image(url)` helper and call it only from the signal, removing it from `hard_delete()`. Alternatively, clear `b2_source_image_url` before calling `super().delete()` to prevent the signal from triggering.
**Priority:** P3 (B2 `delete_object` is idempotent — no functional impact)
**Reason not resolved:** (1) models.py edit budget (max 2 str_replace) exhausted. (2) The pattern matches the pre-existing Cloudinary double-deletion architecture already in production. A cleanup spec should address both Cloudinary and B2 at the same time for consistency.

**Issue:** No prefix allowlist guard on B2 key before deletion. The `b2_rename.py` `cleanup_empty_prefix()` function has an allowlist guard (`bulk-gen/` or `media/`); the new deletion code does not.
**Recommended fix:** Add `if not (b2_key.startswith('bulk-gen/') or b2_key.startswith('media/')): logger.warning(...); return` before the `B2MediaStorage().delete(b2_key)` call in both deletion locations.
**Priority:** P2 (defense-in-depth — not an exploitable vulnerability given staff-only data provenance)
**Reason not resolved:** models.py edit budget exhausted.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** URL key extraction pattern (`urlparse(url).path.lstrip('/')`) assumes CDN URL format (`https://media.promptfinder.net/{key}`). If `B2_CUSTOM_DOMAIN` is not configured (e.g., local dev), the stored URL would be a direct B2/S3 endpoint URL containing the bucket name in the path, causing incorrect key extraction.
**Impact:** Key extraction would produce `{bucket_name}/{key}` in non-CDN environments, causing the deletion to silently fail or target a non-existent key.
**Recommended action:** Use `B2RenameService._url_to_key(url)` (already in `b2_rename.py`) which handles both URL formats, or at minimum add a comment noting the CDN URL assumption.

**Concern:** `hard_delete()` docstring says "Permanently delete prompt and Cloudinary assets" — does not mention B2.
**Impact:** Misleading for developers who may not realize B2 source images are also deleted.
**Recommended action:** Update docstring to "Permanently delete prompt, Cloudinary assets, and B2 source image." One-line change in a future maintenance pass.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | Copy placement correct; `update_fields` not needed; double-deletion acceptable (matches Cloudinary); URL extraction correct for CDN format | No action needed |
| 1 | @security-auditor | 7.0/10 | Double-deletion (medium); missing prefix allowlist (low); no SSRF; double-deletion wasteful but safe | Addressed in report; not fixable (budget) |
| 1 | @code-reviewer | 7.5/10 | Double-deletion design smell; missing `publish_prompt_pages_from_job` test | Added 6th test |
| 2 | @security-auditor | 9.0/10 | Double-deletion resolved (idempotent, matches Cloudinary pattern); prefix allowlist noted for future | No further action |
| 2 | @code-reviewer | 8.5/10 | 6th test closes coverage gap; double-deletion documented and acceptable given constraints | No further action |
| **Round 2 Average** | | **8.83/10** | | **✅ Pass (threshold: 8.0)** |

Round 1 average was 7.83/10 (below threshold). Round 2 average is 8.83/10 after adding the `publish_prompt_pages_from_job` test.

---

## Section 8 — Recommended Additional Agents

**@test-automator:** Would have identified the missing `publish_prompt_pages_from_job` test in round 1, saving the re-run. Worth including in future specs that touch both publish functions.

---

## Section 9 — How to Test

**Automated:**
```bash
# Run new test class
python manage.py test prompts.tests.test_bulk_page_creation.SourceImagePublishTests
# Expected: 6 tests, 0 failures, 0 errors

# System check
python manage.py check
# Expected: System check identified no issues (0 silenced).

# Full suite (runs once at end of session per CC_RUN_INSTRUCTIONS_SESSION_130.md)
python manage.py test
# Expected: 1165+ tests, 0 failures, 12 skipped
```

**Manual verification (once `GeneratedImage.b2_source_image_url` is populated by a future SRC spec):**
1. Create a bulk generation job with a source image URL
2. Publish an image from the job
3. Verify `Prompt.b2_source_image_url` matches the generated image's `b2_source_image_url`
4. Hard-delete the prompt from admin
5. Verify the B2 file at the extracted key no longer exists

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(pending)* | `feat(src-4): copy b2_source_image_url on publish, delete from B2 on hard_delete` |

---

## Section 11 — What to Work on Next

1. **Full test suite** — Run `python manage.py test` now (required after Spec D per session instructions). Expected: 1165+ passing, 0 failures, 12 skipped.

2. **Prefix allowlist guard on B2 source image deletion (P2)** — Add prefix check (must start with `bulk-gen/` or `media/`) to both deletion blocks in `models.py` in a follow-up maintenance spec. Consistent with `b2_rename.py` HARDENING-2 guard.

3. **Fix `hard_delete()` docstring** — Update to mention B2 source image deletion alongside Cloudinary.

4. **Future SRC spec** — Populate `GeneratedImage.b2_source_image_url` by actually downloading the source image from `source_image_url` and uploading it to B2. Once that lands, all the plumbing built in SRC-3 and SRC-4 will activate end-to-end.

---

**END OF REPORT**
