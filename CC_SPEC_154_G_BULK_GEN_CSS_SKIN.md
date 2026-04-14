# CC_SPEC_154_G_BULK_GEN_CSS_SKIN.md
# Bulk Generator CSS — New #f9f8f6 Background Skin Updates

**Spec Version:** 2.0
**Date:** April 2026
**Session:** 154
**Modifies UI/Templates:** Yes (bulk_generator.html — adds class to 2 buttons)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** bulk-generator.css, style.css, bulk_generator.html

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **Run `collectstatic` after all changes**
4. **DO NOT COMMIT until developer confirms visual check**
5. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 OVERVIEW

The app background is changing to `#f9f8f6`. Several bulk generator
elements need updated backgrounds and text colours. Additionally,
`.bg-reset-master-btn` and `.bg-clear-all-btn` are being refactored to
use the shared `.btn-outline-standard` class for visual styling (Option A
— additive approach). This means one future change to `btn-outline-standard`
updates both buttons automatically.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm current .bg-reset-master-btn and .bg-clear-all-btn rules
sed -n '508,577p' static/css/pages/bulk-generator.css

# 2. Confirm btn-outline-standard in style.css
sed -n '1106,1148p' static/css/style.css

# 3. Find reset and clear-all buttons in template
grep -n "bg-reset-master-btn\|bg-clear-all-btn" \
    prompts/templates/prompts/bulk_generator.html | head -5

# 4. Confirm current bg-api-key-section and bg-tier-section
sed -n '1323,1335p' static/css/pages/bulk-generator.css
sed -n '1629,1636p' static/css/pages/bulk-generator.css

# 5. File sizes
wc -l static/css/pages/bulk-generator.css static/css/style.css \
    prompts/templates/prompts/bulk_generator.html
```

---

## 📁 FILE 1 — `static/css/style.css`

### Change 1 — `.btn-outline-standard` background → white

```css
/* BEFORE */
  background-color: transparent;

/* AFTER */
  background-color: #ffffff;
```

Also update the hover to stay clearly distinct from white base:

```css
/* .btn-outline-standard:hover BEFORE */
  background-color: var(--gray-50, #fafafa);

/* AFTER */
  background-color: var(--gray-100, #f5f5f5);
```

This makes all `.btn-outline-standard` buttons white globally — correct
since the page background is now `#f9f8f6` (transparent would blend in).

---

## 📁 FILE 2 — `static/css/pages/bulk-generator.css`

### Change 2 — `.bg-select` background → white

```css
/* BEFORE: line ~118 */
    background: var(--gray-100, #f5f5f5);

/* AFTER */
    background: #ffffff;
```

Leave `.bg-select:disabled` unchanged — grey background correctly
signals inactive state.

---

### Change 3 — `.bg-char-textarea` background + border

```css
/* BEFORE: lines ~170-171 */
    background: var(--gray-50, #FAFAFA);
    border: 1px solid var(--gray-200, #E5E5E5);

/* AFTER */
    background: #ffffff;
    border: 1px solid var(--gray-400, #A3A3A3);
```

---

### Change 4 — `.bg-btn-group` background

```css
/* BEFORE: line ~220 */
    background: var(--gray-100, #F5F5F5);

/* AFTER */
    background: var(--gray-200, #E5E5E5);
```

---

### Change 5 — `.bg-ref-upload` — add white background

No background property currently exists on this rule. Add it as the
first property:

```css
.bg-ref-upload {
    background: #ffffff;
    border: 2px dashed var(--gray-300, #D4D4D4);
    /* ... rest unchanged ... */
}
```

---

### Change 6 — `.bg-visibility-card` background + border

```css
/* BEFORE: lines ~277-278 */
    background: var(--gray-50, #FAFAFA);
    border: 1px solid var(--gray-100, #F5F5F5);

/* AFTER */
    background: #ffffff;
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

### Change 7 — `.bg-reset-master-btn` — strip visual styles, keep layout only

Since `.btn-outline-standard` now owns the visual appearance, remove
the duplicate visual properties from `.bg-reset-master-btn`. Keep only
what is unique to this button (the `display`, `gap`, `padding`,
`font-size`, `font-weight`, `cursor`, `transition`, `font-family` that
differ from or add to `btn-outline-standard`).

Replace the entire `.bg-reset-master-btn` block with:

```css
/* Reset master settings button
   Visual styling inherited from .btn-outline-standard (style.css).
   Only layout overrides here. */
.bg-reset-master-btn {
    gap: 6px;
    padding: 8px 14px;
    font-size: 0.8125rem;
    font-weight: 500;
    font-family: inherit;
}
```

Remove the `:hover` and `:focus-visible` blocks for `.bg-reset-master-btn`
entirely — `btn-outline-standard` provides these states.

---

### Change 8 — `.bg-clear-all-btn` — strip visual styles, keep layout only

Same approach as Change 7. The `:hover` red tint is unique to this
button and must be preserved.

Replace `.bg-clear-all-btn` base rule with:

```css
/* Clear all button
   Visual styling inherited from .btn-outline-standard (style.css).
   Only layout overrides here. */
.bg-clear-all-btn {
    gap: 6px;
    padding: 6px 14px;
    font-size: 0.8125rem;
    font-weight: 500;
    font-family: inherit;
}
```

Keep the `:hover` red tint — it overrides `btn-outline-standard:hover`
correctly:

```css
.bg-clear-all-btn:hover {
    border-color: var(--red-400, #f87171);
    color: var(--red-600, #dc2626);
    background: var(--red-50, #fef2f2);
}
```

Remove `.bg-clear-all-btn:focus-visible` — `btn-outline-standard:focus`
handles this.

Keep `.bg-clear-all-btn .icon { width: 14px; height: 14px; }` — layout
only.

---

### Change 9 — `.bg-api-key-section` — remove border, grey background

```css
/* BEFORE */
    background: var(--gray-50, #fafafa);
    border: 1px solid var(--gray-200, #e5e7eb);

/* AFTER */
    background: var(--gray-200, #E5E5E5);
    border: none;
```

---

### Change 10 — `.bg-tier-section` — remove border, grey background

```css
/* BEFORE */
    background: var(--gray-50, #fafafa);
    border: 1px solid var(--gray-200, #e5e7eb);

/* AFTER */
    background: var(--gray-200, #E5E5E5);
    border: none;
```

---

### Change 11 — `.bg-api-key-subtitle` text colour

```css
/* BEFORE */
    color: var(--gray-500, #737373);

/* AFTER */
    color: var(--gray-800, #262626);
```

---

### Change 12 — `.bg-setting-hint` + `.bg-setting-hint-inline` text colour

```css
/* .bg-setting-hint BEFORE */
    color: var(--gray-500, #737373);

/* AFTER */
    color: var(--gray-800, #262626);
```

```css
/* .bg-setting-hint-inline BEFORE */
    color: var(--gray-500, #737373);

/* AFTER */
    color: var(--gray-800, #262626);
```

---

### Change 13 — `.bg-api-key-help` text colour

```css
/* BEFORE */
    color: var(--gray-500, #737373);

/* AFTER */
    color: var(--gray-800, #262626);
```

---

### Change 14 — `.bg-byok-toggle-wrap` margin

⚠️ Check first:
```bash
grep -n "bg-byok-toggle-wrap" prompts/templates/prompts/bulk_generator.html
```

If the toggle still exists in the template (154-F not yet committed),
add the rule:

```css
.bg-byok-toggle-wrap {
    margin-bottom: 20px;
}
```

If 154-F has removed the toggle, skip this change and note in report.

---

## 📁 FILE 3 — `prompts/templates/prompts/bulk_generator.html`

### Change 15 — Add `btn-outline-standard` to reset and clear-all buttons

From Step 0 grep 3, find the two buttons. Add the class:

```html
<!-- Reset button: add btn-outline-standard -->
<button class="bg-reset-master-btn btn-outline-standard" ...>

<!-- Clear all button: add btn-outline-standard -->
<button class="bg-clear-all-btn btn-outline-standard" ...>
```

Use the exact surrounding HTML from Step 0 grep 3 as anchors.

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. btn-outline-standard background is white
grep -A 3 "\.btn-outline-standard {" static/css/style.css | grep "background"
# Expected: background-color: #ffffff

# 2. Both buttons have btn-outline-standard in template
grep -n "btn-outline-standard" prompts/templates/prompts/bulk_generator.html
# Expected: 2 results

# 3. bg-reset-master-btn no longer has background/border/color rules
grep -A 8 "\.bg-reset-master-btn {" static/css/pages/bulk-generator.css
# Expected: only gap/padding/font rules, no background/border/color

# 4. bg-clear-all-btn keeps its red hover
grep -A 4 "\.bg-clear-all-btn:hover" static/css/pages/bulk-generator.css
# Expected: red-400 border, red-600 color, red-50 background

# 5. API key section and tier section have no border
grep -A 5 "\.bg-api-key-section {" static/css/pages/bulk-generator.css | grep "border"
# Expected: border: none

# 6. Hint text colours updated
grep -n "gray-800\|262626" static/css/pages/bulk-generator.css | head -10

# 7. collectstatic
python manage.py collectstatic --noinput

# 8. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `btn-outline-standard` background → `#ffffff` in style.css
- [ ] Both buttons have `btn-outline-standard` class in template
- [ ] `.bg-reset-master-btn` stripped to layout-only rules
- [ ] `.bg-clear-all-btn` stripped to layout-only, red hover preserved
- [ ] `.bg-select` → white (disabled state unchanged)
- [ ] `.bg-char-textarea` → white + `--gray-400` border
- [ ] `.bg-btn-group` → `var(--gray-200)`
- [ ] `.bg-ref-upload` → white background added
- [ ] `.bg-visibility-card` → white + `--gray-300` border
- [ ] `.bg-api-key-section` → `--gray-200`, no border
- [ ] `.bg-tier-section` → `--gray-200`, no border
- [ ] All hint/subtitle/help text → `var(--gray-800)`
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify `.bg-clear-all-btn:hover` red tint overrides `btn-outline-standard:hover`
  correctly (specificity check — both single class, last one wins in cascade)
- Verify `btn-outline-standard` white background renders visibly distinct
  against `#f9f8f6` page background
- Verify `.bg-select:disabled` still grey
- Show Step 1 verification outputs
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify no visual properties remain in `.bg-reset-master-btn` base rule
- Verify `btn-outline-standard` class added to both buttons in template
- Verify all 14 CSS changes applied
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL VISUAL CHECK

Hard refresh (`Cmd+Shift+R`) then:

1. Form controls (selects, textarea, ref-upload, visibility card) → white ✅
2. Dimension/quality button groups → visible grey background ✅
3. Reset button → white, outlined, matches other standard buttons on site ✅
4. Clear All button → white, outlined; on hover turns red ✅
5. API Key + Tier sections → grey blocks, no border ✅
6. Hint/subtitle/help text → dark and readable ✅

---

## 💾 COMMIT MESSAGE

```
style(bulk-gen): update elements for #f9f8f6 page skin; btn-outline-standard refactor

- style.css: btn-outline-standard background → white (global)
- bulk-generator.html: add btn-outline-standard to reset + clear-all buttons
- bulk-generator.css: strip visual styles from bg-reset-master-btn/bg-clear-all-btn
  (now inherited from btn-outline-standard); keep red hover on clear-all
- Form controls → white backgrounds; btn-groups → --gray-200
- API key + tier sections → --gray-200, no border
- Hint/subtitle/help text → --gray-800 for readability
```

---

**END OF SPEC**
