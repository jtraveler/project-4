# CC_SPEC_160_D_FULL_DRAFT_AUTOSAVE.md
# Full Draft Autosave — All Settings + Per-Prompt Boxes, Persists After Generation

**Spec Version:** 1.0
**Session:** 160
**Modifies UI/Templates:** Yes
**Migration Required:** No
**Agents Required:** 6 minimum
**Estimated Scope:** Major expansion of `bulk-generator-autosave.js` (🔴 Critical)
+ 2–3 str_replace in `bulk-generator.js` (🟠 High Risk)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **Investigation-first** — read `bulk-generator-autosave.js` IN FULL before
   writing any code. The existing autosave system must be understood before
   extending it.
4. **`bulk-generator.js` was modified by 160-B and 160-C** — re-read full
   current file before any str_replace
5. **`bulk-generator-autosave.js` is 376 lines** — 🟡 Caution tier.
   Re-read before each str_replace.
6. **Do NOT persist uploaded reference image files** — localStorage cannot
   store binary files. Persist the reference image URL if already uploaded
   to B2 (the `data-url` or similar attribute on the upload zone), not the
   raw file object.
7. **Draft persists after generation** — do NOT clear on job submission.
   Cleared only when user explicitly resets.

---

## 📋 CONTEXT

The current autosave (Session 158-C) saves: model, quality, aspect ratio.
It restores on DOMContentLoaded and pageshow (bfcache).

**What needs to be added:**
- All master header settings: Images per Prompt, toggle switches (any visible
  toggles in the header area), character description field
- Per-prompt box settings: prompt text, AI Direction toggle state, AI Direction
  text content, Dimensions dropdown, Images dropdown, Prompt From Image dropdown
- Draft persists after generation (currently not cleared, confirmed correct)
- Explicit "Clear draft" resets all saved state

**Architecture note:** This is the localStorage-based draft system. A future
feature (Feature 4 in CLAUDE.md) will add server-side named drafts for logged-in
users. The localStorage system is the anonymous/session fallback and the
foundation for the named draft feature. When designing the save/restore structure,
use a JSON schema that can later be serialised and sent to the server as
`settings_json` + `prompts_json` for the `PromptDraft` model.

---

## 📁 STEP 0 — MANDATORY INVESTIGATION

```bash
# 1. Read FULL current bulk-generator-autosave.js
cat static/js/bulk-generator-autosave.js

# 2. Read FULL current bulk-generator.js (post-160-C state)
cat static/js/bulk-generator.js

# 3. Find ALL current PF_STORAGE_KEYS
grep -n "PF_STORAGE_KEYS\|pf_bg_\|saveSettings\|restoreSettings" \
    static/js/bulk-generator.js static/js/bulk-generator-autosave.js | head -30

# 4. Find all master header settings elements
grep -n "imagesPerPrompt\|characterDescription\|settingToggle\|toggle.*setting" \
    prompts/templates/prompts/bulk_generator.html | head -20

# 5. Find per-prompt box settings elements
grep -n "bg-override\|ai-direction\|aiDirection\|override.*quality\|override.*dimensions" \
    prompts/templates/prompts/bulk_generator.html static/js/bulk-generator.js | head -30

# 6. Find the AI Direction toggle and text field IDs/classes
grep -n "ai.direction\|aiDirection\|add.*ai\|direction.*toggle" \
    prompts/templates/prompts/bulk_generator.html | head -15

# 7. Find how prompt boxes are identified (do they have stable IDs or indices?)
grep -n "prompt.*box.*id\|id.*prompt.*box\|data-box\|data-prompt" \
    prompts/templates/prompts/bulk_generator.html | head -10

# 8. Find any existing "clear" or "reset" functionality
grep -n "clearDraft\|resetDraft\|clear.*draft\|reset.*all\|clear.*all" \
    static/js/bulk-generator*.js | head -10

# 9. Find where generation is submitted (to confirm draft NOT cleared there)
grep -n "submitJob\|startGeneration\|generate.*all\|form.*submit" \
    static/js/bulk-generator*.js | head -10
```

**Read and understand ALL of the above before writing any code.**

---

## 📁 STEP 1 — Design the draft JSON schema

Before writing save/restore code, define the schema. This must be compatible
with the future `PromptDraft` server-side model.

```javascript
// Draft schema — stored as single JSON blob under 'pf_bg_draft'
var DRAFT_KEY = 'pf_bg_draft';

// Schema:
{
    "version": 1,
    "saved_at": "ISO timestamp",
    "settings": {
        "model": "google/nano-banana-2",
        "quality": "high",
        "aspect_ratio": "1:1",
        "images_per_prompt": 1,
        "character_description": "...",
        // any additional master toggle states
    },
    "prompts": [
        {
            "index": 0,
            "text": "prompt text here",
            "ai_direction_enabled": false,
            "ai_direction_text": "",
            "dimensions": "use_master",
            "images": "use_master",
            "prompt_from_image": "no",
            "reference_image_url": ""  // B2 URL if uploaded, not file object
        }
        // ... more prompts
    ]
}
```

**Adjust field names** to match actual element names found in Step 0.
Store as a single JSON blob (one `localStorage.setItem` call) rather than
separate keys per field. This is more efficient and easier to migrate to
server-side later.

---

## 📁 STEP 2 — Implement saveDraft()

Extend `bulk-generator-autosave.js` with a `saveDraft()` function that:

1. Reads all master settings from the DOM
2. Reads all per-prompt box settings from each box
3. Builds the JSON schema object
4. Saves to `localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))`
5. Wrapped in try/catch for private browsing safety

Call `saveDraft()` on:
- Every settings change (model, quality, aspect ratio, Images per Prompt, toggles)
- Every prompt box text change (debounced 500ms — don't save on every keystroke)
- Every per-box dropdown change
- Every AI Direction toggle/text change

**Debounce prompt text saves** to avoid excessive localStorage writes:
```javascript
var _draftSaveTimer = null;
function debouncedSaveDraft() {
    clearTimeout(_draftSaveTimer);
    _draftSaveTimer = setTimeout(saveDraft, 500);
}
```

---

## 📁 STEP 3 — Implement restoreDraft()

Replace/extend the existing `restoreSettings()` with a `restoreDraft()`
function that:

1. Reads the JSON blob from localStorage
2. Validates the version field
3. Restores master settings (model → triggers handleModelChange → quality →
   aspect ratio → other settings)
4. Adds prompt boxes to match the saved count
5. Fills each box with saved text, dropdown values, AI direction state
6. Calls `updateCostEstimate()` after restoration
7. Handles gracefully if saved data is missing or malformed

**Critical sequence:**
```
restoreDraft() →
  1. Set model value
  2. Call handleModelChange() (rebuilds dependent UI)
  3. Set quality value (after handleModelChange)
  4. Set aspect ratio (after handleModelChange rebuilds buttons)
  5. Set other master settings
  6. Add extra prompt boxes if needed
  7. Fill each box's text + dropdowns + AI direction
  8. updateCostEstimate()
```

---

## 📁 STEP 4 — Add explicit "Clear draft" / "New session" action

Find the existing clear/reset button or add one. When clicked:
```javascript
function clearDraft() {
    try {
        localStorage.removeItem(DRAFT_KEY);
        // Also remove old individual keys for backwards compatibility
        localStorage.removeItem('pf_bg_model');
        localStorage.removeItem('pf_bg_quality');
        localStorage.removeItem('pf_bg_aspect_ratio');
    } catch (e) {}
    // Reset UI to defaults
    location.reload(); // or explicit reset of all fields
}
```

---

## 📁 STEP 5 — MANDATORY VERIFICATION

```bash
# 1. Confirm single DRAFT_KEY used (not individual keys)
grep -n "DRAFT_KEY\|pf_bg_draft" static/js/bulk-generator-autosave.js | head -5

# 2. Confirm old individual keys still cleaned up on clear
grep -n "pf_bg_model\|pf_bg_quality\|pf_bg_aspect" \
    static/js/bulk-generator-autosave.js | head -5

# 3. Confirm draft NOT cleared on generation submit
grep -n "clearDraft\|removeItem.*draft" \
    static/js/bulk-generator*.js | grep -i "submit\|generat" | head -5
# Expected: 0 results (draft not cleared on submit)

# 4. Confirm saveDraft called on text change (debounced)
grep -n "debouncedSaveDraft\|saveDraft\|input.*draft\|change.*draft" \
    static/js/bulk-generator*.js | head -10

# 5. Confirm no API keys or sensitive data in draft
grep -n "api_key\|byok\|token\|password" \
    static/js/bulk-generator-autosave.js | head -5
# Expected: 0 results

# 6. Django check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 full investigation completed ✓
- [ ] Single JSON blob schema (not individual keys) ✓
- [ ] Schema compatible with future `PromptDraft` server model ✓
- [ ] All master settings saved and restored ✓
- [ ] All per-prompt box settings saved and restored ✓
- [ ] Prompt text debounced (500ms) ✓
- [ ] Draft NOT cleared on generation submit ✓
- [ ] Explicit clearDraft() function removes localStorage entries ✓
- [ ] try/catch on all localStorage operations ✓
- [ ] No API keys or binary files persisted ✓
- [ ] Restoration sequence correct (model → handleModelChange → quality → boxes) ✓

---

## 🤖 AGENT REQUIREMENTS

**Minimum 6 agents. Average 8.5+. All must score 8.0+.**

### 1. @frontend-developer
- Is the restoration sequence correct for all edge cases (empty draft, partial
  draft, new boxes added after save)?
- Rating: 8.0+/10

### 2. @ui-visual-validator
- All settings restored correctly after hard refresh ✅
- Per-prompt box text and AI Direction restored ✅
- Rating: 8.0+/10

### 3. @code-reviewer
- Is the JSON schema compatible with the future `PromptDraft` Django model?
- Is the debounce implementation correct?
- Rating: 8.0+/10

### 4. @backend-security-coder
- No sensitive data in localStorage ✅
- localStorage value used in DOM safely (no XSS via restore) ✓
- Rating: 8.0+/10

### 5. @tdd-orchestrator
- Any Django tests affected?
- Rating: 8.0+/10

### 6. @architect-review
- Is the schema designed to be easily serialised to `settings_json` +
  `prompts_json` for the future server-side `PromptDraft` model?
- Rating: 8.0+/10

### ⛔ MINIMUM REJECTION CRITERIA
- API keys, BYOK keys, or file objects persisted to localStorage
- Draft cleared on generation submit
- No try/catch on localStorage operations
- Restoration sequence incorrect (e.g. aspect ratio restored before
  handleModelChange rebuilds the button group)

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test --verbosity=0
```

**Manual checks:**
1. Set all master settings + add 3 boxes with prompts + AI direction → hard
   refresh → **everything restored exactly** ✅
2. Generate → hit back → **all settings and prompts still there** ✅
3. DevTools → Application → Local Storage → one `pf_bg_draft` key with JSON ✅
4. Click "Clear draft" → settings reset to defaults ✅
5. Open incognito → loads with defaults, no crash ✅

---

## 💾 COMMIT MESSAGE

```
feat(ui): full draft autosave — all settings + per-prompt boxes

- Single JSON schema under pf_bg_draft key
- Saves all master settings: model, quality, aspect, images/prompt, toggles
- Saves all per-prompt: text (debounced 500ms), AI direction, dropdowns
- Draft persists after generation (cleared only on explicit reset)
- Schema compatible with future PromptDraft server-side model
- try/catch for private browsing; no sensitive data persisted

Agents: 6 agents, avg X/10, all passed 8.0+ threshold
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_D.md`

Section 3 must include the full JSON schema used. Section 4 must document
the exact restoration sequence and any edge cases encountered.

---

**END OF SPEC**
