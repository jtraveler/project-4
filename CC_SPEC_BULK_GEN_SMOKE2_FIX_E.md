# CC_SPEC_BULK_GEN_SMOKE2_FIX_E — Relocate Bulk-Gen Images to Standard media/images Path

**Spec ID:** SMOKE2-FIX-E
**Created:** March 11, 2026
**Type:** Micro-Spec — P1 Structural Fix
**Template Version:** v2.5
**Modifies UI/Templates:** No

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Use required agents** — @django-pro, @code-reviewer, and @security-auditor are MANDATORY
4. **Report agent usage** — Include ratings and findings in completion summary

**Work is REJECTED if agents are not run or average score is below 8.0/10.**

---

## 📋 OVERVIEW

### Bulk-Gen Images Live at Wrong Path — Must Relocate to Standard Structure

Images published through the Bulk Generator are stored at `bulk-gen/{job_id}/{seo-filename}.jpg` after the SMOKE2-FIX-D rename pass. Upload-flow images land at `media/images/{year}/{month}/large/{seo-filename}.jpg`. Having two different path structures for the same content type is architecturally untidy, makes URL patterns inconsistent, and becomes increasingly costly to fix as image count grows.

Decision: **Relocate all bulk-gen images to `media/images/{year}/{month}/large/`** — fully consistent with the upload flow. This must happen during the rename step so images land in the correct location from birth on future publishes, and a backfill handles existing prompts.

### Scope

- Modify `B2RenameService` to support full-path relocation (not just filename replacement)
- Modify `rename_prompt_files_for_seo` to detect bulk-gen paths and target the standard directory
- Update `backfill_bulk_gen_seo_rename` management command to relocate existing prompts
- Clean up stale `bulk-gen/{job_id}/` directory prefixes after relocation (delete any remaining B2 keys under that prefix)

---

## 🎯 OBJECTIVES

### Primary Goal

All bulk-gen published prompt images live at `media/images/{year}/{month}/large/{seo-filename}.jpg` — identical path structure to upload-flow images. The `bulk-gen/` prefix is eliminated from all Prompt URL fields.

### Success Criteria

- ✅ `B2RenameService` has a new `move_file(old_url, target_directory, new_filename)` method that copies to a fully-specified new key, verifies copy, deletes original, returns new CDN URL
- ✅ `rename_prompt_files_for_seo` detects bulk-gen URLs and targets `media/images/{year}/{month}/large/` using `prompt.created_at` for year/month
- ✅ `rename_prompt_files_for_seo` correctly handles the thumb and medium subdirectories: `media/images/{year}/{month}/thumb/` and `media/images/{year}/{month}/medium/` for `b2_thumb_url` and `b2_medium_url` respectively
- ✅ Stale `bulk-gen/{job_id}/` keys are deleted from B2 after successful relocation
- ✅ `backfill_bulk_gen_seo_rename` management command updated to relocate existing 6 prompts
- ✅ After backfill, no Prompt has `b2_image_url__contains='bulk-gen/'`
- ✅ After backfill, no orphaned keys remain under `bulk-gen/` prefix in B2
- ✅ No migration needed
- ✅ Full test suite passes

---

## 🔍 PROBLEM ANALYSIS

### Current State

After SMOKE2-FIX-D, a bulk-gen published prompt's URLs look like:
```
b2_image_url:  https://media.promptfinder.net/bulk-gen/{job_id}/{seo-name}-ai-prompt.jpg
b2_thumb_url:  https://media.promptfinder.net/bulk-gen/{job_id}/{seo-name}-ai-prompt.jpg
b2_medium_url: https://media.promptfinder.net/bulk-gen/{job_id}/{seo-name}-ai-prompt.jpg
b2_large_url:  https://media.promptfinder.net/bulk-gen/{job_id}/{seo-name}-ai-prompt.jpg
```

### Target State

After this fix, the same prompt's URLs should look like:
```
b2_image_url:  https://media.promptfinder.net/media/images/2026/03/large/{seo-name}-ai-prompt.jpg
b2_thumb_url:  https://media.promptfinder.net/media/images/2026/03/thumb/{seo-name}-ai-prompt.jpg
b2_medium_url: https://media.promptfinder.net/media/images/2026/03/medium/{seo-name}-ai-prompt.jpg
b2_large_url:  https://media.promptfinder.net/media/images/2026/03/large/{seo-name}-ai-prompt.jpg
```

Note: Currently all four fields point to the same physical file (the full-resolution image used as fallback for all sizes). The relocation preserves this — all four fields still point to the same physical file, just organised into their correct subdirectory. Real size variants (thumb, medium, large as separate files) are Phase 7 scope.

### Why `B2RenameService.rename_file()` Is Insufficient

The existing `rename_file` method does:
```python
parts = old_key.rsplit('/', 1)
directory = parts[0]           # preserved as-is
new_key = f"{directory}/{new_filename}"
```

It explicitly preserves the original directory. A new `move_file` method is needed that accepts a `target_directory` argument and builds `new_key = f"{target_directory}/{new_filename}"` instead.

### Detection of Bulk-Gen Paths

`rename_prompt_files_for_seo` should detect bulk-gen images by checking if the URL contains `bulk-gen/`:

```python
is_bulk_gen = prompt.b2_image_url and 'bulk-gen/' in prompt.b2_image_url
```

If `is_bulk_gen` is True, use `move_file` with target directory `media/images/{year}/{month}/{size}/`. If False, use the existing `rename_file` behaviour unchanged.

### Year/Month Source

Use `prompt.created_at` for the year/month directory:
```python
year = prompt.created_at.strftime('%Y')
month = prompt.created_at.strftime('%m')
```

This is consistent with how Django's `upload_to` generates date-based paths for upload-flow images.

### Subdirectory Mapping

Since all four URL fields currently point to the same physical file, the relocation should:
- `b2_image_url` → `media/images/{year}/{month}/large/`
- `b2_thumb_url` → `media/images/{year}/{month}/thumb/`
- `b2_medium_url` → `media/images/{year}/{month}/medium/`
- `b2_large_url` → `media/images/{year}/{month}/large/`

`b2_image_url` and `b2_large_url` point to the same file and same target directory — the group-by-URL logic introduced in SMOKE2-FIX-D ensures the physical B2 copy+delete is done once, and the URL is mirrored to both fields. This is already handled correctly; no change needed to that logic.

### Stale Directory Cleanup

After all files under `bulk-gen/{job_id}/` have been moved and deleted (by the copy+delete rename process), the prefix is logically empty. However, to be safe, after the rename task completes for a prompt, add a cleanup step:

1. Extract the `job_id` from the original `b2_image_url` before rename
2. After all fields are successfully renamed, list all B2 keys with prefix `bulk-gen/{job_id}/`
3. Delete any remaining keys (there should be none if rename succeeded, but this catches edge cases)
4. Log the cleanup result

The cleanup should be best-effort and non-blocking — failure to clean up must not cause the rename task to fail or retry.

---

## 🔧 SOLUTION

### File 1: `prompts/services/b2_rename.py`

#### Add `move_file` Method

```python
def move_file(self, old_url: str, target_directory: str, new_filename: str) -> dict:
    """
    Move a file in B2 to a different directory with a new filename.

    Unlike rename_file (which preserves the original directory),
    move_file relocates the file to target_directory/new_filename.

    Args:
        old_url: Current CDN URL of the file
        target_directory: Target directory key (e.g., 'media/images/2026/03/large')
        new_filename: New filename (e.g., 'my-prompt-ai-prompt.jpg')

    Returns:
        dict: {
            'success': True/False,
            'new_url': 'https://cdn.../new-path',
            'old_url': 'https://cdn.../old-path',
            'error': None or error message
        }
    """
    try:
        old_key = self._url_to_key(old_url)
        if not old_key:
            return {
                'success': False,
                'new_url': None,
                'old_url': old_url,
                'error': f'Could not extract key from URL: {old_url}',
            }

        new_key = f"{target_directory}/{new_filename}"

        # Skip if old and new are the same
        if old_key == new_key:
            logger.info(f"[B2 Move] Skipping - already at target: {old_key}")
            return {
                'success': True,
                'new_url': old_url,
                'old_url': old_url,
                'error': None,
            }

        # Copy to new location
        self.client.copy_object(
            Bucket=self.bucket,
            CopySource={'Bucket': self.bucket, 'Key': old_key},
            Key=new_key,
            MetadataDirective='COPY',
        )

        # Verify copy before deleting original
        self.client.head_object(Bucket=self.bucket, Key=new_key)

        # Delete original
        self.client.delete_object(Bucket=self.bucket, Key=old_key)

        new_url = self._key_to_url(new_key)
        logger.info(f"[B2 Move] Moved: {old_key} -> {new_key}")

        return {
            'success': True,
            'new_url': new_url,
            'old_url': old_url,
            'error': None,
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"[B2 Move] B2 error ({error_code}): {e}")
        return {
            'success': False,
            'new_url': None,
            'old_url': old_url,
            'error': f'B2 error: {error_code}',
        }
    except Exception as e:
        logger.exception(f"[B2 Move] Unexpected error: {e}")
        return {
            'success': False,
            'new_url': None,
            'old_url': old_url,
            'error': str(e),
        }

def cleanup_empty_prefix(self, prefix: str) -> dict:
    """
    Delete any remaining B2 keys under a given prefix.

    Used after bulk-gen image relocation to clean up stale bulk-gen/{job_id}/ directories.
    Best-effort — logs results but does not raise exceptions.

    Args:
        prefix: B2 key prefix to clean up (e.g., 'bulk-gen/abc-123/')

    Returns:
        dict: {'deleted': int, 'errors': int}
    """
    deleted = 0
    errors = 0
    try:
        paginator = self.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                try:
                    self.client.delete_object(Bucket=self.bucket, Key=obj['Key'])
                    logger.info(f"[B2 Cleanup] Deleted orphaned key: {obj['Key']}")
                    deleted += 1
                except Exception as e:
                    logger.warning(f"[B2 Cleanup] Failed to delete {obj['Key']}: {e}")
                    errors += 1
    except Exception as e:
        logger.warning(f"[B2 Cleanup] Failed to list prefix {prefix}: {e}")
        errors += 1

    logger.info(f"[B2 Cleanup] Prefix '{prefix}': deleted={deleted}, errors={errors}")
    return {'deleted': deleted, 'errors': errors}
```

### File 2: `prompts/tasks.py` — `rename_prompt_files_for_seo`

#### Detect Bulk-Gen and Route to `move_file`

In the rename task, after building `seo_service = B2RenameService()`, add bulk-gen detection:

```python
# Detect bulk-gen prompts — relocate to standard media/images path
is_bulk_gen = bool(prompt.b2_image_url and 'bulk-gen/' in prompt.b2_image_url)

if is_bulk_gen:
    year = prompt.created_at.strftime('%Y')
    month = prompt.created_at.strftime('%m')
    # Map each field to its correct subdirectory
    bulk_gen_subdir_map = {
        'b2_image_url': f'media/images/{year}/{month}/large',
        'b2_thumb_url': f'media/images/{year}/{month}/thumb',
        'b2_medium_url': f'media/images/{year}/{month}/medium',
        'b2_large_url': f'media/images/{year}/{month}/large',
    }
    # Store original bulk-gen prefix for cleanup after rename
    from urllib.parse import urlparse
    original_key = seo_service._url_to_key(prompt.b2_image_url)
    # Extract bulk-gen/{job_id}/ prefix — everything up to and including the second /
    parts = original_key.split('/')
    bulk_gen_prefix = f"{parts[0]}/{parts[1]}/" if len(parts) >= 2 else None
```

The group-by-URL logic in the existing rename task iterates over unique physical files. For each unique URL, use `move_file` instead of `rename_file` when `is_bulk_gen` is True, passing the appropriate `target_directory` from `bulk_gen_subdir_map` for the first field that maps to this URL (since all four fields point to the same physical file, any subdir will do — use `large` as the canonical target for the shared physical file).

After all fields are renamed and saved, add the cleanup step:

```python
if is_bulk_gen and bulk_gen_prefix:
    try:
        cleanup_result = seo_service.cleanup_empty_prefix(bulk_gen_prefix)
        logger.info(
            "[SEO Rename] Bulk-gen cleanup for prefix '%s': %s",
            bulk_gen_prefix, cleanup_result
        )
    except Exception as e:
        # Non-blocking — cleanup failure must not affect task outcome
        logger.warning(
            "[SEO Rename] Bulk-gen cleanup failed for prefix '%s': %s",
            bulk_gen_prefix, e
        )
```

### File 3: `prompts/management/commands/backfill_bulk_gen_seo_rename.py`

Update the filter to match any remaining bulk-gen prompts (whether UUID-named or already SEO-renamed but still at bulk-gen path):

```python
qs = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__contains='bulk-gen/',
)
```

This is unchanged from SMOKE2-FIX-D — it will correctly find all 6 existing prompts since their `b2_image_url` still contains `bulk-gen/` even after the filename rename.

After running the command, add a verification query:

```python
remaining = Prompt.objects.filter(b2_image_url__contains='bulk-gen/').count()
self.stdout.write(f'Remaining bulk-gen paths in DB: {remaining} (should be 0)')
```

---

## ✅ PRE-AGENT SELF-CHECK

⛔ **Before invoking ANY agent, verify all of the following:**

- [ ] `B2RenameService.move_file()` exists in `b2_rename.py`
- [ ] `B2RenameService.cleanup_empty_prefix()` exists in `b2_rename.py`
- [ ] `rename_prompt_files_for_seo` detects `bulk-gen/` in URL and branches to `move_file`
- [ ] All four URL fields are mapped to correct subdirectories (large/thumb/medium/large)
- [ ] Cleanup step runs after successful rename and is non-blocking
- [ ] Management command updated with `b2_image_url__contains='bulk-gen/'` filter
- [ ] Management command includes post-run verification (remaining count = 0)
- [ ] `python manage.py makemigrations --check` → No changes detected
- [ ] Full test suite passes: `python manage.py test`

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

### Required Agents

**1. @django-pro**
- Focus: Is `prompt.created_at` the correct date source for year/month? Is the group-by-URL logic correctly extended to use `move_file` for bulk-gen paths? Is the bulk-gen prefix extraction (`parts[0]/parts[1]/`) correct and safe for all bulk-gen URL formats? Is the management command post-run verification correct?
- Rating requirement: 8+/10

**2. @code-reviewer**
- Focus: Is `move_file` structurally consistent with `rename_file` (same copy-verify-delete pattern)? Are there edge cases where `bulk-gen_prefix` could be incorrect or `None`? Is the cleanup step correctly non-blocking? Could the subdir mapping cause any field to point to a non-existent file?
- Rating requirement: 8+/10

**3. @security-auditor**
- Focus: Does `cleanup_empty_prefix` have any risk of deleting keys outside the intended prefix? Is the paginator correctly scoped to the bucket and prefix? Could a malformed URL cause `bulk_gen_prefix` to reference an unintended path?
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- `cleanup_empty_prefix` can delete keys outside the `bulk-gen/{job_id}/` prefix
- `move_file` does not verify the copy before deleting the original
- Cleanup step is blocking (can cause rename task failure)
- Management command does not include post-run verification

---

## 🧪 TESTING CHECKLIST

- [ ] `python manage.py makemigrations --check` → No changes detected
- [ ] Full test suite: `python manage.py test` — all pass, report total count
- [ ] After production backfill: `Prompt.objects.filter(b2_image_url__contains='bulk-gen/').count()` → 0
- [ ] After production backfill: spot-check one prompt detail page — image URL contains `media/images/2026/03/large/`

### ⛔ FULL SUITE GATE

`tasks.py` and `b2_rename.py` both modified → **Full test suite is mandatory.**

---

## 📊 CC COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
SMOKE2-FIX-E: BULK-GEN IMAGE RELOCATION - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY
[agent report]

## 📁 FILES MODIFIED / CREATED
[list with line numbers]

## 🧪 TESTING PERFORMED
[full suite output]

## ✅ SUCCESS CRITERIA MET
[checklist]

## 🔄 DATA MIGRATION STATUS
[Backfill command output — total, renamed, skipped, errors]
[Post-backfill verification: remaining bulk-gen paths = 0]

## 📝 NOTES
[Any observations]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
feat(bulk-gen): relocate bulk-gen images to standard media/images path

Bulk-gen images were stored at bulk-gen/{job_id}/{seo-name}.jpg after
SMOKE2-FIX-D rename. This diverged from upload-flow images which land
at media/images/{year}/{month}/large/{seo-name}.jpg.

Changes:
- B2RenameService: add move_file() for full-path relocation and
  cleanup_empty_prefix() to delete stale bulk-gen/{job_id}/ keys
- rename_prompt_files_for_seo: detect bulk-gen/ paths and use
  move_file() targeting media/images/{year}/{month}/{size}/ using
  prompt.created_at for year/month
- Cleanup step runs post-rename to purge stale bulk-gen prefix (non-blocking)
- backfill_bulk_gen_seo_rename: updated to relocate existing 6 prompts
  and verify 0 remaining bulk-gen paths post-run

Agent ratings: @django-pro X/10, @code-reviewer X/10, @security-auditor X/10
```
