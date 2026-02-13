# CLAUDE_PHASES.md - Phase Specifications (2 of 3)

**Last Updated:** February 13, 2026

> **📚 Document Series:**
> - **CLAUDE.md** (1 of 3) - Core Reference
> - **CLAUDE_PHASES.md** (2 of 3) - Phase Specifications ← YOU ARE HERE
> - **CLAUDE_CHANGELOG.md** (3 of 3) - Session History

---

## 📋 All Phases at a Glance

| Phase | Name | Status | One-Line Summary |
|-------|------|--------|------------------|
| A | Tag Infrastructure | ✅ Done | 209 tags across 21 categories |
| B | AI Content Generation | ✅ Done | GPT-4o-mini generates titles/descriptions/tags |
| C | Upload UI | ✅ Done | Pexels-style drag-and-drop |
| D | Two-Step Upload | ✅ Done | Step 1: upload, Step 2: fill form |
| D.5 | Trash Bin | ✅ Done | Soft delete with 5/30 day retention |
| E | User Profiles | ✅ Done | Profile pages, follow system |
| F | Admin Tools | ✅ Done | Bulk actions, moderation dashboard |
| G | Homepage Tabs | ✅ Done | Home/All/Photos/Videos + Trending/New sorting |
| H | Username System | 🔲 Planned | Edit username with rate limits |
| I | URL Migration | ✅ Done | /ai/ → /prompts/ with 301 redirects |
| J | Prompt Detail Redesign | ✅ Done | Complete UI overhaul |
| **K** | **Collections** | **⏸️ 95%** | **"Saves" feature - ON HOLD** |
| L | Media Infrastructure | ✅ Done | Cloudinary → B2 + Cloudflare |
| M | Video Moderation | ✅ Done | FFmpeg + OpenAI Vision NSFW check |
| N3 | Single-Page Upload | 🔄 ~95% | Upload page optimization |
| **N4** | **Optimistic Upload Flow** | **🔄 ~99% Complete** | **N4h rename trigger, XML sitemap, indexes migration** |
| **2B** | **Category Taxonomy Revamp + Tag Pipeline** | **✅ 2B-1 through 2B-9 + S80-81 Done** | **46 categories, 109 descriptors, AI backfill, demographic SEO, IDF-weighted scoring, tag validation pipeline, admin metadata** |

---

## 🔄 Phase N3: Single-Page Upload (~95% Complete)

**Status:** ~95% Complete
**Started:** January 2026
**Goal:** Make uploads feel instant instead of making users wait 15+ seconds

### The Problem We Solved

**Old flow (clunky):**
1. User uploads file → Stares at spinner for 10-15 seconds
2. Redirected to Step 2 → More waiting for AI suggestions
3. Finally can fill out form

**New flow (smooth):**
1. User drops file → Instant preview (no upload yet!)
2. Form appears immediately
3. All the slow stuff happens in background
4. User fills form while processing happens

### What's Complete

| Task | Description | Rating |
|------|-------------|--------|
| ✅ Single-page template | Combined Step 1 + Step 2 into one page | - |
| ✅ B2 background upload | Direct presigned URL upload, non-blocking | - |
| ✅ NSFW checking | Runs in background, blocks submit if failed | - |
| ✅ Orphan cleanup | Deletes B2 files if user cancels/navigates away | - |
| ✅ CSS extraction | Moved ~500 lines to upload.css | - |
| ✅ Admin extraction | Moved ordering functions to admin_views.py | - |
| ✅ Rate limit modal | Shows friendly message when 20/hour limit hit | 8.3/10 |
| ✅ Validation error modal | Shows error for wrong file type/size | 9.5/10 |
| ✅ File size limits | 3MB images, 15MB videos | 8.75/10 |
| ✅ B2 client caching | Reuse boto3 client (small perf win) | 8.25/10 |

### What's Left

- 🔲 Final testing across browsers
- 🔲 Deploy to production
- 🔲 Monitor for edge cases

---

## 🔄 Phase N4: Optimistic Upload Flow (CURRENT)

**Status:** ~99% Complete - Lighthouse 96/100/100/100
**Created:** January 26, 2026
**Detailed Documentation:** `docs/PHASE_N4_UPLOAD_FLOW_REPORT.md`

### Objective
Reduce perceived upload time from 15-20 seconds to 5-10 seconds by restructuring the upload flow with background processing and a dedicated processing page.

### Sub-Phases

| Phase | Description | Status |
|-------|-------------|--------|
| N4a | Variant generation after NSFW passes | ✅ Complete |
| N4b | Add processing_uuid field to Prompt model | ✅ Complete |
| N4c | Install & configure Django-Q2 | ✅ Complete |
| N4d | Create processing page template | ✅ Complete |
| N4e | AI job queuing for videos (uses thumbnail) | ✅ Complete |
| N4f | ProcessingModal in upload-form.js | ✅ Complete |
| N4 Cleanup | Remove old upload code | ✅ Complete |
| N4g | Video submit fix (session key mismatch) | ✅ Resolved (S64) |
| N4-SEO | Race/ethnicity, Schema.org VideoObject, alt tags | ✅ Complete (S64) |
| N4h | Deferred B2 file renaming task | ✅ Code complete (trigger issue remaining) |
| N4i | SEO additions (JSON-LD, sitemap) | 🔄 Deferred to pre-launch (JSON-LD done, sitemap pending) |
| N4j | Testing & polish | ⏳ Pending |
| N4-SEO | robots.txt, preconnect cleanup, font optimization | ✅ Complete (Session 69) |
| N4-A11y | Heading hierarchy (h3→h2), aria-label fixes | ✅ Complete (Session 69) |
| N4-Minify | CSS/JS minification management command | ✅ Complete (Session 69) |

**Lighthouse Scores (Session 69):**
- Performance: 96 | Accessibility: 100 | Best Practices: 100 | SEO: 100

**Remaining Items:**
- N4h rename not triggering in production (code complete, needs debugging)
- XML sitemap (deferred to pre-launch)
- Indexes migration pending (`makemigrations` needed)
- Final testing and deploy

### New Database Fields

```python
processing_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
processing_complete = models.BooleanField(default=False)
```

### Files Status

**Created:**
- `prompts/tasks.py` - Django-Q background tasks ✅ (uncommitted)
- `docs/PHASE_N4_UPLOAD_FLOW_REPORT.md` - Planning document ✅

**Modified:**
- `static/js/upload-form.js` - Added ProcessingModal (replaced processing.js)
- `prompts/views/api_views.py` - AI job queuing for videos (uncommitted)

**Deleted (Session 61 cleanup):**
- ~~`prompts/templates/prompts/processing.html`~~ - Not needed (reused prompt_detail.html)
- ~~`static/js/processing.js`~~ - Replaced by ProcessingModal in upload-form.js
- ~~`static/js/upload-step1.js`~~ - Old step-based upload removed
- ~~`prompts/templates/prompts/upload_step1.html`~~ - Replaced by upload.html
- ~~`prompts/templates/prompts/upload_step2.html`~~ - Replaced by upload.html

**Still Pending:**
- `prompts/sitemaps.py` - XML sitemap (N4i)

### New Dependencies

- `django-q2` - Background task queue

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Background tasks | Django-Q2 | Free, uses PostgreSQL, no Redis |
| Status updates | Polling (3s) | Simple, Heroku compatible |
| AI analysis | 80% Vision / 20% Text | Users write vague prompts |
| File cleanup | 5-30 day retention | Use existing trash system |

### Success Criteria

- [ ] Processing page shows within 200ms of submit
- [ ] AI generation completes in 5-10 seconds (typical)
- [ ] Fallback mode works on AI timeout
- [ ] User can cancel during processing
- [ ] Files renamed for SEO after completion

---

## ⏸️ Phase K: Collections Feature (ON HOLD at 95%)

### ⚠️ DON'T FORGET: This is unfinished and needs to be resumed!

**Status:** ~96% Complete - Paused in December 2025
**Why Paused:** Needed to build media infrastructure (Phase L) and video moderation (Phase M) first  
**When to Resume:** After Phase N is complete and deployed

### What Are Collections?

Think Pinterest boards. Users can:
- Save any prompt to their collections
- Create named collections ("Cyberpunk Art", "Portrait Prompts", etc.)
- Make collections public or private
- View all saved prompts via profile "Saves" tab

### Why This Matters

1. **Competitive advantage:** PromptHero (main competitor) doesn't have collections
2. **User retention:** People come back to manage their saves
3. **Premium conversion:** Collection limits drive upgrades

### What's DONE ✅

All core functionality works:

| Micro-Spec | What It Does | Status |
|------------|--------------|--------|
| #1 | Save button on prompt detail page | ✅ |
| #2 | Save button on prompt cards (grid) | ✅ |
| #2.5 | Button hover effects + modal CSS | ✅ |
| #3-5b | Collection & CollectionItem models | ✅ |
| #6-8 | Modal template + JavaScript | ✅ |
| #9 | API: Get user's collections | ✅ |
| #10 | API: Add prompt to collection | ✅ |
| #11 | API: Remove prompt from collection | ✅ |
| #12 | API: Create new collection | ✅ |
| #13 | Wire modal to all APIs | ✅ |
| #14 | Profile "Saves" tab | ✅ |

### What's NOT DONE ❌

#### K.2: Enhanced Features (Estimated: 1-2 weeks when resumed)

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Download Tracking** | Record when users download prompts | Analytics, "most downloaded" lists |
| **"Your Downloads" collection** | Virtual collection showing all downloaded prompts | Users can find prompts they downloaded before |
| **"Your Likes" collection** | Virtual collection showing all liked prompts | Quick access to favorites |
| Collection reordering | Drag-drop to reorder prompts within collection | Nice-to-have UX |
| Collection covers | Custom cover image for each collection | Visual appeal |

#### K.3: Premium Features (Estimated: 1 week when resumed)

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Collection limits** | Free: 10 collections, Premium: unlimited | Drive premium conversion |
| **Private collection limits** | Free: 2 private, Premium: unlimited | Drive premium conversion |
| **Upgrade prompts** | "Upgrade to Premium" modal when limit hit | Revenue |
| Collection analytics | How many people viewed/saved your public collection | Premium perk |

### Database Models (Already Created)

```python
class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_by = models.ForeignKey(User, null=True, ...)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['collection', 'prompt']  # Can't add same prompt twice
```

### Key Files for Phase K

```
MODELS:
prompts/models.py                    # Collection, CollectionItem at bottom of file

VIEWS:
prompts/views/collection_views.py    # All API endpoints (~440 lines)

JAVASCRIPT:
static/js/collections.js             # Modal open/close, API calls (~273 lines)

TEMPLATES:
prompts/templates/prompts/partials/_collection_modal.html

CSS:
static/css/style.css                 # Lines ~700-793 have modal styles
```

---

## ✅ Phase L: Media Infrastructure (COMPLETE)

**Completed:** January 2026  
**Goal:** Move from Cloudinary to Backblaze B2 + Cloudflare CDN

### Why We Did This

| Problem with Cloudinary | How B2 Fixes It |
|------------------------|-----------------|
| NSFW policy too strict (rejected legitimate AI art) | B2 has no content restrictions |
| Expensive at scale | B2 is ~70% cheaper |
| Server had to proxy all uploads | Browser uploads directly to B2 |

### What Was Built

| Feature | Description |
|---------|-------------|
| L1-L5 | Core B2 bucket setup, Cloudflare CDN integration |
| L6 | Video support (B2 video URLs, thumbnails) |
| L7 | Legacy Cloudinary fallback (old prompts still work) |
| L8 | Quick mode - presigned URLs for direct upload |
| L8-DIRECT | Browser uploads directly to B2 (no server middleman) |
| L9 | Orphan file cleanup (delete abandoned uploads) |
| L10 | SEO review queue when AI fails silently |
| L11 | Documentation |

---

## ✅ Phase M: Video Moderation (COMPLETE)

**Completed:** January 2026  
**Goal:** Check videos for NSFW content before allowing upload

### How It Works

```
1. Video uploads to B2
      ↓
2. FFmpeg extracts 3 frames (at 25%, 50%, 75% of video)
      ↓
3. Each frame sent to OpenAI Vision API
      ↓
4. If ANY frame is "critical" severity → VIDEO REJECTED
   If ANY frame is "high" severity → VIDEO FLAGGED for review
   Otherwise → VIDEO APPROVED
```

### What Was Built

| Feature | Description | Status |
|---------|-------------|--------|
| M1 | FFmpeg frame extraction | ✅ Done |
| M2 | OpenAI Vision NSFW analysis | ✅ Done |
| M3 | Frame position optimization | 🔲 Deferred |
| M4 | Video metadata extraction | 🔲 Deferred |
| M5 | Video dimensions (prevents layout shift) | ✅ Done |
| M6 | Video length limits | 🔲 Deferred |

---

## 🔲 Phase H: Username System (PLANNED)

**Status:** Not Started  
**Priority:** Medium  
**Estimated:** 1 week

### Features

| Feature | Description |
|---------|-------------|
| Username editing | Users can change their username |
| Rate limit | Max 2 changes per week |
| Profanity filter | Block offensive usernames |
| Grace period | Old username reserved for 3 days |

### Why Rate Limit?

- Usernames are personal branding
- Followers recognize usernames  
- Prevents confusion and abuse
- 2x/week allows corrections without constant changes

---

## ✅ Phase 2B: Category Taxonomy Revamp + Tag Pipeline (2B-1 through 2B-9 + S80-81 COMPLETE)

**Completed:** February 9-12, 2026
**Design Doc:** `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md`
**Execution Roadmap:** `docs/PHASE_2B_AGENDA.md`

### What Was Built

Three-tier taxonomy system for prompt classification:
- **Tier 1:** 46 subject categories (expanded from 25)
- **Tier 2:** 109 descriptors across 10 types (gender, ethnicity, age, features, profession, mood, color, holiday, season, setting)
- **Tier 3:** Up to 10 tags per prompt (increased from 5)

Plus: Admin metadata editing, security hardening, tag validation pipeline, compound preservation, audit tooling.

### Sub-Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 2B-1 | ✅ Complete | SubjectDescriptor model, taxonomy expansion, 5 migrations |
| 2B-2 | ✅ Complete | Three-tier AI prompt in tasks.py, descriptor parsing |
| 2B-3 | ✅ Complete | Upload flow descriptor assignment from cache/session |
| 2B-4 | ✅ Complete | 6-factor related prompts scoring (30/25/35/5/3/2 — rebalanced in 2B-9c with IDF weighting) |
| 2B-5 | ✅ Complete | Full AI content backfill (51 prompts, 0 errors) |
| 2B-6 | ✅ Complete | SEO demographic strengthening (ethnicity/gender rules) |
| 2B-7 | ✅ Complete | Tag demographic refinements (banned ethnicity, gender confidence) |
| 2B-8 | ✅ Complete | Exact tag filtering (`?tag=` parameter), video display fix |
| 2B-9a | ✅ Complete | Weight rebalance: 90/10 content/tiebreaker split |
| 2B-9b | ✅ Complete | IDF weighting for tags and categories |
| 2B-9c | ✅ Complete | IDF weighting for descriptors, rebalanced to 30/25/35/5/3/2 |
| 2B-9d | ✅ Complete | Stop-word filtering (infrastructure ready, disabled at 51 prompts), published-only IDF counting |
| S80: Admin | ✅ Complete | Enhanced PromptAdmin, SlugRedirect model, B2 preview, XSS safeguards, dynamic weights, regenerate button |
| S80: Security | ✅ Complete | Auth decorators on destructive views, CSRF on delete, form validation |
| S81: Backfill | ✅ Complete | `--tags-only`, `--under-tag-limit`, `--published-only` flags |
| S81: Validation | ✅ Complete | `_validate_and_fix_tags()` 7-check pipeline, compound preservation |
| S81: GPT Context | ✅ Complete | COMPOUND TAG RULE, WEIGHTING RULES, excerpt in tags-only prompt |
| S81: Audit | ✅ Complete | `audit_tags` command, root-level audit scripts, `cleanup_old_tags` rewrite |
| S81: Tests | ✅ Complete | 130 new tests (113 validate + 17 context), all passing |
| S82: Hardening | ✅ Complete | Fail-fast download, `_is_quality_tag_response()` quality gate, `GENERIC_TAGS`, `_check_image_accessible()` |
| S82: Cleanup | ✅ Complete | Module-level constants, removed dead code, fixed fallback tags, temperature 0.7→0.5 |
| S82: Tests | ✅ Complete | 44 new tests (`test_backfill_hardening.py`), 7 existing tests updated, total 472 |

### Remaining From Original Agenda

| Task | Status | Notes |
|------|--------|-------|
| Cloudinary → B2 media migration | 🔲 Not started | Original 2B-6 in agenda, independent of taxonomy |
| Browse/Filter UI | 🔲 Not started | Original 2B-7 in agenda, needs all data in place |
| Backfill re-run with hardening | 🔲 Not started | Re-run `backfill_ai_content --tags-only` with quality gate + fail-fast active |
| Tag audit post-hardening | 🔲 Not started | Run `audit_tags` after backfill re-run to verify improvement |
| IDF stop-word threshold | 🔲 Not started | Enable at 0.25 threshold when 200+ prompts (currently disabled at 1.0) |

---

## 📋 Future Features (After Phase N)

### Pre-Launch Checklist

| Task | Priority | Notes |
|------|----------|-------|
| XML Sitemap | High | `prompts/sitemaps.py` - deferred from N4i |
| Run indexes migration | High | `makemigrations` + `migrate` for composite indexes |
| Debug N4h rename trigger | Medium | Code complete, needs production debugging |
| Font Awesome full removal | Low | 30+ new SVG sprite icons needed, already non-render-blocking |
| Commit all uncommitted changes | Critical | Many sessions of uncommitted work |
| Deploy and test end-to-end | Critical | Full production validation |

### Tier 1: Critical (Q1 2026)

| Feature | Effort | Notes |
|---------|--------|-------|
| Premium Tier System | 2-3 weeks | Stripe subscriptions, collection limits |
| Phase K.2 completion | 1-2 weeks | Download tracking, virtual collections |
| Comment Pagination | 2-3 days | "Load more" for comments |
| Social Sharing | 1-2 days | Twitter, Pinterest share buttons |

### Tier 2: High (Q2 2026)

| Feature | Effort | Notes |
|---------|--------|-------|
| Related Prompts | 1 week | ✅ Phase 1 done (Session 74), scoring refined in 2B-9 (IDF-weighted) |
| Image Lightbox | 3-4 days | Click to zoom |
| Notification System | 2 weeks | In-app notifications |
| Search Improvements | 2 weeks | Autocomplete, filters |

---

## 🤖 Development Rules

### Micro-Spec Methodology

After multiple failures with big specs (CC ignores details, gives false high ratings):

1. **Each spec** = 10-20 lines of code maximum
2. **Manual testing** after each spec
3. **Agent validation** required (8+/10 average)
4. **Never combine** multiple features in one spec

### File Size Limits

| Size | CC Can Edit? |
|------|--------------|
| < 500 lines | ✅ Yes |
| 500-1000 lines | ⚠️ Careful |
| > 1000 lines | ❌ Edit manually |

### Agent Workflow

1. **During implementation:** Use wshobson/agents in Claude Code
2. **After implementation:** Use Claude.ai review personas
3. **Required rating:** 8+/10 average before committing

---

**Version:** 4.1 (Session 82 — Backfill hardening, quality gate, fail-fast download, tasks.py cleanup)
**Last Updated:** February 13, 2026
