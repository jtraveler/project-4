# CC_SPEC_N4H_UPLOAD_RENAME_FIX — Upload-Flow SEO Rename Task Not Triggering

**Spec ID:** N4H-UPLOAD-RENAME-FIX
**Created:** March 12, 2026
**Type:** Bug Fix — Background task not queued in upload submit path
**Template Version:** v2.5
**Modifies UI/Templates:** No
**Requires Migration:** No
**Depends On:** Nothing — standalone fix

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`**
2. **Read this entire specification**
3. **Read `prompts/views/upload_views.py` IN FULL** — map the entire submit path before writing a single line
4. **Read `prompts/tasks.py`** — find `rename_prompt_files_for_seo`, understand its signature and the `async_task` call pattern
5. **Read `prompts/services/b2_rename.py`** — understand the rename service to know what preconditions the task requires
6. **Find SMOKE2-FIX-D's exact change** — run `git log --oneline --all | grep -i smoke2\|fix-d\|fix_d\|rename` and then `git show <hash>` to see exactly where and how `async_task('prompts.tasks.rename_prompt_files_for_seo', ...)` was added in the bulk-gen path. The upload-flow fix must follow the same pattern.
7. **Use both required agents** — @django-pro and @test-automator are MANDATORY

**Work is REJECTED if the git archaeology step is skipped, agents are skipped, or the fix is added without a test.**

---

## 📋 OVERVIEW

### The Problem

`rename_prompt_files_for_seo` is a Django-Q2 background task that renames uploaded B2 files from their UUID-based paths to SEO-friendly slugs like `stylish-woman-beach-sunset-midjourney-prompt.jpg`.

SMOKE2-FIX-D (Session 121) fixed the bulk-gen path: after a `GeneratedImage` completes processing and a `Prompt` is created via `create_pages`, the rename task is now correctly queued.

The **upload-flow path** — where a user manually uploads an image through the upload page and submits the form — has a completely separate code path in `prompts/views/upload_views.py`. This path creates a `Prompt` and saves it, but **never queues `rename_prompt_files_for_seo`**. As a result, all upload-flow prompts keep UUID-based B2 filenames indefinitely.

### What This Spec Does

1. **Diagnose** — precisely identify the submit path in `upload_views.py` and confirm the missing queue call
2. **Fix** — add `async_task('prompts.tasks.rename_prompt_files_for_seo', prompt.id)` in the correct location after prompt save
3. **Guard** — add a precondition check to only queue if the prompt has a B2 URL (not a local preview URL)
4. **Test** — add one targeted test confirming the task is queued on upload submit

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Git archaeology completed — SMOKE2-FIX-D's exact `async_task` call pattern identified
- ✅ Upload submit path in `upload_views.py` fully mapped
- ✅ `async_task('prompts.tasks.rename_prompt_files_for_seo', prompt.id)` queued after successful prompt creation in the upload path
- ✅ Queue call is conditional — only fires if `prompt.b2_image_url` is set and non-empty
- ✅ One new test confirming task is queued on submit
- ✅ Full suite passes
- ✅ Both agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

---

### Touch Point 1 — Git Archaeology (MANDATORY FIRST STEP)

Run the following to find SMOKE2-FIX-D:

```bash
git log --oneline | head -30
# Find the SMOKE2-FIX-D commit hash

git show <hash> -- prompts/tasks.py prompts/views/ prompts/services/
# Read exactly what was added and where
```

Document your findings before proceeding:
- What file was edited?
- What function was edited?
- What exact line was added?
- What preconditions were checked before the `async_task` call?

This is not optional. The upload-flow fix must follow exactly the same pattern.

---

### Touch Point 2 — Map the Upload Submit Path

Read `prompts/views/upload_views.py` completely. Find the view function that handles the upload form submission (likely a POST handler). Map:

1. Where is `prompt.save()` called (or `Prompt.objects.create()`)?
2. Is there already any `async_task` call anywhere in the upload submit path?
3. What is `prompt.b2_image_url` set to at the point of save — is it a B2 URL or could it be a local preview URL during development?
4. Is there a `processing_complete` flag or equivalent on the upload-flow prompt at save time?

Write a brief summary of your findings as a comment before the fix — future developers must be able to understand why the queue call is where it is.

---

### Touch Point 3 — Add the Queue Call

After `prompt.save()` in the upload submit view, add the `async_task` call following the exact pattern from SMOKE2-FIX-D. Use a `b2_image_url` precondition guard:

```python
# Queue SEO rename task if B2 URL is set (upload-flow fix — N4H-UPLOAD-RENAME-FIX)
# Follows same pattern as SMOKE2-FIX-D for bulk-gen path.
if prompt.b2_image_url:
    async_task('prompts.tasks.rename_prompt_files_for_seo', prompt.id)
```

Read the file to confirm:
- The correct import for `async_task` is already present (it should be — upload_views.py likely imports from django_q already, or tasks.py). If not, add it.
- The guard condition matches what SMOKE2-FIX-D uses — if the bulk-gen path uses a different field or condition, use the same one.

---

### Touch Point 4 — Add One Test

**File:** `prompts/tests/test_upload_views.py` (or the closest existing upload test file — read the test directory to find it)

Add one test to the existing upload test class. The test must confirm that submitting the upload form with a B2 URL set on the resulting prompt causes `async_task` to be called with `rename_prompt_files_for_seo` and the prompt's ID.

Pattern (mock `async_task`, POST to the submit view, assert called):

```python
@patch('prompts.views.upload_views.async_task')
def test_rename_task_queued_on_upload_submit(self, mock_async_task):
    """rename_prompt_files_for_seo is queued after successful upload submit."""
    # [set up test prompt data with a b2_image_url]
    # [POST to upload submit view]
    # Assert:
    mock_async_task.assert_called_once_with(
        'prompts.tasks.rename_prompt_files_for_seo',
        <prompt_id>
    )
```

Read the existing upload tests to replicate the exact setup pattern — don't invent a new one.

Also add a complementary test confirming the task is NOT queued when `b2_image_url` is empty/None:

```python
@patch('prompts.views.upload_views.async_task')
def test_rename_task_not_queued_without_b2_url(self, mock_async_task):
    """rename_prompt_files_for_seo is not queued if no B2 URL is set."""
    # [set up test prompt data WITHOUT b2_image_url]
    # [POST to upload submit view]
    mock_async_task.assert_not_called()
```

---

## ✅ DO / DO NOT

### DO
- ✅ Run git archaeology FIRST — read SMOKE2-FIX-D before writing any code
- ✅ Read `upload_views.py` completely before adding anything
- ✅ Follow the exact `async_task` call pattern from SMOKE2-FIX-D
- ✅ Add both the positive test (task queued) and the negative test (task not queued without B2 URL)
- ✅ Run the full test suite after committing

### DO NOT
- ❌ Do not add the queue call before `prompt.save()` — the prompt ID must exist first
- ❌ Do not queue if `b2_image_url` is not set — local preview URLs must never be renamed
- ❌ Do not modify `tasks.py` or `b2_rename.py` — the task itself is working correctly
- ❌ Do not add more than 2 tests — this is a targeted fix, not a test refactor

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Git archaeology complete — SMOKE2-FIX-D's exact pattern documented
- [ ] Upload submit path fully mapped — `prompt.save()` location confirmed
- [ ] `async_task` call added after `prompt.save()` with `b2_image_url` guard
- [ ] Import for `async_task` confirmed present in `upload_views.py`
- [ ] Both tests added (queued + not queued)
- [ ] Full suite passes

---

## 🤖 AGENT REQUIREMENTS

**@django-pro — MANDATORY**
- Focus: Is the `async_task` call placed correctly relative to `prompt.save()`? Is the `b2_image_url` guard the right precondition — are there any edge cases where `b2_image_url` is set but the file isn't actually on B2 yet (e.g. during async upload)? Does the pattern exactly match SMOKE2-FIX-D?
- Rating: 8+/10

**@test-automator — MANDATORY**
- Focus: Do the two new tests actually cover the fix? Is the `@patch` target correct — is `async_task` imported at module level in `upload_views.py` or called via a module reference? Does the negative test (no B2 URL) definitively prove the guard works?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- Git archaeology step skipped
- `async_task` call pattern differs from SMOKE2-FIX-D without documented reason
- Queue call not guarded by `b2_image_url` check
- Either of the two tests missing
- Any agent below 8.0/10
- Full suite not run

---

## 🧪 TESTING

### Automated

```bash
python manage.py test prompts.tests.test_upload_views -v 2
# Expected: all existing tests pass + 2 new tests pass

python manage.py test
# Full suite — expected: 1147 + 2 = 1149 tests, 0 failures
```

### Manual Production Verification (after deploy)

1. Upload a new prompt through the upload page
2. In Django shell (or admin), check `Prompt.objects.latest('created_at').b2_image_url`
3. Confirm the filename is SEO-friendly (e.g. `portrait-woman-red-dress-midjourney-prompt.jpg`) not a UUID

If UUID is still present, check Django-Q worker logs for the rename task — it may have been queued but failed. That is a separate issue from this spec.

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
N4H-UPLOAD-RENAME-FIX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

Git archaeology completed — SMOKE2-FIX-D hash:      ✅/❌
Upload submit path mapped — prompt.save() location: ✅/❌
async_task call added after prompt.save():           ✅/❌
b2_image_url guard in place:                         ✅/❌
async_task import confirmed in upload_views.py:      ✅/❌
Test: task queued with B2 URL:                       ✅/❌
Test: task not queued without B2 URL:                ✅/❌

Agent: @django-pro     Score: X/10  Findings:  Action:
Agent: @test-automator Score: X/10  Findings:  Action:

Full suite: X tests, 0 failures ✅

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
fix(upload): N4H — queue rename_prompt_files_for_seo on upload submit

- upload_views.py: async_task queued after prompt.save() when b2_image_url is set
- Follows SMOKE2-FIX-D pattern (bulk-gen path fix, Session 121)
- Guard: task only queued if b2_image_url is non-empty
- Tests: 2 new — task queued with B2 URL, task not queued without B2 URL
- Closes N4h blocker: upload-flow prompts now get SEO-friendly B2 filenames

Agents: @django-pro X/10, @test-automator X/10
Full suite: X tests, 0 failures
```
