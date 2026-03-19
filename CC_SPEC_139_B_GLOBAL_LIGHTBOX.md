# CC_SPEC_139_B_GLOBAL_LIGHTBOX.md
# Global Lightbox Unification — Prompt Detail + Results Page + Featured Image

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 139
**Modifies UI/Templates:** YES (prompt_detail.html, style.css or prompt-detail.css)
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~80 lines across 3 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.1** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **Run after Spec A** — Spec A removes the Bootstrap modal and wires
   `window.openPromptDetailLightbox`. This spec defines that function.
4. **`prompt_detail.html` is 🟡 Caution** — str_replace only
5. **`bulk-generator-gallery.js` is ✅ Safe** — normal editing
6. **`bulk-generator-job.css` is 🟡 Caution** — max 3 str_replace calls

---

## 📋 OVERVIEW

Two different lightbox styles currently exist:
- **Results page** — custom JS lightbox (`G.createLightbox` in `bulk-generator-gallery.js`)
- **Prompt detail** — Bootstrap modal (`#sourceImageModal`)

The results page custom lightbox becomes the global standard. Changes:

1. **Remove prompt text paragraph** from results page lightbox (keep the lightbox,
   just remove the `<p class="lightbox-caption">` element)
2. **Add `openPromptDetailLightbox` function** to prompt detail page — same
   custom lightbox style, with "Open in new tab" button included
3. **Add lightbox to hero image** on prompt detail — magnifying glass on hover,
   cursor becomes zoom cursor, click opens lightbox

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full createLightbox function in bulk-generator-gallery.js
grep -n "createLightbox\|lightbox-caption\|lightboxCaption\|caption" \
    static/js/bulk-generator-gallery.js | head -10

# 2. Read openLightbox function
grep -n "openLightbox\|lightboxTrigger\|is-open" \
    static/js/bulk-generator-gallery.js | head -10

# 3. Read lightbox CSS
grep -n "lightbox\|lightbox-caption" static/css/pages/bulk-generator-job.css | head -15

# 4. Read the hero image HTML in prompt_detail.html
sed -n '198,235p' prompts/templates/prompts/prompt_detail.html

# 5. Read the end of prompt_detail.html to find script block location
tail -30 prompts/templates/prompts/prompt_detail.html

# 6. Read current source-image-thumb-wrap (from Spec A) to confirm selector
grep -n "source-image-thumb-wrap\|openSourceImageLightbox\|openPromptDetailLightbox" \
    prompts/templates/prompts/prompt_detail.html 2>/dev/null | head -5
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Remove caption from results page lightbox

**File:** `static/js/bulk-generator-gallery.js`

From Step 0 grep, find `createLightbox`. Remove the caption element creation:

```javascript
        var caption = document.createElement('p');
        caption.className = 'lightbox-caption';
        caption.id = 'lightboxCaption';
        ...
        inner.appendChild(caption);
```

Also remove `aria-describedby="lightboxCaption"` from the overlay element.

In `openLightbox`, remove the caption assignment:
```javascript
        caption.textContent = promptText ? '\u201C' + promptText + '\u201D' : '';
```

Remove `var caption = document.getElementById('lightboxCaption');`

**File:** `static/css/pages/bulk-generator-job.css`
**str_replace call 1 of 2**

Find and remove `.lightbox-caption` CSS rule. Replace with empty comment
to avoid leaving an orphaned selector.

---

## 📁 STEP 2 — Add `openPromptDetailLightbox` to prompt_detail.html

**File:** `prompts/templates/prompts/prompt_detail.html`

Find the existing `{% block extras %}` or script section at the bottom of the
template. Add a self-contained lightbox for the prompt detail page:

```html
{% if prompt.b2_source_image_url or prompt.display_large_url %}
<script>
(function() {
    'use strict';

    var pdLightboxEl = null;
    var pdLightboxTrigger = null;

    function createPdLightbox() {
        var overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.id = 'pdImageLightbox';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', 'Image preview');

        var inner = document.createElement('div');
        inner.className = 'lightbox-inner';

        var closeBtn = document.createElement('button');
        closeBtn.className = 'lightbox-close';
        closeBtn.setAttribute('aria-label', 'Close preview');
        closeBtn.setAttribute('type', 'button');
        closeBtn.innerHTML = '&times;';

        var img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'pdLightboxImage';
        img.alt = '';

        // "Open in new tab" link — shown for prompt detail lightbox
        var openLink = document.createElement('a');
        openLink.className = 'lightbox-open-link';
        openLink.target = '_blank';
        openLink.rel = 'noopener noreferrer';
        openLink.innerHTML =
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" ' +
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
            'stroke-linejoin="round" aria-hidden="true">' +
            '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>' +
            '<polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>' +
            '</svg> Open in new tab';

        inner.appendChild(closeBtn);
        inner.appendChild(img);
        inner.appendChild(openLink);
        overlay.appendChild(inner);
        document.body.appendChild(overlay);

        closeBtn.addEventListener('click', closePdLightbox);
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) closePdLightbox();
        });
        document.addEventListener('keydown', function(e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') closePdLightbox();
            if (e.key === 'Tab') { e.preventDefault(); closeBtn.focus(); }
        });

        pdLightboxEl = overlay;
        return overlay;
    }

    function openPdLightbox(imageUrl, altText) {
        pdLightboxTrigger = document.activeElement;
        if (!pdLightboxEl) createPdLightbox();
        var img = document.getElementById('pdLightboxImage');
        var link = pdLightboxEl.querySelector('.lightbox-open-link');
        img.src = imageUrl;
        img.alt = altText || 'Full size preview';
        link.href = imageUrl;
        pdLightboxEl.classList.add('is-open');
        document.body.style.overflow = 'hidden';
        pdLightboxEl.querySelector('.lightbox-close').focus();
    }

    function closePdLightbox() {
        if (!pdLightboxEl) return;
        pdLightboxEl.classList.remove('is-open');
        document.body.style.overflow = '';
        if (pdLightboxTrigger && typeof pdLightboxTrigger.focus === 'function') {
            pdLightboxTrigger.focus();
            pdLightboxTrigger = null;
        }
    }

    // Expose globally for Spec A's openSourceImageLightbox() + hero image click
    window.openPromptDetailLightbox = openPdLightbox;
})();
</script>
{% endif %}
```

---

## 📁 STEP 3 — Add lightbox + zoom hover to hero image

**File:** `prompts/templates/prompts/prompt_detail.html`

From Step 0 grep, find the hero image wrapper. The main image is inside
`.media-container.prompt-media-container`. Wrap it with a zoom-enabled
container and wire the click:

Find the `<img ... class="hero-image"` tags (there are 3 — B2, Cloudinary,
and placeholder). For the B2 and Cloudinary variants (not the placeholder),
wrap the `<img>` in a clickable div:

```html
<div class="hero-image-wrap"
     role="button"
     tabindex="0"
     aria-label="View full size image"
     onclick="window.openPromptDetailLightbox(this.querySelector('img').src, this.querySelector('img').alt)"
     onkeydown="if(event.key==='Enter'||event.key===' ')window.openPromptDetailLightbox(this.querySelector('img').src,this.querySelector('img').alt)">
    <img src="{{ prompt.display_large_url }}" ... class="hero-image" ...>
    <div class="hero-image-zoom-icon" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
             stroke="white" stroke-width="2" stroke-linecap="round"
             stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
    </div>
</div>
```

⚠️ Wrap only the real image variants (B2 and Cloudinary). Do NOT wrap the
placeholder SVG — it should not be clickable.

⚠️ Read the exact B2 URL used in the onclick. Use `{{ prompt.display_large_url }}`
for the B2 variant and `{{ prompt.featured_image.url|... }}` for Cloudinary.
The inline onclick approach avoids templating issues.

---

## 📁 STEP 4 — Add hero image zoom CSS to `prompt-detail.css`

Append to `static/css/pages/prompt-detail.css`:

```css
/* ── Hero Image Lightbox Hover (Session 139) ───────────────── */
.hero-image-wrap {
    position: relative;
    display: block;
    cursor: zoom-in;
}

.hero-image-zoom-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: none;
}

.hero-image-wrap:hover .hero-image-zoom-icon,
.hero-image-wrap:focus .hero-image-zoom-icon {
    opacity: 1;
}

/* Open in new tab link inside prompt detail lightbox */
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

@media (prefers-reduced-motion: reduce) {
    .hero-image-zoom-icon { transition: none; }
    .hero-image-wrap { cursor: pointer; }
}
```

---

## 📁 STEP 5 — Add lightbox CSS shared rules

The lightbox CSS (`.lightbox-overlay`, `.lightbox-inner`, `.lightbox-close`,
`.lightbox-image`) currently lives only in `bulk-generator-job.css`. Since the
prompt detail page now uses the same lightbox style, add the shared rules to
`style.css` or `prompt-detail.css`.

From Step 0 grep, read the lightbox CSS from `bulk-generator-job.css`. Copy
the rules verbatim to `prompt-detail.css` under a comment:

```css
/* ── Shared Lightbox (global style — Session 139) ──────────── */
/* Matches bulk-generator-job.css lightbox for visual consistency */
```

⚠️ Do NOT remove the rules from `bulk-generator-job.css` — the results page
still needs them. This is a copy, not a move. In a future session the shared
rules can be centralised in `style.css`.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Caption `<p>` removed from `createLightbox` in gallery.js
- [ ] `aria-describedby` removed from lightbox overlay in gallery.js
- [ ] Caption assignment removed from `openLightbox` in gallery.js
- [ ] `.lightbox-caption` CSS removed from `bulk-generator-job.css`
- [ ] `openPromptDetailLightbox` defined and exposed on `window`
- [ ] "Open in new tab" link included in prompt detail lightbox
- [ ] Hero image wrapped in `.hero-image-wrap` (B2 and Cloudinary only)
- [ ] Placeholder image NOT wrapped (not clickable)
- [ ] `cursor: zoom-in` on `.hero-image-wrap`
- [ ] Magnifying glass appears on hero image hover
- [ ] Lightbox CSS copied to `prompt-detail.css` (not moved from job.css)
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify caption fully removed from createLightbox AND openLightbox
- Verify `window.openPromptDetailLightbox` accessible to Spec A's JS
- Verify hero image placeholder not wrapped
- Verify focus trap works in prompt detail lightbox
- Rating requirement: 8+/10

### 2. @ux-ui-designer
- Verify magnifying glass icon size/position matches results page style
- Verify "Open in new tab" link visible and styled correctly in lightbox
- Verify `cursor: zoom-in` on hero image
- Rating requirement: 8+/10

### 3. @accessibility
- Verify lightbox has `role="dialog"` and `aria-modal="true"`
- Verify focus moves to close button on open, restored on close
- Verify hero wrap accessible via keyboard (tabindex + keydown)
- Rating requirement: 8+/10

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser check (Mateo must verify):**
1. Results page — hover an image, click → lightbox opens with NO caption text
2. Prompt detail — hover the hero image → magnifying glass appears, cursor changes
3. Click hero image → lightbox opens, "Open in new tab" link visible
4. Source image (from Spec A) → click thumbnail → same lightbox style
5. Press Escape → lightbox closes, focus returns to trigger element

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
feat(lightbox): global lightbox — remove caption from results, add to hero image, open-in-new-tab
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_139_B_GLOBAL_LIGHTBOX.md`

---

**END OF SPEC**
