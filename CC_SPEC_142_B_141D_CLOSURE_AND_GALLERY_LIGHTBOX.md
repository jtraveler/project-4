# CC_SPEC_142_B_141D_CLOSURE_AND_GALLERY_LIGHTBOX.md
# Close 141-D Protocol Violation + Fix gallery.js Lightbox (Results Page Only)

**Spec Version:** 1.0 (written after file review)
**Date:** March 2026
**Session:** 142
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 6 minimum
**Estimated Scope:** ~30 lines in `bulk-generator-gallery.js`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator-gallery.js` is ✅ Safe** — normal editing
4. **`openai_provider.py`** — review only, NO code changes expected

---

## 📋 CONFIRMED CURRENT STATE (verified before spec was written)

**`openai_provider.py`** is correctly implemented:
- `images.edit()` used when reference image provided ✅
- `images.generate()` fallback when not provided ✅
- Non-fatal download failure ✅
- 20MB size limit ✅
- Mock mode unchanged ✅
- No module-level imports ✅

This spec runs @django-pro and @python-pro to formally confirm the
fix is correct and close the 141-D protocol violation.

**`prompt_detail.html`** `createPdLightbox` is already correct:
- `overlay.appendChild(closeBtn)` ✅ (line 957)
- `inner.appendChild(openLink)` ✅ (line 956)
- Two-element focus trap ✅
No changes needed here.

**`lightbox.css`** `.lightbox-close` already has `position: absolute;
top: 16px; right: 16px; z-index: 10000` ✅
No CSS changes needed.

**`bulk-generator-gallery.js`** `createLightbox` is STILL using the
old structure:
- Close button inside `inner` (not on `overlay`) ❌
- Caption `<p>` element still present ❌
- `aria-describedby="lightboxCaption"` on overlay ❌
- Caption text still assigned in `openLightbox` ❌

**Only `bulk-generator-gallery.js` needs code changes.**

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read current createLightbox in full (confirm exact current state)
sed -n '370,425p' static/js/bulk-generator-gallery.js

# 2. Read openLightbox caption assignment
sed -n '426,450p' static/js/bulk-generator-gallery.js

# 3. Read openai_provider.py generate() method in full
sed -n '62,165p' prompts/services/image_providers/openai_provider.py

# 4. Run existing provider tests
python manage.py test prompts.tests.test_bulk_generator --verbosity=1 \
    2>&1 | tail -10

# 5. Confirm prompt_detail.html lightbox is already correct
grep -n "overlay\.appendChild(closeBtn)\|inner\.appendChild(closeBtn)" \
    prompts/templates/prompts/prompt_detail.html

# 6. Confirm lightbox.css close button positioning
grep -n "lightbox-close\|position.*absolute\|top.*16px" \
    static/css/components/lightbox.css | head -8
```

**Do not proceed until all greps are complete and read carefully.**

Step 0 greps 5 and 6 are verification-only — they confirm no changes
are needed in those files. Document findings in Section 3.

---

## 📁 PART A — Close 141-D (review only, no code changes)

From Step 0 grep 3, read the current `generate()` method.
From Step 0 grep 4, confirm tests pass.

**Document in Section 3:**
- Whether `ref_file = None` is correctly initialised
- Whether `images.edit(image=ref_file, ...)` is used when ref_file exists
- Whether `images.generate(...)` is the fallback
- Whether download failure is non-fatal
- Whether 20MB limit is present
- Whether mock mode is unchanged
- Test output from Step 0 grep 4

**Explicitly state in Section 3:** "141-D protocol violation is closed.
Both agents confirm openai_provider.py is correctly implemented."

---

## 📁 PART B — Fix `createLightbox` in `bulk-generator-gallery.js`

**File:** `static/js/bulk-generator-gallery.js`

From Step 0 grep 1, read the exact current function. Replace it with
the correct structure where the close button is on the overlay directly:

**Find the full `createLightbox` function (exact text from Step 0 grep 1)
and replace it entirely with:**

```javascript
    G.createLightbox = function () {
        var overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.id = 'imageLightbox';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', 'Image preview');
        // No aria-describedby — caption removed

        // Close button on overlay directly (NOT in inner) — this ensures
        // it is always position:absolute top-right regardless of image size
        var closeBtn = document.createElement('button');
        closeBtn.className = 'lightbox-close';
        closeBtn.setAttribute('aria-label', 'Close preview');
        closeBtn.setAttribute('type', 'button');
        closeBtn.innerHTML = '&times;'; /* Safe: hardcoded character */

        var inner = document.createElement('div');
        inner.className = 'lightbox-inner';

        var img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'lightboxImage';
        img.alt = '';
        // No caption — removed

        inner.appendChild(img);
        overlay.appendChild(closeBtn);   // Close on overlay, NOT inner
        overlay.appendChild(inner);
        document.body.appendChild(overlay);

        closeBtn.addEventListener('click', G.closeLightbox);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) G.closeLightbox();
        });
        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') { G.closeLightbox(); return; }
            // Single focusable element — keep Tab on close button
            if (e.key === 'Tab') { e.preventDefault(); closeBtn.focus(); }
        });

        G.lightboxEl = overlay;
        return overlay;
    };
```

**Also update `openLightbox`** (Step 0 grep 2) — remove caption lines:

Find and delete:
```javascript
var caption = document.getElementById('lightboxCaption');
```
and:
```javascript
caption.textContent = promptText ? '\u201C' + promptText + '\u201D' : '';
```

These two lines must be completely removed.

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Verify close button is on overlay (NOT in inner)
grep -n "overlay\.appendChild(closeBtn)\|inner\.appendChild(closeBtn)" \
    static/js/bulk-generator-gallery.js

# 2. Verify caption completely gone
grep -n "caption\|lightboxCaption\|aria-describedby" \
    static/js/bulk-generator-gallery.js

# 3. Verify tests still pass
python manage.py test prompts.tests.test_bulk_generator --verbosity=1 \
    2>&1 | tail -5
```

**Expected results:**
- Grep 1: shows `overlay.appendChild(closeBtn)` — NOT `inner.appendChild`
- Grep 2: returns 0 results (caption completely gone)
- Grep 3: 0 failures

**If Grep 1 shows `inner.appendChild` the fix was not applied. Do not
run agents. Fix and re-verify.**

Show all outputs in Section 3 of the report.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] Step 1 verification greps all pass (shown in report)
- [ ] `createLightbox`: close button on `overlay`, NOT `inner`
- [ ] `createLightbox`: NO caption element created
- [ ] `createLightbox`: NO `aria-describedby` on overlay
- [ ] `openLightbox`: caption variable and assignment removed
- [ ] `prompt_detail.html` lightbox confirmed already correct (no change)
- [ ] `lightbox.css` close button positioning confirmed (no change)
- [ ] openai_provider.py: `images.edit()` used when ref image provided
- [ ] openai_provider.py: tests pass
- [ ] **WCAG 1.4.11:** `.lightbox-close` white circle on dark overlay —
      verify contrast is acceptable (dark background provides contrast)
- [ ] **WCAG 2.4.3:** Focus moves to close button on lightbox open
- [ ] **WCAG 2.1.1:** Escape closes lightbox, Tab stays within
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 6 agents. All must score 8.0+.
If any score below 8.0 — fix and run a confirmed second round.

### PART A — 141-D Closure (review only)

#### 1. @django-pro
**Closes 141-D protocol violation — confirms openai_provider.py is correct.**
- Verify `images.edit()` used when `ref_file` is not None
- Verify `images.generate()` used as fallback when `ref_file` is None
- Verify download failure is non-fatal — generation continues
- Verify no module-level imports were added
- Verify mock mode path completely unchanged
- Show test output from Step 0 grep 4
- **Must state explicitly:** "141-D protocol violation is now closed"
- Rating requirement: **8.0+ required**

#### 2. @python-pro
**Python quality review on the provider — sonnet model.**
- Verify `BytesIO` + `.name` attribute pattern is correct for OpenAI SDK
- Verify `requests.get` with `timeout=20` and `raise_for_status()` follows
  Python best practices
- Verify `len(ref_bytes) > 20 * 1024 * 1024` is the correct size check
- Verify the exception handling is correctly scoped and specific
- Rating requirement: 8+/10

### PART B — Lightbox Fix

#### 3. @frontend-developer
**Structural correctness of the gallery.js lightbox fix.**
- Verify `overlay.appendChild(closeBtn)` — not `inner.appendChild`
- Verify NO caption element anywhere in `createLightbox`
- Verify NO `aria-describedby` on overlay
- Verify caption variable and text assignment both removed from `openLightbox`
- Verify focus trap: Tab keeps focus on close button (single element)
- Show all Step 1 verification grep outputs
- Rating requirement: 8+/10

#### 4. @accessibility-expert
**Full WCAG audit — opus model.**
- **WCAG 1.4.11:** Verify `.lightbox-close` non-text contrast against
  dark overlay. The button has `background: rgba(0,0,0,0.5)` with
  `border: 2px solid rgba(255,255,255,0.6)` — verify the white border
  meets 3:1 against the dark overlay. Calculate explicitly.
- **WCAG 2.4.3:** Verify focus moves to close button when lightbox opens
  (`closeBtn.focus()` called in `openLightbox`)
- **WCAG 2.1.1:** Verify keyboard operation — Escape closes, Tab trapped
- **WCAG 4.1.2:** Verify `role="dialog"`, `aria-modal="true"`,
  `aria-label="Image preview"` all present on overlay
- Verify removal of `aria-describedby` was correct (caption was empty
  noise for AT users — removing it is the right call)
- Rating requirement: 8+/10

#### 5. @frontend-security-coder
**Client-side security on the lightbox — opus model.**
- Verify `closeBtn.innerHTML = '&times;'` is safe (hardcoded, not
  user-controlled input)
- Verify image URLs in `img.src` come from `data-image-url` attributes
  set at server render time — not from user input
- Verify no user-controlled content is injected as HTML anywhere in
  `createLightbox` or `openLightbox`
- Rating requirement: 8+/10

#### 6. @code-reviewer
**Cross-file consistency — opus model.**
- Verify `bulk-generator-gallery.js` and `prompt_detail.html` lightboxes
  are now structurally consistent (both have close button on overlay)
- Verify `lightbox.css` `position: absolute` on close button matches
  the JS structure (button appended to overlay, not inner)
- Verify all Step 1 verification outputs are shown in report
- Verify Section 3 explicitly states "141-D protocol violation is closed"
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Caption element still exists in `createLightbox`
- Close button still appended to `inner` (not `overlay`)
- 141-D closure not explicitly stated in Section 3
- Verification greps not shown in Section 3

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test prompts.tests.test_bulk_generator
```

**Manual browser checks (Mateo must verify):**
1. Open lightbox on results page → verify × is top-right of the dark
   overlay, NOT overlaid on the image or below it
2. Resize to mobile → verify × stays top-right
3. Generate with reference image → verify `[REF-IMAGE] Attached` in logs

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(lightbox): gallery.js close button on overlay (re-applied), caption removed; 141-D closed
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_142_B_141D_CLOSURE_AND_GALLERY_LIGHTBOX.md`

**Section 3 MUST include:**
- All Step 1 verification grep outputs
- Test output from `test_bulk_generator`
- Explicit statement: **"141-D protocol violation is now closed"**
- WCAG 1.4.11 contrast calculation for close button

---

**END OF SPEC**
