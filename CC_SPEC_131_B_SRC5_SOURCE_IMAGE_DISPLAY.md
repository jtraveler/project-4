# CC_SPEC_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md
# SRC-5 — Prompt Detail: Admin Source Image Display + Lightbox

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 131
**Phase:** SRC-5
**Modifies UI/Templates:** YES
**Migration Required:** No — reads existing `prompt.b2_source_image_url` field (added in SRC-1, migration 0076)
**Agents Required:** 3 minimum
**Estimated Scope:** ~40 lines across 1 file (`prompt_detail.html`)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **Read this entire spec** before making any changes
5. **`prompt_detail.html` is 🟡 Caution (1,010 lines)** — use `str_replace` with 5+ line anchors only
6. **Template changes only** — no Python, no JS files, no CSS files, no migrations
7. **Staff-only** — this feature is completely invisible to non-staff users

---

## 📋 OVERVIEW

When a bulk-gen image is published, `prompt.b2_source_image_url` is populated with
the URL of the original source image the user supplied in the bulk generator
(added in SRC-4, Session 130D). Staff need to be able to view this source image
on the prompt detail page for moderation and audit purposes.

This spec adds:
1. A new **staff-only rail card** below the existing SOURCE / CREDIT card showing
   a thumbnail of the source image with a button to open a lightbox
2. A **Bootstrap modal lightbox** displaying the source image at full size

---

## 🎯 OBJECTIVES

- ✅ New `#source-image-card` rail card visible only to `user.is_staff AND prompt.b2_source_image_url`
- ✅ Card shows a small thumbnail (max 120px wide) with an "View Source Image" button
- ✅ Clicking button opens Bootstrap modal showing full-size source image
- ✅ Modal uses `modal-dialog modal-xl modal-dialog-centered` for large image display
- ✅ Modal image has appropriate `alt` text and `loading="lazy"`
- ✅ Card and modal follow existing DOM patterns exactly (rail-card, Bootstrap modal)
- ✅ Zero impact on non-staff users — guarded by `{% if user.is_staff and prompt.b2_source_image_url %}`
- ✅ `python manage.py check` passes

---

## 🔍 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm b2_source_image_url field name on Prompt model
grep -n "b2_source_image_url" prompts/models.py | head -5

# 2. Confirm existing source credit card anchor (insertion point)
grep -n "SOURCE / CREDIT\|source-credit-card\|source_credit" prompts/templates/prompts/prompt_detail.html

# 3. Confirm existing modal structure pattern
grep -n "modal fade\|modal-dialog\|modal-header\|modal-body" prompts/templates/prompts/prompt_detail.html | head -10

# 4. Confirm endblock content location
grep -n "endblock content\|block extras" prompts/templates/prompts/prompt_detail.html
```

**Do not proceed until greps are complete.**

---

## 🔧 STEP 1 — Add source image rail card to `prompt_detail.html`

**File:** `prompts/templates/prompts/prompt_detail.html`

**Insertion point:** Immediately AFTER the existing `{% endif %}` that closes the
SOURCE / CREDIT section (after `{% if user.is_staff and prompt.source_credit %}`
block), and BEFORE the `<!-- Prompt Text Card -->` comment.

**Current anchor (use for str_replace — copy exactly):**
```html
            {% endif %}

            <!-- Prompt Text Card -->
```

**Replace with:**
```html
            {% endif %}

            <!-- Source Image Card (staff-only, SRC-5) -->
            {% if user.is_staff and prompt.b2_source_image_url %}
            <div class="rail-card source-image-card" id="source-image-card">
                <h2 class="rail-card-title">Source Image</h2>
                <div class="source-image-content">
                    <img src="{{ prompt.b2_source_image_url }}"
                         alt="Source image for {{ prompt.title }}"
                         class="source-image-thumb"
                         loading="lazy"
                         style="max-width: 120px; border-radius: var(--radius-sm, 6px); display: block; margin-bottom: 0.5rem;">
                    <button type="button"
                            class="btn-outline-standard action-icon-btn"
                            data-bs-toggle="modal"
                            data-bs-target="#sourceImageModal"
                            aria-label="View full size source image for {{ prompt.title }}">
                        <svg class="icon icon-sm" aria-hidden="true"><use href="{% static 'icons/sprite.svg' %}#icon-zoom-in"/></svg>
                        View Source Image
                    </button>
                </div>
            </div>
            {% endif %}

            <!-- Prompt Text Card -->
```

---

## 🔧 STEP 2 — Add lightbox modal to `prompt_detail.html`

**File:** `prompts/templates/prompts/prompt_detail.html`

**Insertion point:** Immediately BEFORE `{% endblock content %}` (the line at the
very end of the content block, before `{% block extras %}`).

**Current anchor (use for str_replace — copy exactly):**
```html
{% endblock content %}

{% block extras %}
```

**Replace with:**
```html
{% if user.is_staff and prompt.b2_source_image_url %}
<!-- Source Image Lightbox Modal (staff-only, SRC-5) -->
<div class="modal fade" id="sourceImageModal" tabindex="-1"
     aria-labelledby="sourceImageModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="sourceImageModalLabel">Source Image</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body text-center p-2">
                <img src="{{ prompt.b2_source_image_url }}"
                     alt="Full size source image for {{ prompt.title }}"
                     class="img-fluid"
                     loading="lazy"
                     style="max-height: 80vh; object-fit: contain;">
            </div>
        </div>
    </div>
</div>
{% endif %}

{% endblock content %}

{% block extras %}
```

---

## 🏗️ DOM STRUCTURE

```
<!-- Right rail (existing) -->
├── .rail-card.source-credit-card   ← existing (staff-only, if source_credit)
├── .rail-card.source-image-card    ← NEW (staff-only, if b2_source_image_url)
│   ├── h2.rail-card-title "Source Image"
│   └── .source-image-content
│       ├── img.source-image-thumb  (max-width: 120px, inline style)
│       └── button[data-bs-toggle="modal"] "View Source Image"
└── .rail-card.prompt-card          ← existing

<!-- Modals (before endblock content) -->
├── #deleteModal                    ← existing
├── #reportModal                    ← existing
└── #sourceImageModal               ← NEW (staff-only, if b2_source_image_url)
    └── .modal-dialog.modal-xl.modal-dialog-centered
        └── .modal-content
            ├── .modal-header "Source Image" + close button
            └── .modal-body
                └── img.img-fluid (max-height: 80vh)
```

---

## ♿ ACCESSIBILITY

- The thumbnail `<img>` has `alt="Source image for {{ prompt.title }}"` — descriptive
- The lightbox button has `aria-label="View full size source image for {{ prompt.title }}"` — clear intent
- The modal `<img>` has `alt="Full size source image for {{ prompt.title }}"` — descriptive
- Bootstrap's modal handles focus trap and `aria-hidden` automatically
- `btn-close` has `aria-label="Close"` — matches existing modal pattern
- No additional ARIA roles needed — Bootstrap modal pattern is already accessible

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — `b2_source_image_url` field name confirmed
- [ ] Both template changes use `str_replace` with 5+ line anchors
- [ ] Rail card is inserted AFTER source-credit `{% endif %}` and BEFORE `<!-- Prompt Text Card -->`
- [ ] Modal is inserted BEFORE `{% endblock content %}` and AFTER existing modals
- [ ] Both blocks are wrapped in `{% if user.is_staff and prompt.b2_source_image_url %}`
- [ ] Modal uses `modal-xl modal-dialog-centered` (large, centered)
- [ ] Thumbnail `img` has `loading="lazy"` and inline `max-width: 120px`
- [ ] Modal `img` has `loading="lazy"`, `img-fluid`, and `max-height: 80vh`
- [ ] `data-bs-target="#sourceImageModal"` matches `id="sourceImageModal"` exactly
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+. Average must be ≥ 8.0.

### 1. @frontend-developer
- Verify modal trigger `data-bs-target` matches modal `id` exactly
- Verify `modal-xl modal-dialog-centered` classes are correct Bootstrap 5 pattern
- Verify thumbnail and modal image both have `loading="lazy"` and `alt` text
- Verify rail card insertion point is correct (after source-credit, before prompt-card)
- Rating requirement: 8+/10

### 2. @ux-ui-designer
- Verify thumbnail size (120px max-width) is appropriate for a rail card
- Verify "View Source Image" button uses `btn-outline-standard action-icon-btn` (matches existing copy button pattern)
- Verify modal provides enough space for large images (`modal-xl`, `80vh`)
- Rating requirement: 8+/10

### 3. @security-auditor
- Verify BOTH template blocks are guarded by `user.is_staff` — non-staff cannot see thumbnail OR trigger modal
- Verify `prompt.b2_source_image_url` is a CDN URL (not user-input) — no XSS risk from `src` attribute
- Verify no Django template variable is rendered unescaped (auto-escaping applies to all `{{ }}` here)
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Score MUST be below 6 if:
- Either block is missing the `user.is_staff` guard
- `data-bs-target` value does not exactly match modal `id`
- Modal is placed inside `{% block extras %}` instead of before `{% endblock content %}`
- Any template variable rendered with `|safe` without justification

---

## 🖥️ MANUAL BROWSER CHECK (REQUIRED)

After implementation, you (Mateo) must verify in the browser:

1. Log in as **staff** — navigate to any published prompt that has `b2_source_image_url` set
2. Verify "Source Image" rail card appears below the Source / Credit card
3. Verify thumbnail is visible (small, ~120px)
4. Click "View Source Image" — verify Bootstrap modal opens with full-size image
5. Verify modal closes with X button and Escape key
6. Log in as **non-staff user** — verify the Source Image card is completely invisible
7. Log in as **anonymous** — verify the Source Image card is completely invisible

⚠️ **Note:** For step 1, you'll need at least one Prompt in your dev DB that has `b2_source_image_url` populated. If none exist, you can set one manually via Django admin shell:
```python
from prompts.models import Prompt
p = Prompt.objects.filter(status=1).first()
p.b2_source_image_url = 'https://media.promptfinder.net/bulk-gen/test/test.jpg'
p.save()
```

---

## 🧪 TESTING

```bash
python manage.py check
```
Expected: 0 issues.

**No new automated tests required** — this is a template-only change with a `user.is_staff` guard. The security check (staff-only visibility) is verified by the browser test above and the @security-auditor agent review.

No full test suite run — runs once at end of session per protocol.

---

## 💾 COMMIT MESSAGE

```
feat(prompt-detail): SRC-5 staff-only source image display + lightbox
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

Include:
- Confirmation that `b2_source_image_url` field exists on Prompt model (from Step 0 grep)
- Browser test results (all 7 steps)
- Agent ratings table

---

**END OF SPEC**
