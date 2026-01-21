# PHASE N: OPTIMISTIC UPLOAD UX
## Detailed Implementation Outline

**Created:** January 20, 2026
**Last Updated:** January 21, 2026 (Session 52)
**Status:** N0-N2 Logic Complete, N3 In Progress (Single-Page Rebuild)
**Goal:** Transform upload flow to single-page optimistic UX

---

## 🎯 PURPOSE & PHILOSOPHY

### Why Phase N Exists

The upload experience should feel **instant and simple**. Users shouldn't:
- Wait for processing they don't need to see
- Navigate multiple pages for a single action
- Fill out fields we can generate automatically

### Core Principle: "The Restaurant Analogy"

> At a restaurant, we don't ask customers to wash their own dishes. They're customers, not employees.

**Applied to PromptFinder:**
- Users upload content and provide the prompt they used
- WE handle SEO (tags, titles, descriptions, slugs)
- Users don't understand SEO and might enter "garbage" tags
- Keep the form simple - minimum required fields only

### What Users Provide vs What We Generate

| User Provides | We Generate (Background) |
|---------------|-------------------------|
| Image/Video | NSFW moderation |
| Prompt text (required) | AI-generated title |
| AI Generator (required) | AI-generated description |
| Visibility (draft/publish) | SEO-optimized tags |
| | URL slug |
| | Image variants |

---

## 🔄 SINGLE-PAGE UPLOAD FLOW

### Overview

**OLD: Two separate pages**
```
/upload/step1/ (select file) → /upload/step2/ (fill form) → /prompt/...
```

**NEW: Single page**
```
/upload/ (select file + fill form on SAME page) → /prompt/processing/<uuid>/
```

---

### SINGLE UPLOAD PAGE STATES

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ URL: /upload/                                                               │
│ STATE 1: NO FILE SELECTED                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │     ┌─────────────────────────────────────────────────────────┐      │ │
│  │     │                                                         │      │ │
│  │     │            🖼️  Drag and drop to upload                 │      │ │
│  │     │                      - or -                             │      │ │
│  │     │                  [ Browse ]                             │      │ │
│  │     │                                                         │      │ │
│  │     │         Supports JPG, PNG, GIF, MP4, WebM               │      │ │
│  │     │              Max 50MB for images                        │      │ │
│  │     │              Max 200MB for videos                       │      │ │
│  │     │                                                         │      │ │
│  │     └─────────────────────────────────────────────────────────┘      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  FORM (visible but DISABLED - grayed out)                             │ │
│  │                                                                       │ │
│  │  Prompt Content *              [________________________] (disabled)  │ │
│  │  AI Generator *                [Select generator... ▼ ] (disabled)   │ │
│  │  ☐ Save as draft                                        (disabled)   │ │
│  │                                                                       │ │
│  │  [ Submit ] (disabled)                                                │ │
│  │                                                                       │ │
│  │  Helper text: "Select an image or video to enable the form"          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ URL: /upload/                                                               │
│ STATE 2: FILE SELECTED (instant transition, no page load)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │                         │  │                                         │  │
│  │    ┌───────────────┐    │  │  Prompt Content *                       │  │
│  │    │               │    │  │  ┌─────────────────────────────────┐   │  │
│  │    │  LOCAL IMAGE  │    │  │  │                                 │   │  │
│  │    │   PREVIEW     │    │  │  │  Enter the prompt you used...   │   │  │
│  │    │               │    │  │  │                                 │   │  │
│  │    │  (from browser│    │  │  └─────────────────────────────────┘   │  │
│  │    │   memory -    │    │  │                                         │  │
│  │    │   NOT server) │    │  │  AI Generator *                         │  │
│  │    │               │    │  │  ┌─────────────────────────────────┐   │  │
│  │    └───────────────┘    │  │  │ Select generator...          ▼ │   │  │
│  │                         │  │  └─────────────────────────────────┘   │  │
│  │    [ 🔄 Change Image ]  │  │                                         │  │
│  │                         │  │  ☐ Save as draft                        │  │
│  │                         │  │                                         │  │
│  │                         │  │  ┌─────────────────────────────────┐   │  │
│  │                         │  │  │ ⏳ Checking content safety...  │   │  │
│  │                         │  │  └─────────────────────────────────┘   │  │
│  │                         │  │                                         │  │
│  │                         │  │  [ Submit ] (disabled until NSFW done) │  │
│  │                         │  │                                         │  │
│  └─────────────────────────┘  └─────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ BACKGROUND (user is oblivious to all of this):                      │   │
│  │                                                                     │   │
│  │  1. B2 upload starts immediately when file selected                 │   │
│  │  2. NSFW check queued (starts after B2 upload completes)            │   │
│  │  3. User fills form while background work happens                   │   │
│  │  4. Submit button enables when NSFW check completes                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE 3: NSFW COMPLETE - READY TO SUBMIT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Same layout as State 2, but:                                               │
│                                                                             │
│  NSFW indicator shows one of:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✅ Content approved - ready to submit                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OR (flagged - can still submit):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ⚠️ Content flagged for admin review - you may still submit         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Submit button: [ Submit ] (ENABLED)                                        │
│                                                                             │
│  OR (rejected - cannot submit):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ❌ MODAL: Content cannot be uploaded. Please try different content. │   │
│  │    [ Start New Upload ]                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### "CHANGE IMAGE" FUNCTIONALITY

When user clicks "Change Image":

```
1. Clear local preview (revoke ObjectURL)
2. Cancel/abandon any in-progress B2 upload
3. Reset form to State 1 (show drop zone, disable form)
4. Orphaned B2 files cleaned up by background job (not user's problem)
5. NSFW polling stops
```

This matches professional sites (Instagram, Twitter, Imgur) that let users change their selection before posting.

---

### POST-SUBMIT FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ON SUBMIT                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Create Prompt record with:                                              │
│     - processing_uuid = new UUID                                            │
│     - processing_status = 'processing'                                      │
│     - image_url = B2 URL (from background upload)                           │
│     - prompt_text = user input                                              │
│     - ai_generator = user selection                                         │
│     - is_draft = user checkbox                                              │
│     - title = NULL (AI will generate)                                       │
│     - description = NULL (AI will generate)                                 │
│     - tags = [] (AI will generate)                                          │
│     - slug = NULL (built from AI title)                                     │
│                                                                             │
│  2. Queue Django-Q background task for AI generation                        │
│                                                                             │
│  3. INSTANT redirect to processing page                                     │
│     → /prompt/processing/<uuid>/                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ PROCESSING PAGE: /prompt/processing/<uuid>/                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "Your prompt is being processed..."                                        │
│  Image preview shown                                                        │
│  Animated progress indicator                                                │
│                                                                             │
│  BACKGROUND (user can leave anytime - processing continues):                │
│  - AI title/description/tags generation                                     │
│  - Slug creation from title                                                 │
│  - Image variant generation                                                 │
│                                                                             │
│  Frontend polls for status                                                  │
│  When ready → 301 redirect to /prompt/<slug>/                               │
│                                                                             │
│  USER CAN NAVIGATE AWAY: Processing happens regardless                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FINAL: /prompt/<slug>/                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Full prompt displayed with AI-generated content                            │
│  SEO-friendly URL                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ PRESERVED PROTECTIONS

### 1. Navigation Guard (Abandon Protection)

**Trigger:** User tries to navigate away, hit back button, or close tab

**Behavior:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MODAL: Leave this page?                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  You have an upload in progress. If you leave now:                          │
│  • Your uploaded image/video will be deleted                                │
│  • Any information you entered will be lost                                 │
│                                                                             │
│  Are you sure you want to leave?                                            │
│                                                                             │
│  [ Stay and continue editing ]    [ Yes, leave and delete upload ]          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**When active:** After file is selected (State 2+)
**When inactive:** Before file selected, after successful submit

**Browser warning:** Also triggers native "unsaved changes" dialog for:
- Tab close
- Browser close
- External navigation

### 2. Cleanup on Abandon

**When user confirms leaving or session expires:**
1. Clear local preview
2. Cancel any pending uploads
3. B2 cleanup job removes orphaned files (runs periodically)
4. No orphaned content on server

**Principle:** Only keep content that will become a prompt

### 3. Idle Detection

**Trigger:** User inactive for X minutes on upload page

**Behavior:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MODAL: Still working on this?                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Your upload session will expire in:                                        │
│                                                                             │
│                          [ 30 ]                                             │
│                         seconds                                             │
│                                                                             │
│  Click below to continue editing or cancel this upload.                     │
│                                                                             │
│  [ Yes, I need more time ]          [ Cancel Upload ]                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**If countdown reaches 0:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MODAL: Upload Session Expired                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⏰ Your upload session ended due to inactivity.                            │
│                                                                             │
│  Don't worry - you can start a new upload anytime!                          │
│                                                                             │
│  [ Got it, take me home ]                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Idle timer resets on:** Any user activity (typing, clicking, mouse movement)

---

## 🏗️ IMPLEMENTATION APPROACH: BUILD FROM SCRATCH

### Why Build Fresh (Not Refactor)

| Refactor Existing | Build Fresh |
|-------------------|-------------|
| Extract JS from 1,700-line file | Write clean code from specs |
| Keep legacy tag/AI code then remove | Never include tag/AI code |
| Two pages → combine later | Single page from start |
| More work, technical debt | Less work, clean architecture |

**Decision:** Build new single-page upload from scratch using CC specifications.

### What We're Preserving (Logic Only)

The following LOGIC from existing files will be incorporated into new clean code:
- B2 upload handling (from upload-step1.js)
- NSFW polling (from upload_step2.html)
- Navigation guards (from upload_step2.html)
- Idle detection (from upload_step2.html)

**CC will rebuild this logic cleanly** - not copy/paste the existing tangled code.

---

## 📋 CC SPECIFICATION SEQUENCE

### Spec 1: `upload.html` Template (~400 lines)
**What CC Creates:**
- New single-page template at `prompts/templates/prompts/upload.html`
- Three states: no file, file selected, ready to submit
- All modals (navigation, idle, expired, rejected)
- Form fields (prompt, generator, visibility)
- NSFW status indicator
- Drop zone + preview area

**CC Agents:** @django-expert, @ui, @frontend-developer

### Spec 2: `upload-core.js` (~200 lines)
**What CC Creates:**
- File selection and validation
- Local preview (ObjectURL)
- B2 background upload
- Change Image functionality
- Upload state management

**CC Agents:** @frontend-developer, @code-review

### Spec 3: `upload-form.js` + NSFW logic (~300 lines)
**What CC Creates:**
- Form state management (disabled → enabled)
- Form validation
- NSFW polling (queue task, poll status)
- NSFW UI updates (checking → approved/flagged/rejected)
- Submit handling

**CC Agents:** @frontend-developer, @security-auditor

### Spec 4: `upload-guards.js` (~300 lines)
**What CC Creates:**
- Navigation guard (beforeunload, link clicks)
- Idle detection timer
- Warning modal management
- Session expiry handling
- Cleanup on abandon

**CC Agents:** @frontend-developer, @code-review

### Spec 5: URL Routing + View Updates
**What CC Creates:**
- New view for `/upload/`
- Redirect views for legacy URLs
- URL patterns in urls.py

**CC Agents:** @django-expert

---

## 📁 FILE MANAGEMENT PLAN

### Phase 1: Create New Files (N3)

**CREATE:**
```
prompts/templates/prompts/upload.html     ← NEW single-page template
static/js/upload-core.js                  ← NEW file handling
static/js/upload-form.js                  ← NEW form + NSFW
static/js/upload-guards.js                ← NEW navigation + idle
```

### Phase 2: Test New System

**Keep old files during testing** - allows rollback if issues

### Phase 3: Cleanup After N3 Verified (Separate Commit)

**DELETE (empty/unused):**
```
static/js/upload-step2-form.js            ← DELETE (empty, never used)
static/js/upload-step2-guards.js          ← DELETE (empty, never used)
static/js/upload-step2-nsfw.js            ← DELETE (empty, never used)
```

**DEPRECATE (keep for rollback, remove after N5):**
```
static/js/upload-step1.js                 ← DEPRECATE
prompts/templates/prompts/upload_step1.html  ← DEPRECATE
prompts/templates/prompts/upload_step2.html  ← DEPRECATE
```

### Phase 4: Final Cleanup After N5 Verified

**DELETE deprecated files:**
```
static/js/upload-step1.js                 ← DELETE
prompts/templates/prompts/upload_step1.html  ← DELETE
prompts/templates/prompts/upload_step2.html  ← DELETE
```

---

## 🔄 URL MIGRATION

### New URL Structure

```python
# prompts/urls.py

urlpatterns = [
    # New single-page upload
    path('upload/', views.upload_page, name='upload'),
    
    # Legacy redirects (keep for bookmarks, external links)
    path('upload/step1/', RedirectView.as_view(pattern_name='prompts:upload', permanent=True)),
    path('upload/step2/', RedirectView.as_view(pattern_name='prompts:upload', permanent=True)),
    
    # Processing page (N4)
    path('prompt/processing/<uuid:processing_uuid>/', views.prompt_processing, name='prompt_processing'),
]
```

---

## 🏗️ PHASE BREAKDOWN

### ════════════════════════════════════════════════════════════
### N0: DJANGO-Q INFRASTRUCTURE ✅ COMPLETE
### ════════════════════════════════════════════════════════════

**Status:** Done - Django-Q2 installed and configured

**Files:**
- `prompts_manager/settings.py` - Q_CLUSTER config
- `prompts/tasks.py` - Task functions
- `requirements.txt` - django-q2==1.6.2

---

### ════════════════════════════════════════════════════════════
### N1: LOCAL PREVIEW LOGIC ✅ COMPLETE
### ════════════════════════════════════════════════════════════

**Status:** Logic exists in upload-step1.js, will be rebuilt cleanly

---

### ════════════════════════════════════════════════════════════
### N2: BACKGROUND NSFW LOGIC ✅ COMPLETE
### ════════════════════════════════════════════════════════════

**Status:** Logic exists in upload_step2.html, will be rebuilt cleanly

**Endpoints (already created):**
- `POST /api/upload/nsfw/queue/` - Queue moderation task
- `GET /api/upload/nsfw/status/?upload_id=X` - Poll for status

---

### ════════════════════════════════════════════════════════════
### N3: SINGLE-PAGE UPLOAD 🔄 IN PROGRESS
### ════════════════════════════════════════════════════════════

**Objective:** Build new single-page upload from scratch

**Implementation Steps:**

| Step | CC Spec | Files Created | Test |
|------|---------|--------------|------|
| 3.1 | Spec 1 | upload.html | Visual check |
| 3.2 | Spec 2 | upload-core.js | File select, preview |
| 3.3 | Spec 3 | upload-form.js | NSFW polling, form |
| 3.4 | Spec 4 | upload-guards.js | Navigation, idle |
| 3.5 | Spec 5 | URLs + views | Full flow test |
| 3.6 | Cleanup | Delete empty files | Verify no breaks |

**Estimated Effort:** 6-8 hours total

**Current Status:** Creating CC specifications

---

### ════════════════════════════════════════════════════════════
### N4: BACKGROUND AI + PROCESSING PAGE 📋 PENDING
### ════════════════════════════════════════════════════════════

**Objective:** After submit, process AI content in background

**What Needs To Be Done:**

1. Add fields to Prompt model:
   - `processing_uuid`
   - `processing_status`

2. Modify submit view:
   - Create prompt with minimal data
   - Queue AI generation task
   - Redirect to `/prompt/processing/<uuid>/`

3. Create AI generation Django-Q task

4. Create processing page template

**Estimated Effort:** 4-5 hours

---

### ════════════════════════════════════════════════════════════
### N5: 301 REDIRECT TO SLUG 📋 PENDING
### ════════════════════════════════════════════════════════════

**Objective:** SEO-friendly redirect from processing URL to final URL

**Estimated Effort:** 2-3 hours

---

## 📊 SUMMARY TABLE

| Spec | Description | Status | Effort |
|------|-------------|--------|--------|
| N0 | Django-Q setup | ✅ Complete | Done |
| N1 | Local preview logic | ✅ Complete | Done |
| N2 | Background NSFW logic | ✅ Complete | Done |
| N3 | Single-page upload rebuild | 🔄 In Progress | 6-8h |
| N4 | Background AI + processing page | 📋 Pending | 4-5h |
| N5 | 301 redirect to slug | 📋 Pending | 2-3h |

**Total Estimated Remaining:** 12-16 hours

---

## 🆘 SESSION HANDOFF INSTRUCTIONS

If this session ends abruptly, here's how to continue:

### Current State (as of Session 52)

1. **PHASE_N_DETAILED_OUTLINE.md** - This document is the source of truth
2. **Empty files to delete:**
   - `static/js/upload-step2-form.js`
   - `static/js/upload-step2-guards.js`
   - `static/js/upload-step2-nsfw.js`
3. **Approach:** Build single-page upload from scratch using CC specs
4. **Next step:** Create CC Spec 1 for `upload.html` template

### How to Continue

1. Share this document with new session
2. Delete the empty `upload-step2-*.js` files if not done
3. Request: "Create CC Spec 1 for upload.html template"
4. Follow spec sequence: Spec 1 → 2 → 3 → 4 → 5
5. Test after each spec before proceeding

### Key Decisions Made

- ✅ Single page replaces step1 + step2
- ✅ Form visible but disabled until file selected
- ✅ NO tags on form (AI generates)
- ✅ NO AI suggestions on upload page
- ✅ Build from scratch (not refactor)
- ✅ Preserve navigation guards, idle detection, cleanup

---

## 🔮 FUTURE FEATURES (Post-Phase N)

### ════════════════════════════════════════════════════════════
### N6: BEFORE/AFTER TRANSFORMATION UPLOADS 📋 FUTURE
### ════════════════════════════════════════════════════════════

**Use Case:** Many AI prompts transform existing images:
- "Transform this photo into 1950s style"
- "Change the person to have blonde long hair"
- "Make this photo look like a watercolor painting"
- "Age this person 30 years"

These transformation prompts are much more impactful when viewers can see the **before** and **after** side by side.

**User Story:**
> As a user uploading a transformation prompt, I want to upload both my original image and the AI result, so viewers can see exactly what the prompt accomplished.

**UI Concept - Upload Page:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UPLOAD PAGE (with transformation toggle)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☐ This is a transformation (before/after)     ← NEW TOGGLE                │
│                                                                             │
│  WHEN UNCHECKED (default - current behavior):                               │
│  ┌─────────────────────────────────────────┐                               │
│  │     [ Single Upload Zone ]              │                               │
│  │     Drag & drop your AI-generated image │                               │
│  └─────────────────────────────────────────┘                               │
│                                                                             │
│  WHEN CHECKED (transformation mode):                                        │
│  ┌─────────────────────┐  ┌─────────────────────┐                          │
│  │   BEFORE (Original) │  │   AFTER (AI Result) │                          │
│  │   ┌─────────────┐   │  │   ┌─────────────┐   │                          │
│  │   │             │   │  │   │             │   │                          │
│  │   │  Upload     │   │  │   │  Upload     │   │                          │
│  │   │  Original   │   │  │   │  AI Result  │   │                          │
│  │   │             │   │  │   │             │   │                          │
│  │   └─────────────┘   │  │   └─────────────┘   │                          │
│  └─────────────────────┘  └─────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**UI Concept - Prompt Detail Page:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PROMPT DETAIL PAGE (transformation view)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────┐                               │
│  │                                         │                               │
│  │   BEFORE          │ ← SLIDER →│  AFTER  │                               │
│  │                   │           │         │                               │
│  │   [Original]      │===========│ [Result]│                               │
│  │                   │           │         │                               │
│  │                                         │                               │
│  └─────────────────────────────────────────┘                               │
│                                                                             │
│  User can drag slider left/right to compare                                 │
│                                                                             │
│  Prompt: "Transform this photo into a 1950s style vintage portrait..."     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Database Changes:**
```python
class Prompt(models.Model):
    # Existing fields...
    
    # Transformation support (N6)
    is_transformation = models.BooleanField(default=False)
    before_image_url = models.URLField(null=True, blank=True)
    before_thumb_url = models.URLField(null=True, blank=True)
    # Note: existing image_url becomes the "after" image
```

**Technical Requirements:**
| Component | What's Needed |
|-----------|--------------|
| Upload UI | Toggle + dual upload zones |
| Validation | Both images required when toggle ON |
| B2 Upload | Upload both images (parallel) |
| NSFW Check | Check BOTH images |
| Database | New fields for before_image |
| Processing | Generate variants for both images |
| Detail Page | Slider comparison component |
| SEO | Schema markup for before/after |

**Implementation Notes:**
- Slider component: Consider libraries like `img-comparison-slider` or build custom
- Mobile: Slider should work with touch/swipe
- Fallback: If JS fails, show images stacked vertically
- Accessibility: Keyboard controls for slider

**Architecture Decisions for N3 (Now):**
To make N6 easier later, the current single-image implementation should:
- ✅ Use `image_url` (not `after_image_url`) - simpler now, rename not needed
- ✅ Keep upload logic modular in `upload-core.js` - can extend for 2 files
- ✅ NSFW checking accepts image_url parameter - can call twice for both images

**Estimated Effort:** 8-12 hours

**Priority:** Medium - Nice to have, enhances transformation prompts significantly

**Dependencies:** 
- N3-N5 complete (single-image flow working)
- Slider component selection/development

---

### Other Future Enhancements (Ideas)

| Feature | Description | Priority |
|---------|-------------|----------|
| Batch Upload | Upload multiple prompts at once | Low |
| Draft Editing | Edit prompts saved as drafts | Medium |
| Video Support | Enhanced video prompt handling | Medium |
| Collections | Group related prompts together | Medium |
| Remix/Fork | Create variant from existing prompt | Low |

---

## 🎯 SUCCESS CRITERIA

**Phase N is complete when:**
- [ ] Single `/upload/` page replaces step1 + step2
- [ ] File selection shows instant local preview (no upload wait)
- [ ] Form disabled until file selected
- [ ] B2 upload runs in background
- [ ] NSFW check runs in background (after B2)
- [ ] Submit disabled until NSFW complete
- [ ] Navigation guard prompts on leave attempt
- [ ] Idle detection prompts inactive users
- [ ] Orphaned uploads cleaned up
- [ ] Submit creates prompt with processing_uuid
- [ ] Redirect to /prompt/processing/<uuid>/
- [ ] AI content generates in background
- [ ] 301 redirect to /prompt/<slug>/ when ready
- [ ] No tag input on form (AI generates)
- [ ] All agent ratings 8+/10
- [ ] Production deployed and verified
- [ ] Legacy files cleaned up

---

**END OF PHASE N OUTLINE**
