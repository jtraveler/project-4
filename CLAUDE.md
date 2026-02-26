# CLAUDE.md - PromptFinder Project Documentation (1 of 3)

## ⚠️ IMPORTANT: This is Part 1 of 3

**Before proceeding, also read:**
- **CLAUDE_PHASES.md** - Phase specs, unfinished work details
- **CLAUDE_CHANGELOG.md** - Session history, recent changes

These three files together replace the original CLAUDE.md.
Do NOT edit or reference this document without reading all three.

---

**Last Updated:** February 26, 2026
**Project Status:** Pre-Launch Development

**Owner:** Mateo Johnson - Prompt Finder

> **📚 Document Series:**
> - **CLAUDE.md** (1 of 3) - Core Reference ← YOU ARE HERE
> - **CLAUDE_PHASES.md** (2 of 3) - Phase Specifications & Unfinished Work
> - **CLAUDE_CHANGELOG.md** (3 of 3) - Session History

---

## 🚫 DO NOT MOVE — Core Root Documents

The following files MUST stay in the project root. They are referenced by CLAUDE.md, handoff templates, and CC specs. Moving them to `docs/` or elsewhere will break cross-references.

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Core project reference (1 of 3) |
| `CLAUDE_PHASES.md` | Phase specs & unfinished work (2 of 3) |
| `CLAUDE_CHANGELOG.md` | Session history (3 of 3) |
| `CC_COMMUNICATION_PROTOCOL.md` | Agent requirements for Claude Code |
| `CC_SPEC_TEMPLATE.md` | Standard template for CC specifications |
| `AGENT_TESTING_SYSTEM.md` | 8-persona review system |
| `HANDOFF_TEMPLATE_STRUCTURE.md` | Session handoff document template |
| `PROJECT_FILE_STRUCTURE.md` | Complete file tree |
| `README.md` | Public-facing project README |

> **If you reorganize the repo**, update every cross-reference in all nine files above plus any active specs.

---

## 📋 Quick Status Dashboard

### What's Active Right Now

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase N4** | 🔄 ~99% Complete | Optimistic Upload Flow | XML sitemap, indexes migration, final testing |
| **Phase N3** | 🔄 ~95% | Single-Page Upload | Final testing, deploy to prod |

### What's Paused (Don't Forget!)

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase K** | ⏸️ ~96% | Collections ("Saves") | Trash video bugs (3), K.2: Download tracking, virtual collections; K.3: Premium limits |

### Recently Completed

| Phase | When | What It Was |
|-------|------|-------------|
| Phase R1 + R1-D | Feb 17-18, 25-26, 2026 | User Notification System (model, signals, API, bell dropdown, notifications page redesign with avatars/quotes/action buttons, per-card mark-as-read, bell sync, dedup fix, shared tab components, delete all/per-card delete, Load More pagination, two-phase delete animation, staggered fade-in, reverse signal handlers, real-time polling, "Updates available" banner, cross-component DOM event sync) |
| Phase 2B (1-9) + Tag Pipeline + Hardening + Pass 2 SEO | Feb 9-16, 2026 | Category Taxonomy Revamp, tag validation pipeline, admin metadata, security hardening, backfill hardening, tag pipeline refinements, Pass 2 background SEO, admin UX |
| Phase 2B (1-8) | Feb 9-10, 2026 | Category Taxonomy Revamp: 46 categories, 109 descriptors, AI backfill, demographic SEO rules |
| Subject Categories P2 | Feb 9, 2026 | AI-assigned prompt classification (25 categories, cache-first logic) |
| Related Prompts P1 | Feb 7, 2026 | "You Might Also Like" section on prompt detail (scoring algorithm, AJAX Load More) |
| Phase L | Jan 2026 | Media Infrastructure (moved from Cloudinary to B2 + Cloudflare) |
| Phase M | Jan 2026 | Video NSFW Moderation (FFmpeg frame extraction + OpenAI Vision) |
| Phase J | Dec 2025 | Prompt Detail Page Redesign |

---

## 🚀 Current Phase: N4 - Optimistic Upload Flow

**Status:** ~99% Complete - Lighthouse 96/100/100/100, All Core Features Done
**Detailed Spec:** See `docs/PHASE_N4_UPLOAD_FLOW_REPORT.md`

### Overview
Rebuilding upload flow to feel "instant" by:
- Processing images in background while user types
- Using dedicated processing page with polling
- Running AI analysis after submit
- Deferring file renaming for faster perceived performance

### Implementation Progress

| Sub-Phase | Status | What It Does |
|-----------|--------|--------------|
| **N4a** | ✅ Complete | Model fields: `processing_uuid`, `processing_complete` |
| **N4b** | ✅ Complete | Django-Q2 setup with PostgreSQL ORM broker |
| **N4c** | ✅ Complete | Admin fieldset updates for processing fields |
| **N4d** | ✅ Complete | Processing page template and view |
| **N4e** | ✅ Complete | AI job queuing for videos (uses thumbnail) |
| **N4f** | ✅ Complete | ProcessingModal in upload-form.js |
| **N4 Cleanup** | ✅ Complete | Removed old upload code (step templates, processing.js) |
| **SEO Meta** | ✅ Complete | OG/Twitter blocks, Schema.org JSON-LD + VideoObject, canonical URLs |
| **AI Quality** | ✅ Complete | Style-first titles, description truncation fix, race/ethnicity identification |
| **SEO Enhance** | ✅ Complete | Race/ethnicity in AI prompts, enhanced alt tags, Schema.org VideoObject (Session 64) |
| **N4g Video Fix** | ✅ Resolved | Video submit "Upload data missing" - session key mismatch fixed |
| **CI/CD Fixes** | ✅ Complete | Fixed 31 issues across 9 files, all 3 CI/CD jobs passing (Session 64) |
| **Worker Dyno** | ✅ Complete | Heroku worker dyno configured for Django-Q processing (Session 64) |
| **Collection Edit** | ✅ Complete | Created collection_edit.html, fixed 500 error on edit page (Session 64) |
| **Upload Redesign** | ✅ Complete | Complete visual redesign of upload page with modern card layout (Session 64) |
| **Upload Polish** | ✅ Complete | File input reset fix, visibility toggle, native aspect ratio preview (Session 66) |
| **CSS Architecture** | ✅ Complete | Shared media container component, 22 border-radius unified to var(--radius-lg) (Session 66) |
| **SEO Overhaul** | ✅ Complete | Comprehensive SEO: JSON-LD, OG/Twitter, canonical, headings, noindex drafts (72→95/100) (Session 66) |
| **SEO Headings** | ✅ Complete | Fixed heading hierarchy (H1→H2→H3), visual breadcrumbs with focus-visible (Session 67) |
| **N4h File Rename** | ✅ Complete | B2 SEO file renaming: seo.py utility, B2RenameService, background task in tasks.py (Session 67) |
| **Admin Improvements** | ✅ Complete | Prompt ID display, B2 Media URLs fieldset, all fieldsets expanded (Session 68) |
| **Upload UX** | ✅ Complete | 30-second soft warning toast, improved error message with friendly copy (Session 68) |
| **Perf: Backend** | ✅ Complete | select_related/prefetch_related optimization, materialized likes/comments, query reduction ~60-70% (Session 68) |
| **Perf: Caching** | ✅ Complete | Template fragment caching for tags and more_from_author (5-min TTL) (Session 68) |
| **Perf: Indexes** | ✅ Complete | Composite indexes: (status,created_on), (author,status,deleted_at) - migration pending (Session 68) |
| **Perf: Frontend** | ✅ Complete | Critical CSS inlining, async CSS loading, LCP preload with imagesrcset, preconnect hints, JS defer (Session 68) |
| **SEO: robots.txt** | ✅ Complete | Created robots.txt served via WHITENOISE_ROOT (HTTP 200, no redirect) (Session 69) |
| **Perf: CSS Optim** | ✅ Complete | Removed stale preconnects, reduced font weights (4→3), deferred icons.css with noscript fallback (Session 69) |
| **A11y Fixes** | ✅ Complete | Fixed heading hierarchy (h3→h2), aria-label mismatches with pluralize filter (Session 69) |
| **Asset Minification** | ✅ Complete | Management command for CSS/JS minification targeting STATIC_ROOT (Session 69) |

### Key Components
1. **Variant generation after NSFW** - Start thumbnails while user types
2. **Processing page** - `/prompt/processing/{uuid}/` with polling ✅ IMPLEMENTED
3. **Django-Q background tasks** - AI generation runs async
4. **Deferred file renaming** - SEO filenames applied after "ready"
5. **Fallback handling** - Graceful degradation on AI failure

### Target Performance
- Upload page → Submit: **0 seconds wait** (processing happens after)
- Processing page → Ready: **5-10 seconds**
- Total perceived improvement: **50-60% faster**

### Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Background tasks | Django-Q2 | Free, uses PostgreSQL, no Redis needed |
| Status updates | Polling (3s) | Simple, reliable, Heroku compatible |
| AI analysis ratio | 80% Vision / 20% Text | Users often write vague prompts |
| File cleanup | 5-30 day retention | Use existing trash system |

### Current Blockers

| Issue | Description | Impact |
|-------|-------------|--------|
| **N4h rename not triggering** | `rename_prompt_files_for_seo` task is coded but not generating SEO filenames in production | Files keep UUID names instead of SEO slugs |
| **Indexes migration pending** | Composite indexes added to models.py but `makemigrations` not yet run | Indexes not active in database |
| **CI/CD pipeline failing** | All 3 jobs (Django Tests, Code Linting, Security Scan) failing | Blocks merge to main — top priority for Session 89 |

**N4h Root Cause (Suspected):** The rename task queues after AI content generation completes, but may not be triggering due to Django-Q worker configuration or the task not being picked up. Needs investigation.

**Resolved in Session 69:** SEO score regression (92→100) fixed via robots.txt + preconnect cleanup + font optimization.

### Phase K Known Bugs (Session 73)

| Bug | Description | Impact |
|-----|-------------|--------|
| Video poster aspect ratio | Poster images may crop to wrong aspect ratio with `object-fit: cover` | Visual glitch |
| Mobile play icon resize | Play icon doesn't reappear after desktop→mobile resize | Minor UX |
| Videos at ≤768px | Videos disappear on homepage/gallery at mobile breakpoint | Needs investigation |

### Related Prompts Feature (Phase 2B-9 Complete)

"You Might Also Like" section on prompt detail pages. Full design: `docs/DESIGN_RELATED_PROMPTS.md`.

| Component | Details |
|-----------|---------|
| **Scoring algorithm** | `prompts/utils/related.py` — 6-factor IDF-weighted scoring (275 lines) |
| **Weights** | 30% tags, 25% categories, 35% descriptors, 5% generator, 3% engagement, 2% recency |
| **Content split** | 90% content similarity (tags+categories+descriptors) / 10% tiebreakers |
| **IDF weighting** | `1 / log(count + 1)` — rare items worth more; published-only counting |
| **Stop-word threshold** | Infrastructure ready, disabled at 1.0 (re-enable at 0.25 when 200+ prompts) |
| **Pre-filter** | Must share at least 1 tag, category, OR descriptor (max 500 candidates) |
| **AJAX endpoint** | `/prompt/<slug>/related/` — 18 per page, 60 max |
| **Layout** | CSS `column-count` responsive grid (4→3→2→1 columns) |
| **Video autoplay** | IntersectionObserver on desktop (skip mobile/reduced-motion) |
| **Load More** | Reinitializes video observer after appending new cards |

### Subject Categories & Descriptors (Phase 2B)

Three-tier AI taxonomy for prompt classification, expanded from initial 25-category system.

| Component | Details |
|-----------|---------|
| **SubjectCategory model** | name, slug, description, display_order — 46 categories |
| **SubjectDescriptor model** | name, slug, descriptor_type — 109 descriptors across 10 types |
| **Prompt.categories** | M2M field (1-5 categories per prompt) |
| **Prompt.descriptors** | M2M field (up to 10 descriptors per prompt) |
| **AI assignment** | During upload via OpenAI Vision prompt, written to cache at 90% progress |
| **Descriptor types** | gender, ethnicity, age, features, profession, mood, color, holiday, season, setting |
| **Migrations** | `0046`-`0047` (initial categories), `0048`-`0049` (descriptors), `0050` (category updates), `0051`-`0052` (fixes) |
| **Backfill** | `python manage.py backfill_ai_content` — regenerates all AI content for existing prompts |
| **Admin** | `SubjectCategoryAdmin` + `SubjectDescriptorAdmin` with read-only enforcement |

### Phase 2B: Category Taxonomy Revamp (2B-1 through 2B-8 COMPLETE)

Full design in `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md`, execution roadmap in `docs/PHASE_2B_AGENDA.md`.

| Sub-Phase | Status | What It Does |
|-----------|--------|--------------|
| **2B-1** | ✅ Complete | SubjectDescriptor model, taxonomy expansion (46 cats, 109 descs) |
| **2B-2** | ✅ Complete | AI prompt update for three-tier taxonomy |
| **2B-3** | ✅ Complete | Upload view descriptor assignment |
| **2B-4** | ✅ Complete | Descriptor-aware related prompts scoring (6-factor) |
| **2B-5** | ✅ Complete | Full AI content backfill (51 prompts, 0 errors) |
| **2B-6** | ✅ Complete | SEO demographic strengthening (ethnicity/gender in titles/descriptions) |
| **2B-7** | ✅ Complete | Tag demographic refinements (ethnicity banned from tags, gender confidence rules) |
| **2B-8** | ✅ Complete | Tag filter fix (exact tag matching via `?tag=`), video display fix |
| **2B-9a** | ✅ Complete | Weight rebalance: 90/10 content/tiebreaker split |
| **2B-9b** | ✅ Complete | IDF weighting for tags and categories |
| **2B-9c** | ✅ Complete | IDF weighting for descriptors, rebalanced to 30/25/35/5/3/2 |
| **2B-9d** | ✅ Complete | Stop-word filtering (infrastructure ready, disabled at 51 prompts), published-only IDF counting |

### Demographic SEO Rules (Phase 2B-6/2B-7)

| Rule | Where Applied | Details |
|------|---------------|---------|
| **Ethnicity** | Title, description, descriptors | REQUIRED when person visible; BANNED from tags (17 banned words) |
| **Gender** | Title, description, descriptors, tags | REQUIRED when person visible; both forms in tags (man+male, woman+female) |
| **80% confidence** | All | Use "person" when gender unclear |
| **Age terms** | All | boy/girl, teen-boy/teen-girl, baby/infant for children |
| **Auto-flag** | `needs_seo_review` | Flagged when gender detected but ethnicity missing |
| **AI-related tags** | Tags | No longer mandatory (removed Session 80); `ALLOWED_AI_TAGS` whitelist (5 terms) permits ai-prefixed tags |

### Tag System Rules (Phase 2B + Sessions 80-85)

- 10 tags per prompt (increased from 5)
- 17 ethnicity terms banned from tags (african-american, asian, caucasian, etc.)
- Gender tags retained (man/woman/male/female) — zero SEO controversy
- Tags created via `get_or_create` (new tags auto-created for long-tail SEO)
- **AI-related tags no longer mandatory** (removed via `remove_mandatory_tags` command, Session 80)

**3-Layer Tag Quality System (Session 83):**
- **Layer 1 — GPT (expert):** Self-check rule 7 validates compounds before returning; `compounds_check` field is chain-of-thought trick (generated by GPT, discarded by parser)
- **Layer 2 — Validator (safety net):** `_validate_and_fix_tags()` — mechanical checks only (stop words, banned terms, single-char, dedup, demographic reorder)
- **Layer 3 — Pass 2 (BUILT, Session 85):** Background SEO expert review post-publish using Django-Q2 + gpt-4o-mini via `queue_pass2_review()`. Triggered by admin "Optimize Tags & Description" button or `run_pass2_review` management command. Protects title, slug, categories, descriptors via `PROTECTED_TAGS` constant.

**Philosophy:** GPT makes SEO judgment calls, validator handles mechanical issues only. Scaling to thousands of prompts without manual intervention.

**Tag Validation Pipeline (`_validate_and_fix_tags()` in tasks.py):**
8-check post-processing pipeline runs on every GPT response before saving:
1. Strip whitespace / reject empty tags
2. Lowercase all tags
3. Reject banned AI tags (with `ALLOWED_AI_TAGS` exceptions: ai-influencer, ai-avatar, ai-headshot, ai-girlfriend, ai-boyfriend)
4. Reject banned ethnicity tags (17 terms)
5. Compound tag splitting via `_should_split_compound()` — stop words discarded (not kept as tags), `PRESERVE_SINGLE_CHAR_COMPOUNDS` respected (12 entries: x-ray, 3d-render, k-pop, etc.)
6. Deduplicate tags
7. Enforce 10-tag maximum
8. Demographic tag reorder — `DEMOGRAPHIC_TAGS` (16 entries: man, male, woman, female, boy, girl, etc.) moved to end of tag list for UX consistency

**Tag Ordering (Session 85):**
- Tags display in validated insertion order on detail/edit pages via `ordered_tags()` model method
- `ordered_tags()` queries `TaggedItem` by `id` (insertion order) to preserve validation pipeline ordering
- Pass 1 uses `clear()` + sequential `add()` in `_apply_ai_m2m_updates()` (not `tags.set()` which doesn't preserve order)
- `GENDER_LAST_TAGS` constant: demographic tags (man, male, woman, female, etc.) moved to end of tag list
- `PROTECTED_TAGS` constant: title, slug, categories, descriptors — never modified by Pass 2
- `reorder_tags` management command: retroactively reorders existing prompts' tags per validation rules
- `escapejs` filter on tag name onclick handlers for XSS protection

**Compound Tag Preservation (COMPOUND TAG RULE):**
- Default: **preserve compound tags** (e.g., "double-exposure" stays as-is)
- Only split if **both** halves are stop/filler words from `SPLIT_THESE_WORDS` set (30 words)
- `PRESERVE_DESPITE_STOP_WORDS` exemption set for known terms (e.g., "pin-up")
- `PRESERVE_SINGLE_CHAR_COMPOUNDS` set for terms with single-char prefixes (12 entries: x-ray, 3d-render, k-pop, etc.)
- Helper: `_should_split_compound(tag)` returns True only if split should occur
- GPT prompt includes COMPOUND TAG RULE instructing AI to use hyphens for multi-word concepts
- **Stop words from splits are discarded** (not kept as individual tags) — Session 83

**TAG_RULES_BLOCK (Session 83):**
- Single source of truth for tag rules across both GPT prompts (`_call_openai_vision` and `_call_openai_vision_tags_only`)
- ~76 lines of canonical tag instructions extracted into module-level constant
- Eliminates the "Two GPT prompt copies" maintenance burden (previously a known issue)

**SEO Research Finding (Session 83):**
Google treats hyphens as word separators. Compound tags give DUAL search coverage (compound term + individual words). Splitting compounds destroys search intent and wastes tag slots.

**Backfill Hardening (Session 82):**
Three-layer defense against silent data corruption during backfill:
1. **Fail-fast download:** `_download_and_encode_image()` returns `None` on failure → callers (`_call_openai_vision`, `_call_openai_vision_tags_only`) return `{'error': ...}` instead of falling back to raw URL
2. **Quality gate:** `_is_quality_tag_response()` checks min 3 tags, no all-caps responses, max 60% generic ratio. Uses `GENERIC_TAGS` constant (32 entries with singular/plural forms)
3. **URL pre-check:** `_check_image_accessible()` HEAD request in backfill before calling OpenAI

If any layer fails, existing tags are PRESERVED — never overwritten with garbage.

**GPT Temperature Settings:**
- Full generation (`_call_openai_vision`): temperature=0.5 (titles need some creativity)
- Tags-only (`_call_openai_vision_tags_only`): temperature=0.3 (strict rule compliance)

**WEIGHTING RULES in GPT Prompt:**
- PRIMARY source: The image itself (what you see)
- SECONDARY: Title + description (if provided)
- TERTIARY: User's prompt text (often vague/misleading)
- UNRELIABLE: Never assume style from prompt text alone

**Tag Context Enhancement:**
- `_call_openai_vision_tags_only()` receives excerpt for context
- Excerpt truncated at 500 chars in GPT prompt
- Backfill passes `excerpt=prompt.excerpt` to tags function

### Title Generation Rules (Phase 2B-6)

- 40-60 characters
- No filler words (in, at, with, the, and, overlooking, featuring, standing)
- Ethnicity + gender in first 3-4 words when person visible
- Every word should be a searchable keyword

### Slug Configuration (Phase 2B)

- `Prompt.slug` max_length: 200 (was 50)
- Code limit in `_generate_unique_slug_with_retry`: 200 (was 50)
- `SubjectCategory.slug` max_length: 200

### Admin Metadata Editing (Sessions 80, 85)

Enhanced PromptAdmin with full metadata editing capabilities and safeguards:

| Feature | Details |
|---------|---------|
| **SlugRedirect model** | Auto-creates 301 redirect when admin changes slug (migration 0053) |
| **B2 preview images** | Thumbnail previews in admin via `_b2_preview()` method |
| **XSS protection** | `format_html()` used for all admin HTML output |
| **Character limits** | Title 200 chars, excerpt 500 chars — enforced in admin form |
| **Dynamic weights** | Related prompts weights editable via admin (reads from `related.py`) |
| **Slug protection** | Admin change auto-creates SlugRedirect for SEO preservation |
| **Tag autocomplete** | django-taggit autocomplete restored after initial removal |
| **Admin templates** | `change_form_object_tools.html`, `change_form.html`, `regenerate_confirm.html` |

**Two-Button Admin System (Session 85):**

| Button | Label | Action | What It Changes |
|--------|-------|--------|-----------------|
| **Blue (Pass 2)** | "Optimize Tags & Description" | `seo_review_view` → `queue_pass2_review()` | Tags + description ONLY. Title, slug, categories, descriptors protected. |
| **Red (Pass 1+2)** | "Rebuild All Content" | `regenerate_view` → full AI regen + auto-queues Pass 2 | EVERYTHING: title, description, tags, categories, descriptors. Slug preserved. |

- Buttons styled with `border-radius: 20px` (rounded pills)
- Help text block below buttons with `clear: both` positioning (in `change_form.html`)
- Bulk action dropdown labels match: "Optimize Tags & Description (Pass 2)" / "Rebuild All Content (Pass 1 + 2)"
- Pass 1 tag ordering uses `clear()` + sequential `add()` to preserve validated order

### Security Hardening (Session 80)

| Fix | Details |
|-----|---------|
| **Auth decorators** | `@login_required` + `@require_POST` added to `prompt_delete`, `prompt_toggle_visibility` |
| **CSRF on delete** | Prompt detail delete button uses POST form with CSRF token (was GET link) |
| **Admin save_model** | XSS-safe `format_html()`, ownership validation, SlugRedirect auto-creation |
| **Form validation** | `clean_title()` / `clean_excerpt()` enforce character limits server-side |

### Tag Filter System (Phase 2B-8)

- Tag clicks use `?tag=` parameter with exact Django-taggit matching (`tags__name=tag_name`)
- Text search uses `?search=` parameter with `icontains`
- `.distinct()` applied to prevent M2M join duplicates

### Backfill Management Command

```
python manage.py backfill_ai_content --dry-run                 # Preview only
python manage.py backfill_ai_content --limit 10                # Process 10
python manage.py backfill_ai_content --prompt-id 42            # Single prompt
python manage.py backfill_ai_content --batch-size 10 --delay 3 # Rate control
python manage.py backfill_ai_content --skip-recent 7           # Skip last 7 days
python manage.py backfill_ai_content --tags-only               # Regenerate tags only (Session 81)
python manage.py backfill_ai_content --under-tag-limit 5       # Only prompts with < N tags (Session 81)
python manage.py backfill_ai_content --published-only           # Published prompts only (default: all)
```

Regenerates title, slug, description, tags, categories, and descriptors for existing prompts using Phase 2B three-tier taxonomy prompt. `--tags-only` mode skips title/description/categories/descriptors and only regenerates tags via `_call_openai_vision_tags_only()`.

### Reorder Tags Management Command (Session 85)

```
python manage.py reorder_tags                        # Reorder all prompts
python manage.py reorder_tags --dry-run              # Preview only
python manage.py reorder_tags --prompt-id 42         # Single prompt
```

Retroactively reorders existing prompts' tags per validation pipeline rules (demographic tags to end via `GENDER_LAST_TAGS`). Uses `clear()` + sequential `add()` to preserve insertion order.

### Run Pass 2 Review Management Command (Session 85)

```
python manage.py run_pass2_review                    # Review all published prompts
python manage.py run_pass2_review --dry-run          # Preview only
python manage.py run_pass2_review --prompt-id 42     # Single prompt
python manage.py run_pass2_review --limit 10         # Process N prompts
```

Runs Pass 2 SEO expert review on published prompts. Optimizes tags and description only — title, slug, categories, descriptors protected via `PROTECTED_TAGS`.

### Known Issues/Limitations (Phase 2B)

- **OpenAI Vision inconsistency:** Same image can return different demographics across runs
- **Auto-flag gap:** `needs_seo_review` doesn't trigger when neither gender nor ethnicity assigned (only when gender present but ethnicity missing)
- **Compound edge cases:** Preserve-by-default allows overly-specific compounds where both words are non-stop-words. GPT self-check (rule 7 + `compounds_check`) now catches most cases at Layer 1. 3-part compound split was attempted and reverted (Session 83) — too aggressive.
- **~~Two GPT prompt copies~~** — CLOSED (Session 83): Resolved by `TAG_RULES_BLOCK` constant — single source of truth for tag rules in both GPT prompts.
- **~~WEIGHTING RULES parity~~** — CLOSED: Upload path calls `_call_openai_vision()` with empty prompt_text (user hasn't submitted yet), so WEIGHTING RULES don't apply. Not a gap.
- **~~Anti-compound coverage gap~~** — CLOSED: Both GPT prompts already have identical WRONG examples covering all reported gaps. Session 81 validator catches remainder.

### Backfill Status

- **Last full backfill:** Session 83, February 14, 2026
- **Result:** 51/51 prompts updated, 0 errors
- **Applied:** All tag pipeline improvements (self-check, AI exceptions, stop-word discarding, demographic reorder)
- **Orphan tag cleanup** needed after backfill (flagged, not yet run)

### Future Architecture (Planned, NOT Built)

- **~~Pass 2 background SEO expert~~** — BUILT (Session 85): `queue_pass2_review()` in tasks.py, admin button, `run_pass2_review` management command. Uses gpt-4o-mini + PROTECTED_TAGS.
- **Embedding generation:** Will be added to Pass 2 background task for future related prompts via pgvector.
- **Related prompts via embeddings:** Tag-based similarity (current, quick win) → embeddings + pgvector (later).

### Technical Patterns (Session 74)

**CSS `!important` cascade:**
- `masonry-grid.css` uses `!important` on many properties
- Overrides in page-specific CSS must also use `!important`
- NEVER use `!important` on properties JS controls inline (like `opacity`) — it blocks JS from toggling

**B2-aware thumbnails:**
- Always use `display_thumb_url` / `display_medium_url` properties (B2 → video thumb → Cloudinary fallback)
- NEVER use `get_thumbnail_url()` — it's Cloudinary-only and returns None for B2 prompts

**Video autoplay pattern:**
- IntersectionObserver with threshold `[0, 0.3, 0.5]`
- Skip on mobile (`window.innerWidth <= 768`) and `prefers-reduced-motion`
- CSS uses `data-initialized="true"` attribute + adjacent sibling selector to switch thumbnail from `position: relative` to `position: absolute`
- Disconnect observer before recreating (memory leak prevention)

**Cache-first categories:**
- AI writes all data (including categories) to cache at 90% progress
- `upload_views.py` checks cache before session — if cache has title, use ALL cache data
- Session fallback only when cache is truly empty

### Trash Prompts Architecture (Session 73)

The trash prompts grid uses a **self-contained card approach** with CSS columns instead of JavaScript masonry:

- **Why:** Homepage masonry JS isn't initialized on trash page, and `_prompt_card.html` video elements break in trash context
- **Solution:** Self-contained cards in `user_profile.html` (lines ~1267-1480) with `column-count` CSS layout
- **CSS:** Styles in `static/css/style.css` under "Trash video styling" section (~line 2555-2590)
- **Specificity Note:** `.trash-prompt-wrapper .trash-video-play` uses specificity 0,2,0 to beat `masonry-grid.css` `.video-play-icon` (0,1,0) which loads later

### Known Risk Pattern: Inline Code Extraction (CRITICAL)

When extracting inline `<script>` or `<style>` blocks to external files:

1. **Identify ALL code within the same tag** before making changes. The block being extracted may share a `<script>` or `<style>` tag with unrelated code.
2. **Verify tag balance after editing.** Run `grep -n '<script\|</script' [file]` to confirm every `<script>` has a matching `</script>`.
3. **Check what comes AFTER the extracted code.** If there is more JS/CSS after the removed section, ensure it's still inside a valid tag.
4. **Test ALL interactive elements** on the affected page after extraction.

**Origin:** Session 86 (Phase R1 FIX SPEC v4) — extracting overflow IIFE from `user_profile.html` left ~640 lines of follow/unfollow/modal JS outside `<script>` tags, rendering as raw text. Caught by @code-reviewer agent.

### WCAG Contrast Compliance (CRITICAL)

All text must meet WCAG 2.1 AA minimum contrast ratios:
- **Normal text (< 18px or < 14px bold):** 4.5:1 minimum
- **Large text (≥ 18px or ≥ 14px bold):** 3:1 minimum

**Safe text colors on white backgrounds:**
- `var(--gray-500, #737373)` — 4.6:1 ✅ (minimum safe for normal text)
- `var(--gray-600, #525252)` — 7.1:1 ✅
- `var(--gray-700, #404040)` — 9.7:1 ✅
- `var(--gray-800, #262626)` — 14.5:1 ✅

**UNSAFE text colors on white backgrounds (DO NOT USE for body text):**
- `var(--gray-400, #A3A3A3)` — 2.7:1 ❌ FAILS AA
- `var(--gray-300, #D4D4D4)` — 1.5:1 ❌ FAILS AA
- `opacity: 0.6` on any gray — ❌ ALWAYS CHECK, usually fails

**Rules:**
1. NEVER use `opacity` to de-emphasize text. Use an explicit `color` value instead. Opacity affects the entire element and makes contrast unpredictable.
2. NEVER use `--gray-400` or lighter for readable text on white backgrounds.
3. For de-emphasized but readable text, use `--gray-500` (#737373) as the minimum. It passes AA at 4.6:1.
4. For placeholder text or truly decorative text that isn't essential for understanding, `--gray-400` is acceptable per WCAG 1.4.3 (incidental text).

**This pattern caused WCAG violations in Phase R1 Fixes v3 and v5. Always verify contrast when selecting text colors for de-emphasis.**

### Shared UI Components (Session 86)

| Component | File | Used By |
|-----------|------|---------|
| Overflow Tabs JS | `static/js/overflow-tabs.js` | notifications.html, user_profile.html, collections_profile.html |
| Profile Tabs CSS | `static/css/components/profile-tabs.css` | Same 3 templates |
| Pexels Dropdown | `templates/base.html` (IIFE) | Explore, Profile, Bell icon dropdowns |

Options for `initOverflowTabs()`:
- `centerActiveTab: true/false` — auto-scroll active tab to center on load
- `centerWhenFits: true/false` — center tabs when they all fit (no overflow)

### Resolved Blockers (Session 64-66)

| Issue | Resolution | Session |
|-------|------------|---------|
| Change File button | Moved outside preview overlay, always visible | 66 |
| Privacy toggle | Redesigned as visibility toggle, defaults to Public | 66 |
| SEO score 72/100 | Comprehensive overhaul: JSON-LD, OG, Twitter, canonical, headings | 66 |
| Worker dyno | Configured Standard-1X worker dyno on Heroku | 64 |
| CI/CD pipeline | Fixed 31 issues across 9 files, all 3 jobs passing | 64 |
| Collection edit 500 | Created missing collection_edit.html template | 64 |
| N4g: Video submit fails | Session key mismatch fixed | 64 |
| Description truncation | `max_tokens` 500→1000, `max_length` 500→2000 | 63-64 |
| Video redirect delay | Self-resolved (was timing issue) | 64 |

### Production Infrastructure Notes

- **Heroku Worker Dyno**: Configured for Django-Q background processing
  - AI content generation tasks run asynchronously
  - Command: `heroku ps:scale worker=1 --app mj-project-4`
  - Current tier: Standard-1X ($25/month) - can downgrade to Basic ($7/month) for pre-launch
  - Procfile includes: `worker: python manage.py qcluster`

- **B2 CORS Configuration**: Must include all domains
  - `https://promptfinder.net`
  - `https://www.promptfinder.net` (CRITICAL - missing this breaks production uploads)
  - `https://mj-project-4-68750ca94690.herokuapp.com`
  - `http://localhost:8000` (development)
  - Operations: s3_put, s3_get, s3_head
  - Use B2 CLI to update: `b2 bucket update --cors-rules ...`

### Uncommitted Changes (Do Not Revert)

| File | Change |
|------|--------|
| `prompts/tasks.py` | AI prompt rewrite, `max_tokens` 500→1000, `rename_prompt_files_for_seo` task, domain allowlist, race/ethnicity (S64-S67) |
| `prompts/views/api_views.py` | AI job queuing for videos |
| `prompts/views/upload_views.py` | `.strip()` on excerpt assignment (S64) |
| `prompts_manager/settings.py` | Domain allowlist fix |
| `prompts/services/content_generation.py` | `max_tokens` 500→1000, filename 3→5 keywords, alt tag format, race/ethnicity, video description fix (S64) |
| `prompts/templates/prompts/collection_edit.html` | New template - collection edit form (S64) |
| `prompts/utils/__init__.py` | NEW - Utils package init (S67) |
| `prompts/utils/seo.py` | NEW - SEO filename generation utility (S67) |
| `prompts/services/b2_rename.py` | NEW - B2 file rename service (copy-verify-delete) (S67) |
| `prompts/templates/prompts/upload.html` | Heading hierarchy fixes, visual breadcrumbs, accessibility (S67) |
| `prompts/admin.py` | ID display, B2 Media URLs fieldset, expanded fieldsets (S68) |
| `prompts/views/prompt_views.py` | Query optimization: select_related, prefetch_related, materialized likes/comments (S68) |
| `prompts/models.py` | Composite indexes: (status,created_on), (author,status,deleted_at) (S68) |
| `prompts/templates/prompts/prompt_detail.html` | Template fragment caching, critical CSS, async loading, preconnect hints (S68) |
| `static/js/upload-core.js` | 30-second upload warning timer (S67-S68) |
| `static/js/upload-form.js` | Improved error message display, warning toast dismiss (S67-S68) |
| `static/css/upload.css` | Warning toast styles, error card styles, breadcrumb styles (S67-S68) |
| `static_root/robots.txt` | NEW - Search engine crawl directives served via WHITENOISE_ROOT (S69) |
| `prompts_manager/settings.py` | Added WHITENOISE_ROOT = BASE_DIR / 'static_root' (S69) |
| `templates/base.html` | Removed stale preconnects, reduced font weights (4→3), deferred icons.css with noscript (S69) |
| `prompts/templates/prompts/prompt_detail.html` | Fixed h3→h2 headings, aria-label mismatches with pluralize filter (S69) |
| `prompts/management/commands/minify_assets.py` | NEW - CSS/JS minification command targeting STATIC_ROOT (S69) |
| `requirements.txt` | Added csscompressor>=0.9.5, rjsmin>=1.2.0 (S69) |
| `prompts/utils/related.py` | Related prompts IDF-weighted scoring (6-factor: tags 30%, categories 25%, descriptors 35%, generator 5%, engagement 3%, recency 2%) (Phase 2B-9 complete) |
| `prompts/templates/prompts/partials/_prompt_card_list.html` | NEW - AJAX partial for related prompts Load More (S74) |
| `prompts/views/prompt_views.py` | Added related_prompts_ajax view, get_related_prompts import, context updates (S74) |
| `prompts/urls.py` | Added /prompt/<slug>/related/ AJAX endpoint (S74) |
| `prompts/templates/prompts/prompt_detail.html` | Added "You Might Also Like" section with masonry grid + Load More JS (S74) |
| `static/css/pages/prompt-detail.css` | Related prompts section styles (S74) |
| `prompts/templates/prompts/user_profile.html` | Trash page polish: tap-to-toggle, card-link, clock icon, bookmark removal, FOUC fix (S74) |
| `static/css/style.css` | --radius-pill variable, trash badge styles, FOUC fix (S74) |
| `static/icons/sprite.svg` | Added icon-clock for trash "deleted X days ago" (S74) |
| `docs/DESIGN_RELATED_PROMPTS.md` | Related Prompts system reference — full rewrite (Phase 2B-9) |
| `prompts/models.py` | Added SubjectCategory model, Prompt.categories M2M (S74) |
| `prompts/admin.py` | Added SubjectCategoryAdmin with read-only enforcement (S74) |
| `prompts/tasks.py` | Added category assignment in AI prompt, writes to cache at 90% (S74) |
| `prompts/management/commands/backfill_categories.py` | NEW - Backfill categories for existing prompts (S74) |
| `prompts/migrations/0046_add_subject_categories.py` | NEW - SubjectCategory model + M2M (S74) |
| `prompts/migrations/0047_populate_subject_categories.py` | NEW - Seed 25 categories (S74) |
| `prompts/views/collection_views.py` | B2-aware thumbnail URLs replacing Cloudinary-only get_thumbnail_url() (S74) |
| `prompts/views/user_views.py` | B2-aware thumbnail URLs for trash collections (S74) |
| `prompts/templates/prompts/collection_detail.html` | Grid column fix, video autoplay observer, CSS overrides (S74) |
| `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md` | NEW - Phase 2B taxonomy revamp full design (S74) |
| `docs/PHASE_2B_AGENDA.md` | NEW - Phase 2B execution roadmap (S74) |

**Committed in Session 88 (Feb 25-26, 2026):**
- `prompts/notification_signals.py` - Reverse signal handlers: unlike (m2m post_remove), unfollow (post_delete), comment delete (post_delete)
- `prompts/services/notifications.py` - delete_notification(), delete_all_notifications()
- `prompts/views/notification_views.py` - Delete endpoints (delete-all, delete/<id>), Load More pagination
- `prompts/urls.py` - Delete URL patterns
- `prompts/tests/test_notifications.py` - 23 new delete/pagination tests + 12 reverse signal tests (62→85 total)
- `prompts/templates/prompts/notifications.html` - Delete buttons, confirmation dialog, Load More, "Updates available" banner
- `prompts/templates/prompts/partials/_notification_list.html` - Updated AJAX partial for Load More
- `static/js/notifications.js` - Delete, pagination, polling (15s), banner, two-phase animation, staggered fade-in (~500 lines)
- `static/js/navbar.js` - notifications:stale + count-updated listeners for bell sync
- `static/css/pages/notifications.css` - Delete animation, dialog, banner, hover states, Load More styles (~580 lines)
- `static/css/components/profile-tabs.css` - Tab padding adjustment
- `AGENT_TESTING_SYSTEM.md` - 8 hard rejection criteria matching CC_SPEC_TEMPLATE v2.0
- `design-references/UI_STYLE_GUIDE.md` - v1.4: --gray-500 contrast floor, focus management, ARIA stagger rules
- `CC_COMMUNICATION_PROTOCOL.md` - v2.1: PRE-AGENT SELF-CHECK, accessibility-first, COPY EXACTLY, data migration, DOM compliance
- `CC_SPEC_TEMPLATE.md` - v2.1: 5 new sections + PRE-AGENT SELF-CHECK

**Committed in Session 87 (Feb 18, 2026):**
- `prompts/templates/prompts/notifications.html` - Card-based redesign with avatars, quotes, action buttons, per-card mark-as-read
- `prompts/signals/notification_signals.py` - Comment links include #comments anchor
- `prompts/services/notifications.py` - Dedup filter: added link + message to Q filter
- `prompts/tests/test_notifications.py` - 5 new dedup edge case tests (57→62 total)
- `static/css/pages/notifications.css` - Card styling, 4-column layout, unread purple tint
- `static/css/pages/prompt-detail.css` - scroll-margin-top: 100px on #comments
- `static/js/notifications.js` - Event delegation, mark-as-read, bell sync listener
- `static/js/navbar.js` - Dispatch 'notifications:all-read' custom event, polling 60s→15s
- `static/icons/sprite.svg` - Added square-check-big icon
- `static/css/style.css` - Design tokens update (removed --gray-70)
- `prompts/management/commands/backfill_comment_anchors.py` - NEW: Idempotent backfill for comment notification link anchors
- `CC_SPEC_TEMPLATE.md` - v2.0: 5 new sections (accessibility, DOM diagrams, COPY EXACTLY, data migration, agent rejection)
- `CC_COMMUNICATION_PROTOCOL.md` - v2.0: aligned with spec template, standardized agent reporting

**Committed in Session 86 (Feb 17, 2026):**
- `prompts/models.py` - Notification model (6 types, 5 categories, 3 DB indexes)
- `prompts/services/notifications.py` - NEW: Notification service layer (create, count, mark-read, 60s duplicate prevention)
- `prompts/signals/__init__.py` - NEW: Signals package init
- `prompts/signals/notification_signals.py` - NEW: Signal handlers for comment, like (M2M), follow, collection save
- `prompts/views/notification_views.py` - NEW: API endpoints (unread-count, mark-all-read, mark-read) + notifications page
- `prompts/templates/prompts/notifications.html` - NEW: Full notifications page with category tab filtering
- `prompts/templates/prompts/partials/_notification_list.html` - NEW: AJAX notification list partial
- `prompts/tests/test_notifications.py` - NEW: 54 notification tests
- `prompts/migrations/0056_add_notification_model.py` - NEW: Notification model migration
- `static/js/overflow-tabs.js` - NEW: Shared overflow tab scroll module (187 lines)
- `static/js/notifications.js` - NEW: Notifications page JS
- `static/css/components/profile-tabs.css` - NEW: Shared tab component CSS
- `static/css/pages/notifications.css` - NEW: Notifications page CSS
- `templates/base.html` - Bell icon dropdown with pexels dropdown, notification polling
- `static/js/navbar.js` - Notification polling (60s), keyboard nav (WAI-ARIA roving focus), badge updates
- `static/css/navbar.css` - Notification badge styles, bell icon positioning
- `prompts/urls.py` - Notification URL patterns (page, API endpoints)
- `prompts/apps.py` - Notification signals registration
- `prompts/templatetags/notification_tags.py` - Updated notification template tags
- `prompts/templates/prompts/user_profile.html` - Migrated to shared profile-tabs system
- `prompts/templates/prompts/collections_profile.html` - Migrated to shared profile-tabs system, removed 75 lines inline CSS

**Committed in Session 85 (Feb 15-16, 2026):**
- `prompts/tasks.py` - Pass 2 SEO system (`queue_pass2_review()`, `_run_pass2_seo_review()`), `PROTECTED_TAGS` constant, `GENDER_LAST_TAGS` constant, rewritten Pass 2 GPT prompt
- `prompts/admin.py` - Two-button system (SEO Review + Rebuild), button label updates, `_apply_ai_m2m_updates` tag ordering fix (`clear()` + sequential `add()`), updated success messages
- `prompts/models.py` - `seo_pass2_at` field, `ordered_tags()` method
- `prompts/views/prompt_views.py` - `ordered_tags()` in detail/edit contexts
- `prompts/views/upload_views.py` - `ordered_tags()` in create context
- `prompts/migrations/0055_add_seo_pass2_at.py` - NEW: seo_pass2_at DateTimeField
- `prompts/management/commands/reorder_tags.py` - NEW: Tag reordering command
- `prompts/management/commands/run_pass2_review.py` - NEW: Pass 2 review command
- `prompts/tests/test_pass2_seo_review.py` - NEW: 60+ tests for Pass 2 system
- `prompts/tests/test_admin_actions.py` - NEW: 23 tests for admin actions and button labels
- `prompts/tests/test_validate_tags.py` - Expanded with tag ordering tests
- `prompts/templates/prompts/prompt_detail.html` - `escapejs` on tag onclick, `ordered_tags` usage
- `prompts/templates/prompts/prompt_create.html` - `ordered_tags` usage
- `prompts/templates/prompts/prompt_edit.html` - `ordered_tags` usage
- `templates/admin/prompts/prompt/change_form.html` - NEW: Two-button layout with help text
- `templates/admin/prompts/prompt/change_form_object_tools.html` - Updated button labels, rounded styling
- `CC_COMMUNICATION_PROTOCOL.md` - Reorganized to project root, content refresh
- `AGENT_TESTING_SYSTEM.md` - NEW: Moved to project root
- `HANDOFF_TEMPLATE_STRUCTURE.md` - NEW: Renamed from docs/
- `PHASE_N_DETAILED_OUTLINE.md` - NEW: Moved to project root
- `docs/REPORT_ADMIN_ACTIONS_AGENT_REVIEW.md` - NEW: Admin actions review report
- `docs/REPORT_DEMOGRAPHIC_TAG_ORDERING_FIX.md` - NEW: Tag ordering fix report

**Committed in Session 83 (Feb 14, 2026):**
- `prompts/tasks.py` - `TAG_RULES_BLOCK` shared constant (~76 lines), `ALLOWED_AI_TAGS` (5 terms), `PRESERVE_SINGLE_CHAR_COMPOUNDS` (12 entries), `DEMOGRAPHIC_TAGS` (16 entries), GPT self-check (rule 7 + `compounds_check`), compound stop-word discard, demographic tag reorder, `GENERIC_TAGS` expanded (24→32 entries)
- `prompts/tests/test_validate_tags.py` - Expanded to 200 tests (+37 new/updated in Session 83: GPT self-check, demographic reorder, stop-word discard, ALLOWED_AI_TAGS)
- `prompts/tests.py` - DELETED (stale stub conflicting with tests/ directory discovery)

**Committed in Session 82 (Feb 13, 2026):**
- `prompts/tasks.py` - Fail-fast image download (return error instead of raw URL fallback), `_is_quality_tag_response()` quality gate, `GENERIC_TAGS` constant (25 terms with singular/plural), module-level tag validation constants, removed dead `LEGACY_APPROVED_COMPOUNDS`, fixed `_handle_ai_failure` fallback tags, temperature 0.7→0.5
- `prompts/management/commands/backfill_ai_content.py` - `_check_image_accessible()` HEAD request pre-check, quality gate before `prompt.tags.set()`
- `prompts/tests/test_backfill_hardening.py` - NEW: 44 tests for backfill hardening (quality gate, fail-fast, URL pre-check, tag preservation)
- `prompts/tests/test_tags_context.py` - Updated 7 tests for fail-fast compatibility (mock returns tuple instead of None)

**Committed in Sessions 80-81 (Feb 11-12, 2026):**
- `prompts/models.py` - SlugRedirect model for SEO-preserving slug changes
- `prompts/admin.py` - Enhanced PromptAdmin: full metadata editing, B2 preview, XSS safeguards, dynamic weights, regenerate button, tag autocomplete
- `prompts/tasks.py` - `_validate_and_fix_tags()` pipeline, `_should_split_compound()`, COMPOUND TAG RULE, WEIGHTING RULES, excerpt in tags-only prompt
- `prompts/views/prompt_views.py` - SlugRedirect lookup, auth decorators on delete/toggle, CSRF protection
- `prompts/views/admin_views.py` - `regenerate_ai_content` view
- `prompts/views/upload_views.py` - Tag validation on upload submit
- `prompts/utils/related.py` - Dynamic weight reading for admin, hardcoded weight percentages audited
- `prompts/management/commands/backfill_ai_content.py` - `--tags-only`, `--under-tag-limit`, `--published-only` flags
- `prompts/management/commands/audit_tags.py` - NEW: Tag audit for compound fragments and quality issues
- `prompts/management/commands/remove_mandatory_tags.py` - NEW: Remove mandatory AI-related tags
- `prompts/management/commands/cleanup_old_tags.py` - Rewritten: orphan detection + capitalized merge
- `prompts/tests/test_tags_context.py` - NEW: 17 tests for tag context enhancement
- `prompts/tests/test_validate_tags.py` - NEW: 113 tests for tag validation pipeline
- `prompts/migrations/0053_add_slug_redirect.py` - NEW: SlugRedirect model
- `prompts/migrations/0054_rename_3d_photo_category.py` - NEW: Rename "3D Photo / Forced Perspective" category
- `prompts/templates/prompts/prompt_detail.html` - CSRF POST form for delete button
- `prompts_manager/settings.py` - INSTALLED_APPS additions for admin
- `prompts_manager/urls.py` - Admin regenerate URL
- `templates/admin/prompts/prompt/change_form_object_tools.html` - NEW: Admin regenerate button
- `templates/admin/prompts/prompt/regenerate_confirm.html` - NEW: Regenerate confirmation page
- `static/js/prompt-detail.js` - Delete uses POST form (was GET link)
- `audit_nsfw_tags.py` - NEW: Root-level NSFW tag audit script
- `audit_tags_vs_descriptions.py` - NEW: Root-level tag vs description audit script
- `docs/SESSION_REPORT_TAGS_AND_SEO_PROMPT_FIXES.md` - NEW: Session 81 completion report

**Committed in Phase 2B Session (Feb 9-10, 2026):**
- `prompts/models.py` - SubjectDescriptor model, Prompt.descriptors M2M, slug max_length 200
- `prompts/admin.py` - SubjectDescriptorAdmin with read-only enforcement
- `prompts/tasks.py` - Three-tier taxonomy AI prompt, demographic SEO rules, banned ethnicity tags
- `prompts/views/upload_views.py` - Descriptor assignment from cache/session
- `prompts/views/prompt_views.py` - Tag filter (`?tag=` parameter), video visibility fix (B2-first)
- `prompts/utils/related.py` - IDF-weighted 6-factor scoring (30/25/35/5/3/2), published-only counting, stop-word infrastructure
- `prompts/templates/prompts/prompt_list.html` - Tag links changed from `?search=` to `?tag=`
- `prompts/templates/prompts/prompt_detail.html` - Tag links changed from `?search=` to `?tag=`
- `prompts/management/commands/backfill_ai_content.py` - NEW: Bulk AI content regeneration
- `prompts/migrations/0048_create_subject_descriptor.py` - NEW: SubjectDescriptor model
- `prompts/migrations/0049_populate_descriptors.py` - NEW: Seed 109 descriptors
- `prompts/migrations/0050_update_subject_categories.py` - NEW: Expand to 46 categories
- `prompts/migrations/0051_fix_descriptor_type_duplicate_index.py` - NEW: Index fix
- `prompts/migrations/0052_alter_subjectcategory_slug.py` - NEW: Slug max_length 200
- `docs/DESIGN_RELATED_PROMPTS.md` - Updated scoring weights for 6-factor system
- `docs/PHASE_2B1_COMPLETION_REPORT.md` through `docs/PHASE_2B6_COMPLETION_REPORT.md` - NEW: Phase completion reports

**Committed in Session 66** (commit `806dd5b`):
- `prompts/templates/prompts/prompt_detail.html` - Complete SEO overhaul (JSON-LD, OG, Twitter, canonical, headings, tag links, noindex)
- `prompts/templates/prompts/upload.html` - Two-column grid redesign
- `templates/base.html` - OG/Twitter blocks + dynamic copyright year
- `static/css/upload.css` - Complete rewrite with modern card design
- `static/css/style.css` - Media container component, border-radius variables
- `static/css/pages/prompt-detail.css` - Media container + SEO updates
- `static/js/upload-core.js` - File input reset fix
- `static/js/upload-form.js` - Visibility toggle, modal handlers

---

## 🎯 What is PromptFinder?

### The Elevator Pitch

**PromptFinder** is like Pinterest for AI art prompts. Users share the text prompts they used to create AI-generated images and videos, and others can discover, save, and learn from them.

**Example:** Someone creates an amazing cyberpunk image using Midjourney. They upload it to PromptFinder along with the exact prompt: "cyberpunk samurai in neon-lit Tokyo alley, rain reflections, cinematic lighting --ar 16:9 --v 6". Now thousands of other users can find it, save it, and use that prompt for their own creations.

### Who Uses It?

| User Type | What They Do |
|-----------|--------------|
| **AI Artists** | Share their best work, build a following, get likes |
| **Content Creators** | Find prompt inspiration for client projects |
| **Hobbyists** | Learn prompting techniques from the community |
| **Beginners** | Copy working prompts instead of trial-and-error |

### How We Make Money (Planned)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 10 uploads/week, 10 collections, 2 private collections |
| **Premium** | $7/month | Unlimited uploads, unlimited collections, private prompts, analytics |

### Key URLs

| What | URL |
|------|-----|
| Production Site | https://mj-project-4-68750ca94690.herokuapp.com/ |
| Future Domain | https://promptfinder.net |

### Brand Language

- Users = "**Prompt Finders**"
- Community = "**Finder Community**"  
- Tagline = "**Find. Create. Share.**"

---

## 🛠️ Technical Stack

### Core Technologies

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| **Framework** | Django | 5.2.9 | Python web framework |
| **Language** | Python | 3.12 | Backend logic |
| **Database** | PostgreSQL | - | Hosted on Heroku |
| **Media Storage** | Backblaze B2 | - | Images, videos, thumbnails |
| **CDN** | Cloudflare | - | Serves B2 files globally |
| **AI** | OpenAI GPT-4o-mini | - | Content generation, NSFW moderation |
| **Hosting** | Heroku Eco Dyno | - | $5/month |
| **CI/CD** | GitHub Actions | - | Tests, linting, security scans |

### Frontend (No React/Vue)

| Technology | Usage |
|------------|-------|
| Django Templates | Server-side HTML rendering |
| Bootstrap 5 | CSS framework, responsive grid |
| Custom CSS | Component-based architecture (navbar.css, upload.css, etc.) |
| Vanilla JavaScript | No frameworks, just plain JS |
| Lucide Icons | SVG sprite system for icons |

### Authentication

- **Django Allauth** handles login/signup
- Social login ready (Google, Apple - not yet enabled)
- Email verification required

### Legacy Media (Being Phased Out)

Some older prompts still have images stored on **Cloudinary**. New uploads go to **B2**. Templates use "B2-first" pattern:

```python
# If B2 URL exists, use it. Otherwise fall back to Cloudinary.
{{ prompt.b2_image_url|default:prompt.cloudinary_url }}
```

---

## 💰 Current Costs

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Heroku Eco Dyno (web) | $5 | Covered by $248 credits (lasts until late 2026) |
| Heroku Standard-1X (worker) | $25 | Django-Q background tasks; can downgrade to Basic ($7) |
| Heroku PostgreSQL Mini | $5 | Covered by credits |
| Backblaze B2 | ~$0 | Free tier (10GB storage, 1GB/day downloads) |
| Cloudflare | $0 | Free tier |
| OpenAI API | ~$0.50 per 1000 uploads | Pay-as-you-go |
| **Total** | **~$35/month** | Web + DB covered by credits; worker is new cost |

### Why We Moved Away from Cloudinary

1. **NSFW Policy:** Cloudinary's AI flagged legitimate AI art as violations
2. **Cost at Scale:** B2 is ~70% cheaper than Cloudinary
3. **Direct Uploads:** Browser uploads directly to B2 (faster, no server bottleneck)

---

## 📁 Key File Locations

### Working on Uploads? (Phase N)

```
TEMPLATES:
prompts/templates/prompts/upload.html      # The main upload page

JAVASCRIPT (in static/js/):
upload-core.js      # File selection, drag-drop, B2 upload, preview
upload-form.js      # Form handling, NSFW status display  
upload-guards.js    # Navigation guards, idle timeout detection

CSS:
static/css/upload.css    # All upload page styles (~920 lines, rewritten S66, expanded S68)

BACKEND:
prompts/views/api_views.py           # API endpoints (1374+ lines)
prompts/services/b2_presign_service.py    # Generates presigned URLs for B2
prompts/services/b2_upload_service.py     # B2 upload utilities
prompts/services/b2_rename.py        # B2 file renaming (copy-verify-delete)
prompts/utils/seo.py                 # SEO filename generation
prompts/tasks.py                     # Background tasks (AI generation, SEO rename)
```

> ⚠️ **CRITICAL: api_views.py is 1374+ lines**
> - Claude Code crashes (SIGABRT) when editing this file
> - ALL edits to api_views.py must be done MANUALLY by developer
> - Create specifications with exact line numbers for manual editing

### Working on Moderation?

```
prompts/services/cloudinary_moderation.py   # VisionModerationService (OpenAI Vision)
prompts/services/video_processor.py         # FFmpeg frame extraction
prompts/services/video_moderation.py        # Video NSFW checking
prompts/services/content_generation.py      # AI title/description/tag generation
```

### Working on Collections? (Phase K - ON HOLD)

```
prompts/models.py                                    # Collection, CollectionItem models
prompts/views/collection_views.py                    # Collections API endpoints
static/js/collections.js                             # Modal JavaScript
prompts/templates/prompts/partials/_collection_modal.html   # Modal HTML
```

### Views Package Structure

Views were split into a modular package for maintainability:

```
prompts/views/
├── __init__.py           # Exports all views
├── admin_views.py        # Admin functions (ordering, bulk actions)
├── api_views.py          # API endpoints (1374 lines - TOO BIG FOR CC)
├── collection_views.py   # Collections API
├── generator_views.py    # AI generator filter pages
├── leaderboard_views.py  # Leaderboard/ranking pages
├── prompt_views.py       # Prompt CRUD, detail, tag filtering
├── redirect_views.py     # URL redirects and legacy routes
├── social_views.py       # Social sharing endpoints
├── upload_views.py       # Upload page views
├── user_views.py         # User profile pages
└── utility_views.py      # Utility/helper views
```

---

## 🔄 How Upload Works

### Philosophy: "The Restaurant Analogy"

> At a restaurant, we don't ask customers to wash their own dishes. They're customers, not employees.

**Applied to PromptFinder:**
- Users upload content and provide the prompt they used
- WE handle SEO (tags, titles, descriptions, slugs) in the background
- Keep the form simple - minimum required fields only

| User Provides | We Generate (Background) |
|---------------|-------------------------|
| Image/Video | NSFW moderation |
| Prompt text (required) | AI-generated title |
| AI Generator (required) | AI-generated description |
| Visibility (draft/publish) | SEO-optimized tags & slug |

### The User Experience (Phase N - Current)

**Image Flow:**
```
1. User drags/drops an image
        ↓ INSTANT (no upload yet)
2. Preview appears from browser memory
        ↓ BACKGROUND (user doesn't wait)
3. File uploads directly to B2 via presigned URL
        ↓ BACKGROUND
4. Server generates thumbnail
        ↓ BACKGROUND
5. OpenAI Vision checks for NSFW content
        ↓
6. User fills out title, description, tags (while above happens)
        ↓
7. User clicks Submit → Modal shows "Processing content..."
        ↓
8. AI generates title/description/tags in background
        ↓
9. Prompt created → Redirect to detail page
```

**Video Flow (Session 61):**
```
1. User drags/drops a video
        ↓
2. Preview appears from browser memory
        ↓ BACKGROUND
3. Video uploads directly to B2 via presigned URL
        ↓ BACKGROUND
4. FFmpeg extracts frames for NSFW moderation
        ↓ BACKGROUND
5. OpenAI Vision checks frames for NSFW content
        ↓ BACKGROUND
6. AI job queued using video thumbnail
        ↓ (ai_job_id returned to frontend)
7. User fills out form (while above happens)
        ↓
8. User clicks Submit → Modal shows "Processing content..."
        ↓
9. Polls for AI completion using ai_job_id
        ↓
10. Prompt created → Redirect to detail page
```

### Key Principle: Optimistic UX

Users see instant feedback. All the slow stuff (B2 upload, AI processing, NSFW check) happens invisibly in the background.

### Upload Limits

| Limit | Value | Enforced Where |
|-------|-------|----------------|
| Uploads per hour | 20 | Backend (rate limit cache) |
| Image max size | 3 MB | Frontend + Backend |
| Video max size | 15 MB | Frontend + Backend |

### API Endpoints

| Endpoint | Method | What It Does |
|----------|--------|--------------|
| `/api/upload/b2/presign/` | POST | Get presigned URL for direct B2 upload |
| `/api/upload/b2/complete/` | POST | Confirm upload, generate thumbnail |
| `/api/upload/b2/moderate/` | POST | Run NSFW check |
| `/api/upload/b2/delete/` | POST | Delete orphaned file (cleanup) |
| `/upload/submit/` | POST | Final submission, create Prompt |

---

## 🛡️ NSFW Moderation

### How It Works

1. Image/video uploads to B2
2. OpenAI Vision API analyzes it
3. Returns severity level
4. We take action based on severity

### Severity Levels

| Severity | What It Means | What Happens |
|----------|---------------|--------------|
| **critical** | Clearly prohibited (minors, extreme) | REJECTED - upload blocked |
| **high** | Likely problematic | FLAGGED - needs admin review |
| **medium** | Borderline | APPROVED with internal note |
| **low/none** | Safe | APPROVED |

### Video Moderation (Phase M)

Videos get 3 frames extracted at 25%, 50%, 75% of duration using FFmpeg. Each frame is sent to OpenAI Vision. If ANY frame is critical → video rejected.

### What's Banned

- Explicit nudity/sexual content
- Minors in any suggestive context (ZERO TOLERANCE)
- Violence, gore, blood
- Hate symbols
- Satanic/occult imagery
- Medical/graphic content

---

## 🤖 Development Workflow

### The Micro-Spec Approach

We learned the hard way: **big specs fail**. Claude Code ignores details in long specs and gives misleading high ratings on broken code.

**Now we use micro-specs:**
- Each spec = 10-20 lines of code max
- Manual testing after each spec
- Agent validation required (8+/10)

### Dual Agent Quality System

| When | System | Tool |
|------|--------|------|
| During coding | System 1 | wshobson/agents in Claude Code |
| After coding | System 2 | Claude.ai review personas |

**Required:** 8+/10 average rating before committing

### Agent Rating Protocol

When an agent scores below 8/10 and issues are fixed inline:

1. The agent MUST be re-run after fixes are applied to confirm the post-fix score meets the 8+/10 threshold.
2. "Projected" or "estimated" post-fix scores are NOT acceptable. The agent must actually re-evaluate the fixed code.
3. If re-running the full agent is impractical, run the agent on ONLY the specific files/issues that were fixed and report the focused re-evaluation score.
4. Document both the initial score and the confirmed post-fix score in the completion report.

**Example:**
- ❌ "@accessibility: 7.4/10 → ~8.2/10 (projected)" — NOT acceptable
- ✅ "@accessibility: 7.4/10 → 8.3/10 (re-verified after contrast fix)" — Acceptable

### File Size Warning for Claude Code

| File Size | Can CC Edit It? |
|-----------|-----------------|
| < 500 lines | ✅ Yes, safe |
| 500-1000 lines | ⚠️ Be careful |
| > 1000 lines | ❌ NO - edit manually |

**`api_views.py` is 1374 lines. NEVER let CC edit it directly.**

---

## 📊 Key Configuration Values

### Upload Config (in upload.html)

```javascript
window.uploadConfig = {
    maxFileSize: 3 * 1024 * 1024,      // 3MB for images
    maxVideoSize: 15 * 1024 * 1024,    // 15MB for videos
    allowedImageTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    allowedVideoTypes: ['video/mp4', 'video/quicktime', 'video/webm'],
    idleTimeout: 300000,               // 5 min until warning
    idleWarning: 60000,                // 1 min countdown
};
```

### Rate Limit Constants (in api_views.py)

```python
B2_UPLOAD_RATE_LIMIT = 20    # max uploads per window
B2_UPLOAD_RATE_WINDOW = 3600 # window = 1 hour (3600 seconds)
```

---

## 🔗 Related Documents

| Document | What It Contains |
|----------|------------------|
| **CLAUDE_PHASES.md** (2 of 3) | Detailed phase specs, especially Phase K unfinished work |
| **CLAUDE_CHANGELOG.md** (3 of 3) | Session history, what was done when |
| `CC_COMMUNICATION_PROTOCOL.md` | Agent requirements for Claude Code |
| `CC_SPEC_TEMPLATE.md` | Template for writing specs |
| `PROJECT_FILE_STRUCTURE.md` | Complete file tree |
| `docs/DESIGN_RELATED_PROMPTS.md` | Related Prompts system reference (Phase 2B-9 complete) |
| `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md` | Phase 2B category taxonomy revamp design |
| `docs/PHASE_2B_AGENDA.md` | Phase 2B execution roadmap (7 phases) |
| `docs/PHASE_2B1_COMPLETION_REPORT.md` - `PHASE_2B6_COMPLETION_REPORT.md` | Phase 2B sub-phase completion reports |

---

## ✅ Quick Start Checklist for New Sessions

1. ☐ Read this document for overall context
2. ☐ Check **CLAUDE_PHASES.md** for current phase details and unfinished work
3. ☐ Check **CLAUDE_CHANGELOG.md** for what was done in recent sessions
4. ☐ Create micro-specs (not big specs) for any new work
5. ☐ Get 8+/10 agent ratings before committing
6. ☐ Don't let CC edit files > 1000 lines
7. ☐ Update CLAUDE_CHANGELOG.md at end of session

---

**Version:** 4.15 (Session 88 — Phase R1-D v7 notification management: delete, pagination, animations, reverse signals, real-time polling, document alignment)
**Last Updated:** February 26, 2026
