# CC_SPEC_132_B_SESSION131_CLEANUP.md
# Session 131 Remaining Fixes — Regex, Module Constant, Thumbnail, Modal Link

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 132
**Phase:** Cleanup
**Modifies UI/Templates:** YES (prompt_detail.html)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~10 lines across 3 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **Read this entire spec** before making any changes
5. **`bulk_generator_views.py` is ✅ Safe** — normal editing
6. **`prompt_detail.html` is 🟡 Caution (1,010 lines)** — str_replace with 5+ line anchors

---

## 📋 OVERVIEW

Four small cleanup items flagged by agents in Session 131 reports. All are
low-risk changes that improve code quality or UX without touching any logic.

1. **Dead regex tail** — `_SRC_IMG_EXTENSIONS` in `bulk_generator_views.py`
   still has `(\?.*)?$` which is now dead code since the regex runs against
   `_parsed.path` (which never contains query strings). Simplify to clean it up.

2. **Module-level constant** — `_SRC_IMG_EXTENSIONS` is currently compiled
   inside `create_job()` on every call. Move to module level for correctness
   and minor performance improvement.

3. **Thumbnail max-height** — the source image thumbnail in `prompt_detail.html`
   has no height constraint. A tall portrait source image will make the rail
   card disproportionately tall. Add `max-height: 80px; object-fit: cover;`

4. **Open in new tab link** — add a small link below the modal image so staff
   can open the source image at full resolution in a new tab for comparison.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find current _SRC_IMG_EXTENSIONS definition
grep -n "_SRC_IMG_EXTENSIONS\|SRC_IMG" prompts/views/bulk_generator_views.py

# 2. Find source image thumbnail in prompt_detail.html
grep -n "source-image-thumb\|source_image_card\|b2_source_image_url" prompts/templates/prompts/prompt_detail.html

# 3. Find source image modal body in prompt_detail.html
grep -n "sourceImageModal\|source-image-modal\|modal-body.*source" prompts/templates/prompts/prompt_detail.html
```

---

## 📁 STEP 1 — Simplify and promote `_SRC_IMG_EXTENSIONS`

**File:** `prompts/views/bulk_generator_views.py`

### Step 1a — Find current definition
From Step 0 grep, locate `_SRC_IMG_EXTENSIONS = re.compile(...)` inside
`create_job()`. Note the exact current regex string.

### Step 1b — Move to module level
Find the module-level imports/constants section at the top of the file (where
other module-level constants like `VALID_SIZES`, `VALID_PROVIDERS` etc. live).
Add the simplified constant there:

```python
_SRC_IMG_EXTENSIONS = re.compile(r'\.(jpg|jpeg|png|webp|gif|avif)$', re.IGNORECASE)
```

### Step 1c — Remove the old in-function definition
Remove the old `_SRC_IMG_EXTENSIONS = re.compile(...)` line from inside
`create_job()`. The reference to `_SRC_IMG_EXTENSIONS` in the validation
code stays exactly as-is — it now reads from the module-level constant.

⚠️ Do NOT change the validation line itself — only move and simplify the
constant definition.

---

## 📁 STEP 2 — Add max-height to thumbnail in `prompt_detail.html`

**File:** `prompts/templates/prompts/prompt_detail.html`

From Step 0 grep, find the `source-image-thumb` img tag. Update its inline style:

**Current:**
```html
style="max-width: 120px; border-radius: var(--radius-sm, 6px); display: block; margin-bottom: 0.5rem;"
```

**Replace with:**
```html
style="max-width: 120px; max-height: 80px; object-fit: cover; border-radius: var(--radius-sm, 6px); display: block; margin-bottom: 0.5rem;"
```

---

## 📁 STEP 3 — Add "Open in new tab" link in modal

**File:** `prompts/templates/prompts/prompt_detail.html`

From Step 0 grep, find the `modal-body` div inside `#sourceImageModal`.

**Current modal body:**
```html
            <div class="modal-body text-center p-2">
                <img src="{{ prompt.b2_source_image_url }}"
                     alt="Full size source image for {{ prompt.title }}"
                     class="img-fluid"
                     loading="lazy"
                     style="max-height: 80vh; object-fit: contain;">
            </div>
```

**Replace with:**
```html
            <div class="modal-body text-center p-2">
                <img src="{{ prompt.b2_source_image_url }}"
                     alt="Full size source image for {{ prompt.title }}"
                     class="img-fluid"
                     loading="lazy"
                     style="max-height: 80vh; object-fit: contain;">
                <div class="mt-2">
                    <a href="{{ prompt.b2_source_image_url }}"
                       target="_blank"
                       rel="noopener"
                       class="btn-outline-standard action-icon-btn"
                       aria-label="Open source image in new tab">
                        <svg class="icon icon-sm" aria-hidden="true"><use href="{% static 'icons/sprite.svg' %}#icon-external-link"/></svg>
                        Open in new tab
                    </a>
                </div>
            </div>
```

⚠️ `icon-external-link` is already used in the SOURCE / CREDIT card at line 466
of `prompt_detail.html` — it exists in the sprite. Do NOT use a different icon.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `_SRC_IMG_EXTENSIONS` now at module level (not inside `create_job()`)
- [ ] Regex simplified — no `(\?.*)?` tail
- [ ] `re.IGNORECASE` retained
- [ ] Old in-function definition removed
- [ ] Thumbnail has `max-height: 80px; object-fit: cover;` added
- [ ] Modal "Open in new tab" link uses `icon-external-link` (confirmed in sprite)
- [ ] Modal link has `rel="noopener"` and `target="_blank"`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.

### 1. @django-pro
- Verify `_SRC_IMG_EXTENSIONS` is now at module level and removed from function
- Verify regex is correct and `re.IGNORECASE` is retained
- Verify no other code in `create_job()` depends on `_SRC_IMG_EXTENSIONS`
  being defined locally (it shouldn't — module-level is fine)
- Rating requirement: 8+/10

### 2. @frontend-developer
- Verify `max-height: 80px; object-fit: cover;` added correctly to thumbnail
- Verify `icon-external-link` is used (not a different icon)
- Verify modal link has `target="_blank"` and `rel="noopener"`
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Score MUST be below 6 if:
- `_SRC_IMG_EXTENSIONS` still defined inside `create_job()`
- Modal link missing `rel="noopener"` (security requirement for target="_blank")
- `icon-external-link` replaced with an icon not confirmed in sprite

---

## 🧪 TESTING

```bash
python manage.py check
```
Expected: 0 issues. No new tests required — these are cosmetic/cleanup changes.
Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix: promote _SRC_IMG_EXTENSIONS to module level, thumbnail max-height, modal open-in-new-tab
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_132_B_SESSION131_CLEANUP.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
