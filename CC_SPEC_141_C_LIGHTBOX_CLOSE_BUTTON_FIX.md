# CC_SPEC_141_C_LIGHTBOX_CLOSE_BUTTON_FIX.md
# Lightbox — Fix Close Button Position + Extract Shared CSS

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 141
**Modifies UI/Templates:** YES (prompt_detail.html)
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** ~60 lines across 4 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`prompt_detail.html` is 🟡 Caution** — str_replace only
4. **`bulk-generator-job.css` is 🟡 Caution** — max 3 str_replace calls
5. **`bulk-generator-gallery.js` is ✅ Safe** — normal editing

---

## ⚠️ IMPORTANT: READ CURRENT STATE BEFORE ANY CHANGES

Session 139 Spec B and Session 140 Spec C both reported making changes to
`bulk-generator-gallery.js` but the current file shows the old structure
(close button directly in `inner`, caption still present). CC MUST read the
current state of each file via Step 0 greps before writing any changes.

---

## 📋 OVERVIEW

**Problem confirmed in browser testing:** The close × button on the prompt
detail lightbox appears BELOW the image on smaller screens because it shares
a div (`.lightbox-right-panel`) with the "Open in new tab" link, and on mobile
the entire right panel stacks below the image.

**Correct desktop layout:**
- Image: horizontally centered, fills maximum height
- Close × button: absolutely positioned to the top-right of the overlay,
  completely independent of the image — always visible at top-right
- "Open in new tab" link: below the image, horizontally centered

**Correct mobile layout (≤768px):**
- Close × button: absolutely positioned top-right of overlay (same as desktop)
- Image: below, centered
- "Open in new tab" link: below the image

**Key insight:** The × button should NEVER be inside a flow element. It must
always be `position: absolute` at the top-right of the overlay, so it floats
above everything regardless of image size or screen size.

**Additionally:** Session 139 Spec B reported removing the caption `<p>` from
`createLightbox` in `bulk-generator-gallery.js` but the caption is still
present in the current file. This must be cleaned up.

**Also:** Shared lightbox CSS is duplicated between `bulk-generator-job.css`
and `prompt-detail.css`. Extract to `static/css/components/lightbox.css`.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the FULL current createLightbox function (confirm actual current state)
sed -n '370,430p' static/js/bulk-generator-gallery.js

# 2. Read the FULL current createPdLightbox in prompt_detail.html
grep -n "createPdLightbox\|lightbox-right-panel\|lightbox-close\|openLink\|rightPanel" \
    prompts/templates/prompts/prompt_detail.html | head -20

# 3. Read the lightbox CSS in bulk-generator-job.css
sed -n '896,965p' static/css/pages/bulk-generator-job.css

# 4. Read the lightbox CSS in prompt-detail.css
grep -n "lightbox" static/css/pages/prompt-detail.css | head -20

# 5. Check if components/ CSS directory exists
ls static/css/components/ 2>/dev/null || echo "components/ does not exist"

# 6. Check which templates include lightbox CSS
grep -rn "lightbox\|bulk-generator-job\|prompt-detail" \
    prompts/templates/prompts/bulk_generator_job.html \
    prompts/templates/prompts/prompt_detail.html 2>/dev/null | \
    grep -i "css\|link\|style" | head -10
```

**Do not proceed until all greps are complete. The current state determines
exactly what changes are needed.**

---

## 📁 STEP 1 — Fix `createLightbox` in `bulk-generator-gallery.js`

**File:** `static/js/bulk-generator-gallery.js`

From Step 0 grep 1, read the exact current structure. Replace/update it to
the correct structure. The final state must be:

```javascript
    G.createLightbox = function () {
        var overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.id = 'imageLightbox';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', 'Image preview');
        // No aria-describedby — caption was removed in Session 139

        // Close button — absolutely positioned top-right of overlay
        var closeBtn = document.createElement('button');
        closeBtn.className = 'lightbox-close';
        closeBtn.setAttribute('aria-label', 'Close preview');
        closeBtn.setAttribute('type', 'button');
        closeBtn.innerHTML = '&times;';

        var inner = document.createElement('div');
        inner.className = 'lightbox-inner';

        var img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'lightboxImage';
        img.alt = '';
        // No caption element — removed in Session 139

        inner.appendChild(img);
        overlay.appendChild(closeBtn); // Close directly on overlay, NOT in inner
        overlay.appendChild(inner);
        document.body.appendChild(overlay);

        closeBtn.addEventListener('click', G.closeLightbox);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) G.closeLightbox();
        });
        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') { G.closeLightbox(); return; }
            if (e.key === 'Tab') { e.preventDefault(); closeBtn.focus(); }
        });

        G.lightboxEl = overlay;
        return overlay;
    };
```

⚠️ The close button is appended to `overlay` directly, NOT to `inner`. This
is the key structural change — `position: absolute` on `.lightbox-close` then
positions it relative to the overlay (which is `position: fixed; inset: 0`),
placing it consistently at the top-right regardless of image size.

Also update `openLightbox` to remove any caption assignment. Find:
```javascript
var caption = document.getElementById('lightboxCaption');
```
and remove it along with any `caption.textContent = ...` assignment.

---

## 📁 STEP 2 — Fix `createPdLightbox` in `prompt_detail.html`

**File:** `prompts/templates/prompts/prompt_detail.html`

From Step 0 grep 2, read the exact current `createPdLightbox` structure.
Update it to the same pattern — close button on the overlay, not in a panel:

```javascript
        // Close button — absolutely positioned top-right of overlay
        var closeBtn = document.createElement('button');
        closeBtn.className = 'lightbox-close';
        closeBtn.setAttribute('aria-label', 'Close preview');
        closeBtn.setAttribute('type', 'button');
        closeBtn.innerHTML = '&times;';

        var inner = document.createElement('div');
        inner.className = 'lightbox-inner';

        var img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'pdLightboxImage';
        img.alt = '';

        // "Open in new tab" link — below the image, centered
        var openLink = document.createElement('a');
        openLink.className = 'lightbox-open-link';
        openLink.target = '_blank';
        openLink.rel = 'noopener noreferrer';
        openLink.innerHTML = '... Open in new tab';

        inner.appendChild(img);
        inner.appendChild(openLink); // Link is inside inner, below image
        overlay.appendChild(closeBtn); // Close button directly on overlay
        overlay.appendChild(inner);
        document.body.appendChild(overlay);
```

**Focus trap update** — with the new structure, only two focusable elements:
close button (on overlay) and open link (in inner). Update the Tab handler:

```javascript
        document.addEventListener('keydown', function(e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') { closePdLightbox(); return; }
            if (e.key === 'Tab') {
                e.preventDefault();
                var focused = document.activeElement;
                if (focused === closeBtn) {
                    openLink.focus();
                } else {
                    closeBtn.focus();
                }
            }
        });
```

---

## 📁 STEP 3 — Update lightbox CSS

**File:** `static/css/pages/bulk-generator-job.css`
**str_replace call 1 of 2**

Update `.lightbox-close` to be absolutely positioned on the overlay:

```css
/* Close button — absolutely positioned top-right of overlay, not in flow */
.lightbox-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    background: rgba(0, 0, 0, 0.5);
    border: 2px solid rgba(255, 255, 255, 0.6);
    color: white;
    font-size: 24px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.15s ease;
    z-index: 10000; /* above the image */
}

.lightbox-close:hover {
    background: rgba(0, 0, 0, 0.75);
    border-color: rgba(255, 255, 255, 0.9);
}

.lightbox-close:focus-visible {
    outline: none;
    box-shadow:
        0 0 0 2px rgba(0, 0, 0, 0.65),
        0 0 0 4px rgba(255, 255, 255, 0.9);
}
```

Remove any `.lightbox-right-panel` rules if present.

Update `.lightbox-inner` — no longer needs to accommodate a right panel:

```css
.lightbox-inner {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    max-width: 90vw;
    max-height: 90vh;
}

.lightbox-image {
    max-width: 90vw;
    max-height: 85vh;
    object-fit: contain;
    border-radius: var(--radius-lg, 0.5rem);
    display: block;
}

/* Open in new tab link — below image, centered */
.lightbox-open-link {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.75rem;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.875rem;
    text-decoration: none;
    padding: 0.4rem 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    transition: color 0.15s, border-color 0.15s;
}

.lightbox-open-link:hover {
    color: white;
    border-color: rgba(255, 255, 255, 0.7);
}

.lightbox-open-link:focus-visible {
    outline: none;
    box-shadow:
        0 0 0 2px rgba(0, 0, 0, 0.65),
        0 0 0 4px rgba(255, 255, 255, 0.9);
    border-color: rgba(255, 255, 255, 0.9);
}
```

**File:** `static/css/pages/bulk-generator-job.css`
**str_replace call 2 of 2**

Update the `prefers-reduced-motion` block to include the new close button
transition:

```css
@media (prefers-reduced-motion: reduce) {
    .lightbox-overlay { transition: none; }
    .lightbox-close { transition: none; }
    .lightbox-open-link { transition: none; }
}
```

---

## 📁 STEP 4 — Apply same CSS to `prompt-detail.css`

**File:** `static/css/pages/prompt-detail.css`

The prompt-detail.css lightbox rules must be identical to those in
bulk-generator-job.css. Find the existing lightbox block and replace
it entirely with the same rules from Step 3.

⚠️ DO NOT remove the lightbox CSS from `bulk-generator-job.css` — both files
need it until a shared component file is created.

---

## 📁 STEP 5 — Extract shared lightbox CSS to component file

**File:** `static/css/components/lightbox.css` (create new)

From Step 0 grep 5, if `static/css/components/` does not exist, create it.

Create `static/css/components/lightbox.css` with the final lightbox rules
(copy from `bulk-generator-job.css` after Step 3):

```css
/**
 * Shared Lightbox Component
 * Used by: bulk_generator_job.html, prompt_detail.html
 * Session 141 — extracted from bulk-generator-job.css and prompt-detail.css
 */

.lightbox-overlay { ... }
.lightbox-overlay.is-open { ... }
.lightbox-inner { ... }
.lightbox-image { ... }
.lightbox-close { ... }
.lightbox-close:hover { ... }
.lightbox-close:focus-visible { ... }
.lightbox-open-link { ... }
.lightbox-open-link:hover { ... }
.lightbox-open-link:focus-visible { ... }

@media (prefers-reduced-motion: reduce) { ... }
```

Then check Step 0 grep 6 to find how CSS is included in each template.
Add `<link>` to `lightbox.css` in both `bulk_generator_job.html` and
`prompt_detail.html`. Then REMOVE the lightbox rules from both
`bulk-generator-job.css` and `prompt-detail.css` (now centralised).

⚠️ If adding a `<link>` to both templates creates a risk, an alternative is
to `@import` from each CSS file. Use whichever approach matches the existing
pattern in the templates.

---

## 📁 STEP 6 — MANDATORY VERIFICATION

```bash
# Verify close button is on overlay, not in inner (gallery.js)
grep -n "overlay\.appendChild(closeBtn)\|inner\.appendChild(closeBtn)" \
    static/js/bulk-generator-gallery.js

# Verify close button is on overlay (prompt_detail.html)
grep -n "overlay\.appendChild(closeBtn)\|inner\.appendChild(closeBtn)" \
    prompts/templates/prompts/prompt_detail.html

# Verify caption is removed from gallery.js
grep -n "lightboxCaption\|caption\b" static/js/bulk-generator-gallery.js | head -5

# Verify lightbox component file exists
ls static/css/components/lightbox.css
```

**First grep MUST show `overlay.appendChild(closeBtn)` — not
`inner.appendChild(closeBtn)`. If it shows inner, the structural fix was
not applied. Do not run agents until this is correct.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and current state confirmed
- [ ] Step 6 verification greps all pass (show output in report)
- [ ] Close button appended to `overlay`, NOT `inner`, in BOTH lightboxes
- [ ] Caption `<p>` removed from gallery.js `createLightbox`
- [ ] `aria-describedby="lightboxCaption"` removed from overlay
- [ ] "Open in new tab" link inside `inner` (below image)
- [ ] Focus trap cycles between close button and open link (prompt detail)
- [ ] Focus trap stays on close button (results page — only one focusable element)
- [ ] CSS: `.lightbox-close` is `position: absolute; top: 16px; right: 16px`
- [ ] CSS: no `.lightbox-right-panel` rules remain
- [ ] **WCAG 1.4.11:** `.lightbox-close` dark circle background — verify
  contrast at 3:1 minimum against the dark overlay (`rgba(0,0,0,0.5)` on
  `rgba(0,0,0,0.85)` overlay — check the button is distinguishable)
- [ ] `prefers-reduced-motion` covers both close button and open-link transitions
- [ ] `lightbox.css` component file created and linked in both templates
- [ ] Lightbox rules removed from `bulk-generator-job.css` and `prompt-detail.css`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify `overlay.appendChild(closeBtn)` in BOTH lightbox builders
- Verify caption removed from `createLightbox` AND from `openLightbox`
- Verify focus trap correctly cycles between 2 elements (prompt detail)
  and stays on close (results page — only 1 element)
- Verify Step 6 verification greps are shown in report
- Rating requirement: 8+/10

### 2. @ux-ui-designer
- Verify × button is visible at top-right on desktop AND mobile
- Verify image is horizontally centered without the right panel
- Verify "Open in new tab" link appears below image in prompt detail
- Verify no layout regression on the results page lightbox
- Rating requirement: 8+/10

### 3. @accessibility
- **WCAG 1.4.11:** Verify `.lightbox-close` dark circle meets 3:1 non-text
  contrast. Dark circle `rgba(0,0,0,0.5)` on dark overlay `rgba(0,0,0,0.85)`:
  the button may blend into the overlay. If contrast fails, use
  `background: rgba(255,255,255,0.15); border: 2px solid white` instead.
- Verify focus trap in both lightboxes is correct
- Verify `aria-modal="true"` and `role="dialog"` still present
- Verify `prefers-reduced-motion` covers all new transitions
- Rating requirement: 8+/10

### 4. @code-reviewer
- Verify CSS rules in `lightbox.css` exactly match what was removed from
  the two page-level CSS files
- Verify both templates correctly link `lightbox.css`
- Verify no duplicate lightbox rules remain in `bulk-generator-job.css`
  or `prompt-detail.css`
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Close button is still inside `inner` or `.lightbox-right-panel`
- Caption element still present in `createLightbox`
- Step 6 first grep shows `inner.appendChild(closeBtn)`
- `lightbox.css` not created or not linked in templates

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser checks (Mateo must verify):**
1. Open lightbox on results page → verify × is in top-right of the dark
   overlay, NOT overlaid on the image
2. Resize to mobile width → verify × stays top-right (does NOT move below image)
3. Open lightbox on prompt detail page → verify × is top-right, "Open in
   new tab" is below the image
4. Press Tab → verify focus cycles correctly
5. Press Escape → verify lightbox closes

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(lightbox): close button absolutely positioned on overlay, caption removed, CSS extracted to component
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_141_C_LIGHTBOX_CLOSE_BUTTON_FIX.md`

**Section 3 MUST include all Step 6 verification grep outputs.**

---

**END OF SPEC**
