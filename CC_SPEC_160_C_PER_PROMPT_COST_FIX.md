# CC_SPEC_160_C_PER_PROMPT_COST_FIX.md
# Per-Prompt Cost — Fix Quality Change Not Updating Cost in Boxes

**Spec Version:** 1.0
**Session:** 160
**Modifies UI/Templates:** Yes (JS only)
**Migration Required:** No
**Agents Required:** 6 minimum
**Estimated Scope:** 2–3 str_replace in `bulk-generator.js` (🟠 High Risk)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **`bulk-generator.js` was modified by 160-B** — re-read FULL current file
4. **This is investigation-first** — Step 0 must identify the exact failure
   point before any code is written

---

## 📋 CONFIRMED PROBLEM (verified April 2026)

Per-prompt box quality labels correctly show 1K/2K/4K for NB2 (from 159-B).
But when the user changes the quality selection on a per-prompt box, the cost
display inside that box does not update. The sticky bar total also does not
reflect the per-box quality change.

This persisted through Session 158-B and 159-B fixes. The root cause has not
been fully resolved despite two attempts.

---

## 📁 STEP 0 — MANDATORY INVESTIGATION

```bash
# 1. Re-read FULL current bulk-generator.js (post-160-B state)
cat static/js/bulk-generator.js

# 2. Find ALL change event listeners on quality selectors
grep -n "quality.*change\|change.*quality\|addEventListener.*change" \
    static/js/bulk-generator.js | head -20

# 3. Find updateCostEstimate() — full implementation
grep -n -A 40 "function updateCostEstimate\|updateCostEstimate = function" \
    static/js/bulk-generator.js | head -50

# 4. Find per-prompt cost display element — what gets updated?
grep -n "costDisplay\|cost.*text\|\.cost\b\|prompt.*cost\|box.*cost" \
    static/js/bulk-generator.js | head -20

# 5. Find NB2_TIER_COSTS and how per-box quality is read
grep -n "NB2_TIER_COSTS\|_nbTiers\|bg-override-quality\|per.*box.*quality" \
    static/js/bulk-generator.js | head -20

# 6. Find where new prompt boxes get their event listeners attached
grep -n "addPromptBox\|createPromptBox\|addEventListener\|\.on(" \
    static/js/bulk-generator.js | grep -i "quality\|change" | head -15

# 7. Check bulk-generator-autosave.js for any quality change handling
grep -n "quality.*change\|change.*quality" \
    static/js/bulk-generator-autosave.js | head -10
```

**Document the exact failure point from Step 0 in Section 4 of the report
before writing any code.**

---

## 📁 STEP 1 — Fix based on investigation findings

The fix depends on what Step 0 reveals. Three likely root causes:

**Root Cause A — Change event not firing on per-box quality select:**
The event listener uses direct binding on elements that existed at page load.
Dynamically added boxes don't get the listener. Fix: use event delegation
on a stable parent container.

```javascript
// Event delegation approach — attach once to stable parent:
document.querySelector('#prompt-boxes-container').addEventListener('change',
    function(e) {
        if (e.target.matches('.bg-override-quality')) {
            updateCostEstimate();
        }
    }
);
```

**Root Cause B — `updateCostEstimate()` reads master quality, not per-box:**
The cost calculation uses `document.getElementById('settingQuality').value`
for all boxes. Fix: pass the triggering element's value, or read per-box
quality inside the cost loop.

**Root Cause C — Cost display element not found inside the prompt box:**
The DOM query for the cost element uses a selector that doesn't match the
actual element structure. Fix: update the selector to match the actual DOM.

**Apply whichever fix matches the actual root cause from Step 0.**

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm change event wired on per-box quality (delegation or direct)
grep -n "bg-override-quality\|quality.*change" static/js/bulk-generator.js | head -10

# 2. Confirm NB2_TIER_COSTS used for per-box cost (not master quality)
grep -n "NB2_TIER_COSTS\|_nbTiers" static/js/bulk-generator.js | head -5

# 3. Django check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Root cause identified from Step 0 — documented in Section 4 ✓
- [ ] Per-box quality change triggers cost update ✓
- [ ] NB2 tier costs used for per-box cost calculation ✓
- [ ] Newly added boxes also get quality change coverage ✓
- [ ] Master sticky bar total also updates ✓
- [ ] Non-NB2 models not regressed ✓

---

## 🤖 AGENT REQUIREMENTS

**Minimum 6 agents. Average 8.5+. All must score 8.0+.**

### 1. @frontend-developer
- Does event delegation correctly handle both existing and new boxes?
- Rating: 8.0+/10

### 2. @ui-visual-validator
- NB2 per-box: change quality → cost updates immediately ✅
- Sticky bar total reflects per-box quality changes ✅
- Rating: 8.0+/10

### 3. @code-reviewer
- Is the delegation selector specific enough to not fire on unrelated changes?
- Rating: 8.0+/10

### 4. @accessibility-expert
- Cost update announced to AT when quality changes?
- Rating: 8.0+/10

### 5. @tdd-orchestrator
- Tests for quality-driven cost update?
- Rating: 8.0+/10

### 6. @architect-review
- Is event delegation the right long-term pattern here?
- Rating: 8.0+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Root cause not identified from Step 0
- Cost still doesn't update on per-box quality change
- New boxes added after page load don't get quality change coverage

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test --verbosity=0
```

**Manual:**
1. Select NB2 → add 3 boxes → set 1K/2K/4K → each shows **correct cost** ✅
2. Change box 2 from 2K → 4K → **box 2 cost updates to $0.151** ✅
3. Sticky bar total **updates to reflect all 3 boxes** ✅

---

## 💾 COMMIT MESSAGE

```
fix(ui): per-prompt cost updates on quality change

Root cause: [from Step 0]
Fix: [describe fix applied]

Agents: 6 agents, avg X/10, all passed 8.0+ threshold
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_C.md`

Section 4 must document the exact root cause found in Step 0.

---

**END OF SPEC**
