# CC_SPEC_153_E_FRONTEND_ERROR_MESSAGES.md
# Fix Frontend Error Message Map — Quota and Billing Limit

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No (JavaScript only)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** 1 str_replace in `static/js/bulk-generator-config.js`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator-config.js` is ✅ SAFE** — normal editing
4. **DO NOT COMMIT** until agent scores confirmed ≥ 8.0
5. **No migration required**

---

## 📋 OVERVIEW

### Frontend Error Message Map — Two Gaps

`G._getReadableErrorReason()` in `bulk-generator-config.js` maps backend
error message strings to user-facing display text. It has two problems:

**Problem 1 — `'Quota exceeded'` message is wrong for BYOK users.**
Current text: `'Failed. API quota exceeded — contact admin.'`
The bulk generator uses BYOK (Bring Your Own Key) — the user IS the admin.
Telling them to "contact admin" is useless and wastes everyone's time.

**Problem 2 — `'Billing limit reached'` is missing from the map entirely.**
The 153-D billing fix added a new backend message that returns
`error_type='quota'` with text `'API billing limit reached. Please top up
your OpenAI account at platform.openai.com/settings/organization/billing.'`
The frontend sanitises this to `'Billing limit reached'` (or passes it
through — confirmed below) but there is no entry in `reasonMap` for it,
so it falls through to the generic fallback:
`'Generation failed — try again or contact support if this repeats.'`
This is actively misleading — there is nothing wrong with the generation
itself, and contacting support is the wrong action.

### Design Principle

Messages must be blunt, honest, and actionable. Users need to know:
- Exactly what happened
- Exactly where to fix it
- No middleman, no vague "contact support"

### Confirmed Current State

```javascript
// Line 110 — wrong message for BYOK users
'Quota exceeded': 'Failed. API quota exceeded \u2014 contact admin.',

// MISSING — no entry for billing limit
// Falls through to generic fallback at line 116
```

---

## 🎯 OBJECTIVES

### Primary Goal

Both quota and billing limit errors show clear, honest, actionable messages
that tell the user exactly what happened and link them directly to the
OpenAI billing page.

### Success Criteria

- ✅ `'Quota exceeded'` message updated — no "contact admin"
- ✅ `'Billing limit reached'` entry added to `reasonMap`
- ✅ Both messages include the OpenAI billing URL
- ✅ All other `reasonMap` entries unchanged
- ✅ Generic fallback unchanged
- ✅ `python manage.py check` returns 0 issues

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full _getReadableErrorReason function (confirm current state)
sed -n '100,120p' static/js/bulk-generator-config.js

# 2. Confirm no other quota/billing references exist in JS files
grep -rn "quota\|billing\|Billing limit\|Quota exceeded" static/js/ | grep -v ".pyc"

# 3. Check file size
wc -l static/js/bulk-generator-config.js

# 4. Confirm backend sanitised message strings match what the map expects
grep -n "Quota exceeded\|Billing limit\|quota\|billing" \
    prompts/views/bulk_generator_views.py | head -10
grep -n "Quota exceeded\|Billing limit\|quota\|billing" \
    prompts/tasks.py | head -10
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Update `reasonMap` in `_getReadableErrorReason`

**File:** `static/js/bulk-generator-config.js`
**str_replace call: 1 of 1**

From Step 0 grep 1, the exact current `reasonMap` block is:

```javascript
        var reasonMap = {
            'Authentication error':     'Invalid API key \u2014 check your key and try again.',
            'Invalid request':          'Invalid request \u2014 check your prompt or settings.',
            'Content policy violation': 'Content policy violation \u2014 revise this prompt.',
            'Upload failed':            'Generation succeeded but file upload failed \u2014 try regenerating.',
            'Quota exceeded':           'Failed. API quota exceeded \u2014 contact admin.',
            'Rate limit reached':       'Rate limit reached \u2014 try again in a few minutes.',
            'Generation failed':        'Generation failed \u2014 try again or contact support if this repeats.',
        };
```

Replace with:

```javascript
        var reasonMap = {
            'Authentication error':     'Invalid API key \u2014 check your key and try again.',
            'Invalid request':          'Invalid request \u2014 check your prompt or settings.',
            'Content policy violation': 'Content policy violation \u2014 revise this prompt.',
            'Upload failed':            'Generation succeeded but file upload failed \u2014 try regenerating.',
            'Quota exceeded':           'Your OpenAI API quota is exhausted \u2014 top up your account at platform.openai.com/settings/organization/billing.',
            'Billing limit reached':    'Your OpenAI billing limit has been reached \u2014 increase it at platform.openai.com/settings/organization/billing.',
            'Rate limit reached':       'Rate limit reached \u2014 try again in a few minutes.',
            'Generation failed':        'Generation failed \u2014 try again or contact support if this repeats.',
        };
```

**Changes made:**
- `'Quota exceeded'` — rewritten. Removed "contact admin" (wrong for BYOK). Now tells user exactly what happened and where to fix it.
- `'Billing limit reached'` — NEW entry added. Maps the new backend message to a clear, actionable message with the billing URL.
- All other entries: **unchanged**. Do not touch them.

⚠️ **Before writing this str_replace**, verify from Step 0 grep 4 that the
backend actually sanitises to `'Billing limit reached'` as the key string.
If the backend passes through the full message text instead, adjust the
key to match exactly what the backend sends. The str_replace anchor must
use the exact text from Step 0 grep 1.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm Quota exceeded entry updated
grep -n "Quota exceeded" static/js/bulk-generator-config.js
# Expected: no "contact admin" in the output

# 2. Confirm Billing limit reached entry added
grep -n "Billing limit reached" static/js/bulk-generator-config.js
# Expected: 1 line with the new message

# 3. Confirm billing URL present in both new entries
grep -n "platform.openai.com/settings/organization/billing" \
    static/js/bulk-generator-config.js
# Expected: 2 lines

# 4. Confirm all other entries unchanged (count should be 8 total now)
grep -n "reasonMap\|Authentication\|Invalid request\|Content policy\|Upload failed\|Rate limit\|Generation failed" \
    static/js/bulk-generator-config.js
# Expected: all original entries still present

# 5. Run collectstatic so Heroku picks up the JS change
python manage.py collectstatic --noinput
```

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and backend key string confirmed
- [ ] Step 2 verification greps all return expected results (shown in report)
- [ ] `'Quota exceeded'` message no longer says "contact admin"
- [ ] `'Billing limit reached'` entry present in `reasonMap`
- [ ] Both new entries include `platform.openai.com/settings/organization/billing`
- [ ] All 6 other entries unchanged
- [ ] Generic fallback unchanged
- [ ] `collectstatic` run — JS change will reach Heroku
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. Both must score 8.0+.

### 1. @frontend-developer
**Verify the map is correct and complete.**
- Confirm `'Quota exceeded'` no longer says "contact admin"
- Confirm `'Billing limit reached'` is present with correct key string
- Confirm the key strings match what the backend actually sends
  (exact-match map — any mismatch means silent fallback to generic message)
- Confirm all other entries unchanged
- Show Step 2 verification grep outputs
- Rating requirement: **8+/10**

### 2. @code-reviewer
**Cross-file consistency check.**
- Verify the two new message strings are honest and actionable per the
  design principle — no vague "contact support", no "contact admin"
- Verify the OpenAI billing URL is correct:
  `platform.openai.com/settings/organization/billing`
- Verify the generic fallback is appropriate for the remaining cases
  where it still applies
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- `'Billing limit reached'` key does not match what the backend sends
- `'Quota exceeded'` still says "contact admin"
- Any other `reasonMap` entry modified
- Step 2 verification greps not shown in report
- `collectstatic` not run

---

## 📊 CC COMPLETION REPORT FORMAT

```markdown
═══════════════════════════════════════════════════════════════
SPEC 153-E: FRONTEND ERROR MESSAGES — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | X/10 | [findings] | Yes/No |
| 1 | @code-reviewer | X/10 | [findings] | Yes/No |
| Average | | X.X/10 | — | Pass ≥8.0 / Fail |

## 📁 FILES MODIFIED

static/js/bulk-generator-config.js — reasonMap updated (2 entries)

## 🧪 TESTING PERFORMED

[collectstatic output + python manage.py check]

## ✅ SUCCESS CRITERIA MET

[Checklist]

## 🔄 DATA MIGRATION STATUS

N/A

## 🔁 SELF-IDENTIFIED FIXES APPLIED

[If none: "None identified."]

## 🔁 DEFERRED — OUT OF SCOPE

[If none: "None identified."]

## 📝 NOTES

[Step 2 verification grep outputs must be shown here]
[Confirm exact backend key string match]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): clear actionable error messages for quota and billing limit

- 'Quota exceeded': removed misleading "contact admin" (BYOK users are
  the admin); now directs user to OpenAI billing page
- 'Billing limit reached': new entry added; was falling through to generic
  "Generation failed" fallback which gave no actionable guidance
```

---

## ⛔ CRITICAL REMINDERS (Repeated)

- **Verify the backend key string FIRST** — the map uses exact-match;
  wrong key = silent fallback to generic message = bug not fixed
- **Run `collectstatic`** — without this the JS change never reaches Heroku
- **Do not touch any other `reasonMap` entries**

---

**END OF SPEC**
