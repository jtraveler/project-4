# CLAUDE_ARCHIVE_COMPLETED.md
# Archived Recently Completed Entries

This file contains older entries from CLAUDE.md's "Recently Completed"
table, archived to keep the main reference document concise.

For the full narrative of each session, see CLAUDE_CHANGELOG.md.
For current and recent entries, see CLAUDE.md.

Archived: April 2026 (Session 153-M)

---

## Entries

| Phase | When | What It Was |
|-------|------|-------------|
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
