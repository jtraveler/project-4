# SMOKE2-FIX-E: Bulk-Gen Image Relocation — Completion Report

**Spec:** CC_SPEC_BULK_GEN_SMOKE2_FIX_E.md
**Session:** March 11, 2026
**Commit:** `64c3ab1`
**Heroku Release:** v653

---

## 1. Overview

Bulk-gen published prompt images were stored at `bulk-gen/{job_id}/{seo-name}.jpg` after the SMOKE2-FIX-D rename pass. Upload-flow images land at `media/images/{year}/{month}/large/{seo-name}.jpg`. Having two different path structures for the same content type is architecturally inconsistent and becomes increasingly costly to fix as image count grows.

This fix relocated all bulk-gen images to the standard `media/images/{year}/{month}/large/` path, eliminating the `bulk-gen/` prefix from all Prompt URL fields and cleaning up orphan files in B2.

---

## 2. Expectations vs. Outcomes

| Expectation | Outcome |
|-------------|---------|
| `B2RenameService.move_file()` method added | ✅ Implemented with copy-verify-delete pattern |
| `B2RenameService.cleanup_empty_prefix()` method added | ✅ Implemented with paginated list+delete |
| `rename_prompt_files_for_seo` detects bulk-gen and uses `move_file` | ✅ Detects via `'bulk-gen/' in prompt.b2_image_url` |
| All four URL fields mapped to `media/images/{year}/{month}/large/` | ✅ Primary field moved; mirror fields get same URL |
| Stale `bulk-gen/{job_id}/` keys deleted from B2 after backfill | ✅ 7 orphan files deleted during backfill cleanup |
| `backfill_bulk_gen_seo_rename` relocates all existing 6 prompts | ✅ 6/6 renamed, 0 errors |
| After backfill: `Remaining bulk-gen paths in DB: 0` | ✅ Confirmed |
| No migration needed | ✅ `makemigrations --check` → No changes |
| Full test suite passes | ✅ 1112 tests, 12 skipped, OK |

---

## 3. Improvements Made

### `prompts/services/b2_rename.py`

**`move_file(old_url, target_directory, new_filename)`** — New method for full-path B2 relocation. Follows the same copy-verify-delete pattern as `rename_file` but builds `new_key = f"{target_directory}/{new_filename}"` instead of preserving the original directory. Returns the standard `{success, new_url, old_url, error}` dict.

**`cleanup_empty_prefix(prefix)`** — New method that paginates `list_objects_v2` and deletes all keys under a given prefix. Best-effort (never raises): per-object errors are caught and counted; paginator errors are caught and counted. Returns `{deleted: int, errors: int}`.

### `prompts/tasks.py` — `rename_prompt_files_for_seo`

**Bulk-gen detection:**
```python
is_bulk_gen = bool(prompt.b2_image_url and 'bulk-gen/' in prompt.b2_image_url)
```

**Subdir mapping:** Each URL field maps to a target directory. In practice, all four fields share one physical file, so the primary field (`b2_image_url`) is moved to `large/` and all mirror fields are pointed to the same URL — no additional B2 ops.

**Mirror-not-repeat pattern (critical bug fix):** The original implementation independently called `move_file` for each mirror field after the primary field's `move_file` already deleted the source. This caused "NoSuchKey" B2 errors for all mirror fields. Fixed by using the same URL-mirror pattern as upload-flow (set field = new_url, no B2 op).

**`_rename_field` → `_rename_or_move_field` (bug fix):** WebP and video fields called the old `_rename_field` function name which no longer existed after the refactor. Fixed to call `_rename_or_move_field`.

**`parts[1]` non-empty guard:** Prevents `bulk_gen_prefix` from becoming `bulk-gen//` if a malformed double-slash URL ever reached this code.

**Per-prompt cleanup (safe by design):** The per-prompt rename task no longer calls `cleanup_empty_prefix`. Instead, it uses `list_objects_v2(MaxKeys=1)` to check and log whether the prefix is empty. This prevents deleting sibling prompts' files from the same job that haven't been renamed yet.

### `prompts/management/commands/backfill_bulk_gen_seo_rename.py`

- Collects unique bulk-gen prefixes before processing each prompt
- Post-run verification: `Prompt.objects.filter(b2_image_url__contains='bulk-gen/').count()` → should be 0
- Post-rename cleanup: iterates collected prefixes and calls `cleanup_empty_prefix` after confirming `remaining == 0` — safe because all DB records have been updated by this point; any remaining B2 keys are true orphans

---

## 4. Issues Encountered and Resolved

### Issue 1: `prompt.created_at` vs `prompt.created_on`
The spec incorrectly referenced `prompt.created_at`. The model uses `created_on = DateTimeField(auto_now_add=True)`. Detected by grepping `models.py` before writing code. Fixed: used `prompt.created_on` throughout.

### Issue 2: Mirror-on-deleted-source bug (CRITICAL)
The initial implementation called `_rename_or_move_field(mirror_field, ...)` for each sharing field. This reads `getattr(prompt, mirror_field)` at call time — the old bulk-gen URL — and passes it to `move_file`, which tries to copy from an already-deleted source. Result: B2 NoSuchKey errors for all mirror fields.

**Root cause:** `move_file` uses copy+delete atomically. After moving the primary field, the source no longer exists.

**Fix:** All sharing fields (primary + mirrors) that had the same old URL now use the same URL-mirror pattern regardless of whether it's bulk-gen or upload-flow.

### Issue 3: Cleanup blast-radius on multi-prompt jobs (CRITICAL — code-reviewer and security-auditor)
The initial implementation called `cleanup_empty_prefix` at the end of each per-prompt rename. For jobs with multiple prompts, the first rename would run cleanup and delete sibling prompts' files before they could be moved.

**Example:** Job with 3 prompts — after prompt A's rename, cleanup deletes prompt B's and C's files. When prompt B's rename runs, its source is already gone.

**Fix:** Per-prompt task only checks prefix emptiness (logs, never deletes). Actual cleanup deferred to backfill command which runs after ALL prompts are confirmed relocated (remaining == 0).

### Issue 4: `_rename_field` undefined for webp/video fields
After refactoring the inner function to `_rename_or_move_field`, the webp and video field rename calls still referenced the old `_rename_field` name. Caught by @django-pro agent reading the code. Fixed by updating the three call sites.

### Issue 5: Missing `parts[1]` non-empty guard
Both @code-reviewer and @security-auditor flagged that `bulk_gen_prefix` could become `bulk-gen//` if `parts[1]` is empty (e.g., a malformed URL with double slash). Added `and parts[1]` to the guard.

---

## 5. Remaining Issues

**Known limitation:** All four URL fields (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`) point to the same physical `large/` file after relocation. Bulk-gen currently doesn't generate real thumbnail/medium variants. `display_thumb_url` and `display_medium_url` on these prompts return the full-res image. Real size variants are a future phase concern.

**No dedicated test for sibling-check path:** The 1112 existing tests cover the rename logic but don't specifically test the "skip cleanup if sibling files remain" branch. Adding a unit test for this would improve coverage.

---

## 6. Concerns and Areas for Improvement

- **`cleanup_empty_prefix` has no prefix allowlist**: Callers must validate the prefix (which they do — `bulk-gen/` check + `parts[1]` guard). Defense-in-depth could add a prefix allowlist to the method itself.
- **Backfill cleanup gated on `remaining == 0`**: If the backfill crashes partway through, the cleanup phase won't run. Orphan B2 files in `bulk-gen/` are harmless (no storage cost at current scale) but will persist until the next successful full run.
- **Multiple `prompt.save()` calls**: Each mirror field update triggers a separate DB write. For bulk-gen with 4 sharing fields, this is 4 separate saves. Could be batched into a single save with `update_fields=[field_1, field_2, ...]` for the mirror fields. Minor performance concern for background tasks.

---

## 7. Agent Ratings

| Agent | Initial | Post-Fix | Notes |
|-------|---------|----------|-------|
| @django-pro | 7/10 | Re-run N/A (key bugs fixed before re-run) | Caught `_rename_field` undefined bug; confirmed `created_on` correct |
| @code-reviewer | 7/10 | **8.5/10** | Initial: blast-radius, `_rename_field` bug, mirror-on-deleted bug. Post-fix: blast-radius resolved, mirror logic confirmed correct, unused import removed |
| @security-auditor | 7/10 | **8.5/10** | Initial: cleanup blast-radius, missing `parts[1]` check. Post-fix: all critical issues resolved, `parts[1]` guard closes edge case |

**Average post-fix score: 8.5/10** (above the 8.0 threshold)

---

## 8. Recommended Additional Agents

For future bulk-gen features:
- **@test-automator** — Add dedicated test for the sibling-check cleanup path and `move_file` with mocked S3 responses
- **@performance-engineer** — Batch the mirror field `prompt.save()` calls into a single DB write

---

## 9. How to Test

### Verify 0 bulk-gen paths in DB (production)
```bash
heroku run python manage.py shell --app mj-project-4
>>> from prompts.models import Prompt
>>> Prompt.objects.filter(b2_image_url__contains='bulk-gen/').count()
0
```

### Spot-check prompt image URL
Check any of the 6 relocated prompts in the Django admin. `b2_image_url` should contain `media/images/2026/03/large/` (not `bulk-gen/`).

### Verify images display correctly
Visit any of the 6 relocated prompt detail pages on production. Images should load correctly from the new CDN path.

### Future new bulk-gen publishes
When publishing a new batch, the SEO rename task will automatically move images from `bulk-gen/{job_id}/` to `media/images/{year}/{month}/large/` within seconds of publishing.

---

## 10. Commits

| Hash | Description |
|------|-------------|
| `64c3ab1` | `feat(bulk-gen): relocate bulk-gen images to standard media/images path` |

**Heroku:** v653, deployed successfully
**Backfill:** `Total: 6 | Renamed: 6 | Skipped: 0 | Errors: 0`
**Verification:** `Remaining bulk-gen paths in DB: 0 (should be 0) ✓`
**B2 orphan cleanup:** 7 orphan UUID-named files deleted from 3 job prefixes

---

## 11. What to Work on Next

1. **Production smoke test** — Verify the 6 relocated prompt detail pages load images correctly at their new `media/images/2026/03/large/` URLs
2. **Watch for new bulk-gen publishes** — The SEO rename pipeline now auto-relocates future publishes; confirm in Heroku logs after the next publish
3. **Address N4h rename trigger bug** — Upload-flow prompts may still not be getting SEO renamed (reported in CLAUDE.md as a known blocker). SMOKE2 series fixed bulk-gen; upload-flow path needs investigation
4. **Consider batching mirror saves** — Minor: change mirror field updates to a single `prompt.save(update_fields=[...])` call
5. **Add sibling-check unit test** — Mock S3 responses to test the per-prompt cleanup branch (`KeyCount > 0` → skip vs. `KeyCount == 0` → log empty)
