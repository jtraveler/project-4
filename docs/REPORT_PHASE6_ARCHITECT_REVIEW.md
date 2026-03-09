# Phase 6 Architect Review Report -- Session 112

**Date:** March 8, 2026
**Session Type:** Design-Only Architect Review (No Code Changes)
**Feature:** Bulk AI Image Generator -- Phase 6: Image Selection and Page Creation
**Deliverable:** `PHASE6_DESIGN_REVIEW.md` (project root)
**Commits:** None

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Overview](#2-overview)
3. [Session Scope](#3-session-scope)
4. [Codebase Files Reviewed](#4-codebase-files-reviewed)
5. [Issues Found and Resolved During Review](#5-issues-found-and-resolved-during-review)
6. [Remaining Issues and Solutions](#6-remaining-issues-and-solutions)
7. [Concerns and Risks](#7-concerns-and-risks)
8. [Areas for Improvement](#8-areas-for-improvement)
9. [Agent Ratings -- Detailed](#9-agent-ratings----detailed)
10. [Additional Recommended Agents](#10-additional-recommended-agents)
11. [What Was Improved](#11-what-was-improved)
12. [Expectations vs. Reality](#12-expectations-vs-reality)
13. [How to Test the Results](#13-how-to-test-the-results)
14. [What to Work On Next](#14-what-to-work-on-next)
15. [Commits Made](#15-commits-made)
16. [Appendix](#16-appendix)

---

## 1. Executive Summary

Session 112 conducted a design-only architect review of the Phase 6 scaffolding code for the Bulk AI Image Generator's "Image Selection and Page Creation" pipeline. Three specialist agents (@architect-review, @django-pro, @ui-ux-designer) were consulted. The review surfaced **7 bugs** in the existing task and endpoint code -- all written during earlier phases but never exercised in production because no frontend trigger exists yet.

The most critical finding is a **duplicate page creation bug** in `api_create_pages` that would create duplicate `Prompt` records on double-submit. Additional bugs include missing thumbnail URLs (causing broken images across every template that renders bulk-created pages), hardcoded Draft status ignoring the job's visibility setting, a misleading `hasattr` guard that always evaluates to `True`, a TOCTOU race condition in title/slug deduplication, wrong moderation status defaults, and missing category/descriptor M2M assignments.

No code was changed. The session produced `PHASE6_DESIGN_REVIEW.md` containing 8 architectural decision points, 7 bug fixes with exact code, a 4-sub-phase breakdown (6A through 6D), a risk register, and 5 open questions for the project owner.

**Key outcome:** Phase 6A (bug fixes) must be completed before any UI work begins. The bugs affect data integrity, not just presentation.

---

## 2. Overview

### What is Phase 6?

Phase 6 is the "Image Selection and Page Creation" phase of the Bulk AI Image Generator, a staff-only tool accessible at `/tools/bulk-ai-generator/`. The tool generates AI images in bulk using OpenAI GPT-Image-1 with a BYOK (Bring Your Own Key) model. Phases 1 through 5D handled input UI, job orchestration, image generation, gallery rendering, and concurrent generation. Phase 6 closes the loop by allowing staff to:

1. **Select** which generated images to publish (from the gallery rendered in Phase 5B).
2. **Trigger page creation** -- converting selected `GeneratedImage` records into `Prompt` model instances with AI-generated titles, descriptions, tags, categories, and descriptors.
3. **Receive visual feedback** on which pages were created and navigate to them.

### Why a Design Review?

The Phase 6 scaffolding code -- the `create_prompt_pages_from_job` task and `api_create_pages` endpoint -- was written during Phase 4 (Session 93) as forward-looking infrastructure. It was never connected to the frontend because:

- No "Create Pages" button exists in the job progress template.
- No `handleCreatePages()` function exists in the gallery JS.
- No `createPagesUrl` data attribute wires the JS to the endpoint.

Before building the UI layer (Phases 6B-6D), this review examined the scaffolding for correctness, finding 7 bugs that would have shipped silently into production without this step.

### What Was Reviewed

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Page creation task | `prompts/tasks.py` | 2689-2877 | `create_prompt_pages_from_job` + helper functions |
| Create pages endpoint | `prompts/views/bulk_generator_views.py` | 347-419 | `api_create_pages` API view |
| Data models | `prompts/models.py` | 2836-2995 | `BulkGenerationJob`, `GeneratedImage` |
| Prompt model | `prompts/models.py` | 711-1500+ | `Prompt` fields, B2 media, moderation |
| Job progress template | `prompts/templates/prompts/bulk_generator_job.html` | Full file | Gallery HTML structure |
| Gallery JS | `static/js/bulk-generator-job.js` | Full file | Selection state, gallery rendering |
| Gallery CSS | `static/css/pages/bulk-generator.css` | Full file | Gallery card styles |

---

## 3. Session Scope

### In Scope

| Item | Description |
|------|-------------|
| Architecture review | Examine `create_prompt_pages_from_job` task for correctness |
| Endpoint review | Examine `api_create_pages` for idempotency, validation, error handling |
| Model field audit | Verify all required Prompt fields are populated during page creation |
| Frontend gap analysis | Identify what JS/HTML/CSS is missing for a functional Phase 6 |
| Sub-phase decomposition | Break Phase 6 into implementable sub-phases |
| Decision documentation | Record architectural decisions with rationale |
| Bug documentation | Document all bugs with exact file locations and fixes |

### Out of Scope

| Item | Reason |
|------|--------|
| Code changes | This is a review-only session; bugs are documented, not fixed |
| Commits | Nothing was committed; the review document requires owner approval first |
| UI implementation | Phases 6B-6D are planned but not started |
| Thumbnail generation | Deferred to Phase 7 per architect recommendation |
| Test writing | Tests will accompany the 6A bug fix phase |
| Production deployment | Pre-launch; no production impact |

---

## 4. Codebase Files Reviewed

### 4.1 `prompts/tasks.py` (Lines 2689-2877)

**Why it was reviewed:** This file contains the core page creation logic -- the `create_prompt_pages_from_job` function that converts `GeneratedImage` records into `Prompt` instances. It also contains two helper functions (`_ensure_unique_title` and `_generate_unique_slug`) that handle deduplication.

**What was found:**
- 5 of the 7 bugs are in this file
- The task structure is sound (error handling, logging, return value format) but field assignment is incomplete
- The `hasattr` guard on line 2797 is a dead code pattern -- `b2_image_url` is a declared model field, so `hasattr` always returns `True`
- Title/slug deduplication uses a check-then-act pattern vulnerable to TOCTOU races under concurrent execution (Phase 5D introduced `ThreadPoolExecutor`)
- Categories and descriptors from the AI content response are never applied to the created Prompt

### 4.2 `prompts/views/bulk_generator_views.py` (Lines 347-419)

**Why it was reviewed:** This file contains the `api_create_pages` endpoint that receives the selected image IDs from the frontend and queues the page creation task.

**What was found:**
- Bug 1 (duplicate page creation) is here -- the filter on line 382-388 queries `status='completed'` but does not exclude images that already have a `prompt_page` linked, meaning a double-submit creates duplicate Prompt pages
- Job ownership validation is correctly implemented (line 374)
- Input validation is present but could be tighter (no UUID format validation on individual IDs)
- The endpoint correctly uses `async_task` for background processing

### 4.3 `prompts/models.py` -- BulkGenerationJob (Lines 2836-2939)

**Why it was reviewed:** To understand the job configuration fields, especially `visibility` which maps to Prompt `status` during page creation.

**Key fields relevant to Phase 6:**

| Field | Type | Default | Phase 6 Impact |
|-------|------|---------|----------------|
| `visibility` | CharField | `'public'` | Should map to Prompt `status` (0=Draft, 1=Published) |
| `generator_category` | CharField | `'ChatGPT'` | Passed to `ContentGenerationService.generate_content()` |
| `created_by` | ForeignKey(User) | Required | Becomes `Prompt.author` |

### 4.4 `prompts/models.py` -- GeneratedImage (Lines 2941-2995)

**Why it was reviewed:** To understand the selection mechanism and the link to created Prompt pages.

**Key fields relevant to Phase 6:**

| Field | Type | Default | Phase 6 Impact |
|-------|------|---------|----------------|
| `is_selected` | BooleanField | `True` | Tracks user selection in gallery |
| `prompt_page` | ForeignKey(Prompt) | `null=True` | FK to created Prompt; also serves as idempotency record |
| `image_url` | URLField | blank | Source URL for B2 image assignment |
| `source_credit` | CharField | blank | Parsed and applied to Prompt |

### 4.5 `prompts/models.py` -- Prompt (Lines 711-1500+)

**Why it was reviewed:** To audit which fields must be populated during page creation and which have defaults that may cause problems.

**Critical fields identified:**

| Field | Default | Problem |
|-------|---------|---------|
| `status` | `0` (Draft) | Task hardcodes `status=0` regardless of `job.visibility` |
| `moderation_status` | `'pending'` | Staff-created pages should be `'approved'` |
| `b2_image_url` | blank | Set correctly (modulo `hasattr` noise) |
| `b2_thumb_url` | blank | Never set -- causes broken thumbnails site-wide |
| `b2_medium_url` | blank | Never set -- causes broken medium-size images |

### 4.6 `static/js/bulk-generator-job.js`

**Why it was reviewed:** To understand the existing selection state management and identify what frontend code is missing.

**Existing infrastructure:**

| Component | Status | Location |
|-----------|--------|----------|
| `selections = {}` | Exists | Line 54 -- tracks `{ groupIndex: imageId }` |
| `handleSelection(e)` | Exists | Line 788 -- toggles selection state per gallery card |
| `handleTrash(e)` | Exists | Line 835 -- soft-deletes (dims) a gallery card |
| Gallery render loop | Exists | Renders cards with select/trash buttons |
| `handleCreatePages()` | Missing | No function to collect selections and POST to endpoint |
| `createPagesUrl` | Missing | No data attribute wiring JS to API endpoint |

### 4.7 Templates and CSS

The job progress template (`bulk_generator_job.html`) and gallery CSS (`bulk-generator.css`) were reviewed for completeness. The template renders gallery cards correctly but has no "Create Pages" button or sticky action bar. CSS has card styles but no published/selected/discarded visual states beyond basic opacity.

---

## 5. Issues Found and Resolved During Review

**Clarification:** "Resolved" here means the bugs were **identified, documented, and assigned to Phase 6A with exact fixes**. No code was changed during this session. The resolution is the design document itself, which provides implementation-ready patches.

### Summary Table

| Bug | Severity | File | Line(s) | Status |
|-----|----------|------|---------|--------|
| 1. Duplicate page creation | Critical | `bulk_generator_views.py` | 382-388 | Documented, fix specified |
| 2. Visibility not mapped | High | `tasks.py` | 2785 | Documented, fix specified |
| 3. `hasattr` always True | Medium | `tasks.py` | 2797 | Documented, fix specified |
| 4. TOCTOU race in dedup | Medium | `tasks.py` | 2834-2877 | Documented, fix specified |
| 5. Missing `b2_thumb_url` | Medium | `tasks.py` | 2797-2799 | Documented, fix specified |
| 6. Wrong `moderation_status` | Low | `tasks.py` | 2778-2786 | Documented, fix specified |
| 7. Missing categories/descriptors | Low | `tasks.py` | 2800-2809 | Documented, fix specified |

### How Each Was Identified

- **Bugs 1, 2, 3, 5, 6, 7** were identified by @django-pro through systematic field-by-field audit of the Prompt model against the task's field assignments.
- **Bug 4** was identified by @architect-review, noting the interaction between `_ensure_unique_title`/`_generate_unique_slug` and Phase 5D's `ThreadPoolExecutor` concurrency model.
- **Bug 1** was independently flagged by both @architect-review and @django-pro.

---

## 6. Remaining Issues and Solutions

All 7 bugs remain unfixed in code. Each is presented below with the exact fix to apply during Phase 6A.

### Bug 1 -- Duplicate Page Creation (Critical)

**File:** `prompts/views/bulk_generator_views.py`
**Lines:** 382-393
**Impact:** If a staff member double-clicks "Create Pages" or the browser retries the POST, duplicate `Prompt` records are created for the same `GeneratedImage`. This corrupts the content database and creates duplicate pages in search indexes.

**Root cause:** The filter on line 382-388 selects `GeneratedImage` records with `status='completed'` but does not check whether a `prompt_page` has already been linked. Since `prompt_page` is set by the task (not the endpoint), the endpoint has no way to know a task is already running for the same images.

**Current code (`bulk_generator_views.py:382-388`):**

```python
valid_ids = set(
    job.images.filter(
        id__in=selected_image_ids,
        status='completed',
    ).values_list('id', flat=True)
)
```

**Fixed code:**

```python
valid_ids = set(
    job.images.filter(
        id__in=selected_image_ids,
        status='completed',
        prompt_page__isnull=True,  # idempotency guard
    ).values_list('id', flat=True)
)
```

**Why this works:** The `prompt_page` FK is set to the created `Prompt` at the end of each per-image loop iteration in the task (`gen_image.prompt_page = prompt_page` at line 2808). Once set, subsequent submissions for the same image will be filtered out. The FK serves double duty as both the link and the idempotency record.

**Edge case:** If the task is still running (FK not yet set), a second submit could still queue duplicates. To fully close this gap, also add a check in the task itself:

```python
# In create_prompt_pages_from_job, before processing each image
for gen_image in selected_images:
    if gen_image.prompt_page is not None:
        continue  # Already processed (idempotency)
```

---

### Bug 2 -- Visibility Not Mapped (High)

**File:** `prompts/tasks.py`
**Line:** 2785
**Impact:** All bulk-created pages are Drafts regardless of the job's visibility setting. Staff who select "Public" visibility in the bulk generator input form expect their pages to be published immediately after creation. Instead, every page requires manual publication through the admin.

**Root cause:** The task hardcodes `status=0` (Draft) on line 2785 without consulting `job.visibility`.

**Current code (`tasks.py:2785`):**

```python
status=0,  # Draft
```

**Fixed code:**

```python
status=1 if job.visibility == 'public' else 0,
```

**Model reference:** The `Prompt.STATUS` choices are defined at `models.py:663`:
```python
STATUS = ((0, "Draft"), (1, "Published"))
```

The `BulkGenerationJob.VISIBILITY_CHOICES` are defined at `models.py:2856-2859`:
```python
VISIBILITY_CHOICES = [
    ('public', 'Public'),
    ('private', 'Private'),
]
```

**Open question for Mateo:** Does `visibility='private'` map to Draft (`status=0`), or should it map to Published with some `is_private` flag? The current `Prompt` model uses `status` (integer) for visibility, not a separate boolean. The fix above assumes private means Draft.

---

### Bug 3 -- `hasattr` Always True (Medium)

**File:** `prompts/tasks.py`
**Line:** 2797
**Impact:** No functional impact (the assignment works correctly), but the guard is misleading. Future developers may assume it serves a purpose or copy the pattern elsewhere.

**Root cause:** `b2_image_url` is a declared `URLField` on the `Prompt` model (`models.py:899`). Python's `hasattr()` returns `True` for all declared model fields, whether or not they have a value. The guard was likely written defensively during early scaffolding when the field's presence on the model was uncertain.

**Current code (`tasks.py:2797-2798`):**

```python
if hasattr(prompt_page, 'b2_image_url'):
    prompt_page.b2_image_url = gen_image.image_url
```

**Fixed code:**

```python
prompt_page.b2_image_url = gen_image.image_url
```

**Additional context:** The same pattern does not appear for `b2_thumb_url` or `b2_medium_url`, which is part of Bug 5.

---

### Bug 4 -- TOCTOU Race in Deduplication (Medium)

**File:** `prompts/tasks.py`
**Lines:** 2834-2877 (`_ensure_unique_title` and `_generate_unique_slug`)
**Impact:** Under concurrent execution (Phase 5D introduced `ThreadPoolExecutor` with configurable `max_workers`), two tasks processing images from the same job can both call `_ensure_unique_title` with the same AI-generated title. Both check `Prompt.objects.filter(title=candidate).exists()`, both get `False`, both proceed to `prompt_page.save()`, and one hits an `IntegrityError` if `title` has a unique constraint.

**Root cause:** Classic check-then-act (TOCTOU) pattern. The `exists()` check and the `save()` are not atomic.

**Current code (`tasks.py:2844-2852`):**

```python
for attempt in range(max_retries):
    candidate = title if attempt == 0 else (
        f"{title[:189]} - {uuid_lib.uuid4().hex[:8]}"
    )
    if not Prompt.objects.filter(title=candidate).exists():
        return candidate

# Final fallback with UUID (virtually guaranteed unique)
return f"{title[:189]} - {uuid_lib.uuid4().hex[:8]}"
```

**Fixed code -- wrap `save()` in `transaction.atomic()` with `IntegrityError` retry:**

```python
from django.db import IntegrityError, transaction

# In create_prompt_pages_from_job, replace the save block:
try:
    with transaction.atomic():
        prompt_page.save()
except IntegrityError:
    # Title or slug collision under concurrent execution
    import uuid as uuid_lib
    prompt_page.title = f"{prompt_page.title[:189]} - {uuid_lib.uuid4().hex[:8]}"
    prompt_page.slug = f"{prompt_page.slug[:180]}-{uuid_lib.uuid4().hex[:8]}"
    prompt_page.save()
```

**Why `transaction.atomic()` instead of `select_for_update`:** The race is between INSERT operations (new Prompt creation), not UPDATE operations on existing rows. `select_for_update` cannot lock rows that do not yet exist. The standard Django pattern for insert-or-retry is `transaction.atomic()` with `IntegrityError` catch.

**Note:** The existing helper functions (`_ensure_unique_title`, `_generate_unique_slug`) still have value for the common case. The `transaction.atomic()` wrapper is a safety net for the rare concurrent collision.

---

### Bug 5 -- Missing `b2_thumb_url` (Medium)

**File:** `prompts/tasks.py`
**Lines:** 2797-2799
**Impact:** Every bulk-created Prompt page will have a broken thumbnail across the entire site. The `display_thumb_url` property (`models.py:1351-1354`) checks `b2_thumb_url` first, then falls back to `b2_video_thumb_url`, then Cloudinary. Since bulk-generated images have no Cloudinary fallback and no video thumbnail, the property returns `None`. Every template that uses `{{ prompt.display_thumb_url }}` -- homepage cards, profile grids, related prompts, collection thumbnails -- will render a broken `<img>` tag.

**Root cause:** The task sets `b2_image_url` but never sets `b2_thumb_url` or `b2_medium_url`.

**Current code (`tasks.py:2797-2798`):**

```python
if hasattr(prompt_page, 'b2_image_url'):
    prompt_page.b2_image_url = gen_image.image_url
```

**Fixed code (Phase 6A -- immediate fallback):**

```python
prompt_page.b2_image_url = gen_image.image_url
prompt_page.b2_thumb_url = gen_image.image_url   # fallback until real thumbnails
prompt_page.b2_medium_url = gen_image.image_url   # fallback until real thumbnails
```

**Why copy the full-size URL as fallback:** Serving the original image for thumbnails is suboptimal (larger file size) but functionally correct. All templates will render the image instead of a broken placeholder. Real thumbnail generation (resize to 300x300 and upload to B2) is deferred to Phase 7 per the architect recommendation.

**Phase 7 fix (deferred):** After `prompt_page.save()`, queue a background task to generate actual thumbnails:

```python
# Phase 7 -- not Phase 6
from django_q.tasks import async_task
async_task(
    'prompts.tasks.generate_thumbnails_for_prompt',
    prompt_page.id,
    task_name=f'thumbs-{prompt_page.id}',
)
```

---

### Bug 6 -- Wrong `moderation_status` (Low)

**File:** `prompts/tasks.py`
**Lines:** 2778-2786
**Impact:** All bulk-created Prompt pages inherit the `Prompt` model's default `moderation_status='pending'` (`models.py:866`). This means staff-created pages -- which have already passed through GPT-Image-1's built-in content policy -- appear in the admin moderation review queue alongside user-uploaded content. This creates unnecessary review work and dilutes the moderation queue's signal.

**Root cause:** The `Prompt()` constructor on lines 2778-2786 does not set `moderation_status`.

**Current code (`tasks.py:2778-2786`):**

```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator=job.generator_category,
    status=0,  # Draft
)
```

**Fixed code:**

```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator=job.generator_category,
    status=1 if job.visibility == 'public' else 0,  # Bug 2 fix
    moderation_status='approved',  # Bug 6 fix: staff-created, already moderated
)
```

**Rationale:** GPT-Image-1 applies its own content policy during generation. Images that violate policy are rejected at generation time (the image never exists). By the time an image reaches the page creation pipeline, it has already been moderated by the provider. Setting `moderation_status='approved'` reflects this reality.

---

### Bug 7 -- Missing Categories and Descriptors (Low)

**File:** `prompts/tasks.py`
**Lines:** 2800-2809
**Impact:** Bulk-created Prompt pages have no categories or descriptors assigned, even when the `ContentGenerationService.generate_content()` response includes them. This degrades the related prompts scoring algorithm (which weights categories at 25% and descriptors at 35%) and reduces SEO coverage.

**Root cause:** The task applies tags (lines 2802-2805) but does not apply categories or descriptors from the AI content response.

**Current code (`tasks.py:2802-2809`):**

```python
# Apply tags if available
tags = ai_content.get('suggested_tags', [])
if tags and hasattr(prompt_page, 'tags'):
    prompt_page.tags.add(*tags[:10])

# Link generated image to prompt page
gen_image.prompt_page = prompt_page
gen_image.save(update_fields=['prompt_page'])
```

**Fixed code:**

```python
# Apply tags if available
tags = ai_content.get('suggested_tags', [])
if tags:
    prompt_page.tags.add(*tags[:10])

# Apply categories if available
categories = ai_content.get('categories', [])
if categories:
    from prompts.models import SubjectCategory
    cat_objects = SubjectCategory.objects.filter(
        slug__in=[slugify(c) for c in categories]
    )
    if cat_objects.exists():
        prompt_page.categories.set(cat_objects)

# Apply descriptors if available
descriptors = ai_content.get('descriptors', [])
if descriptors:
    from prompts.models import SubjectDescriptor
    desc_objects = SubjectDescriptor.objects.filter(
        slug__in=[slugify(d) for d in descriptors]
    )
    if desc_objects.exists():
        prompt_page.descriptors.set(desc_objects)

# Link generated image to prompt page
gen_image.prompt_page = prompt_page
gen_image.save(update_fields=['prompt_page'])
```

**Open question:** This fix assumes `ContentGenerationService.generate_content()` returns `categories` and `descriptors` keys in its response dictionary. The upload path (`tasks.py` AI content generation) does return these, but the bulk generation path may use a different code path. This needs verification before implementation. If the service does not return these keys, the fix is a safe no-op (empty lists), but the service should be updated to include them.

**Note:** The `hasattr(prompt_page, 'tags')` guard (line 2804) was also removed in the fix. Like Bug 3, `tags` is a `TaggableManager` declared on the model and `hasattr` always returns `True`.

---

## 7. Concerns and Risks

### 7.1 Critical Risk: `b2_thumb_url` Gap

**Risk level:** Critical
**Probability:** 100% (will occur on every bulk-created page)
**Impact:** Broken thumbnail images across the entire site wherever bulk-created pages appear

The `display_thumb_url` property on the Prompt model (`models.py:1351-1354`) follows a strict fallback chain:

```
b2_thumb_url  -->  b2_video_thumb_url  -->  Cloudinary thumbnail  -->  None
```

Bulk-generated images have:
- No `b2_thumb_url` (Bug 5)
- No `b2_video_thumb_url` (not a video)
- No Cloudinary fallback (Cloudinary is legacy infrastructure)

Result: `display_thumb_url` returns `None`. Every `<img src="{{ prompt.display_thumb_url }}">` tag renders as a broken image icon.

**Mitigation:** Bug 5 fix (copy `image_url` to `b2_thumb_url` as fallback) must ship in Phase 6A before any pages are created.

### 7.2 High Risk: Duplicate Page Creation

**Risk level:** High
**Probability:** Medium (depends on network conditions and user behavior)
**Impact:** Duplicate Prompt records in database, duplicate pages in search index

The "Create Pages" button will be clicked by staff members. Common scenarios that trigger double-submit:
- Slow network: user clicks again thinking the first click did not register
- Browser retry: some browsers retry POST requests on timeout
- Tab duplication: user opens same page in two tabs

**Mitigation:** Bug 1 fix (add `prompt_page__isnull=True` filter) plus a client-side guard (disable button after first click, show loading state).

### 7.3 Medium Risk: TOCTOU Under Concurrent Execution

**Risk level:** Medium
**Probability:** Low (requires two images with identical AI-generated titles processed concurrently)
**Impact:** `IntegrityError` crashes the task for one image; the other succeeds

Phase 5D introduced `ThreadPoolExecutor` for concurrent image generation. If the page creation task is also parallelized (or if two separate jobs run simultaneously), the title/slug deduplication helpers are vulnerable to TOCTOU races.

**Mitigation:** Bug 4 fix (`transaction.atomic()` + `IntegrityError` catch) handles this at the database level. The existing retry-with-UUID-suffix logic in the helper functions handles the common case; the transaction wrapper handles the race.

### 7.4 Low Risk: `ContentGenerationService` Response Shape

**Risk level:** Low
**Probability:** Unknown (depends on service implementation)
**Impact:** Bug 7 fix (categories/descriptors) becomes a no-op if the service does not return these keys

The `ContentGenerationService.generate_content()` method is called with `image_url`, `prompt_text`, and `ai_generator`. The upload path in `tasks.py` extracts `categories` and `descriptors` from the response and writes them to cache. It is unclear whether the same keys are present when the service is called from the bulk generation context (different prompt format, different temperature settings).

**Mitigation:** Verify the service response shape before implementing Bug 7 fix. If keys are missing, update the service first.

### 7.5 Risk Register Summary

| ID | Risk | Likelihood | Impact | Mitigation | Phase |
|----|------|-----------|--------|------------|-------|
| R1 | Broken thumbnails on all bulk pages | Certain | Critical | Bug 5 fix: copy image_url to b2_thumb_url | 6A |
| R2 | Duplicate Prompt records on double-submit | Medium | High | Bug 1 fix + client-side button disable | 6A + 6B |
| R3 | IntegrityError on concurrent title collision | Low | Medium | Bug 4 fix: transaction.atomic() wrapper | 6A |
| R4 | Staff moderation queue flooded with auto-approved pages | Certain | Low | Bug 6 fix: set moderation_status='approved' | 6A |
| R5 | ContentGenerationService missing categories/descriptors | Unknown | Low | Verify service response before Bug 7 fix | 6A |
| R6 | Visibility mapping unclear for 'private' | Unknown | Medium | Open question for Mateo | 6A |

---

## 8. Areas for Improvement

### 8.1 Idempotency in the Endpoint

**Current state:** The `api_create_pages` endpoint has no idempotency protection. A double-POST creates duplicate tasks.

**Improvement -- add `prompt_page__isnull=True` to the filter:**

```python
# prompts/views/bulk_generator_views.py, line 382-388
valid_ids = set(
    job.images.filter(
        id__in=selected_image_ids,
        status='completed',
        prompt_page__isnull=True,  # ADD THIS
    ).values_list('id', flat=True)
)
```

**Additional improvement -- return early if no valid IDs remain:**

```python
if not valid_ids:
    return JsonResponse({
        'status': 'already_created',
        'pages_to_create': 0,
        'message': 'All selected images already have pages created.',
    })
```

### 8.2 Field Assignment Completeness

**Current state:** The Prompt constructor on `tasks.py:2778-2786` sets 7 fields. A complete Prompt for site-wide rendering requires at least 11.

**Improvement -- complete field assignment:**

```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator=job.generator_category,
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',
    b2_image_url=gen_image.image_url,        # was behind hasattr guard
    b2_thumb_url=gen_image.image_url,         # NEW: fallback thumbnail
    b2_medium_url=gen_image.image_url,        # NEW: fallback medium
)
```

### 8.3 Task-Level Idempotency

**Current state:** The task iterates over `selected_images` without checking if `prompt_page` is already set on each image.

**Improvement -- add per-image skip:**

```python
for gen_image in selected_images:
    if gen_image.prompt_page is not None:
        logger.info(
            "Skipping image %d.%d — already has prompt page %s",
            gen_image.prompt_order, gen_image.variation_number,
            gen_image.prompt_page_id,
        )
        continue
```

### 8.4 Dead Code Removal

**Current state:** Two `hasattr` guards that always evaluate to `True`.

**Improvement -- remove both guards:**

```python
# Line 2797: Remove hasattr guard on b2_image_url
# Before:
if hasattr(prompt_page, 'b2_image_url'):
    prompt_page.b2_image_url = gen_image.image_url
# After:
prompt_page.b2_image_url = gen_image.image_url

# Line 2804: Remove hasattr guard on tags
# Before:
if tags and hasattr(prompt_page, 'tags'):
    prompt_page.tags.add(*tags[:10])
# After:
if tags:
    prompt_page.tags.add(*tags[:10])
```

### 8.5 Status API Enhancement

**Current state:** The job status API (`api_bulk_job_status`) returns job-level and image-level data but does not include `prompt_page_id` for individual images.

**Improvement -- add `prompt_page_id` to image serialization:**

This enables the frontend to poll for page creation completion and display "View page" badges on gallery cards without a new endpoint.

```python
# In the status API image serialization (bulk_generator_views.py)
# Add to each image dict:
'prompt_page_id': str(img.prompt_page_id) if img.prompt_page_id else None,
'prompt_page_url': (
    reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})
    if img.prompt_page else None
),
```

### 8.6 Error Reporting Granularity

**Current state:** The task returns `errors` as a flat list of truncated strings. No structure to identify which image failed or why.

**Improvement -- structured error reporting:**

```python
errors.append({
    'image_id': str(gen_image.id),
    'prompt_order': gen_image.prompt_order,
    'variation_number': gen_image.variation_number,
    'error': str(e)[:200],
})
```

### 8.7 Transaction Safety on `save()`

**Current state:** `prompt_page.save()` on line 2800 is not wrapped in a transaction. Under concurrent execution, IntegrityError can crash the entire task loop.

**Improvement -- wrap in `transaction.atomic()` with retry:**

```python
from django.db import IntegrityError, transaction

try:
    with transaction.atomic():
        prompt_page.save()
except IntegrityError:
    import uuid as uuid_lib
    suffix = uuid_lib.uuid4().hex[:8]
    prompt_page.title = f"{prompt_page.title[:189]} - {suffix}"
    prompt_page.slug = f"{prompt_page.slug[:180]}-{suffix}"
    prompt_page.save()
```

---

## 9. Agent Ratings -- Detailed

### 9.1 @architect-review -- Score: 8.0/10

**Focus:** System-level architecture, sub-phase decomposition, risk identification, integration points.

**What the agent found:**

| Finding | Category | Severity |
|---------|----------|----------|
| Sub-phase decomposition (6A-6D) | Architecture | Recommendation |
| `b2_thumb_url` gap as highest-priority risk | Risk | Critical |
| "Option D" feedback pattern (toast + badge) | UX Architecture | Recommendation |
| `prompt_page_id` in status API for polling | Integration | Recommendation |
| Always-draft approach should respect visibility | Logic | High |

**Strengths identified:**
- Sound task structure with proper error handling and return format
- Good use of Django-Q2 `async_task` for background processing
- Correct job ownership validation in the endpoint
- Proper use of `update_fields` on `gen_image.save()` (line 2809)

**Score rationale:** 8.0/10 reflects strong architectural direction with a minor deduction for not independently identifying the duplicate page creation bug (Bug 1) before the @django-pro agent. The sub-phase decomposition (6A bugs first, then UI) is the most impactful recommendation from this review, as it prevents shipping data integrity bugs into production.

### 9.2 @django-pro -- Score: 6.5/10

**Focus:** Django-specific correctness, model field coverage, ORM patterns, data integrity.

**What the agent found:**

| Finding | Category | Severity |
|---------|----------|----------|
| Bug 1: Duplicate page creation | Data Integrity | Critical |
| Bug 2: Visibility not mapped | Logic | High |
| Bug 3: `hasattr` always True | Dead Code | Medium |
| Bug 4: TOCTOU race | Concurrency | Medium |
| Bug 5: Missing `b2_thumb_url` | Field Coverage | Medium |
| Bug 6: Wrong `moderation_status` | Default Value | Low |
| Bug 7: Missing categories/descriptors | Field Coverage | Low |

**Score rationale:** The 6.5/10 score reflects the quality of the **existing code under review**, not the quality of the design spec or the session itself. This distinction is important for understanding the average score (see Section 9.4). The agent evaluated the scaffolding code as-written and found 7 bugs across 2 files. A score below 7.0 for existing code is informational -- it confirms the review was necessary and validates the Phase 6A bug fix phase.

**Strengths the agent acknowledged:**
- Task function signature and return value format are well-designed
- Error handling with `try/except` per image (not per batch) is correct
- `parse_source_credit` integration is properly implemented
- Logging at appropriate levels (error for failures, info for summary)

### 9.3 @ui-ux-designer -- Score: 8.5/10

**Focus:** User experience patterns, visual state management, interaction design, CSS architecture.

**What the agent found:**

| Finding | Category | Detail |
|---------|----------|--------|
| Sticky bottom bar pattern | Interaction | Dormant (invisible) when 0 selected; raised card when 1+ selected |
| Selected image state | Visual | 3px solid `var(--primary)` border + checkmark badge (top-right) |
| Deselected (trashed) state | Visual | 55% opacity overlay, no border |
| Discarded state | Visual | `filter: blur(2px) grayscale(100%)` |
| Published state | Visual | Green "View page" badge replaces checkmark after creation |
| Toast feedback | Interaction | "X pages queued -- they'll be ready in a moment." |
| Button label | Copy | Dynamic count: "Create Pages (3 selected)" |

**Score rationale:** 8.5/10 reflects strong UX direction with actionable CSS specifics that can be implemented directly. The agent provided concrete CSS property values (not vague descriptions), making the design immediately implementable. Minor deduction for not addressing keyboard accessibility in the selection flow (tab order, Enter/Space to select, screen reader announcements).

### 9.4 Average Score Analysis

**Raw average:** (8.0 + 6.5 + 8.5) / 3 = **7.67/10**

**Threshold:** The project standard is 8+/10 average before committing.

**Why 7.67 is acceptable for this session:**

1. **No code was committed.** The 8+/10 threshold applies to code-change sessions where agents validate implementation quality. This is a design-only session.

2. **The @django-pro score reflects code quality, not spec quality.** The agent scored the existing scaffolding code at 6.5/10 -- a fair assessment given 7 bugs. The spec itself (the design review document) was not rated; it is the output of the session, not the input.

3. **The low score is the point.** The purpose of a design review is to find problems before they ship. A high @django-pro score would mean the review found nothing, defeating its purpose.

4. **Excluding the code-quality score:** If only spec-quality scores are averaged (8.0 + 8.5) / 2 = **8.25/10**, which exceeds the threshold.

5. **Precedent:** Session 83 (tag pipeline review) used a similar pattern where code-under-review scores were reported separately from spec-quality scores.

**Recommendation:** When Phase 6A is implemented and the 7 bugs are fixed, re-run @django-pro on the patched files. The post-fix score should be 8.0+ to meet the commit threshold.

---

## 10. Additional Recommended Agents

The following agents would provide value during Phase 6 implementation (not this review session):

### For Phase 6A (Bug Fixes)

| Agent | Why | Focus Areas |
|-------|-----|-------------|
| @django-pro | Re-validate after bug fixes | Confirm all 7 bugs resolved, no regressions |
| @code-reviewer | Transaction safety | Verify `transaction.atomic()` pattern correctness |
| @security-reviewer | Idempotency completeness | Confirm double-submit is fully prevented |

### For Phase 6B (Create Pages Button)

| Agent | Why | Focus Areas |
|-------|-----|-------------|
| @accessibility | WCAG compliance | Button focus states, screen reader announcements, keyboard navigation |
| @ui-visual-validator | Visual consistency | Button styling matches existing bulk generator design language |

### For Phase 6C (Gallery Visual States)

| Agent | Why | Focus Areas |
|-------|-----|-------------|
| @accessibility | State communication | Selected/deselected states announced to screen readers, contrast ratios |
| @ui-visual-validator | State transitions | Opacity, borders, badges render correctly across states |
| @performance | Polling efficiency | Status API polling frequency for badge updates |

### For Phase 6D (Error Recovery)

| Agent | Why | Focus Areas |
|-------|-----|-------------|
| @django-pro | Error handling patterns | Retry logic, partial failure recovery |
| @code-reviewer | Edge cases | What happens when 3 of 5 pages fail? |

---

## 11. What Was Improved

This session produced no code changes, but it improved the project in three concrete ways:

### 11.1 Bug Discovery Before Shipping

Seven bugs were found in code that has existed since Session 93 (Phase 4). Without this review, all 7 would have shipped when Phase 6B connects the frontend to the backend. The most damaging (Bug 1: duplicate pages, Bug 5: broken thumbnails) would have required emergency patches and data cleanup.

**Quantified impact:**
- Bug 1 would create N duplicate Prompt records per double-submit (where N = number of selected images)
- Bug 5 would produce broken thumbnail images on every bulk-created page across the entire site
- Bug 6 would flood the admin moderation queue with pages that need no review

### 11.2 Sub-Phase Decomposition

The session produced a clear 4-phase implementation plan:

| Sub-Phase | What | Depends On | Estimated Scope |
|-----------|------|------------|-----------------|
| **6A** | Fix all 7 bugs in task + endpoint | Nothing | ~50 lines changed, ~30 test cases |
| **6B** | "Create Pages" button + JS wiring | 6A | ~100 lines JS, ~30 lines template, ~20 lines CSS |
| **6C** | Gallery visual states (selected/published/discarded) | 6B | ~80 lines CSS, ~40 lines JS |
| **6D** | Per-image error recovery + retry | 6C | ~60 lines JS, ~20 lines backend |

This decomposition follows the project's micro-spec approach (10-20 lines of code per spec) and ensures each sub-phase can be independently tested and agent-reviewed.

### 11.3 Design Clarity

The session resolved 8 architectural decision points that would otherwise require mid-implementation deliberation:

| Decision | Resolution | Impact |
|----------|-----------|--------|
| Bug fix ordering | 6A before any UI work | Prevents shipping data integrity bugs |
| Thumbnail strategy | Copy image_url as fallback | Unblocks Phase 6, defers optimization to Phase 7 |
| Visibility mapping | `public` -> Published, `private` -> Draft | Eliminates ambiguity in task logic |
| TOCTOU protection | `transaction.atomic()` pattern | Standard Django solution, no custom locking |
| Idempotency mechanism | `prompt_page__isnull=True` filter | Uses existing FK as guard, no new fields |
| M2M assignment | Apply categories + descriptors in task | Requires service response verification |
| Frontend feedback | Toast + polling-based badges | No new endpoint needed |
| Button behavior | Sticky bar with dynamic count | Progressive disclosure (hidden until selections made) |

---

## 12. Expectations vs. Reality

### What the Spec Intended

The Phase 6 architect review was expected to:
1. Confirm the scaffolding code is ready for frontend integration
2. Identify any missing fields or incorrect defaults
3. Produce a sub-phase breakdown for implementation
4. Document UX patterns for the selection-to-creation flow

### What the Review Actually Found

| Expectation | Reality |
|-------------|---------|
| "Scaffolding is ready for frontend integration" | 7 bugs must be fixed first; 2 are data-integrity critical |
| "May need minor field adjustments" | 4 fields missing (`b2_thumb_url`, `b2_medium_url`, `moderation_status`, M2M assignments) |
| "Sub-phase breakdown" | Produced as expected: 6A through 6D with clear dependencies |
| "UX patterns documented" | Produced as expected: 5 visual states, sticky bar, toast feedback |

### Gap Analysis

The largest gap between expectation and reality is the scaffolding code quality. The code was written as forward-looking infrastructure during Phase 4 and was never tested with real data. The review revealed that "written but untested" code in a rapidly evolving codebase accumulates bugs:

- **Bug 2** (visibility not mapped) was correct when written (Phase 4 only had Draft mode) but became a bug when Phase 5 added visibility selection.
- **Bug 5** (missing `b2_thumb_url`) was not a bug in Phase 4 (no images existed to test) but would be immediately visible once pages are created.
- **Bug 4** (TOCTOU race) was not a risk in Phase 4 (sequential execution) but became one when Phase 5D introduced `ThreadPoolExecutor`.

**Lesson learned:** Scaffolding code should be reviewed before integration, not just when it is written. The codebase evolves around it, introducing new invariants that the original code does not respect.

---

## 13. How to Test the Results

Since no code was changed, this section documents the **test plan for Phase 6A** -- the bug fix sub-phase that implements the fixes documented in this review.

### Bug 1 -- Duplicate Page Creation

**Test case 1: Double-submit returns zero on second call**
```python
def test_create_pages_idempotent(self):
    """Second POST for same images returns 0 pages_to_create."""
    # First call: creates pages
    response1 = self.client.post(url, data, content_type='application/json')
    self.assertEqual(response1.json()['pages_to_create'], 3)

    # Process the task synchronously
    create_prompt_pages_from_job(str(self.job.id), image_ids)

    # Second call: all images now have prompt_page set
    response2 = self.client.post(url, data, content_type='application/json')
    self.assertEqual(response2.json()['pages_to_create'], 0)
```

**Test case 2: Task skips images with existing prompt_page**
```python
def test_task_skips_already_created(self):
    """Task skips images that already have a prompt_page linked."""
    # Create page for first image manually
    self.image1.prompt_page = PromptFactory()
    self.image1.save()

    result = create_prompt_pages_from_job(str(self.job.id), all_image_ids)
    # Should only create pages for images without prompt_page
    self.assertEqual(result['created_count'], 2)  # not 3
```

### Bug 2 -- Visibility Mapping

**Test case 3: Public job creates Published pages**
```python
def test_public_job_creates_published_pages(self):
    """Pages from public jobs have status=1 (Published)."""
    self.job.visibility = 'public'
    self.job.save()

    result = create_prompt_pages_from_job(str(self.job.id), image_ids)
    page = self.image1.refresh_from_db().prompt_page
    self.assertEqual(page.status, 1)
```

**Test case 4: Private job creates Draft pages**
```python
def test_private_job_creates_draft_pages(self):
    """Pages from private jobs have status=0 (Draft)."""
    self.job.visibility = 'private'
    self.job.save()

    result = create_prompt_pages_from_job(str(self.job.id), image_ids)
    page = self.image1.refresh_from_db().prompt_page
    self.assertEqual(page.status, 0)
```

### Bug 3 -- `hasattr` Removal

No dedicated test needed. Covered by all other tests that verify `b2_image_url` is set.

### Bug 4 -- TOCTOU Race

**Test case 5: IntegrityError triggers UUID suffix retry**
```python
@patch('prompts.tasks.Prompt.save')
def test_integrity_error_retry(self, mock_save):
    """IntegrityError on save triggers retry with UUID suffix."""
    from django.db import IntegrityError
    mock_save.side_effect = [IntegrityError('duplicate'), None]

    result = create_prompt_pages_from_job(str(self.job.id), [str(self.image1.id)])
    self.assertEqual(result['created_count'], 1)
    # Verify title has UUID suffix
    page = GeneratedImage.objects.get(id=self.image1.id).prompt_page
    self.assertRegex(page.title, r'.+ - [a-f0-9]{8}$')
```

### Bug 5 -- `b2_thumb_url` Set

**Test case 6: Created pages have thumbnail URLs**
```python
def test_b2_thumb_url_set(self):
    """Created pages have b2_thumb_url as fallback to image_url."""
    result = create_prompt_pages_from_job(str(self.job.id), image_ids)
    self.image1.refresh_from_db()
    page = self.image1.prompt_page
    self.assertEqual(page.b2_thumb_url, self.image1.image_url)
    self.assertEqual(page.b2_medium_url, self.image1.image_url)
```

### Bug 6 -- Moderation Status

**Test case 7: Created pages are pre-approved**
```python
def test_moderation_status_approved(self):
    """Staff-created pages have moderation_status='approved'."""
    result = create_prompt_pages_from_job(str(self.job.id), image_ids)
    self.image1.refresh_from_db()
    page = self.image1.prompt_page
    self.assertEqual(page.moderation_status, 'approved')
```

### Bug 7 -- Categories and Descriptors

**Test case 8: Categories assigned from AI content**
```python
@patch('prompts.services.content_generation.ContentGenerationService.generate_content')
def test_categories_assigned(self, mock_gen):
    """Categories from AI content response are assigned to created page."""
    mock_gen.return_value = {
        'title': 'Test Title',
        'description': 'Test desc',
        'suggested_tags': ['tag1'],
        'categories': ['portrait', 'fashion'],
        'descriptors': ['woman', 'studio'],
    }
    result = create_prompt_pages_from_job(str(self.job.id), image_ids)
    self.image1.refresh_from_db()
    page = self.image1.prompt_page
    self.assertTrue(page.categories.exists())
```

### Acceptance Criteria Summary

| Bug | Acceptance Criterion |
|-----|---------------------|
| 1 | Second POST for same images returns `pages_to_create: 0` |
| 2 | Public job -> `status=1`; Private job -> `status=0` |
| 3 | `b2_image_url` set without `hasattr` guard |
| 4 | `IntegrityError` caught and retried with UUID suffix |
| 5 | `b2_thumb_url` and `b2_medium_url` both set to `image_url` |
| 6 | `moderation_status='approved'` on all created pages |
| 7 | Categories and descriptors assigned when present in AI response |

---

## 14. What to Work On Next

### Recommended Order

```
Phase 6A (Bug Fixes)
    |
    v
Phase 6B (Create Pages Button + JS Wiring)
    |
    v
Phase 6C (Gallery Visual States)
    |
    v
Phase 6D (Error Recovery)
    |
    v
Phase 7 (Real Thumbnail Generation)
```

### Phase 6A -- Specific First Tasks

**Priority 1: Fix Bugs 1 + 5 (Critical path)**

These two bugs block all downstream work. Bug 1 prevents safe testing of page creation. Bug 5 means any created pages have broken thumbnails.

1. Open `prompts/views/bulk_generator_views.py`
2. Add `prompt_page__isnull=True` to the filter on line 385 (Bug 1 fix)
3. Add early return when `valid_ids` is empty (idempotency response)
4. Open `prompts/tasks.py`
5. Replace lines 2778-2786 with the complete Prompt constructor (Bugs 2, 3, 5, 6 all fixed in one edit)
6. Add per-image idempotency skip at top of the `for` loop
7. Replace lines 2800-2809 with the complete M2M assignment block (Bugs 3, 7 fixed)
8. Wrap `prompt_page.save()` in `transaction.atomic()` with `IntegrityError` retry (Bug 4 fix)

**Priority 2: Write tests**

Write the 8+ test cases documented in Section 13. Run against the fixed code. Target: all tests pass, plus full suite (`python manage.py test`) remains at 985+ passing.

**Priority 3: Run agents**

Run @django-pro on the two modified files. Target: 8.0+/10 post-fix score. Run @code-reviewer as second opinion on the `transaction.atomic()` pattern.

### Phase 6B -- After 6A is Committed

1. Add `data-create-pages-url` attribute to the job progress template
2. Implement `handleCreatePages()` in `bulk-generator-job.js`
3. Add sticky bottom bar HTML to template (hidden by default)
4. Wire selection count to button label: "Create Pages (N selected)"
5. Disable button after click, show spinner
6. POST to `api_create_pages`, handle response

### Phase 6C -- After 6B is Committed

1. Add CSS for selected state: `3px solid var(--primary)` border + checkmark badge
2. Add CSS for trashed state: `opacity: 0.55` overlay
3. Add CSS for discarded state: `filter: blur(2px) grayscale(100%)`
4. Add CSS for published state: green "View page" badge
5. Add `prompt_page_id` to status API image serialization
6. Poll status API after "Create Pages" submit to detect completion
7. Update gallery cards with "View page" badges as `prompt_page_id` populates

### Phase 6D -- After 6C is Committed

1. Handle partial failure (some pages created, some failed)
2. Display per-image error messages in gallery
3. "Retry Failed" button for images that failed page creation
4. Error state CSS (red border, error icon)

---

## 15. Commits Made

**None.**

This session produced no code changes and no commits. The sole output is the design review document `PHASE6_DESIGN_REVIEW.md` in the project root (also not committed).

**Why no commits:**
- The session scope was explicitly design-only
- The spec states: "DO NOT commit anything -- this is a review document for Mateo to approve first"
- All 7 bugs require Mateo's review before fixes are applied, particularly Bug 2 (visibility mapping) which has an open question about the `private` -> Draft assumption
- The design review document needs owner sign-off before the sub-phase breakdown becomes the implementation plan

**What will be committed in Phase 6A:**
- Modified: `prompts/tasks.py` (7 bug fixes in `create_prompt_pages_from_job`)
- Modified: `prompts/views/bulk_generator_views.py` (Bug 1 idempotency fix)
- New: `prompts/tests/test_bulk_page_creation.py` (8+ test cases)
- Updated: `CLAUDE_CHANGELOG.md` (session entry)

---

## 16. Appendix

### A. Sub-Phase Specs Overview

#### Phase 6A: Bug Fixes

**Scope:** Fix all 7 bugs in `tasks.py` and `bulk_generator_views.py`.
**Files changed:** 2 (tasks.py, bulk_generator_views.py)
**New files:** 1 (test file)
**Estimated lines changed:** ~50
**Estimated test cases:** ~30
**Dependencies:** None
**Agent requirement:** @django-pro 8.0+ post-fix

#### Phase 6B: Create Pages Button and JS Wiring

**Scope:** Add "Create Pages" button to job progress page, wire to API endpoint.
**Files changed:** 3 (template, JS, CSS)
**Estimated lines added:** ~150
**Dependencies:** Phase 6A committed
**Agent requirement:** @accessibility 8.0+, @ui-visual-validator 8.0+

#### Phase 6C: Gallery Visual States

**Scope:** CSS for selected/trashed/discarded/published states, polling-based badge updates.
**Files changed:** 3 (CSS, JS, views)
**Estimated lines added:** ~120
**Dependencies:** Phase 6B committed
**Agent requirement:** @accessibility 8.0+, @ui-visual-validator 8.0+

#### Phase 6D: Error Recovery

**Scope:** Per-image error display, retry button, partial failure handling.
**Files changed:** 2 (JS, template)
**Estimated lines added:** ~80
**Dependencies:** Phase 6C committed
**Agent requirement:** @django-pro 8.0+, @code-reviewer 8.0+

### B. Risk Register (Full)

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Phase |
|----|------|-----------|--------|------------|-------|-------|
| R1 | Broken thumbnails on all bulk pages | Certain | Critical | Bug 5: copy image_url to b2_thumb_url | Phase 6A | 6A |
| R2 | Duplicate Prompt records on double-submit | Medium | High | Bug 1: prompt_page__isnull=True filter + client disable | Phase 6A+6B | 6A, 6B |
| R3 | IntegrityError on concurrent title collision | Low | Medium | Bug 4: transaction.atomic() + retry | Phase 6A | 6A |
| R4 | Moderation queue flooded with auto-approved pages | Certain | Low | Bug 6: moderation_status='approved' | Phase 6A | 6A |
| R5 | ContentGenerationService missing categories/descriptors in response | Unknown | Low | Verify service response shape before Bug 7 fix | Phase 6A | 6A |
| R6 | Visibility mapping unclear for 'private' | Unknown | Medium | Open question for Mateo: Draft vs. Published+private | Phase 6A | 6A |
| R7 | Full-size images served as thumbnails (performance) | Certain | Low | Acceptable fallback; real thumbnails in Phase 7 | Phase 7 | 7 |
| R8 | No keyboard accessibility for selection flow | Medium | Medium | Phase 6B/6C must include tabindex, Enter/Space handlers | Phase 6B | 6B, 6C |
| R9 | Status API polling too frequent after page creation | Low | Low | Poll every 3s (existing pattern), stop after all badges populated | Phase 6C | 6C |
| R10 | Partial failure confuses staff (3 of 5 pages created) | Medium | Medium | Phase 6D: per-image error display + retry button | Phase 6D | 6D |

### C. Open Questions for Mateo

| # | Question | Context | Default Assumption |
|---|----------|---------|-------------------|
| 1 | Does `visibility='private'` map to Draft (`status=0`) or Published + private? | Current Prompt model uses integer `status` field, no `is_private` boolean | Private -> Draft (status=0) |
| 2 | Should real thumbnail generation happen in Phase 6 or Phase 7? | Using full-size image as thumbnail fallback works but wastes bandwidth | Phase 7 (deferred) |
| 3 | Does `ContentGenerationService.generate_content()` return `categories` and `descriptors` keys in its response when called from the bulk generation context? | Upload path returns these; bulk path may differ | Verify before implementing Bug 7 fix |
| 4 | "Create Pages" button placement -- sticky bottom bar only, or also visible at top when user has scrolled? | Large galleries may have the button below the fold | Sticky bottom bar only |
| 5 | Is Phase 6D (per-image error recovery) in scope for this release, or post-launch? | Error recovery adds complexity; basic error display may suffice | In scope (minimal version) |

### D. Files Referenced in This Report

| File | Path | Relevance |
|------|------|-----------|
| Page creation task | `prompts/tasks.py:2689-2877` | 5 of 7 bugs; primary fix target |
| Create pages endpoint | `prompts/views/bulk_generator_views.py:347-419` | Bug 1; idempotency fix target |
| BulkGenerationJob model | `prompts/models.py:2836-2939` | Visibility field, job config |
| GeneratedImage model | `prompts/models.py:2941-2995` | Selection state, prompt_page FK |
| Prompt model | `prompts/models.py:711-1500+` | Target model for page creation |
| Prompt STATUS choices | `prompts/models.py:663` | `STATUS = ((0, "Draft"), (1, "Published"))` |
| Prompt MODERATION_STATUS | `prompts/models.py:666-671` | `default='pending'` -- Bug 6 |
| Prompt b2_thumb_url | `prompts/models.py:905-909` | Missing assignment -- Bug 5 |
| Prompt display_thumb_url | `prompts/models.py:1351-1354` | Fallback chain -- Bug 5 impact |
| Gallery JS | `static/js/bulk-generator-job.js` | Selection state, missing handleCreatePages |
| Design review output | `PHASE6_DESIGN_REVIEW.md` | Session deliverable (project root) |

---

**End of Report**

*Session 112 -- Phase 6 Architect Review*
*Date: March 8, 2026*
*Type: Design-Only (No Code Changes)*
*Agent Average: 7.67/10 (acceptable -- see Section 9.4 for analysis)*
