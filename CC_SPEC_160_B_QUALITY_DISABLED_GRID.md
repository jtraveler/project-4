# CC_SPEC_160_B_QUALITY_DISABLED_GRID.md
# Quality Section — Restore Disabled/Greyed with High Locked + Fix Grid Layout

**Spec Version:** 1.0
**Session:** 160
**Modifies UI/Templates:** Yes (JS + CSS)
**Migration Required:** No
**Agents Required:** 6 minimum
**Estimated Scope:** 2–3 str_replace in `bulk-generator.js` (🟠 High Risk),
1 str_replace in CSS (✅ Safe)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **`bulk-generator.js` is 🟠 High Risk** — re-read full file before each str_replace
4. **160-C also modifies this file** — this spec must commit first
5. **Do NOT change quality visibility for NB2** — NB2 quality stays visible and
   interactive. Only non-quality-tier models (Flux Dev, Flux Schnell etc.) get
   the disabled treatment.

---

## 📋 CONFIRMED PROBLEMS (verified April 2026)

**Problem 1 — Quality section hidden instead of disabled**
Session 159-B changed quality to `display: none` for non-quality models.
The developer prefers it visible but disabled/greyed — both for UX consistency
(users see "High quality" is locked in) and for future-proofing (per-prompt
model selection will re-enable it without layout shift).

**Problem 2 — Grid layout broken when quality hidden**
When quality is hidden, the Dimensions section spans full width in the
`1fr 1fr` grid. This looks wrong. The fix should either restore the grid
by keeping quality in the layout (disabled approach solves this automatically)
or explicitly set `gridColumn` on Dimensions when quality is absent.

**Design decision confirmed by developer:**
- Non-quality models: quality section **visible but disabled**, value **locked
  to "High"**, greyed appearance
- Reason: future per-prompt model selection will re-enable quality without
  layout shift; users understand "High" = best quality even when locked
- NB2 and GPT-Image-1.5: quality **interactive** as before

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Re-read FULL current bulk-generator.js
cat static/js/bulk-generator.js

# 2. Find the current quality show/hide logic in handleModelChange
grep -n -B 2 -A 15 "quality.*display\|display.*quality\|qualityGroup\|quality.*hide\|quality.*show" \
    static/js/bulk-generator.js | head -60

# 3. Find the per-prompt box quality visibility logic
grep -n "bg-override-quality\|prompt.*quality\|quality.*prompt\|per.*box.*quality" \
    static/js/bulk-generator.js | head -20

# 4. Find the grid/dimensions layout code
grep -n "gridColumn\|1fr.*1fr\|dimensions\|DIMENSIONS" \
    static/js/bulk-generator.js | head -15

# 5. Find the CSS file for the quality group disabled state
grep -rn "qualityGroup\|quality.*disabled\|quality.*group\|bg-setting-group" \
    static/css/ --include="*.css" | head -15

# 6. Confirm current quality option values (low/medium/high)
grep -n "settingQuality\|quality.*option\|option.*quality" \
    prompts/templates/prompts/bulk_generator.html | head -10
```

---

## 📁 STEP 1 — Restore disabled/greyed quality for non-quality models

From Step 0 grep 2, find the quality section handling in `handleModelChange()`.

**For non-quality-tier models** (everything except NB2 and GPT-Image-1.5):

```javascript
// Show quality group but disabled, locked to 'high'
qualityGroupEl.style.display = '';           // visible
qualityGroupEl.style.opacity = '0.5';        // greyed
qualitySelectEl.disabled = true;             // not interactive
qualitySelectEl.value = 'high';              // locked to High
// Add visual indicator class
qualityGroupEl.classList.add('bg-setting-group--disabled');
```

**For quality-tier models** (NB2, GPT-Image-1.5):

```javascript
// Show quality group, fully interactive
qualityGroupEl.style.display = '';
qualityGroupEl.style.opacity = '';           // full opacity
qualitySelectEl.disabled = false;
qualityGroupEl.classList.remove('bg-setting-group--disabled');
```

**Note on opacity:** Developer confirmed in Session 158 that opacity should
be removed (158-A spec). However the developer now wants a disabled appearance
for quality when locked. Use a **CSS class approach** (`bg-setting-group--disabled`)
rather than inline opacity — this keeps `style.opacity` clean and is easier
to maintain. The CSS class can handle the greyed appearance.

---

## 📁 STEP 2 — Apply same treatment to per-prompt box quality selectors

From Step 0 grep 3, find the per-prompt box quality handling. Apply the same
disabled/locked/greyed approach to per-box quality selectors when the model
doesn't support quality tiers:

```javascript
// For each per-prompt quality selector:
promptQualityEl.disabled = !supportsQualityTiers;
promptQualityEl.value = supportsQualityTiers ? promptQualityEl.value : 'high';
promptQualityEl.closest('.quality-wrapper')  // or whatever wrapper class
    ?.classList.toggle('bg-setting-group--disabled', !supportsQualityTiers);
```

---

## 📁 STEP 3 — Fix grid layout

From Step 0 grep 4, if `gridColumn: '1 / -1'` was added to Dimensions in
159-B, remove it — the grid will naturally rebalance when quality stays
in the DOM. Verify the two-column layout is restored.

If the grid is defined in CSS, confirm the two-column layout works correctly
with quality visible but disabled.

---

## 📁 STEP 4 — Add CSS for disabled quality group

From Step 0 grep 5, find the CSS file. Add the disabled appearance class:

```css
.bg-setting-group--quality-disabled select,
.bg-setting-group--quality-disabled label {
    opacity: 0.5;
    cursor: not-allowed;
}
```

**Adjust selector** to match the actual class structure found in Step 0.

---

## 📁 STEP 5 — MANDATORY VERIFICATION

```bash
# 1. Confirm quality group stays visible for all models
grep -n "quality.*display.*none\|display.*none.*quality" static/js/bulk-generator.js
# Expected: 0 results (quality never hidden)

# 2. Confirm disabled/enabled logic present
grep -n "qualitySelectEl.disabled\|quality.*disabled" static/js/bulk-generator.js

# 3. Confirm 'high' lock present for non-quality models
grep -n "qualitySelectEl.value.*high\|value.*=.*['\"]high" static/js/bulk-generator.js

# 4. Confirm gridColumn removal (if it was added in 159-B)
grep -n "gridColumn.*-1\|1.*\/.*-1" static/js/bulk-generator.js
# Expected: 0 results

# 5. Django check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Quality section never hidden — always visible ✓
- [ ] Non-quality models: quality disabled, greyed, locked to "high" ✓
- [ ] Quality-tier models (NB2, GPT-Image-1.5): quality interactive ✓
- [ ] Per-prompt box quality matches master behaviour ✓
- [ ] Grid layout: Dimensions stays in two-column layout ✓
- [ ] CSS class used for greyed appearance (not inline opacity) ✓
- [ ] `python manage.py check` passes ✓

---

## 🤖 AGENT REQUIREMENTS

**Minimum 6 agents. Average 8.5+. All must score 8.0+.**

### 1. @frontend-developer
- When switching from NB2 to Flux Dev, does quality correctly transition
  from interactive → disabled with "High" locked?
- When switching back, does it become interactive again?
- Rating: 8.0+/10

### 2. @ui-visual-validator
- Non-quality model: quality shows greyed, "High" selected, not clickable ✅
- NB2: quality shows interactive 1K/2K/4K ✅
- Two-column grid layout correct in both states ✅
- Rating: 8.0+/10

### 3. @code-reviewer
- Is the CSS class approach cleaner than inline opacity?
- Rating: 8.0+/10

### 4. @accessibility-expert
- `disabled` attribute on `<select>` correctly communicates non-interactivity
  to screen readers?
- Rating: 8.0+/10

### 5. @tdd-orchestrator
- Any existing tests for quality state that need updating?
- Rating: 8.0+/10

### 6. @architect-review
- Is this pattern future-proof for per-prompt model selection where quality
  will need to activate per-box when model is changed at row level?
- Rating: 8.0+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Quality section hidden (`display: none`) for any model
- Grid layout still broken (Dimensions spans full width)
- Quality not locked to "High" for non-quality-tier models
- Inline style opacity used instead of CSS class

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test --verbosity=0
```

**Manual checks:**
1. Select Flux Dev → quality shows **greyed, "High" selected, not clickable** ✅
2. Select NB2 → quality shows **interactive 1K/2K/4K** ✅
3. Grid layout: Dimensions in **same row as quality** (two columns) ✅
4. Switch Flux Dev → NB2 → Flux Dev → each transition correct ✅

---

## 💾 COMMIT MESSAGE

```
fix(ui): quality section disabled/greyed with High locked, grid layout fixed

- Non-quality models: quality visible but disabled, locked to 'high'
- Quality-tier models: quality interactive (unchanged)
- CSS class for greyed appearance instead of inline opacity
- Two-column grid layout restored

Agents: 6 agents, avg X/10, all passed 8.0+ threshold
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_B.md`

---

**END OF SPEC**
