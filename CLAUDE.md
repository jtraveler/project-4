# CLAUDE.md - PromptFinder Project Documentation (1 of 3)

## ⚠️ IMPORTANT: This is Part 1 of 3

**Before proceeding, also read:**
- **CLAUDE_PHASES.md** - Phase specs, unfinished work details
- **CLAUDE_CHANGELOG.md** - Session history, recent changes

These three files together replace the original CLAUDE.md.
Do NOT edit or reference this document without reading all three.

---

**Project Status:** Pre-Launch Development
**Last Updated:** May 1, 2026

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
| `CLAUDE_ARCHIVE_COMPLETED.md` | Archived older "Recently Completed" rows from CLAUDE.md (Session 153-M) |

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
| **Phase REP** | 🔄 ~98% | Multi-provider bulk generation (Replicate/xAI) | `_download_image` duplication (P3). NSFW UX feedback for Replicate platform model 400s (P2). Cloudinary full removal: `UserProfile` avatar done in Session 163; `Prompt.featured_image` + `Prompt.featured_video` CloudinaryField → CharField migration still pending (P2). Rate limiting audit for Replicate/xAI: only global `BULK_GEN_MAX_CONCURRENT=1` ceiling currently — provider-specific concurrency config deferred (P2, detail at §Phase REP Blockers). |

### What's Paused (Don't Forget!)

| Phase | Status | Description | What's Left |
|-------|--------|-------------|-------------|
| **Phase K** | ⏸️ ~96% | Collections ("Saves") | Trash video bugs (3), K.2: Download tracking, virtual collections; K.3: Premium limits |
| **Phase P2-B** | 🔲 Planned | Admin Log Tab | Activity log for staff actions |
| **Phase P2-C** | 🔲 Planned | Web Pulse Tab | Site analytics and pulse data |

### Recently Completed

| Phase | When | What It Was |
|-------|------|-------------|
| Session 173-F | May 1, 2026 | NSFW chip redesign + report-to-admin mailto stub + Tier 2 architectural fix + seed restoration deferred. **Single-spec cluster, 5 folded items, single commit.** (1) **Chip layout** (closes 173-C deferred preference): replaces 14px inline icon with stacked layout — large gray icon (~3em) over red "Content blocked" pill over body copy with two inline links ("learn more" + "Let us know"). New CSS modifier `.error-chip--stacked` + child classes `__pill`/`__body`/`__link`. Stacked applied ONLY to content_policy variant — auth/quota/rate_limit/exhausted/retrying chips keep inline rendering (intentional asymmetry). New JS helper `_renderContentPolicyChip` builds via DOM-node construction. (2) **Block source distinction** (new): backend now includes `block_source: 'preflight' \| 'provider'` in validate + polling responses. Frontend chip body copy varies — preflight: "We flagged this prompt because..."; provider: "This prompt may have violated...". Memory Rule #13 silent-fallback: missing field defaults to provider-side wording (semantically conservative). (3) **Tier 2 advisory architectural fix** (surfaced during testing): legacy `check_text` `_load_word_list` loaded ALL active words regardless of `block_scope`, so Tier 1 universal always caught advisory words first — Tier 2 advisory NEVER fired in production despite 173-B/E shipping the full pipeline. Fix: filter `block_scope='universal'` in `_load_word_list`. Required for Mateo's headline activation test to actually verify Tier 2. (4) **Report-to-admin mailto stub** (closes 173-C deferred-feature, partial): "Let us know" link constructs `mailto:` URL with auto-populated context. New `CONTENT_BLOCK_REPORT_EMAIL` Django setting (default `matthew.jtraveler@gmail.com`, swappable via env var). Surfaced to JS via `data-content-block-report-email` attribute. Full backend report system deferred to Session 175. (5) **Seed restoration BLOCKED** at permission layer: `heroku run python manage.py seed_provider_advisory_keywords` denied by harness despite spec authorization. Mateo runs manually post-deploy (idempotent command restores 11 missing advisory keywords from accidental admin-UI deletion). Code changes ship without depending on seed-state — chip redesign + block_source threading work for any seed state. **Activation test deferred until seed restored.** 3 new tests on validate endpoint (block_source flow, settings smoke check). 1411 → 1414 tests. Memory Rules #16 (3 deferred items closed) + #17 (single-commit pattern) + #13 (silent fallback documented) + #14 (closing checklist with activation as headline). Commit pending. Agent avg pending. |
| Session 173-E | May 1, 2026 | Frontend wire-up of `model_identifier` in `api_validate_prompts` POST body — activates 173-B Tier 2 advisory pre-flight in production. Closes REPORT_173_B Section 5 P2 deferred item (Memory Rule #16 application — explicit closure of prior-session deferred item before Session 174 begins). **Step 0 finding:** the backend wire-up was ALREADY DONE in 173-B (commit `e06ab5c`, `bulk_generator_views.py:267-275` already extracts `model_identifier` with isinstance defense + passes to service). The remaining gap was frontend-only — `bulk-generator-generation.js:911` POST body excluded `model_identifier`. **One-line fix:** added `model_identifier: (I.settingModel && I.settingModel.value) || ''` to the validate fetch body. Defensive empty-string fallback covers uninitialised state — backend then falls back to Tier 1 universal-only (the 173-B-defined backward-compat path; not silent corruption, so Memory Rule #13's `logger.warning` requirement does NOT apply). **3 new defensive tests** in `ValidatePromptsAPITests`: happy-path (model_identifier flows to `service.validate_prompts(prompts, provider_id=...)`), backward-compat (omitted field defaults to empty), defensive boundary (list/dict/null/int/bool all coerce to empty at the HTTP boundary, never passed to service). All 11 ValidatePromptsAPITests pass (8 prior + 3 new). **Memory Rule #17 single-commit pattern:** docs and code ship in same commit; "see commit log for hash" phrasing avoids self-referencing chicken-and-egg. **Cluster shape:** SINGLE-SPEC. Commit: see git log. Agent avg pending. 1411 tests (1408 pre + 3 new). |
| Session 173-D | May 1, 2026 | End-of-session docs update for the 173 cluster + 171-D/172-D placeholder backfills + 2 new memory rules. (1) 4 new `CLAUDE_CHANGELOG.md` entries (173-A, -B, -C, -D); (2) 4 new "Recently Completed" rows (above) + Session 175 placeholder section added documenting the full policy-docs cluster scope (~80 lines: self-drafted policy posture, DMCA registration plan, cost absorption framework, content ownership, policy-drafting skill outline, stage-gate references); (3) **Memory Rules count 15 → 17 of 30** with 2 new rule entries: **#16 (surface deferred backlog at session start)** — established after the silent-accumulation pattern in 171-D and 172-D; **#17 (docs spec self-reference backfill)** — solves the recurring "Commit pending. Agent avg pending." pattern; (4) **171-D and 172-D placeholders backfilled** (171-D: `Commit pending. Agent avg pending.` → `Commit \`3dc7e17\`. Avg 9.0/10.`; 172-D: same shape → `Commit \`66c15da\`. Avg 9.1/10.`); (5) CSS:1338 font-size removal documented as intentional (Mateo's UX call — preexisting in 172-A working tree, not a bug); (6) PFS top-line counts: Last Updated April 29 → May 1, Sessions span 163–172 → 163–173, Tests 1400 → 1408 (+6 from 173-B, +2 from 173-C), Migrations 93 → 94 (+0092 from 173-B), Test Files +2; (7) version footer 4.70 → 4.71. Cluster shape: **HYBRID** per Memory Rule #15 — 173-A and 173-B drafted from prior-session evidence, 173-C depends on 173-B's URL slug, 173-D depends on all three. **This 173-D row is itself a Memory Rule #17 application — backfilled in a follow-up commit immediately after the docs commit.** Commit `474b308` (docs) + the backfill commit applying Rule #17 itself. Agents @technical-writer (sub via general-purpose) 8.5, @code-reviewer 9.5. Avg 9.0/10. 1408 tests (no change). |
| Session 173-C | May 1, 2026 | content_policy chip icon + placeholder content policy page. (1) **icon-alert-circle added to sprite** (Lucide alert-circle, 39 → 40 icons total) — universally recognized warning glyph. Index comment updated. (2) **Chip rendering prepends 14px alert-circle icon for content_policy variant only** — `_classifyErrorChip` adds `iconId` field on the content_policy classification dict; `_renderErrorChip` renders SVG icon BEFORE the label so flexbox order reads "[icon] Content blocked". Other chip variants (auth, quota, rate_limit, server_error, invalid_request) keep text-only — out of scope. Sprite URL accessed via `G.spriteUrl` (project pattern at gallery.js:289), NOT `window.SPRITE_URL` (a Round 1 BLOCKER from spec pseudocode that doesn't exist in the codebase). (3) **"Learn more" link in failed-slot for content_policy** — separate `<a>` DOM node (not inline HTML, because reason text is rendered via textContent at multiple call sites). Link: `/policies/content/`, target=_blank, rel=noopener noreferrer, descriptive aria-label. (4) **Placeholder content policy page** at `/policies/content/` — minimal ~200-word page honest about being pre-launch. Links to `mailto:matthew.jtraveler@gmail.com` for reports. Full policy ships in Session 175. View `ContentPolicyPlaceholderView(TemplateView)` in utility_views.py (TemplateView import at top per E402). 2 new smoke tests pass. **Round 1 review:** @code-reviewer 7.5/10 (BLOCKED on `window.SPRITE_URL` undefined); fix applied + Round 2 9.2/10 re-verified. **Round 1 false alarm:** @ui-visual-validator misread DOM-order; appendChild order is correct (icon child[0], label child[1] → flex renders [icon] [label]). Commit `bef3115`. Agents @frontend-developer 9.2, @accessibility-expert (sub) 9.5, @code-reviewer 7.5→9.2 (Round 2), @ui-visual-validator 9.0. Avg 9.225/10. 1408 tests. |
| Session 173-B | May 1, 2026 | NSFW pre-flight v1 — provider-aware ProfanityWord. Mateo's account-suspension risk: every NSFW prompt that reaches the API counts against PromptFinder's API account; xAI charges $0.02/rejection, OpenAI/Google can suspend access. Pre-flight catches most before any API call. **Tiered architecture:** Tier 1 (universal, existing block_scope='universal') blocks across ALL providers; Tier 2 (provider advisory, new block_scope='provider_advisory' + affected_providers JSONField) blocks only when user has selected one of the listed providers. **Changes:** ProfanityWord 4 new fields (block_scope, affected_providers, last_reviewed_at, review_notes), migration 0092 (4 AddField only), profanity_filter.py new `check_text_with_provider()` method (universal-then-advisory pattern, dict return), bulk_generation.py `validate_prompts(prompts, provider_id='')` extended (Tier 1 still uses legacy `check_text` for backward-compat; Tier 2 conditional), bulk_generator_views.py extracts `model_identifier` from request, new `seed_provider_advisory_keywords` management command (idempotent, --dry-run), admin UI new "Provider Awareness" fieldset section. **Implementation deviation from spec section 5.2:** affected_providers__contains ORM filter is inconsistent between PostgreSQL prod and SQLite test for "list-contains-string" — switched to fetch-all-advisory + filter-in-Python pattern (defense + cross-backend). **Frontend wire-up of model_identifier in /api/validate/ POST body is OUT OF SCOPE per spec section 6.2** — backend defaults to empty provider_id (Tier 2 skipped), backward-compat preserved. Documented as Remaining Issue follow-up. **Pre-existing security gap noted (NOT introduced by 173-B):** api_start_generation does not call validate_prompts server-side — relies on frontend voluntarily hitting api_validate_prompts first. Mitigated by @staff_member_required decorator. Mateo runs after deploy: `python manage.py seed_provider_advisory_keywords --dry-run` then without --dry-run; tunes via /admin/prompts/profanityword/. Commit `e06ab5c`. Agents @django-pro 8.8, @backend-security-coder 8.7, @code-reviewer 9.3, @test-automator 9.0, @architect-review 8.8. Avg 8.92/10. 1408 tests (1400 pre + 6 new). |
| Session 173-A | May 1, 2026 | Per-card "Use master" reset bugs + xAI keyword rename. Three independent reset gaps all manifested as "per-card quality shows 4K instead of Use master, even after delete-all + add-new". (1) `handleModelChange` (bulk-generator.js:1037) only forced `sel.value='high'` on non-quality-tier models — switching back to a quality-tier model left stale `'high'` values. Added `else { sel.value = ''; }` branch + 18-line block comment documenting the UX tradeoff (clobbering explicit per-box choice on model swap is acceptable for the three-part rationale documented inline). (2) `clearAllConfirm` (bulk-generator-generation.js:415) cleared text/paste/error but not per-box override dropdowns. Added 16-line per-box override reset block — resets quality, size, images, vision, direction-checkbox, direction-text, dirRow display, has-override class. (3) `resetMasterConfirm` (bulk-generator-generation.js:460) reset master row but not per-box overrides. Plus a separate latent bug: `I.settingModel.value = 'gpt-image-1'` is NOT a valid model_identifier — silently fell back to first dropdown option (Flux Schnell). Slug corrected to `'black-forest-labs/flux-schnell'` (Mateo confirmed) + per-box reset block added + `I.handleModelChange()` call appended to refresh capability UI. Bug #5 (sticky pricing not updating on master quality change) was downstream of 1-3 — fixes 1-3 resolve it automatically. (4) Pulled-forward cleanup from 172-B agent feedback: `_POLICY_KEYWORDS` → `_XAI_POLICY_KEYWORDS` rename in xai_provider.py at all 4 occurrences (definition, 2 comments, 2 usages) + 2 stale test comment updates. **`replace_all`-with-substring-containment gotcha** caught via verification grep — initial replace_all turned `_XAI_POLICY_KEYWORDS` into `_XAI_XAI_POLICY_KEYWORDS` because old name is a substring of new. Fixed with second replace_all + targeted edit; documented as future-spec gotcha. **CSS:1338 font-size removal is intentional** — Mateo's UX call (preexisting from 172-A working tree, the 0.9rem font on `.publish-modal-links li` was unreadable). Documented in 173-D section. Commit `369b2a0`. Agents @frontend-developer 9.4, @code-reviewer 9.5, @accessibility-expert (sub) 9.0, @django-pro 9.5. Avg 9.35/10. 1400 tests (no change — JS-side fixes verified manually). |
| Session 172-D | Apr 29, 2026 | End-of-session docs update for the 172 cluster. (1) 4 new `CLAUDE_CHANGELOG.md` entries (172-A, -B, -C, -D); (2) 4 new "Recently Completed" rows + Session 171 Verification-Pending row resolved (modal + NB2 chip verified, Grok chip resolved via 172-B's separate root cause); (3) 3 new Deferred P2 rows (modal persistence on bulk publish refresh, IMAGE_COST_MAP per-model restructure (Scenario B1), Reset Master + Clear All Prompts UX); (4) 1 new Deferred P3 row (Try-in URL future text change for single-page generator); (5) Memory rules count unchanged at 15 of 30 (no new rules in 172); (6) PFS top-line counts: Last Updated April 26 → April 29, Sessions span 163–171 → 163–172, Tests 1396 → 1400, Migrations unchanged (none added in 172); (7) version footer 4.69 → 4.70. Cluster shape: **BATCHED with prior-session evidence capture** per Memory Rule #15 — three pieces of evidence anchored the cluster (172-A static review of 4 surfaces, 172-B Mateo's heroku pg:psql capture of verbatim xAI rejection wording, 172-C static review of `bulk-generator-ui.js:88` + backend payload contract). **Precedent documented:** when log-based investigation fails (Memory Rule #13 violation masking the symptom), database-state inspection is a valid fallback for read-only diagnostics. 172-B itself fixed the Memory Rule #13 violation that necessitated the workaround. Commit `66c15da`. Agents @technical-writer (sub via general-purpose) 9.2, @code-reviewer 9.0. Avg 9.1/10. 1400 tests (no change). |
| Session 172-C | Apr 29, 2026 | Per-image overlay restoration on page reload. Mateo regression: published-badge overlays were lost on page reload because `G.markCardPublished` (introduced 170-B at `bulk-generator-gallery.js:49`) was only called from `startPublishProgressPolling` (`bulk-generator-selection.js:805`) which only runs after a Create Pages click. **Fix:** frontend-only — extended `G.renderImages` (`bulk-generator-ui.js:88`) to call `markCardPublished` for any image whose polling payload has `prompt_page_id` set. Placement: AFTER the status branch (completed/failed/generating/queued), INSIDE the per-image `for` loop. Truthiness guard `if (image.prompt_page_id && image.id)` avoids null cases. Idempotency guaranteed by `markCardPublished`'s early-return at `bulk-generator-gallery.js:56` (`if (slot.classList.contains('is-published')) return;`) plus secondary `!slot.querySelector('.published-badge')` guard. Backend payload contract verified intact at `bulk_generation.py:430-431`. **Tests:** 2 new tests in `PublishFlowTests` (multi-image variants, count=2) — `test_172_c_polling_response_exposes_page_id_for_multiple_published` + `test_172_c_polling_response_nulls_page_id_for_multiple_unpublished`. Complement existing single-image tests at `test_bulk_generator_views.py:1284-1362`. Commit `1b59266`. Agents @frontend-developer 9.5, @code-reviewer 9.2, @accessibility-expert (sub) 9.0, @ui-visual-validator 9.0. Avg 9.175/10. 1400 tests. |
| Session 172-B | Apr 29, 2026 | Grok content moderation hotfix — `_POLICY_KEYWORDS` expansion. Mateo verified post-170-B that NB2 NSFW failures correctly displayed the red "Content blocked" chip but Grok NSFW failures continued showing legacy "Failed — Invalid request" text. **Root cause:** xAI's actual rejection wording is `"Generated image rejected by content moderation."` — but `_POLICY_KEYWORDS` (line 37 of `xai_provider.py`) had no entry matching `'moderation'` or `'rejected'`. Fall through to `invalid_request` branch. **Evidence trail:** Mateo captured the verbatim wording from production Postgres via `heroku pg:psql` (database-state inspection was the only diagnostic path because Memory Rule #13's silent-fallback observability principle had been violated — no log line on the BadRequestError fallthrough). **Fix:** (1) Added `'moderation'` and `'rejected'` to `_POLICY_KEYWORDS` (defense-in-depth for xAI wording variations); both content_policy detection paths benefit (SDK at line 166 + httpx-direct edits at line 292) — single tuple shared. (2) Added `logger.info` on BadRequestError fallthrough path per Memory Rule #13. Future investigations can read Heroku logs instead of querying Postgres. Log level `info` (not `warning`) — expected taxonomy gap, not error condition. `[:300]` truncation safety margin. **Architectural concerns surfaced (P3):** `'rejected'` is broader keyword (could appear in parameter validation 400s); xAI keyword-matching is provider-specific (OpenAI uses structured `error.code`); `_POLICY_KEYWORDS` should rename to `_XAI_POLICY_KEYWORDS` if other providers add similar detection. **Tests:** 2 new in `XAINSFWKeywordTests` — `test_xai_content_moderation_classified_as_content_policy` (uses verbatim psql-captured wording) + `test_xai_unrecognized_400_logs_at_info` (Memory Rule #13 observability via `assertLogs`). Commit `b00c0d9`. Agents @code-reviewer 9.3, @debugger 9.5, @test-automator 9.5, @architect-review 8.8. Avg 9.275/10. 1400 tests. |
| Session 172-A | Apr 29, 2026 | Bundled polish — 4 small fixes. (1) **Modal footer transparent background** — `.publish-modal-footer` uses `<footer>` element semantically and inherits global page `<footer>` dark background via element selector. Class rule had no `background` property — added explicit `background: transparent`. CSS-only fix preferred over markup change to preserve semantics. (2) **Per-box disabled quality select styling** — `.bg-box-override-select` had no `:disabled` rule; added rule mirroring master row's `.bg-select:disabled` (line 155-159) byte-for-byte: `gray-100` bg, `gray-400` color, `cursor: not-allowed`. WCAG 1.4.3 disabled-controls exemption applies. (3) **Memory Rule #13 logger.warning in `tasks.py`** — both Replicate (line 3138) and OpenAI (line 3140) silent-fallback branches for `model_name` now emit `logger.warning` BEFORE the silent assignment per Session 169-B's established rule. Structured field `job_id`; actionable message references `api_start_generation` endpoint and `GeneratorModel` seed. (4) **Nano Banana 2 master quality default to 1K** — when user selects NB2, master quality auto-selects "1K" (low) instead of preserving prior selection. Guard `if (_qs.value !== 'low')` preserves explicit within-session user choice. Compatible with autosave restore (handleModelChange runs first then restore overwrites). **Pre-existing working-tree state acknowledged:** session began with `bulk-generator-job.css` already modified (font-size removal in `.publish-modal-links li` line 1338 was preexisting); bundled into commit and documented in REPORT Section 4. Commit `d340e1e`. Agents @frontend-developer 9.0, @code-reviewer 8.5, @accessibility-expert (sub) 8.5, @django-pro 9.5. Avg 8.875/10. 1400 tests (no test additions for this spec; visual + observability paths). |
| Session 171 — Modal + Chip Production Verification | ✅ **Resolved** (Apr 29, 2026) | Modal + NB2 chip verified post-171 deploy via Mateo's Memory Rule #14 closing checklist. The Grok chip regression (Regression C) was resolved separately via Session 172-B with a different root cause (`_POLICY_KEYWORDS` keyword-list gap, not the chip pipeline that 171-INV had inspected as structurally intact). Lesson learned: log-based investigation failed because Memory Rule #13 silent-fallback observability had been violated; 172-B fixed both the keyword gap AND the underlying observability principle. |
| Session 171-D | Apr 26, 2026 | End-of-session docs update for the 171 cluster. (1) 4 new `CLAUDE_CHANGELOG.md` entries (171-A, -B, -C, -D); (2) 4 new "Recently Completed" rows + 1 Verification-Pending row (above); (3) 2 new Deferred P2 rows (page-refresh state recovery during bulk publish, Replicate concurrency policy) — both surfaced by Mateo April 26; (4) 1 new Deferred P3 row (gpt-image-2 pricing audit — pending OpenAI per-quality/size data publication, since 171-C chose Option B2 mirror placeholder); (5) Memory rules count `13 of 30` → `15 of 30` with rules #14 (REPORT closing checklist — added 2026-04-26) and #15 (cluster-shape disclosure) entries; (6) PFS top-line counts: Last Updated April 25 → April 26, Sessions span 163-169 → 163-171, Tests 1386 → 1396, Migrations 90 → 93; (7) version footer 4.68 → 4.69. Cluster shape: **BATCHED with prior-session investigation** per Memory Rule #15 — investigation-then-batched-fix pattern eliminated unknown-unknowns. Commit `3dc7e17`. Agents @technical-writer (sub via general-purpose) 9.0, @code-reviewer 9.0. Avg 9.0/10. 1396 tests (no change). |
| Session 171-C | Apr 26, 2026 | GPT Image 2 (BYOK) integration. OpenAI released gpt-image-2 on April 21, 2026 (model ID `gpt-image-2`); spec adds it as a BYOK-only selectable model mirroring `gpt-image-1-5-byok`. Five surfaces: new `AI_GENERATORS['gpt-image-2-byok']` entry, new `AI_GENERATOR_CHOICES` tuple entry (Round 2 fix — see below), new `GeneratorModel` row seeded by migration 0090 (RunPython, idempotent via `update_or_create`) AND mirrored in `seed_generator_models.py` for fresh-DB convergence (defaults byte-identical), choices migration 0091 (auto-generated; AlterField on both `Prompt.ai_generator` and `DeletedPrompt.ai_generator` per the 169-C sibling-field pattern), `OpenAIImageProvider` threading `model_name` through `__init__` → `self.model_name` → API calls (replaces 2 hardcoded `'gpt-image-1.5'` literals; default preserves backward compat), `tasks.py` `_provider_kwargs` setup gains `elif job.provider == 'openai':` branch (mirrors existing Replicate pattern). **IMAGE_COST_MAP scenario:** chose Option B2 (mirror gpt-image-1.5 prices as placeholder) — gpt-image-2 is BYOK so OpenAI bills user directly; displayed cost is informational only; per-model restructure deferred as P3. **Round 1 caught a blocking gap** — AI_GENERATOR_CHOICES in `prompts/models/constants.py` did not include the new slug; without it, Django model validation would silently reject `prompt.save()` for any GPT Image 2 publish (silent corruption per memory rule #13). Round 2 fix: tuple entry + auto-generated migration 0091. `# noqa: C901` added to `process_bulk_generation_job` (new `elif` pushed flake8 complexity 15 → 16; suppression matches existing in-file precedent). Real SEO copy + dedicated icon deferred per existing P3 rows. Commit `843d12e`. Agents Round 1: @django-pro 8.5, @code-reviewer 6.5 (BLOCKED), @architect-review 8.5 (false-alarm on promotional_label), @database-migrations (sub) 9.0; avg 8.125. Round 2 (focused): @django-pro 9.5, @code-reviewer 9.5; avg 9.5. 1396 tests. |
| Session 171-B | Apr 26, 2026 | Cleanup: quality labels + Try-in URLs + 170-B P2/P3. (1) Per-generator `quality_label_map` field on `AI_GENERATORS['nano-banana-2']` → maps `low/medium/high` to `1K/2K/4K` (additive; generators without override fall back to default capitalize). View injects `quality_label_map_json` via JSON; template exposes via `data-quality-label-map`; polling.js parses with try/catch fallback; new `G.formatQualityLabel(quality)` helper in config.js; ui.js routes per-prompt-group meta AND single-quality-override header through it. (2) AI_GENERATORS website URLs audited via WebFetch + WebSearch — all 7 bulk-gen entries updated to verified official model-owner pages. Notable: `grok-imagine` → `x.ai/api/imagine`, `gpt-image-1-5-byok` → `platform.openai.com/docs/models/gpt-image-1.5`, all 4 Flux variants → `bfl.ai/` (older variant pages no longer documented on BFL homepage; falls back to model-owner root per spec rule), `nano-banana-2` → `gemini.google/overview/image-generation/` (replaces broken `nanobanana.ai` ECONNREFUSED). (3) 170-B P3 (auth wording divergence) resolved — typed-error map and legacy reasonMap unified to `"Authentication failed — update your API key."`. (4) 170-B P2 (Done auto-focus guard) resolved — `setPublishModalTerminal` now compound-guards `closeBtn !== document.activeElement && doneBtn !== document.activeElement` before `.focus()` (prevents screen-reader announcement thrash on terminal-state re-entry). Commit `6a58ef9`. Agents @code-reviewer 9.0, @frontend-developer 9.0, @django-pro 9.0, @accessibility-expert (sub) 9.0. Avg 9.0/10. 1396 tests. |
| Session 171-A | Apr 26, 2026 | Multi-line `{# #}` Django comment fix. Three multi-line `{# ... #}` blocks in `bulk_generator_job.html` (lines 150-153, 172-176, 224-228 pre-fix) were leaking as visible page text on bulk job results pages — Django's `{# #}` regex (`\{#.*?#\}` without `re.DOTALL`) is single-line only. Fix: convert all 3 to `{% comment %} ... {% endcomment %}` blocks (Django's documented multi-line comment syntax). Comment text content preserved verbatim. Spec confidence 100% — definitive root cause confirmed in prior CC session's investigation (`docs/REPORT_171_INVESTIGATION.md` Section 3 + 5.1, untracked). Commit `410563c`. Agents @frontend-developer 10/10, @code-reviewer 9.5, @accessibility-expert (sub) 9.5. Avg 9.67/10. 1396 tests (template-syntax change only — no functional impact on test suite). |
| Session 171-INV | Apr 26, 2026 (untracked) | Diagnostic-only investigation pass. Reproduced + statically traced 170-B Regressions A (multi-line `{# #}` comment leak — DEFINITIVE root cause), B (modal not appearing during publish — full pipeline traced as structurally intact), C (chip not rendering on Grok content_policy failure — full pipeline traced as structurally intact). Produced 637-line `docs/REPORT_171_INVESTIGATION.md` (untracked, per spec rule — Mateo uploaded to Claude.ai for next-session multispec drafting). Section 5 hypothesis ranking drove the 171-A/B/C/D cluster shape: 171-A as definitive fix; B/C verifications deferred to post-deploy Memory-Rule-#14 checklist (regressions likely B1/C1 cosmetic-conflation or B2/C3 cached-bundle). Browser-interactive sections (1.3 / 2.3 evidence capture) flagged as Mateo TODO since CC has no browser-control tooling. No code edits, no commits, no agent reviews — investigation deliverable IS the report. Pattern-of-record for "investigation-first → batched-fix → post-deploy verification" cluster shape (Memory Rule #15). |
| Session 169-D | Apr 25, 2026 | Comprehensive 169-cluster docs catch-up. Closes 9 documentation gaps that emerged from 169-A/B/C but were not absorbed into the cluster's session entries: (1) new `#### Generator Slug Resolution Helper` H3 in Bulk AI Image Generator section explaining the `_resolve_ai_generator_slug` helper architecture, `/prompts/other/` rationale as defensive infrastructure for silent-fallback path, sequential vs concurrent path coverage, and operator drift signal; (2) `Active memory rules (9 of 30)` → `(13 of 30)` plus 4 new rule entries (#10 read current files, #11 Cloudinary video preload observation, #12 tasks.py postmortem reference, #13 silent-fallback observability) plus token-cost math update from 9 rules to 13; (3) 4 new Deferred P3 rows (`EndToEndPublishFlowTests` fixture gap caught by @test-automator in 169-C, PFS broader stale-counts audit, `@technical-writer` substitution formalization, real SEO copy for 7 `AI_GENERATORS` model entries); (4) 169-C row placeholders `Commit pending`/`Agent avg pending` filled with actual values; (5) CC_SPEC_TEMPLATE Critical Reminder #10 (Silent-Fallback Observability) added with 162-E and 169-B as evidence; (6) CC_SPEC_TEMPLATE new "Agent Substitution Convention" subsection codifying 13+ consecutive `@technical-writer → general-purpose + persona` substitution; (7) PFS top-line counts: Last Updated April 24 → April 25, Tests 1364 → 1386, Migrations 88 → 90, Test Files 28 → 29; (8) `CLAUDE_CHANGELOG.md` 168-A entry em-dash individual agent scores → real per-agent scores from `docs/REPORT_168_A_REFACTORING_AUDIT.md`; (9) version footer 4.67 → 4.68. Commit `a6e3140`. Agent avg 8.95/10. 1386 tests (no change). |
| Session 169-C | Apr 25, 2026 | Cleanup pass closing 169-B P2/P3 follow-ups + working-tree hygiene + 169-cluster docs catch-up. (1) `RegexValidator(GENERATOR_SLUG_REGEX)` added to `DeletedPrompt.ai_generator` (latent risk closed — 169-B added the validator to `Prompt.ai_generator` and `BulkGenerationJob.generator_category` but missed the sibling field). Migration 0088 schema-only — no `RunPython`, no data migration. (2) `AI_GENERATORS['other']` stub entry added so `/prompts/other/` serves a content-thin landing page rather than 404 when the helper's silent-fallback path fires; 169-B's `logger.warning` remains as the operator-side drift signal. (3) `PublishTaskTests.setUp` gained a `GeneratorModel` fixture + new `test_publish_sets_ai_generator_from_registry` test asserting the concurrent `publish_prompt_pages_from_job` path resolves correctly through the helper (mirrors 169-B's `ContentGenerationAlignmentTests` coverage of the sequential path). (4) Working-tree hygiene: 12 stale `CC_SPEC_*.md` files removed (7 staged-deleted + 3 already-gone + 2 untracked drafts). (5) Docs catch-up: 3 new `CLAUDE_CHANGELOG.md` entries + 3 new "Recently Completed" rows + version bump 4.66 → 4.67 + April 25 date sync. PROJECT_FILE_STRUCTURE.md NOT modified — structural additions are at granularities PFS doesn't enumerate. **Real SEO copy for the 7 169-B model entries explicitly deferred** (needs Mateo's marketing input). Commit `d9fcda7`. Agent avg 9.1/10. 1386 tests (+1 PublishTaskTests addition). |
| Session 169-B | Apr 25, 2026 | Generator slug permanent fix. P0 production 500 on prompt detail pages caused by 4 hardcoded `ai_generator='gpt-image-1.5'` literals at `tasks.py:3387, 3424, 3636, 3693` mis-tagging Grok prompts. Six categories of change: `_resolve_ai_generator_slug` helper from `GeneratorModel` registry (with `logger.warning` for unknown providers), `RegexValidator(r'^[a-z0-9][a-z0-9-]*$\|^$')` on `Prompt.ai_generator` and `BulkGenerationJob.generator_category` (`model_name` exempt for Replicate vendor strings), bidirectional migration 0087 retagging 7 mis-tagged Grok prompts to `'grok-imagine'`, taxonomy alignment across `AI_GENERATOR_CHOICES`/`AI_GENERATORS`/`GeneratorModel.slug`, defensive `None` return in `get_generator_url_slug` + template `{% if %}{% else %}` guard, 21-test regression suite enforcing canonical rule. Agents @code-reviewer 9.3, @architect-review 8.3, @test-automator 9.1, @backend-security-coder 9.0. Avg 8.925/10. Commit `a37d2d8`. 1385 tests. |
| Session 169-A | Apr 25, 2026 | Generator slug diagnostic + permanent-fix plan. Read-only investigation of production 500 on prompt detail pages — confirmed 3 bugs (Bug C P0: 4 hardcoded literals causing Grok mis-tagging; Bug A P2: dotted defaults from migration 0080; Bug B P1: three identifier taxonomies disagree). Scope: 7 of 64 prompts (10.9%) — trivial data migration. Section 9 prescribes canonical rule `^[a-z0-9][a-z0-9-]*$` with defense at validator + choice + dict + URL + helper + template + test layers. Recommended sequence: 169-B (consolidated fix), 169-D deferred. Zero code changes. Zero production DB writes. Agents @code-reviewer 9.0, @architect-review 9.0. Avg 9.0/10. Commit `2106eb9`. 1364 tests. |
| Session 168-E | Apr 24, 2026 | tasks.py refactor abandoned. 168-E-prep committed (`aa13ed7`, agent avg 9.75/10) — produced comprehensive import-graph + 41-name shim contract + Django-Q registration map. 168-E-A attempted Phase 1 extraction of 4 low-risk submodules; passed all acceptance gates (1,364 tests OK, 4-agent avg 9.625/10) but required inlining `b2_storage` back into `__init__.py` because `@patch` mocks fail to propagate across submodule boundaries — net 4% file-size reduction insufficient to justify shipping. Reverted local working tree, no commit on origin. tasks.py remains at 3,822 lines. **Full architectural analysis + future-attempt thresholds in `docs/POSTMORTEM_168_E_TASKS_SPLIT.md`.** Session 168-A audit's #2 ranked refactor closes as Won't Fix until threshold conditions met. |
| Session 168-F | Apr 23, 2026 | Fourth code refactor from 168-A audit. Split 2,459-line `prompts/admin.py` into `prompts/admin/` package with 12 submodules (forms, inlines, 8 domain admins, custom views, orchestration `__init__.py`). Module-level side effects preserved in correct order: Tag unregister, User unregister, index_template. Backward-compat re-exports for PromptAdmin + trash_dashboard — zero consumer-file changes. `.flake8` gained `*/admin/*.py` per-file-ignore line mirroring the pre-existing `*/admin.py` rule (same codes silenced in the monolithic file). Commit `16a95cf`. Agent avg 9.30/10. 1364 tests (identical to pre-split, 12 skipped preserved). |
| Session 168-D | Apr 22, 2026 | Third code refactor from 168-A audit. Split 3,517-line `prompts/models.py` into `prompts/models/` package — 9 submodules (8 domain + 1 constants) with 34-name re-export shim preserving backward compatibility. `delete_cloudinary_assets` signal relocated from models.py to signals.py with string-reference sender. `makemigrations --dry-run` → "No changes detected" (no schema drift). Commit `56cad16`. Agent avg 9.475/10 (@code-reviewer 9.2, @architect-review 9.2, @test-automator 10.0, @backend-security-coder 9.5). 1364 tests (exact match pre/post, 12 skipped preserved). |
| Session 168-D-prep | Apr 21, 2026 | Read-only analysis producing the concrete evidence 168-D needed to design the models.py split correctly. Catalogued all 28 top-level classes, 53+ relationships, 10 @receiver handlers across 4 signal files (including 2 previously unknown to Claude.ai: notification_signals.py and social_signals.py), ~110 external import sites, 2 in-function lazy imports inside models.py. Proposed 8-domain grouping verified against evidence. 168-D blockers: 1 HIGH + 4 MEDIUM + 7 LOW + 2 UNKNOWN with mitigation outlines. Plus absorbed ~10-line CLAUDE.md addition documenting the three CSS subdirectories (`partials/`, `components/`, `pages/`). First spec to apply memory rule #10 (request current files before drafting). Commit `a905de3`. Agent avg 9.1/10. |
| Session 168-C | Apr 21, 2026 | First code refactor from 168-A audit. Split 4,479-line `static/css/style.css` into a 17-line `@import` index + 5 focused partial files under `static/css/partials/`. Byte-level preservation verified (concatenated partial bodies diff byte-identical against pre-split style.css, 4,479 = 4,479 lines, diff exit 0). Pre-commit `end-of-file-fixer` hook stripped 2 trailing blank lines — zero CSS semantic impact (trailing whitespace irrelevant in parsing). Commit `213f604`. Agent avg 8.87/10 (@code-reviewer 9.5, @frontend-developer 9.0, @architect-review 8.1). |
| Session 168-B-discovery | Apr 21, 2026 | Docs-only, additive. Closes the onboarding gap introduced by 168-B. Four additive edits: archive `## 🔗 Related Documents` table row + Quick Start Checklist item #4 ("Archives exist but are not usually required") + CLAUDE_CHANGELOG top banner ("Looking for Sessions ≤ 99?") + PFS `archive/` entries. Plus absorbed PFS line 1196 inline relocation comment preserving historical "Files Created" semantics. Commit `e554fa6`. Agent avg 9.05/10. |
| Session 168-B | Apr 21, 2026 | Docs archive pass. Reduced active CLAUDE_CHANGELOG.md from 4,704 → 2,839 lines (~40%) by moving Sessions 13–99 (37 entries) to `archive/changelog-sessions-13-99.md` (1,889 lines). `PHASE_N4_UPLOAD_FLOW_REPORT.md` moved to `archive/` via `git mv` (history preserved). `BULK_IMAGE_GENERATOR_PLAN.md` status header corrected from "Planning Complete, Ready for Implementation" to "✅ SHIPPED". Byte-identity verified: Sessions 99, 50, and 13 match pre-archive hash-for-hash. Commit `b45ecdd`. Agent avg 8.95/10. |
| Session 168-A | Apr 21, 2026 | Read-only analysis. Full repository refactoring audit. Catalogued top 10 refactor opportunities across Python + CSS + HTML + JS tree: 133,642 total Python LOC, 68% in 12 files. Top 5 ranked for subsequent specs: (1) style.css 4,479 lines, (2) tasks.py 3,822, (3) models.py 3,517, (4) admin.py 2,459, (5) docs archive pass. Proposed sequence 168-B through 168-K. Commit `5b7b26d`. Agent avg 8.80/10. |
| Session 167-B | Apr 20, 2026 | Docs-only. Four polish edits to the Claude Memory System H2 section added by 167-A: added S6 as 13th deferred row; corrected `_sanitise_error_message` location to `bulk_generation.py:537` (spec had 467 — stale; CC verified actual); added Rule #1 italic note explaining intentional asymmetry; reordered three-criteria framework to precede Deferred table. Plus absorbed "framework below" → "above" directional fix. Commit `606f3c6`. Agent avg 8.95/10. |
| Session 167-A | Apr 20, 2026 | New `## 🧠 Claude Memory System & Process Safeguards` H2 section added to CLAUDE.md (~264 lines at line 2634). Documents 9 then-active memory rules with rationale and examples, 12 deferred candidates, 3-criteria evaluation framework (decision-meaningful / context-bound-vs-session / ROI), token cost ROI, related safeguards. Makes process discipline visible. Commit `a2843fa`. Agent avg 8.80/10. Found 2 spec errors during execution (12/13 count, `_sanitise_error_message` location) — addressed in 167-B. |
| Session 166 | Apr 20, 2026 | Docs-only. 11 catch-up items across CLAUDE.md, CLAUDE_CHANGELOG.md, and PROJECT_FILE_STRUCTURE.md: 165-B hash fills, Sessions 164+165 rows added, version bump 4.54 → 4.56, Phase REP dashboard updates, Session 161 correction note, django_summernote drift documentation, Session 163 condensation, 2026-04-18 credentials rotation note, profanity policy documentation, env.py safety gate added to Quick Start Checklist as item 4. Commit `82a8541`. Agent avg 9.07/10. |
| Session 165 | Apr 21, 2026 | Deployment safety hardening (two-spec session). 165-A: Procfile `release: python manage.py migrate --noinput` added — future deploys auto-apply migrations before web dynos serve traffic. Fail-closed semantics. Addresses 2026-04-20 near-miss (12min of 500s post-v758 because Procfile had no release phase). Commit `4d874d4`. 165-B: Migration 0086 aligns `UserProfile.avatar_url` migration state with current model definition — help_text-only drift surfaced by release-phase activation. SQL no-op verified via `sqlmigrate`. Commit `a457da2`. Agent avg 9.18 (165-A), 9.23 (165-B). 1364 tests. |
| Session 164 | Apr 20, 2026 | Monetization strategy restructure. 3-tier launch (Free $0, Pro $14/mo launch / $19 regular, Studio $39/mo launch / $49 regular) — supersedes Session 154's 4-tier framework. Launch pricing scarcity: first 200 annual OR 6 months whichever first. 100:1 credit system (internal, never exposed to users); 10-model lineup with per-model credit costs; top-up packs 200/$3, 1000/$12, 3500/$35. Discovery caps, anonymous browsing wall (100 views), welcome email sequence Day 1/3/7/14/28, Stripe metadata tracking. ~860 lines added to CLAUDE.md across 4 new H2 sections. Docs-only. Agent avg 9.05. |
| Session 163 | Apr 20, 2026 | Avatar pipeline rebuild (Phase F1 complete). Migration 0085: `CloudinaryField avatar` dropped, `b2_avatar_url` renamed to `avatar_url`, new `avatar_source` CharField (163-B). B2 direct upload pipeline: `b2_presign_service` extended to avatars, new `avatar_upload_service.py`, new endpoints `/api/upload/avatar/presign/` + `complete/`, new `avatar-upload.js`, `edit_profile.html` rewritten (163-C). Social-login plumbing: allauth Google provider config, `OpenSocialAccountAdapter`, `social_avatar_capture.py` (SSRF-guarded), `social_signals.py`, PyJWT dep (163-D). "Sync from provider" button with shared rate-limit bucket (163-E). **2026-04-19 production incident:** v1 163-B applied migration to production via `env.py` DATABASE_URL — ~30min outage, 0 data loss; env.py neutralised + v2 spec redesign with safety gate + no-migrate-by-CC rule + three-phase migration handoff (full detail in CLAUDE_CHANGELOG Session 163). 1364 tests. |
| Session 162 | Apr 19, 2026 | Cloudinary migration queryset filter fix — SQL `IN (NULL)` returns UNKNOWN, so `.filter(b2_*_url__in=('', None))` silently missed all legacy NULL rows; replaced with `Q(field='') \| Q(field__isnull=True)` across image/video/avatar branches. Dry-run now identifies 36 prompt images + 14 videos (162-A). Six avatar templates now prefer `b2_avatar_url` over Cloudinary `avatar.url` via three-branch B2-first pattern; `edit_profile.html` reserved for Session 164 F2 pending upload pipeline switch in 163 F1 (162-B). `vision_moderation.py` video-fallback path + three `fix_cloudinary_urls` branches moved from `str(CloudinaryField)` to explicit `.public_id` extraction — latent `str(None) == 'None'` bug fixed; investigation showed the 161-A claim that `str(CloudinaryResource)` returns object repr was wrong, current SDK's `__str__` returns `self.public_id` (162-C). xAI primary SDK path billing exhaustion now returns `error_type='quota'` (was `'billing'` — no handler in tasks.py, fell into retry loop). Matches 161-F httpx-path fix, static error message (162-D). `except Exception:` narrowed to `(ValueError, ImportError, AttributeError, KeyError)` around provider-registry cost lookup with `logger.warning`; fallback behavior unchanged, observability added (162-E). CC_SPEC_TEMPLATE v2.7 codifies three retrospective rules: Queryset Integration Test Rule (no SimpleNamespace mocks), Cross-Spec Bug Absorption Policy (absorb <5-line fixes, don't defer), Stale Narrative Text Grep Rule (Step 0 check before writing code) (162-H). 1321 tests. |
| Session 161 | Apr 18, 2026 | Cloudinary migration command bugs fixed: B2 credential check now uses `B2_ACCESS_KEY_ID`/`B2_SECRET_ACCESS_KEY` (actual Django setting names), CloudinaryResource public_id extraction via `getattr(..., "public_id", "") or ""` — dry-run now correctly identifies ~36 records (161-A). **Correction (Session 162-C investigation):** the original 161-A report claimed the pre-fix code fell back to `str(CloudinaryResource)` which returned object repr; direct SDK test shows `str(CloudinaryResource)` returns `self.public_id` in the current version. The real latent bug was `str(None) == 'None'` producing malformed URLs when the field was NULL — the `.public_id` pattern still fixes that and is preferred for SDK-version defense. Autosave: `.bg-vision-direction-input` added to input listener so typing into AI Direction triggers save; master Reset button now calls `I.clearDraft()` to remove `pf_bg_draft` from localStorage; `clearSavedPrompts()` cancels pending debounce timer (TOCTOU fix) (161-B). "Reset to master" (per-box) now preserves AI Direction checkbox state, row visibility, and textarea text — AI Direction is user content, not a setting (161-C). Results page pricing: view uses stored `job.actual_total_images` and Decimal `job.estimated_cost` (accurate to per-prompt count overrides) instead of master-only recalculation; Decimal preserved end-to-end for precision (161-D). New `UserProfile.b2_avatar_url` URLField + migration 0084; `migrate_cloudinary_to_b2` extended with `_migrate_avatar()` and `--model userprofile` choice (161-E). Grok httpx-direct edits path: 400 with 'billing' keyword returns `error_type='quota'` (stops job); `httpx.TransportError` caught and returns `error_type='server_error'` for retry (161-F). 1286 tests. |
| Session 160 | Apr 18, 2026 | Profanity error UX: triggered word bold/italic + clickable "Prompt N" link built via DOM API (no innerHTML); empty/duplicate errors also get the link. Quality section restored to disabled/greyed (not hidden) with "High" locked for non-quality models; two-column grid layout restored (160-B). Per-prompt cost fix: sticky-bar total now uses per-box `totalCost` accumulator for all models (previously non-BYOK recomputed from master quality, ignoring per-box overrides); console.warn for unmapped models (160-C). Full draft autosave: single `pf_bg_draft` JSON blob (version 1) captures ALL master settings + per-prompt box content + toggles + overrides; replaces 4 legacy keys via one-shot migration; draft persists after generation, cleared only by Clear All; schema maps cleanly to future `PromptDraft` server model (160-D). Pricing accuracy: `floatformat:"-3"` on results page + `parseFloat(x.toFixed(3)).toString()` in JS — $0.067 no longer rounds to $0.07, $0.003 no longer to $0.00 (160-E). Cloudinary → B2 migration command: `migrate_cloudinary_to_b2` with `--dry-run`, `--limit`, idempotency, fail-fast credential check, 50MB streaming size cap, `res.cloudinary.com` hostname allow-list (160-F). 1278 tests. |
| Session 159 | Apr 2026 | Profanity filter shows triggered words. Per-prompt boxes: NB2 1K/2K/4K labels, quality hidden for non-quality models, results page actual_cost, grid layout fix. Autosave: pageshow bfcache handler, aspect ratio restore. NB2 progress bar: provider-aware CSS durations (was stalling at ~85%). Cloudinary removal blocked by CloudinaryField model fields — unused import removed, full removal needs migration spec. 1270 tests. |
| Session 158 | Apr 17, 2026 | Opacity removed from disabled groups, per-prompt cost model-aware (NB2 tier costs per-row), autosave master header settings to localStorage (pf_ namespace). 1268 tests. |
| Session 157 | Apr 17, 2026 | NB2 quality labels 1K/2K/4K + tier-aware sticky bar cost, results page uses provider.get_cost_per_image() (single source of truth), upload zone hover suppressed when disabled, NB2 progress bar stall fixed (counts generating+completed). 1268 tests. |
| Session 156 | Apr 16, 2026 | Phase REP production readiness: Grok ref image httpx fix (SDK multipart hang → direct httpx POST), cost display audit + fix (all 6 models corrected, provider-aware cost in tasks.py), FLUX 2 Pro added (input_images array, 5 credits), Nano Banana 2 resolution tiers (1K/2K/4K with per-tier costs), cursor label comment. 1268 tests. |
| Session 155 | Apr 16, 2026 | Phase REP P1 blockers resolved: cursor:not-allowed on disabled groups, xAI NSFW 8-keyword detection, Grok ref image via /v1/images/edits, Nano Banana 2 ref image via image_input array, footer white text, P2/P3 cleanup. 1254 tests. |
| Session 154 | Apr 2026 | Phase REP: Replicate/xAI providers (Flux family, Grok Imagine, Nano Banana 2). GeneratorModel DB. 4-tier credit system. BYOK UX redesign. JS init order fixes. CSS skin. xAI aspect_ratio via extra_body. Provider-specific cost display. 1245 tests. |
| Session 153 | Apr 11–12, 2026 | GPT-Image-1.5 upgrade (153-A, migration 0080 — both `images.edit()` and `images.generate()` paths, 7 files + metadata + 2 new choice tests). IMAGE_COST_MAP updated to GPT-Image-1.5 pricing (153-C, 20% reduction across 10 files + 27 test assertions via Option B regression fix). Billing hard limit shows actionable error (153-D, new `BadRequestError` branch). Full billing chain end-to-end: `_sanitise_error_message` emits `'Billing limit reached'`, Q-filter catches billing, JS reasonMap entry added, `'Quota exceeded'` no longer says "contact admin" for BYOK users (153-E, 4 new tests). Per-image progress bar survives page refresh via `generating_started_at` timestamp + negative CSS `animation-delay` (153-F, migration 0081, `isFirstRenderPass` flag removed, 2 new tests). Input page `I.COST_MAP` sticky-bar pricing sync with Python constants (153-F caught in Step 1 grep). 1221 tests. |
| Session 152 | Apr 11, 2026 | Vision `detail: 'low'`→`'high'` (spatial accuracy). Direction decoupled from Vision (two-step: describe then edit). Progress bar counts generating+completed, excludes failed. Vision composition: frame-position, depth, crowd, anti-bokeh. 1213 tests. |
| Session 151 | Apr 8–10, 2026 | Vision empty prompt validation fix. Reset→header, AI Direction→above Source/Credit. Vision text override fix (was using placeholder). Diff suppressed for Vision placeholders. "Reset to master" label. Vision prompt: "RECREATE not reinterpret", spatial accuracy. Prompt logging (300 chars). Two-layer placeholder safety (`in` not `startswith`). `data-completed-count` live DB. 1213 tests. |
| Session 150 | Mar 31, 2026 | Bug fixes (Vision box count, progress bar init, API key scroll+shake). CSS tooltip system. UI labels cleaned, tier ~ prefix, stronger tier warning. Vision prompt quality (no sentence limit, visible watermark ignore, max_tokens 200→500). AI Direction for ALL boxes (text prompt editing via GPT-4o-mini). Diff display on results page (LCS word diff, strikethrough/highlight). Migration 0079 (original_prompt_text). Business model section added. 1213 tests. |
| Session 149 | Mar 31, 2026 | Feature 2: "Prompt from Image" per-prompt dropdown + direction textarea + GPT-4o-mini Vision backend (detail:high since Session 152, base64). Vision runs before translate/watermark. Autosave extended for Vision state. "Remove Watermarks (Beta)" toggle in Column 4 (ON by default). Feature 2B (master mode) planned. 1213 tests. |
| Session 148 | Mar 30, 2026 | OPENAI_API_KEY wired to settings (fixes 401 on prepare-prompts). Translation toggle in Column 4 (ON by default, skip translation when OFF). Tier error scrolls to tier section + shakes panel. Prepare-prompts rate limited (20/hr). Error banner auto-dismiss 5s→8s, suppressed for reduced-motion. 1213 tests. |
| Session 147 | Mar 30, 2026 | Fixed visible template comment in tier section, tier error now uses prominent bottom-bar banner. New "Prepare Prompts" pipeline: one GPT-4o-mini call translates non-English prompts + strips watermarks before generation. Non-blocking fallback. Features 1 (Translate) and 3 (Watermark Removal) complete. 1213 tests. |
| Session 146 | Mar 29, 2026 | Global delay floor bug fixed (OPENAI_INTER_BATCH_DELAY deprecated), cost estimate now size-aware (portrait/landscape prices correct), Django-Q timeout 120→7200s + max_attempts 1 (high-quality jobs no longer killed), "Done in Xs" timer removed (server-side Duration only), conditional tier UX (auto-detect for Tier 2+, Tier 1 zero friction). 1213 tests. |
| Session 145 | Mar 29, 2026 | Stale 0.034→0.042 billing path fix in `_apply_generation_result()`, proxy `cache.incr()` ValueError guard + `_HttpResponse` alias removed, `openai_tier` field on `BulkGenerationJob` (migration 0078), `_TIER_RATE_PARAMS` per-job rate limiting in `_run_generation_loop()`, tier 1–5 dropdown on bulk gen input page, global settings now ceilings, D2 confirmed already built, CLAUDE.md D4 architecture + Replicate plans. 1213 tests. |
| Session 144 | Mar 28, 2026 | PASTE-DELETE `.closest()` fix, stale 0.034→0.042 cost fallback, proxy `user.pk` logging + 60 req/min rate limit, `.finally()` removed, dead `urlValidateRef` removed, `.container` CSS moved, `ref_file.name` Content-Type sniff, `deleteBox` `.catch` warns, `OPENAI_INTER_BATCH_DELAY` hoisted, quota capitalisation fixed. 1213 tests. |
| Session 143 bulk-gen | Mar 26, 2026 | JS split (1685→725 lines + 2 modules), D1 pending sweep, D3 inter-batch delay, QUOTA-1 error distinction, pricing correction, migration 0077. 1209 tests. |
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

> **Older entries archived to `CLAUDE_ARCHIVE_COMPLETED.md`** (Session 153-M).
> For the full session history, see `CLAUDE_CHANGELOG.md`.

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

*Last updated: Session 143 (March 26, 2026). `bulk-generator.js` split from
1,547→725 lines. Re-run the file size audit whenever a file is significantly
extended or split.*

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

**Status:** Feature-complete for staff use. Full 6E series complete (per-prompt size, quality, image count overrides + hardening + cleanup). 5 JS input modules + 5 JS job modules. 1221 tests. D1 pending sweep + D3 rate limit delay deployed. D4 per-job tier rate limiting deployed (Session 145). QUOTA-1 error distinction live. D2 generation retry already implemented (Phase 5C `_run_generation_with_retry()`). Session 153: GPT-Image-1.5 upgrade (migration 0080), pricing updated to GPT-Image-1.5 rates, billing hard limit error path end-to-end, per-image progress bar survives page refresh (migration 0081 — `generating_started_at`). Next: V2 launch. V2 scope: BYOK for premium users, Replicate models (Nano Banana 2, Flux), archive staging page at `/profile/<username>/ai-generations/`.

#### Planned: Replicate Providers (Session 146+)

Two models planned via Replicate (platform-paid — your Replicate key, users
pay you via subscription, no BYOK required):

- **Nano Banana 2** (`replicate.com/google/nano-banana-2`) — Google's image
  model via Replicate. 1.5M+ runs, actively maintained. Platform-paid works
  here because Replicate bills per-run to your account, not per-user-key.
- **Flux** (Replicate) — via same platform-paid model.

**BYOK field behaviour:**
- OpenAI selected → BYOK key input shown (user brings their key)
- Replicate model selected → BYOK field hidden entirely (server-side key)

**Implementation:** One `replicate_provider.py` handles both models (different
model IDs, same Replicate SDK). Add `register_provider('nano-banana-2', ...)` and
`register_provider('flux', ...)` to `registry.py` `_register_defaults()`.
`REPLICATE_API_TOKEN` stored as Heroku config var.

**Note:** GPT-Image-1 is also listed on Replicate but is BYOK-only there —
it routes charges to the user's OpenAI key. No advantage over calling OpenAI
directly. Do not add this via Replicate.

**Resolved (Session 122):** Cancel-path `G.totalImages` staleness ✅, `bulk-generator-ui.js` at 766/780 lines ✅ (now 338 lines), N4h rename not triggering ✅.

**Open items as of Session 127 (post-audit):**

| Item | Notes |
|------|-------|
| **Terminal-state ARIA branches** | ✅ CLOSED — comment added to `bulk-generator-polling.js` (Session 127). Non-actionable by design. |
| **Admin path rename task** | ✅ FIXED — `async_task` queued from `save_model` in `admin.py` (Session 127). |
| **Video B2 rename** | ✅ CLOSED — audit confirmed `b2_video_url` already handled in `tasks.py` lines 1936–1944. Stale entry. |
| **Debug print() statements** | ✅ FIXED — 13 print() statements removed from `upload_views.py` (Session 127). |

#### Generator Slug Resolution Helper (Sessions 169-A/B/C)

Every prompt published via the bulk AI image generator —
whether through the **sequential** `create_prompt_pages_from_job`
path or the **concurrent** `publish_prompt_pages_from_job`
path — sets `Prompt.ai_generator` via the
`_resolve_ai_generator_slug(job)` helper in `prompts/tasks.py`.

**The helper:**

1. Reads the `BulkGenerationJob`'s `provider` + `model_name`
   fields
2. Looks up the matching `GeneratorModel` registry row
3. Returns that row's `slug` value (e.g., `'gpt-image-1-5'`,
   `'grok-imagine'`, `'flux-pro-1-1'`)
4. **On no match** — provider+model combination missing from
   `GeneratorModel` — returns `'other'` AND emits
   `logger.warning` with structured fields (`provider`,
   `model_name`, `job_id`)

This replaces the previous pattern of 4 hardcoded
`ai_generator='gpt-image-1.5'` literals at `tasks.py:3387,
3424, 3636, 3693` (Bug C in 169-A's diagnostic) which caused
every prompt published from any provider — including Grok —
to be tagged GPT-Image. The fix shipped in 169-B (commit
`a37d2d8`).

**Why `/prompts/other/` exists:**

The `'other'` fallback path is **defensive infrastructure**
for the case where a new `GeneratorModel` row is added to
the registry but its `slug` doesn't match any current
`AI_GENERATORS` dict entry — e.g., a future provider or a
typo. Without this fallback:
- The publish would `IntegrityError` on the
  `RegexValidator(GENERATOR_SLUG_REGEX)` constraint added in
  169-B, OR
- The detail page URL `/prompts/<slug>/` would 404 because
  no listing page exists at `/prompts/other/`

The `AI_GENERATORS['other']` stub entry added in 169-C
ensures the listing page renders (content-thin landing page
rather than 404). Combined with the `logger.warning`, this
gives the system **defense-in-depth** plus an **operator-side
drift signal** — the warning fires whenever the helper
silently falls back, so drift is visible in logs even though
the publish succeeds.

**Test coverage of both paths:**

| Path | Test class | Spec |
|------|------------|------|
| Sequential (`create_prompt_pages_from_job`) | `ContentGenerationAlignmentTests` | 169-B |
| Concurrent (`publish_prompt_pages_from_job`) | `PublishTaskTests.test_publish_sets_ai_generator_from_registry` | 169-C |

Both paths must continue to resolve via the helper. Any
future bulk-generator change touching publish logic must
preserve this contract or re-test both classes.

**Operational note:**

If `/prompts/other/` ever shows actual content (a Grok image,
a Flux image, etc.), it means the fallback fired. Check
production logs for the `logger.warning` and either:
1. Add the missing `AI_GENERATORS` dict entry for the new
   provider+model combination, OR
2. Backfill the affected `Prompt.ai_generator` values via a
   data migration similar to migration 0087 (169-B's Grok
   retag pattern)

### Recommended Build Sequence — Remaining Safety Infrastructure

| Step | Item | Status |
|------|------|--------|
| 1 | `detect_b2_orphans` command (Section B prerequisite) | ✅ Complete (Session 123, commit 61edad1) |
| 2 | Bulk job deletion backend — Section A items 1–6 (soft-delete fields → JobReceipt → DeletionAuditLog → pre-deletion task → cleanup command → Scheduler entry) | 🔲 Planned |
| 3 | Bulk job deletion frontend UI — Section A item 7 | 🔲 Planned — do NOT start before Step 2 complete |
| 4 | Admin operational notifications — Section C (wraps Steps 1–3) | 🔲 Planned |

> ⚠️ Step 3 (frontend UI) must not be specced or built until Step 2 is fully committed and tested.
> The Section A build order in "Bulk Job Deletion — Pre-Build Reference" is mandatory — no skipping ahead.

### Deferred P2 Items

Substantive items that warrant their own spec but don't block any
in-flight work. Surfaced during 171–172 cluster development.

> **Closed since the table below was last updated:** the
> "Frontend wire-up of `model_identifier` in `/api/validate/`
> POST body" P2 deferred item from REPORT_173_B Section 5 was
> closed by **Session 173-E** (May 1, 2026). The item didn't
> have its own row in this table — it was tracked only in the
> 173-B report — but is acknowledged here for traceability per
> Memory Rule #16 (closure of prior-session deferred items
> should be visible at the top-line index, not just buried in
> per-session reports).

| Item | File / Surface | Notes |
|------|----------------|-------|
| Modal persistence on bulk publish refresh | `prompts/views/bulk_generator_views.py` + `static/js/bulk-generator-selection.js` + `static/js/bulk-generator-polling.js` + `static/js/bulk-generator-config.js` (initPage) | When user clicks Create Pages and refreshes the page (or leaves and comes back), the publish modal should restore until the user explicitly closes it. Backend has the data (polling payload exposes `published_count` and per-image `prompt_page_id`); frontend needs (a) localStorage tracking for "user has not yet dismissed publish modal for job X" with sentinel like `pf_publish_modal_dismissed=<job_id>`, (b) `initPage` restoration logic that opens the modal if state warrants. Note: Session 172-C resolved the per-image overlay restoration but the modal-itself-persistence is a separate concern — the modal is a transient UI artifact controlled by selection.js, while the overlay is a per-card persistent indicator from gallery.js. Estimated 1 spec. Surfaced April 28, 2026 by Mateo, deferred from Session 172 cluster scope. |
| IMAGE_COST_MAP per-model restructure (Scenario B1) | `prompts/constants.py` `IMAGE_COST_MAP` + `get_image_cost(quality, size)` signature + all callers (~5-10 sites in `tasks.py`, `bulk_generator_views.py`) + `bulk-generator.js` `I.COST_MAP` mirror | Spec 171-C used Scenario B2 (mirrored gpt-image-1.5 pricing as placeholder for gpt-image-2). Web research subsequently confirmed gpt-image-2 pricing differs by >15% across all quality tiers ($0.006/$0.053/$0.211 vs gpt-image-1.5's $0.009/$0.034/$0.134) — high tier ~60% more expensive than gpt-image-1.5 for some sizes. Per Spec 171-C's own decision tree, this exceeds the 15% threshold for Scenario B1 (per-model cost map restructure). Restructure `IMAGE_COST_MAP` to be model-keyed (`{model: {quality: {size: price}}}`) and update `get_image_cost()` signature to accept a `model` parameter. Update all callers. Add gpt-image-2 prices. Will also be required when first PLATFORM-key (non-BYOK) OpenAI model ships. Surfaced April 28, 2026 by Mateo during cluster scoping discussion, deferred from Session 172. Estimated 1 spec. **Note:** also subsumes the existing P3 row "gpt-image-2 per-quality/size pricing audit" which becomes redundant once this P2 row is closed. |
| Reset Master Settings + Clear All Prompts UX | `static/js/bulk-generator-autosave.js` (not yet uploaded by Mateo) + `static/js/bulk-generator.js` (Reset Master button handler + Clear All Prompts handler) + per-box override reset propagation | When user clicks Reset Master Settings, existing prompt cards' overrides should reset to "Use master" (currently they retain their explicit value). When user clicks Clear All Prompts, same expectation. Plus: Reset Master should respect Nano Banana 2's 1K default (currently resetting sets master quality to "medium"/"2K" which is wrong for NB2 — Session 172-A established 1K as the NB2 master default). Requires `bulk-generator-autosave.js` analysis (file not yet uploaded by Mateo for static review) and per-box override reset propagation logic. Estimated 1 spec. Surfaced April 28, 2026 by Mateo, deferred from Session 172 due to missing autosave file. |
| Page-refresh state recovery during bulk publish | `prompts/views/bulk_generator_views.py` + `static/js/bulk-generator-selection.js` + `static/js/bulk-generator-polling.js` | When a user refreshes the bulk job results page mid-publish or after publish completes, the modal/toast UI is lost (modal closes; sticky toast disappears; published links list resets). Server holds the truth (`BulkGenerationJob.published_count`, per-image `prompt_page_id` + `prompt_page_url`). Frontend should reconstruct UI state from polling response on page load — re-derive `totalPublishTarget`, re-render published links list, re-show terminal modal at "Done!" state. Surfaced April 26, 2026 by Mateo during 171-INV browser-task discussion. Estimated 1 spec. **Note:** Session 172-C resolved the per-image published-badge restoration on page reload (the overlay use case). The remaining work for this row is the *modal* and *sticky toast* + *published links list* which are session-state UI not per-card UI. Largely overlaps with the new "Modal persistence on bulk publish refresh" P2 row above — should be reconciled when either is specced. |
| Replicate concurrency policy | `prompts/tasks.py` `_run_generation_loop` `_TIER_RATE_PARAMS` + `prompts/services/image_providers/replicate_provider.py` | `BULK_GEN_MAX_CONCURRENT=1` forces sequential generation across ALL providers. Replicate handles parallelism gracefully (per-call billing, no shared rate limit ceiling per user). Per-provider concurrency policy (Replicate=4-8, OpenAI=tier-bound via existing `_TIER_RATE_PARAMS`, xAI=its own limit) would substantially reduce wall-clock time on bulk Flux/Nano Banana 2 jobs. Surfaced April 26, 2026 by Mateo. Requires investigation + design + implementation. Estimated 2 specs. |

---

### Deferred P3 Items

Small items not worth individual specs — batch into cleanup passes periodically.

| Item | File | Notes |
|------|------|-------|
| Try-in URL text adjustment for future single-page generator | (TBD — likely `prompts/templates/prompts/prompt_detail.html` or wherever the future single-page generator's "Try in [model]" link lives) | Mateo noted the "Try in [model]" link text should adjust slightly when the project's single-page generator launches — wording should encourage users to try the prompt in PromptFinder's own generator first rather than (or in addition to) the model-owner's site. No code change yet; this is a placeholder for when the single-page generator ships. Surfaced April 28, 2026 by Mateo during 172 cluster scoping. |
| EndToEndPublishFlowTests `GeneratorModel` fixture gap | `prompts/tests/test_bulk_page_creation.py` | 169-C closed the parallel gap in `PublishTaskTests` (added `GeneratorModel` fixture in `setUp`) but `EndToEndPublishFlowTests` from Phase 7 has the same risk pattern — its `setUp` does not create a `GeneratorModel` row, so any future test relying on the `_resolve_ai_generator_slug` helper would fall through to `'other'` instead of the expected slug. Caught by @test-automator during 169-C review (8.5/10 score). Trivial fix — copy the fixture from `PublishTaskTests`. P3 because no current test in `EndToEndPublishFlowTests` exercises the resolution path; latent risk only. **Session 171-C extends the same risk to `gpt-image-2-byok`** — neither `PublishTaskTests.setUp` nor `EndToEndPublishFlowTests.setUp` creates a gpt-image-2-byok GeneratorModel fixture, so a future gpt-image-2 publish test would also fall through to `'other'`. Resolution: include a `gpt-image-2-byok` fixture in the broader test-fixture audit when this row is closed. |
| gpt-image-2 per-quality/size pricing audit + IMAGE_COST_MAP per-model restructure | `prompts/constants.py` `IMAGE_COST_MAP` + `get_image_cost(quality, size)` signature + all callers | Session 171-C added gpt-image-2 BYOK support but chose Option B2 (mirror gpt-image-1.5 prices as placeholder) because (a) gpt-image-2 is BYOK so OpenAI bills user directly — displayed cost is informational only; (b) precise per-quality/size pricing not yet published by OpenAI (token-based pricing only at $8/M input + $30/M output tokens). Per-image equivalents range $0.01-$0.02 (low) to $0.15-$0.22 (high) — high tier ~60% more expensive than gpt-image-1.5. When OpenAI publishes per-quality/size pricing, restructure `IMAGE_COST_MAP` to be model-keyed (`{model: {quality: {size: price}}}`) and update `get_image_cost()` signature to accept a `model` parameter (Option B1 from spec section 5). Update all callers (~5-10 sites in `tasks.py` + `bulk_generator_views.py`). Add gpt-image-2 prices. Will also be required when first PLATFORM-key (non-BYOK) OpenAI model ships. |
| PROJECT_FILE_STRUCTURE.md broader stale-counts audit | `PROJECT_FILE_STRUCTURE.md` | 169-D updated 4 top-line counts (Last Updated, Tests, Migrations, Test Files) but the file has additional stale entries inside per-session historical tree snapshots and inline LOC values. A comprehensive PFS audit pass would catch these but is out of scope for incremental docs catch-up specs. Defer until cumulative drift becomes large enough to justify a dedicated PFS audit spec. |
| Formalize `@technical-writer` substitution in agent registry | `CC_SPEC_TEMPLATE.md` (already partial via 169-D), agent registry config | 169-D added an "Agent Substitution Convention" subsection acknowledging the substitution as canonical. The deeper question — whether `general-purpose + persona` should be added as a first-class agent in the wshobson/agents registry, OR whether a custom `@technical-writer-personality` should be authored — remains open. 13+ consecutive sessions of substitution suggests yes; defer the decision until at least one session attempts a custom-agent author. |
| Real SEO copy for the 7 169-B `AI_GENERATORS` model entries | `prompts/constants.py` | 169-B added placeholder SEO copy for the 7 new model-specific entries (`gpt-image-1-5`, `grok-imagine`, `flux-pro-1-1`, `flux-1-1-pro-ultra`, `nano-banana-2`, `flux-pro-1-1-ultra`, `imagen-4`). Real marketing-quality copy needs Mateo's direct input — generated copy at the SEO-meaningful level requires brand voice judgment. Tracked since 169-B (April 25); defer until Phase SUB launch prep (when SEO content becomes a launch blocker). |
| tasks.py modular split (`prompts/tasks.py`, 3,822 lines) | `prompts/tasks.py` | Refactor attempted Session 168-E and abandoned — `@patch` mock semantics across submodule boundaries make naive extraction yield only ~4% file-size reduction. Future revisit gated by thresholds in `docs/POSTMORTEM_168_E_TASKS_SPLIT.md` Section 10. |
| Preload-warning observation on async stylesheet link | `prompts/templates/prompts/prompt_detail.html` (line 99) | `<link rel="preload" href="…prompt-detail.css" as="style" onload="this.onload=null;this.rel='stylesheet'">` can emit a Chrome DevTools "resource was preloaded using link preload but not used within a few seconds" warning on some page loads. After 168-C's `@import`-based `style.css`, the timing window widened because the browser now serially fetches 5 partials before the async stylesheet is consumed. Non-blocking (cosmetic console warning; no functional impact). Candidate fix: replace preload-then-swap-rel with direct `<link rel="stylesheet">`, or add explicit `media` attribute to gate application. Verify under Lighthouse before changing — the preload was added for LCP optimization in Session 68. |
| `prompt_list_views.py` growth monitor | `prompts/views/prompt_list_views.py` | 620 lines, `prompt_detail` is ~320 lines — watch for growth |
| ~~`__init__.py` imports through shim~~ | `prompts/views/__init__.py` | ✅ RESOLVED Session 138 — imports directly from domain modules |
| `int(content_length)` no try/except | `prompts/tasks.py` | Pre-existing in both download functions — safe but opaque error on malformed header |
| ~~`clearAllConfirm` paste state reset~~ | `static/js/bulk-generator.js` | ✅ RESOLVED Session 140 — full paste state reset added |
| ~~`B2_CUSTOM_DOMAIN` empty edge case~~ | `prompts/views/upload_api_views.py` | ✅ RESOLVED Session 140 — empty guard with 500 response |
| ~~`getMasterDimensions()` hardcoded fallback~~ | `static/js/bulk-generator.js` | ✅ RESOLVED Session 140 — reads first available button from DOM |
| ~~`lightbox-open-link:focus-visible`~~ | `static/css/pages/prompt-detail.css` | ✅ RESOLVED Session 140 — double-ring pattern added |
| ~~Hidden 16:9 button `aria-hidden`~~ | `prompts/templates/prompts/bulk_generator.html` | ✅ RESOLVED Session 140 — aria-hidden + tabindex=-1 |
| ~~`_upload_source_image_to_b2` docstring~~ | `prompts/tasks.py` | ✅ RESOLVED Session 140 — WebP conversion documented |
| ~~Space key `event.preventDefault()`~~ | `prompts/templates/prompts/prompt_detail.html` | ✅ RESOLVED Session 140 — preventDefault on source image wrap |
| ~~Single-box ✕ B2 delete~~ | `static/js/bulk-generator.js` | ✅ RESOLVED Session 142 — fires B2 delete before clearing URL field |
| ~~`X-Content-Type-Options` on download proxy~~ | `prompts/views/upload_api_views.py` | ✅ RESOLVED Session 142 — nosniff added to download proxy |
| ~~gallery.js lightbox close button~~ | `static/js/bulk-generator-gallery.js` | ✅ RESOLVED Session 142 — confirmed on overlay (141 fix verified) |
| ~~`[PASTE-DELETE]` ✕ button `.classList.contains()`~~ | `static/js/bulk-generator.js` | ✅ RESOLVED Session 144 — uses `.closest()` matching deleteBtn/resetBtn pattern |
| ~~Stale 0.034 fallback in cost estimate~~ | `prompts/views/bulk_generator_views.py` | ✅ RESOLVED Session 144 — updated to 0.042, consistent with IMAGE_COST_MAP |

### Session 175 — Policy Documentation Cluster (Planned)

**Status:** Planned. Begins after Session 174 (modal persistence +
IMAGE_COST_MAP restructure).

**Self-drafted policy posture confirmation (Mateo, April 30, 2026):**
Mateo accepts that policy documents (ToS, Privacy Policy, Content
Policy) will be self-drafted by Claude.ai with documented limitations
rather than lawyer-reviewed. Reasoning: tight budget, lawyer
back-and-forth too slow for launch timeline, self-drafted is "better
than 80% of indie SaaS apps" per Claude.ai's prior assessment. Plan
to revisit when revenue justifies legal review (estimated 6-12 months
post-launch).

**Documented limitations:**
- Liability limitation clauses have jurisdiction-specific magic-word
  requirements not reliably captured by self-drafted text
- GDPR Article 30 records and full Data Processing Agreements with
  subprocessors (OpenAI, Replicate, xAI, Backblaze, Cloudflare,
  Heroku) not included
- COPPA / state privacy law (CCPA/VCDPA) compliance verification
  not done
- Specific industry compliance (none currently identified) not vetted

**Mitigations in place:**
- Self-drafted ToS/Privacy is better than no policy at all for
  low-traffic, pre-revenue stage
- Casual disputes (DMCA notices, refund requests, account suspension)
  resolvable through self-drafted terms
- DMCA Agent registration ($6 at dmca.copyright.gov, mandatory before
  launch) provides federal safe harbor protection

**Cluster scope (~6 specs):**

- **175-A** Internal `docs/CONTENT_POLICY.md` — drives code, admin
  tooling, cost absorption rules, severity definitions, refund
  triggers, harassment escalation
- **175-B** Internal `docs/MODERATION_RUNBOOK.md` — operational SOPs
  for handling reports, DMCA process, repeat infringer policy +
  **DMCA Agent registration walkthrough as non-negotiable launch
  checklist item**
- **175-C** Public-facing `docs/CONTENT_GUIDELINES.md` (replaces the
  173-C placeholder at `/policies/content/`) +
  `docs/REFUND_POLICY.md`
- **175-D** `docs/TERMS_OF_SERVICE.md` (drafted from competitor
  patterns + PromptFinder facts; clearly documented as not
  lawyer-reviewed)
- **175-E** `docs/PRIVACY_POLICY.md` (same approach)
- **175-F** End-of-session docs

**Stage-gate before 175 begins:**

Mateo collects sample policy docs from comparable apps for Claude.ai
to use as drafting references:
- 5-7 ToS samples (Midjourney, OpenAI, Replicate, Stability,
  ImagineArt, Civitai, Leonardo.ai)
- 3-5 Privacy Policy samples (same)
- 3-5 Content Policy samples
- 2-3 DMCA pages
- Refund policies

Estimated time: 2-3 hours of clicking + saving. These get fed into
a `policy-drafting` Claude skill (outline below).

**Policy-drafting skill outline:**

The skill (to be created at `/.claude/skills/policy-drafting/SKILL.md`
or similar) should contain:

1. **Reference docs** — the competitor samples Mateo collects above
2. **PromptFinder-specific facts** — extracted from CLAUDE.md (data
   collection, subprocessors, jurisdiction, age policy, business
   model)
3. **Drafting checklists** — ToS (25-point), Privacy Policy
   (18-point), Content Policy (AI-platform specific), Refund Policy
   (decision tree)
4. **Jurisdiction notes** — US-based business, worldwide users,
   GDPR/CCPA considerations
5. **Standard clause library** — pre-written customizable boilerplate
   (limitation of liability, indemnification, dispute resolution,
   choice of law, termination, force majeure, severability, DMCA
   agent designation, repeat infringer, modifications,
   children/minors)
6. **Red flags / common mistakes** — patterns to avoid
7. **Self-audit questions** — post-drafting checks

**Cost absorption policy (drafted in 175-A, summarized here):**

Documents what PromptFinder absorbs vs charges back to users for
content-moderation rejections:

- **What we absorb:** First N (currently 3) content-policy rejections
  per user per day; all rejections from users with <M (currently 5)
  total rejections in account history (new users); rejections from
  prompts that PASSED our pre-flight (provider rejected something we
  didn't flag — that's our miss)
- **What we don't absorb / future enforcement:** Sustained-violation
  users (>3 rejections/day for >7 days) → soft-block via stricter
  pre-flight + admin queue; bulk batches with >50% pre-flight
  rejection rate → block batch entirely; repeat universal-block
  triggers → incident logged + admin notification + possible
  suspension

xAI charges $0.02 per content-moderation rejection. OpenAI/Google
can suspend API access for sustained violations. Pre-flight (Session
173-B) catches most before they hit the API.

**Content ownership framework (drafted in 175-D, summarized here):**

User-uploaded content (avatars, source images for Vision API):
- User represents and warrants ownership/license + no infringement
- User grants PromptFinder limited license to host/process for
  service delivery

AI-generated content (bulk generator output):
- PromptFinder assigns rights to user
- Output may not be copyrightable (AI-generated); may be
  similar/identical across users; resemblance to existing
  works/people remains user's responsibility regardless of Terms
  ownership
- PromptFinder reserves aggregated/anonymized usage rights for
  service improvement

**DMCA Agent registration:**

Non-negotiable line item before public launch. $6 one-time
registration at `dmca.copyright.gov/`. Without DMCA agent
designation, PromptFinder loses federal safe harbor protection —
losing safe harbor means direct copyright liability for any
infringing user uploads ($750-$30,000 statutory damages per work).

Required steps:
1. Register agent with US Copyright Office at
   `https://dmca.copyright.gov/` (15 minutes online)
2. List agent contact info on PromptFinder website (footer +
   Privacy Policy + dedicated DMCA page)
3. Document the takedown response process in
   `MODERATION_RUNBOOK.md` (175-B)
4. Document the repeat infringer policy in ToS and
   `MODERATION_RUNBOOK.md`

### 🚀 Planned New Features

> These features are scoped and discussed but not yet specced for implementation.
> Documented here so context is not lost between sessions.

#### Feature 1: Translate Prompts to English — ✅ COMPLETE (Session 147)

**Summary:** Before generation starts, send all non-English prompts to GPT-4o in a single batch call to translate them to English. Fires during the "Starting generation…" phase — invisible to the user.

**Benefits:** OpenAI's image models perform significantly better with English prompts. Users who copy prompts from non-English sources get better outputs without manual translation. Zero user friction — happens automatically.

**Implementation approach:** One GPT-4o call with all prompts batched. System prompt: detect language of each prompt, translate to English if not already English, return array of cleaned prompts in same order. Runs after validation, before `service.create_job()`. Estimated latency: 1-3 seconds added to "Starting…" phase.

**Pros:** High value, low cost (text is cheap), one API call, no UI changes.
**Cons:** Adds latency to generation start, GPT-4o translation is not perfect for highly technical or stylistic prompts.
**Risks:** Translated prompt may lose nuance from the original language. Mitigation: only translate if detected language is not English.
**Priority:** High — relatively simple, high impact.

#### Feature 2: Generate Prompt from Source Image (Vision API) — ✅ COMPLETE (Session 149)

**Summary:** A per-prompt "Prompt from Image" dropdown that uses GPT-4o-mini Vision to generate a concise image-generation prompt from the attached source image. The Vision-generated prompt replaces the text field content and is used for both generation and the result page display.

**UX behaviour:** "Prompt from Image" dropdown appears on the same row as IMAGES in each prompt box. When set to "Yes": text field disabled (strike-through on existing text, text preserved), a direction instructions textarea appears for AI guidance (max 500 chars), source image URL field becomes required. Character Description still applies. Vision API call fires per enabled prompt during "Preparing prompts…" phase, before translate/watermark.

**Vision API prompt strategy:** Instruct GPT-4o-mini Vision (detail:high) to describe subject, style, composition (frame-position, depth, crowd), lighting, technical quality. Covers 8 categories: subject, attire/appearance, setting/background, composition/framing, lighting, style/medium, mood/atmosphere, technical quality. No sentence limit. Base64-encode images before sending. Direction applied as separate GPT-4o-mini edit step (two-step architecture).

**Implementation approach:** `_generate_prompt_from_image()` helper in `bulk_generator_views.py` using GPT-4o-mini Vision API. Called per vision-enabled prompt during `api_prepare_prompts`, before translate/watermark batch. Falls back to original prompt text on any error. HTTPS URL validation + 10 MB size cap + no redirects for defense-in-depth. Front-end: dropdown per prompt box + direction textarea, autosave extension for Vision state.

**Pros:** Major differentiator, solves "I have an image but no prompt" problem, high accuracy with Vision API.
**Cons:** One Vision API call per enabled prompt (~$0.009–0.015 each at detail:high), adds latency per checked prompt, requires accessible source image URL.
**Risks:** Vision API may not always produce concise output — requires careful system prompt tuning. Source image must be HTTPS and accessible (validated by HTTPS scheme check + no-redirect policy).
**Priority:** High — genuine differentiator.

#### Feature 2B: Master "Prompt from Image" Mode (Planned — Future Session)

**Summary:** A master toggle in Column 4 of the master settings grid (alongside Visibility and Translate to English) that puts ALL prompt boxes into Vision mode simultaneously. When enabled:
- All prompt text fields are hidden (not just disabled — replaced by the direction instructions textarea as the primary input)
- The "Prompt from Image" per-box dropdown is hidden (redundant in master mode)
- A master direction instructions field appears in the master settings for global guidance that applies to all prompts
- Source image URL field in each box becomes required

**UX behaviour:** Toggle defaults OFF. When toggled ON, all boxes immediately enter Vision mode. Boxes that already have text in the prompt field: text is preserved but hidden. When toggled OFF: all boxes revert to normal mode with text restored.

**Implementation approach:** New `settingMasterVision` checkbox in Column 4. On change: iterate all `.bg-prompt-box` elements, toggle `.bg-vision-master-mode` class on each. CSS handles field visibility. Per-box Vision dropdown hidden via `.bg-vision-master-mode .bg-box-override-vision` selector.

**Dependency:** Feature 2 (per-prompt Vision) must be fully stable first.
**Priority:** Medium — powerful for users who want all-Vision workflows.
**Status:** Planned — do not spec until Feature 2 is confirmed stable in production.

#### Feature 3: Remove Watermark Text from Prompts — ✅ COMPLETE (Session 147)

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

#### localStorage ↔ Server-Side Draft Relationship (Session 160)

The Session 160-D full draft autosave (localStorage) is the
anonymous/pre-login foundation of the named draft system. The JSON
schema stored under `pf_bg_draft` was designed to be directly
serialisable to the `PromptDraft` model:

- `settings` dict → `settings_json` field
- `prompts` array → `prompts_json` field

When Feature 4 ships, logged-in users will have their localStorage
draft automatically offered for promotion to a named server-side
draft. Logged-out users continue to use localStorage only.

**Schema (pf_bg_draft) — version 1:**

```json
{
  "version": 1,
  "saved_at": "ISO timestamp",
  "settings": {
    "model", "quality", "aspect_ratio", "pixel_size",
    "images_per_prompt", "character_description",
    "visibility", "translate", "remove_watermark", "tier"
  },
  "prompts": [
    {
      "index", "text", "source_credit", "source_image_url",
      "vision_enabled", "vision_direction", "direction_checked",
      "quality_override", "size_override", "images_override"
    }
  ]
}
```

**Version strategy:** The loader accepts `version >= 1 &&
version <= DRAFT_SCHEMA_VERSION` so future v2 fields are additive
(no breaking migration). Restore code treats missing fields as
falsy.

**Migration coercion at promotion:** Boolean `settings.visibility`
→ `'public'`/`'private'` CharField on the server model (one-line
transformation, done at promotion time).

#### Draft Versioning — Tier Design Decision (Session 160)

Draft versioning (save history) is a premium tier differentiator:

| Tier | Named Drafts | Version History | Sharing |
|------|--------------|-----------------|---------|
| Free | 1 (overwrite only) | No | No |
| Creator | 5 named drafts | No | No |
| Pro | Unlimited | Yes (last 10 versions) | No |
| Studio | Unlimited | Yes (unlimited) | Yes (team) |

**Status:** Design decision confirmed. Do not spec until Phase SUB
(Stripe subscription tiers) ships. Tier names and limits subject to
change based on pricing strategy.

#### Combined "Prepare Prompts" Architecture — ✅ LIVE (Session 147)

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

- **Session 153 — JS cost maps can drift from Python constants.** `I.COST_MAP`
  in `bulk-generator.js` is a client-side copy of `IMAGE_COST_MAP` in
  `constants.py`. When 153-C updated the Python constant, the JS copy was
  missed — caught in a Step 0 grep during 153-F. Fix pending in 153-J:
  `get_image_cost()` helper + (future) template context injection so JS
  prices are generated from Python at render time.
- **Session 153 — CC agent name substitution is a protocol violation.** CC
  has consistently substituted agent names (e.g. `@backend-security-coder`
  for `@django-security`, `@ui-visual-validator` for
  `@accessibility-expert`, `@tdd-orchestrator` for `@tdd-coach`). The
  Session 153 Batch 2 run instructions added a hard rule: **Use EXACT agent
  names. Do not substitute. If an agent is unavailable, stop and report.**
  Spec templates should be updated to use registry-correct names going
  forward.
- **Session 153 — Negative CSS `animation-delay` for elapsed-time accuracy.**
  `animation-delay: -Ns` starts an animation as if it began N seconds ago
  (not a pause). Used in 153-F to show per-image progress bars at their
  correct elapsed position on page refresh — no fake restart, no 0% bar,
  no invisible placeholder. Combine with a `90%` cap (`Math.min(elapsed,
  duration * 0.9)`) so a slow-running image never shows near-complete.
- **Session 153 — `billing_hard_limit_reached` arrives as `BadRequestError`
  (400), not `RateLimitError` (429).** The existing `insufficient_quota`
  handler in `RateLimitError` does not catch billing-limit hits. A
  separate branch in the `BadRequestError` handler is required (153-D),
  and the backend sanitiser (`_sanitise_error_message`) also needs a
  billing branch BEFORE the quota check so the JS `reasonMap` can surface
  an actionable message (153-E). Matching keyword: `'billing limit'` (two
  words), not `'billing hard limit'` (three words) — the 153-D cleaned
  provider message is `'API billing limit reached...'` which does NOT
  contain the three-word form.
- **Session 154 — `GeneratorModel` as admin-toggleable single source of truth:**
  All model availability, credit costs, tier gates, aspect ratios, and
  promotional badges live in `GeneratorModel` DB table. No hardcoded model
  lists anywhere. Admin can disable a broken model instantly without a deploy.
- **Session 154 — Platform mode vs BYOK architecture:** OpenAI is ALWAYS BYOK
  (user's key, never a platform key). Replicate and xAI run in platform mode
  (master keys from Heroku env vars). `api_key_encrypted = NULL` is valid for
  Replicate/xAI jobs; fail hard for OpenAI jobs with no key.
- **Session 154 — Replicate uses `aspect_ratio` not pixel dimensions:**
  Replicate models accept strings like '1:1', '16:9' — not '1024x1024'. The
  UI switches between pixel size buttons and aspect ratio buttons based on the
  selected model. `getMasterDimensions()` returns whichever is active.
- **Session 154 — Credit system is DB-only until Phase SUB:** `UserCredit` and
  `CreditTransaction` track usage but no Stripe, no tier enforcement, no
  top-up purchase flow yet. All deferred to Phase SUB.
- **Session 154 — 4-tier framework (superseded Session 164):** Originally
  confirmed Starter/Creator/Pro/Studio at $0/$9/$19/$49 with ~22% annual
  discount. **Superseded by Session 164's 3-tier launch structure** (Free
  + Pro + Studio). Creator tier ($9) deferred to Month 4–6 post-launch
  pending signal data. See "Monetization Strategy & Upgrade Psychology"
  H2 section for current pricing and reasoning. Credit top-ups available
  on all tiers.
- **BYOK is the only viable model for bulk generation at scale:** Platform-paid API model fails because all users share Mateo's rate limits, creating unacceptable wait times with concurrent users.
- **Django-Q2 runs synchronously in local dev:** Tasks queued via ORM broker execute in the web process locally (either `sync=True` setting or Django-Q2 default). This means `[BULK-DEBUG] process_bulk_generation_job CALLED` appears in `runserver.log`, not `qcluster.log`. Production behavior (separate Heroku worker dyno) is unaffected.
- **`tee` for persistent log capture:** Use `python manage.py runserver 2>&1 | tee runserver.log` and `python manage.py qcluster 2>&1 | tee qcluster.log` for reliable debug log capture. Then grep with: `grep "BULK-DEBUG\|ERROR\|Traceback" runserver.log`
- **ThreadPoolExecutor (not asyncio) for concurrent generation in Django-Q2:** Django-Q2 task context is synchronous; `asyncio.run()` does not work inside it. Use `concurrent.futures.ThreadPoolExecutor` for parallel GPT-Image-1 calls in Phase 5D.
- **`flush_all` uses `@login_required` + manual staff check (not `@staff_member_required`):** `@staff_member_required` redirects non-staff to login instead of returning 403 JSON, breaking the AJAX flow. Manual check returns `JsonResponse({'error': ...}, status=403)`. Documented with verbatim comment in codebase.
- **OpenAI Tier 1 rate limit:** 5 images/minute, 15–45s per image. Sequential generation causes unacceptable wait times at scale — Phase 5D replaces it with `ThreadPoolExecutor`.

- **Rate limit compliance gap (Session 143):** `BULK_GEN_MAX_CONCURRENT=4` + `ThreadPoolExecutor`
  dispatches up to 4 concurrent API calls per batch, completing in ~15s before the next batch
  starts. This produces ~16 images/minute against Tier 1's 5 images/minute limit. The original
  Phase 5C inter-image delay was removed in Phase 5D. **IMMEDIATE MITIGATION (no code deploy):**
  Set `BULK_GEN_MAX_CONCURRENT=1` in Heroku config vars. **Permanent fix (DEPLOYED Session 143):**
  `OPENAI_INTER_BATCH_DELAY=12` setting added. D3 now enforces 12s inter-batch delay for Tier 1.
- **`OPENAI_INTER_BATCH_DELAY` — DEPRECATED (Session 146).** Per-job
  `_TIER_RATE_PARAMS` in `tasks.py` now controls all delay. Setting this
  config var has no effect. Use `BULK_GEN_MAX_CONCURRENT` for emergency
  concurrency ceiling only.
- **`BULK_GEN_MAX_CONCURRENT=1` is the safe Tier 1 baseline.** With
  `MAX_CONCURRENT=1`, GPT-Image-1's natural ~15–20s generation time paces
  requests under 5/min for medium and high quality. Low quality gets a 3s
  delay from `_TIER_RATE_PARAMS`. **Do not increase `MAX_CONCURRENT` beyond
  1 until the user's OpenAI tier is verified — or use the per-job tier
  system (see Section D).**
- **D2 generation retry is already implemented** — `_run_generation_with_retry()`
  in `tasks.py` retries `rate_limit` and `server_error` with exponential backoff
  (30s→60s→120s, max 3 attempts). This was built in Phase 5C. Do not re-implement.
- **Quality affects safe max_concurrent:** high quality (~30–40s gen time) is
  naturally paced even at `MAX_CONCURRENT=2` on Tier 1. Low quality (~8–10s)
  needs a delay buffer. Per-job rate params handle this automatically via
  `_TIER_RATE_PARAMS` lookup in `_run_generation_loop()`, added in Session 145.

- **Heroku env vars must be wired into `settings.py` (Session 148).** Setting a
  config var in Heroku does NOT make it available via `getattr(settings, ...)`.
  You must explicitly add `SETTING_NAME = os.environ.get('SETTING_NAME', '')`
  to `settings.py`. The prepare-prompts pipeline returned 401 because
  `OPENAI_API_KEY` existed in Heroku but `settings.OPENAI_API_KEY` resolved
  to empty string. Always verify both Heroku config AND `settings.py` wiring.

- **Django-Q timeout must exceed maximum expected job duration (Session 146).**
  A 200-prompt high-quality job can take 2+ hours. `timeout: 7200`,
  `retry: 7500`, `max_attempts: 1` are the correct production values.
  Retrying bulk gen tasks wastes API credits and produces duplicate images.
  The previous `timeout: 120` (2 minutes) was killing 3-prompt high-quality
  jobs mid-run.

- **Vision API calls use `detail: 'high'` for prompt generation (upgraded Session 152).**
  `detail: 'low'` (Session 149 original) compressed images to ~85×85px, losing
  spatial/depth information needed for accurate composition. `detail: 'high'`
  costs ~$0.009–0.015 per call but produces far better spatial descriptions.
  Base64-encode images before sending (URL passing is unreliable with
  CDN-served images). HTTPS URL validation + 10 MB size cap + no redirects
  for defense-in-depth (staff-only endpoint).

- **Word-level diff is computed client-side (Session 150).** LCS algorithm
  in `bulk-generator-ui.js`. No extra DB query or server computation needed.
  `original_prompt_text` stored only when different from prepared text
  (empty string = no modifications, zero storage cost for unmodified prompts).
  HTML-escaped per-word to prevent XSS in `innerHTML` context.

- **Vision direction must be decoupled from Vision analysis (Session 152).**
  Passing direction instructions INTO the Vision API call causes the model to
  reinterpret rather than describe the source image. Correct approach: Step 1 =
  Vision describes image (no direction), Step 1.5 = direction edits the Vision
  output via GPT-4o-mini (two-step). This produces accurate base descriptions
  with targeted modifications applied separately.

- **Vision composition: frame-position from viewer's perspective (Session 152).**
  LEFT/RIGHT/CENTRE must be from the viewer's perspective, not relative to
  subjects in the image. Add depth/distance, crowd/group counts, and
  anti-bokeh instructions ("describe background in detail, do not say bokeh").

- **Progress bar query: use `exclude(status='failed')` (Session 152).** Images
  start as `queued` status. Using `filter(status__in=['generating','completed'])`
  misses queued images. `exclude(status='failed')` catches all non-failed states.

- **`VISION_PLACEHOLDER_PREFIX in p` not `p.startswith(...)` (Session 151).**
  Character description prepending moves the Vision placeholder to mid-string
  position. Use `in` operator for substring match, not `startswith`.

- **Cloudflare caches job pages even with `Cache-Control: no-store` (Session 152).**
  Requires a Cloudflare Cache Rule bypass for `/tools/bulk-ai-generator/job/*`
  paths. Without this, users see stale progress on page refresh.

- **GPT-Image-1.5 released December 2025** with better instruction following
  and composition accuracy. Pending upgrade from `gpt-image-1`. Evaluate for
  improved spatial accuracy in generated images.

- **Pending-after-completion gap (Session 143):** If the generation loop exits before all
  `GeneratedImage` records transition from `status='pending'` to `status='failed'` (e.g., quota
  exhaustion, unhandled exception), those images show as "Not generated" in the gallery but are
  never counted in `failed_count`. The job reports 0 failures despite images not generating.
  Root cause: `failed_count` only increments when the backend explicitly catches an exception per
  image — orphaned `pending` records are never swept up. **Fix deployed (Session 143, D1):**
  post-loop sweep marks orphaned pending/generating images as failed and recalculates `failed_count`.
- **`select_for_update()` must be inside `transaction.atomic()`:** In Django autocommit mode, row locks acquired outside an explicit transaction are released immediately after the SELECT. Always wrap `select_for_update()` calls in `with transaction.atomic()`.
- **`continue` is illegal inside `with transaction.atomic()`:** Use a flag variable (`_already_published = False`, set inside block, tested after) instead of `continue` inside an atomic context manager.
- **M2M assignment must be duplicated in `IntegrityError` retry block:** Django rolls back the entire `transaction.atomic()` block on `IntegrityError`, including any M2M `.add()` calls. The retry block must re-apply all M2M (tags, categories, descriptors) from scratch.
- **Static `aria-live` announcer over dynamic injection:** Dynamically injected `aria-live` regions are not reliably announced by screen readers. Declare the region in the HTML at page load and populate its text content from JS (clear + 50ms timeout before setting).
- **OpenAI SDK note (Session 141):** GPT-Image-1 reference images require `client.images.edit(image=ref_file, ...)` — NOT `client.images.generate()`. The Python SDK v2.26.0 does not support an `images` parameter on `images.generate()`. Pass a `BytesIO` file-like object with `.name` attribute set (e.g. `ref_file.name = 'reference.png'`).

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

> `needs_seo_review` not set on bulk-created pages — fix in 153-H.

| Issue | Description | Impact |
|-------|-------------|--------|
| **Google OAuth credentials not yet configured** | Session 163-D built the allauth social-login plumbing but it is inert until the developer adds `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` to Heroku config vars OR creates a Google `SocialApp` row in admin. No end-to-end OAuth test is possible until then. | Developer action — next step for avatar pipeline full activation. |
| **env.py no longer sets DATABASE_URL (Session 163 incident)** | Local dev MUST use SQLite via settings.py fallback. Any local command that needs production data must inline `DATABASE_URL=<url>` for that specific command. Migration commands are developer-only; CC never runs `python manage.py migrate`. | Structural safeguard — see CLAUDE_CHANGELOG Session 163 incident section. |
| **`needs_seo_review` on bulk pages** | `create_prompt_pages_from_job` creates `Prompt` objects without `needs_seo_review=True`. Bulk-created pages silently bypass the SEO review queue. Priority blocker before large-scale content seeding. | Fix in 153-H (Session 153 Batch 2). |
| **~~N4h rename (upload-flow)~~** | ✅ RESOLVED Session 122 (commit a9acbc4). Guard changed from `is_b2_upload and prompt.pk` to `prompt.b2_image_url`. | Resolved — upload-flow prompts now trigger rename task |
| **~~CI/CD pipeline failing~~** | ~~All 3 jobs failing~~ — **RESOLVED Session 89** (691 tests at time of fix; now 976 passing, 12 skipped, flake8 clean, bandit clean) | ✅ All 3 jobs green |

**Phase REP Blockers:**
- ~~Grok reference image: needs `/v1/images/edits` endpoint~~ — ✅ RESOLVED Session 155 (155-C), then replaced with direct httpx POST in Session 156 (156-B) to fix SDK hang
- ~~Nano Banana 2 reference image: parameter is `image_input` (ARRAY)~~ — ✅ RESOLVED Session 155 (155-D)
- ~~NSFW error UX for platform models: xAI 400s show no user feedback~~ — ✅ RESOLVED Session 155 (155-B, 8-keyword detection)
- ~~Cost display incorrect for non-OpenAI models~~ — ✅ RESOLVED Session 156 (156-C audit, 156-D fix)
- ~~Grok billing 400 not routed to job-stop~~ — ✅ RESOLVED Session 161 (161-F, httpx path now returns `error_type='quota'`)
- ~~Grok connection drop returns `error_type='unknown'`~~ — ✅ RESOLVED Session 161 (161-F, `httpx.TransportError` caught → `server_error` for retry)
- NSFW UX feedback for Replicate platform model 400s (P2 — Replicate has only 3 keywords vs xAI's 8)
- `_download_image` duplicated in Replicate + xAI providers (P3, defer to third provider)
- ~~Primary SDK handler at `xai_provider.py:173` still uses `error_type='billing'`~~ — ✅ RESOLVED Session 162 (162-D, now returns `error_type='quota'` with static error message, matching 161-F's httpx-path pattern).
- ~~Bulk gen job view silent fallback~~ — ✅ RESOLVED Session 162 (162-E, `except Exception:` narrowed to `(ValueError, ImportError, AttributeError, KeyError)` + `logger.warning` — observability only; non-OpenAI semantic fallback correctness deferred as P2).

#### Rate Limiting Audit — Replicate + xAI (Deferred to Session 162+)

Current `_TIER_RATE_PARAMS` in `tasks.py` covers OpenAI tiers only.
Replicate and xAI have no provider-specific concurrency or delay config —
they rely on the global `BULK_GEN_MAX_CONCURRENT=1` ceiling only.

**Investigation required:**
- Read current `_run_generation_loop()` rate parameter lookup
- Add Replicate-specific concurrency config (safe default: 3 concurrent,
  Replicate free tier = 5 concurrent predictions)
- Add xAI-specific concurrency config (conservative default: 1–2)
- Wire provider-aware limits alongside existing OpenAI tier system

**Why this matters:** Flux Schnell generates in ~2 seconds. At
MAX_CONCURRENT=1 you generate ~30 images/minute — well under Replicate's
limits. Higher concurrency is safe and would significantly speed up
content seeding. Currently leaving performance on the table.

**Status:** Deferred — do not spec until Session 162 or later.


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
- ⚠️ **Priority before content seeding at scale:** bulk-created prompt pages do not have `needs_seo_review` set. This must be fixed before large-scale content seeding begins — otherwise hundreds of pages bypass the SEO review queue. Planned for Session 151.
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

- **Cloudflare Bot Fight Mode**: ENABLED (March 26, 2026)
  - Enabled on promptfinder.net domain via Cloudflare Security → Settings → Bot traffic
  - Detects and challenges malicious bot traffic
  - Verified search engine bots (Googlebot, Bingbot etc.) are whitelisted — no SEO impact
  - JS Detections: On
  - Triggered by PHP probe scan observed in Heroku logs from IP 4.232.84.11

### Heroku Release Phase (added Session 165, 2026-04-21)

The Procfile declares a `release` process type that runs
`python manage.py migrate --noinput` on every deploy, before the
new web dynos start serving traffic. This means:

- Migrations apply automatically when `git push heroku main` runs
  the release phase
- The new code never sees a stale schema (no recurrence of the
  2026-04-20 near-miss where v758 deployed with code expecting
  `avatar_url` 12 minutes before the column existed)
- If a migration fails, the release fails — Heroku does not
  promote the new dynos and traffic continues serving the previous
  release
- Developers no longer need to run
  `heroku run python manage.py migrate --app mj-project-4` after
  deploys

This complements the env.py policy documented in the Current
Blockers table (Session 163 incident row) and CLAUDE_CHANGELOG
Session 163 incident section. env.py prevents migrations from
leaking onto production from a developer machine; the release
phase ensures migrations DO apply on production via the proper
release-phase channel. Two complementary pieces of deployment
infrastructure — one negative (prevents wrong-channel application),
one positive (guarantees right-channel application).

**Important operational notes:**

- `--noinput` flag is mandatory — prevents `migrate` from hanging
  on destructive-operation confirmation prompts in the non-
  interactive release-dyno context
- `collectstatic` is NOT in the release phase. The Heroku Python
  buildpack already runs `collectstatic --noinput` during the
  build phase. Adding it to release would duplicate work and slow
  every deploy
- If a migration must be skipped for a deploy (emergency rollback
  of code without rolling back the migration), the developer can
  temporarily comment out the release line before pushing — this
  should be exceedingly rare
- Procfile change affects Heroku only. Local `python manage.py
  runserver` does not read Procfile and is unaffected

### Known deploy warning: `django_summernote`

Every Heroku deploy's release-phase output will include this line:

```
Your models in app(s): 'django_summernote' have changes that are not
yet reflected in a migration, and so won't be applied.
```

This is a known upstream package quirk (the `django-summernote`
package's model state is not fully captured by its bundled
migrations). It is NOT our code and NOT actionable. The `prompts`
app drift of this class was resolved in Session 165-B (migration
0086); `django_summernote` remains as a cosmetic deploy-log
warning only.

If the warning ever upgrades to an actual migration failure
(release fails, v`<n>` doesn't promote), investigate an upstream
package version bump or contribute a fix upstream. Until then:
ignore.

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

### Business Model & Monetisation Plan

**Phase 1 — Content seeding (current):**
Use the bulk generator internally to populate PromptFinder with
high-quality prompt pages at scale. Builds the SEO content library
and organic traffic that makes the platform worth monetising.

**Phase 2 — Subscription launch (Phase SUB):**
Once content library is established, introduce subscription plans.
Bulk generator is the premium hook.

---

#### Three-Tier Launch Structure (supersedes Session 154's 4-tier)

| Tier | Launch Monthly | Launch Annual | Regular Monthly | Regular Annual | Credits/mo | Models |
|---|---|---|---|---|---|---|
| Free | $0 | — | $0 | — | 100 (one-time signup) | Flux Schnell only |
| **Pro** | **$14** ~~$19~~ | **$138/yr** ~~$189~~ | $19 | $189/yr | 800 | All except 4MP HD and 4K variants |
| **Studio** | **$39** ~~$49~~ | **$384/yr** ~~$480~~ | $49 | $480/yr | 3000 | All models incl. FLUX 2 Pro 4MP HD + Nano Banana 2 4K |

**Launch pricing availability:**
- Available to the first 200 annual subscribers OR first 6 months
  post-launch, whichever comes first
- Annual subscribers at launch pricing are grandfathered at that
  rate for the lifetime of their continuously-active subscription
  (cancel and resubscribe = new pricing applies)
- Monthly subscribers get launch pricing for their first 3 months,
  then auto-transition to regular pricing via Stripe subscription
  schedule

**Why 3 tiers not 4 at launch (reasoning — do not remove):**

Session 154 specified 4 tiers (Starter/Creator/Pro/Studio). The
Creator tier ($9) is deferred to Month 4–6 post-launch because:

1. **No user data to validate 4-tier segmentation yet.** Every paid
   tier adds Stripe complexity, pricing page decisions, feature
   gating logic, test coverage, upgrade/downgrade flow edge cases.
   Four tiers means ~4× the pricing-related bugs of two paid tiers.
2. **Choice paralysis hurts conversion.** SaaS pricing research
   consistently shows conversion drops past 3 total options
   including free. Two paid options is a cleaner cognitive decision.
3. **Creator tier strategically weakest.** Creator would not include
   the bulk generator — the platform's core differentiator. Creator
   users would pay $9/mo for commodity features. Anyone wanting
   bulk generation upgrades to Pro; anyone not wanting it is better
   served by Free. Creator serves no clear audience at launch.
4. **Discovery-cap upgrades mostly hit Free → first paid tier.**
   With Creator and Pro competing for the same conversion event,
   Creator wins because it's cheaper, cannibalizing Pro revenue.
5. **Learning priority.** 3 tiers = 3 meaningful transitions to
   analyze (Free→Pro, Free→Studio, Pro→Studio). 4 tiers = 6.
   Cleaner data, faster iteration.

**When to add Creator tier ($9) back (Month 4–6 post-launch):**

Add if ANY of these signals emerge:

- **Signal 1:** >70% of Free users hitting discovery caps churn
  rather than upgrade (price resistance)
- **Signal 2:** ≥3 organic mentions in exit surveys/support/social
  of "I'd pay something but $14/19 is too much"
- **Signal 3:** Direct competitor launches sub-$10 tier pulling users
- **Signal 4:** Promotional campaigns (Black Friday, education,
  referral) need a $9 discount anchor

**Not reasons to add Creator:**
- Gut feeling that "more tiers = more revenue"
- Copying competitors who have 4 tiers
- Wanting to hit subscriber count faster without evidence

**Minimum criteria before launching Creator:** ≥100 paying
subscribers, ≥30 days of churn data, month 4–6 window, survey
feedback requesting lower tier.

---

#### Model Lineup and Credit Costs (April 2026)

| Model | Raw API Cost | Credits | Markup | Free | Pro | Studio |
|---|---|---|---|---|---|---|
| Flux Schnell | ~$0.003 | 1 | Margin floor | ✅ | ✅ | ✅ |
| GPT-Image-1.5 (BYOK) | $0 (user pays) | 2 | Platform fee | ❌ | ✅ | ✅ |
| Flux Dev | ~$0.025 | 3 | +20% | ❌ | ✅ | ✅ |
| Flux 1.1 Pro | ~$0.04 | 5 | +25% | ❌ | ✅ | ✅ |
| FLUX 2 Pro | ~$0.055 | 7 | +27% | ❌ | ✅ | ✅ |
| Grok Imagine | ~$0.07 | 8 | +14% | ❌ | ✅ | ✅ |
| Nano Banana 2 1K (Limited Time) | ~$0.067 | 8 | +19% | ❌ | ✅ | ✅ |
| Nano Banana 2 2K | ~$0.101 | 12 | +19% | ❌ | ✅ | ✅ |
| FLUX 2 Pro 4MP HD | ~$0.11 | 13 | +18% | ❌ | ❌ | ✅ |
| Nano Banana 2 4K | ~$0.151 | 18 | +19% | ❌ | ❌ | ✅ |

**`GeneratorModel.credit_cost` database field is live source of
truth.** Admin can adjust without deploy. This table is
informational; if it disagrees with the database, the database is
correct and this document needs refresh.

---

#### Top-Up Credit Packs

| Pack | Price | Per-credit | Positioning |
|---|---|---|---|
| 200 credits | $3 | $0.015 | Slightly worse than monthly sub — nudges toward subscription |
| 1000 credits | $12 | $0.012 | Same rate as monthly sub — convenience buy |
| 3500 credits | $35 | $0.010 | Matches annual sub rate — rewards heavy users |

Top-ups roll over monthly. Stack on top of subscription credits.
Mature credit-based SaaS products typically earn 40–60% of revenue
from top-ups rather than subscriptions.

---

#### Architecture Decisions (preserved from Session 154)

- **OpenAI GPT-Image-1.5 is ALWAYS BYOK** (user provides their own
  OpenAI key). No platform OpenAI key for image generation.
- **Replicate + xAI run in PLATFORM MODE** by default (master keys
  in Heroku env vars)
- **`GeneratorModel` DB table is single source of truth** for model
  availability — admin can toggle on/off/promotional instantly
- Pricing page and tier feature cards read from `GeneratorModel`
  dynamically — no hardcoded marketing copy
- Scheduled promotions: `scheduled_available_from/until` fields
  enable time-boxed promos (e.g., Nano Banana 2 "Limited Time")
- NSFW: platform NSFW checker (`requires_nsfw_check=True`) on all
  Replicate/xAI providers
- Replicate GPT-Image-1.5 wrapper skipped — direct OpenAI BYOK is
  better

---

#### Revenue Streams

1. **Subscription fees** (Pro, Studio; future Creator)
2. **Credit top-up purchases** — significant revenue stream, often
   40–60% of total
3. **Future: Prompt marketplace** — commission on sales or premium
   listings
4. **Future: API access for developers** — usage-based pricing

---

**Sequencing note:** Content seeding must happen BEFORE monetisation
launch. The bulk generator solves the chicken-and-egg problem —
internal tool populates the platform before real users arrive. Fix
`needs_seo_review` for bulk-created pages before seeding at scale.

**Platform cost per user:** Low but nonzero. Prepare-prompts pipeline
(translate, watermark, Vision, direction) costs ~$0.001–0.01 per
job (platform paid). Generation: Replicate/xAI platform-paid
(credits deducted from user balance). OpenAI BYOK — user pays
OpenAI directly.

**Detailed monetization strategy, upgrade psychology, profitability
math, credit system design, and post-launch items: see the four
dedicated sections that follow.**

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

## 💰 Monetization Strategy & Upgrade Psychology

> This section is the strategic companion to the "Business Model &
> Monetisation Plan" subsection above. It documents *why* pricing
> decisions were made, *how* upgrade triggers work, and *what*
> principles guide feature gating. Treat this as institutional
> memory — future sessions can consult it without re-deriving the
> reasoning.

### Two Independent Revenue Engines

PromptFinder has two parallel revenue engines. Understanding the
distinction informs every feature and pricing decision.

**Revenue Engine 1: Generation-driven upgrades.** Users upgrade
when they hit credit caps or want premium models. Every upgrade
has real dollar cost to the platform (API fees to OpenAI/Google/
xAI). Margin comes from credit markup plus fixed subscription fees.

**Revenue Engine 2: Discovery-driven upgrades.** Users upgrade
when they hit view caps, upload limits, collection caps, or want
access to hover-to-run. Near-zero marginal cost per user. These
upgrades are essentially pure margin after fixed platform costs.

Different personas (active creator vs. casual browser). Capturing
both expands the total addressable market meaningfully. Pricing
and feature gates are designed to activate both engines.

---

### Discovery Caps Table (launch values)

| Feature | Free | Pro | Studio |
|---|---|---|---|
| Prompt views/day (logged in) | 200 | Unlimited | Unlimited |
| Prompts uploaded/month | 5 | 100 | Unlimited |
| Saved/bookmarked prompts | 50 | 500 | Unlimited |
| Prompt drafts (unpublished) | 3 | 25 | Unlimited |
| Public collections | 5 | 50 | Unlimited |
| Private collections | 1 | 20 | Unlimited |
| Prompts per collection | 25 | Unlimited | Unlimited |
| Hover-to-run from gallery | Teaser (greyed, upgrade CTA on click) | 10/day | Unlimited |
| Advanced search filters (when built) | Basic | Full | Full |
| Download prompt metadata (JSON/CSV) | ❌ | ✅ | ✅ |
| Priority bulk generation processing | ❌ | ❌ | ✅ Studio only |
| Bulk generator access | ❌ | ✅ | ✅ |

**These are launch starting points. Validate with first 60 days of
data and adjust via Stripe metadata analysis (see Tracking section
below).**

---

### Cap Reasoning (why each number)

**Prompt views/day (Free: 200):** Casual browsers don't hit 200
daily. Active users will. Cap hits the right audience — users
engaged enough to browse heavily are the users closest to
conversion. Cap is a conversion opportunity at peak engagement,
not a punishment.

**Prompts uploaded/month (Free: 5):** Creators have different use
patterns than browsers. A user uploading 6+ prompts/month
demonstrates creator intent — they're building presence on the
platform. Pro's 100/month is generous for individuals; Studio
unlimited serves agencies and high-volume producers.

**Saved/bookmarked prompts (Free: 50):** 50 saved prompts
represents real investment. A user with 50+ saves has switching
cost — migrating elsewhere means losing curated collection. Cap
creates upgrade pressure at maximum engagement.

**Prompt drafts (Free: 3):** Drafts represent work-in-progress.
Users working on multiple drafts simultaneously are power users.
Tight cap (3) is deliberately restrictive because draft workflow
is Pro-tier-and-above behavior.

**Collections (Free: 5 public, 1 private, 25 prompts each):**
Collections are a lightly-used feature for most users but
critical for power users. Tight Free caps quickly exceeded by
power users, invisible to casual users.

**Hover-to-run:** Highest-value feature in the design. See
dedicated subsection below.

---

### The Hover-to-Run Feature as Premium Anchor

Hover-to-run is a gallery interaction: users hovering over any
prompt image see a button appear that opens a modal letting them
run the prompt on a generator of their choice.

**Why it's the strongest upgrade lever:**

1. **Converts browsing into generation.** Users browsing galleries
   are in inspiration-seeking mode. Removing friction between
   "this looks cool" and "let me make my own version" converts
   browsing (low revenue) into generation (high revenue).
2. **Demonstrates value at point of denial.** Free users see the
   greyed button, understand what it does, feel the friction.
   Desire created exactly at the point of encountering the limit.
3. **Hard for competitors to copy convincingly.** PromptHero
   doesn't have it. PromptBase doesn't either. Once experienced,
   alternatives feel clunky.

**Implementation:**
- Free and Pro users see button greyed with tooltip: "Generate
  this prompt — upgrade to [next tier] to unlock." Click opens
  short upgrade CTA.
- Pro gets functional hover-to-run, capped at 10/day.
- Studio gets unlimited hover-to-run.

**Dependency:** Requires single generator to be deployed. Bulk
generator is too heavy for a hover modal. Sequencing: single
generator ships → hover-to-run launches as Pro/Studio feature.

---

### Anonymous Browsing Strategy

**Anonymous visitor flow:**

- First 100 prompt views: uninterrupted browsing
- Every 50 views: persistent modal suggesting login ("Log in to
  continue discovering" / "Create a free account to save prompts
  you love")
- After 100 total views: hard login wall

**Logged-in Free tier:** 200 views/day (resets UTC midnight)

**Logged-in paid tiers:** Unlimited

**Why this structure:**

- **Anonymous cap protects SEO.** Google/crawlers complete their
  work before any wall appears.
- **Modal every 50 creates pressure without blocking.** Truly
  engaged users see multiple modals, normalizing signup.
- **Hard wall at 100 is non-negotiable.** Beyond this, continued
  free browsing is infrastructure cost without conversion path.
- **Daily reset (not per-session) prevents gaming.** Counter tied
  to IP + day minimum, better if session/device fingerprint.

---

### Launch Pricing Strategy with Countdown Urgency

**Launch pricing display:**
- Shown with strikethrough on regular price for visual contrast:
  "$14 ~~$19~~"
- Banner at top of homepage + pricing page during launch period
- Plain language: "Launch pricing. Limited to first 200 annual
  subscribers or 6 months."

**Grandfathering rules (recap):**
- Annual subscribers at launch pricing: locked forever while
  subscription continuously active
- Monthly subscribers: 3 months at launch rate, then
  auto-transition to regular

**Why annual-only permanent grandfathering:**

- **Cash flow:** Annual subscribers commit $138/$384 upfront —
  meaningful runway for a pre-launch business
- **Conversion signal:** Annual sign-ups self-select for conviction.
  These are customers worth rewarding with permanent rates
- **Scarcity psychology:** "Grandfathered forever — annual only"
  creates commitment-gated scarcity (more attractive to right
  customers) rather than mere time-gated scarcity

**Countdown timer mechanics (last 7 days of launch pricing only):**

- Sticky banner at top of homepage + pricing page (not every page)
- Real deadline. No resetting. No "extended by popular demand."
- Tiered urgency messaging:
  - Days 7–4: "Launch pricing ends in X days — lock in your rate now"
  - Days 3–1: Red accent + "Final [X] days to lock in launch pricing"
  - Final 24 hours: Animated pulse + countdown HH:MM:SS
- Dismissible per session, reappears after 24 hours, never modal-blocking
- Tracked in analytics: impressions vs. clicks vs. conversions.
  Conversion rate during countdown days should be ≥1.5× preceding
  week to justify the pattern
- Reserve this pattern for genuinely significant moments (launch
  end, Black Friday, milestones). Rare = powerful

**Price increase communication:**
- Announce price increase 30 days before it happens
- Creates conversion surge: "Prices go up [date], lock in $14 now"
- Plan pricing-increase campaign specifically to drive conversions

---

### Free Tier Strategy

**Free tier IS the trial at launch.** No formal trial period. Free
users get:

- 100 one-time signup credits (no monthly recurring)
- Flux Schnell model access only
- Full prompt discovery (capped per table above)
- Hover-to-run teaser (greyed button with upgrade CTA)
- Basic saving/bookmarking (50 prompt cap)
- Prompt creation (5/month cap)

**Why no recurring free credits:**

Every free image generation has real dollar cost to the platform.
Monthly recurring free credits = users who never convert but cost
real money indefinitely. One-time signup credits cap exposure — if
a free user converts, platform earns back the $1 of API cost many
times over. If they don't convert, loss is bounded.

**Why Flux Schnell only:**

At $0.003/image it has smallest dollar exposure per free
generation. Gating expensive models (Nano Banana 2 at $0.067, Grok
Imagine at $0.07) behind paid tiers protects margin. Flux Schnell
is genuinely usable for evaluation — not a crippled free product,
the most affordable full product.

**Why 100 signup credits specifically:**

100 credits at 100:1 internal ratio = ~$1 of real API cost per
signup. Enough for ~100 Flux Schnell images — a genuine product
taste. $1 acquisition cost per signup is low compared to paid
advertising CAC (typically $10–50 per paying customer, meaning
$1–5 per signup at 5–20% conversion rate).

---

### Trial Approach

**At launch: no formal trial period.** Free tier serves as the trial.

**Re-evaluate trials at Month 2–3 post-launch if:**

- Conversion rate from Free → Pro is below 2% after 60 days
- Exit surveys indicate "I didn't know if it was worth it" as
  common response
- Baseline conversion data exists to measure trial impact

**If trials are added later, structure:**

- 7-day trial to Pro tier only (not Studio)
- Credit card required — conversion rates 3–4× higher than
  no-CC trials
- Mandatory email reminder sequence:
  - Day 0: Welcome + trial-end date + "you'll be charged $X unless
    you cancel"
  - Day 3: Progress check-in + "trial ends in 4 days"
  - Day 5: "2 days left" with easy cancel link
  - Day 6: "Trial ends tomorrow" — subject line that actually
    gets read
  - Day 7 morning (6 hours before charge): "Your trial ends today"
  - Day 7 post-charge: Receipt + "you've been charged, cancel
    anytime"

**Why not launch with trials:**

- Adds Stripe complexity when stability matters most
- Trial abandonment, dunning flows, trial-end notifications need
  to work perfectly day 1 — large surface for bugs
- No baseline conversion data; impossible to measure trial impact
- Chargeback risk damages Stripe account health early when
  payment reputation is still being established
- Without email reminders, trial chargeback rates become
  unacceptable (2–5% vs. 0.5–1% with reminders)

**Note on chargebacks:** Terms of Service CANNOT prevent
chargebacks. Card networks give cardholders dispute rights
regardless of ToS. What DOES reduce chargebacks:
- Clear billing descriptors ("PROMPTFINDER.NET" not "MJ-PROJECT-4")
- Visible 2-click cancellation (no dark patterns)
- Pre-charge notifications (email 3 days before renewal)
- Responsive refund policy (easier to get refund = fewer disputes)
- Solid receipt emails with usage summary and cancellation link

---

### Welcome Email Sequence (required at launch)

First-month welcome sequence, required regardless of trial
structure:

- **Day 1 (signup):** Welcome email + onboarding checklist + first
  generation tutorial
- **Day 3:** "Here's what you've made so far" with their generated
  images + engagement prompts
- **Day 7:** "Pro tip" email demonstrating advanced feature they
  haven't tried yet
- **Day 14:** "Halfway through your first month — here's what
  people like you are doing" (social proof + aspirational framing)
- **Day 28 (before first renewal, if paid):** Usage summary +
  receipt preview + "You'll be charged $X on [date], cancel
  anytime"

**Why Day 28 email is critical:**

Addresses "forgot they signed up" problem directly. Reminds users
of upcoming charge, shows value received, gives clean exit path.
Dramatically reduces chargebacks and refund requests. Users who
stay after this email are intentional paying customers.

---

### Stripe Metadata Tracking (required at launch)

Every Stripe subscription creation and upgrade event must populate
custom metadata. Free data, compounds in value.

**Required metadata fields:**

- `trigger_feature` — specific cap/feature that prompted upgrade.
  Values: `prompt_view_cap`, `upload_cap`, `collection_cap`,
  `hover_to_run_teaser`, `bulk_generator_gate`,
  `premium_model_gate`, `saved_prompts_cap`, `draft_cap`,
  `organic` (no specific trigger)
- `trigger_source` — where upgrade UI was presented. Values:
  `pricing_page`, `feature_modal`, `settings_page`,
  `countdown_banner`, `email_campaign`, `onboarding_flow`
- `previous_tier` — `free`, `pro`
- `time_on_free_tier_days` — days between signup and upgrade
- `generations_consumed_pre_upgrade` — image count before paying
- `launch_pricing_applied` — boolean, whether subscriber got
  launch rate

**Implementation:** Frontend sends trigger context to backend on
"Upgrade" button click. Backend includes metadata in Stripe
checkout session creation. Retrievable via Stripe Dashboard or API.

**What this unlocks at Month 3–6:**

- Which feature drives the most conversions? → double down
- Which caps do users hit but NOT upgrade from? → caps wrong or
  feature not valued enough
- Do collection-cap upgrades convert higher than upload-cap? →
  informs cap tightening
- Average time from signup to upgrade? → informs email timing
- Do countdown-banner conversions differ from feature-modal? →
  informs UI investment

**Most founders skip this setup and regret it six months later
when pricing decisions need signal. Set up at launch.**

---

### Visible Cap Counters UI Pattern

Caps should be visible, not hidden. "27/30 prompt views today"
sitting in the corner of every page is more conversion-effective
than surprise blocking.

**Why visible counters work:**

- Create anticipatory upgrade behavior — users upgrade *before*
  hitting the wall, feels like their choice not a forced decision
- Reduce the "angry wall" moment generating support tickets and
  negative sentiment
- Provide continuous ambient awareness vs. discrete disruptive
  events
- Seeing "495/500 saved prompts" creates more urgency than
  suddenly being blocked at #501

**Counter placement:**
- Account menu dropdown: full breakdown of all tier caps
- Header bar (compact): most-relevant current cap based on page
  context
- Relevant feature pages: inline next to feature being used

**Color coding:**
- 0–70% of cap: neutral/muted
- 70–90%: amber/warning
- 90–100%: red/urgent + soft upgrade CTA
- 100%: block + clear upgrade modal

---

### Positioning and Marketing Language

**Sell time saved, not credits or images.** Price anchors matter.
The $19 Pro tier positions against Midjourney ($30) and ChatGPT
Plus ($20) — not against raw API cost.

**Good marketing copy examples:**

- "Generate 200 publish-ready AI images in 20 minutes"
- "Turn your prompt library into indexed pages automatically"
- "Skip the setup — one subscription, six image models"
- "Your prompt feed, organized and searchable"
- "Bulk generate, moderate, and publish — all in one tool"

**Bad marketing copy (avoid):**

- "$0.048 per image" — invites unit-cost comparison to raw APIs
- "1000 credits for $19" — invites math that reveals margin
- "X% cheaper than Midjourney" — positions as budget alternative
- "Same quality as [expensive competitor]" — leaves price as only
  differentiator
- "Credits never expire" — if true, say it differently ("Unused
  credits roll over")

**Why this matters:**

Users who can do unit math and compare to raw API access aren't
the target customer. They're developers who should use APIs
directly. Target customer values their time at any reasonable
hourly rate and wants convenience + workflow + SEO automation.
For them, $14–19/mo is cheap. Anchor isn't "how much does an
image cost" — it's "how much is my time worth."

---

## 📊 Profitability Targets & Market Context

> Break-even math, scale milestones, market advantages, disadvantages,
> and risks. Uses conservative assumptions so numbers are floor
> estimates, not aspirational.

### Fixed Monthly Cost Baseline

| Category | Estimated cost |
|---|---|
| Heroku dynos + Postgres + add-ons | $50–100 |
| Backblaze B2 storage + Cloudflare CDN | $10–30 (current scale) |
| Domain, email, misc SaaS tooling | $30 |
| OpenAI baseline (vision moderation, AI content) | $20 |
| **Total fixed monthly** | **~$150–200** |

Fixed costs must be covered regardless of subscriber count. Grow
sub-linearly with users — doubling subscribers doesn't double
Heroku costs.

---

### Per-Subscriber Unit Economics (approximate)

| Tier | Avg monthly revenue | Est variable cost | Net per sub |
|---|---|---|---|
| Free | $0 | $0.10–0.30 | -$0.10 to -$0.30 (acquisition loss) |
| Pro launch ($14) | $14 | $4–8 | $6–10 |
| Pro regular ($19) | $19 | $4–8 | $11–15 |
| Studio launch ($39) | $39 | $12–25 | $14–27 |
| Studio regular ($49) | $49 | $12–25 | $24–37 |

Plus top-up pack revenue: industry typical 40–60% of total
subscription revenue from mature credit-based SaaS.

**Actual unit economics vary based on model-mix used by each
subscriber. Update this table with real data at Month 3.**

---

### Scale Milestones

| Milestone | Paying subscribers | What it means |
|---|---|---|
| Fixed-cost break-even | ~15 | Platform costs covered |
| Side-project viable | 50–100 | Covers costs + modest income |
| Minimum-wage equivalent | 200–300 | Hourly-equivalent solo income |
| Real business | 500+ | Sustainable full-time income |
| Strong business | 1,000+ | Room for reinvestment, contractors |
| Scale business | 5,000+ | Justifies full-time team |

**Example calculation at 500 paying subscribers** (conservative
Pro/Studio mix, average ARPU ~$22/mo factoring top-ups):
- Gross revenue: ~$11,000/mo
- Variable costs (API, vision moderation): ~$2,500/mo
- Fixed costs: ~$200/mo
- Stripe fees (2.9% + $0.30 per transaction): ~$350/mo
- **Net: ~$7,950/mo** (~$95,400/yr)

---

### Market Advantages (PromptFinder's structural strengths)

1. **SEO flywheel.** Content seeding (Phase 1) creates organic
   traffic that compounds monthly. Unlike paid acquisition that
   stops when budget stops, SEO traffic grows until actively
   damaged. First-mover advantage in narrow niche (AI prompt
   discovery + bulk generation) is real.
2. **Bulk generator differentiation.** Competitors (PromptHero,
   PromptBase, Civitai) offer discovery without bulk generation.
   AI image generation platforms (Midjourney, Ideogram) offer
   generation without discovery. Combining both is unusual and
   defensible.
3. **Credit system scalability.** Credit-based pricing allows
   shifting between models as provider prices change without
   repricing subscriptions. If Nano Banana 2 drops 50% next
   quarter, reflected in `GeneratorModel.credit_cost` without
   subscription changes.
4. **Multi-provider integration.** Users don't have to manage API
   keys across three providers. Real convenience worth paying for.
5. **Content seeding head start.** By Phase SUB launch, platform
   already has meaningful content — not an empty shell begging
   for uploads.
6. **BYOK option for power users.** Users who want to pay OpenAI
   directly bring their own key, keeping platform relevant for
   cost-sensitive segment without hurting margin (they pay for
   tooling, not API).
7. **Two independent revenue engines.** Most competitors have
   only one.

---

### Market Disadvantages and Risks

1. **Crowded competitive landscape.** PromptHero, PromptBase,
   Civitai, Lexica, Leonardo, OpenArt, and others already exist.
   Users have habits. Displacing an incumbent requires clear
   differentiation (which PromptFinder has) but must be actively
   marketed.
2. **AI image generation commoditizing.** New models launch
   monthly, most cheaper than previous. Differentiation on "best
   model" is impossible; differentiation on workflow, SEO, and
   convenience is the strategy. User expectations around model
   quality will outpace what cheap models deliver, creating
   constant pressure.
3. **Three-provider reliability risk.** Dependency on OpenAI,
   Replicate (Flux variants), and xAI (Grok) = three points of
   billing failure, rate limit issues, potential outages. Any
   provider down degrades product. Mitigation: queue retry logic,
   clear user messaging, alternative provider fallback where
   reasonable.
4. **Free tier costs real dollars.** Unlike content-based free
   tiers where "free" means a few cents of compute, every free
   image costs real money to Google/xAI/BFL. One-time signup
   credits cap exposure; indefinite monthly free credits would
   bleed out. This is why launch uses one-time credits only.
5. **Hype-driven market volatility.** AI market sentiment shifts
   quickly. Regulatory changes, company pivots, scandals — all
   reshape user acquisition costs overnight. Unlike stable SaaS
   categories, AI tools don't have predictable demand curves yet.
6. **Solo founder bandwidth.** Building, marketing, supporting,
   iterating — all one person. At launch focus is core; at scale
   something gives. Plan for contractor/freelance help at 1,000
   subscribers ("Strong business" milestone).
7. **Solo founder single point of failure.** If founder
   incapacitated, platform dies. Document everything. Secure
   credentials in password manager. Consider dead-man's switch
   for critical credentials at scale.

---

### Success Signals to Watch

**Leading indicators of product-market fit (Month 1–3):**

- Organic signup rate trending up (not just stable)
- Time-to-first-generation < 5 minutes post-signup
- Day-30 retention (% of signups returning in month 2): industry
  benchmark 40%+ for consumer-ish products
- Free → Pro conversion rate: target 2–5% at Month 3
- Average generations per paid user per week: if growing, value
  is landing
- Unsolicited word-of-mouth mentions (Twitter, Reddit, Discord):
  qualitative but important

**Red flags requiring strategy adjustment:**

- Free signups without any generations (product isn't clicking)
- Pro users churning within first 30 days (onboarding or value
  delivery problem)
- High refund/chargeback rate (>2%, likely billing trust issue)
- Support tickets about pricing confusion (tier structure or copy
  needs clarification)
- No users hitting any caps (caps too loose, not generating
  upgrade pressure)

---

## 🪙 Credit System Design Principles

> Why credits, not dollars. Why 100:1 ratio. Why markup 14–27% per
> model. Why psychological rounding matters. Internal vs. external
> credit pricing.

### Why Credits, Not Dollar-Per-Image

Credits abstract the real cost in ways that benefit both platform
and users.

**For users:**
- Simpler mental model than tracking different model prices
- "I have 800 credits this month" easier to reason about than
  "I have $6.40 of API budget"
- Buying top-ups feels like buying capability, not spending money
- Round credit numbers feel abundant ("800 credits") more than
  decimal dollar amounts ("$6.40 in credits")

**For the platform:**
- Insulates subscription price from provider price changes
- Enables model-mix flexibility — if users shift from expensive
  to cheap models, revenue stays stable even though costs drop
- Credit cost per model adjustable server-side without repricing
  subscriptions

---

### The 100:1 Internal Ratio

**Internal reference: 100 credits ≈ $1 of raw API cost.**

**This ratio exists for platform planning. It is NEVER exposed
to users anywhere in the product, pricing page, or marketing
copy.**

**Why 100:1 specifically:**

- Abstract enough that users can't easily reverse-engineer markup.
  User doing quick math on "8 credits for one image" at "$14/mo
  for 800 credits" computes "$0.14 per image" — this obscures
  actual API cost ($0.067 for Nano Banana 2) and prevents direct
  comparison to raw API access
- "You have 800 credits" reads as abundance vs. "You have 8
  images" which feels scarce
- Whole-number credit costs per image feel clean ("8 credits per
  Nano Banana 2 image" vs. "67 credits") without sacrificing
  granularity
- Top-up pack math stays readable (200 credits/$3, 1000/$12,
  3500/$35)

**Why NOT 1:1 ratio (1 credit = $0.01):**

Too easy for users to calculate true cost by multiplying and
comparing. Destroys margin-preserving obfuscation.

**Why NOT 1000:1 ratio:**

Numbers become inflated and meaningless ("80,000 credits for
$14/mo"). Users stop feeling value of individual credits.
Marketing copy becomes awkward.

---

### Markup Strategy (14–27% per model)

Every credit cost is set 14–27% above raw API cost, with
psychological rounding to whole credits.

**Rationale for the markup range:**

- Covers platform overhead (vision moderation ~$0.003/image,
  storage, compute, support infrastructure)
- Builds layered margin beyond subscription fee
- Allows absorbing small provider price increases without
  immediate tier repricing

**Rationale for psychological rounding:**

Credit costs rounded to whole numbers feel cleaner than precise
decimals. "8 credits" is intuitive; "7.14 credits" breaks mental
model. Rounding up slightly builds margin without users noticing.

**Worked example: Nano Banana 2 1K at $0.067**

- Raw cost at 100:1 ratio = 6.7 credits
- Round up to 7 credits = slight margin + cleaner number
- **Round up to 8 credits = +19% markup, round number, meaningful
  margin** ← chosen
- Rationale: 8 credits preserves margin floor + matches other
  premium models (Grok Imagine at 8 credits) for tier consistency

**Worked example: Grok Imagine at $0.07**

- Raw cost at 100:1 ratio = 7 credits exactly
- 7 credits = 0% markup, no margin
- **8 credits = +14% markup, matches Nano Banana 2 tier
  positioning** ← chosen

**Worked example: Flux Schnell at $0.003 (outlier)**

- Raw cost at 100:1 ratio = 0.3 credits
- Rounded up to 1 credit = massive percentage markup (+233%),
  but in absolute terms still tiny
- **1 credit serves as "margin floor"** — ensures Flux Schnell
  doesn't become a loss leader while keeping it the clear
  "cheapest option" for users

---

### Credit Costs as Living Values

**`GeneratorModel.credit_cost` database field is the live source
of truth.** Admin can adjust without a deploy. CLAUDE.md
documentation is informational snapshot.

**If CLAUDE.md and database disagree, database is correct and
this document needs updating.**

**When to adjust credit costs:**

- Provider raises/lowers raw API cost materially (±10%)
- Usage patterns shift in ways affecting margin (users heavily
  favoring a model that's underpriced)
- Promotional adjustments (Nano Banana 2 "Limited Time" pricing
  could include temporary credit reduction to drive trial)

**When NOT to adjust:**

- Short-term provider price volatility (<10% swing)
- Temporary usage spikes on specific models
- Competitor repricing (they'll keep moving; react to durable
  trends not single events)

---

### User-Facing Credit Communication

Users see credits, never the ratio or underlying cost. Acceptable
user-facing copy:

- "You have 800 credits this month"
- "This image costs 8 credits"
- "Need more? Top-up packs start at $3"
- "Upgrade to Studio for 3,000 credits/month"

Unacceptable user-facing copy:

- "Credits are worth about $0.01 each"
- "That image costs us $0.067"
- "Our markup on this model is 19%"

---

## 🔮 Post-Launch Recommendations

> Items to revisit once real usage data exists. Timeline phased
> by expected data availability.

### Month 1–3 (first real-usage window)

- **Validate conversion rate assumptions.** If Free → Pro is
  below 2% after 60 days, evaluate trial structure (CC-required
  7-day Pro trial).
- **Measure which discovery caps trigger the most upgrades** via
  Stripe metadata. Tighten caps that don't convert; loosen caps
  causing bounce.
- **Monitor actual model-mix usage.** If users heavily favor
  expensive models, adjust credit costs or tier allocations.
- **Track chargeback rate.** Above 1% = investigate; above 2% =
  urgent intervention.
- **Measure Day-28 email effectiveness.** Compare chargeback and
  refund rates between users who opened the Day-28 email and
  those who didn't.

### Month 3–6 (pattern recognition window)

- **Reassess 4th tier (Creator at $9)** based on signal patterns
  documented in "Monetization Strategy" section. Four specific
  signals; none = don't add; any = consider adding.
- **Evaluate launch pricing phase-out.** If 200 annual
  subscribers hit quickly, consider controlled extension (e.g.,
  "first 500") vs. ending on schedule.
- **Consider referral program** if organic conversion mechanics
  are validated. Suggested: referrer gets 200 credits, referee
  gets +50 signup credits bonus. Don't launch at initial release
  — needs baseline conversion data first.
- **Review GPT-Image-1.5 BYOK usage.** If minimal, consider
  deprecating or repositioning.

### Month 6+ (scale and expansion window)

- **Build out prompt marketplace** (revenue stream 3).
- **Evaluate Phase 2 features:** Content Intelligence Agent,
  CLIP visual similarity, POD (Printify/Printful) integration.
- **Consider API access tier for developers** (usage-based
  pricing).
- **Reassess fixed costs** — scaling may justify infrastructure
  upgrades or migration.
- **Hiring consideration** at 1,000 subscribers milestone —
  contractor help for marketing, customer support, content
  moderation.

### Documentation Visibility Note

CLAUDE.md is currently a private strategy document, readable only
by the project owner and Claude Code. If the repository ever gets
shared with contributors, investors, or open-sourced partially,
CLAUDE.md becomes readable by them.

**Before any repository share event:**

- Review CLAUDE.md for content that should stay private (specific
  revenue targets, competitor critique, candid risk inventory)
- Create a shareable abridged version if appropriate
- Consider splitting into public + private strategy docs

This is not a current concern — all project work is solo — but
worth revisiting at scale milestones or before external sharing.

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

#### Cloudinary Migration Status (Updated Session 162)

Management command `migrate_cloudinary_to_b2` was created in
Session 160-F, credential-fixed in Session 161-A (correct
`B2_ACCESS_KEY_ID`/`B2_SECRET_ACCESS_KEY` setting names;
`CloudinaryResource` public_id via `.public_id` attribute not
`str()`), and queryset-fixed in Session 162-A (Q-object replacement
for SQL `IN (NULL)` three-valued-logic bug). Dry-run now correctly
identifies 36 prompt images + 14 videos + 0 legacy avatars
(no avatars migrated yet — avatar upload pipeline switch is Session
163 F1).

**Correction (162-C investigation):** the 161-A narrative claimed
that pre-fix code fell back to `str(CloudinaryResource)` which
"returned object repr". A direct SDK test at current cloudinary
version shows `str(CloudinaryResource(public_id='legacy/foo'))`
returns `'legacy/foo'` (the public_id, not the repr). The real
latent bug was `str(None) == 'None'` producing `'legacy/None.jpg'`
URLs when the CloudinaryField was NULL. The `.public_id` pattern
still resolves this (falls back to empty string via `or ''`) and
is preferred as defense against future SDK behavior changes.

Avatar migration support was added in Session 161-E:
`UserProfile.b2_avatar_url` URLField (migration 0084) + new
`_migrate_avatar()` method + `--model userprofile` choice.

**Session 163-B update (2026-04-20):** Avatar `CloudinaryField` has
been dropped entirely (migration 0085). `b2_avatar_url` was renamed
to `avatar_url` and `avatar_source` CharField added. The
`_migrate_avatar` method was removed from `migrate_cloudinary_to_b2`
since no avatar data ever existed in production (April 19 diagnostic
confirmed 0 legacy avatars). UserProfile is now fully Cloudinary-free.
`Prompt` still has CloudinaryField (image + video) — those remain
in scope for a future `CloudinaryField → CharField` migration spec.

Run sequence (developer runs manually on Heroku):

1. `heroku run "python manage.py migrate_cloudinary_to_b2 --dry-run"` —
   preview what would be migrated (prompts + avatars). No DB changes.
2. `heroku run "python manage.py migrate_cloudinary_to_b2 --limit 3"` —
   migrate 3 records as a test batch. Verify images load on the
   live site.
3. `heroku run "python manage.py migrate_cloudinary_to_b2"` — full
   migration (prompts + avatars).

Scoped variants:
- `--model prompt` — images + videos on Prompt only.
- `--model userprofile` — avatars only.
- `--model all` (default) — everything.

After confirmed working on Heroku, these follow-up specs should run
in order:

- **CloudinaryField → CharField migration** — future session after
  every prompt has a populated `b2_image_url`. Requires data
  migration to preserve stored public_ids.
- **Cloudinary code + package removal** — after field migration.
  Must include a Step 0 check confirming no `CloudinaryField`
  references remain in any model AND all migration history has been
  squashed or the field-type migration is already applied (per
  @architect-review note in REPORT_161_E Section 6).
- **Remove `CLOUDINARY_URL` from Heroku config vars** — after code
  removal.

Cloud name: `dj0uufabo` (corrected — old typo in some historical
specs was `dj0uufabot`).

### 2026-04-18 credentials rotation

During Cloudinary debugging on 2026-04-18, several production
credentials were accidentally exposed in terminal output and
subsequently rotated:

- `SECRET_KEY` — rotated
- `FERNET_KEY` — rotated. BYOK API keys encrypted with the old
  key are no longer decryptable. No real users had BYOK keys
  stored at rotation time, so no user-facing impact.
- `OPENAI_API_KEY` (the developer-BYOK test key, not a platform
  key) — rotated
- `DATABASE_URL` — Heroku rotates this automatically on the
  essential-0 plan; no manual action required
- Replicate and xAI keys — not rotated at the time (low-risk
  exposure scenario); if future exposure occurs, rotate both

The Cloudinary cloud name typo (`dj0uufabot` → `dj0uufabo`) was
also corrected on the same day — the extra `t` had been causing
404s on historical Cloudinary image URLs.

---

## 🧠 Claude Memory System & Process Safeguards

**Last reviewed:** April 21, 2026 (Session 167-A)
**Source discussion:** Session 166-A follow-up conversation

This section documents how Claude's memory system works in this
project, what memory rules are currently active, why they were
added, and what was considered but deferred. It exists so future
Mateo and future Claude can reason about the memory system
itself — not just operate within it.

### How Claude's memory works

Claude's memory is a set of user-specific rules ("memory edits")
stored by the Anthropic platform and loaded into Claude's context
window at the start of every conversation. Key mechanics:

- **Persistence:** Edits persist across all future conversations
  on Mateo's Claude account until explicitly removed or replaced
- **Loading:** All active edits are loaded at the start of every
  new conversation, adding ~150–200 tokens per edit to the
  baseline context
- **Firing:** Every rule is "active" in every conversation — a
  rule about credential handling fires even during a frontend
  CSS chat, though it remains inert unless relevant
- **Capacity:** 30 slots maximum. Currently 9 used (as of Session
  167-A). Overstuffing causes contradictions and cognitive noise
- **Cost:** Each edit adds to per-message token cost. 9 edits
  adds roughly 1,300–1,800 tokens per message. For a 40-message
  session, that's 52,000–72,000 extra tokens of context overhead
- **Value threshold:** An edit earns its slot by preventing a
  proven failure mode, codifying a consistently-stated preference,
  or formalizing a cadence that silent drift would erode

### Why memory rules matter for this project

PromptFinder has experienced three production incidents in April
2026 — April 18 (credentials exposure), April 19 (env.py migration
leak), April 20 (Procfile release-phase near-miss). All three
were dev-prod boundary failures that could have been prevented
by consistent application of structural safeguards. Memory rules
are the mechanism for making those safeguards consistent rather
than "remember to do this" reminders that drift.

### Active memory rules (17 of 30)

The following rules fire in every Claude conversation for this
project. Listed in slot order.

#### 1. Future-feature tracker: notification link tracking
Track clicks on embedded Quill links in system notification
message body HTML (planned feature).

*Note: Rule #1 predates the April 2026 discussion. It is a
forward-reference tracker for a planned feature, not an
incident-response rule. The rationale-paragraph format used by
rules 2-9 is therefore intentionally omitted.*

#### 2. Context verification on artifact-only starts
When Mateo shares CC reports, specs, or work artifacts at the
start of a session without a context block, Claude uses
`recent_chats` or `conversation_search` to verify project state
and protocol version before producing analysis. Never infer
project context solely from artifact content.

**Rationale:** Session 164 context-verification issue — Claude
reviewed 161-series reports without proper context block,
pattern-matching from artifacts alone. Protocol had drifted
from v2.2 to v2.7 between sessions; 161-A claim was later
corrected in 162-C.

#### 3. ⚠️ Pre-flight warnings on credential-output commands
Before providing commands whose output could expose credentials,
secrets, or PII (heroku config, env inspection, DB queries with
user data, API responses with keys, curl with auth headers,
git diff on env.py), Claude prefixes with a `⚠️` warning naming
the specific data type, explains running is fine but redaction
before pasting back is required, and suggests safer alternatives
when they exist (`heroku config:get --shell`, hash comparison,
schema-only queries).

**Rationale:** 2026-04-18 rotation incident — credentials
accidentally exposed in terminal output during Cloudinary
debugging; SECRET_KEY, FERNET_KEY, OPENAI_API_KEY rotated.
Cost: hours of rotation work + real security exposure. This
rule's pre-execution safeguard prevents recurrence.

#### 4. No credential echo in outputs
When debugging or inspecting code involving credentials
(SECRET_KEY, FERNET_KEY, DATABASE_URL, B2 keys, OAuth secrets,
BYOK keys), Claude never echoes credential values in specs,
reports, or chat responses. If Mateo shares a value inadvertently,
Claude flags the exposure and recommends rotation rather than
proceeding silently. Specs reference env var names, never values.

**Rationale:** Reinforces rule #3 from Claude's side. #3 warns
Mateo; #4 ensures Claude doesn't perpetuate exposures once
they're in context.

#### 5. Dev-prod boundary discipline
Dev-prod boundary is PromptFinder's dominant security concern.
Claude treats any command, setting, or config that could cross
it (`DATABASE_URL`, `CLOUDINARY_URL`, `heroku run migrate`,
manual schema edits, production shell) as requiring explicit
developer confirmation — never CC-autonomous. When drafting
infrastructure specs, Claude explicitly asks: "what could apply
to production unintentionally" and adds guards.

**Rationale:** All three April 2026 incidents were boundary
failures. This rule generalizes the pattern that the env.py
safety gate (Session 163 v2 protocol) and the Procfile release
phase (Session 165-A) address structurally.

#### 6. Pause for significant issues
When Claude detects a significant issue mid-task, Claude pauses
current work and surfaces immediately rather than completing
the task first. "Significant" = (1) user-visible harm risk,
(2) credential or sensitive data exposure, (3) contradicts a
factual claim the task depends on, (4) echoes past incident
patterns. Lower-severity issues flag at task end. When in doubt,
surface sooner — missed escalations cost more than extra
confirmations.

**Rationale:** Addresses calibration gap where task-completion
bias could delay surfacing real problems. Codifies behavior
that was previously implicit and inconsistent.

#### 7. Audit before answering "any outstanding issues"
When Mateo asks about outstanding issues, pending work, or
project state, Claude runs an audit before answering — not just
recall from recent-session context. Check critical-tier docs
(CLAUDE.md, CLAUDE_CHANGELOG.md, PROJECT_FILE_STRUCTURE.md)
for stale entries, version footers, missing session rows,
placeholder tokens like `<hash>`. Scope audit to recent changes,
not the entire document.

**Rationale:** Session 166 morning audit surfaced 11 unaddressed
items in core docs after Claude had answered "nothing to fix"
the previous evening. Memory-based recall missed the broader
project state.

#### 8. Read target files in full before spec drafting
Before drafting specs touching migrations, code, or models,
Claude reads target files in full, not just greps. For migration
specs, read the chain back to the most recent relevant
`AddField` — `RenameField` and `AlterField` inherit metadata
from prior operations. Speculative "likely format" examples
in specs are forbidden; use "whatever Grep A returns" framing.

**Rationale:** Session 165-B CharField-vs-URLField diagnostic
error was surface-signal reasoning. Reading migration 0085 in
full would have caught that the field was already `URLField`
and the drift was `help_text`-only.

#### 9. Phase-completion security audits
At the completion of major phases (Phase REP production-ready,
Phase SUB launch, POD integration MVP, bulk uploader MVP,
content intelligence agent MVP, etc.), Claude proactively
proposes a security audit pass before moving to the next phase.
Audit covers: new attack surfaces, interaction with existing
guards, credential handling in new paths, SSRF/outbound
request exposure, user-input boundaries, rate-limiting coverage,
dev-prod boundary considerations, past incident-pattern echoes.
Separate spec with `@backend-security-coder` + `@security-auditor`
minimum.

**Rationale:** Per-spec security review catches per-spec issues.
Phase-level audit catches emergent interactions between
independently-shipped components — a different failure class.
Security debt compounds silently; proactive cadence addresses
this.

#### 10. Read current versions of files before drafting specs
Before drafting any spec referencing specific file contents,
line numbers, function bodies, or migration chains, Claude
asks Mateo to upload the current versions of every file the
spec touches. The project's core docs (`CLAUDE.md`,
`PROJECT_FILE_STRUCTURE.md`, `CLAUDE_CHANGELOG.md`) and any
target source files referenced by the spec must be uploaded
or read in full before draft begins. Speculation about
"likely" file state is forbidden.

**Rationale:** Session 168-D-prep was the first session where
this rule fired — it surfaced two signal files
(`notification_signals.py`, `social_signals.py`) that stale
project knowledge had missed. Without the rule, the 168-D
models split would have shipped with broken signal handlers.
Generalises rule #8 (read files in full) by making the
"current state" condition explicit before reading begins.

#### 11. Cloudinary video preload warning observation
On prompt detail pages with videos, browsers emit a console
warning that a preloaded video URL was not used within the
load event. Likely cause: incorrect `as=` attribute on
`<link rel="preload">` or video rendered inside a lazy-loaded
modal. Tracked as a non-blocking observation; not a memory
rule that fires preventatively but a reminder that this
specific console warning is **expected behavior under
investigation**, not a regression introduced by recent work.

**Rationale:** First observed during the 168-D smoke test;
rule serves as a noise filter so future sessions don't
repeatedly investigate the same warning as a new bug.
Resolution is deferred until the Cloudinary `featured_image`/
`featured_video` CharField migration ships (Phase REP P2
item).

#### 12. tasks.py refactor postmortem reference
If Mateo or any session raises the question of refactoring
`prompts/tasks.py`, Claude first checks
`docs/POSTMORTEM_168_E_TASKS_SPLIT.md` Section 10 (threshold
conditions) before suggesting any approach. The 168-E split
attempt was abandoned because `@patch` mock semantics fail
to propagate across submodule boundaries, yielding only ~4%
file-size reduction. Re-attempt requires one of the
threshold conditions in Section 10 to be met — Claude does
not propose alternative approaches (function-level
extraction, decorator wrappers, AST rewriting, etc.) without
explicitly checking the postmortem first.

**Rationale:** Without this rule, future sessions would
likely re-derive and re-attempt the same refactor pattern
that already failed. The postmortem captures hours of
investigation; ignoring it wastes that work.

#### 13. Silent-fallback observability rule
Any safe-fallback code path that writes data (sentinel
values, retry-with-default, "other" tags, exception swallows
returning a default) MUST emit `logger.warning` at the
fallback branch with structured fields identifying what
information was missing (`provider`, `model_name`, `job_id`,
etc.). Silent fallbacks that succeed without observability
are forbidden — they make production drift invisible.

**Rationale:** Established in Session 162-E (narrowing
`except Exception` around provider-registry cost lookup with
`logger.warning`) and reinforced in Session 169-B (the
`_resolve_ai_generator_slug` helper's fallback to `'other'`).
Without operator-side drift signals, missing registry
entries silently corrupt downstream data — exactly the
production 500 pattern that 169-B resolved. The
`/prompts/other/` page was added in 169-C as defensive
infrastructure for this fallback; the `logger.warning` is
the signal that makes the defensive path *observable*.
Codified as CC_SPEC_TEMPLATE Critical Reminder #10 in this
spec.

#### 14. REPORT Section 9 closing checklist
Every code spec's REPORT Section 9 (How to Test) must include
a "closing checklist" with at minimum: (a) migrations to apply,
(b) manual browser tests grouped max 2-at-a-time (with explicit
confirmation between each), (c) failure modes to watch for,
(d) backward-compatibility verification steps. Empty subsections
use "N/A — [reason]" rather than omission. Applies to every
code spec, not just feature specs.

**Rationale:** Established Session 170-B during the kickoff
discussion with Mateo. The closing-checklist pattern moves
post-deploy verification from ad-hoc-recall to a structured,
repeatable Round-of-2 sequence that limits cognitive load and
prevents skipped verification steps. Documented in MEMORY.md
on 2026-04-26 as Rule #14.

#### 15. Cluster shape disclosure
Every multi-spec cluster discloses its shape — BATCHED,
SEQUENTIAL, or BATCHED-WITH-PRIOR-INVESTIGATION — in the
session's run instructions AND in each spec's Critical
Reminders. Each spec's REPORT Section 7/11 mentions the
cluster shape so future readers can understand the
inter-spec dependencies and decision sequencing.

**Rationale:** Established Session 171 during the run-instructions
draft. Cluster shape is structural information that decides
spec ordering, full-suite-gate placement, and commit
sequencing. Without explicit disclosure, future readers
have to re-derive the cluster's nature from indirect signals
(commit messages, agent rounds). The 171 cluster is the
first to use BATCHED-WITH-PRIOR-INVESTIGATION — the
investigation-then-batched-fix pattern that produced
171-INV → 171-A/B/C/D as a coherent unit. The shape is
significant precedent: investigation-first eliminates
unknown-unknowns going into the implementation specs and
becomes a strong default for any cluster where regressions
have ambiguous root causes.

#### 16. Surface deferred backlog at session start

At the start of every cluster-planning conversation, after
Mateo presents new asks, Claude reads CLAUDE.md's Deferred P2
backlog and surfaces relevant items: "Before we plan new work,
do any of these deferred items belong in this cluster?"
Forces explicit consideration of accumulated deferred items
rather than silent accumulation.

**Rationale:** Established 2026-05-01 (Session 173-D). The
171-D and 172-D placeholder pattern (`Commit pending. Agent avg
pending.` left stale across sessions until 173-D backfilled
them) revealed that deferred items can sit in CLAUDE.md
forever without anyone explicitly considering them at planning
time. Without an explicit prompt, the safe default is "skip,
plan new work" — which silently accumulates technical debt.
The rule's prompt makes the consideration cost-free and routine.

**How to apply:** Read the Deferred P2 section before drafting
any cluster spec. For each deferred item, ask: "Does the new
asks include this?" If yes, fold it into the cluster scope. If
no, explicitly note in the cluster's run instructions that the
item was considered and deferred (with reason). Documented
example: Session 173 cluster Section 2 "Items NOT in this
cluster" — modal persistence on bulk publish refresh, IMAGE_COST_MAP
restructure, full policy docs all explicitly considered and
deferred.

#### 17. Docs spec self-reference backfill

Every docs spec includes a follow-up working-tree edit (after
the docs commit lands) that backfills the spec's own commit
hash and final agent scores into the just-committed docs file.
The backfill edit is committed as a separate small commit
immediately after the docs commit. Solves the recurring "Commit
pending. Agent avg pending." pattern.

**Rationale:** Established 2026-05-01 (Session 173-D). This
pattern affected Sessions 171-D and 172-D — both shipped with
their own placeholder text uncommitted, requiring 173-D to
backfill them. The "I commit a docs change that says 'commit
pending'" pattern is structurally awkward — the commit
documenting the work doesn't reference itself. A two-commit
shape (1: docs commit; 2: tiny backfill commit referencing the
hash from commit 1) breaks the chicken-and-egg. The backfill
commit is small (2-3 line edits across CLAUDE.md +
CLAUDE_CHANGELOG.md), low-risk, and serves as proof of the
rule in action.

**How to apply:** After the docs commit lands, run `git log -1
--format='%h' HEAD` to get the hash. Edit CLAUDE.md (the
relevant Recently Completed row) and CLAUDE_CHANGELOG.md (the
relevant entry heading + agent ratings line) to replace
`Commit pending. Agent avg pending.` with the real hash + real
average. Commit as a separate small commit immediately. Commit
message format: `docs: backfill <session>-D self-reference
(Memory Rule #17 application)`.

### Three-criteria framework for future memory additions

A memory edit earns a slot if it meets at least one of:

1. **Prevents a failure mode that has already occurred** (not
   hypothetical)
2. **Captures a consistently-stated preference** (not inferred
   from limited evidence)
3. **Formalizes a cadence or protocol that silent drift would
   erode** (not a one-time rule)

Edits that don't meet any criterion become noise: they fire
every conversation while providing no marginal value, and they
contribute to the "running with hand brakes partially engaged"
cognitive overhead.

### Deferred memory candidates

The following candidates were considered during the Session
167-A discussion but did not meet the three-criteria framework
above strongly enough to warrant a slot. Documented so future
additions are deliberate, not re-derived.

| Candidate | Status | Reason for deferral |
|---|---|---|
| SSRF guards on outbound requests | Deferred | Already practiced naturally; no incident history. Add if a future spec introduces a new outbound path without guards |
| User-content sanitization at rendering boundaries | Deferred | Django auto-escape + `bleach` for Quill HTML provide most protection today; explicit memory rule would reinforce but is not currently preventing a known failure. Add if a future spec introduces a new user-content rendering surface |
| Double security-agent review for security-primary specs | Deferred (relocated) | Will be codified in CC_SPEC_TEMPLATE.md instead — one-time edit, no recurring token cost |
| Default to higher-rigor path / flag shortcuts | Deferred | Intrinsic to Claude's engagement style with Mateo. Memorizing risks mechanical application |
| Proactive docs catch-up cadence every 3–5 sessions | Deferred (relocated) | Will be added to CLAUDE.md Quick Start Checklist in a future spec. Placement there has same enforcement power at zero recurring cost |
| Pre-commit commit-message factual verification | Deferred | Good habit but niche firing; can add if incident occurs |
| Diagnostic-by-evidence vs. pattern-match discipline | Deferred | Overlaps with rule #8 (read target files in full); effectively subsumed |
| Test count tracking as health signal | Deferred | Low firing frequency; specialized. Add if a session surfaces test regression |
| Context-switch discipline between tracks | Deferred | Covered naturally when Claude is being careful; memorizing adds noise |
| Active listening for process hints | Deferred | Meta-habit that should be intrinsic. Memorizing risks mechanizing it |
| Confidence-level flagging for low-evidence claims | Deferred | Part of honest engagement; intrinsic rather than rule-based |
| Recognize when out of depth and say so | Deferred | Same as above — intrinsic |
| Explicit trade-off framing on option presentation | Deferred | Can revisit if Claude reverts to neutral-menu option presentation |

### How to add, remove, or modify memory rules

Memory edits are managed via Claude's `memory_user_edits` tool
(invoked during conversation, not via CLAUDE.md). To request a
change:

- **Add:** Describe the proposed rule with rationale. Claude
  will evaluate using the three-criteria framework above,
  propose final wording, and action via `memory_user_edits` on
  confirmation
- **Remove:** Reference the slot number or the rule content;
  Claude will confirm and remove
- **Modify:** Describe the current rule and the desired change;
  Claude will propose revised wording and replace

After any change, update this section of CLAUDE.md via a new
spec. Memory changes without doc updates create drift between
actual Claude behavior and documented expectations.

### Token cost trade-off

With 17 active memory edits, the per-message token overhead is
approximately 2,500–3,400 tokens. For a typical 40-message
session, that's 100,000–136,000 extra tokens of context processed
over the session's lifetime.

At current pricing, this adds roughly $0.50–$1.65 per session
beyond the baseline. Over 20 sessions per month, $10–$33 of
additional cost.

This cost is justified if the memory edits prevent even one
incident requiring credential rotation, recovery from a
production issue, or a wasted spec cycle. The April 2026
incidents each consumed hours of real-time recovery work —
incident cost vastly exceeds memory-edit token cost.

### Related safeguards (non-memory)

Memory is one tool among several for enforcing consistent
behavior. Related safeguards live in other files:

- **env.py safety gate:** Session 163 v2 protocol. Mandatory
  in every code-touching CC spec
- **Heroku release phase:** Session 165-A. Auto-applies
  migrations before web dynos start serving traffic
- **No-migrate-by-CC rule:** Session 163 v2 protocol. CC never
  runs `python manage.py migrate`
- **Fernet-encrypted BYOK storage:** Pre-existing. BYOK API
  keys encrypted at rest
- **SSRF guards (`social_avatar_capture.py`):** Session 163-D.
  Canonical pattern for outbound HTTP to user-supplied URLs
- **`_sanitise_error_message` security boundary:** Pre-existing
  pattern defined in `prompts/services/bulk_generation.py`,
  imported locally in `tasks.py` to avoid circular import
  (see CLAUDE.md line 537 for the circular-import note). Prevents
  error-message data leaks to users
- **6-agent minimum code spec review** (2-minimum for docs):
  `CC_COMMUNICATION_PROTOCOL.md` / `CC_SPEC_TEMPLATE.md` v2.7
- **v2.7 spec format:** STOP banners, DO/DO NOT lists, exact
  response tables — enforcement mechanisms built into the spec
  template itself

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

JAVASCRIPT — Input page (5 modules — window.BulkGenInput namespace):
static/js/bulk-generator.js            725 lines  (main IIFE — form UI, prompt boxes, DOM init)
static/js/bulk-generator-generation.js 625 lines  (API key validation, modals, generation flow)
static/js/bulk-generator-autosave.js   376 lines  (reference image upload, auto-save to localStorage)
static/js/bulk-generator-utils.js      89 lines   (BulkGenUtils — URL validation, paste helpers)
static/js/bulk-generator-paste.js      78 lines   (BulkGenPaste — clipboard paste upload)

JAVASCRIPT — Job page (5 modules — window.BulkGen namespace):
static/js/bulk-generator-config.js     156 lines  (BulkGen namespace + config object)
static/js/bulk-generator-ui.js         338 lines  (gallery render, createGroupRow, parseGroupSize)
static/js/bulk-generator-gallery.js    452 lines  (card states, fillImageSlot, fillFailedSlot, lightbox)
static/js/bulk-generator-polling.js    ~408 lines (status API polling loop)
static/js/bulk-generator-selection.js  581 lines  (image selection, publish bar)

CC safety threshold: 780 lines per file.
All modules well below threshold after Session 143 split.

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

### CSS directory convention

`static/css/` has three subdirectories with distinct roles:

- **`partials/`** — Core site styles split by theme (design tokens, components, trash, collections). Imported by `style.css` via `@import` (Session 168-C).
- **`components/`** — Shared UI components with their own scope (e.g., `profile-tabs.css`). Included on specific pages that need them.
- **`pages/`** — Page-scoped styles (e.g., `bulk-generator.css`). Included only on the page they style.

Adding new CSS: if it's a shared base style, extend the relevant `partials/` file. If it's a reusable component, add to `components/`. If it's page-specific, add to `pages/`.

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

### Profanity filter word list — April 2026 policy decisions

Several words were manually deactivated in the ProfanityWord
admin panel (`/admin/prompts/profanityword/`) in April 2026
because they blocked legitimate artistic/fashion/fantasy prompts:

- **Occultic / fantasy vocabulary (deactivated):** demon,
  demonic, demons, devil, devilish, devils, hellfire, satan,
  satanic, satanism, occult, occultism, pentagram, baphomet,
  beelzebub, antichrist, lucifer. Standard in artistic / fantasy
  AI prompts, not genuinely offensive in context
- **Anatomical terms (reviewed, kept or deactivated case-by-case):**
  vagina, vulva — clinical medical terms acceptable in artistic
  prompts; slut, whore, bitch — previously reviewed, handling
  varies by context
- **High-severity sexual slurs and violence words retained**

If re-adding or auditing this list, this is the rationale for
why those words are not blocking. Manage the list at
`/admin/prompts/profanityword/`.

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

### Planned Feature Architecture — QUOTA Alerts + P2-B/C Surfaces

The following architecture was designed in Session 142/143. Do not rebuild from
scratch — implement exactly as documented here.

---

**QUOTA-1 — Quota Exhaustion Error Message + Bell Notification**
*(Completed: Session 143, migration 0077, commit 98fc1aa)*

| Layer | Change |
|-------|--------|
| `prompts/services/image_providers/openai_provider.py` | In `RateLimitError` handler, check for `'insufficient_quota'` in error body or `e.code == 'insufficient_quota'`. If quota: return `error_type='quota'`, `error_message='Quota exceeded'` (distinct string — NOT the existing `'Rate limit reached'` message). If not quota: keep existing `error_type='rate_limit'` path unchanged. |
| `bulk_generation.py` — `_sanitise_error_message()` | Split `'quota'` keyword out of rate-limit check into its own `'Quota exceeded'` return value. Must appear BEFORE the `'rate limit'` check in the if/elif chain to prevent masking. |
| `static/js/bulk-generator-config.js` — `_getReadableErrorReason()` | Map `'Quota exceeded'` → `"Failed. API quota exceeded — contact admin."` |
| `prompts/models.py` | Add `openai_quota_alert` to `NOTIFICATION_TYPES` |
| New migration | For the notification type addition |
| `prompts/tasks.py` | When quota error kills a job, fire `openai_quota_alert` bell notification to job owner using existing `_fire_bulk_gen_job_notification()` pattern |
| `prompts/tests/` | 2–3 new tests: quota sanitiser maps correctly, notification fires on quota kill, quota does NOT retry |

**⚠️ IMPORTANT — quota vs rate_limit routing in `openai_provider.py`:**
OpenAI raises `RateLimitError` for BOTH true rate limits AND quota exhaustion.
The current code retries ALL `RateLimitError` with exponential backoff (30s→60s→120s).
Quota exhaustion MUST NOT retry — same key, same balance, same result.
Step 0 grep must verify current `RateLimitError` handling before any changes.
Distinguish by: `error.code == 'insufficient_quota'` or `'quota' in str(error).lower()`.

---

**QUOTA-2 — Low Spend-Rate Warning Notification**
*(Planned: Session 144, ~1 spec)*

Design: Spend-rate alert (not true balance check — BYOK keys have no balance API).
Fires inline after each job completes (not a scheduled task).

| Component | Detail |
|-----------|--------|
| Trigger | After every job finalisation, check cumulative spend |
| Calculation | `BulkGenerationJob.objects.filter(user=job.user, created_at__gte=30_days_ago).aggregate(total=Sum('total_cost'))` |
| Threshold | `settings.OPENAI_SPEND_WARNING_THRESHOLD` (env var, default `10.00` USD) |
| New notification type | `openai_quota_warning` |
| Deduplication | Max 1 warning per user per 7 days (use notification duplicate prevention — 60s window exists, extend to 7 days for this type) |
| Message | "You've spent $X on OpenAI in the last 30 days. If your balance is running low, top it up to avoid job failures." |
| New env var | `OPENAI_SPEND_WARNING_THRESHOLD=10.00` in `settings.py` + Heroku config |
| Location | New `_check_and_warn_quota(job)` helper in `prompts/tasks.py`, called from job finalisation |

**Note:** QUOTA-2 gives early warning before QUOTA-1 fires. Together they close the
"blind until the job fails" gap.

---

**P2-B — Admin Log Tab**
*(Planned: Session 145, requires its own planning session before spec writing)*

Status: Currently a "Coming soon" placeholder in `system_notifications.html`.
The tab URL is: `/admin-tools/system-notifications/?tab=admin-log`

Design questions to resolve before spec:
1. Use existing `Notification` model filtered to `notification_type=system` (simpler,
   no new model) OR new `AdminEvent` model (more structured, filterable by event_type)?
   **Recommended:** New `AdminEvent` model — notifications are user-facing, admin events
   are operational. Mixing them in one table creates query complexity.
2. Initial events to surface (P1): quota exhaustion, job failures (entire job),
   B2 cleanup run outcomes, orphan detection results
3. Tab UI: Reverse-chronological feed with event-type filter pills. Show: timestamp,
   event type badge, summary text, user (if applicable), link to related object.
4. Auth: Staff-only (`@staff_member_required` or equivalent JSON-safe check).
5. Pagination: Standard cursor-based (existing pattern in project).

**DO NOT build P2-B without a dedicated planning session first.**
The data model decision (notification vs AdminEvent) has long-term consequences.

---

**P2-C — Web Pulse Tab**
*(Planned: Session 146+, requires its own planning session)*

Status: Currently a "Coming soon" placeholder in `system_notifications.html`.
The tab URL is: `/admin-tools/system-notifications/?tab=web-pulse`

Scope TBD — requires its own design session. Likely includes:
site-wide traffic/activity snapshot, recent signups, bulk gen job volume,
error rate summary. Do not spec until P2-B is complete.

---

### Section D — Generation Retry + Finalisation Sweep + Rate Limit Compliance

> See also: Section A (Bulk Job Deletion — in "Recommended Build Sequence" above),
> Section B (`detect_b2_orphans` — completed Session 123),
> Section C (Admin Operational Notifications — above this section).

> **Status:** D1 ✅ (Session 143), D3 ✅ (Session 143), D4 ✅ (Session 145), D2 ✅ (already built — Phase 5C).
> D2 `_run_generation_with_retry()` already implements exponential backoff retry (30s→60s→120s, max 3).
> Capture date: Session 145 (March 29, 2026). D1+D3 deployed March 26, 2026. D4 deployed March 29, 2026.

#### The Problem

Production testing with 13 prompts revealed three related generation integrity issues:
1. Images silently left in `pending` status after job completion (not counted as failed)
2. No retry for transient failures at the generation level (rate limit, server error)
3. `BULK_GEN_MAX_CONCURRENT=4` dispatches ~16 images/minute against Tier 1's 5/min limit

#### D1 — Pending-After-Completion Finalisation Sweep

After `ThreadPoolExecutor` completes (on ANY exit path — success, exception, quota, cancel),
add a sweep step:

```python
# After generation loop exits
pending_images = job.images.filter(status='pending')
if pending_images.exists():
    pending_images.update(
        status='failed',
        error_message='Not generated — job ended unexpectedly'
    )
    # Recalculate failed_count from DB (not from incremental F() counter which may be stale)
    job.failed_count = job.images.filter(status='failed').count()
    job.save(update_fields=['failed_count'])
```

This ensures `failed_count` always reflects reality and users see accurate failure stats.

**IMPORTANT:** Implement D1 before D2 — retry logic depends on accurate `status` values.

#### D2 — Generation Retry for Transient Failures

After the primary generation loop AND the D1 sweep, add a single retry pass:

- **Retry if:** `error_type` is `rate_limit` or `server_error`
- **Never retry if:** `error_type` is `content_policy`, `auth`, or `quota`
- **Max retries:** 1 per image at this level (provider already retries 3× internally)
- **Delay before retry:** 30 seconds flat (not exponential — this is a one-shot pass)
- **After retry:** Re-run D1 sweep to catch any remaining pending records

This is the "generation retry" explicitly deferred in Phase 5D due to insufficient frequency
data. The 4/13 failure rate (30%) in Session 143 testing justifies the complexity.

**DO NOT build D2 without D1 complete first.**

#### D3 — Rate Limit Compliance Audit + Tier-Aware Configuration

OpenAI rate limits are per API key tier, not just per request. Current config violates Tier 1.

| Tier | Limit | Safe `max_workers` | Recommended inter-batch delay |
|------|-------|-------------------|-------------------------------|
| Tier 1 | 5 img/min | 1 | 12s between images |
| Tier 2 | 20 img/min | 2 | 3s between images |
| Tier 3 | 50 img/min | 4 | 1s between images |
| Tier 4+ | 150 img/min | 8 | 0s (no delay needed) |

*Values aligned with `TIER_RATE_LIMITS` in `openai_provider.py`.*

**Implementation:** Add `OPENAI_TIER` env var (default: `1`). On task startup, read tier and
set `max_workers` + `inter_image_delay` accordingly:

```python
TIER_CONFIG = {
    1: {'max_workers': 1, 'inter_image_delay': 12},
    2: {'max_workers': 2, 'inter_image_delay': 3},
    3: {'max_workers': 4, 'inter_image_delay': 1},
    4: {'max_workers': 8, 'inter_image_delay': 0},
}
tier = int(getattr(settings, 'OPENAI_TIER', 1))
config = TIER_CONFIG.get(tier, TIER_CONFIG[1])
```

This replaces the raw `BULK_GEN_MAX_CONCURRENT` env var. If `BULK_GEN_MAX_CONCURRENT` is also
set, it acts as a hard override on `max_workers` (takes precedence over the tier default).
`OPENAI_TIER` sets the recommended config; `BULK_GEN_MAX_CONCURRENT` lets operators clamp it
lower for safety.

**IMMEDIATE MITIGATION (no code deploy needed):** Set `BULK_GEN_MAX_CONCURRENT=1`
in Heroku config vars until D3 is built.

#### D4 — Per-Job Rate Limiting (Session 145)

`BulkGenerationJob.openai_tier` (PositiveSmallIntegerField, default=1) stores
the user's declared OpenAI tier. `_TIER_RATE_PARAMS` (local dict inside
`_run_generation_loop()` in `tasks.py`) maps `(tier, quality)` to
`(max_concurrent, inter_batch_delay)`. Lookup falls back to
`_DEFAULT_RATE_PARAMS = (1, 3)` for unrecognised tier or quality values.

**Rate parameter table:**
| Tier | Images/min | Low quality | Medium quality | High quality |
|------|-----------|-------------|----------------|--------------|
| 1 | 5 | (1, 3s) | (1, 0s) | (1, 0s) |
| 2 | 20 | (2, 3s) | (2, 0s) | (2, 0s) |
| 3 | 50 | (4, 0s) | (4, 0s) | (4, 0s) |
| 4 | 150 | (8, 0s) | (8, 0s) | (8, 0s) |
| 5 | 250 | (10, 0s) | (10, 0s) | (10, 0s) |

Format: (max_concurrent, inter_batch_delay)

**Global override:** `BULK_GEN_MAX_CONCURRENT` acts as a ceiling on concurrency —
per-job params from `_TIER_RATE_PARAMS` take precedence when lower.
`OPENAI_INTER_BATCH_DELAY` is deprecated (Session 146) and has no effect.
Use `BULK_GEN_MAX_CONCURRENT` for emergency throttling without a code deploy.

**Tier auto-detection (future):** `client.models.list()` does not return
image-specific rate limit headers. Auto-detection requires a real image call
(costs money). User-declared tier is the chosen approach for now.

#### Build Order

```
D1 (pending sweep) → must be first, fixes billing integrity
D3 (rate limit config) → can be built alongside D1
D2 (generation retry) → only after D1 is deployed and verified
```

#### Files That Will Need Changes

| File | Change | Risk Tier |
|------|--------|-----------|
| `prompts/tasks.py` | D1 sweep + D2 retry pass in generation loop | 🔴 Critical |
| `settings.py` | `OPENAI_TIER` env var | ✅ Safe |
| `prompts/services/bulk_generation.py` | Tier-aware `max_workers` + delay config | ✅ Safe |
| Heroku config | `OPENAI_TIER=1`, `BULK_GEN_MAX_CONCURRENT=1` | Manual step |

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
| `docs/POSTMORTEM_168_E_TASKS_SPLIT.md` | Architectural postmortem of the abandoned tasks.py modular split (Session 168-E). Documents what was attempted, why it failed, candidate solutions, investigations to perform first, and threshold conditions for any future revisit. |
| `archive/` (all contents) | **Historical materials.** Contains `changelog-sessions-13-99.md` (CLAUDE_CHANGELOG entries for Sessions 13 through 99, archived in Session 168-B), `PHASE_N4_UPLOAD_FLOW_REPORT.md` (completion report for the N4 upload flow, moved from `docs/` in Session 168-B), plus older archived specs and protocols. Reach for archive contents when answering "why was X done that way?" about pre-Session-100 work. Most sessions do not need to consult the archive. |

---

## ✅ Quick Start Checklist for New Sessions

1. ☐ Read this document for overall context
2. ☐ Check **CLAUDE_PHASES.md** for current phase details and unfinished work
3. ☐ Check **CLAUDE_CHANGELOG.md** for what was done in recent sessions
4. ☐ **Archives exist but are not usually required.** If you need to understand a decision made before Session 100, see `archive/changelog-sessions-13-99.md`. For day-to-day work, CLAUDE.md + CLAUDE_PHASES.md + active CLAUDE_CHANGELOG.md cover ~80-90% of needs.
5. ☐ Before running any migration commands: verify env.py safety gate (`grep -n DATABASE_URL env.py` — must show the `os.environ.setdefault("DATABASE_URL", ...)` line as commented out; second command `python -c "import os; import env; print(os.environ.get('DATABASE_URL','NOT SET'))"` must print `NOT SET`). This gate is mandatory in every CC code spec post-2026-04-19 incident.
6. ☐ Create micro-specs (not big specs) for any new work
7. ☐ Get 8+/10 agent ratings before committing
8. ☐ Don't let CC edit files > 1000 lines
9. ☐ Update CLAUDE_CHANGELOG.md at end of session

---

**Version:** 4.73 (Session 173-F SINGLE-SPEC cluster — NSFW chip redesign + Tier 2 architectural fix + report-to-admin mailto stub + seed restoration deferred. **5 folded items, single commit.** (1) Chip stacked layout: large gray icon over red "Content blocked" pill over body copy with two inline links — closes 173-C deferred preference; only content_policy variant gets stacked, others stay inline (intentional asymmetry). (2) Block source distinction: backend `block_source: 'preflight' \| 'provider'` threaded through validate response + polling response; frontend chip body copy varies — Memory Rule #13 silent-fallback to provider-side wording. (3) Tier 2 architectural fix: legacy `check_text` `_load_word_list` was loading ALL active words regardless of `block_scope`, so Tier 1 universal always caught advisory words first — Tier 2 NEVER fired in production despite 173-B/E shipping the pipeline. Fixed by filtering `block_scope='universal'`. Required for Mateo's headline activation test. (4) Report-to-admin mailto stub: "Let us know" link with auto-populated mailto, new `CONTENT_BLOCK_REPORT_EMAIL` Django setting (env-overridable), surfaced via `data-content-block-report-email` template attribute. Full backend deferred to Session 175. (5) **Seed restoration BLOCKED at harness permission layer** despite spec authorization — Mateo runs `heroku run python manage.py seed_provider_advisory_keywords` manually post-deploy to restore 11 advisory keywords accidentally deleted from admin UI. Activation test deferred until seed restored. 3 new tests on validate endpoint. **Cluster shape:** SINGLE-SPEC. **Memory Rules:** #16 (3 deferred items closed) + #17 (single-commit pattern) + #13 (silent fallback) + #14 (closing checklist). Commit pending — see git log for hash. 1414 tests.)
// Prior version footer (4.72, Session 173-E) preserved for traceability:
// 4.72 (Session 173-E SINGLE-SPEC follow-on cluster — frontend wire-up of `model_identifier` in `api_validate_prompts` POST body. Activates 173-B Tier 2 advisory pre-flight in production. Closes REPORT_173_B Section 5 P2 deferred item per Memory Rule #16. Step 0 finding: backend wire-up was ALREADY DONE in 173-B; only frontend gap remained. 1411 tests.)
// Prior version footer (4.71, Session 173 main cluster) preserved below for historical reference:
// 4.71 (Session 173 cluster — HYBRID with prior-session evidence capture. 173-A `369b2a0` avg 9.35/10 (per-card "Use master" reset bugs + xai keyword rename). 173-B `e06ab5c` avg 8.92/10 (NSFW pre-flight v1). 173-C `bef3115` avg 9.225/10 (alert-circle chip icon + placeholder content policy page). 173-D `474b308` avg 9.0/10 (docs update + 171-D/172-D backfills + Memory Rules #16/#17 + Session 175 plan section). Memory Rules 15 → 17 of 30. 1408 tests.)
**Last Updated:** May 1, 2026
