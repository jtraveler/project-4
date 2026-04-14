# CC_SPEC_154_M_CSS_FIXES.md
# CSS: Aspect Ratio Flex-wrap + Border/Background Skin Updates

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 154
**Migration Required:** No
**Agents Required:** 2 minimum
**Files:** bulk-generator.css

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **Run `collectstatic` after all changes**
4. **DO NOT COMMIT until developer confirms visual check**
5. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📁 STEP 0 — MANDATORY READS

```bash
# Read all affected rules to get exact current values for anchors
grep -n "\.bg-select\b\|\.bg-char-textarea\b\|\.bg-btn-group\b" \
    static/css/pages/bulk-generator.css | grep -v "option\|wrapper\|::after"

grep -n "\.bg-visibility-card\b\|\.bg-api-key-section\b\|\.bg-tier-section\b\|\.bg-prompt-box\b" \
    static/css/pages/bulk-generator.css

grep -n "#settingAspectRatio\|settingAspectRatio" \
    static/css/pages/bulk-generator.css

# File size
wc -l static/css/pages/bulk-generator.css
```

---

## 📁 CHANGE 1 — Aspect ratio buttons flex-wrap

Add new rule for `#settingAspectRatio` at the end of the file,
or after the existing `.bg-btn-group` rule block.

```css
/* Aspect ratio selector — wraps to multiple rows when many options shown.
   Uses ::after filler to left-align the last row without stretching buttons. */
#settingAspectRatio {
    flex-wrap: wrap;
    gap: 4px;
}

#settingAspectRatio .bg-btn-group-option {
    flex: 0 0 auto;
    min-width: 52px;
}

#settingAspectRatio::after {
    content: '';
    flex: 1;
}
```

---

## 📁 CHANGE 2 — `.bg-select` border → `--gray-300`

From Step 0, find the current border value on `.bg-select`:

```css
    border: 1px solid var(--gray-400, #a3a3a3);
```

Replace with:

```css
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

## 📁 CHANGE 3 — `.bg-char-textarea` border → `--gray-300`

From Step 0, find the current border value on `.bg-char-textarea`:

```css
    border: 1px solid var(--gray-400, #A3A3A3);
```

Replace with:

```css
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

## 📁 CHANGE 4 — `.bg-btn-group` background + border

From Step 0, find current `.bg-btn-group` background:

```css
    background: var(--gray-200, #E5E5E5);
```

Replace with:

```css
    background: var(--gray-100, #F5F5F5);
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

## 📁 CHANGE 5 — `.bg-visibility-card` background + border

From Step 0, find current `.bg-visibility-card` values and update:
- background → `var(--gray-100, #F5F5F5)`
- border → `1px solid var(--gray-300, #D4D4D4)` (may already be correct)

---

## 📁 CHANGE 6 — `.bg-api-key-section` background + border

From Step 0, find current `.bg-api-key-section` values:

```css
    background: var(--gray-200, #E5E5E5);
    border: none;
```

Replace with:

```css
    background: var(--gray-100, #F5F5F5);
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

## 📁 CHANGE 7 — `.bg-tier-section` background + border

From Step 0, find current `.bg-tier-section` values:

```css
    background: var(--gray-200, #E5E5E5);
    border: none;
```

Replace with:

```css
    background: var(--gray-100, #F5F5F5);
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

## 📁 CHANGE 8 — `.bg-prompt-box` border → `1px`

From Step 0, find current `.bg-prompt-box` border:

```css
    border: 2px solid var(--gray-300, #D4D4D4);
```

Replace with:

```css
    border: 1px solid var(--gray-300, #D4D4D4);
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Aspect ratio rule added
grep -n "settingAspectRatio\|flex-wrap\|flex: 0 0 auto" \
    static/css/pages/bulk-generator.css | head -8

# 2. Gray-300 borders applied
grep -n "gray-300\|D4D4D4" static/css/pages/bulk-generator.css | head -15

# 3. Gray-100 backgrounds applied
grep -n "gray-100\|F5F5F5" static/css/pages/bulk-generator.css | head -10

# 4. bg-prompt-box border is 1px not 2px
grep -A 3 "\.bg-prompt-box {" static/css/pages/bulk-generator.css | head -5

# 5. collectstatic
python manage.py collectstatic --noinput
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `#settingAspectRatio` flex-wrap rule added
- [ ] `#settingAspectRatio::after` filler added
- [ ] `.bg-select` border → `--gray-300`
- [ ] `.bg-char-textarea` border → `--gray-300`
- [ ] `.bg-btn-group` background → `--gray-100`, border added `--gray-300`
- [ ] `.bg-visibility-card` background → `--gray-100`, border → `--gray-300`
- [ ] `.bg-api-key-section` background → `--gray-100`, border → `--gray-300`
- [ ] `.bg-tier-section` background → `--gray-100`, border → `--gray-300`
- [ ] `.bg-prompt-box` border → `1px` (was `2px`)
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify `#settingAspectRatio::after` flex filler correctly left-aligns last row
- Verify `flex: 0 0 auto` on buttons prevents stretching
- Verify no contrast issues: `--gray-100` backgrounds against `#f9f8f6` page bg
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify all 8 changes applied
- Verify `.bg-btn-group` base rule updated (not just the `#settingAspectRatio` override)
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL VISUAL CHECK

Hard refresh (`Cmd+Shift+R`) then:

1. Select Flux Schnell → aspect ratio buttons wrap cleanly to 2 rows ✅
2. Last row buttons are left-aligned (not spread across full width) ✅
3. All buttons equal width, not stretched ✅
4. Form controls (select, textarea) have lighter grey border ✅
5. Button groups (dimensions, images per prompt) have grey background + border ✅
6. Prompt boxes have thinner 1px border ✅
7. API key + Tier sections have grey background + grey border ✅

---

## 💾 COMMIT MESSAGE

```
style(bulk-gen): aspect ratio flex-wrap, border/background skin updates

- #settingAspectRatio: flex-wrap + ::after filler for clean left-aligned rows
- Form controls: border → --gray-300 (lighter than --gray-400)
- .bg-btn-group, .bg-visibility-card: background → --gray-100, border --gray-300
- .bg-api-key-section, .bg-tier-section: background → --gray-100, border --gray-300
- .bg-prompt-box: border 2px → 1px
```

---
**END OF SPEC 154-M**
