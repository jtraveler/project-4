# CC_SPEC_139_A_SOURCE_IMAGE_CARD_REDESIGN.md
# Prompt Detail — Source Image Card Redesign + WebP Upload Optimization

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 139
**Modifies UI/Templates:** YES (prompt_detail.html, prompt-detail.css)
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~40 lines across 3 files + tasks.py B2 upload

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.1** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`prompt_detail.html` is 🟡 Caution** — str_replace only
4. **`tasks.py` is 🔴 Critical (3,451+ lines)** — max 2 str_replace calls,
   5+ line anchors required
5. **Run Spec B after this spec** — Spec B replaces the Bootstrap modal with
   the custom lightbox. This spec removes the Bootstrap modal trigger button
   and wires an `onclick` to the custom lightbox instead.

---

## 📋 OVERVIEW

The source credit and source image are currently in two separate `rail-card`
divs stacked vertically. The redesign:

1. **Merge into one row** — Source credit (left) and source image (right) in
   a single `rail-card` with a flex row layout
2. **Remove "View Source Image" button** — clicking the image thumbnail opens
   the lightbox instead
3. **Magnifying glass on hover** — same `.btn-zoom` pattern as results page
4. **180×180px thumbnail** — increase from current 120×80px, move inline
   styles to `prompt-detail.css`
5. **WebP conversion** — convert paste source images to WebP with Pillow
   at upload time in `_upload_source_image_to_b2`
6. **Remove Bootstrap modal** — replaced by custom lightbox in Spec B

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read current source credit + source image cards (confirm exact HTML)
sed -n '452,498p' prompts/templates/prompts/prompt_detail.html

# 2. Read current Bootstrap modal
sed -n '867,900p' prompts/templates/prompts/prompt_detail.html

# 3. Read current source-image CSS in prompt-detail.css
grep -n "source-image\|source-credit\|source-image-thumb\|source-image-card" \
    static/css/pages/prompt-detail.css | head -15

# 4. Read _upload_source_image_to_b2 function
sed -n '2965,3015p' prompts/tasks.py

# 5. Check if Pillow is already imported/used in tasks.py
grep -n "^from PIL\|^import PIL\|from PIL import\|Image\.open\|Image\.new" \
    prompts/tasks.py | head -5

# 6. Read btn-zoom CSS for reference (copy pattern from results page)
grep -n "btn-zoom\|zoom-icon\|magnify" static/css/pages/prompt-detail.css | head -5
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Merge source credit + source image into one rail-card

**File:** `prompts/templates/prompts/prompt_detail.html`

Replace the two separate rail-cards with a single merged card. The new card
shows both columns in a flex row, only rendered when at least one of the two
fields is present.

**Current (two separate cards, find exact text from Step 0):**
```html
{% if user.is_staff and prompt.source_credit %}
<div class="rail-card source-credit-card">
    ...
</div>
{% endif %}

{% if user.is_staff and prompt.b2_source_image_url %}
<div class="rail-card source-image-card" id="source-image-card">
    ...
</div>
{% endif %}
```

**Replace with (single merged card):**
```html
{% if user.is_staff and (prompt.source_credit or prompt.b2_source_image_url) %}
<div class="rail-card source-combined-card">
    {% if prompt.source_credit %}
    <div class="source-credit-col">
        <h2 class="rail-card-title">Source</h2>
        <div class="source-credit-content">
            {% if prompt.source_credit_url %}
            <a href="{{ prompt.source_credit_url }}"
               target="_blank"
               rel="noopener nofollow"
               class="source-credit-link"
               aria-label="{{ prompt.source_credit }} (opens in new tab)">
                {{ prompt.source_credit }}
                <svg class="icon icon-sm" aria-hidden="true"><use href="{% static 'icons/sprite.svg' %}#icon-external-link"/></svg>
            </a>
            {% else %}
            <span class="source-credit-text">{{ prompt.source_credit }}</span>
            {% endif %}
        </div>
    </div>
    {% endif %}

    {% if prompt.b2_source_image_url %}
    <div class="source-image-col">
        <h2 class="rail-card-title">Source Image</h2>
        <div class="source-image-content">
            <div class="source-image-thumb-wrap"
                 role="button"
                 tabindex="0"
                 aria-label="View full size source image"
                 onclick="openSourceImageLightbox()"
                 onkeydown="if(event.key==='Enter'||event.key===' ')openSourceImageLightbox()">
                <img src="{{ prompt.b2_source_image_url }}"
                     alt="Source image for {{ prompt.title }}"
                     class="source-image-thumb"
                     loading="lazy">
                <div class="source-image-zoom-icon" aria-hidden="true">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                         stroke="white" stroke-width="2" stroke-linecap="round"
                         stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>
{% endif %}
```

Also **remove the Bootstrap modal** (`#sourceImageModal`) entirely — it will
be replaced by the custom lightbox initialised in Spec B.

Find and delete the entire:
```html
{% if user.is_staff and prompt.b2_source_image_url %}
<!-- Source Image Lightbox Modal (staff-only, SRC-5) -->
<div class="modal fade" id="sourceImageModal" ...>
    ...
</div>
{% endif %}
```

Add a small inline script after the merged card to wire the custom lightbox:
```html
{% if user.is_staff and prompt.b2_source_image_url %}
<script>
function openSourceImageLightbox() {
    if (window.openPromptDetailLightbox) {
        window.openPromptDetailLightbox(
            '{{ prompt.b2_source_image_url|escapejs }}',
            '{{ prompt.title|escapejs }}'
        );
    }
}
</script>
{% endif %}
```

⚠️ `window.openPromptDetailLightbox` is defined in Spec B. This script must
be loaded after Spec B's lightbox initialisation — confirm script order in
the template.

---

## 📁 STEP 2 — Add source image CSS to `prompt-detail.css`

**File:** `static/css/pages/prompt-detail.css`

Add at the end of the file (no str_replace needed — append):

```css
/* ── Source Combined Card (Session 139) ─────────────────── */
.source-combined-card {
    display: flex;
    flex-direction: row;
    gap: 1.5rem;
    align-items: flex-start;
    flex-wrap: wrap;
}

.source-credit-col {
    flex: 1;
    min-width: 120px;
}

.source-image-col {
    flex-shrink: 0;
}

/* Source image thumbnail with zoom overlay */
.source-image-thumb-wrap {
    position: relative;
    display: inline-block;
    cursor: pointer;
    border-radius: var(--radius-sm, 6px);
    overflow: hidden;
}

.source-image-thumb {
    display: block;
    max-width: 180px;
    max-height: 180px;
    width: auto;
    height: auto;
    object-fit: cover;
    border-radius: var(--radius-sm, 6px);
    transition: opacity 0.2s ease;
}

.source-image-thumb-wrap:hover .source-image-thumb {
    opacity: 0.85;
}

.source-image-zoom-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: none;
}

.source-image-thumb-wrap:hover .source-image-zoom-icon,
.source-image-thumb-wrap:focus .source-image-zoom-icon {
    opacity: 1;
}
```

---

## 📁 STEP 3 — WebP conversion in `_upload_source_image_to_b2`

**File:** `prompts/tasks.py`
**str_replace call 1 of 1**

From Step 0 grep, read the full `_upload_source_image_to_b2` function. Find
the point where `image_bytes` is uploaded to B2 and add WebP conversion
before the upload:

```python
def _upload_source_image_to_b2(image_bytes: bytes, job, image) -> str:
```

After reading the bytes and before calling `s3_client.put_object`, add:

```python
    # Convert to WebP for efficient storage and delivery
    try:
        from PIL import Image as PILImage
        import io
        pil_img = PILImage.open(io.BytesIO(image_bytes))
        # Convert RGBA to RGB if needed (WebP supports RGBA but keep it simple)
        if pil_img.mode in ('RGBA', 'LA', 'P'):
            pil_img = pil_img.convert('RGB')
        # Resize to max 1200px on longest side, preserving aspect ratio
        pil_img.thumbnail((1200, 1200), PILImage.LANCZOS)
        webp_buffer = io.BytesIO()
        pil_img.save(webp_buffer, format='WEBP', quality=85, method=4)
        image_bytes = webp_buffer.getvalue()
        content_type = 'image/webp'
        file_ext = 'webp'
    except Exception as pil_exc:
        logger.warning(
            "[SRC-6] WebP conversion failed, uploading original: %s", pil_exc
        )
        # Fall through to upload original bytes with original extension
```

⚠️ The `file_ext` variable is used to build the B2 key filename. Verify from
Step 0 grep how the key is constructed and ensure `file_ext` is used correctly.
If the key is constructed before this block, refactor so the key uses `file_ext`
after the WebP conversion attempt.

⚠️ Verify Pillow is already imported/available in tasks.py from Step 0 grep.
If not, add the import inside the try block (as shown above) to keep it local.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Two separate source rail-cards replaced with single merged card
- [ ] Bootstrap modal (`#sourceImageModal`) fully removed from template
- [ ] Source image thumbnail uses CSS class only (no inline styles)
- [ ] `.source-image-thumb` max-width/height is 180px in CSS
- [ ] Magnifying glass zoom icon overlays thumbnail on hover
- [ ] `openSourceImageLightbox()` calls `window.openPromptDetailLightbox`
- [ ] WebP conversion wrapped in try/except (never blocks upload on failure)
- [ ] `file_ext` updated to `'webp'` after successful conversion
- [ ] `content_type` updated to `'image/webp'` after successful conversion
- [ ] Maximum 1 str_replace call on `tasks.py`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify Bootstrap modal fully removed (no orphaned data-bs-target references)
- Verify `openSourceImageLightbox` JS function scoped correctly
- Verify zoom icon accessible via keyboard (tabindex + keydown handler)
- Rating requirement: 8+/10

### 2. @django-pro
- Verify WebP conversion try/except never raises an unhandled exception
- Verify `file_ext` used correctly in B2 key construction after conversion
- Verify Pillow import scoped correctly
- Rating requirement: 8+/10

### 3. @ux-ui-designer
- Verify merged card layout looks correct with both fields present
- Verify merged card layout looks correct with only one field present
- Verify 180×180px thumbnail size is proportionate in the rail
- Rating requirement: 8+/10

### 4. @security-auditor
- Verify `{{ prompt.b2_source_image_url|escapejs }}` correctly escapes
  the URL in the JS onclick attribute — no XSS vector
- Verify `{{ prompt.title|escapejs }}` also escaped correctly
- Verify the onclick pattern cannot be exploited if a URL contains
  unexpected characters
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Inline `style=` attribute remains on `source-image-thumb`
- Bootstrap modal still present in template
- WebP conversion failure causes upload to fail
- `escapejs` filter missing from URL/title in JS onclick

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser check (Mateo must verify):**
1. Visit a prompt detail page (as staff) that has both source credit and
   source image — verify one row with credit left, image right
2. Hover the source image thumbnail — verify magnifying glass appears
3. Click the thumbnail — verify custom lightbox opens (Spec B must be deployed)
4. Visit a page with only source credit — verify only left column shows
5. Visit a page with only source image — verify only right column shows

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
feat(prompt-detail): merged source card, zoom lightbox, 180px thumb, WebP conversion
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_139_A_SOURCE_IMAGE_CARD_REDESIGN.md`

---

**END OF SPEC**
