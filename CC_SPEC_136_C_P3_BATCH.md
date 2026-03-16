# CC_SPEC_136_C_P3_BATCH.md
# P3 Batch — prefers-reduced-motion, IMAGE_EXT_RE anchor, Accessibility Review

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 136
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~10 lines across 2 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`bulk-generator.js` is 🟠 High Risk** — max 2 str_replace calls
5. **`bulk-generator-utils.js` is ✅ Safe** — normal editing

---

## 📋 OVERVIEW

Three small P3 items from the Deferred P3 Items table in `CLAUDE.md`:

1. **`prefers-reduced-motion` on scroll** — the error link scroll animation
   uses `behavior: 'smooth'` unconditionally. Users who prefer reduced motion
   should get `behavior: 'auto'` (instant scroll).

2. **`IMAGE_EXT_RE` unanchored** — the regex `/\.(jpg|jpeg|png|webp|gif|avif)/i`
   in `bulk-generator-utils.js` is unanchored, meaning it technically matches
   `.jpg` anywhere in a path segment (e.g. `/photo.jpgfoo`). Add a word
   boundary or lookahead to prevent false positives.

3. **`@accessibility` review on clickable error links** — no code change needed,
   just a dedicated agent review of the current implementation to confirm WCAG
   compliance of the `showValidationErrors` clickable links. Results documented
   in the report.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find the scroll animation and scrollBy call
grep -n "scrollIntoView\|scrollBy\|prefers-reduced" static/js/bulk-generator.js

# 2. Find IMAGE_EXT_RE in bulk-generator-utils.js
grep -n "IMAGE_EXT_RE\|_hasImageExtension" static/js/bulk-generator-utils.js

# 3. Find showValidationErrors for accessibility review context
sed -n '1185,1250p' static/js/bulk-generator.js
```

---

## 📁 STEP 1 — `prefers-reduced-motion` on scroll

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 1**

From Step 0 grep, find the scroll block with `setTimeout(350)` + `scrollBy`.

**Current:**
```javascript
                        box.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        // Nudge up 120px to clear the sticky bottom bar
                        setTimeout(function() {
                            window.scrollBy({ top: -120, behavior: 'smooth' });
                        }, 350);
```

**Replace with:**
```javascript
                        var reducedMotion = window.matchMedia(
                            '(prefers-reduced-motion: reduce)'
                        ).matches;
                        var scrollBehavior = reducedMotion ? 'auto' : 'smooth';
                        box.scrollIntoView({ behavior: scrollBehavior, block: 'center' });
                        // Nudge up 120px to clear the sticky bottom bar
                        setTimeout(function() {
                            window.scrollBy({ top: -120, behavior: scrollBehavior });
                        }, reducedMotion ? 0 : 350);
```

When reduced motion is preferred, `setTimeout(0)` fires immediately (no delay
needed since there's no animation to wait for).

---

## 📁 STEP 2 — Fix `IMAGE_EXT_RE` in `bulk-generator-utils.js`

**File:** `static/js/bulk-generator-utils.js`

From Step 0 grep, find `IMAGE_EXT_RE`.

**Current:**
```javascript
    var IMAGE_EXT_RE = /\.(jpg|jpeg|png|webp|gif|avif)/i;
```

**Replace with:**
```javascript
    var IMAGE_EXT_RE = /\.(jpg|jpeg|png|webp|gif|avif)(?:[?#&]|$)/i;
```

The lookahead `(?:[?#&]|$)` ensures the extension is followed by a query
string separator, fragment, or end of string — not by other path characters.
This prevents `/photo.jpgfoo` from matching while still accepting:
- `/photo.jpg` ✅
- `/photo.jpg?w=800` ✅
- `/photo.jpg#anchor` ✅
- `%2Fphoto.png&w=1920` ✅ (in decoded query string)

⚠️ Verify the fix doesn't break the existing `_hasImageExtension` tests by
mentally tracing through the Next.js URL from Session 135:
`decodeURIComponent('?url=%2Fphoto.png&w=1920')` → `?url=/photo.png&w=1920`
The regex should match `.png&` → ✅

---

## 📁 STEP 3 — `@accessibility` review (no code change)

This step produces findings only — no code changes required unless the agent
flags a genuine failure.

The @accessibility agent must review the current `showValidationErrors`
implementation in `bulk-generator.js`, specifically:
- The clickable `<a>` link elements added for prompt numbers
- Their accessible name in context
- Whether screen readers will announce them correctly alongside the error text
- `role="alert"` on the banner container

If the agent identifies a genuine WCAG failure (not just a recommendation),
apply the minimal fix. Document findings in the report regardless.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `reducedMotion` check uses `window.matchMedia` (not hardcoded)
- [ ] `setTimeout(0)` used when reduced motion is preferred
- [ ] `IMAGE_EXT_RE` lookahead confirmed not to break Next.js URL
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify `prefers-reduced-motion` check is correct
- Verify `setTimeout(0)` used for reduced motion path
- Verify `IMAGE_EXT_RE` lookahead correctly handles all test cases
- Verify Next.js URL still passes after regex change
- Rating requirement: 8+/10

### 2. @accessibility
- Review `showValidationErrors` clickable error links:
  - Do links have a meaningful accessible name?
  - Is the `role="alert"` banner announced correctly?
  - Are links keyboard reachable and operable?
  - WCAG 2.1 success criteria: 1.4.1, 2.4.4, 4.1.2
- If genuine WCAG failure found: apply minimal fix and document
- If only recommendations: document without code change
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `prefers-reduced-motion` not checked (always uses smooth)
- `IMAGE_EXT_RE` change breaks the Next.js URL case

---

## 🧪 TESTING

```bash
python manage.py check
```

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(a11y): prefers-reduced-motion scroll, IMAGE_EXT_RE anchor, accessibility review
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_136_C_P3_BATCH.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

Include: @accessibility agent findings verbatim, even if no code change made.

---

**END OF SPEC**
