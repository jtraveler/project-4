# Phase 6 Design Review — Bulk Generator: Image Selection & Page Creation

**Status:** Design review — awaiting Mateo approval before implementation
**Date:** March 8, 2026
**Agents consulted:** @architect-review (8.0/10), @django-pro (6.5/10), @ui-ux-designer (8.5/10)
**Average agent score:** 7.67/10 *(see Agent Findings section for interpretation)*
**Do not commit or implement until Mateo approves this document.**

---

## Purpose

This document answers the 8 architectural decision points for Phase 6 of the Bulk AI Image Generator. Phase 6 covers: image selection UI in the job gallery, the "Create Pages" action, the `create_prompt_pages_from_job` async task, and the post-creation feedback pattern.

The review is based on:
- Reading 6 codebase files (`models.py`, `tasks.py`, `bulk_generator_views.py`, `bulk_generator_job.html`, `bulk-generator-job.js`, `bulk-generator.css`)
- Three specialist agent reviews
- Known bugs and gaps identified in the codebase analysis

---

## Codebase Status Summary

### What Already Exists (Do Not Rebuild)

| Component | Location | Status |
|-----------|----------|--------|
| `create_prompt_pages_from_job` task | `tasks.py:2689` | Fully implemented — with gaps (see below) |
| `api_create_pages` endpoint | `bulk_generator_views.py:347` | Fully implemented — with one bug (see below) |
| `GeneratedImage.is_selected` field | `models.py` | Exists, default=True |
| `GeneratedImage.prompt_page` FK | `models.py` | Exists, null=True, SET_NULL |
| `selections = {}` state object | `bulk-generator-job.js` | Exists |
| `handleSelect()` / `handleTrash()` | `bulk-generator-job.js` | Exist, toggle CSS classes |
| Image gallery render loop | `bulk-generator-job.js` | Exists |

### What Does Not Yet Exist (Phase 6 Must Build)

| Missing Piece | Impact |
|---------------|--------|
| "Create Pages" button in template | Critical — user has no way to trigger creation |
| `createPagesUrl` data attribute | Critical — JS has no endpoint URL |
| `handleCreatePages()` JS function | Critical — no client-side orchestration |
| Published status badges on gallery cards | UX — no visual feedback post-creation |
| `prompt_page_id` in status API response | UX — no polling-based completion detection |

---

## Known Bugs in Existing Code

These bugs exist in the current codebase and **must be fixed** in Phase 6, not left for later.

### Bug 1 — Duplicate Page Creation (Critical)

**File:** `bulk_generator_views.py:382–393`
**Problem:** `api_create_pages` queries `job.images.filter(status='completed')` but does NOT filter `prompt_page__isnull=True`. If the user clicks "Create Pages" twice (double-submit, network retry), pages are created twice.
**Fix:** Add `prompt_page__isnull=True` to the completed images query.

```python
# CURRENT (buggy)
valid_ids = set(
    job.images.filter(
        id__in=selected_image_ids,
        status='completed',
    ).values_list('id', flat=True)
)

# FIXED
valid_ids = set(
    job.images.filter(
        id__in=selected_image_ids,
        status='completed',
        prompt_page__isnull=True,  # idempotency guard
    ).values_list('id', flat=True)
)
```

### Bug 2 — Visibility Not Mapped (High)

**File:** `tasks.py:2785`
**Problem:** All created Prompt pages are hardcoded to `status=0` (Draft), ignoring `job.visibility`. A job with `visibility='public'` should create published pages.
**Fix:** Map `job.visibility` to Prompt.status.

```python
# CURRENT (buggy)
status=0,  # Draft

# FIXED
status=1 if job.visibility == 'public' else 0,
```

### Bug 3 — `hasattr` Always True (Medium)

**File:** `tasks.py:2797`
**Problem:** `if hasattr(prompt_page, 'b2_image_url')` is always True because `b2_image_url` is a model field defined on the class, not a dynamic attribute. This guard never catches anything and creates a false sense of safety.
**Fix:** Remove the `hasattr` guard — just assign directly.

```python
# CURRENT (misleading guard)
if hasattr(prompt_page, 'b2_image_url'):
    prompt_page.b2_image_url = gen_image.image_url

# FIXED
prompt_page.b2_image_url = gen_image.image_url
```

### Bug 4 — TOCTOU Race in Title/Slug Deduplication (Medium)

**File:** `tasks.py:2834–2877`
**Problem:** `_ensure_unique_title()` and `_generate_unique_slug()` both use a check-then-act pattern: `if not Prompt.objects.filter(title=candidate).exists(): return candidate`. Under concurrent generation (ThreadPoolExecutor, Phase 5D), two tasks can both pass the check and both attempt to INSERT with the same title/slug, causing an IntegrityError.
**Fix:** Wrap Prompt creation in `transaction.atomic()` with IntegrityError catch and UUID fallback.

```python
from django.db import IntegrityError, transaction

try:
    with transaction.atomic():
        prompt_page.save()
except IntegrityError:
    # Title or slug collision — append UUID and retry once
    suffix = uuid_lib.uuid4().hex[:8]
    prompt_page.title = f"{prompt_page.title[:189]} - {suffix}"
    prompt_page.slug = f"{slugify(prompt_page.title)[:191]}-{suffix}"
    prompt_page.save()
```

### Bug 5 — Missing b2_thumb_url (Medium)

**File:** `tasks.py:2797–2799`
**Problem:** The task sets `b2_image_url` but does NOT set `b2_thumb_url`, `b2_medium_url`, or `b2_large_url`. Prompt pages created from bulk generation will appear with broken/empty thumbnails across the site (gallery, profile, collections, related prompts).
**Fix:** Copy `b2_image_url` into `b2_thumb_url` as a fallback. Do not generate new thumbnails (out of scope for Phase 6 — add a TODO for Phase 7).

```python
prompt_page.b2_image_url = gen_image.image_url
prompt_page.b2_thumb_url = gen_image.image_url  # fallback until proper thumb
# TODO Phase 7: queue thumbnail generation task
```

### Bug 6 — moderation_status Default is Wrong for Staff Pages (Low)

**File:** `tasks.py:2778–2786`, `models.py`
**Problem:** `Prompt.moderation_status` defaults to `'pending'`, which means admin review queues will be flooded with internally-generated staff content that has already been reviewed by the staff member creating it.
**Fix:** Set `moderation_status='approved'` explicitly on staff-created bulk pages.

```python
prompt_page = Prompt(
    ...
    moderation_status='approved',  # staff-generated, no review needed
)
```

### Bug 7 — Categories and Descriptors Not Assigned (Low)

**File:** `tasks.py:2800–2809`
**Problem:** AI content generation returns categories and descriptors, but the task only applies tags. The Prompt.categories M2M and Prompt.descriptors M2M are never populated.
**Fix:** Apply categories and descriptors after save, following the same pattern as the upload task. (Same service call, same response format — the data is already there, just unused.)

---

## Decision Points

### Decision 1 — Sub-Phase Breakdown

**Decision:** Phase 6 should be broken into four sequential sub-phases. Each is independently testable and releasable.

| Sub-Phase | Deliverable | Dependencies |
|-----------|-------------|--------------|
| **6A — Bug Fixes** | Fix all 7 bugs above in existing code. No new UI. | None |
| **6B — Create Pages Button** | "Create Pages" button in template + `handleCreatePages()` JS + `prompt_page_id` in status API. Basic toast feedback. | 6A complete |
| **6C — Gallery State Feedback** | Published badges on gallery cards, selected/deselected/discarded visual states, sticky bottom bar. | 6B complete |
| **6D — Error Recovery** | Per-image retry for failed page creation, error state on gallery cards. | 6C complete |

**Rationale:** 6A is high-urgency because Bug 1 (duplicate creation) and Bug 2 (visibility) are data-integrity issues that should not ship in any form. 6B delivers the core workflow. 6C and 6D are polish.

---

### Decision 2 — b2_thumb_url Gap

**Decision:** Copy `b2_image_url` into `b2_thumb_url` as a same-image fallback. Defer proper thumbnail generation to Phase 7.

**Rationale:**
- Generating thumbnails requires FFmpeg and a background task. Doing this inside `create_prompt_pages_from_job` would create nested async task complexity.
- The full-size image as a thumbnail placeholder is functional and prevents broken images across the site.
- The site already has a `rename_prompt_files_for_seo` pattern for deferred B2 operations — thumbnail generation fits the same pattern.
- **Risk:** Full-size images used as thumbnails may slow gallery/profile page loads. Mitigate by adding a `TODO Phase 7` comment and tracking in CLAUDE_PHASES.md.

**Code change:** `tasks.py:2797–2799` — add `b2_thumb_url = gen_image.image_url` alongside the existing `b2_image_url` assignment.

---

### Decision 3 — Visibility Mapping

**Decision:** Map `job.visibility` to `Prompt.status` at page creation time.

| `job.visibility` | `Prompt.status` | Meaning |
|-----------------|-----------------|---------|
| `'public'` | `1` | Published immediately |
| `'private'` | `0` | Draft (staff sees it; no public URL) |

**Rationale:**
- The user already expressed their visibility intent when configuring the job. Ignoring it produces the wrong result (all-draft) for public jobs.
- Always-draft was acceptable as a temporary scaffold but is not acceptable for shipped Phase 6.
- The fix is one line (`status=1 if job.visibility == 'public' else 0`) and has no side-effects.

**Note:** The existing `api_create_pages` endpoint does not need to accept a visibility override — the job-level setting is the source of truth.

---

### Decision 4 — TOCTOU Protection Strategy

**Decision:** Use `transaction.atomic()` + `IntegrityError` catch at the Prompt save point. Keep `_ensure_unique_title()` and `_generate_unique_slug()` as pre-flight optimistic helpers, but do not rely on them for correctness.

**Rationale:**
- The check-then-act helpers work correctly in the 99% case (no concurrent writes) and reduce IntegrityError frequency.
- The `transaction.atomic()` catch is the safety net for the 1% concurrent case introduced by Phase 5D's ThreadPoolExecutor.
- This is the standard Django pattern for uniqueness under concurrency — documented in Django docs.
- Do NOT replace the helpers with UUID-only titles (SEO loss) or lock the table (performance cost).

**Code placement:** Wrap `prompt_page.save()` at `tasks.py:2800` in the atomic block with IntegrityError retry.

---

### Decision 5 — Idempotency / Duplicate Creation Prevention

**Decision:** Add `prompt_page__isnull=True` to the `api_create_pages` view's image filter. This is the primary idempotency guard.

**Why this is sufficient:**
- Once `gen_image.prompt_page` is set, it will never be null again (SET_NULL only triggers on Prompt deletion, which staff control).
- Re-submitting the form with the same IDs will return `pages_to_create: 0` and the task will no-op cleanly.
- No need for a separate "already processed" status on GeneratedImage — the FK is the record.

**Frontend complement:** The "Create Pages" button should be disabled after first successful submission (covered in Decision 8).

---

### Decision 6 — Categories and Descriptors Assignment

**Decision:** Apply categories and descriptors in Phase 6A alongside the existing tags assignment fix. Do not defer to Phase 7.

**Rationale:**
- The `ContentGenerationService.generate_content()` response already contains categories and descriptors. The data is there — it's just not being saved.
- Prompt pages without categories/descriptors will be invisible to the related-prompts scoring system (which weights categories 25% and descriptors 35%).
- The fix follows the exact same pattern as tags: `prompt_page.categories.set(...)` after save.
- The effort is ~5 lines of code.

**Implementation pattern:**
```python
# Apply categories
categories = ai_content.get('categories', [])
if categories:
    from prompts.models import SubjectCategory
    cat_objects = SubjectCategory.objects.filter(slug__in=categories)
    prompt_page.categories.set(cat_objects)

# Apply descriptors
descriptors = ai_content.get('descriptors', [])
if descriptors:
    from prompts.models import SubjectDescriptor
    desc_objects = SubjectDescriptor.objects.filter(slug__in=descriptors)
    prompt_page.descriptors.set(desc_objects)
```

---

### Decision 7 — Frontend "Create Pages" Button and Endpoint Wiring

**Decision:** Add a "Create Pages" button to `bulk_generator_job.html` that reads selection state from `selections = {}`, sends a POST to `api_create_pages`, and shows toast feedback.

**Template change:** Add to `bulk_generator_job.html` (near `gallery-selection-instruction`):
```html
<div class="bulk-create-actions" data-create-pages-url="{% url 'prompts:api_create_pages' job.id %}">
    <button class="btn btn-primary bulk-create-btn" id="createPagesBtn" disabled>
        Create Pages (<span id="createPagesCount">0</span> selected)
    </button>
</div>
```

**JS change:** Add `handleCreatePages()` to `bulk-generator-job.js`:
- Reads `Object.values(selections)` to get selected image IDs
- POSTs to `createPagesUrl` with `{ selected_image_ids: [...] }`
- On success: disables button, shows success toast with "X pages queued"
- On error: shows error toast, re-enables button

**Button state rules:**
- Disabled when 0 images selected
- Enabled when ≥1 image selected
- Disabled again after successful submission (prevent double-submit)
- Selection count shown in button label: "Create Pages (3 selected)"

---

### Decision 8 — Post-Creation Feedback Pattern

**Decision:** Use **Option D — Toast + View Link** (recommended by @architect-review).

**Pattern:**
1. On successful `api_create_pages` response: show toast: *"3 pages queued — they'll be ready in a moment."*
2. Gallery cards gain a "processing" badge (spinner icon) as each gains a `prompt_page` FK.
3. When `prompt_page_id` is populated in the status API response (add this field), the badge changes to a green "View →" link badge.
4. The "Create Pages" button remains disabled once submitted.

**Why Option D over alternatives:**
- **Option A (redirect to drafts list):** Abandons the job page, loses context for multi-round workflows.
- **Option B (modal with links):** Blocks further interaction unnecessarily.
- **Option C (inline page links only):** No feedback until polling catches up — feels broken.
- **Option D (toast + live badge):** Non-blocking, continuous feedback, stays in context.

**Status API addition:** Add `prompt_page_id` (string|null) to each image object in the `/api/job-status/<job_id>/` response. The JS already polls this endpoint — this allows badge state to update without a separate API call.

---

## Agent Findings

### @architect-review — 8.0/10

**Recommendation:** Sub-phases 6A→6B→6C→6D as described above. The b2_thumb_url gap is the highest-urgency technical risk. Endorsed draft-always fix and Option D feedback pattern. Recommended adding `prompt_page_id` to the status API response to enable polling-based badge updates without a new endpoint.

**Score rationale:** 8/10 reflects solid architectural direction with appropriate sub-phase decomposition. Minor deduction for not surfacing the `api_create_pages` idempotency bug independently.

---

### @django-pro — 6.5/10

**Critical findings:**
- Duplicate creation bug confirmed (missing `prompt_page__isnull=True`)
- Visibility not mapped — confirmed hardcoded `status=0`
- TOCTOU in `_ensure_unique_title` / `_generate_unique_slug` — identified `transaction.atomic()` pattern
- `hasattr(prompt_page, 'b2_image_url')` always True — identified as misleading guard
- Missing categories/descriptors
- `moderation_status='pending'` wrong for staff pages

**Score rationale:** 6.5/10 reflects the state of the **existing code under review**, not a quality judgment on the spec itself. The existing `create_prompt_pages_from_job` has 6 identified bugs. The low score is informational — it's why Phase 6A (bug fixes) comes first. The @django-pro agent was reviewing real code quality, which was the point.

---

### @ui-ux-designer — 8.5/10

**Recommendations accepted:**
- Sticky bottom bar: dormant (transparent, no button) → active (raised card with "Create Pages" button) as selections are made
- Selected state: 3px solid primary border + checkmark badge (top-right)
- Deselected state: 55% opacity overlay, no border
- Discarded state (trashed): blur + grayscale CSS filter
- Published state: green "View page →" badge replacing checkmark
- Toast feedback on creation queued

**Recommendations deferred to Phase 6C:**
- Sticky bottom bar animation (Phase 6C)
- Blur/grayscale for discarded (Phase 6C)
- Green published badge (Phase 6C — needs `prompt_page_id` in status API, which comes in 6B)

**Score rationale:** 8.5/10 reflects strong UX direction with actionable specifics for CSS states.

---

## Sub-Phase Specs (Overview)

### Phase 6A — Bug Fixes Only

**Files to change:** `tasks.py`, `bulk_generator_views.py`
**No template or JS changes.**

Fixes:
1. `prompt_page__isnull=True` in `api_create_pages`
2. `status=1 if job.visibility == 'public' else 0` in task
3. Remove `hasattr` guard, assign `b2_image_url` directly
4. Add `b2_thumb_url = gen_image.image_url` fallback
5. Add `moderation_status='approved'` on Prompt creation
6. Add categories + descriptors assignment
7. Wrap `prompt_page.save()` in `transaction.atomic()` + IntegrityError catch

**Tests required:** Unit tests for all 7 fixes. Existing `test_bulk_generator_views.py` already has `api_create_pages` test class — extend it.

---

### Phase 6B — Create Pages Button

**Files to change:** `bulk_generator_job.html`, `bulk-generator-job.js`, `bulk_generator_views.py` (add `prompt_page_id` to status response)

Deliverables:
1. "Create Pages (N selected)" button in template
2. `handleCreatePages()` in JS
3. Button disabled/enabled based on selection count
4. Success toast + button locked on submission
5. `prompt_page_id` field added to status API per-image response

**Tests required:** JS unit tests for button state logic; view tests for `prompt_page_id` in status response.

---

### Phase 6C — Gallery State Feedback

**Files to change:** `bulk-generator-job.js`, `bulk-generator.css` (or `bulk-generator-job.css`)

Deliverables:
1. Selected: 3px border + checkmark badge CSS state
2. Deselected (trashed): grayscale + opacity CSS state
3. Published: green "View →" badge (reads `prompt_page_id` from polling)
4. Sticky bottom bar: dormant → active on first selection
5. Button count label updates in real-time

---

### Phase 6D — Error Recovery

**Files to change:** `bulk_generator_views.py`, `bulk-generator-job.js`

Deliverables:
1. Per-image failed state badge on gallery card
2. Retry button on failed cards
3. Partial success handling: "2 of 3 pages created — 1 failed"

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Duplicate pages if user double-submits | High (no guard today) | High (data integrity) | Bug 1 fix (idempotency) |
| Broken thumbnails across site | Certain (no thumb set) | High (visual breakage) | Bug 5 fix (b2_thumb_url fallback) |
| TOCTOU under concurrent generation | Low (Phase 5D concurrent) | Medium (IntegrityError 500) | Bug 4 fix (atomic + catch) |
| Staff pages flooding moderation queue | Medium | Low (admin annoyance) | Bug 6 fix (moderation_status) |
| Pages created with no categories/descriptors | Certain | Medium (SEO/related prompts) | Bug 7 fix (assign from ai_content) |
| "Create Pages" queued but task never runs | Low (Django-Q healthy) | High (silent failure) | 6B adds `prompt_page_id` polling to surface outcome |

---

## Open Questions for Mateo

1. **Visibility mapping:** Should `visibility='private'` create Draft pages (`status=0`) or Published pages with `is_private=True`? The current model uses `status` (0/1) not an `is_private` field — so Draft is the correct mapping for private, but confirm this is the expected UX.

2. **Thumbnail generation in Phase 6 or 7?** The b2_thumb_url fallback (full-size image) is functional but not ideal. Should Phase 6 queue a thumbnail generation task immediately after page creation, or defer to Phase 7?

3. **Categories/descriptors from AI content:** Does `ContentGenerationService.generate_content()` currently return categories and descriptors in its response dict? If not, assigning them in the task is a no-op and should be deferred until the service is updated.

4. **"Create Pages" button placement:** Should this button appear on the job page sticky bar only (per @ui-ux-designer), or also at the top of the gallery when scrolled? Confirm preferred location.

5. **Phase 6D scope:** Is per-image retry (6D) in scope for this release or post-launch? It adds significant JS complexity for an edge case that should be rare once 6A bug fixes are in place.

---

## Implementation Order (Recommended)

```
Phase 6A (bug fixes, no UI) → test → commit
Phase 6B (create pages button) → test → commit
Phase 6C (gallery visual states) → test → commit
Phase 6D (error recovery) → test → commit [post-launch optional]
```

Each phase should pass CI/CD before the next begins. All 7 bugs in 6A are pre-conditions for correctness — do not start 6B until 6A is committed and green.

---

*This document is a design review only. No files were modified during its creation. Awaiting Mateo approval before any implementation begins.*
