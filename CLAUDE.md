# CLAUDE.md - PromptFinder Project Documentation (1 of 3)

## ⚠️ IMPORTANT: This is Part 1 of 3

**Before proceeding, also read:**
- **CLAUDE_PHASES.md** - Phase specs, unfinished work details
- **CLAUDE_CHANGELOG.md** - Session history, recent changes

These three files together replace the original CLAUDE.md.
Do NOT edit or reference this document without reading all three.

---

**Project Status:** Pre-Launch Development
**Last Updated:** March 16, 2026

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
| **Phase N4** | ✅ 100% Complete | Optimistic Upload Flow | All open items resolved Sessions 122–127. Admin rename fix, print removal, ARIA comment, stale items closed. |
| **Phase N3** | 🔄 ~95% | Single-Page Upload | Final testing, deploy to prod |
| **Bulk Gen Phase 6A** | ✅ COMPLETE | Bug Fixes (scaffolding) | Done — 6 of 7 bugs, Session 114 |
| **Bulk Gen Phase 6A.5** | ✅ COMPLETE | Data Correctness (gpt-image-1 choice + pipeline alignment) | Done — Session 114 |
| **Bulk Gen Phase 6B** | ✅ COMPLETE | Publish Flow UI + Concurrent Pipeline | Done — Session 115, 1076 tests |
| **Bulk Gen Phase 6B.5** | ✅ COMPLETE | Transaction Hardening & Quick Wins | Done — Session 116, 1084 tests |
| **Bulk Gen Phase 6C-B** | ✅ COMPLETE | Gallery card states + published badge + A11Y-3/5 | Done — Session 117, ~1100 tests |
| **Bulk Gen Phase 6C-B.1** | ✅ COMPLETE | CSS fixes + test fix + round 4 agent close | Done — Session 118, 1100 tests |
| **Bulk Gen Phase 6C-A** | ✅ COMPLETE | M2M helper extraction + publish task tests | Done — Session 116, 1098 tests |
| **Bulk Gen Phase 6D** | ✅ COMPLETE | Per-image error recovery + retry | Done — Session 119, 1106 tests |
| **Bulk Gen Phases 1–7** | ✅ COMPLETE | Staff bulk AI image generator — full publish flow, error recovery, retry, hardening | Production smoke test before V2 |

### What's Paused (Don't Forget!)

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase K** | ⏸️ ~96% | Collections ("Saves") | Trash video bugs (3), K.2: Download tracking, virtual collections; K.3: Premium limits |
| **Phase P2-B** | 🔲 Planned | Admin Log Tab | Activity log for staff actions |
| **Phase P2-C** | 🔲 Planned | Web Pulse Tab | Site analytics and pulse data |

### Recently Completed

| Phase | When | What It Was |
|-------|------|-------------|
| NOTIF-BG-1+2 | Mar 13, 2026 | Added 4 bulk gen notification types (`bulk_gen_job_completed`, `bulk_gen_job_failed`, `bulk_gen_published`, `bulk_gen_partial`) to `Notification.NOTIFICATION_TYPES`. Migration 0073. New helper functions `_fire_bulk_gen_job_notification` + `_fire_bulk_gen_publish_notification` in `tasks.py`. New test file: `prompts/tests/test_bulk_gen_notifications.py` (6 tests). Renamed `cloudinary_moderation.py` → `vision_moderation.py` (all import sites updated). 1149 → 1155 tests. |
| DETECT-B2-ORPHANS | Mar 13, 2026 | New `detect_b2_orphans` management command (404 lines) in `prompts/management/commands/`. Read-only B2 bucket audit via boto3 paginator. Cross-references `Prompt.all_objects` (7 B2 fields) + `GeneratedImage.image_url` + `BulkGenerationJob.reference_image_url`. `SCAN_PREFIXES` limits scan to `media/` and `bulk-gen/`. `_safe_error_message()` uses structured `ClientError.response['Error']` fields — credential-safe. `iterator(chunk_size=500)` on all DB queries. Flags: `--days`, `--all`, `--dry-run`, `--output`, `--verbose`. CSV output to `docs/orphans_b2.csv`. Commit: 61edad1. Agents: @security-auditor 9.0, @django-pro 9.0, @code-reviewer 8.5. Avg 8.83/10. 1149 tests. |
| MICRO-CLEANUP-1 | Mar 13, 2026 | Seven cleanup items in one commit: (1) group footer separator `·`→`\|` with `margin: 0 0.4rem` and `color: var(--gray-500)`; (2) ID rename `header-quality-col-th/td` → `header-quality-item/value` in HTML + JS; (3) `style.removeProperty('display')` → `.is-quality-visible` class toggle; (4) `VALID_PROVIDERS` + `VALID_VISIBILITIES` → `frozenset` in `bulk_generator_views.py`; (5) `VALID_SIZES` → `frozenset` in `create_test_gallery.py`; (6) `@csp_exempt` blank line removed in `upload_views.py` (bonus: same fix on `extend_upload_time`); (7) `replace('x','×')` → anchored regex `/(\d+)x(\d+)/i`. Commit: a222d15. Agents: @frontend-developer 8.8, @code-reviewer 9.0, @django-pro 8.5. Avg 8.77/10. 1149 tests. |
| N4H-UPLOAD-RENAME-FIX | Mar 12, 2026 | Fixed `rename_prompt_files_for_seo` guard in `upload_views.py`. Guard changed from `is_b2_upload and prompt.pk` (session flag) to `prompt.b2_image_url` (model field check). `async_task` import moved to module level. Discovery: the core `async_task` call was already present from Session 67 — this fix tightened the guard and added tests. New file: `prompts/tests/test_upload_views.py` (2 tests). Commit: a9acbc4. Agents: @django-pro 8.5, @test-automator 8.2. Avg 8.35/10. 1149 tests. |
| 6E-CLEANUP-3 | Mar 12, 2026 | JS bug + quality: cancel-path `G.totalImages` staleness fixed (`data-actual-total-images` template attr + `initPage()` reads it), `parseGroupSize()` helper replaces 3× inline parse in `createGroupRow()`, ARIA `progressAnnouncer` clear-then-50ms-set pattern, dead ternary guards removed from `renderImages()`. Commit: 90ac2cb. Agents: @frontend-developer 8.5, @accessibility 8.5, @code-reviewer 9.0. Avg 8.67/10. 1147 tests. |
| 6E-CLEANUP-2 | Mar 12, 2026 | Extracted `bulk-generator-gallery.js` from `bulk-generator-ui.js` (766→338 lines). New file: `static/js/bulk-generator-gallery.js` (452 lines). Contains: `cleanupGroupEmptySlots`, `markCardPublished`, `markCardFailed`, `fillImageSlot`, `fillFailedSlot`, `createLightbox`, `openLightbox`, `closeLightbox`. Load order: config→ui→gallery→polling→selection. Commit: 5f1ced3. Agents: @frontend-developer 9.0, @code-reviewer 9.0. Avg 9.0/10. 1147 tests. |
| 6E-CLEANUP-1 | Mar 12, 2026 | Python micro-cleanup: `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` converted to `frozenset`; `total_images_estimate` renamed to `resolved_total_images` (3 occurrences in `create_job()`); `get_job_status()` `actual_total_images` fallback uses explicit `> 0` guard; CLAUDE.md Section B forward reference names target heading. Commit: 0b6b720. Agents: @django-pro 9.5, @code-reviewer 9.0. Avg 9.25/10. 1147 tests. |
| 6E-HARDENING-2 | Mar 12, 2026 | Frontend display: `G.totalImages` reads `actual_total_images \|\| total_images \|\| G.totalImages` (3-level fallback); `createGroupRow()` adds `groupQuality` param; group headers show per-group size and quality with job fallbacks; placeholder slots use per-group aspect ratio from `groupSize`; bonus: terminal-on-load one-shot fetch now syncs `G.totalImages`. Commit: 7b1ff65. Agents: @frontend-developer 9.0, @accessibility 9.0, @code-reviewer 8.0. Avg 8.67/10. 1147 tests. |
| 6E-HARDENING-1 | Mar 12, 2026 | Backend hardening: `BulkGenerationJob.actual_total_images` PositiveIntegerField, migration 0072, populated at job creation from `sum(resolved_counts)`; status API returns `actual_total_images` with fallback; `VALID_SIZES` rebuilt from `SUPPORTED_IMAGE_SIZES` (blocks 1792×1024); module-level `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS`; 8 new tests. Commit: 3b42114. Agents: @django-pro 9.0, @security-auditor 8.5, @test-automator 8.5. Avg 8.67/10. 1147 tests. |
| 6E-C — Per-prompt image count | Mar 12, 2026 | `GeneratedImage.target_count` PositiveSmallIntegerField, migration 0071. Per-prompt count override (1–4). `VALID_COUNTS = {1,2,3,4}`. `createGroupRow()` uses `targetCount` param. All 4 `G.imagesPerPrompt` refs audited. Commit: 7d6efb6. Agents: @django-pro 9.2, @frontend-developer 9.0, @security-auditor 9.4, @accessibility 8.5. Avg 9.025/10. 1139 tests. |
| 6E-B — Per-prompt quality | Mar 12, 2026 | `GeneratedImage.quality` CharField, migration 0070. Per-prompt quality override. `VALID_QUALITIES` allowlist. Task resolves per-image or job fallback. Unspecced improvement: `actual_cost` now uses per-image quality/size for accurate cost tracking. Commit: 87d33fa. Agents: @django-pro 9.0, @frontend-developer 9.1, @security-auditor 9.3. Avg 9.13/10. |
| 6E-A — Per-prompt size | Mar 12, 2026 | `GeneratedImage.size` CharField, migration 0069. Per-prompt size override. `VALID_SIZES` allowlist. Task resolves per-image or job fallback. `createGroupRow()` accepts `groupSize`. Placeholder slot-count guard uses `groupData.targetCount`. Commit: e1fd774. Agents: @django-pro 9.1, @frontend-developer 8.7, @security-auditor 9.2, @accessibility 8.7. Avg 8.9/10. |
| CLEANUP-SLOTS-REFACTOR | Mar 12, 2026 | Removed unreachable `:not(.placeholder-terminal)` selector from `cleanupGroupEmptySlots()` in `bulk-generator-ui.js`. Dead code — `:not(.placeholder-terminal)` exclusion proven unreachable because `fillImageSlot`/`fillFailedSlot` remove `.placeholder-loading` before slot-count guard is reached. Agents: @frontend-developer 9.1, @code-reviewer 9.2. Avg 9.15/10. |
| SMOKE2 Series (Fixes A–E) | Mar 11, 2026 | Production smoke test + 5 bug fixes: Fix-A (`processing_complete=True` in publish pipeline), Fix-B (focus ring on page load), Fix-C (`b2_large_url` never set — Media Missing root cause), Fix-D (SEO rename task never queued for bulk-gen), Fix-E (images relocated from `bulk-gen/` path to standard `media/images/{year}/{month}/large/`). All 6 production prompts backfilled. Heroku v649→v653. |
| HARDENING-1 | Mar 11, 2026 | 5 unit tests for sibling-check cleanup path in `rename_prompt_files_for_seo` (including non-blocking exception contract). Batch mirror field saves: N individual DB writes → 1. `prompts/tests/test_bulk_gen_rename.py` (283 lines, new). 1117 tests. Agents: @django-pro 9.5, @test-automator 8.5. |
| JS-SPLIT-1 | Mar 11, 2026 | Split `bulk-generator-job.js` (1830 lines, above 800-line CC safety threshold) into 4 modules: `bulk-generator-config.js` (156), `bulk-generator-ui.js` (722), `bulk-generator-polling.js` (408), `bulk-generator-selection.js` (581). Shared state via `window.BulkGen` namespace. Original file deleted. Template `<script>` tags updated in dependency order. 1117 tests. Agents: @frontend-developer 8.5, @code-reviewer 9.0, @accessibility 8.6. |
| HARDENING-2 | Mar 11, 2026 | Added internal prefix allowlist guard to `cleanup_empty_prefix` in `b2_rename.py`. Raises `ValueError` if prefix does not start with `bulk-gen/` or is exactly `bulk-gen/`. Defense-in-depth — flagged in SMOKE2-FIX-E and HARDENING-1 reports. 1117 tests. Agent: @security-auditor. |
| Bulk Gen Phase 7 | Mar 10, 2026 | Integration polish + hardening: .btn-zoom double-ring focus, persistent #publish-status-text ("X created, Y failed"), cumulative retry progress bar, atomic rate limiter (cache.add+incr TOCTOU-safe, 10 req/min), 429 frontend handling, clearInterval guard, 6 new tests (EndToEndPublishFlowTests + CreatePagesAPITests + cache.clear setUp). Avg 8.625/10. 1112 tests |
| Bulk Gen Phase 6D Hotfix | Mar 10, 2026 | Published badge keyboard access: aria-hidden removed from <a> badge, aria-label added, double-ring a.published-badge:focus-visible, pointer-events comment added. CC_SPEC_TEMPLATE v2.5: Critical Reminder #9 (pair every negative assertion with positive counterpart). Avg 8.7/10. 1106 tests (unchanged) |
| Bulk Gen Phase 6D | Mar 10, 2026 | Per-image publish failure states (.is-failed CSS, red badge strip, stale detection 10-poll/30s, markCardFailed(), Retry Failed button, handleRetryFailed() with optimistic re-select + rollback, api_create_pages image_ids retry path, 6 new tests, 2-round agent review avg 8.9/10, 1106 tests |
| Bulk Gen Phase 6C-B.1 | Mar 10, 2026 | btn-zoom keyboard trap (WCAG 2.4.11), opacity hierarchy fix (0.20→0.65 deselected), available_tags assertGreater, lightbox alt text, loading-text contrast, published-badge clickable link, prefers-reduced-motion hardening, 4-round agent review, 1100 tests |
| Bulk Gen Phase 6C-B | Mar 9, 2026 | Gallery card states (selected/deselected/discarded/published CSS states), published badge with prompt_page_url links, A11Y-3 live region + A11Y-5 focus management, double-ring focus pattern, opacity-compounding bug fix, 2-round agent review, ~1100 tests |
| Bulk Gen Phase 6C-A | Mar 9, 2026 | Extract `_apply_m2m_to_prompt()` helper (4 duplicated M2M blocks), 14 PublishTaskTests (concurrent race, IntegrityError retry, partial failure, sanitise, available_tags), stale test corrections, 1098 tests |
| Bulk Gen Phase 6B.5 | Mar 9, 2026 | Transaction hardening — atomic F() counter, _sanitise_error_message in worker closure, available_tags pre-fetch + order_by, hasattr dead code removed, generator_category default fix + migration 0068, 8 TransactionHardeningTests, 1084 tests |
| Bulk Gen Phase 6B | Mar 9, 2026 | Publish flow — concurrent pipeline (ThreadPoolExecutor), per-image DB lock (select_for_update + atomic), IntegrityError slug-collision retry, published_count F() atomic counter, static aria-live toast announcer, 9 PublishFlowTests, 1076 tests |
| Bulk Gen Phase 6A.5 | Mar 9, 2026 | Data correctness — gpt-image-1 model name fix, pipeline alignment for size/quality/model fields on BulkGenerationJob |
| Bulk Gen Phase 6A | Mar 9, 2026 | Bug fixes — 6 of 7 Phase 4 scaffolding bugs fixed (prompt_page FK, published_count field, migrations 0066+0067, create-pages view, status API fields) |
| Bulk Gen Phase 5D | Mar 7-8, 2026 | ThreadPoolExecutor concurrency, count display fix, dimension select disabled, Failure UX hardening (_sanitise_error_message, gallery failure slots, JS exact-match map), CC_SPEC_TEMPLATE v2.3, 1008 tests |
| Bulk Gen 5C+5B+P1/P2 | Mar 6-7, 2026 | Real GPT-Image-1 generation (openai SDK 2.26.0), flush button, images_per_prompt+aspect ratio bugs fixed, SUPPORTED_IMAGE_SIZES constants, SEC/UX/A11Y hardening, migration 0065, 985 tests |
| Bulk Gen 5A+5B+Polish | Mar 4-5, 2026 | Job progress page, gallery rendering, 5-agent audit (10 fixes), column override bug fix, download extension detection, test gallery size filtering, 237 new tests |
| Phase P2-A | Feb 26-27, 2026 | System Notifications Admin Dashboard (Quill.js editor, batch management, batch_id tracking, rate limiting, auto-mark seen, "Most Likely Seen" stats) |
| Phase R1 + R1-D | Feb 17-18, 25-26, 2026 | User Notification System (model, signals, API, bell dropdown, notifications page redesign with avatars/quotes/action buttons, per-card mark-as-read, bell sync, dedup fix, shared tab components, delete all/per-card delete, Load More pagination, two-phase delete animation, staggered fade-in, reverse signal handlers, real-time polling, "Updates available" banner, cross-component DOM event sync) |
| Phase 2B (1-9) + Tag Pipeline + Hardening + Pass 2 SEO | Feb 9-16, 2026 | Category Taxonomy Revamp, tag validation pipeline, admin metadata, security hardening, backfill hardening, tag pipeline refinements, Pass 2 background SEO, admin UX |
| Phase 2B (1-8) | Feb 9-10, 2026 | Category Taxonomy Revamp: 46 categories, 109 descriptors, AI backfill, demographic SEO rules |
| Subject Categories P2 | Feb 9, 2026 | AI-assigned prompt classification (25 categories, cache-first logic) |
| Related Prompts P1 | Feb 7, 2026 | "You Might Also Like" section on prompt detail (scoring algorithm, AJAX Load More) |
| Phase L | Jan 2026 | Media Infrastructure (moved from Cloudinary to B2 + Cloudflare) |
| Phase M | Jan 2026 | Video NSFW Moderation (FFmpeg frame extraction + OpenAI Vision) |
| Phase J | Dec 2025 | Prompt Detail Page Redesign |

---

## 🛠️ CC Working Constraints & Spec Guidelines

> This section exists to guide session planning and spec writing.
> Claude (planning) and CC (implementing) should both reference this
> before scoping any session or spec.

### File Size Limits

CC's `str_replace` editing reliability degrades on large files.
Never assume CC can safely edit a file without checking its tier first.

| Tier | CC Strategy |
|------|-------------|
| 🔴 Critical (2000+ lines) | Never edit directly. Read-only access. All changes via create-new + rewrite-original strategy. |
| 🟠 High Risk (1200–1999 lines) | Avoid direct editing. New file strategy preferred. If must edit, single precise str_replace only. |
| 🟡 Caution (800–1199 lines) | str_replace with very precise anchor strings. Maximum 2–3 edits per spec. |
| ✅ Safe (under 800 lines) | Normal CC editing. |

#### Current File Tiers (from Session 128 audit)

**🔴 Critical — Never Edit Directly:**
- `prompts/tasks.py` (3,451 lines)
- `prompts/models.py` (3,087 lines)
- `prompts/tests/test_notifications.py` (2,872 lines)
- `prompts/admin.py` (2,366 lines)
- `prompts/tests/test_bulk_generator_views.py` (2,210 lines)
- `prompts/templates/prompts/user_profile.html` (2,073 lines)
- `static/css/style.css` (4,466 lines)

**🟠 High Risk — Avoid Direct Editing:**
- `prompts/tests/test_bulk_generation_tasks.py` (1,861 lines)
- `prompts/templates/prompts/prompt_list.html` (1,700 lines)
- ~~`prompts/views/prompt_views.py` (1,694 lines)~~ — split Session 134, now 50-line shim
- `prompts/tests/test_bulk_page_creation.py` (1,621 lines)
- `static/css/pages/prompt-detail.css` (1,549 lines)
- `static/css/pages/bulk-generator.css` (1,484 lines)
- `static/js/bulk-generator.js` (1,547 lines) — input page JS, actively used
- `static/css/navbar.css` (1,268 lines)

**🟡 Caution — str_replace with Precision (max 2–3 edits per spec):**
- `prompts/tests/test_validate_tags.py` (1,117 lines)
- `static/js/collections.js` (1,108 lines)
- `prompts/tests/test_pass2_seo_review.py` (1,048 lines)
- `prompts/templates/prompts/collections_profile.html` (1,017 lines)
- `prompts/templates/prompts/prompt_detail.html` (1,010 lines)
- `prompts/tests/test_user_profiles.py` (991 lines)
- `static/js/upload-form.js` (1,069 lines)
- `static/js/navbar.js` (899 lines)
- `static/css/upload.css` (921 lines)
- `prompts/services/vision_moderation.py` (904 lines)
- `prompts/views/upload_api_views.py` (852 lines)
- `prompts/management/commands/detect_orphaned_files.py` (798 lines)
- `static/css/pages/bulk-generator-job.css` (1,179 lines)

**✅ Safe but Growing — Watch These:**
- `prompts/views/collection_views.py` (792) — at boundary
- `prompts/views/upload_views.py` (751) — modified 3 recent sessions
- `prompts/views/bulk_generator_views.py` (721) — active development
- `prompts/views/user_views.py` (630) — growing, modified Sessions 74, 86
- `prompts/views/admin_views.py` (577) — admin additions ongoing

*Last updated: Session 128 (March 14, 2026). Re-run the file size audit
whenever a file is significantly extended or split.*

---

### Specs Per Session

| Spec Type | Max Per Session | Notes |
|-----------|----------------|-------|
| Audit / read-only | 6 | Lightweight — greps and reports only |
| Docs-only | 4 | No suite run needed |
| Code change (small) | 4 | Single file, low complexity |
| Code change (medium) | 3 | Multiple files or migration |
| Code change (high risk) | 1–2 | New model, file split, migration + logic |
| Mixed session | 4–5 total | Count high-risk as 2 toward the total |

**When to split a session into two:**
- Any spec touches a 🔴 Critical file AND requires a migration
- More than 2 high-risk specs in the queue
- Previous spec had average agent score below 8.5 (quality may be degrading)
- Full suite run count would exceed 4 in a single session

---

### Full Test Suite Budget

- Each full suite run takes approximately 15–25 minutes
- Maximum **4 full suite runs per session**
- `python manage.py check` (isolated check) does NOT count toward this budget
- Audit and docs-only specs never require a full suite run

---

### Large File Strategies

**For 🔴 Critical files (models.py, tasks.py, etc.):**
- CC reads the file first with targeted greps
- New logic goes in new helper functions at the bottom of the file
- Uses local imports inside functions to avoid circular import risks
- str_replace uses multi-line anchor strings (5+ lines) to guarantee uniqueness
- Never attempts to rewrite or reorganise the file structure

**For splitting a large file (like api_views.py was in Session 128):**
- CC creates new domain module files (new content only)
- CC rewrites the original as a thin compatibility shim
- The shim re-exports everything so urls.py requires no changes
- urls.py is updated to import from modules directly in a follow-up spec

---

### Spec Quality Gates

Every spec — including audit and docs specs — must:
- Complete all Step 0 greps before writing any code
- Run `python manage.py check` after implementation
- Run all required agents (see individual spec for count)
- Include an agent ratings table in the completion report
- Only commit after the full suite passes (for code specs)
- Save the report before committing (report is part of the commit)

Each spec gets exactly one commit. Never bundle two specs into one commit.

---

## 🚀 Current Phases: Bulk AI Image Generator + N4 Upload Flow

### Bulk AI Image Generator (Phases 1–7 complete — Pre-launch QA)

Staff-only tool at `/tools/bulk-ai-generator/` for generating multiple AI images using OpenAI GPT-Image-1 with BYOK (Bring Your Own Key) model.

**Phases 1-4 (Sessions 92-93):** Models, Django-Q tasks, 7 API endpoints, complete input UI with reference image upload, character description, source/credit, auto-save, NSFW moderation.

**Phase 5A-5B (Session 98):** Job progress page with cost tracking, gallery rendering with per-prompt aspect ratio detection, 2 rounds of visual polish, 237 new tests, 36 files changed. Status API enhanced with per-image data.

**Phase 5C (Sessions 100-101):** BYOK key input (Fernet encryption), real GPT-Image-1 generation, 13s rate-limit delay, exponential backoff retry (30s→60s→120s, max 3), structured error routing (auth/content_policy/rate_limit/server_error). `IMAGE_COST_MAP` moved to `prompts/constants.py`. All 3 terminal states clear encrypted API key via `try/finally`. 976 tests passing, 12 skipped.

**Phase 5B bugs + P1/P2 hardening (Sessions 102-107):** Fixed images_per_prompt (all slots rendered), aspect ratio end-to-end (job.size through to gallery CSS), dropdown options (unsupported hidden). DRY-1: `SUPPORTED_IMAGE_SIZES` + `ALL_IMAGE_SIZES` centralised in `prompts/constants.py`. SEC-1: isinstance(bool, int) bypass fixed. UX-1: disabled + "(coming soon)" on unsupported sizes. A11Y-1/4: aria-atomic + aria-describedby on dimension controls. Flush button ("Trash Test Results"): staff-only endpoint deletes unpublished GeneratedImage/BulkGenerationJob records + B2 files in one click. Migration 0065: choices-only SIZE_CHOICES label update. 985 tests passing, 12 skipped.

**Phase 5D (Sessions 108–111):** ✅ COMPLETE. ThreadPoolExecutor concurrency (max_workers=4, configurable via `BULK_GEN_MAX_CONCURRENT` env var), count mismatch fix, dimension dropdowns disabled with v1.1 tooltip. Failure UX hardening: `_sanitise_error_message()` security boundary, gallery failure slots (reason + 60-char truncated prompt), JS refactored to exact-match map. F() atomic per-image progress updates. CC_SPEC_TEMPLATE upgraded to v2.3 (Self-Identified Issues Policy). 1008 tests passing, 12 skipped.

**Phase 6A (Session 114):** ✅ COMPLETE. Fixed 6 of 7 Phase 4 scaffolding bugs: `prompt_page` FK on `GeneratedImage`, `published_count` field on `BulkGenerationJob`, migrations 0066+0067, `create_pages` view (validation, task wiring), status API (`prompt_page_id`/`prompt_page_url` per image, `published_count` on job).

**Phase 6A.5 (Session 114):** ✅ COMPLETE. Data correctness — `gpt-image-1` model name aligned to OpenAI SDK, `size`/`quality`/`model` fields on `BulkGenerationJob` populated correctly at job start.

**Phase 6B (Session 115):** ✅ COMPLETE. Concurrent publish pipeline: `ThreadPoolExecutor` dispatches Prompt creation across worker threads; all ORM writes happen on main thread after futures complete. Per-image DB-level idempotency lock (`select_for_update()` inside `transaction.atomic()`). `IntegrityError` slug-collision retry with UUID suffix. `published_count` incremented via `F()` atomic counter. Sticky publish bar + progress bar in template. Static `#bulk-toast-announcer` for screen-reader toast announcements. 9 `PublishFlowTests` added. 1076 tests passing, 12 skipped.

**Phase 6C-B (Session 117):** ✅ COMPLETE. Gallery card CSS states: `.is-selected` (3px box-shadow ring), `.is-deselected` (65% opacity — corrected in 6C-B.1), `.is-discarded` (55% opacity on image), `.is-published` (green "✓ View page →" clickable badge). A11Y-3: `#generation-progress-announcer` live region with `aria-atomic="true"`. A11Y-5: `focusFirstGalleryCard()` on gallery render. Double-ring focus pattern for overlay buttons. Opacity-compounding bug fixed. ~1100 tests passing, 12 skipped.

**Phase 6C-B.1 (Session 118):** ✅ COMPLETE. Deferred fixes + round 4 agent close: `.btn-zoom:focus-visible` keyboard trap (WCAG 2.4.11), `.is-deselected` opacity 0.20→0.65 (hierarchy inversion fixed), `available_tags` assertGreater, lightbox prompt text alt, `.loading-text` contrast (`--gray-600`), `a.published-badge` clickable (`pointer-events: auto`), `prefers-reduced-motion` hardening. Round 4 avg 8.425/10. 1100 tests passing, 12 skipped.

**Phase 6C-A (Session 116):** ✅ COMPLETE. Extracted `_apply_m2m_to_prompt()` helper — reduced 4 duplicate M2M block copies (tags, categories, descriptors) to a single function. Added 14 `PublishTaskTests`: concurrent race, IntegrityError retry with M2M re-application, partial failure, `_sanitise_error_message` boundary, `available_tags` passed to vision. Stale test corrections (`available_tags` assertion, `generator_category` default). 1098 tests passing, 12 skipped.

**Phase 6D (Session 119):** ✅ COMPLETE. Per-image publish error recovery: `.is-failed` CSS state (0.40 img opacity, red badge strip, select+trash hidden, download preserved), stale detection (10-poll/30s threshold, only counts after first publish), `markCardFailed()`, `_restoreRetryCardsToFailed()` helper, `handleRetryFailed()` (optimistic re-select + rollback on error), "Retry Failed (N)" publish bar button. Backend: `api_create_pages` `image_ids` retry path bypasses per-image `status='completed'` filter (job-level guard still enforced). 6 new Phase 6D tests, 2-round agent review avg 8.9/10. 1106 tests passing, 12 skipped.

**Phase 6D Hotfix (Session 119):** ✅ COMPLETE. Published badge keyboard access:
`aria-hidden="true"` removed from `<a>` badge elements; `aria-label` added
("Published — view prompt page (opens in new tab)"). `<div>` fallback badges
retain `aria-hidden` (decorative, non-interactive). Double-ring `:focus-visible`
on `a.published-badge` (2px white inner + 4px `#166534` outer). `pointer-events:
auto` CSS comment added. CC_SPEC_TEMPLATE upgraded to v2.5 — Critical Reminder #9:
every `assertNotIn` must be paired with a positive `assertEqual` counterpart. Avg
8.7/10. 1106 tests, 12 skipped.

**Phase 7 (Session 119):** ✅ COMPLETE. Integration polish + hardening.
`.btn-zoom:focus-visible` double-ring now matches all other overlay buttons.
Persistent `#publish-status-text` shows "X created, Y failed" on terminal state
(pre-existing `aria-live="polite"` region — no dynamic injection). Cumulative
`totalPublishTarget`: retries do not reset denominator (already counted in original
batch). Atomic rate limiter on `api_create_pages` using `cache.add()` + `cache.incr()`
(TOCTOU-safe; fixes naive get+set race). 429 frontend handling: warning toast,
`failedImageIds` preserved. `clearInterval` guard prevents duplicate polling loops.
6 new tests: `EndToEndPublishFlowTests` (3) + `CreatePagesAPITests` (3). `cache.clear()`
in setUp for test isolation. Avg 8.625/10. 1112 tests passing, 12 skipped.

**Status:** Feature-complete for staff use. Full 6E series complete (per-prompt size, quality, image count overrides + hardening + cleanup). 5 JS modules. 1193 tests. Next: production smoke test before V2 launch, then UI improvements (failed slot dimensions, header stats, group footer weights). V2 scope: BYOK for premium users, Replicate models (Flux, SDXL), archive staging page at `/profile/<username>/ai-generations/`.

**Resolved (Session 122):** Cancel-path `G.totalImages` staleness ✅, `bulk-generator-ui.js` at 766/780 lines ✅ (now 338 lines), N4h rename not triggering ✅.

**Open items as of Session 127 (post-audit):**

| Item | Notes |
|------|-------|
| **Terminal-state ARIA branches** | ✅ CLOSED — comment added to `bulk-generator-polling.js` (Session 127). Non-actionable by design. |
| **Admin path rename task** | ✅ FIXED — `async_task` queued from `save_model` in `admin.py` (Session 127). |
| **Video B2 rename** | ✅ CLOSED — audit confirmed `b2_video_url` already handled in `tasks.py` lines 1936–1944. Stale entry. |
| **Debug print() statements** | ✅ FIXED — 13 print() statements removed from `upload_views.py` (Session 127). |

### Recommended Build Sequence — Remaining Safety Infrastructure

| Step | Item | Status |
|------|------|--------|
| 1 | `detect_b2_orphans` command (Section B prerequisite) | ✅ Complete (Session 123, commit 61edad1) |
| 2 | Bulk job deletion backend — Section A items 1–6 (soft-delete fields → JobReceipt → DeletionAuditLog → pre-deletion task → cleanup command → Scheduler entry) | 🔲 Planned |
| 3 | Bulk job deletion frontend UI — Section A item 7 | 🔲 Planned — do NOT start before Step 2 complete |
| 4 | Admin operational notifications — Section C (wraps Steps 1–3) | 🔲 Planned |

> ⚠️ Step 3 (frontend UI) must not be specced or built until Step 2 is fully committed and tested.
> The Section A build order in "Bulk Job Deletion — Pre-Build Reference" is mandatory — no skipping ahead.

### Deferred P3 Items

Small items not worth individual specs — batch into cleanup passes periodically.

| Item | File | Notes |
|------|------|-------|
| `prompt_list_views.py` growth monitor | `prompts/views/prompt_list_views.py` | 620 lines, `prompt_detail` is ~320 lines — watch for growth |
| ~~`__init__.py` imports through shim~~ | `prompts/views/__init__.py` | ✅ RESOLVED Session 138 — imports directly from domain modules |
| `int(content_length)` no try/except | `prompts/tasks.py` | Pre-existing in both download functions — safe but opaque error on malformed header |

### 🚀 Planned New Features

> These features are scoped and discussed but not yet specced for implementation.
> Documented here so context is not lost between sessions.

#### Feature 1: Translate Prompts to English

**Summary:** Before generation starts, send all non-English prompts to GPT-4o in a single batch call to translate them to English. Fires during the "Starting generation…" phase — invisible to the user.

**Benefits:** OpenAI's image models perform significantly better with English prompts. Users who copy prompts from non-English sources get better outputs without manual translation. Zero user friction — happens automatically.

**Implementation approach:** One GPT-4o call with all prompts batched. System prompt: detect language of each prompt, translate to English if not already English, return array of cleaned prompts in same order. Runs after validation, before `service.create_job()`. Estimated latency: 1-3 seconds added to "Starting…" phase.

**Pros:** High value, low cost (text is cheap), one API call, no UI changes.
**Cons:** Adds latency to generation start, GPT-4o translation is not perfect for highly technical or stylistic prompts.
**Risks:** Translated prompt may lose nuance from the original language. Mitigation: only translate if detected language is not English.
**Priority:** High — relatively simple, high impact.

#### Feature 2: Generate Prompt from Source Image (Vision API)

**Summary:** A per-prompt checkbox ("Generate prompt from source image") that uses GPT-4o Vision to generate a concise image-generation prompt from the attached source image. The Vision-generated prompt replaces the text field content and is used for both generation and the result page display.

**UX behaviour:** Checkbox appears below the source image URL field. When ticked: text field disabled (strike-through on existing text), source image URL field becomes required. When ticked + Character Description is filled: Character Description still applies and is NOT struck through. Vision API call fires per ticked prompt during "Starting…" phase.

**Vision API prompt strategy:** Instruct GPT-4o Vision to output exactly 1-2 sentences covering subject, style, composition, lighting, technical quality. No narrative, no filler — generation-ready format.

**Implementation approach:** New `generate_prompt_from_image(image_url)` helper in tasks.py using GPT-4o Vision API. Called per image during job preparation, results stored on GeneratedImage as `vision_generated_prompt`. Front-end: new checkbox per prompt box, JS disables/strikes text field.

**Pros:** Major differentiator, solves "I have an image but no prompt" problem, high accuracy with Vision API.
**Cons:** One Vision API call per ticked prompt (~$0.01 each), adds latency per checked prompt, requires accessible source image URL.
**Risks:** Vision API may not always produce concise output — requires careful system prompt tuning. Source image must be HTTPS and accessible (validated by existing SSRF hardening).
**Priority:** High — genuine differentiator.

#### Feature 3: Remove Watermark Text from Prompts

**Summary:** Before generation, automatically detect and strip "watermark instructions" from prompts — text that instructs the AI to add a brand name or logo. Runs invisibly in the "Starting…" phase.

**Watermark text pattern:** Typically appears as an instruction wrapped in quotes at the end of a prompt, e.g.: `"Add The name 'IA Arte& Promts' in a clean, professional font in the bottom left corner."`

**Key distinction:** Watermark instructions tell the AI to *add text to the image*. Legitimate scene text describes *text already in the scene* (signs, storefronts). GPT-4o is reliable at distinguishing these.

**Implementation approach:** Batch GPT-4o call alongside translation (or combined into one call). System prompt: for each prompt, identify and remove any instruction to add watermark/branding text. Do not remove descriptions of existing scene text. Can be combined with translation into a single "prepare prompts" GPT-4o call.

**Pros:** High value for users who copy prompts from watermarked sources, zero user friction, one batch API call.
**Cons:** GPT-4o may occasionally misidentify legitimate text as watermark (low risk with careful prompt).
**Risks:** If combined with translation, system prompt complexity increases — test carefully.
**Priority:** High — easy to implement, high value.

#### Feature 4: Save Prompt Draft (Premium)

**Summary:** Allow users to save named prompt drafts server-side, persisting prompt text, source image URLs, pasted images, and all micro-settings. Currently drafts are saved to localStorage only and are lost on "Generate All".

**UX behaviour:** "Save Prompt Draft" button in the sticky bar. First click: modal prompts for draft name. Subsequent edits auto-save every 500ms. Draft can be loaded from a "My Drafts" page (future).

**Implementation approach:** New `PromptDraft` model (`user`, `name`, `prompts_json`, `settings_json`, `created_at`, `updated_at`). Pasted images (B2 paste URLs) must be marked as "draft-pinned" so orphan cleanup does not delete them. New API endpoints: `save_draft`, `load_draft`, `list_drafts`, `delete_draft`.

**Pros:** High value for power users, premium tier justification, prevents loss of complex prompt sets.
**Cons:** Significant storage implications (especially with paste images), requires new model + migrations + API endpoints + UI — 2-3 sessions of work.
**Risks:** Paste image pinning conflicts with orphan cleanup logic (must coordinate). Premium feature requires subscription/tier gating.
**Priority:** Medium — valuable but complex. Build after features 1-3.
**Status:** Deferred — do not spec until other new features are stable.

#### Combined "Prepare Prompts" Architecture

Features 1, 2, and 3 all fire before generation starts. They should be combined into a single "prepare prompts" step:

```
User clicks Generate →
1. Validate API key
2. Validate prompts (existing)
3. Prepare prompts (NEW single step):
   a. Strip watermark text from all prompts
   b. Translate non-English prompts to English
   c. For prompts with "generate from image" checked:
      → Vision API call per image → replace prompt text
4. Start generation job
```

The UI shows a single "Preparing prompts…" status rather than separate spinners for each step.

---

**Phase 6 Architecture — Two-Page Staging:**
- Temp staging page (`/tools/bulk-ai-generator/job/<uuid>/`): shows results of the most recent job. Phase 6 adds the publish flow here.
- Archive staging page (`/profile/<username>/ai-generations/` — FUTURE PHASE): master archive of all AI-generated images. Private to the user. Tier-based retention windows (2–10 days). Auto-delete after window expires.
- Actions on temp staging page mirror to archive staging page.

**Phase 6 Publish Flow:**
- One image (variation) per prompt can be published.
- Non-selected variations are archived (not deleted immediately).
- Visibility mapping: `job.visibility='public'` → Prompt `status=1` (Published); `'private'` → `status=0` (Draft).
- All bulk-created pages: `moderation_status='approved'` (GPT-Image-1 content policy applied at generation time).
- Private/public toggle is a paid-user feature; not in Phase 6 scope for general users.

**Bulk Publish Pipeline Architecture (Phase 6B — Session 115):**
- `publish_prompt_pages_from_job` task in `prompts/tasks.py` owns all publish logic.
- Per-image idempotency: `select_for_update()` inside `with transaction.atomic()` acquires DB row lock before checking `prompt_page__isnull=True`. Uses `_already_published` flag (cannot `continue` inside atomic block).
- `IntegrityError` on slug collision: caught at outer level, UUID suffix appended, full M2M block re-applied inside second `transaction.atomic()` (Django rolls back original block on error — M2M must be duplicated in retry path).
- `published_count` incremented via `F('published_count') + 1` inside `BulkGenerationJob.objects.filter().update()` for race-safe counting.
- `ThreadPoolExecutor` dispatches Prompt creation across worker threads; all ORM writes (Prompt.save, M2M, gen_image.save) happen on main thread after `futures.result()` — avoids Django ORM thread-safety issues.
- `_sanitise_error_message` imported locally inside function to avoid circular import (`prompts.services.bulk_generation` ↔ `prompts.tasks`).

### Key Learnings & Principles

- **BYOK is the only viable model for bulk generation at scale:** Platform-paid API model fails because all users share Mateo's rate limits, creating unacceptable wait times with concurrent users.
- **Django-Q2 runs synchronously in local dev:** Tasks queued via ORM broker execute in the web process locally (either `sync=True` setting or Django-Q2 default). This means `[BULK-DEBUG] process_bulk_generation_job CALLED` appears in `runserver.log`, not `qcluster.log`. Production behavior (separate Heroku worker dyno) is unaffected.
- **`tee` for persistent log capture:** Use `python manage.py runserver 2>&1 | tee runserver.log` and `python manage.py qcluster 2>&1 | tee qcluster.log` for reliable debug log capture. Then grep with: `grep "BULK-DEBUG\|ERROR\|Traceback" runserver.log`
- **ThreadPoolExecutor (not asyncio) for concurrent generation in Django-Q2:** Django-Q2 task context is synchronous; `asyncio.run()` does not work inside it. Use `concurrent.futures.ThreadPoolExecutor` for parallel GPT-Image-1 calls in Phase 5D.
- **`flush_all` uses `@login_required` + manual staff check (not `@staff_member_required`):** `@staff_member_required` redirects non-staff to login instead of returning 403 JSON, breaking the AJAX flow. Manual check returns `JsonResponse({'error': ...}, status=403)`. Documented with verbatim comment in codebase.
- **OpenAI Tier 1 rate limit:** 5 images/minute, 15–45s per image. Sequential generation causes unacceptable wait times at scale — Phase 5D replaces it with `ThreadPoolExecutor`.
- **`select_for_update()` must be inside `transaction.atomic()`:** In Django autocommit mode, row locks acquired outside an explicit transaction are released immediately after the SELECT. Always wrap `select_for_update()` calls in `with transaction.atomic()`.
- **`continue` is illegal inside `with transaction.atomic()`:** Use a flag variable (`_already_published = False`, set inside block, tested after) instead of `continue` inside an atomic context manager.
- **M2M assignment must be duplicated in `IntegrityError` retry block:** Django rolls back the entire `transaction.atomic()` block on `IntegrityError`, including any M2M `.add()` calls. The retry block must re-apply all M2M (tags, categories, descriptors) from scratch.
- **Static `aria-live` announcer over dynamic injection:** Dynamically injected `aria-live` regions are not reliably announced by screen readers. Declare the region in the HTML at page load and populate its text content from JS (clear + 50ms timeout before setting).

---

### N4 - Optimistic Upload Flow

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

> No current blockers as of Session 122.

| Issue | Description | Impact |
|-------|-------------|--------|
| **~~N4h rename (upload-flow)~~** | ✅ RESOLVED Session 122 (commit a9acbc4). Guard changed from `is_b2_upload and prompt.pk` to `prompt.b2_image_url`. | Resolved — upload-flow prompts now trigger rename task |
| **~~CI/CD pipeline failing~~** | ~~All 3 jobs failing~~ — **RESOLVED Session 89** (691 tests at time of fix; now 976 passing, 12 skipped, flake8 clean, bandit clean) | ✅ All 3 jobs green |


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
| **Prompt.source_credit** | CharField max_255, display name for prompt source (staff-only display) |
| **Prompt.source_credit_url** | URLField max_500, original URL if source was a link (admin-only) |
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

### Orphan Detection — B2 Migration Gap

> ✅ `detect_b2_orphans` is complete and ready to use (Session 123, commit 61edad1). The legacy `detect_orphaned_files` command (Cloudinary-only) should be reviewed for disabling in the Cloudinary audit — see planned Cloudinary Audit item in the build sequence above.

#### What Was Built (Phase D.5, October 2025)

`prompts/management/commands/detect_orphaned_files.py` (524 lines) — scans storage for
files with no matching DB record. Generates CSV reports, monitors API rate limits,
emails admins. Was scheduled on Heroku Scheduler daily at 04:00 UTC and weekly Sunday
at 05:00 UTC.

#### The Gap

The command was written for **Cloudinary**. It uses the Cloudinary API to list bucket
contents and cross-references against the DB. After the B2 + Cloudflare migration,
the command still exists in the codebase but points at a storage provider that is
no longer used for new uploads.

**Current status:** Non-functional for B2 files. Running it will scan Cloudinary
(legacy files only) and miss all B2 content entirely.

#### What Needs to Be Built

A `detect_b2_orphans` management command (or rewrite of `detect_orphaned_files`) that:
- Uses the B2 SDK (not Cloudinary) to list bucket contents under `media/` and `bulk-gen/`
- Cross-references against `Prompt.b2_image_url`, `Prompt.b2_large_url`,
  `Prompt.b2_thumb_url`, and `GeneratedImage` B2 URL fields
- Understands the shared-file window (see 'Bulk Job Deletion — Pre-Build Reference' below) — does not
  flag shared files as orphans
- Excludes admin/static asset paths explicitly (configurable prefix exclusion list)
- Maintains the same CSV report, email notification, and rate-limit protection
  patterns as the original command
- Replaces the Heroku Scheduler entries when ready

**Priority:** Must be built before job deletion goes live. A deletion system without
working orphan detection has no safety net.

#### Existing Infrastructure That Still Works

- `cleanup_deleted_prompts` command — **functional**, B2-aware, correctly calls
  `hard_delete()` which handles B2 file removal
- Heroku Scheduler — **configured and running**, just needs the B2 orphan command
  added once built
- Admin email notifications — **functional** (ADMINS setting configured)

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

> ⚠️ **Off-white backgrounds:** `--gray-500` (#737373) achieves 4.74:1 on pure white only.
> On `--gray-100` (#f5f5f5) backgrounds it drops to **3.88:1 (AA fail)**.
> Use `--gray-600` (#525252) as the minimum on any off-white or tinted background (6.86:1+).

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

**Session 125 (March 13, 2026):**
- Renamed `cloudinary_moderation.py` → `vision_moderation.py` (all import sites updated)
- Added bulk gen notification types: `bulk_gen_job_completed`, `bulk_gen_job_failed`,
  `bulk_gen_published`, `bulk_gen_partial` (migration 0073)
- New test file: `prompts/tests/test_bulk_gen_notifications.py` (6 tests)
- 1149 → 1155 tests

**Committed in Sessions 90-91 (Feb 26-27, 2026):**
- `prompts/models.py` - Added batch_id CharField to Notification model
- `prompts/services/notifications.py` - batch_id generation, group by batch_id, delete by batch_id, bleach protocol allowlist, sanitized HTML in title
- `prompts/views/admin_views.py` - batch_id delete, rate limit with remaining seconds, user-friendly delete message, timezone import
- `prompts/views/notification_views.py` - Auto-mark system notifications as read on page load
- `prompts/templates/prompts/system_notifications.html` - Quill editor HTML restoration fix, sent table redesign (removed Clicks/Status, "Most Likely Seen"), batch_id-based delete, preview card with unread dot
- `prompts/templates/prompts/notifications.html` - Render system notification title with |safe, hide quote for system type
- `prompts/templates/prompts/partials/_notification_list.html` - Same |safe and quote changes for AJAX partial
- `prompts/tests/test_notifications.py` - 69 new tests (batch_id, rate limit, delete wording, auto-mark seen, expired exclusion, click tracking, system notification service)
- `prompts/migrations/0057_add_notification_expiry_fields.py` - NEW: expires_at, is_expired fields
- `prompts/migrations/0058_add_notification_click_count.py` - NEW: click_count field
- `prompts/migrations/0059_clear_system_notification_message.py` - NEW: Clear message field for system notifications
- `prompts/migrations/0060_add_notification_batch_id.py` - NEW: batch_id field
- `static/css/pages/notifications.css` - Card alignment (flex-start), notif-body flex basis, title margin, actions min-width
- `static/css/pages/system-notifications.css` - Preview border-radius, removed preview title, button color change
- `CC_COMMUNICATION_PROTOCOL.md` - Added Test Execution Strategy section

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
| **Framework** | Django | 5.2.11 | Python web framework |
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
prompts/services/vision_moderation.py   # VisionModerationService (OpenAI Vision)
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

### Working on Bulk Generator?

```
TEMPLATES:
prompts/templates/prompts/bulk_generator.html   # Full page template

JAVASCRIPT — Input page (3 modules):
static/js/bulk-generator.js            1,547 lines (main IIFE — form, validation, auto-save)
static/js/bulk-generator-utils.js      89 lines    (BulkGenUtils — URL validation, paste helpers)
static/js/bulk-generator-paste.js      78 lines    (BulkGenPaste — clipboard paste upload)

JAVASCRIPT — Job page (5 modules — window.BulkGen namespace):
static/js/bulk-generator-config.js     156 lines  (BulkGen namespace + config object)
static/js/bulk-generator-ui.js         338 lines  (gallery render, createGroupRow, parseGroupSize)
static/js/bulk-generator-gallery.js    452 lines  (card states, fillImageSlot, fillFailedSlot, lightbox)
static/js/bulk-generator-polling.js    ~408 lines (status API polling loop)
static/js/bulk-generator-selection.js  581 lines  (image selection, publish bar)

CC safety threshold: 780 lines per file.
Job page modules well below threshold. Input page main file at 1,546 lines (🟠 High Risk).

CSS:
static/css/pages/bulk-generator.css   # All styles (~1100 lines)

BACKEND:
prompts/views/bulk_generator_views.py        # 7 API endpoints + page view
prompts/services/bulk_generation.py          # BulkGenerationService
prompts/services/image_providers/            # Provider abstraction
prompts/services/image_providers/base.py     # Abstract base class
prompts/services/image_providers/openai_adapter.py  # GPT-Image-1 adapter
prompts/tasks.py                             # generate_single_image task
prompts/models.py                            # BulkGenerationJob, GeneratedImage

TESTS:
prompts/tests/test_bulk_generator_views.py   # ~48 tests
prompts/tests/test_source_credit.py          # 21 tests
prompts/tests/test_bulk_gen_notifications.py # 6 tests (Session 125 — NOTIF-BG-1+2)

UTILITIES:
prompts/utils/source_credit.py               # parse_source_credit() + KNOWN_SITES
```

### Bulk Job Deletion — Pre-Build Reference (DO NOT BUILD WITHOUT READING THIS)

> ⚠️ Read this entire section before writing any deletion spec for BulkGenerationJob.
> Skipping any of these safeguards risks deleting images that paying customers have published.

#### The Shared-File Risk

When a `GeneratedImage` is published as a `Prompt`, the two records initially share
the same physical file in B2. The file is not duplicated — both records point at
the same B2 path.

After `rename_prompt_files_for_seo` runs, the `Prompt` gets its own independent file
at a new SEO-friendly path. At that point the records are genuinely separate.

**The danger window:** Between publish and rename completion, deleting the job's B2 file
also destroys the Prompt's image. The N4h upload-flow rename bug was resolved in Session 122 (commit a9acbc4) — the danger window is now bounded for both bulk-gen and upload-flow prompts.

#### Mandatory Pre-Deletion Checklist

No B2 file belonging to a BulkGenerationJob may be deleted until ALL of the following
pass for that specific file:

1. `GeneratedImage.prompt_page` is NULL — image has not been published as a Prompt
2. No `Prompt.b2_image_url` or `Prompt.b2_large_url` matches this B2 path
3. No pending rename task exists for this image in the Django-Q queue

If any check fails → skip that file. Log the skip with the reason. Never silently ignore.

#### Soft Delete Architecture (Follow Phase D.5 Pattern Exactly)

Do NOT build a separate deletion system for jobs. Extend the existing soft-delete
pattern that Phase D.5 established for Prompts:

- Add `deleted_at`, `deleted_by`, `deletion_reason` fields to `BulkGenerationJob`
- Follow the same `soft_delete()`, `restore()`, `hard_delete()` method pattern
- 72-hour pending window before permanent B2 deletion (vs 5-30 days for Prompts —
  jobs are staff/tool artifacts, not user-created content requiring long retention)
- Hard deletion is a Django-Q task that runs the pre-deletion checklist before
  touching any B2 file

#### New Records Required

**JobReceipt** — A separate immutable model created at job completion. Records:
prompts submitted, images successfully generated, sizes, quality settings, actual cost,
timestamp. This record must survive job deletion permanently — it is the billing audit
trail. Do not cascade-delete it when a job is deleted.

**DeletionAuditLog** — Every B2 file actually deleted gets a log entry:
job ID, GeneratedImage ID, B2 file path, timestamp, which checklist check
authorised deletion. Stored in DB indefinitely. Non-deletable by users.

#### Existing Infrastructure to Reuse

- `cleanup_deleted_prompts` management command — extend or mirror for job cleanup
- Heroku Scheduler already configured — add a job cleanup task to existing schedule
- Trash UI pattern from Phase D.5 — reuse for job deletion UI if needed
- `soft_delete()` / `restore()` model methods — copy the pattern from `Prompt` model

#### What to Build (Ordered)

1. Soft-delete fields on `BulkGenerationJob` (migration)
2. `JobReceipt` model (migration)
3. `DeletionAuditLog` model (migration)
4. Pre-deletion checklist task in Django-Q
5. `cleanup_deleted_jobs` management command (mirrors `cleanup_deleted_prompts`)
6. Heroku Scheduler entry for job cleanup
7. Frontend delete UI (mirrors Prompt trash UX)

Do not build item 7 before items 1–6 are complete and tested.

### Views Package Structure

Views were split into a modular package for maintainability:

```
prompts/views/
├── __init__.py              # Exports all views
├── admin_views.py           # Admin functions (ordering, bulk actions)
├── api_views.py             # API shim (Session 128 split)
├── ai_api_views.py          # AI suggestions, job status (Session 128 split)
├── moderation_api_views.py  # NSFW moderation endpoints (Session 128 split)
├── social_api_views.py      # Collaborate, like endpoints (Session 128 split)
├── upload_api_views.py      # B2 upload, presign, paste endpoints (Session 128 split)
├── bulk_generator_views.py  # Bulk generator page + 8 API endpoints
├── collection_views.py      # Collections API
├── generator_views.py       # AI generator filter pages
├── leaderboard_views.py     # Leaderboard/ranking pages
├── notification_views.py    # Notification API + page views
├── prompt_views.py          # Shim — re-exports from 4 domain modules (Session 134)
├── prompt_list_views.py     # PromptList, prompt_detail, related_prompts_ajax (620 lines)
├── prompt_edit_views.py     # prompt_edit (320 lines — prompt_create removed Session 135)
├── prompt_comment_views.py  # comment_edit, comment_delete (139 lines)
├── prompt_trash_views.py    # prompt_delete, trash_bin, restore, publish, perm_delete, empty (396 lines)
├── redirect_views.py        # URL redirects and legacy routes
├── social_views.py          # Social sharing endpoints
├── upload_views.py          # Upload page views
├── user_views.py            # User profile pages
└── utility_views.py         # Utility/helper views
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

## 🔔 Admin Operational Notifications — Planned Architecture

> 📌 This is a planned future system. Nothing here is built yet.
> Capture date: Session 122 (March 12, 2026).

### The Problem

Scheduled tasks and management commands (cleanup, orphan detection, rename tasks,
job deletion) currently output only to Heroku logs. Non-technical admins have no
visibility into what's happening. A 500 error, a failed cleanup run, or a batch of
orphaned files discovered overnight is invisible to anyone not actively tailing logs.

### The Vision

Tie all automated operations into the existing notification infrastructure so that:
- The frontend notification bell shows admins a summary of scheduled task outcomes
- The admin-only sub-tab in the notifications UI shows a health feed of all operations
- Issues (errors, orphans found, failed images) surface as actionable notification cards
- Non-technical admins can understand platform health without touching Heroku logs

### What Already Exists to Build On

| Infrastructure | Status | Notes |
|---------------|--------|-------|
| Notification model (6 types, 5 categories) | ✅ Built — Session 86 | Has `system` type for admin-originated notifications |
| Frontend bell dropdown + polling (15s) | ✅ Built — Sessions 86–91 | Already shows unread count |
| System notifications page + admin send UI | ✅ Built — Sessions 90–91 | Quill editor, batch send, preview |
| Admin-only notification sub-tab | ✅ Built | Already segregates admin-visible content |
| `create_notification()` service | ✅ Built — `prompts/services/notifications.py` | Can be called from management commands |
| Django-Q task infrastructure | ✅ Built | Background tasks already run; can emit notifications |

### Events to Surface (Priority Order)

**P1 — Surface immediately when they occur:**
- 500 errors (Django signal or middleware → notification)
- Bulk generation job failures (entire job failed, not just single images)
- B2 file deletion failures (items stuck in pending deletion queue)
- Orphan detection: critical finds (B2 files with no DB record AND no pending task)

**P2 — Daily digest (batch into one notification):**
- Cleanup run summary: N jobs deleted, N files removed, N skipped (shared-file window)
- Orphan detection run summary: N files scanned, N orphans found, N already resolved
- SEO rename task outcomes: N renamed, N failed, N pending

**P3 — Weekly digest:**
- DB + B2 consistency check results
- Cost tracking summary: actual spend vs estimated for the week
- Deletion audit log summary: files deleted, skipped, errors

### Implementation Notes (For Future Spec)

- Management commands should call `create_notification()` at completion with a
  structured summary. Use `notification_type='system'`, target admin users only.
- Notification title should be machine-readable enough to be filterable
  (e.g. "Cleanup Run: 3 jobs deleted, 2 skipped") — not just "Cleanup complete".
- The admin notification sub-tab should have a "Health" filter category in addition
  to existing categories — shows only automated-system notifications.
- Batch digest notifications should use the existing `batch_id` field to group
  related events so admins can dismiss an entire run's notifications at once.
- Error notifications (P1) should persist until explicitly dismissed — do not
  auto-expire them.
- The 500 error capture should use Django's existing exception middleware, not a
  third-party service — keep it in-house and route through the notification system.

### What This Is NOT

This is not a replacement for Heroku logs. It is a human-readable operational
summary layer for non-technical admins. Technical staff should still use logs for
debugging. This system surfaces outcomes, not stack traces.

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

**Version:** 4.30 (Session 121 — SMOKE2 series A–E, HARDENING-1, JS-SPLIT-1, HARDENING-2; 1117 tests; bulk-gen smoke test complete; all SMOKE2 production prompts backfilled)
**Last Updated:** March 16, 2026
