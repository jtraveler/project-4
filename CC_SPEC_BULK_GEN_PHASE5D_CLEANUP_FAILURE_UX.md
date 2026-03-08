# CC Spec — Phase 5D Cleanup + Failure UX Improvements

**Spec Version:** 1.0
**Date:** March 8, 2026
**Modifies UI/Templates:** YES — `bulk_generator_job.html`, `bulk-generator-job.js`
**Backend changes:** YES — `bulk_generation.py`, `test_bulk_generation_tasks.py`, `tasks.py`
**Follows:** Phase 5D P2 (commit a737ad6) — 990 tests passing

---

## ⛔ CRITICAL: READ FIRST

```
╔══════════════════════════════════════════════════════════════╗
║  STOP — READ BEFORE WRITING A SINGLE LINE OF CODE           ║
║                                                              ║
║  1. Read CC_COMMUNICATION_PROTOCOL.md                        ║
║  2. Read this ENTIRE spec top to bottom                      ║
║  3. Agents are MANDATORY — work is REJECTED without them     ║
║  4. All agents must score 8+/10 or work is REJECTED          ║
║  5. UI changes require MANUAL BROWSER VERIFICATION           ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📋 OVERVIEW

This spec covers two concerns bundled together because they are small
enough to run in one session:

**Part A — Phase 5D Cleanup (15 min):** Two tiny fixes left open after
Session 110 that CC identified but did not close.

**Part B — Failure UX (primary work):** The bulk generator backend
stores rich failure information (error type, error message, which prompt
failed) but none of it reaches the user's screen. Staff and future paid
customers see only "Failed" with no context. This spec closes that gap.

### Why Failure UX Matters Now

This tool will be used by non-technical staff and eventually paid
customers. "Failed" with no context causes:
- Repeated resubmission of prompts that will always fail (content policy)
- Confusion between a broken API key vs. a content issue vs. a B2 error
- Support tickets to Mateo for problems the user could have self-served

The backend already classifies all failures correctly. This is purely
a frontend + API response gap.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Part A: Fragile test updated, import comment added
- ✅ Part B-1: `error_message` returned per image in status API
- ✅ Part B-2: Failed gallery slots show reason text + which prompt failed
- ✅ Part B-3: Auth failure shows "Invalid API key" message, not generic "Generation failed."
- ✅ Part B-4: Content policy failures identify the specific prompt text that was flagged
- ✅ Full suite: `python manage.py test` → 990+ tests passing
- ✅ Manual browser check: failed slot display verified in browser
- ✅ All agents 8+/10

---

## 🔧 IMPLEMENTATION

### ⚠️ IMPLEMENT IN THIS ORDER

Part A first (lowest risk), then Part B backend, then Part B frontend.
Run targeted tests after Part A before touching Part B.

---

## PART A — PHASE 5D CLEANUP

### A-1: Fix Fragile Test (5 min)

**File:** `prompts/tests/test_bulk_generation_tasks.py`

Find `test_max_concurrent_constant_is_four` and replace it entirely:

**Before:**
```python
def test_max_concurrent_constant_is_four(self):
    """MAX_CONCURRENT_IMAGE_REQUESTS constant is 4."""
    from prompts.tasks import MAX_CONCURRENT_IMAGE_REQUESTS
    self.assertEqual(MAX_CONCURRENT_IMAGE_REQUESTS, 4)
```

**After:**
```python
def test_max_concurrent_reads_from_settings(self):
    """MAX_CONCURRENT_IMAGE_REQUESTS reads from BULK_GEN_MAX_CONCURRENT setting."""
    from django.conf import settings as django_settings
    from prompts.tasks import MAX_CONCURRENT_IMAGE_REQUESTS
    expected = getattr(django_settings, 'BULK_GEN_MAX_CONCURRENT', 4)
    self.assertEqual(MAX_CONCURRENT_IMAGE_REQUESTS, expected)
```

**Verification:**
```bash
grep -n "test_max_concurrent" prompts/tests/test_bulk_generation_tasks.py
```
Must show only the new name. Old name must not exist.

### A-2: Add Import-Time Comment (2 min)

**File:** `prompts/tasks.py`

Find the `MAX_CONCURRENT_IMAGE_REQUESTS` definition and add the comment:

**Before:**
```python
# Tune via BULK_GEN_MAX_CONCURRENT env var (Heroku config) without a code deploy.
MAX_CONCURRENT_IMAGE_REQUESTS = getattr(settings, 'BULK_GEN_MAX_CONCURRENT', 4)
```

**After:**
```python
# Tune via BULK_GEN_MAX_CONCURRENT env var (Heroku config) without a code deploy.
# Evaluated at import time — @override_settings(BULK_GEN_MAX_CONCURRENT=N) in tests
# will NOT change this value. To override in tests, mock
# prompts.tasks.MAX_CONCURRENT_IMAGE_REQUESTS directly.
MAX_CONCURRENT_IMAGE_REQUESTS = getattr(settings, 'BULK_GEN_MAX_CONCURRENT', 4)
```

**Test gate after Part A:**
```bash
python manage.py test prompts.tests.test_bulk_generation_tasks -v1
```
Must pass with same count as before (50 tests). Then proceed to Part B.

---

## PART B — FAILURE UX IMPROVEMENTS

### Background: What Currently Happens

The `GeneratedImage` model has an `error_message` field that stores
the failure reason (e.g. "Content policy violation", "Auth error",
"Generated but upload failed: ..."). However:

1. `get_job_status()` in `bulk_generation.py` does NOT include
   `error_message` in the per-image API response
2. The JS renders failed slots as a grey box with just the word "Failed"
3. The job-level failed state shows "Generation failed." with no reason
4. Content policy failures do not identify which prompt was flagged

This spec fixes all four gaps.

---

### B-1: Add `error_message` to Status API

**File:** `prompts/services/bulk_generation.py`

**READ the current `get_job_status()` method before making changes.**

Find the `images_data` list comprehension inside `get_job_status()`.
It currently builds per-image dicts with these keys:
`id`, `prompt_text`, `prompt_order`, `variation_number`, `status`,
`image_url`.

Add `error_message` to each dict:

**Before:**
```python
images_data = [
    {
        'id': str(img.id),
        'prompt_text': img.prompt_text,
        'prompt_order': img.prompt_order,
        'variation_number': img.variation_number,
        'status': img.status,
        'image_url': img.image_url or '',
    }
    for img in job.images.all().order_by('prompt_order', 'variation_number')
]
```

**After:**
```python
images_data = [
    {
        'id': str(img.id),
        'prompt_text': img.prompt_text,
        'prompt_order': img.prompt_order,
        'variation_number': img.variation_number,
        'status': img.status,
        'image_url': img.image_url or '',
        'error_message': img.error_message or '',
    }
    for img in job.images.all().order_by('prompt_order', 'variation_number')
]
```

**DO NOT** change anything else in `get_job_status()`. One field added.

---

### B-2: Add `error_reason` to Job-Level Status Response

**File:** `prompts/services/bulk_generation.py`

**Same `get_job_status()` method.** Find the `return` dict at the bottom.

Add `error_reason` to the returned dict. This surfaces auth failures
at the job level. Read the existing return keys before editing to
avoid disturbing the existing structure.

Add this key to the return dict:
```python
'error_reason': job.error_reason if hasattr(job, 'error_reason') else '',
```

**IMPORTANT — check the model first:** Before adding this, check
`prompts/models.py` to see if `BulkGenerationJob` has an `error_reason`
field. If it does not, use this approach instead — derive it from
the job's failed images:

```python
# Derive job-level error reason from failed image error messages
job_error_reason = ''
if job.status == 'failed':
    auth_failed = job.images.filter(
        error_message__icontains='auth'
    ).first()
    if auth_failed:
        job_error_reason = 'auth_failure'

'error_reason': job_error_reason,
```

**READ `prompts/models.py` for `BulkGenerationJob` before implementing
this.** Use whichever approach matches the actual model.

---

### B-3: Frontend — Failed Gallery Slot with Reason

**File:** `static/js/bulk-generator-job.js`

**READ the current `fillFailedSlot()` function before making changes.**

The current implementation renders a grey box with only "Failed":
```javascript
failedText.textContent = 'Failed';
```

**Changes needed:**

1. **Pass `errorMessage` and `promptText` into `fillFailedSlot()`.**
   The function currently takes `(groupIndex, slotIndex)`. Update
   its signature to accept these:
   ```javascript
   function fillFailedSlot(groupIndex, slotIndex, errorMessage, promptText) {
   ```

2. **Find where `fillFailedSlot` is called.** Read the image rendering
   logic (around line 385-390 in the current file) where it checks
   `image.status === 'failed'`. Update that call to pass the new args:
   ```javascript
   } else if (image.status === 'failed') {
       fillFailedSlot(groupIndex, slotIndex,
           image.error_message || '',
           image.prompt_text || '');
   }
   ```

3. **Update `fillFailedSlot` body** to display the error reason and
   identify the failed prompt:

```javascript
function fillFailedSlot(groupIndex, slotIndex, errorMessage, promptText) {
    // ... existing DOM setup (read current code, preserve it) ...

    // Replace the simple failedText with structured content
    var failedText = document.createElement('span');
    failedText.className = 'failed-text';
    failedText.textContent = 'Failed';

    failed.appendChild(failedText);

    // Error reason line
    if (errorMessage) {
        var reasonText = document.createElement('span');
        reasonText.className = 'failed-reason';
        reasonText.textContent = _getReadableErrorReason(errorMessage);
        failed.appendChild(reasonText);
    }

    // Prompt identifier (truncated)
    if (promptText) {
        var promptLabel = document.createElement('span');
        promptLabel.className = 'failed-prompt';
        promptLabel.textContent = promptText.length > 60
            ? promptText.substring(0, 57) + '\u2026'
            : promptText;
        promptLabel.title = promptText; // Full text on hover
        failed.appendChild(promptLabel);
    }

    // ... rest of existing logic unchanged ...
}
```

4. **Add `_getReadableErrorReason()` helper function** to translate
   raw error messages into plain language for non-technical users.
   Add this near the top of the JS file with the other helper functions:

```javascript
function _getReadableErrorReason(errorMessage) {
    if (!errorMessage) return '';
    var msg = errorMessage.toLowerCase();
    if (msg.indexOf('auth') !== -1 || msg.indexOf('invalid') !== -1 ||
        msg.indexOf('api key') !== -1) {
        return 'Invalid API key — check your key and try again.';
    }
    if (msg.indexOf('content_policy') !== -1 ||
        msg.indexOf('content policy') !== -1 ||
        msg.indexOf('safety') !== -1) {
        return 'Content policy violation — revise this prompt.';
    }
    if (msg.indexOf('upload failed') !== -1 ||
        msg.indexOf('b2') !== -1) {
        return 'Image saved but upload failed — try regenerating.';
    }
    if (msg.indexOf('retries') !== -1 ||
        msg.indexOf('rate') !== -1) {
        return 'Rate limit reached — try again in a few minutes.';
    }
    return 'Generation failed — check your settings and try again.';
}
```

---

### B-4: Frontend — Job-Level Auth Failure Message

**File:** `static/js/bulk-generator-job.js`

**READ the current `handleTerminalState()` function before editing.**

Find the `status === 'failed'` branch. Currently:
```javascript
} else if (status === 'failed') {
    // ...
    var errorMsg = (data && data.error) ? data.error : '';
    if (statusText) {
        statusText.textContent = 'Generation failed.' + (errorMsg ? ' ' + errorMsg : '');
    }
}
```

Update to also check `data.error_reason` for the auth case:
```javascript
} else if (status === 'failed') {
    updateProgressBar(completed, totalImages);
    if (progressBar) {
        progressBar.classList.add('progress-failed');
    }
    var failedMessage = 'Generation failed.';
    if (data && data.error_reason === 'auth_failure') {
        failedMessage = 'Generation stopped \u2014 invalid API key. '
            + 'Please re-enter your OpenAI API key and try again.';
    } else if (data && data.error) {
        failedMessage = 'Generation failed. ' + data.error;
    }
    if (statusText) {
        statusText.textContent = failedMessage;
    }
}
```

---

### B-5: CSS for New Failed Slot Elements

**File:** `static/css/pages/bulk-generator-job.css`

**READ the existing `.placeholder-failed` and `.failed-text` styles
before adding new rules.** Add these beneath the existing failed
slot styles (do not replace them):

```css
/* Failed slot — reason and prompt label */
.failed-reason {
    display: block;
    font-size: 0.72rem;
    color: var(--error-color, #dc2626);
    margin-top: 4px;
    line-height: 1.3;
    text-align: center;
    padding: 0 8px;
}

.failed-prompt {
    display: block;
    font-size: 0.68rem;
    color: var(--gray-500, #737373);
    margin-top: 4px;
    line-height: 1.3;
    text-align: center;
    padding: 0 8px;
    font-style: italic;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
}
```

**Verify contrast:** `.failed-reason` uses `--error-color` (#dc2626).
On a grey/dark failed slot background, confirm this meets minimum
contrast. If the slot background is white or very light grey, use
`#b91c1c` instead for better contrast.

---

## ♿ ACCESSIBILITY — BUILD THESE IN FROM THE START

**For every failed slot rendered:**

1. The `.placeholder-failed` element already has `role="status"` and
   `aria-label="Image generation failed"`. **Update the `aria-label`**
   to include the reason when available:
   ```javascript
   var ariaLabel = 'Image generation failed';
   if (errorMessage) {
       ariaLabel += ': ' + _getReadableErrorReason(errorMessage);
   }
   failed.setAttribute('aria-label', ariaLabel);
   ```

2. The `.failed-prompt` span is truncated text with a `title` attribute.
   Also add `aria-label` with the full prompt text so screen readers
   read the full version:
   ```javascript
   promptLabel.setAttribute('aria-label', 'Failed prompt: ' + promptText);
   ```

3. Contrast: `.failed-reason` must meet 4.5:1 minimum on the slot
   background. Verify in browser before committing.

---

## 🏗️ DOM STRUCTURE — Failed Slot (Updated)

```
.placeholder-failed (role="status", aria-label="Image generation failed: [reason]")
  ├── .failed-text           ← "Failed" (existing)
  ├── .failed-reason         ← "Content policy violation — revise this prompt." (NEW)
  └── .failed-prompt         ← "[truncated prompt text]..." title="[full prompt]" (NEW)
```

**CC must implement this exact nesting.** `.failed-reason` and
`.failed-prompt` are children of `.placeholder-failed`, not siblings
of it.

---

## 📁 FILES TO MODIFY

| File | Change |
|------|--------|
| `prompts/tests/test_bulk_generation_tasks.py` | Part A-1: Rename test |
| `prompts/tasks.py` | Part A-2: Add import comment |
| `prompts/services/bulk_generation.py` | Part B-1: Add `error_message` to API; Part B-2: Add `error_reason` |
| `static/js/bulk-generator-job.js` | Part B-3: Failed slot with reason; Part B-4: Job-level auth message |
| `static/css/pages/bulk-generator-job.css` | Part B-5: New CSS for failed reason/prompt labels |

**Total: 5 files.** If CC finds a reason to touch additional files,
stop and report to Mateo before proceeding.

---

## 🤖 REQUIRED AGENTS

**Minimum 4 agents. Work is REJECTED with fewer.**

| Agent | What to Review |
|-------|---------------|
| `@django-pro` | `get_job_status()` change — does `error_message` query add N+1 risk? Is B-2 `error_reason` derivation correct for the model structure? |
| `@security-auditor` | `error_message` from DB exposed to frontend — does it leak any sensitive info (API key fragments, internal paths, stack traces)? |
| `@ux-ui-designer` | Failed slot readability: is reason text legible at gallery card sizes? Is prompt truncation at 60 chars appropriate? Does the auth failure message in the status bar give the user a clear action to take? |
| `@accessibility-specialist` | Updated `aria-label` on failed slots, `aria-label` on truncated prompt spans, contrast of `.failed-reason` text |

### ⛔ Agent Minimum Rejection Criteria

`@security-auditor` MUST score below 7 if:
- Raw exception strings, stack traces, or internal paths from
  `error_message` could reach the frontend without sanitisation
- API key fragments are visible in any error message exposed to UI

`@ux-ui-designer` MUST score below 7 if:
- The reason text is smaller than 0.7rem at typical gallery card sizes
- The auth failure message does not include a clear action step
  ("re-enter your key", "revise this prompt", etc.)

### ⛔ Agent Reporting Format

```
🤖 AGENT USAGE REPORT

| Agent                    | Score | Key Findings |
|--------------------------|-------|--------------|
| @django-pro              | ?/10  | [findings]   |
| @security-auditor        | ?/10  | [findings]   |
| @ux-ui-designer          | ?/10  | [findings]   |
| @accessibility-specialist| ?/10  | [findings]   |

Average: ?/10
Threshold met: YES / NO
```

**If average is below 8.0 — do NOT commit. Report to Mateo.**

---

## 🔒 SECURITY NOTE ON `error_message` EXPOSURE

**READ THIS BEFORE IMPLEMENTING B-1.**

The `error_message` field in `GeneratedImage` is set from several
sources:
- `result.error_message` from the OpenAI provider (can contain API
  response text)
- `str(exc)[:500]` from unexpected exceptions (can contain internal
  paths or stack fragments)
- `f'Generated but upload failed: {str(e)}'` from B2 errors (can
  contain S3/B2 error details)

**Before adding `error_message` to the API response, sanitise it:**

In `get_job_status()`, strip the raw message through a sanitiser:

```python
def _sanitise_error_message(raw: str) -> str:
    """Return a safe, user-facing error message from a raw error string."""
    if not raw:
        return ''
    msg = raw.lower()
    if 'auth' in msg or 'api key' in msg or 'invalid' in msg:
        return 'Authentication error'
    if 'content_policy' in msg or 'content policy' in msg or 'safety' in msg:
        return 'Content policy violation'
    if 'upload failed' in msg or 'b2' in msg or 's3' in msg:
        return 'Upload failed'
    if 'retries' in msg or 'rate' in msg:
        return 'Rate limit reached'
    # Generic fallback — never expose raw internal messages
    return 'Generation failed'
```

Then in `images_data`:
```python
'error_message': _sanitise_error_message(img.error_message or ''),
```

**This function must live in `bulk_generation.py`, not `tasks.py`.**
It is used at the API response layer, not the task layer.

The `@security-auditor` must explicitly confirm that no raw exception
strings reach the frontend.

---

## 🧪 TESTING

### Part A Gate
```bash
python manage.py test prompts.tests.test_bulk_generation_tasks -v1
# Must: 50 tests, 0 failures
```

### Part B Backend Gate
```bash
python manage.py test prompts.tests.test_bulk_generator_views -v1
# Must pass — get_job_status() is tested here
```

### Full Suite Gate (MANDATORY — backend files modified)
```bash
python manage.py test prompts
# Must: 990+ tests, 0 failures, 12 skipped
```

### ⛔ MANUAL BROWSER CHECK (MANDATORY — UI modified)

After full suite passes, verify in browser at `127.0.0.1:8000`:

1. Navigate to a completed job that has at least one failed image
   (use the test gallery or a real job with a bad prompt)
2. Confirm failed slots show:
   - "Failed" heading
   - Reason text below it (e.g. "Content policy violation — revise this prompt.")
   - Truncated prompt text in italics below that
3. Hover over the prompt text — confirm full prompt visible in tooltip
4. Confirm `.failed-reason` text is legible (not too small, sufficient contrast)
5. If testing auth failure — confirm job-level status bar shows
   "invalid API key" message, not "Generation failed."

**Do NOT commit without completing this browser check.**

---

## 🔁 SELF-IDENTIFIED ISSUES POLICY

⛔ **This policy is MANDATORY and applies to this spec and all future specs.**

If you identify an issue, rough edge, or improvement DURING implementation of this spec:

- **If the fix is ≤15 minutes AND only touches files already in scope for this spec:**
  → You MUST apply it before marking the spec complete. Do not defer it.
  → Add it to the completion report under "Self-Identified Fixes Applied."

- **If the fix requires a new file, a migration, or an architectural decision:**
  → Do NOT apply it. Flag it in the completion report under "Deferred — Out of Scope."
  → Describe it clearly enough for the next spec to pick it up.

**The pattern of diagnosing a problem, providing the exact fix, and then not applying it is not acceptable.** If you can see the fix and it's in scope, close it.

---

## ✅ DO / ⛔ DO NOT

**DO:**
- Read `prompts/models.py` BulkGenerationJob before implementing B-2
- Sanitise `error_message` before it reaches the frontend (security)
- Preserve all existing `fillFailedSlot` logic — add to it, don't replace
- Verify contrast of `.failed-reason` in browser
- Run full suite twice if any test behaviour seems different

**DO NOT:**
- Expose raw exception strings or internal paths to the frontend
- Remove the existing `role="status"` or `aria-label` from failed slots
- Change the `get_job_status()` return structure beyond the two new keys
- Add new model fields or migrations — this spec uses existing data only
- Touch `process_bulk_generation_job` or `_run_generation_loop` in tasks.py

---

## 📊 COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
PHASE 5D CLEANUP + FAILURE UX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY
[4-agent table as specified above]

## 📁 FILES MODIFIED
[List with line counts — must be exactly 5 files]

## 🧪 TESTING PERFORMED
- Part A targeted: [pass count]
- Part B backend targeted: [pass count]
- Full suite run 1: [pass count]
- Browser check: [PASSED / NOT DONE]

## ✅ SUCCESS CRITERIA MET
- [ ] Part A-1: Fragile test renamed and fixed
- [ ] Part A-2: Import-time comment added to tasks.py
- [ ] Part B-1: error_message in status API (sanitised)
- [ ] Part B-2: error_reason in job-level status response
- [ ] Part B-3: Failed slots show reason + prompt text
- [ ] Part B-4: Auth failure job message updated
- [ ] Part B-5: CSS for new elements added
- [ ] Accessibility: aria-label on failed slots updated
- [ ] Security: raw error strings never reach frontend
- [ ] 990+ tests passing
- [ ] All agents 8+/10
- [ ] Browser check completed

## 🔁 SELF-IDENTIFIED FIXES APPLIED
[List any fixes you identified and closed during this session per the policy above.
If none: "None identified." Do NOT leave this section blank without a statement.]

## 🔁 DEFERRED — OUT OF SCOPE
[List any issues you identified but could not fix within this spec's scope.
If none: "None identified."]

## 🔒 SECURITY CONFIRMATION
[Explicit confirmation from @security-auditor that no raw exception
strings or API key fragments can reach the frontend]

## 📝 NOTES
[Any observations, especially about model structure found in B-2]

═══════════════════════════════════════════════════════════════
```

---

## ⛔ FINAL REMINDERS

```
╔══════════════════════════════════════════════════════════════╗
║  BEFORE YOU COMMIT — CONFIRM ALL OF THE FOLLOWING:          ║
║                                                              ║
║  □ 4 agents used, all scored 8+/10                          ║
║  □ _sanitise_error_message() used in get_job_status()       ║
║  □ @security-auditor explicitly confirmed no raw strings     ║
║  □ Browser check done — failed slots visible and legible    ║
║  □ Full suite passing                                        ║
║  □ No new model fields or migrations                        ║
╚══════════════════════════════════════════════════════════════╝
```
