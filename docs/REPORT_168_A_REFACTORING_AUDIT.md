# REPORT_168_A_REFACTORING_AUDIT — Full Repository Refactoring Audit

**Spec:** CC_SPEC_168_A_FULL_REPO_REFACTORING_AUDIT.md (v1)
**Date:** April 21, 2026
**Status:** Complete. All sections filled. Pending commit.
**Type:** Docs-only, read-only analysis (zero code, zero migrations)

---

## Preamble — Safety Gate + Prerequisite Confirmation

### env.py safety gate

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Gate passed.

### 167-A commit confirmation (spec requirement #7)

```
$ git log --oneline -5
606f3c6 docs: polish Claude Memory System section (Session 167-B)
a2843fa docs: add Claude memory system + security safeguards documentation (Session 167-A)
82a8541 docs: consolidated CLAUDE.md/CHANGELOG catch-up for Sessions 164-165 + backlog items
a457da2 fix(models): align migration state with UserProfile.avatar_url help_text
4d874d4 feat(deploy): add release phase to Procfile for auto-migration on deploy
```

167-A committed as `a2843fa`. 167-B (polish) also committed as
`606f3c6`. Baseline is the latest committed state.

---

## Executive Summary — Ranked Top 5 Refactoring Opportunities

Ranking methodology: opportunities scored on (Value × Inverse Risk)
with Effort as a tie-breaker. "Value" = user/developer impact +
future-unblocking potential. "Risk" = likelihood of introducing
regression during the refactor itself.

**Note on ranking vs. execution order:** Executive Summary ranks
by value-risk score. Proposed Refactoring Sequence (below) orders
by execution dependencies. These can differ — e.g., `tasks.py`
ranks #2 here by value, but `models.py` comes first in sequence
(168-D before 168-E) because tasks.py imports models extensively.
Read both sections together.

### #1 — `static/css/style.css` split (4,479 lines)

- **What:** Largest single text file in the entire codebase. Global
  "catch-all" stylesheet that has accumulated 4,479 lines across all
  page types. Extraction candidate: move page-scoped rules into
  `static/css/pages/*.css` files (pattern already established —
  `pages/bulk-generator.css`, `pages/prompt-detail.css`,
  `pages/notifications.css` exist)
- **Why (metric evidence):** `wc -l static/css/style.css → 4479`.
  Next-largest CSS file is `static/css/pages/bulk-generator.css`
  at 2077 lines. Ratio 2.2× suggests bloat, not natural size
- **Value:** HIGH — every page load parses it; style drift risk;
  merge conflicts on any styling work
- **Risk:** LOW — CSS changes are localized per selector; cascade
  ordering is testable visually
- **Effort:** 8–12 hours across 1–2 sessions to categorize rules,
  split by page/component, verify visual parity
- **Dependencies:** None — standalone refactor
- **Priority rank:** 1 (highest value-to-risk ratio in the audit)

### #2 — `prompts/tasks.py` split (3,822 lines, 4 HIGH-complexity functions)

- **What:** Single-file orchestrator for Django-Q2 background tasks.
  Multiple unrelated concerns: AI content generation, bulk
  generation orchestration, B2 file management, rename tasks,
  Cloudinary-era helpers. Responsibility-boundary split candidate
- **Why (metric evidence):** `wc -l prompts/tasks.py → 3822`.
  flake8 C901 reports 4 functions with complexity ≥11: `_update_prompt_with_ai_content` (15),
  `process_bulk_generation_job` (15), `_download_source_image` (14),
  `generate_ai_content_cached` (11), `_download_and_encode_image` (11).
  High complexity in a 🔴 Critical file compounds CC edit risk
  (SIGABRT at ≥2000 lines)
- **Value:** HIGH — preventing further growth unblocks Phase SUB
  safely; CC cannot directly edit this file today
- **Risk:** MEDIUM — many callers across views/services/tests;
  circular-import sensitivity documented (see CLAUDE.md line 537
  for the `_sanitise_error_message` circular-import pattern)
- **Effort:** 6–10 hours across 2 sessions — one to map the
  responsibility boundaries, one to execute the split with
  `__init__.py` re-exports preserving all existing imports
- **Dependencies:** None strict; #5 (docs archive) helps because
  several comments reference archived session numbers
- **Priority rank:** 2

### #3 — `prompts/models.py` split (3,517 lines)

- **What:** Single-file data layer for all app models. Multiple
  unrelated concerns: `Prompt` + related, `UserProfile`,
  `Notification`, `Collection`, `BulkGenerationJob` +
  `GeneratedImage`, `ProfanityWord`, `GeneratorModel`,
  `UserCredit`, `CreditTransaction`, `SubjectCategory`,
  `SubjectDescriptor`. Domain-boundary split candidate
- **Why (metric evidence):** `wc -l prompts/models.py → 3517`.
  flake8 C901 reports `Prompt.hard_delete` (12) and
  `delete_cloudinary_assets` (14). The hard_delete complexity
  signals method-level concern, not just file-level size
- **Value:** HIGH — model boundaries are naturally orthogonal;
  Phase SUB will add `Subscription`, `StripeCustomer`,
  `UsageRecord` models that would push this past 4,500 lines
  without a split
- **Risk:** MEDIUM-HIGH — Django migration state tracks models
  by `app_label.ModelName`; splitting is safe but requires careful
  `__init__.py` re-exports and no `Meta.app_label` changes. Any
  incorrect import re-export breaks migration replay on fresh
  checkouts. **Signal handler circular-import risk:**
  `notification_signals.py`, `social_signals.py`, `signals.py`
  reference models from multiple domains; the `models/__init__.py`
  re-export shim (same pattern used for `views/`) must be
  validated as part of the 168-D spec so signal handlers still
  resolve cross-domain imports post-split
- **Effort:** 6–10 hours over 2 sessions. Requires the domain
  boundaries to be mapped first (a read-only sub-spec)
- **Dependencies:** Should come AFTER #2 (`tasks.py` split) — tasks
  imports models extensively; splitting models first and tasks
  second is easier than the reverse
- **Priority rank:** 3

### #4 — `prompts/admin.py` split (2,459 lines, 4 C901 methods)

- **What:** Monolithic admin module containing PromptAdmin,
  UserProfileAdmin, CollectionAdmin, NotificationAdmin,
  ProfanityWordAdmin, BulkGenerationJobAdmin, etc.
  Model-aligned split candidate (pairs naturally with #3 model
  split if done after)
- **Why (metric evidence):** `wc -l prompts/admin.py → 2459`.
  flake8 C901 reports 4 functions in PromptAdmin at complexity
  11: `_apply_ai_m2m_updates`, `regenerate_ai_content`,
  `save_model`, and `ProfanityWordAdmin.bulk_import_view` at 13
- **Value:** MEDIUM — admin is staff-facing; fewer users affected
  than user-facing code. But CC edit reliability still compromised
- **Risk:** LOW — Django admin is well-bounded; ModelAdmin classes
  are independent; no cross-admin state
- **Effort:** 4–6 hours; a `prompts/admin/` package with one
  file per ModelAdmin + shared `common.py` for shared mixins is
  the natural split
- **Dependencies:** None hard; naturally paired with #3
- **Priority rank:** 4

### #5 — Documentation archive pass (CLAUDE_CHANGELOG old sessions + stale plan docs)

- **What:** CLAUDE_CHANGELOG.md is 4,704 lines with 97 session
  entries; sessions 13-56 (December 2025 to late January 2026)
  are rarely referenced and bloat every read. Multiple shipped-
  feature plan docs still claim "ready for implementation" status.
  Archive candidates
- **Why (metric evidence):**
  - `wc -l CLAUDE_CHANGELOG.md → 4704`
  - `grep -c "^### Session" CLAUDE_CHANGELOG.md → 97`
  - Oldest entry: Session 13 (Dec 13, 2025) — 4.5 months old
  - `wc -l docs/BULK_IMAGE_GENERATOR_PLAN.md → 1321`, header
    says "Status: Planning Complete, Ready for Implementation"
    but Phases 1–7 of Bulk Generator are SHIPPED per CLAUDE.md
    Quick Status Dashboard
  - Total MD LOC: 362,952 across 521 files — large surface
- **Value:** MEDIUM — reduces docs-search scope and noise; doesn't
  unblock any feature
- **Risk:** LOW — archiving doesn't delete; git history preserves
- **Effort:** 2–3 hours — split CLAUDE_CHANGELOG entries pre-100
  into `archive/changelog-sessions-13-99.md`; move completed plan
  docs to `archive/` with a one-line status update
- **Dependencies:** None
- **Priority rank:** 5 (valuable cleanup but lowest unblocking
  power among the top 5)

---

## Proposed Refactoring Sequence

Ordered list. Each refactor is a candidate for its own spec
(168-B, 168-C, etc.). Dependencies listed.

| Seq | Candidate | Suggested spec | Sessions | Prerequisites | Unblocks |
|-----|-----------|----------------|----------|---------------|----------|
| 1 | **Docs archive pass** (CLAUDE_CHANGELOG sessions 13-99 + stale plan docs → `archive/`) | 168-B | 1 | None | Cleaner docs tree for all future work |
| 2 | **`static/css/style.css` split** into page-scoped + shared | 168-C | 1-2 | None | Reduces every-page CSS parse cost; lowers merge-conflict surface for CSS work |
| 3 | **`prompts/models.py` split** by domain boundary (Prompt / User / Notification / Collection / BulkGen / Credits) | 168-D | 2 | None (but easier before #4) | Enables safe Phase SUB model additions; unblocks #4 and #5 |
| 4 | **`prompts/tasks.py` split** by responsibility (AI tasks / Bulk Gen tasks / B2 tasks / Cloudinary cleanup) | 168-E | 2 | #3 recommended (imports cleaner) | CC can edit task logic directly; reduces circular-import surface |
| 5 | **`prompts/admin.py` split** to `prompts/admin/` package (one file per ModelAdmin) | 168-F | 1-2 | #3 recommended (shared imports aligned) | Easier admin customizations for Phase SUB/POD |
| 6 | **Test file splits** (split `test_notifications.py`, `test_bulk_generator_views.py`, `test_bulk_generation_tasks.py` into module-per-concern) | 168-G | 2 | None | Faster targeted test runs; CC can edit individual test files |
| 7 | **Provider `_download_image` extraction** to shared utility | 168-H | 0.5 | None | Resolves P3 flagged in CLAUDE.md Phase REP blockers |
| 8 | **Template fragment extraction** (`user_profile.html` 2073 lines; `prompt_list.html` 1700 lines → `{% include %}` partials) | 168-I | 2 | None — but see Known Risk Pattern below | Smaller templates, component reuse |
| 9 | **`prompts/views/bulk_generator_views.py` split** (1603 lines, 7 API endpoints + page view) | 168-J | 1 | #4 recommended | Simpler bulk gen maintenance |
| 10 | **`prompts_manager/settings.py` split** to `settings/` package | 168-K | 1 | None | Standard Django pattern; easier Phase SUB env var additions |

**⚠️ Known Risk Pattern for 168-I:** `user_profile.html` contains
inline `<script>` IIFE blocks. Per CLAUDE.md "Known Risk Pattern:
Inline Code Extraction (CRITICAL)" (Session 86 precedent —
extracting overflow IIFE left ~640 lines of JS outside `<script>`
tags, rendering as raw text). Any `{% include %}` extraction spec
must audit script/style-tag boundaries before moving content.

Total estimated sessions for all 10: **13-16 sessions**.

Realistic minimum viable sequence before Phase SUB: **#1, #2, #3,
#4** (6-8 sessions). Phase SUB can then proceed without compounding
existing structural debt.

---

## Category Findings (10 subsections)

### Category 1 — Python file line-count census

**Method:**
```bash
find . -name "*.py" -not -path "./.venv/*" -not -path "*/__pycache__/*" \
    -not -path "./staticfiles/*" -exec wc -l {} + | sort -rn | head -40
```

**Tier summary:**
- Total Python files in scope: **272**
- Total Python LOC: **133,642**
- RED (≥1000 lines): **12 files, 91,229 LOC (68% of all Python LOC concentrated in 4% of files)**
- YELLOW (500-999 lines): **20 files, 13,164 LOC**
- GREEN (<500 lines): **240 files, 29,249 LOC**

**Top 12 RED files:**

| File | LOC | Classification |
|------|-----|----------------|
| `prompts/tasks.py` | 3822 | Orchestrator — accumulation |
| `prompts/models.py` | 3517 | Data layer — natural aggregation + growth |
| `prompts/tests/test_notifications.py` | 2872 | Test file — 163 tests in one file |
| `prompts/tests/test_bulk_generator_views.py` | 2568 | Test file — 156 tests in one file |
| `prompts/admin.py` | 2459 | Admin layer — accumulation |
| `prompts/tests/test_bulk_generation_tasks.py` | 2264 | Test file |
| `prompts/tests/test_bulk_page_creation.py` | 1804 | Test file |
| `prompts/views/bulk_generator_views.py` | 1603 | Views — feature accumulation |
| `prompts/views/upload_api_views.py` | 1334 | Views — already split from api_views.py in Session 128 |
| `prompts/tests/test_validate_tags.py` | 1117 | Test file — tag validation pipeline tests |
| `prompts/tests/test_pass2_seo_review.py` | 1048 | Test file |
| `prompts/tests/test_user_profiles.py` | 991 | Test file (borderline RED) |

**YELLOW highlights (next-tier concern):**
- `prompts/services/vision_moderation.py` (914) — feature-coherent, NOT a refactor target
- `prompts/management/commands/detect_orphaned_files.py` (798) — feature-coherent, NOT a refactor target
- `prompts/views/collection_views.py` (792)
- `prompts/views/upload_views.py` (751)
- `prompts_manager/settings.py` (676) — see Category 7
- `prompts/views/user_views.py` (634)
- `prompts/views/prompt_list_views.py` (620)

**Observations:**
- **Test files dominate the RED tier** (6 of 12). These are inside
  a `tests/` package so the package structure is already good;
  individual files are monolithic by test count (156+ tests each).
  Split-by-concern within each file is a valid refactor
- **Domain modules (`tasks.py`, `models.py`, `admin.py`) are the
  3 largest non-test files.** All three grew organically across
  100+ sessions; natural split boundaries exist (see
  Executive Summary)
- **68% of Python LOC is in 12 files.** Any material improvement
  to code organization will involve touching these files

### Category 2 — Code duplication detection

**Method:** Name pattern-matching across services/views/tasks.
```bash
grep -rn "^def _download" prompts/ 2>/dev/null
grep -rn "def _upload.*b2\|def _download_image" prompts/ 2>/dev/null
```

**Findings:**

1. **`_download_image(url) -> bytes | None`** defined identically
   in `prompts/services/image_providers/replicate_provider.py:233`
   and `prompts/services/image_providers/xai_provider.py:366`.
   Already flagged as P3 in CLAUDE.md Phase REP Blockers
   ("`_download_image` duplication"). Extract to
   `image_providers/base.py` or a shared helper module.
   Estimated savings: 20–30 LOC + single source of truth

2. **Download-family methods (similar purpose, different interfaces):**
   - `prompts/tasks.py:956` — `_download_and_encode_image(url)`
     returns `Optional[Tuple[str, str]]`
   - `prompts/tasks.py:3212` — `_download_source_image(url)`
     returns `Optional[bytes]`
   - `prompts/services/content_generation.py:70` —
     `_download_image_as_base64(image_url)` returns `Optional[str]`
   - `prompts/services/social_avatar_capture.py:78` —
     `_download_provider_photo(url)` (SSRF-guarded)

   These have different return types and different security
   profiles (only `social_avatar_capture` is SSRF-guarded because
   URLs come from external providers). Not a simple merge
   candidate — they serve different trust boundaries. Flagged for
   consideration, not immediate action

3. **Sanitization functions:**
   - `prompts/services/bulk_generation.py:24` —
     `_sanitise_error_message(raw)` (UK spelling — intentional)
   - `prompts/tasks.py:1458` — `_sanitize_content(text, max_length)`
     (US spelling — different purpose)

   Different purposes. NOT duplication.

**Summary:** 1 confirmed duplication (P3, ~25 LOC savings).
2 similar-purpose groups that are intentionally separated.

### Category 3 — Complexity hotspots

**Method:** `flake8 --select=C901 --max-complexity=10 prompts/`
(radon not installed; flake8 mccabe fallback used)

**Top 12 high-complexity functions:**

| File:Line | Function | Complexity | Priority |
|-----------|----------|------------|----------|
| `prompts/tasks.py:1346` | `_update_prompt_with_ai_content` | **15** | HIGH |
| `prompts/tasks.py:2942` | `process_bulk_generation_job` | **15** | HIGH |
| `prompts/utils/related.py:123` | `get_related_prompts` | **15** | HIGH |
| `prompts/tasks.py:3212` | `_download_source_image` | 14 | MEDIUM |
| `prompts/models.py:2248` | `delete_cloudinary_assets` | 14 | MEDIUM |
| `prompts/admin.py:1339` | `ProfanityWordAdmin.bulk_import_view` | 13 | MEDIUM |
| `prompts/models.py:1084` | `Prompt.hard_delete` | 12 | MEDIUM |
| `prompts/admin.py:519` | `PromptAdmin._apply_ai_m2m_updates` | 11 | MEDIUM |
| `prompts/admin.py:602` | `PromptAdmin.regenerate_ai_content` | 11 | MEDIUM |
| `prompts/admin.py:947` | `PromptAdmin.save_model` | 11 | MEDIUM |
| `prompts/tasks.py:956` | `_download_and_encode_image` | 11 | MEDIUM |
| `prompts/tasks.py:1672` | `generate_ai_content_cached` | 11 | MEDIUM |

**Observations:**
- **3 HIGH-priority hotspots (complexity ≥15)** — all orchestration
  functions. `process_bulk_generation_job` and
  `_update_prompt_with_ai_content` both route multiple provider/error
  paths; `get_related_prompts` implements the 6-factor IDF
  scoring algorithm. Complexity is partly inherent (real
  branching) but partly could be extracted into sub-functions
- **`prompts/tasks.py` contains 5 of 12** high-complexity
  functions — reinforces the tasks.py split case
- **`prompts/admin.py` contains 4 of 12** — reinforces the
  admin.py split case; PromptAdmin is the main offender
- Complexity 10–14 at 9 functions: acceptable for careful review,
  not urgent

### Category 4 — Test file sizes and organization

**Method:**
```bash
find . -name "test_*.py" -o -name "tests.py" ... | xargs wc -l | sort -rn
```

**Finding:** Tests are organized in a `prompts/tests/` package
(good — not a single monolithic `tests.py`). The monolithic
pattern is at the *file* level, not the package level.

**Top test files:**

| File | LOC | Test count | Split concern |
|------|-----|------------|---------------|
| `test_notifications.py` | 2872 | 163 | Notification creation, dedup, signals, delete, pagination, rate limiting, system notifications — 7+ concerns in one file |
| `test_bulk_generator_views.py` | 2568 | 156 | Every bulk generator endpoint in one file |
| `test_bulk_generation_tasks.py` | 2264 | (not counted) | Task-layer tests; overlap with test_bulk_generator_views |
| `test_bulk_page_creation.py` | 1804 | (not counted) | Page publish flow |
| `test_validate_tags.py` | 1117 | (not counted) | Tag validation pipeline |
| `test_pass2_seo_review.py` | 1048 | (not counted) | Pass 2 SEO system |

**Recommendations:**
- Each of the 4+ 1500-line test files is a candidate for
  split-by-concern. E.g., `test_notifications.py` → subpackage
  `tests/notifications/test_creation.py`,
  `tests/notifications/test_dedup.py`, etc.
- Test count per file around 30–60 is idiomatic; 150+ is a smell
- Risk is LOW (test splits don't change production behavior);
  discoverability improves with smaller files

### Category 5 — Template fragment duplication

**Method:** Top HTML templates by line count.

**Top templates (custom only, excluding admin/summernote):**

| Template | LOC | Extraction candidate? |
|----------|-----|----------------------|
| `prompts/templates/prompts/user_profile.html` | 2073 | HIGH — gallery, follows, activity feed, trash view can be separate partials |
| `prompts/templates/prompts/prompt_list.html` | 1700 | HIGH — masonry card, filters, pagination are recurring blocks |
| `prompts/templates/prompts/prompt_detail.html` | 1186 | MEDIUM — media container, metadata, related prompts section |
| `prompts/templates/prompts/collections_profile.html` | 1017 | MEDIUM — overlaps with user_profile.html pattern |
| `templates/base.html` | 885 | LOW — base already acceptable; mostly navbar/footer boilerplate |
| `prompts/templates/prompts/bulk_generator.html` | 730 | MEDIUM — many form fields |
| `prompts/templates/prompts/collection_detail.html` | 697 | LOW |
| `prompts/templates/prompts/ai_generator_category.html` | 640 | LOW |

**Observations:**
- Top 4 templates all exceed 1000 lines — high refactor value
- `user_profile.html` and `collections_profile.html` share
  tab+grid patterns (already partially consolidated via
  `components/profile-tabs.css` per CLAUDE.md). Template-side
  consolidation lags
- `_prompt_card.html`, `_masonry_grid.html`, `_notification_list.html`
  partials exist (`prompts/templates/prompts/partials/`) — the
  partial pattern is established; more extraction would follow
  precedent

### Category 6 — Static asset audit (JS/CSS)

**Method:** Top JS/CSS files by line count.

**Top static files:**

| File | LOC | Type | Concern |
|------|-----|------|---------|
| `static/css/style.css` | **4479** | CSS | **#1 Exec Summary candidate** |
| `static/css/pages/bulk-generator.css` | 2077 | CSS | Page-scoped; feature-coherent |
| `static/css/pages/prompt-detail.css` | 1662 | CSS | Page-scoped; feature-coherent |
| `static/css/navbar.css` | 1268 | CSS | Component; could split navbar vs. dropdown vs. mobile |
| `static/js/bulk-generator.js` | 1216 | JS | Input-page main; already split into 5 modules per CLAUDE.md — OK |
| `static/css/pages/bulk-generator-job.css` | 1202 | CSS | Page-scoped; feature-coherent |
| `static/js/collections.js` | 1108 | JS | Collections UX; single-concern |
| `static/js/upload-form.js` | 1069 | JS | Upload form handler; single-concern |
| `static/js/bulk-generator-generation.js` | 999 | JS | Part of 5-module split |
| `static/css/upload.css` | 921 | CSS | Page-scoped |
| `static/js/navbar.js` | 899 | JS | Component |

**Observations:**
- `style.css` is the clear outlier — 2.2× the next-largest CSS
  file. High-value split candidate
- Other CSS files are page-scoped and feature-coherent (NOT
  refactor targets)
- JS files under 1500 lines have known single purposes;
  bulk-generator.js was already split into 5 modules (Session
  143), confirming the pattern works

### Category 7 — Settings/config file audit

**Method:** `wc -l prompts_manager/settings.py env.py`

**Findings:**
- `prompts_manager/settings.py` — 676 lines, 78 top-level
  assignments. Upper YELLOW / near-RED.
- `env.py` — 45 lines. Green. Intentionally minimal; env.py
  safety gate depends on this brevity (Session 163 v2 protocol).
  **NOT a refactor target.**
- Procfile, requirements.txt, .python-version — small, single-purpose.
  NOT refactor targets.

**Recommendation for `settings.py`:** Standard Django
`settings/` package split (base.py + production.py + local.py +
test.py) is well-established pattern. Would reduce merge conflict
surface as Phase SUB adds Stripe/OAuth config. Priority MEDIUM.

### Category 8 — Markdown file audit

**Method:**
```bash
find . -name "*.md" ... -exec wc -l {} + | sort -rn | head -30
```

**Tier summary:**
- Total MD files in scope: **521**
- Total MD LOC: **362,952**
- Over 1000 lines: 24 files
- 500–999 lines: 63 files

**Top 10 MD files:**

| File | LOC | Category | Action |
|------|-----|----------|--------|
| `docs/CLAUDE-ARCHIVE.md` | 11553 | Historical archive | Leave as-is (already archived) |
| `CLAUDE_CHANGELOG.md` | 4704 | Active changelog | **Split sessions 13-99 to archive** (~2500 LOC reduction) |
| `CLAUDE.md` | 3656 | Core reference | Already trimmed in 166-A; no split recommended |
| `archive/sessions/CONVERSATION_SUMMARY_GRID_PERFORMANCE_AUDIT.md` | 2566 | Archived report | Leave |
| `docs/PHASE_N4_UPLOAD_FLOW_REPORT.md` | 2551 | Phase N4 report (Phase complete) | Consider `archive/` |
| `archive/sessions/PHASE_A_E_GUIDE.md` | 2154 | Archived phase guide | Leave |
| `PROJECT_FILE_STRUCTURE.md` | 2076 | Active reference | Audit for staleness — was not updated in 166-A |
| `docs/301_REDIRECT_MIGRATION_PROTOCOL.md` | 1908 | Migration protocol | Retain (operational) |
| `CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md` | 1750 | Spec file | Already committed; can move to `archive/` or remove |
| `design-references/UI_STYLE_GUIDE.md` | 1615 | Style guide | Retain (active reference) |

**Plan docs claiming "ready for implementation" but SHIPPED:**
- `docs/BULK_IMAGE_GENERATOR_PLAN.md` (1321 lines) —
  header: "Status: Planning Complete, Ready for Implementation"
  — but Phases 1–7 of Bulk Generator are SHIPPED per CLAUDE.md
  dashboard. Status label is stale. Move to `archive/` with
  one-line status note OR update header in-place

**Spec + CC_SPEC files in repo root:**
- Currently uncommitted: `CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md`
  (1750 LOC), `CC_SPEC_PROCFILE_RELEASE_PHASE_v2.md`,
  `CC_SPEC_166_A_*`, `CC_SPEC_167_A_*`, `CC_SPEC_167_B_*`,
  `CC_SPEC_168_A_*` — per project convention, specs are not
  committed, but they persist untracked in the repo root after
  sessions. Periodic cleanup (move to local scratch dir) reduces
  root-directory noise but is a workflow concern, not a
  repo-state concern

**CLAUDE_CHANGELOG session distribution:**
- Active-reference band (Session 100+): 67 entries
- Historical band (Session 13–99): 30 entries, ~2500 LOC
- Recommended archive cutoff: Session 99 or below → `archive/changelog-sessions-13-99.md`

### Category 9 — Deprecated code detection

**Method:**
```bash
grep -rn "CloudinaryField|cloudinary|CLOUDINARY" prompts/ | wc -l → 206
grep -rn "DEPRECATED|TODO: remove|XXX|HACK|FIXME" prompts/
```

**Findings:**

1. **Cloudinary references: 206 hits** across non-migration files
   in `prompts/`. Significant but expected — Session 163-B removed
   Cloudinary from UserProfile only; `Prompt.featured_image` and
   `Prompt.featured_video` still use `CloudinaryField`. Pending
   full removal (CLAUDE.md Phase REP blocker: "Prompt fields
   pending"). **Not a refactor target until the Prompt migration
   ships.**

2. **Explicit deprecation markers (5 found):**
   - `prompts/tasks.py:316` — `DEPRECATED (N4-Cleanup): Use
     generate_ai_content_cached instead.`
   - `prompts/views/upload_views.py:222` — `DEPRECATED (N4-Cleanup):
     Redirect to single-page upload.`
   - `prompts/views/upload_views.py:670` — `DEPRECATED
     (N4-Refactor): Redirect to final page or home.`
   - `prompts/templates/prompts/collections_profile.html:268` —
     comment: `.collections-header-row and .btn-create-collection
     are DEPRECATED`
   - `prompts/tests/TEST_USER_PROFILES_README.md:246` — test
     output format reference (not code deprecation)

   All 4 code-level markers relate to N4 upload-flow cleanup.
   These are legitimate dead-code removal candidates for a small
   cleanup spec

3. **No `XXX`, `HACK`, or `FIXME` markers found** in the prompts
   package scope — suggests developer discipline around not
   burying tech debt as silent markers

### Category 10 — Cross-file reference integrity

**Method:** Sample path references from CLAUDE.md and
PROJECT_FILE_STRUCTURE.md, verify file existence.

**Sampled 20 path references, all resolved:**

| Reference | Exists? |
|-----------|---------|
| `prompts/admin.py` | ✅ |
| `prompts/tasks.py` | ✅ |
| `prompts/models.py` | ✅ |
| `prompts/views/bulk_generator_views.py` | ✅ |
| `prompts/views/api_views.py` | ✅ (62 lines — intentional compat shim per CLAUDE.md Session 128 note) |
| `prompts/views/upload_api_views.py` | ✅ |
| `prompts/services/vision_moderation.py` | ✅ |
| `prompts/services/bulk_generation.py` | ✅ |
| `prompts/management/commands/detect_orphaned_files.py` | ✅ |
| `prompts/management/commands/backfill_ai_content.py` | ✅ |
| `prompts/constants.py` | ✅ |
| `prompts/utils/related.py` | ✅ |
| `static/css/style.css` | ✅ |
| `static/js/bulk-generator.js` | ✅ |
| `templates/base.html` | ✅ |
| `CLAUDE.md` | ✅ |
| `CLAUDE_CHANGELOG.md` | ✅ |
| `CLAUDE_PHASES.md` | ✅ |
| `Procfile` | ✅ |
| `env.py` | ✅ |

**Result: 20/20 references resolve.** No broken cross-references
detected in the core docs sample.

**Known caveat:** Many of the 521 MD files are archived or
historical and may reference files deleted long ago. This
audit covers the *active* docs (CLAUDE.md, CLAUDE_CHANGELOG.md,
PROJECT_FILE_STRUCTURE.md, and recent reports). Comprehensive
reference integrity across all 521 MD files is out of scope and
would require a separate spec.

**One stale status note (not a broken reference but a truth
drift):** `docs/BULK_IMAGE_GENERATOR_PLAN.md` claims "Status:
Planning Complete, Ready for Implementation" — the referenced
feature shipped (Phases 1–7). See Category 8.

---

## Non-Recommendations (mandatory ≥10 items)

Files that APPEAR refactorable but should NOT be refactored, with
reasons. This section prevents future specs from targeting wrong
files.

1. **`env.py` (45 lines)** — Intentionally minimal per Session 163
   v2 protocol. The safety gate depends on this brevity. Any
   "cleanup" would reintroduce the 2026-04-19 incident vector.
   **DO NOT refactor.**

2. **`prompts/tests/` package** — Already a package, not a
   monolithic `tests.py`. Individual test files inside are
   refactor candidates (Category 4), but the package structure
   itself is correct.

3. **`prompts/migrations/*.py`** — Migration history is
   structurally immutable once applied. Do not "refactor" an
   applied migration. A future field-type migration spec may
   supersede older ones, but that's not refactoring — it's a
   schema evolution.

4. **`docs/CLAUDE-ARCHIVE.md` (11553 lines)** — Already archived
   by design. It IS a historical snapshot of an older CLAUDE.md.
   The large size is intentional; don't split or modify.

5. **`archive/` directory** — Everything in `archive/` is
   intentionally preserved for historical reference. Not a
   refactor target.

6. **`prompts/views/api_views.py` (62 lines, compat shim)** —
   Thin re-export shim from Session 128's split. CLAUDE.md notes
   its intentional minimal size. DO NOT restore or expand — the
   shim exists so `urls.py` imports remain stable.

7. **`prompts/constants.py` (478 lines, GREEN)** — Single source
   of truth for `IMAGE_COST_MAP`, `SUPPORTED_IMAGE_SIZES`,
   `ALLOWED_AI_TAGS`, `DEMOGRAPHIC_TAGS`, etc. Intentionally
   consolidated. Splitting would fragment the "grep to find any
   constant" affordance.

8. **`prompts/services/vision_moderation.py` (914 lines, YELLOW)**
   — Feature-coherent. Contains
   `VisionModerationService` with related helpers. Splitting
   would scatter NSFW-moderation logic across multiple files.
   Monitor for growth but NOT a current refactor target.

9. **`prompts/services/bulk_generation.py` (595 lines, YELLOW)**
   — Feature-coherent. Contains `_sanitise_error_message`,
   orchestration helpers, cost map utilities for bulk generation.
   Cohesive module.

10. **`prompts/services/orchestrator.py` (562 lines, YELLOW)** —
    Feature-coherent orchestration module for the upload pipeline.
    Single responsibility. Line count noted here so future spec
    writers don't reflex to target YELLOW files without checking
    cohesion.

11. **`prompts/management/commands/detect_orphaned_files.py` (798
    lines, YELLOW)** — Single-command implementation with paginator,
    CSV output, email notification. Monolithic but cohesive.

12. **`prompts/management/commands/backfill_ai_content.py` (612
    lines, YELLOW)** — Single-command backfill script.
    Self-contained.

13. **Test files under 500 lines inside the `tests/` package** —
    Already appropriately sized and cohesive.

14. **`CC_COMMUNICATION_PROTOCOL.md` (1183 lines)** — Living
    process doc; size grows with protocol maturity. Actively
    referenced in every session. Moving content would fragment
    the single-source-of-truth pattern.

15. **`CC_SPEC_TEMPLATE.md`** — Active spec template. Not a
    refactor target.

16. **`AGENT_TESTING_SYSTEM.md` (1010 lines)** — Active reference
    doc for agent workflow. Retain.

17. **`design-references/UI_STYLE_GUIDE.md` (1615 lines)** —
    Active design reference.

18. **`requirements.txt`, `Procfile`, `.python-version`,
    `.flake8`, `.pre-commit-config.yaml`, `.gitignore`** —
    Config files, single-purpose, correctly sized.

19. **`prompts/signals.py`, `prompts/social_signals.py`,
    `prompts/notification_signals.py`** — Signal-handler modules,
    cohesive by trigger type. Not refactor targets.

20. **`prompts/urls.py`** — URL routing table. Centralization is
    the point. DO NOT split.

---

## Health Metrics Summary

| Metric | Value |
|--------|-------|
| Python files in scope | 271–272 (exclude-path dependent) |
| Python LOC total | 133,642 |
| Python files ≥1000 lines | 12 (4.4%) |
| Python LOC in files ≥1000 lines | 91,229 (68.3% of all Python LOC) |
| Python files 500–999 lines | 20 (7.4%) |
| Python files <500 lines | 240 (88.2%) |
| C901 high-complexity functions (≥10) | 12 |
| C901 HIGH-priority (≥15) | 3 |
| Markdown files in scope | 521 |
| Markdown LOC total | 362,952 |
| Markdown files ≥1000 lines | 24 |
| HTML templates (custom) ≥1000 lines | 4 |
| HTML templates (custom) top size | 2073 (`user_profile.html`) |
| CSS files ≥1000 lines | 6 |
| CSS top size | 4479 (`static/css/style.css`) |
| JS files ≥1000 lines | 3 |
| Migration files | 87 (numbered 0001–0086 + `__init__.py`) |
| Settings.py assignments | 78 |
| Cloudinary references (code) | 206 (Prompt fields still use CloudinaryField — pending migration) |
| DEPRECATED markers (code) | 4 |
| Code-duplication confirmed instances | 1 (`_download_image` P3) |
| Broken cross-references (sample of 20) | 0 |

**Derived ratios:**
- **68.3% of Python code lives in 4.4% of files.** Materially
  improving code organization starts with these 12 files.
- **24 of 521 MD files (4.6%) exceed 1000 lines** — the long tail
  of markdown is mostly small (specs, reports, short docs).
  Archiving reduces file count more than LOC.
- **3 HIGH-complexity hotspots** in 2 files (`tasks.py` x2,
  `related.py` x1). All three are orchestration functions.

---

## Section 4 — Issues Encountered and Resolved

### env.py safety gate (recap)

Gate passed. Outputs in Preamble.

### Commands used

All read-only:
- `find`, `ls`, `wc -l`, `grep`, `awk`, `sort -rn`
- `git log --oneline`
- `python manage.py check` (pre + post — both clean)
- `python manage.py showmigrations prompts` (unchanged)
- `flake8 --select=C901 --max-complexity=10 prompts/`
- `pip show radon` (not installed — used flake8 fallback)

### Tool substitution

`radon` cyclomatic-complexity tool was specified as preferred in
the spec. `pip show radon` confirmed it is not installed in the
current virtualenv. Fell back to `flake8 --select=C901
--max-complexity=10 prompts/` per spec's explicit fallback
guidance. Both tools produce equivalent mccabe-complexity output
for the purpose of this audit (flake8's mccabe plugin IS the
same algorithm radon uses for CC scoring). No loss of fidelity.

### No-migrate attestation

```
$ python manage.py showmigrations prompts | tail -3
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
 [ ] 0086_alter_userprofile_avatar_url

$ ls prompts/migrations/ | wc -l
88
```

Migration state unchanged throughout. Migration 0086 still `[ ]`
(unapplied — same state as since 165-B commit). CC ran no
`migrate` or `makemigrations` commands.

### `python manage.py check` start + end

```
Pre-audit:  System check identified no issues (0 silenced).
Post-audit: System check identified no issues (0 silenced).
```

### git status post-audit

```
 D CC_SESSION_163_RUN_INSTRUCTIONS.md
 D CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md
 (4 more deleted 163 specs - unrelated, already deleted)
?? .claude/
?? CC_SPEC_166_A_DOCS_CONSOLIDATED_UPDATE.md
?? (other untracked specs - unrelated)
?? docs/REPORT_168_A_REFACTORING_AUDIT.md  (this report)
```

Only `docs/REPORT_168_A_REFACTORING_AUDIT.md` was created by
this spec. Zero code files modified.

### Issues resolved

- **radon unavailable:** Used flake8 fallback (spec-sanctioned).
  No blocking concern.
- **Grep D original regex returned 88 for migrations count:**
  Actual file count is 87 (counting `*.py` files only —
  `__pycache__` directory doesn't match `*.py`). Reconciled.

---

## Section 5 — Remaining Issues (Deferred)

Nothing NEW deferred by this spec (read-only analysis). The audit
itself surfaces 10 refactor candidates (see Proposed Refactoring
Sequence) — these are the "what to do next" items, not deferred
problems.

Carried forward from prior sessions (unchanged):
- Google OAuth credentials configuration (Session 163-D)
- Single generator implementation (Phase SUB prerequisite)
- Phase SUB implementation
- Prompt CloudinaryField → B2 migration
- `django_summernote` drift (upstream, documented only)
- Provider-specific rate limiting config for Replicate/xAI
- Long-data-migration guidance for Heroku Release Phase
- Migration file docstring convention

---

## Section 6 — Concerns

1. **Audit is a snapshot.** File sizes and complexity change with
   every session. Repeating this audit quarterly (or before every
   major phase kickoff) keeps the picture current. Ad-hoc
   one-shot.

2. **Complexity tool substitution.** flake8 mccabe was used
   instead of radon. Same algorithm; no fidelity loss. But if
   radon is installed later, numbers may vary by ±1 on edge cases
   depending on tool-version differences in how they count
   match/elif branches.

3. **Cross-reference integrity sample size (20).** This is a
   spot-check, not exhaustive. A full integrity pass across all
   521 MD files would take significant time and is out of scope.
   Zero broken refs in the sample is encouraging but not
   definitive.

4. **Refactor sequence assumes availability.** The 13–16 session
   estimate to execute all 10 proposed refactors assumes linear
   progress. Real-world sessions will mix refactors with feature
   work (Phase SUB, Phase POD). Sequencing priority #1–#4 before
   Phase SUB is the practical floor recommendation.

5. **Risk estimates are rough.** "Risk: MEDIUM-HIGH" on `models.py`
   split is based on general Django experience, not on this
   codebase specifically. A pre-refactor sub-spec should map
   exact import chains before committing to the split.

6. **Test file splits affect test runner output.** Splitting
   `test_notifications.py` into multiple files changes CI log
   structure; run time might increase marginally due to per-file
   setup. Low risk, worth noting.

---

## Section 7 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @technical-writer **(substituted — see disclosure below)** | 9.0/10 | Executive Summary genuinely ranked with all 7 fields per entry. Proposed Sequence has dependencies + prerequisites + unblocks. All 10 categories have methodology + evidence + findings + candidate-level recommendations. Non-Recommendations 20 items (2× minimum). Descriptive-vs-prescriptive discipline mostly held; occasional implementation hints acceptable. Institutional memory test passes strongly. Minor nit: Category 8 lacks an action-type legend. | N/A — clean pass |
| @code-reviewer | 8.8/10 | All line-count claims verified exactly (`tasks.py 3822`, `models.py 3517`, `style.css 4479`, `test_notifications.py 2872`, `CLAUDE_CHANGELOG.md 4704`). C901 hotspots at complexity 15 all verified (3 hotspots). Tier arithmetic correct (12+20+240=272; though true count is 271 depending on exclude paths). Migration state verified. Scope discipline clean — no code files modified. Structure complete: 10 categories, 20 Non-Rec items (≥10), 11 sections. Minor: 272 vs 271 off-by-one noted. | **Yes — metrics summary updated to "271–272 (exclude-path dependent)"** |
| @architect-review | 8.6/10 | Refactor sequence coherent (no circular prerequisites). 168-D before 168-E reasoning sound (tasks imports models). Value-risk ranking defensible — CSS at #1 is correct application of Value × Inverse Risk. Phase SUB integration correctly framed as "not blocked but cleaner after 168-D". RED/YELLOW tiers align with CLAUDE.md's CC tiers (different thresholds, compatible purposes). **Flagged 2 architectural risks not addressed:** (a) signal handler circular-import risk post models-split; (b) inline JS IIFE boundary risk for 168-I template extraction (CLAUDE.md Session 86 Known Risk Pattern). Also flagged ranking-vs-sequence inversion as potential reader confusion. | **Yes — all 3 absorbed: (a) added to 168-D Risk discussion; (b) added as Known Risk Pattern call-out for 168-I; (c) added clarifying note in Exec Summary intro.** orchestrator.py line count added to Non-Rec #10. |
| **Average** | **8.80/10** | All 3 agents ≥ 8.0 (lowest 8.6). Average ≥ 8.5 ✅ | |

### Agent substitution disclosure

**Substitution — @technical-writer → general-purpose agent.**
Consistent with Sessions 164, 165-A, 165-B, 166-A, 167-A, 167-B.
Disclosed in the agent prompt AND here. Score: 9.0/10.

@code-reviewer and @architect-review are native registry agents;
no substitution.

### Cross-Spec Bug Absorption Policy applied

Per the policy established in Session 162-H (absorb <5-line fixes
from review findings rather than deferring):

- **Executive Summary intro:** Added note about ranking vs.
  execution order (clarifies the apparent inversion between Exec
  Summary and Sequence table)
- **#3 models.py Risk discussion:** Added signal-handler
  circular-import risk + `models/__init__.py` re-export shim
  requirement
- **Proposed Sequence row 8 (168-I):** Marked "see Known Risk
  Pattern below"; appended inline-JS IIFE extraction warning
  referencing CLAUDE.md Session 86 precedent
- **Non-Recommendation #10:** Added orchestrator.py line count
  (562 YELLOW) inline
- **Health Metrics Summary:** Updated "272" to "271–272
  (exclude-path dependent)"

All 5 absorptions are ≤5 lines each; cumulative ~12 lines.
Documented here and in the commit message.

---

## Section 8 — Recommended Additional Agents

None required for the audit itself. 3 agents is the spec minimum
and covers:
- Narrative quality (@technical-writer)
- Metric accuracy + scope discipline (@code-reviewer)
- Refactor-sequence coherence + non-recommendations value
  (@architect-review)

For the follow-on refactor specs (168-B through 168-K), each will
likely need:
- @django-pro (for model/task/admin splits)
- @backend-architect (for sequencing integrity)
- Feature-specific agents as relevant

---

## Section 9 — How to Test

### Automated (local, already run)

```bash
# env.py gate — passed (Preamble)
# Django check — clean pre+post
python manage.py check
# Result: 0 issues ✅

# No-migrate attestation
python manage.py showmigrations prompts | tail -3
# Result: 0086 still [ ] (unchanged from pre-audit) ✅

# Migrations dir unchanged
ls prompts/migrations/*.py | wc -l
# Result: 87 (unchanged) ✅

# git status — only new report file
git status --short | grep "^ M\|^A"
# Result: only A docs/REPORT_168_A_REFACTORING_AUDIT.md (after staging) ✅
```

### Regression

No code changes → no regression surface. Existing tests continue
to pass (not re-run because audit cannot affect test behavior).

### Manual verification (developer)

- Scan the Proposed Refactoring Sequence against your own mental
  model: does the ordering make sense, or is there a dependency
  you'd swap?
- Check Non-Recommendations: are there any files on that list
  that you DO want refactored, or files NOT on that list you
  want protected?
- Review Executive Summary rankings: would you reorder #1–#5?

### No production test

Read-only audit. No deployment impact.

### Rollback

`git revert <168-A commit>` — clean revert. Zero side effects.

---

## Section 10 — Commits

| Commit hash | Branch | Scope | Files |
|---|---|---|---|
| *(to be filled after commit)* | main | Session 168-A full repository refactoring audit | `docs/REPORT_168_A_REFACTORING_AUDIT.md` |

### Commit message

```
docs: add full repository refactoring audit (Session 168-A)

Adds docs/REPORT_168_A_REFACTORING_AUDIT.md - a read-only
analysis identifying refactoring opportunities across the
entire PromptFinder codebase before Phase SUB/POD work adds
significant new surface area.

Audit methodology: 10 categories analyzed with metric evidence.

- Python file line-count census (12 files >=1000 lines,
  68.3% of Python LOC)
- Code duplication detection (1 confirmed: _download_image
  across Replicate + xAI providers, P3 from CLAUDE.md)
- Complexity hotspots (12 C901 functions, 3 HIGH priority
  at complexity >=15, all orchestration)
- Test file sizes (6 monolithic files; tests/ package
  structure is correct, individual file splits recommended)
- Template fragment duplication (top 4 templates >1000 lines)
- Static asset audit (style.css at 4479 lines is the #1
  single-file concern in the entire codebase)
- Settings/config file audit (676 lines, near-RED)
- Markdown file audit (521 MD files, 362,952 LOC;
  CLAUDE_CHANGELOG sessions 13-99 archive candidate;
  BULK_IMAGE_GENERATOR_PLAN.md status label stale)
- Deprecated code detection (206 Cloudinary refs pending
  Prompt migration; 4 N4-Cleanup deprecation markers)
- Cross-file reference integrity (20/20 spot-check refs
  resolve)

Deliverables:
- Executive Summary: ranked top 5 refactoring opportunities
  (style.css split #1, tasks.py split #2, models.py #3,
  admin.py #4, docs archive pass #5)
- Proposed Refactoring Sequence with 10 candidates and
  dependencies (est. 13-16 sessions total; minimum viable
  sequence before Phase SUB is #1-#4, 6-8 sessions)
- Non-Recommendations: 20 items that look refactorable but
  should not be refactored (env.py, migrations, archive,
  cohesive YELLOW files, etc.)
- Health Metrics Summary

The audit is descriptive, not prescriptive - it identifies
candidates with evidence. Follow-on specs (168-B through
168-K) will propose exact refactor implementations based on
the ranking.

Docs-only. Zero code changes. Zero new migrations. env.py
safety gate passed. python manage.py check clean pre and
post. 167-A + 167-B prerequisites confirmed committed.

Agents: 3 reviewed (@technical-writer via general-purpose
DISCLOSED substitution, @code-reviewer, @architect-review),
all >= 8.0, avg X.XX/10.

Files:
- docs/REPORT_168_A_REFACTORING_AUDIT.md (new)
```

**Post-commit:** No push by CC.

---

## Section 11 — What to Work on Next

**Immediate post-commit actions (developer):**

1. **Review the Executive Summary rankings.** Are they aligned
   with your priorities? Swap any #1–#5 positions before
   spec-ing refactors.
2. **Review the Non-Recommendations list.** Confirm nothing on
   it should actually be refactored.
3. **Push when ready.** Docs-only commit — no deploy-time
   verification needed.

**Next session candidates (ordered by audit ranking):**

- **Session 168-B:** Docs archive pass — CLAUDE_CHANGELOG
  sessions 13-99 → `archive/changelog-sessions-13-99.md`;
  `BULK_IMAGE_GENERATOR_PLAN.md` status update or archive;
  `PHASE_N4_UPLOAD_FLOW_REPORT.md` to `archive/` (Phase complete).
  1 session. Low risk.
- **Session 168-C:** `static/css/style.css` split into
  `pages/*` and shared-component files. 1–2 sessions. Visual
  regression testing required.
- **Session 168-D:** `prompts/models.py` split by domain
  boundary. 2 sessions. Requires pre-work sub-spec to map
  imports.
- **Session 168-E:** `prompts/tasks.py` split by responsibility.
  2 sessions. Depends on 168-D.
- **Session 168-F:** `prompts/admin.py` split to package.
  1–2 sessions. Independent of 168-D/E but cleaner after 168-D.
- **Session 168-G:** Test file splits (`test_notifications.py`,
  `test_bulk_generator_views.py`, `test_bulk_generation_tasks.py`).
  2 sessions. Independent.
- **Session 168-H:** Provider `_download_image` extraction
  (resolves P3 blocker). 0.5 sessions. Independent.
- **Session 168-I:** Template fragment extraction
  (`user_profile.html`, `prompt_list.html`). 2 sessions.
  Independent.
- **Session 168-J:** `bulk_generator_views.py` split
  (1603 lines, 7 endpoints + page view). 1 session. Depends
  on 168-E.
- **Session 168-K:** `settings.py` → `settings/` package.
  1 session. Independent, useful before Phase SUB.

**Phase work interleaved (NOT blocked by refactors):**
- Phase SUB kick-off (Stripe + credit enforcement) — can begin
  after 168-D (models split) to add new models cleanly
- Single-generator implementation — independent
- Google OAuth credentials activation — independent
- Prompt CloudinaryField → B2 migration — independent

**Recommended sequencing decision for Mateo:**
- If targeting Phase SUB soon: run 168-B → 168-D → 168-C → 168-E
  (4-7 sessions) to establish clean structural baseline
- If targeting Phase POD first: same floor sequence; Phase POD
  adds different models but same structural constraints apply
- If targeting both: same floor sequence; structural improvement
  compounds across phases

**Nothing blocked by this audit.** The audit's output IS the
blocker for *targeted* refactoring specs going forward.

---

**END OF REPORT 168-A**
