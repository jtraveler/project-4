# HARDENING-1: Sibling-Check Unit Tests + Batch Mirror Field Saves — Completion Report

**Spec:** CC_SPEC_BULK_GEN_HARDENING_1.md
**Session:** March 11, 2026
**Commit:** `3149a9a`

---

## 1. Overview

HARDENING-1 addressed two follow-up items from the SMOKE2-FIX-E post-implementation review.

**Part A — Sibling-check test coverage.** SMOKE2-FIX-E introduced novel per-prompt sibling-check logic in `rename_prompt_files_for_seo`: after moving a bulk-gen image to the standard `media/images/` path, the task calls `list_objects_v2(MaxKeys=1)` on the `bulk-gen/{job_id}/` prefix to check whether sibling files from the same job remain. If they do, cleanup is deferred. If the prefix is empty, the task logs this and still defers deletion to the backfill command (which only runs cleanup after confirming `remaining == 0`). This logic has a genuine blast-radius risk — if it ever incorrectly triggered deletion, it could destroy sibling prompts' B2 files before those prompts had been relocated. Despite this risk, the logic had no test coverage. HARDENING-1 adds that coverage.

**Part B — Mirror field save batching.** The mirror field update loop in `rename_prompt_files_for_seo` was issuing one `prompt.save(update_fields=[field])` per mirror field. For a bulk-gen prompt where all four image URL fields (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`) share one physical B2 file, this meant three separate DB writes for the mirror fields alone. HARDENING-1 batches these into a single `save(update_fields=[...])` call, reducing mirror-field DB round-trips from N to 1.

---

## 2. Expectations vs. Outcomes

| Expectation | Outcome |
|-------------|---------|
| Unit test: sibling files present → `delete_object` not called for cleanup | ✅ `test_sibling_files_present_skips_cleanup` |
| Unit test: prefix empty → `delete_object` not called, log emitted | ✅ `test_empty_prefix_logs_not_deletes` |
| Unit test: non-bulk-gen prompt → `list_objects_v2` not called | ✅ `test_non_bulk_gen_prompt_no_sibling_check` |
| Mirror field saves batched into single `save(update_fields=[...])` | ✅ `mirror_fields_to_save` list collected, single save issued |
| No behaviour change in rename path | ✅ All field values and save semantics identical; only DB round-trip count changes |
| `makemigrations --check` → No changes detected | ✅ Confirmed |
| Full test suite passes | ✅ 1117 tests, 12 skipped, OK (5 new tests; was 1112) |

---

## 3. Improvements Made

### `prompts/tasks.py`

**Mirror field save batching (lines ~1836–1845)**

The old pattern issued one `prompt.save()` per mirror field:

```python
for mirror_field in sharing_fields[1:]:
    setattr(prompt, mirror_field, new_url)
    prompt.save(update_fields=[mirror_field])
    updated_fields.append(mirror_field)
    results[mirror_field] = {'success': True, 'new_url': new_url, 'mirrored': True}
```

The new pattern collects all mirror fields and issues a single batched save:

```python
mirror_fields_to_save = []
for mirror_field in sharing_fields[1:]:
    setattr(prompt, mirror_field, new_url)
    mirror_fields_to_save.append(mirror_field)
    updated_fields.append(mirror_field)
    results[mirror_field] = {'success': True, 'new_url': new_url, 'mirrored': True}
if mirror_fields_to_save:
    prompt.save(update_fields=mirror_fields_to_save)
```

For a bulk-gen prompt with 4 sharing URL fields, this reduces mirror-field DB writes from 3 to 1. The `update_fields` constraint means Django issues a single `UPDATE` naming only those columns; the `auto_now` field `updated_on` fires exactly once per group instead of three times. The primary field's save (inside `_rename_or_move_field`) is unchanged — it continues to save immediately after the B2 move so the DB URL is always valid even if the task crashes mid-run.

### `prompts/tests/test_bulk_gen_rename.py` (new file, 283 lines)

New test file with two test classes covering the sibling-check and batch-save changes.

**`SiblingCheckTests`** — 4 tests:

| Test | What it verifies |
|------|-----------------|
| `test_sibling_files_present_skips_cleanup` | `list_objects_v2` returns `KeyCount=1` → `delete_object` called exactly once (the move only); no cleanup delete follows |
| `test_empty_prefix_logs_not_deletes` | `list_objects_v2` returns `KeyCount=0` → `delete_object` still called exactly once; INFO log emitted containing the `bulk-gen/{job_id}/` prefix |
| `test_non_bulk_gen_prompt_no_sibling_check` | Standard `media/images/` URL → `list_objects_v2` never called; rename succeeds; `delete_object` called once for the in-place rename |
| `test_sibling_check_exception_is_nonfatal` | `list_objects_v2` raises `ClientError` → task returns `status='success'` (non-blocking confirmed); WARNING log emitted containing the prefix |

**`MirrorFieldBatchSaveTests`** — 1 test:

| Test | What it verifies |
|------|-----------------|
| `test_mirror_fields_batched_into_single_save` | All 3 mirror fields (`b2_thumb_url`, `b2_medium_url`, `b2_large_url`) are saved in exactly one `prompt.save(update_fields=[...])` call rather than three separate calls |

**Mocking approach.** All tests patch `prompts.services.b2_rename.get_b2_client` to inject a `MagicMock` boto3 client whose `copy_object`, `head_object`, `delete_object`, and `list_objects_v2` methods return controlled values. No real B2 API calls are made in any test.

The batch save test additionally patches `prompts.models.Prompt.save` as a context manager (entered after fixture creation) to intercept and count save calls without preventing the ORM `create()` from working.

**Settings override.** All tests use `@override_settings(B2_CUSTOM_DOMAIN='cdn.example.com', B2_BUCKET_NAME='test-bucket', B2_ENDPOINT_URL='https://s3.example.com')` so `B2RenameService._url_to_key` correctly resolves CDN URLs to S3 keys in the test environment.

---

## 4. Issues Encountered and Resolved

### Issue 1: `prompts.tasks.Prompt` does not exist at module level

**Root cause.** `rename_prompt_files_for_seo` imports `Prompt` inside the function body (`from prompts.models import Prompt` at line 1732) to avoid a circular import between `prompts.tasks` and `prompts.models`. When the batch-save test used `@patch('prompts.tasks.Prompt.save')`, Python raised `AttributeError: module 'prompts.tasks' has no attribute 'Prompt'` because the name is never bound at module scope.

**Fix.** Changed the patch target to `prompts.models.Prompt.save`. `unittest.mock.patch` on a class method mutates the method directly on the class object in-place. Because `from prompts.models import Prompt` inside the task binds the same class object, any `prompt.save()` call from any `Prompt` instance created by the task is intercepted — regardless of where `Prompt` was imported. The patch is applied as a `with` context manager entered *after* the fixture prompt is created, so the `Prompt.objects.create()` call in setUp is not intercepted and does not appear in `mock_save.call_args_list`.

### Issue 2: @test-automator initial score 7.5/10 (below 8.0 threshold)

**Root cause.** The initial test file was missing a test for the exception-swallowing path in the sibling check (tasks.py lines 1868–1873):

```python
except Exception as e:
    # Non-blocking — cleanup check failure must not affect task outcome
    logger.warning(
        "[SEO Rename] Bulk-gen prefix check failed for '%s': %s",
        bulk_gen_prefix, e,
    )
```

Without a test, any future refactor narrowing `except Exception` to `except ClientError` (or removing the catch entirely) would silently break the non-blocking contract with no test catching the regression.

Additionally, `test_non_bulk_gen_prompt_no_sibling_check` contained only negative assertions (`assert_not_called()`), violating CC_SPEC_TEMPLATE v2.5 Critical Reminder #9 (every `assertNotIn`/`assert_not_called` must be paired with a positive counterpart).

**Fix.** Added `test_sibling_check_exception_is_nonfatal`: injects a `ClientError` on `list_objects_v2.side_effect`, then asserts `result['status'] == 'success'` (task completed despite the exception) and `result['renamed_count'] > 0` (the rename itself succeeded before the exception). Also asserts a WARNING-level log containing the expected prefix is emitted. Added two positive assertions to `test_non_bulk_gen_prompt_no_sibling_check`: `assertGreater(renamed_count, 0)` and `assertEqual(delete_object.call_count, 1)`.

**Re-run score: 8.5/10.**

---

## 5. Remaining Issues

No blocking issues. The following are minor notes for future sessions:

- **`delete_object.call_count == 1` relies on URL-deduplication invariant.** In `test_sibling_files_present_skips_cleanup` and `test_empty_prefix_logs_not_deletes`, the count of 1 is correct because all four URL fields share the same `BULK_GEN_URL`, causing `url_to_fields` to produce one group and one B2 move operation. This is the correct shape for a real bulk-gen prompt. A future developer adding a test with distinct URLs per field would need a higher expected count. A clarifying comment was left in the test docstrings.

- **No test for `b2_image_url=None` early-exit.** Line 1752 guards `is_bulk_gen = bool(prompt.b2_image_url and 'bulk-gen/' in ...)`. A `None` URL makes `is_bulk_gen=False` and the sibling check is skipped entirely. This path is covered indirectly by the early-return at line 1742 (no title) and the no-op path in `_rename_or_move_field`, but there is no explicit test for a prompt with `b2_image_url=None`.

- **`assertLogs` log-message check is loosely scoped.** The prefix check uses `any(EXPECTED_PREFIX in msg for msg in log_ctx.output)`, which matches the prefix as a substring of any captured record. A more precise check would verify log level and full message format. Sufficient for the current purpose.

---

## 6. Concerns and Areas for Improvement

- **`cleanup_empty_prefix` still has no internal prefix allowlist.** The method accepts any string prefix and deletes all objects under it. The only protection is at the call site (backfill command only calls it when `remaining == 0`). If a future caller bypasses that gate, the blast radius is unrestricted. **Recommendation:** Add `if not prefix.startswith('bulk-gen/'): raise ValueError(f"Refusing to clean unsafe prefix: {prefix!r}")` at the top of the method as defense-in-depth. This is a one-line change in `prompts/services/b2_rename.py`.

- **Per-prompt task never cleans up empty prefixes.** Even when `KeyCount == 0`, the per-prompt task defers to the backfill command. This is architecturally correct (the backfill verifies `remaining == 0` before cleaning), but it means `rename_prompt_files_for_seo` invoked outside the backfill context (e.g. when a single new bulk-gen prompt is published and SEO-renamed) will leave an empty `bulk-gen/{job_id}/` virtual prefix in B2 indefinitely. B2 has no real directory concept so this costs nothing, but operators inspecting the bucket may see unexpected stale prefixes.

- **Agent feedback as quality gate (process note).** The spec required 3 tests; 5 were delivered. The two additional tests (`test_sibling_check_exception_is_nonfatal` and `test_mirror_fields_batched_into_single_save`) arose from agent review — specifically @test-automator flagging the uncovered exception path as the primary reason for a below-threshold score. This demonstrates the intended use of agents: not as a rubber stamp after work is complete, but as a quality gate that expands scope when coverage gaps are found.

---

## 7. Agent Ratings

| Round | Agent | Score | Key Findings | Acted On |
|-------|-------|-------|--------------|----------|
| 1 | @django-pro | 9.5/10 | `update_fields=mirror_fields_to_save` is correct and `auto_now`-safe (`updated_on` fires once as expected). Mock scopes are clean with no leakage between tests. `prompts.models.Prompt.save` patch correctly intercepts the task's deferred import. Minor: redundant `call_kwargs[1]` fallback in prefix assertion (cosmetic, not a defect). | N/A — no blocking issues |
| 1 | @test-automator | 7.5/10 | **Critical:** No test for exception-swallowing path (tasks.py lines 1868–1873). **Moderate:** No positive assertions in `test_non_bulk_gen_prompt_no_sibling_check`. Minor: `assertLogs` check is loosely scoped; repeated local imports lack explanatory comment. | ✅ Added `test_sibling_check_exception_is_nonfatal`; added positive assertions to `test_non_bulk_gen_prompt_no_sibling_check` |
| 2 | @test-automator | 8.5/10 | Exception test is well-formed and correctly exercises both the non-blocking contract and log emission. New positive assertions are accurate. Remaining notes are documentation-level only. | N/A — threshold met |

**Average post-fix score: 9.0/10** (above the 8.0 threshold)

---

## 8. Recommended Additional Agents

- **@code-reviewer** — Would have independently validated the `update_fields` batching pattern, caught the `cleanup_empty_prefix` internal guard gap, and likely flagged the missing exception test before @test-automator did. Recommended for future tasks that touch `b2_rename.py`.

- **@performance-engineer** — Could measure the concrete DB round-trip reduction for a real 20-image bulk-gen publish run and confirm the batched save does not introduce lock contention under concurrent publish operations (Phase 6B uses `select_for_update()` + `transaction.atomic()` in a ThreadPoolExecutor context).

---

## 9. How to Test

### Run the new test file in isolation
```bash
python manage.py test prompts.tests.test_bulk_gen_rename
```
Expected: 5 tests, 0 failures, 0 errors.

### Run the full test suite
```bash
python manage.py test
```
Expected: 1117 tests, 12 skipped, OK.

### Verify mirror field batching (static check)
```bash
grep -n "prompt\.save" prompts/tasks.py
```
The mirror block at ~line 1845 must show one `prompt.save(update_fields=mirror_fields_to_save)` outside the loop — not multiple `prompt.save()` calls inside `for mirror_field in sharing_fields[1:]`.

### Manual verification (production)
The batch save has no visible UI effect. Confirm via Django shell after any bulk-gen publish:
```python
from prompts.models import Prompt
p = Prompt.objects.filter(ai_generator='gpt-image-1').latest('created_on')
print(p.b2_image_url, p.b2_thumb_url, p.b2_medium_url, p.b2_large_url)
# All four should be identical (same media/images/{year}/{month}/large/ path)
```

---

## 10. Commits

| Hash | Description |
|------|-------------|
| `3149a9a` | `test(bulk-gen): add sibling-check unit tests for rename cleanup path` |

---

## 11. What to Work on Next

1. **JS-SPLIT-1** — Split `bulk-generator-job.js` (~1800 lines) into logical modules before it grows further with Phase 6D additions. Spec: `CC_SPEC_BULK_GEN_JS_SPLIT_1.md`. Must be done before Phase 6D is specced.
2. **`cleanup_empty_prefix` internal guard** — Add `prefix.startswith('bulk-gen/')` validation inside `prompts/services/b2_rename.py` as a one-line defense-in-depth change.
3. **N4h rename trigger investigation** — Upload-flow prompts still not getting SEO-renamed (known CLAUDE.md blocker). SMOKE2 series fixed bulk-gen; upload-flow path needs separate investigation.
4. **Production smoke test for SMOKE2-FIX-E** — Verify the 6 relocated bulk-gen prompt pages still serve images correctly from their new `media/images/2026/03/large/` CDN paths.
