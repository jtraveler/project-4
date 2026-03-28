# CC_SPEC_144_A_PASTE_DELETE_FIX.md
# PASTE-DELETE ✕ Button — `.closest()` Fix

**Spec Version:** 1.0 (written after file review)
**Date:** March 2026
**Session:** 144
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** 2 lines in `static/js/bulk-generator.js`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator.js` is ✅ Safe (725 lines)** — no line constraint
4. **This is a P1 bug confirmed in production** — fix exactly as specified

**Work will be REJECTED if `.classList.contains('bg-source-paste-clear')`
is still present after this spec.**

---

## 📋 OVERVIEW

The ✕ clear button on pasted source images does not reliably fire.
The click event listener uses `.classList.contains()` which is an
exact-match-on-target check. When the ✕ button contains an SVG icon
or other child element, `e.target` is the child — not the button —
and `.classList.contains()` silently fails.

The two buttons immediately above it in the same listener (`deleteBtn`
and `resetBtn`) already use `.closest()` correctly. This fix brings
the paste-clear handler in line with the same pattern.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full click listener block to confirm exact current state
sed -n '380,440p' static/js/bulk-generator.js

# 2. Confirm deleteBtn and resetBtn use .closest() (reference pattern)
grep -n "closest\|classList.contains" static/js/bulk-generator.js | head -15

# 3. Confirm exact line number of the broken condition
grep -n "classList.contains('bg-source-paste-clear')" static/js/bulk-generator.js
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Fix the paste-clear handler

**File:** `static/js/bulk-generator.js`
**str_replace: 1 call**

From Step 0 grep 1, read the exact current paste-clear handler block.

**CURRENT (broken):**
```javascript
        // Clear pasted source image
        if (e.target.classList.contains('bg-source-paste-clear')) {
            var clearBox = e.target.closest('.bg-prompt-box');
```

**REPLACE WITH (fixed):**
```javascript
        // Clear pasted source image
        var clearBtn = e.target.closest('.bg-source-paste-clear');
        if (clearBtn) {
            var clearBox = clearBtn.closest('.bg-prompt-box');
```

⚠️ The only other `e.target` reference inside this if-block is
`e.target.closest('.bg-prompt-box')` on the next line. That line
MUST become `clearBtn.closest('.bg-prompt-box')` — as shown above.
Everything else inside the block is unchanged.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm broken pattern is gone
grep -n "classList.contains('bg-source-paste-clear')" static/js/bulk-generator.js

# 2. Confirm fixed pattern is present
grep -n "closest('.bg-source-paste-clear')" static/js/bulk-generator.js

# 3. Confirm no remaining e.target inside the paste-clear block
sed -n '394,432p' static/js/bulk-generator.js
```

**Expected results:**
- Grep 1: 0 results
- Grep 2: 1 result
- Grep 3: shows `clearBtn.closest(...)` — no remaining `e.target.closest`
  inside the paste-clear block

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] Step 2 verification greps all pass (shown in report)
- [ ] `e.target.classList.contains('bg-source-paste-clear')` does not exist
- [ ] `e.target.closest('.bg-prompt-box')` does not exist inside this block
- [ ] `clearBtn.closest('.bg-prompt-box')` is used instead
- [ ] All other content in the if-block is unchanged
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.
If any score below 8.0 → fix and re-run. No projected scores.

### 1. @frontend-developer
**JS correctness on the `.closest()` fix.**
- Verify `e.target.classList.contains('bg-source-paste-clear')` is gone
- Verify `clearBtn = e.target.closest('.bg-source-paste-clear')` is present
- Verify `clearBox = clearBtn.closest('.bg-prompt-box')` — not `e.target`
- Verify the fix matches the exact same pattern as `deleteBtn` and `resetBtn`
  above it in the same listener
- Show Step 2 verification grep outputs
- Rating requirement: 8+/10

### 2. @javascript-pro
**JavaScript quality review.**
- Verify the `.closest()` delegation chain is correct for all child
  element click scenarios (SVG child, text node, button itself)
- Verify no ES6+ syntax introduced (project uses ES5-compatible patterns)
- Verify the `return` at the end of the if-block is still present
- Rating requirement: 8+/10

### 3. @code-reviewer
**Overall quality and consistency.**
- Verify the three button handlers in this listener (deleteBtn, resetBtn,
  clearBtn) are now structurally identical in pattern
- Verify Step 2 verification outputs are shown in report
- Rating requirement: 8+/10

### 4. @accessibility-expert
**Keyboard and AT interaction.**
- Verify the ✕ button is reachable via keyboard (check existing HTML
  markup for `type="button"` and tab index — do not alter if already correct)
- Verify the fix does not affect focus management
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `.classList.contains('bg-source-paste-clear')` still present
- `e.target.closest('.bg-prompt-box')` still present inside paste-clear block
- Step 2 verification greps not shown in report

---

## 🧪 TESTING

```bash
# Targeted test
python manage.py test prompts.tests.test_bulk_generator --verbosity=1 2>&1 | tail -5

# Django check
python manage.py check
```

**Manual browser check (Mateo must verify after session):**
- Paste image into prompt box → click the SVG icon inside the ✕ button
  (not just the button edge) → Heroku logs show `[PASTE-DELETE] single-box
  fetch failed:` on network error OR silent success on clean delete.
  The key test: clicking the icon area MUST trigger the clear action.

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): paste-clear button uses .closest() — fixes click miss on SVG child
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_144_A_PASTE_DELETE_FIX.md`

**Section 3 MUST include all Step 2 verification grep outputs.**

---

**END OF SPEC**
