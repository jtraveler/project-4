# CC_SPEC_153_F_COST_MAP_AND_ANIMATION_FIX.md
# Fix Input Page Pricing + Accurate Per-Image Progress Bar on Refresh

**Spec Version:** 2.0 (supersedes v1.0 — implements Option C timestamp approach)
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No
**Migration Required:** YES — new nullable DateTimeField on GeneratedImage
**Agents Required:** 4 minimum
**Estimated Scope:** 6 files (models, migration, tasks, service, JS×2, CSS)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`prompts/models.py` is 🔴 CRITICAL** — max 2 str_replace calls
4. **`prompts/tasks.py` is 🔴 CRITICAL** — use sed, NOT str_replace
5. **DO NOT COMMIT** until developer confirms both browser tests
6. **WORK IS REJECTED** if any agent scores below 8/10

---

## 📋 OVERVIEW

### Two Bugs Fixed in One Spec

---

### Bug 1 — Input Page Pricing Discrepancy (CONFIRMED)

`static/js/bulk-generator.js` (the input page) has its own hardcoded
`I.COST_MAP` at lines 97-101 with old GPT-Image-1 prices. Spec 153-C
updated `prompts/constants.py` and Python fallbacks but missed this JS
copy. The sticky bar on the input page shows inflated prices that do not
match the job results page.

---

### Bug 2 — Per-Image Progress Bar Restarts / Disappears on Refresh

**Root cause (confirmed):** Spec 153-B added `G.isFirstRenderPass` to
prevent the fake timed CSS animation from restarting on page refresh.
However the fix was incomplete — it removed the progress bar but did not
ensure the container remains visible without it, causing the spinner to
disappear or the card to appear blank.

**Option C fix:** Add a `generating_started_at` timestamp to
`GeneratedImage`. When the status API returns this timestamp, the JS
calculates the true elapsed time and starts the CSS animation at the
correct position using a negative `animation-delay`. The bar is now
accurate — it reflects how long OpenAI has actually been working on the
image, survives page refresh, and never restarts from 0%.

The `isFirstRenderPass` guard is removed entirely and replaced with
timestamp-aware logic:
- **`generating_started_at` known** → show bar at correct elapsed position
- **`generating_started_at` unknown (fallback)** → show spinner + label only

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ `I.COST_MAP` in `bulk-generator.js` uses GPT-Image-1.5 prices
- ✅ `GeneratedImage.generating_started_at` field added (nullable DateTimeField)
- ✅ Migration created and applied cleanly
- ✅ `tasks.py`: `generating_started_at = timezone.now()` set when status → `'generating'`
- ✅ `api_job_status` response includes `generating_started_at` per image (ISO string or null)
- ✅ `updateSlotToGenerating` uses elapsed time to set `animation-delay` on fill bar
- ✅ CSS fix: `.placeholder-generating` container visible without `.placeholder-progress-wrap`
- ✅ `isFirstRenderPass` flag and guard removed from BOTH JS files
- ✅ On page refresh: spinner + bar at correct elapsed position (not 0%)
- ✅ Full suite passes

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm I.COST_MAP current values
sed -n '93,106p' static/js/bulk-generator.js

# 2. Confirm GeneratedImage has no generating_started_at yet
grep -n "generating_started_at\|completed_at\|created_at" prompts/models.py | tail -10

# 3. Find exact line where img.status = 'generating' is set in tasks.py
grep -n "img.status.*=.*'generating'\|img\.save.*status" prompts/tasks.py | head -10

# 4. Find get_job_status in bulk_generation.py — read image dict structure
grep -n "def get_job_status\|'status'\|'image_url'\|'prompt_order'\|'variation_number'\|generating_started" \
    prompts/services/bulk_generation.py | head -30

# 5. Read CSS for loading/generating states
grep -n "placeholder-generating\|placeholder-loading\|loading-spinner\|placeholder-progress" \
    static/css/pages/bulk-generator-job.css

# 6. Confirm isFirstRenderPass locations
grep -n "isFirstRenderPass" static/js/bulk-generator-ui.js \
    static/js/bulk-generator-polling.js

# 7. File sizes
wc -l prompts/models.py prompts/tasks.py prompts/services/bulk_generation.py \
    static/js/bulk-generator-ui.js static/js/bulk-generator-polling.js \
    static/js/bulk-generator.js static/css/pages/bulk-generator-job.css

# 8. Confirm timezone is imported in tasks.py
grep -n "from django.utils import timezone" prompts/tasks.py | head -3

# 9. Baseline test count
python manage.py test --verbosity=0 2>&1 | tail -3
```

**Do not proceed until all greps are complete.**

---

## 📁 FILE CHANGES

---

### File 1: `prompts/models.py` — Add `generating_started_at`

**Tier: 🔴 CRITICAL — max 2 str_replace calls**

Find the timestamps section in `GeneratedImage` (has `created_at` and
`completed_at`). Add `generating_started_at` between them:

```python
# BEFORE
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

# AFTER
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    generating_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the image generation call was dispatched to OpenAI. '
                  'Used by the job page to show accurate per-image progress '
                  'on page refresh.'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
```

---

### File 2: Migration

```bash
python manage.py makemigrations --name add_generating_started_at_to_generated_image
python manage.py migrate
```

Expected: `AddField` on `GeneratedImage.generating_started_at`.
Nullable — no data migration needed.

---

### File 3: `prompts/tasks.py` — Set timestamp when status → generating

**Tier: 🔴 CRITICAL — use sed, NOT str_replace**

From Step 0 grep 3, confirm exact context. Then:

```bash
# Step 1: add the timestamp assignment after the status line
sed -i "s/            img\.status = 'generating'/            img.status = 'generating'\n            img.generating_started_at = timezone.now()/" prompts/tasks.py

# Step 2: add the field to update_fields
sed -i "s/img\.save(update_fields=\['status'\])/img.save(update_fields=['status', 'generating_started_at'])/" prompts/tasks.py
```

Verify both changes applied:
```bash
grep -n "generating_started_at" prompts/tasks.py
```
Expected: 2 lines — the assignment and the update_fields entry.

If `timezone` is NOT already imported (check Step 0 grep 8), add:
```python
from django.utils import timezone
```

---

### File 4: `prompts/services/bulk_generation.py` — Add to API response

**Tier: Check `wc -l` from Step 0.**

From Step 0 grep 4, read the per-image dict in `get_job_status`.
Add `generating_started_at` to each image dict:

```python
# ADD this key to the per-image dict (alongside existing keys like 'status', 'image_url', etc.)
'generating_started_at': (
    img.generating_started_at.isoformat()
    if img.generating_started_at else None
),
```

Use the exact surrounding context from Step 0 grep 4 as your str_replace anchor.

---

### File 5: `static/js/bulk-generator-ui.js` — Timestamp-aware animation

**Tier: Check `wc -l` from Step 0.**

**Change 1 — Remove `isFirstRenderPass` clear from `renderImages`:**

Find and remove from end of `renderImages` (line ~142):
```javascript
        // Clear first-render flag after initial gallery is built.
        // Subsequent polls know they are live (not a page-refresh scenario).
        G.isFirstRenderPass = false;
```

**Change 2 — Update `updateSlotToGenerating` signature and logic:**

The function currently takes `(groupIndex, slotIndex, quality)`.
Add the `generatingStartedAt` parameter and replace the `isFirstRenderPass`
guard with timestamp-aware progress bar logic.

Find the section after `loading.appendChild(genLabel);` and the
`isFirstRenderPass` guard. Replace with:

```javascript
        loading.appendChild(spinner);
        loading.appendChild(genLabel);

        // Show the progress bar with an accurate elapsed-time offset so it
        // reflects true generation time. Uses a negative CSS animation-delay —
        // e.g. if 8s have elapsed on a 20s animation, delay is -8s so the bar
        // starts at 40% and continues forward. This is accurate on both initial
        // load AND page refresh. Falls back to spinner-only if no timestamp.
        if (generatingStartedAt) {
            var elapsed = (Date.now() - new Date(generatingStartedAt).getTime()) / 1000;
            // Cap at 90% of duration — don't show near-complete bar for
            // an image that is still generating server-side.
            var offset = Math.min(elapsed, duration * 0.9);

            var progressWrap = document.createElement('div');
            progressWrap.className = 'placeholder-progress-wrap';
            var progressFill = document.createElement('div');
            progressFill.className = 'placeholder-progress-fill';
            progressFill.style.animationDuration = duration + 's';
            // Negative delay starts animation mid-progress accurately
            progressFill.style.animationDelay = '-' + offset.toFixed(2) + 's';
            progressWrap.appendChild(progressFill);
            loading.appendChild(progressWrap);
        }
```

**Change 3 — Pass `generatingStartedAt` from `renderImages`:**

```javascript
// BEFORE
G.updateSlotToGenerating(groupIndex, slotIndex, imgQuality);

// AFTER
G.updateSlotToGenerating(groupIndex, slotIndex, imgQuality,
    image.generating_started_at || null);
```

---

### File 6: `static/js/bulk-generator-polling.js` — Remove `isFirstRenderPass` init

Find and remove from `initPage` (line ~306):
```javascript
        G.isFirstRenderPass = true;  // Cleared after first renderImages() call
```

---

### File 7: `static/css/pages/bulk-generator-job.css` — Fix container visibility

**Tier: ✅ SAFE**

From Step 0 grep 5, determine whether `.placeholder-loading` or
`.placeholder-generating` collapses when `.placeholder-progress-wrap`
is absent. If yes, add explicit sizing so the container stays visible
with only spinner + label present:

```css
/* Ensure generating placeholder stays visible even without the progress
   bar child (e.g. when generating_started_at is null). */
.placeholder-loading.placeholder-generating {
    min-height: 80px; /* match .placeholder-queued height — verify from existing CSS */
}
```

⚠️ Read the existing CSS values before applying. Match the `min-height`
to `.placeholder-queued` so both states have consistent sizing.
Document the root cause in Section 4 of the report.

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Field in model
grep -n "generating_started_at" prompts/models.py

# 2. Field set in tasks.py (expect 2 lines)
grep -n "generating_started_at" prompts/tasks.py

# 3. Field in API response
grep -n "generating_started_at" prompts/services/bulk_generation.py

# 4. JS uses field and negative delay
grep -n "generating_started_at\|animationDelay\|generatingStartedAt\|animation-delay" \
    static/js/bulk-generator-ui.js

# 5. isFirstRenderPass completely gone
grep -rn "isFirstRenderPass" static/js/
# Expected: 0 results

# 6. I.COST_MAP old prices gone
grep -n "0\.011\|0\.016\|0\.042\|0\.063\|0\.167\|0\.250" static/js/bulk-generator.js | grep -i "cost"
# Expected: 0 results

# 7. Migration exists
ls prompts/migrations/ | grep "generating_started"

# 8. collectstatic
python manage.py collectstatic --noinput

# 9. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `generating_started_at` field added to `GeneratedImage` model
- [ ] Migration created and applied
- [ ] `tasks.py`: timestamp set atomically with status in same `.save()` call
- [ ] `timezone` import confirmed in `tasks.py`
- [ ] API response includes `generating_started_at` (ISO or null)
- [ ] `updateSlotToGenerating` uses negative `animationDelay`
- [ ] `isFirstRenderPass` removed from BOTH JS files (grep returns 0 results)
- [ ] `I.COST_MAP` has 9 updated GPT-Image-1.5 values
- [ ] CSS fix applied — container visible without progress bar child
- [ ] `collectstatic` run
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.

### 1. @django-security
- Confirm `generating_started_at` set atomically with status in same `.save()`
- Confirm ISO timestamp in API response doesn't leak sensitive data
- Confirm nullable field has correct null/blank settings
- Rating requirement: **8+/10**

### 2. @frontend-developer
- Verify `elapsed` uses `Date.now()` minus ISO timestamp correctly
- Verify negative `animation-delay` starts animation mid-progress in all major browsers
- Verify 90% cap prevents premature near-complete display
- Verify `isFirstRenderPass` fully removed — show Step 1 grep 5 (0 results)
- Rating requirement: **8+/10**

### 3. @accessibility-expert
- Confirm `role="status"` and `aria-label="Image generating"` in all code paths
- Confirm spinner + label visible in both timestamp-known and fallback paths
- Confirm CSS fix preserves AT perception of loading state
- Rating requirement: **8+/10**

### 4. @tdd-coach
- Verify `generating_started_at` is set in the task execution test
- Verify API response test checks for `generating_started_at` key
- Verify fallback path (null timestamp → no progress bar) is tested
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- `isFirstRenderPass` still present anywhere in JS
- `generating_started_at` not in API response
- Positive (not negative) `animation-delay` used
- `I.COST_MAP` still has old prices
- Migration not created or not applied
- CSS container still invisible without progress bar child

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): accurate per-image progress on refresh via generating_started_at

- GeneratedImage: add generating_started_at nullable DateTimeField
- tasks.py: set generating_started_at when status → generating
- bulk_generation.py: include generating_started_at in status API response
- bulk-generator-ui.js: use negative animation-delay for elapsed-time
  accurate progress bar; remove isFirstRenderPass guard
- bulk-generator-polling.js: remove isFirstRenderPass init
- bulk-generator-job.css: fix .placeholder-generating visibility
- bulk-generator.js: update I.COST_MAP to GPT-Image-1.5 pricing
- migration 00XX: add generating_started_at to GeneratedImage
```

---

## ⛔ CRITICAL REMINDERS (Repeated)

- **`tasks.py` — sed only** (CRITICAL tier, 3500+ lines)
- **`models.py` — max 2 str_replace calls** (CRITICAL tier, 3000+ lines)
- **Negative `animation-delay`** — positive delay adds a pause, not an offset
- **Remove `isFirstRenderPass` from BOTH files** — grep must return 0
- **Run `collectstatic`** — JS/CSS never reaches Heroku without it
- **Both browser checks required** before committing

---

**END OF SPEC**
