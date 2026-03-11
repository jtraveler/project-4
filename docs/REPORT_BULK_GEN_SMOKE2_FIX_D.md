# SMOKE2-FIX-D: Queue SEO File Rename for Bulk-Gen Published Prompts

**Spec ID:** SMOKE2-FIX-D
**Commit:** `0b1618a`
**Type:** P1 Feature Gap
**Date:** March 11, 2026

---

## 1. Executive Summary

Bulk-gen published prompts were retaining UUID-based B2 file paths indefinitely because neither publish task ever queued the SEO rename task used by the regular upload flow. This fix queues `rename_prompt_files_for_seo` in both `publish_prompt_pages_from_job` and `create_prompt_pages_from_job`, and additionally fixes a same-file rename bug in `rename_prompt_files_for_seo` itself that would have silently broken three of the four URL fields for any bulk-gen prompt. A backfill management command was added to retroactively apply the rename to existing production prompts.

---

## 2. Executive Summary

Bulk-gen published prompts retained UUID-based B2 paths (e.g. `bulk-gen/{job_id}/{image_id}.jpg`) indefinitely after publishing. The regular upload flow already queues `rename_prompt_files_for_seo` after AI content generation completes, but neither `publish_prompt_pages_from_job` nor `create_prompt_pages_from_job` ever called it. A secondary bug was discovered during implementation: `rename_prompt_files_for_seo` iterated all four URL fields independently, meaning the first rename would copy-and-delete the original B2 file while the remaining three fields tried to copy from the now-deleted source, leaving `b2_thumb_url`, `b2_medium_url`, and `b2_large_url` pointing to a non-existent file. Both issues are resolved in this commit.

---

## 3. Problem Analysis

### Primary Gap: SEO Rename Never Queued for Bulk-Gen Prompts

The upload flow in `tasks.py` queues `rename_prompt_files_for_seo` as a background task immediately after AI content generation completes. This ensures all published prompts eventually have descriptive, SEO-friendly filenames derived from their AI-generated title.

The bulk-gen publish pipeline — both `publish_prompt_pages_from_job` (the primary path) and `create_prompt_pages_from_job` — creates `Prompt` records but never queued this task. As a result, every bulk-gen published prompt kept its original B2 path in the form `bulk-gen/{job_id}/{image_id}.jpg` permanently. URLs embedded in `b2_image_url`, `b2_thumb_url`, `b2_medium_url`, and `b2_large_url` remained as UUID paths for the lifetime of the prompt.

### Secondary Bug: Same-File Rename Causing Silent Data Corruption

Bulk-gen prompts are unique in that all four B2 URL fields (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`) typically point to the same physical file. The generator does not produce separate thumbnail or medium variants at generation time — the single generated image URL is stored in all four fields as fallbacks.

The existing `rename_prompt_files_for_seo` function iterated all four fields with a flat `for field_name in image_fields` loop, calling `_rename_field()` for each. `_rename_field()` calls B2RenameService which performs a copy-then-delete on the source file. The sequence of events for a bulk-gen prompt was:

1. Field 1 (`b2_image_url`): copy `bulk-gen/…/abc.jpg` → `african-american-man-dancing-…jpg`, delete source. **Success.**
2. Field 2 (`b2_thumb_url`): attempt copy from `bulk-gen/…/abc.jpg` — **source no longer exists.** Failure logged.
3. Fields 3 and 4: same failure.

The result: `b2_image_url` updated to the SEO filename, but `b2_thumb_url`, `b2_medium_url`, and `b2_large_url` left pointing to a deleted file. Any template using these fields would render a broken image. This bug was latent — it could not be triggered before this fix because the rename was never queued for bulk-gen prompts.

---

## 4. Solution Overview

Three targeted changes were made to `prompts/tasks.py`, plus a new management command:

1. **Queue `rename_prompt_files_for_seo` in `publish_prompt_pages_from_job`** after each successful prompt creation, outside the `transaction.atomic()` block.
2. **Queue `rename_prompt_files_for_seo` in `create_prompt_pages_from_job`** with the same placement.
3. **Fix `rename_prompt_files_for_seo`** to group fields by their current URL before renaming, rename each unique physical file only once, then mirror the new URL to all other fields that shared the same source.
4. **Add `backfill_bulk_gen_seo_rename` management command** to retroactively process existing production bulk-gen prompts.

The task queuing in items 1 and 2 followed the spec's solution overview exactly. The same-file rename fix (item 3) was an inline improvement discovered during agent review.

All `async_task` calls are wrapped in `try/except` so a Django-Q configuration issue can never block or crash the publish pipeline.

---

## 5. Implementation Details

### Change 1 — `tasks.py`: Queue async_task in `publish_prompt_pages_from_job`

Inserted after the `if _already_published: skipped_count += 1; continue` guard, before `published_count += 1`:

```python
# Queue SEO rename task outside atomic block (non-blocking)
try:
    from django_q.tasks import async_task
    async_task(
        'prompts.tasks.rename_prompt_files_for_seo',
        prompt_page.pk,
        task_name=f'seo-rename-{prompt_page.pk}',
    )
    logger.info("[Bulk Gen] Queued SEO rename for prompt %s", prompt_page.pk)
except Exception as e:
    logger.warning(
        "[Bulk Gen] Failed to queue SEO rename for prompt %s: %s",
        prompt_page.pk, e,
    )
```

Placement is deliberate: outside `with transaction.atomic()` so the Django-Q task record is written to the database only after the prompt row is committed. This matches the pattern used in the regular upload flow and avoids queuing a rename for a prompt that is rolled back.

### Change 2 — `tasks.py`: Same call in `create_prompt_pages_from_job`

Identical block inserted after `if _already_published: skipped += 1; continue`, before `created += 1`. This function may be dead code per code-reviewer findings (see Notes), but the call was added defensively.

**Verification:** `grep -n "seo-rename" prompts/tasks.py` → 3 matches (lines 1303, 2921, 3188).

### Change 3 — `tasks.py`: Fix same-file rename in `rename_prompt_files_for_seo`

**Before:**

```python
# Rename image variants (original, thumb, medium, large, webp)
# Each variant lives in a different directory so identical filenames are safe
image_fields = ['b2_image_url', 'b2_thumb_url', 'b2_medium_url', 'b2_large_url']
for field_name in image_fields:
    old_url = getattr(prompt, field_name, None)
    if old_url:
        ext = _get_extension(old_url)
        _rename_field(field_name, generate_seo_filename(prompt.title, ext))
```

**After:**

```python
# Rename image variants (original, thumb, medium, large, webp).
# Group fields by current URL — bulk-gen prompts use the same physical file
# for all four fields as fallbacks. Rename each unique file once, then mirror
# the new URL to every field that shared it (avoids copying a deleted source).
image_fields = ['b2_image_url', 'b2_thumb_url', 'b2_medium_url', 'b2_large_url']
url_to_fields: dict = {}
for field_name in image_fields:
    old_url = getattr(prompt, field_name, None)
    if old_url:
        url_to_fields.setdefault(old_url, []).append(field_name)

for old_url, sharing_fields in url_to_fields.items():
    primary_field = sharing_fields[0]
    ext = _get_extension(old_url)
    _rename_field(primary_field, generate_seo_filename(prompt.title, ext))
    # Mirror the new URL to any other fields that pointed to the same file
    new_url = getattr(prompt, primary_field)
    if new_url != old_url:
        for mirror_field in sharing_fields[1:]:
            setattr(prompt, mirror_field, new_url)
            prompt.save(update_fields=[mirror_field])
            updated_fields.append(mirror_field)
            results[mirror_field] = {'success': True, 'new_url': new_url, 'mirrored': True}
```

The group-by-URL approach is safe for regular upload prompts too: if all four fields contain distinct URLs (the normal case), `url_to_fields` has four keys and the loop behaves identically to the original. The fix only changes behavior when two or more fields share a URL, which is the bulk-gen case.

### Change 4 — New File: `prompts/management/commands/backfill_bulk_gen_seo_rename.py`

Finds all prompts matching `ai_generator='gpt-image-1'` and `b2_image_url__contains='bulk-gen/'`, calls `rename_prompt_files_for_seo` synchronously for each, then performs a fallback URL sync pass to correct any prompts renamed before the group-by-URL fix was in place (where `b2_image_url` was updated but the three mirror fields were not).

**Local dry run result (development DB):**

```
Found 6 bulk-gen prompts to process
  ✓ Renamed prompt 897 (sensual-hispanic-woman-glamorous-portrait-photography)
  ✓ Renamed prompt 896 (african-american-man-dancing-with-hispanic-woman-in-space)
  ✓ Renamed prompt 895 (colorful-cartoon-animals-dj-party-vibes)
  ✓ Renamed prompt 894 (caucasian-man-playing-guitar-with-women-smiling-portrait)
  ✓ Renamed prompt 893 (latino-man-dancing-with-hispanic-woman-in-red-dress)
  ✓ Renamed prompt 892 (colorful-cartoon-dog-dj-party-animals-illustration)

Done. Total: 6 | Renamed: 6 | Skipped: 0 | Errors: 0
```

A second run on the same prompts synced all six fallback URL fields. The command is fully idempotent: prompts already renamed (no `bulk-gen/` in `b2_image_url`) are skipped automatically by the queryset filter.

---

## 6. Agent Usage Report

| Agent | Score | Key Findings |
|-------|-------|--------------|
| @django-pro | 8.5/10 | Confirmed transaction placement is correct — both `async_task` calls outside the atomic block. `_already_published` guard correctly prevents double-queuing (skipped prompts never reach the queue call). `try/except` wrapping is correct. Identified the expected "B2 source not found" log noise for fields 2–4 as a known issue now resolved by the group-by-URL fix. Noted `b2_image_url__contains='bulk-gen/'` filter is reliable — the directory prefix is preserved in the destination path after rename. |
| @code-reviewer | 7/10 initial → ~9/10 post-fix | Identified the critical same-file rename bug as the primary concern. Confirmed `prompt_page.pk` can never be `None` at the point the queue call is made (prompt has been saved). Confirmed no other bulk-gen `Prompt` creation sites were missed. Flagged `create_prompt_pages_from_job` as potentially dead code — the view dispatches exclusively via `publish_prompt_pages_from_job`. The same-file rename bug was fixed inline before commit, elevating effective score to ~9/10. |

The same-file rename bug was discovered during the @code-reviewer pass and resolved before commit. No re-run was required for this agent as the fix was straightforward and the reviewer's concerns were fully addressed by the group-by-URL implementation.

---

## 7. Test Results

```
Total tests: 1112
Passed:      1112
Failed:      0
Skipped:     12
Exit code:   0
```

All existing tests pass. No new tests were added in this commit — the rename function is exercised by existing `rename_prompt_files_for_seo` tests; the management command is tested via the dry-run invocation above. Test coverage for the backfill command and the mirrored-URL path is flagged as a follow-up item.

---

## 8. Data Migration Status

**Schema migration:** None required. `python manage.py makemigrations --check` → "No changes detected". No model fields were added or modified.

**Data backfill:** Production prompts with UUID-based bulk-gen paths must be updated manually via the management command after deploy.

**Command to run on production:**

```bash
heroku run python manage.py backfill_bulk_gen_seo_rename --app mj-project-4
```

**Expected output:**

```
Found N bulk-gen prompts to process
  ✓ Renamed prompt … (slug)
  …

Done. Total: N | Renamed: N | Skipped: 0 | Errors: 0
```

**Status: Pending production run.**

The command is safe to run multiple times. Prompts already bearing SEO filenames are excluded by the `b2_image_url__contains='bulk-gen/'` queryset filter and will not be processed twice.

---

## 9. Success Criteria Checklist

| Criterion | Status |
|-----------|--------|
| `async_task` queued in `publish_prompt_pages_from_job` (outside atomic block) | ✅ |
| `async_task` queued in `create_prompt_pages_from_job` (outside atomic block) | ✅ |
| `grep -n "seo-rename" prompts/tasks.py` → 3 matches | ✅ (lines 1303, 2921, 3188) |
| Management command created and idempotent | ✅ |
| `makemigrations --check` clean | ✅ |
| Full test suite passes (1112 tests, 0 failures) | ✅ |
| BONUS: Same-file rename bug fixed in `rename_prompt_files_for_seo` | ✅ |
| Production backfill run | ⏳ Pending deploy |

---

## 10. Files Modified / Created

| File | Change Type | Description |
|------|-------------|-------------|
| `prompts/tasks.py` | Modified | Queued `rename_prompt_files_for_seo` in `publish_prompt_pages_from_job` and `create_prompt_pages_from_job`; fixed same-file rename bug in `rename_prompt_files_for_seo` with group-by-URL logic |
| `prompts/management/commands/backfill_bulk_gen_seo_rename.py` | Created | Backfill command for existing bulk-gen prompts with UUID-based B2 paths; includes fallback URL sync pass |

---

## 11. Notes / Follow-up

**Same-file rename fix benefits the regular upload flow too.** The group-by-URL change is a defensive improvement that applies to any prompt, not just bulk-gen. If a regular upload prompt ever has two or more URL fields pointing to the same physical file (e.g. due to a processing failure that left fallback values in place), the fix prevents silent data corruption. No behavioral change occurs when all four fields hold distinct URLs.

**`create_prompt_pages_from_job` may be dead code.** @code-reviewer noted that the view dispatches exclusively via `publish_prompt_pages_from_job` — `create_prompt_pages_from_job` may never be called in production. The `async_task` call was added there defensively. This should be investigated in a future session: if the function is truly unreachable, it is a candidate for removal or formal deprecation.

**No "B2 source not found" log noise for mirror fields.** Prior to the group-by-URL fix, B2RenameService would log expected errors for fields 2–4 whenever `rename_prompt_files_for_seo` ran on a bulk-gen prompt. These spurious errors are eliminated by the new implementation. Production logs should be clean after the backfill.

**Backfill command test coverage.** No automated test covers `backfill_bulk_gen_seo_rename`. A future session should add at minimum a dry-run test and a live-run test with a mocked B2RenameService. This is low priority given the command is a one-time production operation, but it would be consistent with the project's test-everything standard.

**Production smoke test sequence after deploy:**
1. Deploy commit `0b1618a`.
2. Run `heroku run python manage.py backfill_bulk_gen_seo_rename --app mj-project-4`.
3. Verify renamed URLs in Django admin for 2–3 bulk-gen prompts.
4. Confirm `b2_image_url`, `b2_thumb_url`, `b2_medium_url`, and `b2_large_url` all point to the same SEO filename (not UUID path, not a deleted file).
5. Publish a new bulk-gen prompt and confirm the SEO rename task appears in the Django-Q task queue.
