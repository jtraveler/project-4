# REPORT: N4H-UPLOAD-RENAME-FIX — Upload-Flow SEO Rename Task Not Triggering

**Spec ID:** N4H-UPLOAD-RENAME-FIX
**Date:** March 12, 2026
**Commit:** `a9acbc4`
**Test count before:** 1147 | **Test count after:** 1149 | **Failures:** 0 | **Skipped:** 12

---

## Section 1 — Overview

### What this fix was

`rename_prompt_files_for_seo` is a Django-Q2 background task that renames B2-uploaded files
from their UUID-based storage paths to SEO-friendly slugs. For example:

- **Before rename:** `media/images/2026/03/original/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`
- **After rename:** `media/images/2026/03/original/stylish-woman-beach-sunset-midjourney-prompt.jpg`

Search engines index both the URL path and the filename. UUID filenames contain no keywords,
providing zero SEO value. SEO-friendly filenames give search engines additional keyword signals
for image search ranking.

### Why the bug existed

PromptFinder has two distinct code paths that create `Prompt` records with B2 image URLs:

1. **Bulk-gen publish path** — `publish_prompt_pages_from_job` and `create_prompt_pages_from_job`
   in `prompts/tasks.py`. Used when staff publish bulk-generated images via the bulk AI generator tool.

2. **Upload-flow path** — `upload_submit` in `prompts/views/upload_views.py`. Used when any
   authenticated user manually uploads an image through the upload page at `/upload/`.

SMOKE2-FIX-D (commit `0b1618a`, Session 121, March 11, 2026) fixed the bulk-gen publish path.
The upload-flow path was missed entirely. Every prompt created via the upload form kept its
UUID-based filename indefinitely, since `rename_prompt_files_for_seo` was never queued for
that code path.

### Important discovery: the core call was already present

When mapping the upload submit path as required by the spec, it emerged that the `async_task`
call was already added to `upload_views.py` in commit `ac1e5ea` (Session 67, February 4, 2026)
— before SMOKE2-FIX-D was written. This means the CLAUDE.md blocker entry for "N4h rename
(upload-flow)" was outdated. The core async_task call had already been added.

What this spec actually fixed was:

1. **Guard condition:** The earlier code used `if is_b2_upload and prompt.pk:` (session-based flag).
   The spec requires `if prompt.b2_image_url:` (model field check). The difference matters: for
   video B2 uploads, `is_b2_upload` is True but `b2_image_url` is None — the old guard would queue
   a no-op task; the new guard correctly skips it.

2. **Import location:** `async_task` was imported inside the `try` block (local import). Moving it
   to module level is more idiomatic for a view and is required for the `@patch` decorator to
   intercept it in tests (`@patch('prompts.views.upload_views.async_task')`).

3. **Tests:** No tests existed for this code path. Two tests were added.

### SEO impact of the original bug

Without rename, upload-flow prompts retained UUID-based filenames. Search engines crawling these
image URLs found filenames containing no searchable keywords. The rename task corrects this in the
background, after the upload completes. With the fix in place, newly uploaded prompts will have
their B2 filenames updated to SEO-friendly slugs within seconds of creation (once the Django-Q2
worker processes the task).

---

## Section 2 — Expectations

The spec required all of the following. All were met:

| Expectation | Status | Notes |
|-------------|--------|-------|
| Git archaeology completed — SMOKE2-FIX-D hash identified | ✅ | Hash `0b1618a`, changes in `prompts/tasks.py` |
| Upload submit path fully mapped — `prompt.save()` location confirmed | ✅ | `_save_with_unique_title(prompt)` at line 516 |
| `async_task('prompts.tasks.rename_prompt_files_for_seo', prompt.pk)` queued after save | ✅ | Was already present; guard and import refined |
| Guard: queue only fires if `prompt.b2_image_url` is set and non-empty | ✅ | Changed from `is_b2_upload and prompt.pk` |
| `async_task` import confirmed in `upload_views.py` | ✅ | Moved to module level |
| Test: task queued with B2 URL | ✅ | `test_rename_task_queued_on_upload_submit` |
| Test: task not queued without B2 URL | ✅ | `test_rename_task_not_queued_without_b2_url` |
| Both agents score 8+/10 | ✅ | @django-pro 8.5/10, @test-automator 8.2/10 |
| Full suite passes | ✅ | 1149 tests, 0 failures |

---

## Section 3 — Improvements Made

### File 1: `prompts/views/upload_views.py`

**Change 1: `async_task` moved to module-level import**

BEFORE (line 20 area, nothing; local import inside function):
```python
from prompts.utils.source_credit import parse_source_credit
import json
import logging
```

AFTER:
```python
from prompts.utils.source_credit import parse_source_credit
from django_q.tasks import async_task
import json
import logging
```

---

**Change 2: Guard updated; inner local import removed**

Position: after `_save_with_unique_title(prompt)` at line ~516, before tag assignment.

BEFORE:
```python
# N4h: Queue SEO file renaming for B2 uploads
# Renames UUID filenames to SEO-friendly slugs (e.g., "title-slug-ai-prompt.jpg")
if is_b2_upload and prompt.pk:
    try:
        from django_q.tasks import async_task
        async_task(
            'prompts.tasks.rename_prompt_files_for_seo',
            prompt.pk,
            task_name=f'seo-rename-{prompt.pk}',
        )
        logger.info(f"Prompt {prompt.pk}: Queued SEO rename task")
    except Exception as e:
        # Non-blocking: rename failure shouldn't break the upload flow
        logger.warning(f"Prompt {prompt.pk}: Failed to queue SEO rename: {e}")
```

AFTER:
```python
# N4h: Queue SEO file renaming for B2 image uploads (N4H-UPLOAD-RENAME-FIX).
# Renames UUID-based filenames to SEO-friendly slugs (e.g., "title-slug-ai-prompt.jpg").
# Guard: only queue if b2_image_url is set — avoids a no-op task for video/Cloudinary uploads.
# Follows same pattern as SMOKE2-FIX-D for bulk-gen path (Session 121).
if prompt.b2_image_url:
    try:
        async_task(
            'prompts.tasks.rename_prompt_files_for_seo',
            prompt.pk,
            task_name=f'seo-rename-{prompt.pk}',
        )
        logger.info(f"Prompt {prompt.pk}: Queued SEO rename task")
    except Exception as e:
        # Non-blocking: rename failure shouldn't break the upload flow
        logger.warning(f"Prompt {prompt.pk}: Failed to queue SEO rename: {e}")
```

---

### File 2: `prompts/tests/test_upload_views.py` (new file, 90 lines)

**`test_rename_task_queued_on_upload_submit`:**

```python
@patch('prompts.views.upload_views.async_task')
@patch(
    'prompts.services.profanity_filter.ProfanityFilterService.check_text',
    return_value=(True, [], 'none'),
)
def test_rename_task_queued_on_upload_submit(self, mock_profanity, mock_async_task):
    """rename_prompt_files_for_seo is queued after a successful B2 image upload submit."""
    from prompts.models import Prompt

    self._set_b2_image_session()
    response = self.client.post(self.url, {
        'content': 'A stunning portrait of a woman in a red dress',
        'ai_generator': 'midjourney',
        'tags': '[]',
        'save_as_draft': '1',
    })

    self.assertEqual(response.status_code, 302, 'Successful submit should redirect')
    prompt = Prompt.objects.filter(author=self.user).first()
    self.assertIsNotNone(prompt, 'Prompt should have been created')
    self.assertTrue(prompt.b2_image_url, 'b2_image_url must be set for guard to fire')
    mock_async_task.assert_called_once_with(
        'prompts.tasks.rename_prompt_files_for_seo',
        prompt.pk,
        task_name=f'seo-rename-{prompt.pk}',
    )
```

**`test_rename_task_not_queued_without_b2_url`:**

```python
@patch('prompts.views.upload_views.async_task')
@patch(
    'prompts.services.profanity_filter.ProfanityFilterService.check_text',
    return_value=(True, [], 'none'),
)
def test_rename_task_not_queued_without_b2_url(self, mock_profanity, mock_async_task):
    """rename_prompt_files_for_seo is not queued when b2_image_url is absent (video upload).

    save_as_draft='1' is intentional: it bypasses queue_pass2_review, which uses a local
    async_task import that would not affect mock_async_task but keeps the test focused.
    """
    self._set_b2_video_session()
    response = self.client.post(self.url, {
        'resource_type': 'video',
        'content': 'A cinematic video scene with dramatic lighting',
        'ai_generator': 'runway',
        'tags': '[]',
        'save_as_draft': '1',
    })

    self.assertIn(response.status_code, [200, 302], 'View should complete without error')
    mock_async_task.assert_not_called()
```

---

## Section 4 — Issues Encountered and Resolved

### Issue 1: Core fix already present from Session 67

**Discovery:** Reading `upload_views.py` before writing any code revealed that `async_task` was
already being called at lines 525–538. Commit `ac1e5ea` (Session 67, February 4, 2026) had added
the call.

**Root cause:** The CLAUDE.md blocker entry "N4h rename (upload-flow) still not triggering" was
written at a point in the project history when the fix did not yet exist. Multiple sessions passed
without the blocker being closed, and the spec (written March 12, 2026) was authored based on this
stale blocker entry.

**Resolution:** Proceeded with the spec as written. The remaining work was meaningful:
(a) tightening the guard to `prompt.b2_image_url`, (b) moving the import to module level, and
(c) adding tests that didn't exist. The commit documents this clearly.

### Issue 2: `@patch('prompts.views.upload_views.async_task')` requires module-level import

**Discovery:** The spec's suggested `@patch` decorator only intercepts a name if that name exists
at module level in the patched module. The original code used `from django_q.tasks import async_task`
inside the `try` block (lazy local import). Patching `prompts.views.upload_views.async_task` on a
local import would silently fail — the patch would succeed but have no effect on the function's
local binding.

**Root cause:** The SMOKE2-FIX-D pattern used local imports inside `tasks.py` functions. This was
appropriate for `tasks.py` (which runs in Django-Q worker context and needs defensive lazy imports).
For a view module like `upload_views.py`, a module-level import is idiomatic and testable.

**Resolution:** Moved `from django_q.tasks import async_task` to the module-level import block.
This makes `prompts.views.upload_views.async_task` a valid patch target.

### Issue 3: No existing upload submit test file to replicate patterns from

**Discovery:** The spec said "read the existing upload tests to replicate the exact setup pattern."
No `test_upload_views.py` existed. No other test file tested `upload_submit`.

**Resolution:** Modelled the test class on `test_bulk_generator_views.py` (same project, same test
patterns). The test setup uses Django's `TestClient`, session manipulation, and `@patch` decorators
in the standard Django test pattern.

### Git archaeology findings (SMOKE2-FIX-D, commit `0b1618a`)

- **File edited:** `prompts/tasks.py`
- **Functions edited:** `create_prompt_pages_from_job` and `publish_prompt_pages_from_job`
- **Pattern used:** Local import inside `try` block — `from django_q.tasks import async_task`
- **Preconditions:** Called outside `transaction.atomic()` to ensure task is only queued after DB commit
- **Guard used:** No explicit guard beyond `_already_published` flag (per-image idempotency)
- **`task_name` kwarg:** `task_name=f'seo-rename-{prompt_page.pk}'` — matched in upload-flow fix

---

## Section 5 — Remaining Issues

### Remaining issue 1: CLAUDE.md N4h blocker entry is outdated

The entry in CLAUDE.md under "Current Blockers" still reads:
> **N4h rename (upload-flow)** | `rename_prompt_files_for_seo` still not triggering for
> upload-flow prompts...

This should be removed. The fix is committed and the blocker is closed. This update should be
part of the end-of-session docs update spec.

### Remaining issue 2: Production verification not completed

The spec's manual verification step (upload a prompt, check `b2_image_url` in shell, confirm SEO
filename) was not completed in this session. No deployment to production was made.

**Recommended steps to verify after next deploy:**

```bash
heroku run python manage.py shell --app mj-project-4
>>> from prompts.models import Prompt
>>> p = Prompt.objects.filter(b2_image_url__isnull=False).latest('created_on')
>>> p.b2_image_url
# Should show a slug-based filename, not a UUID
# e.g. "https://cdn.promptfinder.net/media/images/2026/03/original/portrait-woman-red-dress-midjourney-prompt.jpg"
```

If the filename is still UUID-based, check Django-Q worker logs for the rename task:
```bash
heroku logs --tail --dyno worker --app mj-project-4 | grep seo-rename
```

### Remaining issue 3: Pre-existing `@csp_exempt` decorator gap (flagged by @django-pro)

In `upload_views.py` lines 235–237:
```python
@login_required
@csp_exempt


def upload_submit(request):
```

There is a blank line between `@csp_exempt` and `def upload_submit`. In Python, decorators must
immediately precede `def` (or the next decorator). The blank line causes `@csp_exempt` to not be
applied to `upload_submit`. This is a pre-existing bug, not introduced by this spec, but it means
the Content-Security-Policy exemption is not active on this view.

**Fix:** Remove the blank line between `@csp_exempt` and `def upload_submit`.

### Remaining issue 4: Pre-existing debug `print()` statements in production view

`upload_views.py` contains multiple `print(f"[DEBUG upload_submit]...")` statements that emit
to Heroku logs on every form submission. These should be converted to `logger.debug(...)` calls
or removed before launch.

---

## Section 6 — Concerns and Areas for Improvement

### Concern 1: Other upload-flow code paths that may be missing the rename task

The spec asked specifically about this. Review of the codebase identified these Prompt creation
paths and their rename task status:

| Code path | File | Rename task queued? |
|-----------|------|-------------------|
| Upload-flow (image + video) | `upload_views.py: upload_submit` | ✅ Yes (since ac1e5ea; guard tightened in a9acbc4) |
| Bulk-gen create-pages | `tasks.py: create_prompt_pages_from_job` | ✅ Yes (SMOKE2-FIX-D, 0b1618a) |
| Bulk-gen publish-pages | `tasks.py: publish_prompt_pages_from_job` | ✅ Yes (SMOKE2-FIX-D, 0b1618a) |
| Admin direct Prompt creation | `admin.py` | ⚠️ Not checked — investigate |
| Bulk import (if exists) | Unknown | ⚠️ Not applicable (no bulk import exists) |

The admin path should be verified. If admins can create Prompts with B2 URLs directly through
the Django admin, those prompts may also miss the rename task. Search `admin.py` for `b2_image_url`
assignments and confirm whether `rename_prompt_files_for_seo` is queued there.

### Concern 2: The rename task is a no-op for video uploads even when queued

`rename_prompt_files_for_seo` only processes image URL fields (`b2_image_url`, `b2_thumb_url`,
`b2_medium_url`, `b2_large_url`, `b2_webp_url`). It does not rename `b2_video_url`. Video upload
prompts never get SEO-friendly filenames. This is a feature gap, not a bug — the spec did not
require video rename support. However, it should be noted for V2 planning.

### Concern 3: The `is_b2_upload and prompt.pk` guard was confusing

The original guard used a session flag (`is_b2_upload`) rather than the model field
(`prompt.b2_image_url`). Session state is less reliable than model state for a guard that controls
a background task. The new guard checks the actual data that the task will operate on, making the
intent explicit and the test trivial to write.

**Guidance for future code:** When guarding a background task that processes a model field, always
guard on the model field, not on session or request state.

---

## Section 7 — Agent Ratings

### Round 1

| Agent | Score | Key Findings | Acted On? |
|-------|-------|-------------|-----------|
| @django-pro | 8.5/10 | Placement correct; `prompt.pk` guaranteed at guard point; `b2_image_url` definitely set before guard; B2 upload confirmed complete before submit (no async window); module-level import acceptable and idiomatic; pre-existing `@csp_exempt` blank-line decorator gap flagged; negative test should assert response status code | Yes — response status assertion added to negative test |
| @test-automator | 8.2/10 | Patch target `prompts.views.upload_views.async_task` correct for module-level import; positive test does not prove guard alone (requires pairing with negative test, which is present); `assert_not_called()` fragility if `save_as_draft` removed (comment added); missing HTTP status assertion on positive test; missing `prompt.b2_image_url` assertion before mock call assertion | Yes — status assertion and b2_image_url assertion added to positive test; comment added to negative test |

**Average: 8.35/10 — exceeds 8.0 threshold. ✅**

---

## Section 8 — Recommended Additional Agents

| Agent | What they would have reviewed |
|-------|------------------------------|
| @code-reviewer | Checked for overall code quality, the pre-existing `@csp_exempt` blank-line bug, debug print() statements, and whether the import ordering follows PEP8 conventions |
| @security-auditor | Reviewed whether the `b2_image_url` guard is sufficient as a security boundary (e.g. can a user inject a non-B2 URL into the session?) and confirmed the profanity filter mock does not create a security bypass in tests |

---

## Section 9 — How to Test

### Automated tests

**Run isolated (new tests only):**
```bash
python manage.py test prompts.tests.test_upload_views -v 2
# Expected: Ran 2 tests in ~2.6s OK
```

**Run full suite:**
```bash
python manage.py test
# Expected: Ran 1149 tests ... OK (skipped=12)
```

**Actual results:**
- Isolated: `Ran 2 tests in 2.646s OK`
- Full suite: `Ran 1149 tests in 1119.854s OK (skipped=12)`

### Manual production verification (not yet completed)

1. Deploy the fix to Heroku
2. Log in and upload a new image prompt through the upload page
3. Wait ~30 seconds for the Django-Q worker to process the rename task
4. Check the filename in the Django shell:

```python
# heroku run python manage.py shell --app mj-project-4
from prompts.models import Prompt
p = Prompt.objects.filter(b2_image_url__isnull=False).latest('created_on')
print(p.b2_image_url)
# Expected: SEO slug, e.g. "portrait-woman-red-dress-midjourney-prompt.jpg"
# Not expected: UUID like "a1b2c3d4-e5f6-7890-abcd.jpg"
```

5. If UUID is still present, check worker logs:
```bash
heroku logs --tail --dyno worker --app mj-project-4 | grep "seo-rename\|rename_prompt"
```

**Manual verification status: NOT COMPLETED.** No production deploy was made in this session.

---

## Section 10 — Commits

| Hash | Description |
|------|-------------|
| `a9acbc4` | fix(upload): N4H — queue rename_prompt_files_for_seo on upload submit |

**Changes in `a9acbc4`:**
- `prompts/views/upload_views.py` — `async_task` moved to module-level import; guard changed from `is_b2_upload and prompt.pk` to `prompt.b2_image_url`; comment updated
- `prompts/tests/test_upload_views.py` — new file with 2 tests

**For reference (pre-existing, not part of this spec):**
- `ac1e5ea` — feat(N4h): Add SEO file renaming for B2 uploads (Session 67, Feb 4 2026) — original async_task call added
- `0b1618a` — feat(bulk-gen): queue SEO rename task after publishing prompt pages (SMOKE2-FIX-D, Session 121, Mar 11 2026) — bulk-gen path fixed

---

## Section 11 — What to Work on Next

1. **Frozenset micro-spec (`VALID_PROVIDERS`, `VALID_VISIBILITIES`, `create_test_gallery.py`).**
   Hard-code the provider/visibility validation logic into frozenset constants to eliminate
   repeated string comparisons. Add `create_test_gallery.py` helper for test fixture creation.
   This was flagged in CLAUDE.md as the next item after the N4h fix.

2. **Session 122 docs update spec.** Update all four core docs:
   - `CLAUDE.md` — remove the N4h blocker entry (now resolved); update test count to 1149;
     update the recently completed table to include this fix
   - `CLAUDE_CHANGELOG.md` — add Session 122 entry covering all work done in this session
   - `CLAUDE_PHASES.md` — update Phase N4 status to reflect N4h is fully resolved
   - `PROJECT_FILE_STRUCTURE.md` — add `prompts/tests/test_upload_views.py`

3. **`detect_b2_orphans` management command spec.** Build the B2-aware orphan detection
   command to replace the non-functional Cloudinary-based `detect_orphaned_files` command.
   Must cross-reference `Prompt.b2_image_url`, `Prompt.b2_large_url`, `Prompt.b2_thumb_url`,
   `GeneratedImage` B2 URL fields, and understand the shared-file window before flagging files
   as orphans. Must maintain the same CSV report and email notification patterns as the original.
   See the "Orphan Detection — B2 Migration Gap" section in CLAUDE.md for full requirements.

4. **Bulk job deletion spec.** Implement soft-delete for `BulkGenerationJob` following the
   Phase D.5 pattern for Prompts. Requires: soft-delete fields + migration, `JobReceipt` model,
   `DeletionAuditLog` model, pre-deletion checklist (shared-file safety check), Django-Q cleanup
   task, and `cleanup_deleted_jobs` management command. Do NOT build the frontend delete UI until
   items 1–6 are complete and tested. See "Bulk Job Deletion — Pre-Build Reference" in CLAUDE.md
   for the full safety checklist that must be followed.
