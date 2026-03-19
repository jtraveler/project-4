# CC_SPEC_139_C_RESULTS_PAGE_FIXES.md
# Results Page — btn-select Hover Isolation + 2:3 Default Dimensions

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 139
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~10 lines across 2 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.1** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator-job.css` is 🟡 Caution** — max 3 str_replace calls
4. **`bulk-generator.js` is 🟠 High Risk** — this session already used the
   file budget in Spec A (Spec D from Session 138). Verify current call count
   before editing. If 2 calls already used, treat as Critical tier.
5. **Read current CSS state from disk** — Session 138 Spec C redesigned
   `.btn-select`. Confirm exact current CSS before making changes.

---

## 📋 OVERVIEW

Four items in this spec:

1. **`.btn-select` hover isolation** — hovering the entire image currently
   triggers the selector circle's border and check mark. The circle should
   only react when the user hovers the circle itself.

2. **2:3 as default master dimensions** — change the active/default button
   to the 2:3 ratio (1024×1536 or equivalent).

3. **`clearAllConfirm` paste cleanup** — the Clear All button doesn't fire
   B2 paste cleanup. Add the same fire-and-forget pattern as `deleteBox`.

4. **P3 micro-cleanup batch** — three small items from Session 138 agent
   reports: redundant `filter` in `deleteBox`, lightbox firing on
   `.is-published` slots, and `.btn-select` border opacity on dark images.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read current btn-select CSS (post Session 138 Spec C)
sed -n '620,760p' static/css/pages/bulk-generator-job.css

# 2. Find the dimensions button group in bulk_generator.html
grep -n "1:1\|2:3\|1024\|1536\|dimensions\|settingDimensions\|active" \
    prompts/templates/prompts/bulk_generator.html | head -20

# 3. Find getMasterDimensions in bulk-generator.js
grep -n "getMasterDimensions\|settingDimensions\|active.*dimension\|1024" \
    static/js/bulk-generator.js | head -10

# 4. Find if there's a prompt-image-slot:hover .btn-select rule
grep -n "slot.*hover.*btn\|hover.*slot.*btn\|image-slot:hover" \
    static/css/pages/bulk-generator-job.css | head -10

# 5. Find clearAllConfirm handler in bulk-generator.js
grep -n "clearAll\|clear-all\|clearAllConfirm\|Clear All" \
    static/js/bulk-generator.js | head -10

# 6. Find deleteBox filter (redundant after Session 138 fix)
sed -n '260,280p' static/js/bulk-generator.js

# 7. Find lightbox click delegation for is-published check
grep -n "is-published\|is-discarded\|lightbox\|openLightbox" \
    static/js/bulk-generator-polling.js | head -10

# 8. Read current btn-select border opacity
grep -n "rgba.*btn-select\|btn-select.*border\|border.*0\." \
    static/css/pages/bulk-generator-job.css | head -10
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Fix `.btn-select` hover isolation

**File:** `static/css/pages/bulk-generator-job.css`
**str_replace call 1 of 1**

From Step 0 grep, find the current `.btn-select` hover rules added in
Session 138 Spec C. The issue: the rule
`.prompt-image-slot:hover .btn-select` makes the check mark visible
whenever the user hovers anywhere on the image card.

**Find and remove** any rule of the form:
```css
.prompt-image-slot:hover .btn-select {
    ...
    color: white; /* or similar — makes check visible on image hover */
}
```

The check mark (`color: white` on the SVG) should ONLY appear via:
- `.btn-select:hover` — direct hover on the circle
- `.btn-select:focus-visible` — keyboard focus
- `.prompt-image-slot.is-selected .btn-select` — selected state

The circle border and background should remain visible at all times (it's
a dark semi-transparent circle, always present), but the check mark
should only appear when hovering the circle itself.

**Correct final state for btn-select hover:**
```css
.btn-select:hover {
    background: rgba(0, 0, 0, 0.6);
    color: white; /* check appears only on direct hover */
    border-color: rgba(255, 255, 255, 0.8);
}
```

No `.prompt-image-slot:hover .btn-select` rule should exist.

---

## 📁 STEP 2 — Set 2:3 as default master dimensions

**File:** `prompts/templates/prompts/bulk_generator.html`

From Step 0 grep, find the dimensions button group (`settingDimensions`).
Currently 1:1 (1024×1024) has the `active` class. Change the `active` class
to the 2:3 option (1024×1536).

**Find the active dimension button** — it will look like:
```html
<button ... data-value="1024x1024" class="bg-btn-group-option active">
    1:1
</button>
```

**Remove `active` from 1:1 and add it to 2:3:**
```html
<button ... data-value="1024x1024" class="bg-btn-group-option">
    1:1
</button>
...
<button ... data-value="1024x1536" class="bg-btn-group-option active">
    2:3
</button>
```

⚠️ Read the exact current HTML from Step 0 grep — the button structure,
data-value format, and class names must match exactly. The `active` class
drives `getMasterDimensions()` in `bulk-generator.js`.

⚠️ Also check if localStorage draft saving persists the dimensions setting.
If it does, users with saved drafts may not see the new default. This is
acceptable — the new default only applies for fresh sessions.

---

## 📁 STEP 3 — `clearAllConfirm` paste cleanup

**File:** `static/js/bulk-generator.js`

From Step 0 grep, find the `clearAllConfirm` click handler. Before the
boxes are cleared, iterate over all prompt boxes and fire the paste
delete for any that have a paste URL:

```javascript
        // Clean up B2 paste images before clearing all boxes
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function(box) {
            var pasteInput = box.querySelector('.bg-prompt-source-image-input');
            var pasteUrl = pasteInput ? pasteInput.value.trim() : '';
            if (pasteUrl && pasteUrl.indexOf('/source-paste/') !== -1) {
                fetch('/api/bulk-gen/source-image-paste/delete/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf,
                    },
                    body: JSON.stringify({ cdn_url: pasteUrl }),
                }).catch(function() {
                    // Non-critical — ignore failure
                });
            }
        });
```

Add this immediately before the lines that clear the boxes (before
textarea values are reset).

---

## 📁 STEP 4 — P3 micro-cleanup batch

**4a — Remove redundant `filter` in `deleteBox`**

**File:** `static/js/bulk-generator.js`

From Step 0 grep (Step 6), find the `nextSibling` line in `deleteBox`:

```javascript
            var nextSibling = allCurrent.filter(function (b) { return b !== box; });
```

Since `box` already has `.removing` and `allCurrent` uses `:not(.removing)`,
`box` can never be in `allCurrent`. The filter is redundant:

```javascript
            var nextSibling = allCurrent; // box already excluded by :not(.removing)
```

**4b — Guard lightbox from firing on `.is-published` slots**

**File:** `static/js/bulk-generator-polling.js`

From Step 0 grep, find the image click handler added in Session 138 Spec B:

```javascript
                var clickedImg = e.target.closest('.prompt-image-container img');
                if (clickedImg && !e.target.closest('button')) {
                    var slot = clickedImg.closest('.prompt-image-slot');
```

Add a guard for published slots (published images have a link overlay,
clicking should not open lightbox):

```javascript
                var clickedImg = e.target.closest('.prompt-image-container img');
                if (clickedImg && !e.target.closest('button')) {
                    var slot = clickedImg.closest('.prompt-image-slot');
                    if (slot && slot.classList.contains('is-published')) return;
```

**4c — Raise `.btn-select` border opacity on dark images**

**File:** `static/css/pages/bulk-generator-job.css`

From Step 0 grep, find the current `.btn-select` border rule. Raise opacity
from 0.5 to 0.75:

```css
.btn-select {
    ...
    border: 2px solid rgba(255, 255, 255, 0.75); /* was 0.5 — better visibility on dark images */
    ...
}
```

**4d — Add `source_image_url` to view docstring**

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep (if not already done), find the `api_start_generation`
view docstring (around line 140). Add a note:

```python
    # Each prompt entry may include:
    #   "text": str — the prompt text (required)
    #   "size": str — per-prompt size override (optional)
    #   "quality": str — per-prompt quality override (optional)
    #   "image_count": int — per-prompt image count override (optional)
    #   "source_image_url": str — per-prompt source image URL (optional)
    #     URL must be https:// and end in a recognised image extension.
    #     Used by SRC-6 to download and store the source image to B2.
```

- [ ] Step 0 greps completed
- [ ] `.prompt-image-slot:hover .btn-select` rule removed or not present
- [ ] `.btn-select:hover` only shows check mark on direct hover
- [ ] `.prompt-image-slot.is-selected .btn-select` still shows check mark
- [ ] `active` class moved from 1:1 to 2:3 button in HTML
- [ ] No other dimension button has `active` class
- [ ] `clearAllConfirm` fires paste cleanup before clearing boxes
- [ ] Paste cleanup uses `.catch()` — never blocks clear-all
- [ ] Redundant `filter` in `deleteBox` removed
- [ ] Lightbox guarded from firing on `.is-published` slots
- [ ] `.btn-select` border opacity raised to 0.75
- [ ] `source_image_url` documented in view docstring
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify no `.prompt-image-slot:hover .btn-select` rule remains
- Verify check mark still appears correctly in selected state
- Verify 2:3 button has `active` class, 1:1 does not
- Verify `clearAllConfirm` paste cleanup uses `.catch()` (non-blocking)
- Verify lightbox guard correctly blocks `.is-published` slots
- Verify redundant `filter` removed from `deleteBox`
- Rating requirement: 8+/10

### 2. @ux-ui-designer
- Verify dark circle always visible (not affected by image hover)
- Verify check mark appears only on circle hover
- Verify 2:3 active state visually correct in button group
- Verify border opacity 0.75 improves visibility on dark images
- Rating requirement: 8+/10

### 3. @accessibility
- Verify `.btn-select` non-text contrast meets WCAG 1.4.11 (3:1 ratio)
  with raised border opacity 0.75 on both light and dark image backgrounds
- Verify `clearAllConfirm` keyboard behaviour unchanged
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `.prompt-image-slot:hover .btn-select` rule still exists
- `clearAllConfirm` paste cleanup blocks the clear-all flow on failure
- Lightbox still fires on `.is-published` slot clicks

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser check (Mateo must verify):**
1. Open bulk generator results page → hover anywhere on an image (not the
   circle) → verify selector circle does NOT show a check mark
2. Hover the dark circle in the top-left → verify check mark appears
3. Click a published image → verify lightbox does NOT open
4. Click an unpublished image → verify lightbox opens normally
5. Open bulk generator input page → verify 2:3 is the pre-selected dimension
6. Paste an image → click Clear All → check Heroku logs for `[PASTE-DELETE]`

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(results): btn-select hover isolation, 2:3 default dimension, clear-all paste cleanup, P3 batch
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_139_C_RESULTS_PAGE_FIXES.md`

---

**END OF SPEC**
