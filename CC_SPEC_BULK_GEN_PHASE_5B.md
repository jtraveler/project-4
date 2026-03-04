# CC_SPEC_BULK_GEN_PHASE_5B — Gallery Rows + Progressive Loading

**Date:** March 2, 2026
**Phase:** Bulk AI Image Generator — Phase 5B
**Depends On:** Phase 5A + 5A Fixes (complete)
**Estimated Effort:** 4-6 hours

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`**
2. **Read this entire specification**
3. **Read `static/js/bulk-generator-job.js`** — You will ADD to this file
4. **Read `static/css/pages/bulk-generator-job.css`** — You will ADD to this file
5. **Read `prompts/templates/prompts/bulk_generator_job.html`** — You will ADD to this file
6. **Read `static/icons/sprite.svg`** — You will ADD one new icon
7. **Read `prompts/views/bulk_generator_views.py`** — Check what the status API returns for image data
8. **Use required agents** — Minimum 3 agents
9. **Report agent usage** — Include ratings and findings in completion summary

⛔ **IMPORTANT:** The template uses `{% block extras %}` for scripts (NOT `{% block extra_scripts %}`). Do NOT change this.

---

## ⛔ STOP — MANDATORY REQUIREMENTS

> **Work will be REJECTED if ANY of the following are missing:**
>
> 1. Gallery rows appear inside `.job-gallery-container` as images complete
> 2. Each prompt group shows as one row: prompt header + 4-column image grid
> 3. Grey placeholders shown for unfilled image slots (always 4 columns)
> 4. Selection circle overlay (upper-right) — outline → solid white + black checkmark on select
> 5. Download icon button (upper-right, left of selection circle)
> 6. Only 1 image selectable per prompt group (radio-style)
> 7. Non-selected images fade to 35% opacity when one is selected
> 8. Truncated prompt text with hover overlay showing full prompt
> 9. Smooth entrance animation for new rows (like existing prompt box load-more animation)
> 10. Download SVG icon added to sprite.svg
> 11. All existing 945 tests still passing
> 12. Agent ratings 8+/10

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### Task: Gallery Rows with Image Selection + Progressive Loading

Build the gallery section of the job progress page. As the polling returns completed images, prompt group rows appear one by one with smooth animation. Each row shows the prompt text, a 4-column image grid, and per-image overlay icons for selection and download.

### What This Spec Covers
- ✅ Prompt group rows appearing progressively during polling
- ✅ 4-column image grid per row with grey placeholders
- ✅ Uniform square image containers with `object-fit: contain`
- ✅ Image selection (1 per group, radio-style) with circle overlay
- ✅ Download button overlay per image
- ✅ Truncated prompt text with hover overlay for full text
- ✅ Per-group metadata line (dimensions, quality)
- ✅ Fade effect on non-selected images
- ✅ Download SVG icon added to sprite

### What This Spec Does NOT Cover
- ❌ Edit prompt / Regenerate buttons (Phase 5C)
- ❌ Image lightbox / click to enlarge (Phase 5C)
- ❌ Per-group publish toggle (Phase 5D)
- ❌ "Create Pages" button (Phase 6)
- ❌ Failed image handling with retry (Phase 5C)

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Prompt rows render in gallery container as images complete via polling
- ✅ Each row: prompt number + truncated text + metadata + 4 image slots
- ✅ Grey placeholder boxes for slots without images
- ✅ Completed images display in their prompt group with `object-fit: contain` in square containers
- ✅ Hover on truncated prompt text → overlay popup shows full prompt
- ✅ Click selection circle → circle fills white with black checkmark, other images in group fade to 35%
- ✅ Click download icon → triggers browser download of the image
- ✅ Rows animate in smoothly (fade-up, staggered)
- ✅ Mobile responsive: 4 cols → 2 cols → 1 col
- ✅ All tests pass

---

## 🔧 SOLUTION

### Implementation Approach

1. **Modify the polling `updateProgress()` in `bulk-generator-job.js`** to also process image data from the status API response
2. **Render prompt group rows dynamically** using JS DOM creation (no separate template)
3. **Track which images have been rendered** to avoid duplicates on subsequent polls
4. **Add CSS** for gallery rows, image containers, overlays, hover states, and animations
5. **Add download icon SVG** to the existing sprite file
6. **Modify template** minimally — just ensure the gallery container has any needed data attributes

### How the Status API Returns Image Data

⛔ **CC MUST read the actual status view** (`bulk_generator_views.py` → the status endpoint) to verify what image data it returns. The response likely includes an `images` array with objects like:
```json
{
    "images": [
        {
            "id": "uuid",
            "prompt_text": "a dog in the forest...",
            "prompt_index": 0,
            "status": "completed",
            "image_url": "https://...",
            "quality": "medium",
            "size": "1024x1024",
            "order": 0
        }
    ]
}
```

**Use the ACTUAL field names from the API response.** If the API doesn't currently return image data in the status response, you will need to ADD it to the status view — include each image's id, prompt_text, prompt_index (or order), status, image_url, quality, and size.

### Image Grouping Logic

Images are grouped by prompt. The `images_per_prompt` setting (from the job) determines how many images belong to each group. Images are ordered — images 0-3 belong to prompt group 0, images 4-7 to prompt group 1, etc. (if images_per_prompt=4).

More precisely: `group_index = floor(image.order / images_per_prompt)`

Each group always shows 4 slots. If `images_per_prompt` is 2, slots 0-1 have images and slots 2-3 are grey placeholders.

---

## 🏗️ DOM STRUCTURE

⛔ **CC must implement the EXACT nesting shown here.**

### Per Prompt Group Row
```
.prompt-group (data-group-index="0")
├── .prompt-group-header
│     ├── .prompt-group-number   "#1"
│     ├── .prompt-group-text-wrapper
│     │     ├── .prompt-group-text (truncated, ~80 chars + "...")
│     │     └── .prompt-group-text-overlay (hidden, shown on hover)
│     │           └── .prompt-overlay-content (full prompt text)
│     └── .prompt-group-meta
│           ├── span "1024×1024"
│           └── span "Medium"
│
└── .prompt-group-images
      ├── .prompt-image-slot (data-slot="0")
      │     ├── .prompt-image-container
      │     │     ├── img (or .placeholder-empty if no image)
      │     │     └── .prompt-image-overlay (shown on image hover)
      │     │           ├── button.btn-download (aria-label="Download image")
      │     │           │     └── svg (use sprite #icon-download)
      │     │           └── button.btn-select (aria-label="Select this image")
      │     │                 └── svg (use sprite #icon-check OR circle outline)
      │
      ├── .prompt-image-slot (data-slot="1") ... same structure
      ├── .prompt-image-slot (data-slot="2") ... same or placeholder
      └── .prompt-image-slot (data-slot="3") ... same or placeholder
```

### Placeholder Slot (no image)
```
.prompt-image-slot.is-placeholder (data-slot="2")
└── .prompt-image-container
      └── .placeholder-empty (grey box, no overlay icons)
```

### Selected State
```
.prompt-image-slot.is-selected   → solid circle with checkmark, full opacity
.prompt-image-slot.is-deselected → 35% opacity (applied to siblings when one is selected)
```

---

## 📋 COPY EXACTLY — Download Icon SVG for Sprite

⛔ **Add this EXACT SVG to `static/icons/sprite.svg` as a new symbol. Do NOT substitute.**

```xml
<symbol id="icon-download" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 17V3"/>
    <path d="m6 11 6 6 6-6"/>
    <path d="M19 21H5"/>
</symbol>
```

**Verification:** After adding, run `grep "icon-download" static/icons/sprite.svg` and confirm exactly 1 match.

---

## 📁 FILES TO MODIFY

### File 1: `static/icons/sprite.svg`

Add the `icon-download` symbol (see COPY EXACTLY section above).

### File 2: `prompts/views/bulk_generator_views.py`

**Check the status API endpoint.** If it doesn't return image data, ADD image details to the status response. The response must include:

```python
'images': [
    {
        'id': str(img.id),
        'prompt_text': img.prompt_text,
        'order': img.order,
        'status': img.status,
        'image_url': img.image_url or '',
        'quality': img.quality or job.quality,
        'size': img.size or job.size,
    }
    for img in job.images.all().order_by('order')
]
```

⛔ **Read the existing view first.** If image data is already returned, use the existing field names. Only add if missing.

### File 3: `static/js/bulk-generator-job.js`

**ADD the following capabilities** (do not rewrite existing code):

**A) Track rendered groups:**
```javascript
var renderedGroups = {};  // { groupIndex: { slots: {0: imageId, ...}, element: domNode } }
var imagesPerPrompt = parseInt(root.dataset.imagesPerPrompt, 10) || 1;
```

Add `data-images-per-prompt` to the template root element.

**B) In `updateProgress(data)`, after existing logic, process images:**
```javascript
if (data.images && data.images.length > 0) {
    renderImages(data.images);
}
```

**C) `renderImages(images)` function:**
- Group images by prompt: `groupIndex = Math.floor(image.order / imagesPerPrompt)`
- For each group, if the group row doesn't exist yet, create it with `createGroupRow(groupIndex, promptText)`
- For each completed image in the group, if the slot isn't filled yet, fill it with `fillImageSlot(groupIndex, slotIndex, image)`

**D) `createGroupRow(groupIndex, promptText)` function:**
- Creates the DOM structure from the tree diagram above
- Prompt text truncated to ~80 chars with "..." if longer
- Full text stored in the overlay element
- 4 placeholder slots created initially
- Append to `.job-gallery-container` with entrance animation class
- Stagger animation delay: `style="animation-delay: ${groupIndex * 80}ms"`

**E) `fillImageSlot(groupIndex, slotIndex, image)` function:**
- Find the slot element by data-slot attribute
- Remove placeholder content
- Create `<img>` with `src=image.image_url`, `alt` text, `loading="lazy"`
- Add overlay with download + select buttons
- Smooth fade-in transition for the image

**F) Selection logic:**
- Click on `.btn-select` → add `.is-selected` to that slot, add `.is-deselected` to all other slots in the same group
- If clicking an already-selected slot, deselect (remove all classes, restore all to full opacity)
- Track selections: `var selections = {};  // { groupIndex: imageId }`
- Selection circle: default is outline circle (CSS border-radius: 50%, border only). Selected state: solid white background with checkmark icon.

**G) Download logic:**
- Click on `.btn-download` → create a temporary `<a>` element with `href=image.image_url`, `download` attribute, trigger click
- Or use `window.open(image.image_url, '_blank')` as fallback

**H) Hover overlay for prompt text:**
- Mouseenter on `.prompt-group-text-wrapper` → show `.prompt-group-text-overlay`
- Mouseleave → hide it
- Position: absolute, below the text, with arrow/shadow, z-index above images
- Max-width: 500px, word-wrap

### File 4: `static/css/pages/bulk-generator-job.css`

**ADD the following styles** (append to existing file):

**A) Prompt Group Row:**
```css
.prompt-group {
    margin-bottom: 2rem;
    animation: promptGroupFadeIn 300ms ease-out forwards;
    opacity: 0;
}
@keyframes promptGroupFadeIn {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}
```

**B) Prompt Group Header:**
- `.prompt-group-header`: flex, align-items center, gap 0.75rem, margin-bottom 0.75rem, flex-wrap wrap
- `.prompt-group-number`: font-weight bold, color `var(--gray-800)`, font-size `var(--text-base)`, min-width 2rem
- `.prompt-group-text`: color `var(--gray-600)`, font-size `var(--text-sm)`, white-space nowrap, overflow hidden, text-overflow ellipsis, max-width 500px, cursor pointer
- `.prompt-group-meta span`: font-size `var(--text-xs)`, color `var(--gray-500)`, separated by " · "

**C) Prompt Text Hover Overlay:**
- `.prompt-group-text-wrapper`: position relative
- `.prompt-group-text-overlay`: position absolute, top 100%, left 0, z-index 10, background `var(--white)`, border `1px solid var(--gray-200)`, border-radius `var(--radius-lg)`, padding 1rem, box-shadow `0 4px 12px rgba(0,0,0,0.1)`, max-width 500px, display none
- `.prompt-group-text-wrapper:hover .prompt-group-text-overlay`: display block
- `.prompt-overlay-content`: font-size `var(--text-sm)`, color `var(--gray-700)`, line-height 1.5, white-space normal, word-wrap break-word

**D) Image Grid:**
- `.prompt-group-images`: display grid, grid-template-columns `repeat(4, 1fr)`, gap 0.75rem
- Mobile: below 768px → `repeat(2, 1fr)`, below 480px → `repeat(1, 1fr)`

**E) Image Slot + Container:**
- `.prompt-image-slot`: position relative, aspect-ratio 1/1, border-radius `var(--radius-lg)`, overflow hidden
- `.prompt-image-container`: width 100%, height 100%, display flex, align-items center, justify-content center, background `var(--gray-100)`
- `.prompt-image-container img`: max-width 100%, max-height 100%, object-fit contain
- `.placeholder-empty`: width 100%, height 100%, background `var(--gray-100)`, border `2px dashed var(--gray-200)`, border-radius `var(--radius-lg)`

**F) Image Overlay (download + select buttons):**
- `.prompt-image-overlay`: position absolute, top 0, right 0, padding 0.5rem, display flex, gap 0.35rem, opacity 0, transition opacity 0.2s
- `.prompt-image-slot:hover .prompt-image-overlay`: opacity 1
- `.btn-download, .btn-select`: width 32px, height 32px, border-radius 50%, display flex, align-items center, justify-content center, cursor pointer, border none, transition all 0.2s
- `.btn-download`: background `rgba(0,0,0,0.5)`, color white
- `.btn-download:hover`: background `rgba(0,0,0,0.7)`
- `.btn-download svg`: width 16px, height 16px
- `.btn-select`: background transparent, border `2px solid white`, color transparent
- `.btn-select svg`: width 16px, height 16px, opacity 0
- `.btn-select:hover`: background `rgba(255,255,255,0.3)`

**G) Selected State:**
- `.prompt-image-slot.is-selected .btn-select`: background white, border-color white, always visible (opacity 1 on overlay)
- `.prompt-image-slot.is-selected .btn-select svg`: opacity 1, color/stroke `var(--gray-800)`
- `.prompt-image-slot.is-selected .prompt-image-overlay`: opacity 1 (always show icons on selected image)
- `.prompt-image-slot.is-deselected`: opacity 0.35, transition opacity 0.3s
- `.prompt-image-slot.is-deselected:hover`: opacity 0.6 (slightly brighter on hover to indicate clickability)

**H) Image Fade-In:**
```css
.prompt-image-container img {
    animation: imageFadeIn 400ms ease-out;
}
@keyframes imageFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

### File 5: `prompts/templates/prompts/bulk_generator_job.html`

**Minimal changes:**
- Add `data-images-per-prompt="{{ job.images_per_prompt }}"` to the `#bulk-generator-job` root element
- That's it — gallery content is rendered by JS

---

## ♿ ACCESSIBILITY

1. **Image alt text:** Each generated image gets `alt="Generated image [slotIndex+1] for prompt [groupIndex+1]"`
2. **Download button:** `aria-label="Download image [slotIndex+1]"`
3. **Select button:** `aria-label="Select image [slotIndex+1]"` and `aria-pressed="true/false"`
4. **Prompt overlay:** The overlay is CSS-driven (`:hover`), also add `role="tooltip"` and wire `aria-describedby` on the truncated text pointing to the overlay ID
5. **Selection announcement:** When selection changes, update an `aria-live="polite"` region with "Image [X] selected for prompt [Y]"
6. **Keyboard:** Both overlay buttons reachable via Tab. Enter/Space triggers click. The overlay buttons should have `tabindex="0"` if not native buttons.
7. **Contrast:** All text `--gray-500` minimum. Overlay icons are white on dark semi-transparent background (sufficient contrast).

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] DOM nesting matches tree diagram — especially `.prompt-image-overlay` is INSIDE `.prompt-image-container`, not a sibling
- [ ] `icon-download` symbol added to sprite.svg with correct id
- [ ] No text using `--gray-400` or lighter
- [ ] `aria-label` on all overlay buttons
- [ ] Selection logic: only 1 selected per group, clicking selected deselects
- [ ] `{% block extras %}` NOT changed to anything else
- [ ] All tests pass

---

## 🤖 AGENT REQUIREMENTS

### Required Agents (Minimum 3)

**1. @django-pro**
- Task: Review status API changes (if any), image data in response
- Rating requirement: 8+/10

**2. @ui-visual-validator**
- Task: DOM structure matches tree diagram, CSS grid layout, hover overlays, selection states, responsive breakpoints
- Rating requirement: 8+/10

**3. @accessibility**
- Task: aria-labels, keyboard nav for overlay buttons, aria-pressed on select, aria-live announcement, tooltip role
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

- **UI Agent:** DOM nesting doesn't match tree diagram
- **UI Agent:** Image grid is not 4 columns
- **UI Agent:** Selection doesn't use radio-style (1 per group)
- **Accessibility Agent:** Overlay buttons missing aria-labels
- **Accessibility Agent:** No keyboard access to overlay buttons
- **Code Reviewer:** Prompt text overlay uses JavaScript when CSS `:hover` would suffice

---

## 🖥️ MANUAL BROWSER CHECK (Required)

**Test procedure:**

1. Create test GeneratedImage records in Django shell:
```python
from prompts.models import BulkGenerationJob, GeneratedImage

job = BulkGenerationJob.objects.first()
job.status = 'processing'
job.completed_count = 8
job.images_per_prompt = 2
job.save()

# Create 8 images (4 prompt groups × 2 images each)
# Use any public image URL for testing
test_url = 'https://picsum.photos/1024/1024'
for i in range(8):
    GeneratedImage.objects.create(
        job=job,
        prompt_text=f'A beautiful landscape with mountains and rivers in the golden hour light, photorealistic, 8k resolution, dramatic lighting, wide angle shot number {i+1}',
        order=i,
        status='completed',
        image_url=f'{test_url}?random={i}',
    )
```

2. Visit the job page, verify:
   - 4 prompt group rows visible
   - Each row: prompt #, truncated text, 2 images + 2 grey placeholders
   - Hover on prompt text → overlay shows full text
   - Hover on image → download + select icons appear
   - Click select → circle fills, others fade to 35%
   - Click download → image downloads
   - Responsive: shrink to 768px → 2 columns, 480px → 1 column

---

## 🧪 TESTING CHECKLIST

### Post-Implementation Testing

- [ ] Gallery rows render from polling data
- [ ] Correct grouping (images_per_prompt determines group boundaries)
- [ ] Grey placeholders for unfilled slots
- [ ] Selection: 1 per group, radio-style, fade effect
- [ ] Download triggers browser download
- [ ] Hover overlay shows full prompt text
- [ ] Responsive grid at all breakpoints
- [ ] No console errors
- [ ] `grep "icon-download" static/icons/sprite.svg` returns 1 match

### ⛔ FULL SUITE GATE

> Modified `views/` file? → YES (if status API changed) → Run `python manage.py test`
> Only JS/CSS/template? → Targeted tests sufficient

---

## 💾 COMMIT STRATEGY

```bash
git commit -m "feat(bulk-gen): Phase 5B — Gallery rows with image selection

- Prompt group rows render progressively during polling
- 4-column image grid per row with grey placeholders
- Uniform square containers with object-fit: contain
- Selection circle overlay — radio-style, 1 per group
- Download icon button per image (icon added to sprite)
- Non-selected images fade to 35% opacity
- Truncated prompt text with hover overlay for full text
- Per-group metadata line (dimensions, quality)
- Smooth entrance animation for new rows
- Responsive: 4→2→1 columns
- Accessible: aria-labels, keyboard nav, aria-pressed"
```

---

**END OF SPECIFICATION**
