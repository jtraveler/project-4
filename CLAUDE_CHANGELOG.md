# CLAUDE_CHANGELOG.md - Session History (3 of 3)

**Last Updated:** April 25, 2026 (Sessions 101–169)

> **📚 Document Series:**
> - **CLAUDE.md** (1 of 3) - Core Reference
> - **CLAUDE_PHASES.md** (2 of 3) - Phase Specifications
> - **CLAUDE_CHANGELOG.md** (3 of 3) - Session History ← YOU ARE HERE

---

## How to Use This Document

This is a running log of development sessions. Each session entry includes:
- What was worked on
- What was completed
- Agent ratings received
- Any blockers or issues discovered

**Update this document at the end of every session.**

---

> **📦 Looking for Sessions ≤ 99?** They live in
> [`archive/changelog-sessions-13-99.md`](archive/changelog-sessions-13-99.md).
> This active CHANGELOG contains **Sessions 100 onward**.
> Most contribution work does not require consulting the
> archive — reach for it only when tracing the history of
> a pre-Session-100 decision.

---

## February–April 2026 Sessions

### Session 169-D — April 25, 2026 (Comprehensive 169-cluster Docs Catch-up — commit `<HASH>`)

**Outcome:** Closes 9 documentation gaps that emerged during
the 169 cluster (169-A/B/C) but were not absorbed into the
cluster's session entries. Additive across 4 docs files +
1 new completion report.

**Why this spec exists:**

The 169 cluster shipped successfully and is documented at
the session-row granularity in CLAUDE.md's Recently Completed
table and in CLAUDE_CHANGELOG.md (169-A/B/C entries). However,
the work surfaced **system-level patterns and concepts** that
had no doc home: the `_resolve_ai_generator_slug` helper
architecture, the `/prompts/other/` page's rationale as
defensive infrastructure, memory rules drift (CLAUDE.md said
"9 of 30" while actual count was 13), the silent-fallback
observability principle as a CC_SPEC_TEMPLATE Critical
Reminder, agent substitution formalization, PFS top-line
count drift, and several P3 follow-ups from 169-C agent
review.

**Files modified (4 + 1 new):**

1. **CLAUDE.md** — most extensive edits:
   - New `#### Generator Slug Resolution Helper (Sessions
     169-A/B/C)` H3 inside the Bulk AI Image Generator
     section. Explains the `_resolve_ai_generator_slug(job)`
     helper architecture, why `/prompts/other/` exists
     (defensive infrastructure for silent-fallback path),
     sequential vs concurrent publish-path test coverage
     (`ContentGenerationAlignmentTests` and
     `PublishTaskTests.test_publish_sets_ai_generator_from_registry`),
     and operator-side drift signal via `logger.warning`.
   - "Active memory rules (9 of 30)" → "(13 of 30)" header
     bump.
   - 4 new memory rule entries inserted after rule #9:
     #10 (read current versions of files before drafting
     specs — 168-D-prep evidence), #11 (Cloudinary video
     preload warning observation — first observed during
     168-D smoke test), #12 (tasks.py refactor postmortem
     reference — gates future 168-E reattempts), #13
     (silent-fallback observability — 162-E and 169-B
     evidence).
   - Token-cost trade-off math updated: 9 rules → 13 rules,
     1,300–1,800 → 1,900–2,600 tokens per message,
     $0.30–$1.00 → $0.45–$1.45 per session.
   - 4 new Deferred P3 rows: `EndToEndPublishFlowTests`
     `GeneratorModel` fixture gap, broader PFS stale-counts
     audit, `@technical-writer` registry formalization, real
     SEO copy for 7 `AI_GENERATORS` model entries.
   - 169-C Recently Completed row: `Commit pending` →
     `Commit \`d9fcda7\``, `Agent avg pending` → `Agent avg
     9.1/10`. Surgical replacement; rest of row
     unchanged.
   - New 169-D Recently Completed row at top of table.
   - Version footer 4.67 → 4.68 with summary covering all
     169-D additions plus closing the 169 cluster recap.

2. **CC_SPEC_TEMPLATE.md** — two additions:
   - **Critical Reminder #10 — Silent-Fallback
     Observability**: any safe-fallback code path that
     writes data must emit `logger.warning` with structured
     fields. Examples: 162-E (`except Exception` narrowing
     around provider-registry cost lookup), 169-B
     (`_resolve_ai_generator_slug` fallback to `'other'`).
     Pattern test: if you removed the warning, would
     production drift be detectable? If not, warning is
     required.
   - **Agent Substitution Convention** subsection inside
     AGENT REQUIREMENTS: formalizes `@technical-writer` →
     `general-purpose + persona` (13+ consecutive sessions)
     and `@test-engineer` → `@test-automator` (since 168-A)
     as canonical substitutions. Disclosure required in
     every spec's agent ratings table.
   - Changelog header v2.7 → v2.8 with summary of these
     two additions.

3. **PROJECT_FILE_STRUCTURE.md** — 4 top-line surgical edits:
   - Last Updated April 24 → April 25, 2026 (Sessions 163–169)
   - Total Tests 1364 → 1386
   - Migrations 88 → 90 (169-B's `0087_retag_grok_prompts`
     + 169-C's `0088_alter_deletedprompt_ai_generator`)
   - Test Files 28 → 29 (169-B's
     `test_generator_slug_validation.py`)
   - Broader PFS stale-counts audit deferred via the new P3
     row added to CLAUDE.md in this spec.

4. **CLAUDE_CHANGELOG.md** — two edits:
   - **This entry** (new at top of active sessions block).
   - **168-A entry surgical fix:** em-dash individual agent
     scores replaced with real per-agent scores from
     `docs/REPORT_168_A_REFACTORING_AUDIT.md` (@technical-writer
     sub 9.0, @code-reviewer 8.8, @architect-review 8.6,
     average 8.80). Trivial recovery; was flagged in
     168-catchup as deferred and again in 169-C deferred
     list.

**Files NOT modified:**

- All `.py`, `.html`, `.js`, `.css` files
- Any migration file
- `CLAUDE_PHASES.md` (separate concern, not drifted)
- `CC_COMMUNICATION_PROTOCOL.md` (no changes needed for
  this catch-up)
- `prompts/constants.py` real SEO copy (deferred to Phase
  SUB launch prep — needs Mateo's marketing input)

**Explicitly deferred (NOT in 169-D):**
- Real SEO copy for the 7 model-specific `AI_GENERATORS`
  entries from 169-B (P3 row added; needs Mateo's marketing
  input)
- Master "Outstanding Issues" tracker section (bigger
  restructure — separate future spec)
- Cloudinary video preload warning fix (memory rule #11 is
  observation-only)
- 168-F `.flake8` retroactive note (git history captures)

**Verified:**
- `python manage.py check`: 0 issues pre + post
- Test suite: 1386 tests pass (no change — docs-only spec)
- `git status`: only 4 docs files modified + 1 new report
- Migration directory unchanged (no new migrations)

**Agents:** 2 reviewed (`@code-reviewer` 9.2/10,
`@technical-writer` 8.7/10 — substituted via `general-purpose +
persona`, **14th consecutive session of substitution**;
formalized in this spec's CC_SPEC_TEMPLATE addition). Both
≥ 8.0. Avg 8.95/10.

**Commit:** `<HASH>`. 1386 tests (no change).

---

### Session 169-C — April 25, 2026 (Cleanup Pass — P2/P3 Follow-ups + Working-Tree Hygiene + Docs Catch-up)

**Outcome:** consolidated cleanup commit closing the 169-B
deferred items, removing 12 stale spec files from the working
tree, and bringing CLAUDE.md / CLAUDE_CHANGELOG.md current.

**169-B follow-ups closed:**

- **`DeletedPrompt.ai_generator` validator added.** 169-B
  added `RegexValidator(GENERATOR_SLUG_REGEX)` to
  `Prompt.ai_generator` and `BulkGenerationJob.generator_category`
  but missed the sibling `DeletedPrompt.ai_generator` field
  (line ~1086 of `prompts/models/prompt.py`). Latent risk:
  if a future restoration path resurrected pre-169-B
  `DeletedPrompt` rows with dotted values, no validator would
  block them at create-time. Migration 0088 adds the same
  validator. Schema-only — no `RunPython`, no data migration
  (production has 0 dotted values per 169-A audit).

- **`AI_GENERATORS['other']` stub entry added.** Closes the
  silent-fallback hole in `_resolve_ai_generator_slug`: when
  the helper falls back to `'other'` (no GeneratorModel match),
  `/prompts/other/` previously 404d. The new entry serves a
  content-thin landing page with generic descriptive copy. The
  `logger.warning` 169-B added to the helper's fallback branch
  remains as the operator-side drift signal.

- **`PublishTaskTests` GeneratorModel fixture + `ai_generator`
  assertion added.** 169-B's `ContentGenerationAlignmentTests`
  covered the sequential `create_prompt_pages_from_job` path's
  helper integration; the concurrent
  `publish_prompt_pages_from_job` (Phase 6B) path lacked
  parallel coverage. New `test_publish_sets_ai_generator_from_registry`
  test asserts the fixture's slug `'gpt-image-1-5-byok'`
  resolves correctly through the concurrent path.

**Working-tree hygiene:** 12 stale `CC_SPEC_*.md` files
removed from the repo root (7 already-staged-deleted
`CC_SPEC_163_*.md` + `CC_SPEC_168_F_ADMIN_SPLIT.md` from
prior sessions; 3 already removed before 169-C
[`CC_SPEC_168_E_POSTMORTEM`, `CC_SPEC_169_A`, `CC_SPEC_169_B`];
2 untracked drafts removed in 169-C — `MONETIZATION_STRATEGY_DOCS_UPDATE`,
`PROCFILE_RELEASE_PHASE_v2`).

**Docs catch-up:** CLAUDE_CHANGELOG.md gained 169-A, 169-B,
and 169-C entries; CLAUDE.md gained 3 Recently Completed rows
+ version footer bump 4.66 → 4.67 + Last Updated synced to
April 25, 2026. PROJECT_FILE_STRUCTURE.md unchanged
(structural additions are at granularities PFS doesn't
enumerate — individual migrations and individual test files).

**Files:** 5 modified (prompt.py, constants.py,
test_bulk_page_creation.py, CLAUDE.md, CLAUDE_CHANGELOG.md);
2 new (migration 0088, REPORT_169_C); 12 deletions. Test
count: 1385 → 1386 (+1 PublishTaskTests addition).

**Explicitly deferred (NOT in 169-C):**
- Real SEO copy for the 7 model-specific `AI_GENERATORS`
  entries from 169-B (needs Mateo's marketing input)
- Formalize `@technical-writer` substitution in
  CC_SPEC_TEMPLATE (now 13+ consecutive sessions)
- Cloudinary video preload warning (memory rule #11)
- Recover Session 168-A individual agent scores
- `prompt_list_views.py` growth monitor (passive)
- 168-F `.flake8` retroactive note (git history captures)

**Agents:** 3 reviewed (`@code-reviewer`, `@architect-review`,
`@test-automator` — sub for `@test-engineer`). Scores filled
post-review.

---

### Session 169-B — April 25, 2026 (Generator Slug Permanent Fix — commit `a37d2d8`)

**Outcome:** P0 fix for production 500 on prompt detail pages
with dotted `ai_generator` values, plus permanent dot-character
class defense per the 169-A diagnostic.

**Root cause:** four hardcoded `ai_generator='gpt-image-1.5'`
literals at `tasks.py:3387, 3424, 3636, 3693` wrote dotted
values regardless of which AI model actually ran. A Grok job
(provider=`xai`, model_identifier=`grok-imagine-image`)
produced 7 prompts, all mis-tagged. The dotted value crashed
`prompt_detail.html`'s `{% url 'ai_generator_category' %}`
because Django's `<slug:>` URL converter rejects dots. All 7
dotted-`ai_generator` rows on production came from this single
bug.

**Six categories of change in one coordinated fix:**

1. **Helper function** `_resolve_ai_generator_slug(job)`
   replaces the four hardcoded literals. Pulls slug from
   `GeneratorModel` registry by `(provider, model_identifier)`.
   Intentionally does NOT filter by `is_enabled` (would mis-
   tag historical jobs whose model is later disabled). Logs
   `logger.warning` with structured fields when falling back
   to `'other'` for observability (post-agent-review fix).

2. **`RegexValidator(r'^[a-z0-9][a-z0-9-]*$|^$')`** added to
   `Prompt.ai_generator` and `BulkGenerationJob.generator_category`.
   Default values changed from `'gpt-image-1.5'` to
   `'gpt-image-1-5'`. `BulkGenerationJob.model_name`
   intentionally exempt — Replicate vendor strings
   (`'black-forest-labs/flux-1.1-pro'`) contain dots by design.

3. **Bidirectional data migration 0087** retags 7 mis-tagged
   Grok prompts: `ai_generator='gpt-image-1.5'` → `'grok-imagine'`
   (correct attribution, not just URL-safe form). Defensive
   sweep on `BulkGenerationJob.generator_category` (expected
   0 rows per 169-A Query D).

4. **Taxonomy update** — `AI_GENERATOR_CHOICES` updated:
   `'gpt-image-1.5'` → `'gpt-image-1-5'` (display string
   unchanged). 7 new entries added matching `GeneratorModel.slug`
   values. `AI_GENERATORS` dict gained matching entries with
   placeholder SEO copy (real marketing copy deferred).

5. **Defensive fallback** — `get_generator_url_slug()` returns
   `None` on no-match. Template wraps `{% url %}` call in
   `{% with %}{% if %}{% else %}{% endif %}` guard with
   no-link `<span>` fallback that preserves visual layout.

6. **Regression test suite** — new file
   `prompts/tests/test_generator_slug_validation.py` (21 tests,
   7 classes) enforces the canonical rule across all four
   taxonomies + helper + explicit `model_name` exemption test.

**Verified post-deploy:** production has 0 dotted
`ai_generator`, 7 `'grok-imagine'`, 0 original
`'gpt-image-1.5'`. Previously-failing URL renders 200 OK with
"Model Used: Grok Imagine" linking to `/prompts/grok-imagine/`.

**Files:** 8 modified, 3 new (migration 0087, test file,
report). Test count: 1364 → 1385 (+21).

**Agents:** 4 reviewed (`@code-reviewer` 9.3,
`@architect-review` 8.3, `@test-automator` 9.1,
`@backend-security-coder` 9.0). Average 8.925/10.

---

### Session 169-A — April 25, 2026 (Generator Slug Diagnostic — commit `2106eb9`)

**Outcome:** read-only diagnostic for production 500 on prompt
detail pages + permanent-fix plan for the dot-character class
of issue.

**Three bugs confirmed:**

- **Bug C (P0):** 4 hardcoded `ai_generator='gpt-image-1.5'`
  literals at `tasks.py:3387, 3424, 3636, 3693` (the user-
  visible cause)
- **Bug A (P2):** Migration 0080 (Session 153) reintroduced
  dotted defaults on `BulkGenerationJob.model_name` /
  `generator_category`
- **Bug B (P1):** Three identifier taxonomies disagree
  (`AI_GENERATOR_CHOICES`, `AI_GENERATORS` dict,
  `GeneratorModel.slug`) — only the last is URL-clean

**Scope:** 7 of 64 prompts (10.9%) — trivial data migration.
All 7 dotted prompts came from a single Grok job, mis-tagged
by the hardcoded literal.

**Section 9 of the report** prescribed the permanent-fix plan
addressing the dot-character class at every layer (validator,
choice, dict, URL converter, helper, template, test). Settled
on canonical rule `^[a-z0-9][a-z0-9-]*$` with defense-in-depth.
Recommended sequence: 169-B (consolidated fix), 169-D deferred.

**Files:** 1 new (`docs/REPORT_169_A_GENERATOR_SLUG_DIAGNOSTIC.md`,
708 lines). Zero code changes. Zero production DB writes.

**Agents:** 2 reviewed (`@code-reviewer` 9.0, `@architect-review`
9.0 after fix-cycle from initial 7.5). Average 9.0/10.

---

### Session 168-E — April 24, 2026 (tasks.py Refactor — Abandoned)

**Outcome:** refactor abandoned after a Phase 1 attempt
revealed an architectural constraint that changes the
cost/benefit. tasks.py remains at 3,822 lines on origin/main.
**See `docs/POSTMORTEM_168_E_TASKS_SPLIT.md` for full
analysis.**

**168-E-prep — committed:** read-only import-graph + Django-Q
contract analysis. Catalogued all 49 functions, 15 module-
level constants, 34 in-function lazy imports, and a 41-name
shim contract (7 Django-Q string-reference entry points + 12
public + 20 private + 9 constants). Repo-wide grep confirmed
0 DB-stored Schedule rows, 0 schedule() calls. Found 14
blockers across the split, severity-ranked. Commit `aa13ed7`.
Agent avg 9.75/10 (@code-reviewer, @architect-review).

**168-E-A — attempted, REVERTED before commit:** Phase 1
extraction targeted 4 low-risk submodules (notifications,
nsfw_moderation, b2_storage, placeholders) plus a transitional
`_remainder.py` for Phase 2 targets. CC's execution passed all
acceptance gates (1,364 tests OK, 4-agent avg 9.625/10) but
required inlining `b2_storage` back into `__init__.py` after
4 progressive test-fix iterations because `@patch('prompts.
tasks.X')` mocks fail to propagate when call sites live in
sibling submodules. Net file-size reduction: ~4% (3,822 →
3,667 in `__init__.py`); aggregate package larger than
original due to header overhead. User concluded cost-benefit
didn't justify shipping; reverted local working tree to
`aa13ed7`. No commit on origin.

**Key learning (full detail in postmortem):** Python's
`@patch(name)` replaces the name in the patched module's
namespace, but `from .submodule import X` in sibling
submodules already bound to the underlying function at import
time. Heavily-mocked modules cannot be naively split into
submodules without either (a) updating test patch paths, or
(b) routing all sibling-submodule imports through the package
shim. The 168-E-prep report did not anticipate this — future
prep specs for similar refactors should include a `@patch`
audit explicitly.

**Status of tasks.py:** stays as-is on origin/main. Future
revisit gated by thresholds documented in postmortem Section
10. The 6 `noqa: C901` complexity-flagged functions remain as
candidate targets for a different refactoring approach
(reduce complexity rather than restructure files).

---

### Session 168-F — April 23, 2026 (admin.py Split into Package)

**Fourth code refactor from the 168-A audit.** The 2,459-line
`prompts/admin.py` replaced by a `prompts/admin/` package with
12 submodules (forms, inlines, 8 domain-admin files, custom
views, orchestration `__init__.py`) plus backward-compat
re-exports preserving the public import contract for
`PromptAdmin` and `trash_dashboard`.

**Structure:**
- `__init__.py` — import orchestration (submodule order
  matters; taxonomy_admin BEFORE other admin modules that might
  reference Tag; users_admin internally unregisters User before
  CustomUserAdmin registers; index_template set last) +
  backward-compat re-exports for PromptAdmin, PromptAdminForm,
  RESERVED_SLUGS, trash_dashboard
- `forms.py` — PromptAdminForm + RESERVED_SLUGS (104 lines)
- `inlines.py` — 4 inline classes (56 lines)
- `prompt_admin.py` — PromptAdmin (952 LOC largest),
  PromptViewAdmin, SlugRedirectAdmin (1,023 lines)
- `moderation_admin.py` — ModerationLog, ContentFlag,
  ProfanityWord (incl. bulk-import view), PromptReport,
  NSFWViolation admins (573 lines)
- `users_admin.py` — UserProfile, AvatarChangeLog,
  EmailPreferences, CustomUserAdmin (+ User unregister) (324
  lines)
- `interactions_admin.py` — Comment, Collection,
  CollectionItem, Notification admins (153 lines)
- `bulk_gen_admin.py` — BulkGenerationJob, GeneratorModel
  admins (92 lines)
- `taxonomy_admin.py` — TagCategory, SubjectCategory,
  SubjectDescriptor admins (+ Tag unregister) (110 lines)
- `site_admin.py` — SiteSettings, CollaborateRequest admins
  (69 lines)
- `credits_admin.py` — UserCredit, CreditTransaction admins
  (46 lines)
- `custom_views.py` — trash_dashboard standalone view (81
  lines)

**Two external consumers discovered during Step 0** and
resolved via backward-compat re-exports (not consumer-file
edits): `prompts/tests/test_admin_actions.py:16` imports
PromptAdmin; `prompts_manager/urls.py:8` imports
trash_dashboard. Both work post-split without changes.

**Verified:**
- `python manage.py check`: 0 issues
- `makemigrations --dry-run`: "No changes detected"
- Test suite: 1,364 tests pass pre AND post (exact match, 12
  skipped preserved)
- `admin.site._registry`: 37 models post-split, IDENTICAL
  Model→AdminClass mapping to pre-split baseline (forensic
  verification — decorators all fired at the correct order)
- Module-level side effects preserved: Tag unregister in
  taxonomy_admin.py, User unregister in users_admin.py,
  `index_template = 'admin/custom_index.html'` in __init__.py
- Zero consumer file modifications

**Flake8:** `.flake8` gained one line — `*/admin/*.py` per-file
ignore list, mirroring the existing `*/admin.py` rule that
silenced the same codes (E402/E501/F401/F841/W-series/E261/
E302/E303) in the monolithic file. Same mechanical move as
the earlier `*/views/*.py` addition after the views split.
No body-code style changes.

**Commit:** `16a95cf`. Agent average **9.30/10**
(@code-reviewer 9.2, @architect-review 9.5, @test-automator
9.2 — sub for @test-engineer).

### Session 168-D — April 22, 2026 (models.py Split)

**Focus:** Third code refactor from the 168-A audit. Split the
3,517-line `prompts/models.py` into a `prompts/models/` package
with 9 submodules (8 domain + 1 constants) and a re-export shim
preserving backward compatibility.

**Package structure:**

- `prompts/models/__init__.py` — re-export shim (all 34 public
  names: 28 classes + 6 constants)
- `prompts/models/constants.py` — shared module constants
  (`STATUS`, `MODERATION_STATUS`, `MODERATION_SERVICE`,
  `AI_GENERATOR_CHOICES`, `DELETION_REASONS`,
  `NOTIFICATION_TYPE_CATEGORY_MAP`, `_BULK_SIZE_DISPLAY`)
- `prompts/models/users.py` — UserProfile, AvatarChangeLog,
  EmailPreferences, Follow
- `prompts/models/taxonomy.py` — TagCategory, SubjectCategory,
  SubjectDescriptor
- `prompts/models/prompt.py` — PromptManager, Prompt,
  SlugRedirect, DeletedPrompt, PromptView (largest submodule at
  ~1,382 lines)
- `prompts/models/interactions.py` — Comment, Collection,
  CollectionItem, Notification
- `prompts/models/moderation.py` — PromptReport, ModerationLog,
  ProfanityWord, ContentFlag, NSFWViolation
- `prompts/models/bulk_gen.py` — BulkGenerationJob,
  GeneratedImage, GeneratorModel
- `prompts/models/credits.py` — UserCredit, CreditTransaction
- `prompts/models/site.py` — SiteSettings, CollaborateRequest

**Key decisions:**

- `delete_cloudinary_assets` signal handler relocated from the
  former `models.py:2247` to `prompts/signals.py` with
  string-reference sender `sender='prompts.Prompt'`. Consistent
  with `notification_signals.py` convention
- Cross-package imports within `prompts/models/` use in-function
  lazy imports (e.g., `from .moderation import ContentFlag`
  inside `Prompt.get_critical_flags`) to avoid circular imports
- Shim re-exports 34 names (28 classes + 6 constants). The
  additional class beyond the prep-report estimate of 27 is
  `PromptManager`, defensively re-exported
- Absorbed one dead import (`from django.db.models import Q`
  inside `Prompt.get_recent_engagement`) removed during the
  split — the `Q` symbol was imported but never used. Caught by
  flake8 pre-commit on the new submodule. No behavior change
- `Follow.Meta.db_table = 'prompts_follow'` override preserved
  verbatim; `BulkGenerationJob.SIZE_CHOICES` still yields
  4 entries post-split

**Verified post-split:**

- `python manage.py check`: 0 issues
- `python manage.py makemigrations --dry-run`: "No changes
  detected" (no accidental schema drift)
- Full test suite: **1364 tests passing / 12 skipped** (exact
  match to pre-split baseline)
- All 34 public names resolve via `from prompts.models import X`
- `admin.py` 24-name import line (HIGH-severity blocker from
  prep report) works unchanged
- Zero modifications to `admin.py`, `tasks.py`, `views/`,
  `notification_signals.py`, `social_signals.py`, `tests/`,
  `apps.py`, `templatetags/`
- Signal registered exactly once (`post_delete._live_receivers`
  returns one sync receiver: `delete_cloudinary_assets`)
- 88 migrations unchanged; 0086 still `[ ]`

**Agents (4 reviewed, minimum for largest code refactor in repo):**

| Agent | Score |
|---|---|
| @code-reviewer | 9.2/10 |
| @architect-review | 9.2/10 |
| @test-automator (sub @test-engineer) | 10.0/10 |
| @backend-security-coder | 9.5/10 |
| **Average** | **9.475/10** |

All ≥ 8.0 ✅ Average ≥ 8.5 ✅

**Files:**

- `prompts/models.py` (DELETED — content migrated to package)
- `prompts/models/` (NEW package — 10 files)
- `prompts/signals.py` (MODIFIED — absorbs
  `delete_cloudinary_assets`)
- `docs/REPORT_168_D.md` (new completion report)

**Commit:** `56cad16`.

---

### Session 168-D-prep — April 21, 2026 (models.py Import Graph Analysis)

**Focus:** Read-only prep work for 168-D. Analyzed the
3,517-line `prompts/models.py` + `signals.py` + all external
import sites to produce the concrete evidence needed to design
the models/ package split and `__init__.py` re-export shim
without speculation.

**Analysis deliverables (`docs/REPORT_168_D_PREP_MODELS_IMPORT_GRAPH.md`):**

- Complete inventory of 28 top-level class definitions (27
  models + 1 Manager) with line ranges, LOC sizes, and proposed
  8-domain grouping
- Relationship map (FK, OneToOne, M2M, string references) with
  file:line evidence for every relationship
- All 10 `@receiver` signal handlers across 4 signal files
  (`prompts/signals.py`, `models.py`,
  `notification_signals.py`, `social_signals.py`) — 3
  direct-class senders, 5 string-reference senders, 2 allauth
  signals
- All external import sites enumerated (`admin.py` 25 names,
  `tasks.py` 16 in-function imports,
  `notification_signals.py` 4 imports, `templatetags/` 1
  import, 25 test files with ~70 imports)
- 2 in-function lazy imports inside `models.py`
  (`UserProfile.is_following` / `is_followed_by` referencing
  `Follow`)
- 168-D blockers and risks with severity ratings: **1 HIGH
  (admin.py 24-name import line blocker), 4 MEDIUM, 7 LOW, 2
  UNKNOWN** (migration RunPython, test patches — later
  resolved as LOW in 168-D)

**Absorbed during this spec (per Cross-Spec Bug Absorption
Policy, Session 162-H):**

- taggit signal-registration ordering risk added to Section 11
  at MEDIUM severity (TaggableManager triggers internal signal
  handlers at class-definition time)
- `db_table='prompts_follow'` override on Follow added at LOW
  severity (table name hardcoded, survives file move)
- CollaborateRequest placement ambiguity (site.py vs
  interactions.py) called out in Section 10 for 168-D explicit
  decision
- 10-line CLAUDE.md addition documenting the three CSS
  subdirectories' distinct roles (`partials/` vs `components/`
  vs `pages/`) — closes the 168-C @architect-review implicit
  decision boundary

**Agents (2 reviewed, docs-only minimum):**

| Agent | Score |
|---|---|
| @code-reviewer | 9.5/10 |
| @architect-review | 8.7/10 |
| **Average** | **9.1/10** |

**Files:**

- `CLAUDE.md` (10-line CSS directory convention in Key File
  Locations)
- `docs/REPORT_168_D_PREP_MODELS_IMPORT_GRAPH.md` (new)

**Commit:** `a905de3`.

---

### Session 168-C — April 21, 2026 (style.css Split into 5 Modular Partials)

**Focus:** First code refactor from the 168-A audit. Reduced
the largest single text file in the repo (`static/css/style.css`
at 4,479 lines) to a 17-line `@import` index plus 5 focused
partial files under `static/css/partials/`.

**Approach:** `@import`-based index. `style.css` remains the
entry point (no base-template changes needed) and imports 5
partials in cascade order.

**Partial splits:**

- `partials/_design-tokens.css` (lines 1–327) — custom
  properties, brand colors, typography
- `partials/_components.css` (lines 328–1708) — filters, hero,
  sidebar, masonry, buttons, forms, modals, responsive
- `partials/_trash.css` (lines 1709–2262) — alert, toggle,
  trash card / modal / action bar
- `partials/_collections.css` (lines 2263–3477) — trash
  collection footer, unified button, generator dropdown
- `partials/_collections-modal.css` (lines 3478–4479) —
  collections modal, thumbnail grid, card states, responsive

**Pre-commit hook interaction:** Byte-level diff was empty
(4,479 = 4,479 lines). The `end-of-file-fixer` hook then
stripped 2 trailing blank lines from `_design-tokens.css` and
`_collections.css` during staging. Post-hook content: 4,477
lines reassembled vs 4,479 original — 2 trailing blank lines
stripped at module boundaries. Zero semantic CSS impact (EOF
whitespace has no parsing effect; each partial is `@imported`
independently). Accepted the hook's modification rather than
bypassing repo hygiene policy via `--no-verify`.

**Verification:**

- `python manage.py check` clean pre + post
- `collectstatic --dry-run`: 17 files staged, 0 missing
- All selectors, properties, and values preserved
  byte-identically
- Zero Python / HTML / JS / migration changes

**Agents (3 reviewed):**

| Agent | Score |
|---|---|
| @code-reviewer | 9.5/10 |
| @frontend-developer | 9.0/10 |
| @architect-review | 8.1/10 |
| **Average** | **8.87/10** |

**Non-blocking findings (deferred per Section 6):**

- `@import` runtime fetch cost (future perf concern)
- Underscore prefix + potential SCSS toolchain silent-skip
  risk (future-proofing)
- `partials/` vs `components/` naming overlap (later closed by
  168-D-prep's CLAUDE.md addition)
- `_components.css` still large at 1,381 lines (future
  sub-split candidate)
- `style.css` name no longer matches its role (cosmetic;
  renaming would require base.html template change, out of
  scope)

**Files:**

- `static/css/style.css` (4,479 → 17 lines — now an import
  index)
- `static/css/partials/_design-tokens.css` (new)
- `static/css/partials/_components.css` (new)
- `static/css/partials/_trash.css` (new)
- `static/css/partials/_collections.css` (new)
- `static/css/partials/_collections-modal.css` (new)
- `docs/REPORT_168_C.md` (new completion report)

**Commit:** `213f604`.

---

### Session 168-B-discovery — April 21, 2026 (Archive Discoverability Pass)

**Focus:** Close the onboarding gap introduced by 168-B's
archive move. Add discoverability surfaces so new readers
(human or AI) can find archived content without scrolling to
the bottom of `CLAUDE_CHANGELOG.md`.

**Four additive edits:**

1. `CLAUDE.md` Related Documents table — new row pointing to
   `archive/` contents with framing that tells readers
   archives are for "why was X done" questions about
   pre-Session-100 work, not routine contribution needs.
2. `CLAUDE.md` Quick Start Checklist — new item #4 explicitly
   stating "Archives exist but are not usually required" with
   guidance on when they are. Existing items renumbered
   (env.py gate shifted from #4 to #5).
3. `CLAUDE_CHANGELOG.md` — top banner ("Looking for
   Sessions ≤ 99?") inserted between title / preamble and first
   session heading, pointing to archive. Complements the
   168-B footer pointer note — top + bottom coverage for
   readers who scan from either end.
4. `PROJECT_FILE_STRUCTURE.md` — file-location table updated:
   `PHASE_N4` entry redirected from `docs/` to `archive/`
   with session attribution; new entry added for
   `changelog-sessions-13-99.md`. Plus one absorbed fix
   (per Cross-Spec Bug Absorption Policy, Session 162-H):
   PFS "Files Created" tree for `PHASE_N4` gained an inline
   relocation note preserving historical context while
   signaling current archive location.

**Key framing:** New readers are told that the archive
contains historical context but is not required for routine
work. Prevents both (a) skipping archives entirely when
pre-Session-100 context matters, and (b) reading all archives
unnecessarily when they don't.

**Agents (2 reviewed):**

| Agent | Score |
|---|---|
| @technical-writer (sub via general-purpose — 9th consecutive) | 8.9/10 |
| @code-reviewer | 9.2/10 |
| **Average** | **9.05/10** |

**Files:**

- `CLAUDE.md` (2 targeted additive edits)
- `CLAUDE_CHANGELOG.md` (top banner added; footer pointer
  preserved)
- `PROJECT_FILE_STRUCTURE.md` (archive entries added/updated
  + absorbed tree-listing fix)
- `docs/REPORT_168_B_DISCOVERY.md` (new completion report)

**Commit:** `e554fa6`.

---

### Session 168-B — April 21, 2026 (Archive Old Changelog Sessions)

**Focus:** First refactor from the 168-A audit. Docs-only
file moves and one in-place status header update. Reduced
active `CLAUDE_CHANGELOG.md` by ~40% (4,704 → 2,839 lines).

**Changes:**

1. `CLAUDE_CHANGELOG` sessions 13–99 (December 2025 – March
   2026) moved verbatim to `archive/changelog-sessions-13-99.md`.
   Active CHANGELOG retains sessions 100+ (60 heading entries)
   plus a new pointer note at the file footer.
2. `BULK_IMAGE_GENERATOR_PLAN.md` line 5 status header updated
   from "Planning Complete, Ready for Implementation" to
   "SHIPPED — Phases 1–7 complete (Sessions 100+)…" Document
   body preserved unchanged; it remains a useful historical
   planning reference.
3. `PHASE_N4_UPLOAD_FLOW_REPORT.md` moved from `docs/` to
   `archive/` via `git mv` (history preserved via R status at
   `find-renames=50`). Phase N4 is fully shipped per
   CLAUDE.md. Pre-commit hook applied whitespace cleanup
   during staging (trailing-whitespace removal only, no
   content change).

**Session heading conservation:**

- Pre-edit: 97 headings in `CLAUDE_CHANGELOG.md` (git HEAD)
- Post-edit: 60 active + 37 archive = 97 total
- Byte-identical content verified for Sessions 99, 50, 13

**Agents (2 reviewed):**

| Agent | Score |
|---|---|
| @technical-writer (sub via general-purpose — 7th consecutive) | 8.7/10 |
| @code-reviewer | 9.2/10 |
| **Average** | **8.95/10** |

**Files:**

- `CLAUDE_CHANGELOG.md` (sessions 99–13 removed; pointer note
  added)
- `docs/BULK_IMAGE_GENERATOR_PLAN.md` (line 5 status updated)
- `archive/changelog-sessions-13-99.md` (new, 1,889 lines)
- `archive/PHASE_N4_UPLOAD_FLOW_REPORT.md` (moved from
  `docs/`, whitespace-cleaned)
- `docs/REPORT_168_B.md` (new completion report)

**Commit:** `b45ecdd`.

---

### Session 168-A — April 21, 2026 (Full Repository Refactoring Audit)

**Focus:** Read-only analysis identifying refactoring
opportunities across the entire PromptFinder codebase before
Phase SUB / POD work adds significant new surface area.

**Audit methodology:** 10 categories analyzed with metric
evidence:

- Python file line-count census (12 files ≥ 1,000 lines;
  68.3% of Python LOC concentrated in 4.4% of files)
- Code duplication detection (1 confirmed: `_download_image`
  across Replicate + xAI providers — P3 from CLAUDE.md)
- Complexity hotspots (12 `C901` functions; 3 HIGH priority at
  complexity 15, all orchestration)
- Test file sizes (6 monolithic files; `tests/` package
  structure is correct, individual file splits recommended)
- Template fragment duplication (top 4 templates > 1,000 lines)
- Static asset audit (`style.css` at 4,479 lines is the #1
  single-file concern in the entire codebase)
- Settings / config file audit (676 lines, near-RED)
- Markdown file audit (521 MD files, 362,952 LOC;
  `CLAUDE_CHANGELOG` sessions 13–99 archive candidate;
  `BULK_IMAGE_GENERATOR_PLAN.md` status label stale)
- Deprecated code detection (206 Cloudinary refs pending
  Prompt migration; 4 N4-Cleanup deprecation markers)
- Cross-file reference integrity (20/20 spot-check refs
  resolve)

**Executive Summary — top 5 refactoring opportunities ranked:**

1. `style.css` split (→ Session 168-C)
2. `tasks.py` split (→ future 168-E)
3. `models.py` split (→ Session 168-D)
4. `admin.py` split (→ future 168-F)
5. Docs archive pass (→ Session 168-B)

**Proposed Refactoring Sequence:** 10 candidates with
dependencies (estimated 13–16 sessions total; minimum viable
sequence before Phase SUB is #1–#4, 6–8 sessions).

**Non-Recommendations:** 20 items that look refactorable but
should NOT be refactored (env.py, migrations, archive,
cohesive YELLOW files, `orchestrator.py`, etc.).

**Absorbed (per Cross-Spec Bug Absorption Policy, Session
162-H):** 5 refinements from agent reviews:

- Executive Summary intro note clarifying ranking vs.
  execution order
- #3 `models.py` Risk discussion extended with signal handler
  circular-import risk post-split + `models/__init__.py`
  re-export shim requirement
- Sequence row 8 (168-I template extraction) annotated with
  Known Risk Pattern call-out referencing CLAUDE.md Session
  86 inline-JS IIFE extraction precedent
- Non-Rec #10 (`orchestrator.py`) annotated with line count

**Agents (3 reviewed):**

| Agent | Score |
|---|---|
| @technical-writer (sub via general-purpose) | 9.0/10 |
| @code-reviewer | 8.8/10 |
| @architect-review | 8.6/10 |
| **Average** | **8.80/10** |

(Individual scores recovered from `docs/REPORT_168_A_REFACTORING_AUDIT.md`
agent ratings table during Session 169-D docs catch-up.)

**Files:**

- `docs/REPORT_168_A_REFACTORING_AUDIT.md` (new)

**Commit:** `5b7b26d`.

---

### Session 167-B — April 21, 2026 (Polish Claude Memory System Section)

**Focus:** Four targeted edits to the Claude Memory System &
Process Safeguards section added in 167-A, addressing review
findings.

**Edits:**

1. Add 13th deferred candidate: user-content sanitization at
   rendering boundaries (S6 from Session 166-A/167 discussion
   was missing from the original table, causing a 12-vs-13
   count mismatch with the spec's narrative claim).
2. Correct `_sanitise_error_message` location in Related
   Safeguards bullet: defined in
   `prompts/services/bulk_generation.py`, imported locally in
   `tasks.py` to avoid circular import (per CLAUDE.md canonical
   note — original 167-A text said "pre-existing tasks.py
   pattern" which was location-imprecise).
3. Add inline italic note to Rule #1 explaining its rationale
   asymmetry with rules 2–9: Rule #1 predates the April 2026
   discussion and is a forward-reference tracker rather than
   an incident-response rule. The omitted rationale is
   intentional, not editorial oversight.
4. Reorder: move Three-criteria framework subsection to
   precede Deferred memory candidates. The framework is
   applied BY the deferred reasons, so framework should come
   first. Bridging sentence added to Deferred intro to
   forward-reference the framework now above it.

**Absorbed fix (per Cross-Spec Bug Absorption Policy, Session
162-H):** "How to add, remove, or modify memory rules"
subsection referenced "three-criteria framework below" —
stale after Edit 4 moved the framework above. Changed to
"framework above". One-word fix, well under the 5-line
absorption threshold. Flagged by @technical-writer review.

**Agents (2 reviewed):**

| Agent | Score |
|---|---|
| @technical-writer (sub via general-purpose — 8th consecutive) | 8.7/10 |
| @code-reviewer | 9.2/10 |
| **Average** | **8.95/10** |

**Files:**

- `CLAUDE.md` (4 targeted edits + 1 absorbed fix within
  Memory System H2)
- `docs/REPORT_167_B.md` (new completion report)

**Commit:** `606f3c6`.

---

### Session 167-A — April 21, 2026 (Claude Memory System + Security Safeguards)

**Focus:** Add new H2 section "🧠 Claude Memory System &
Process Safeguards" to CLAUDE.md documenting how Claude's
memory works in this project, the 9 currently active memory
rules, deferred candidates, and the three-criteria framework
for future additions.

**Content added:**

- How Claude's memory mechanically works (context loading,
  token cost, firing behavior, 30-slot capacity)
- All 9 currently active memory rules with rationale for each
- 12 deferred memory candidates with documented reasons for
  deferral (expanded to 13 in 167-B)
- Three-criteria framework for future memory additions
- Token cost vs. incident-prevention ROI analysis
- Related non-memory safeguards (env.py gate, release phase,
  SSRF patterns, etc.)

**Context:** Mateo and Claude had an extended Session 166-A
follow-up discussion about enhancing Claude's memory to
elevate project quality. Seven new memory edits were added
as a result, bringing total active memory to 9 of 30 slots.
This spec documents the discussion, rules, and reasoning so
future sessions (human or AI) can reason about the memory
system itself rather than just operating within it.

**Memory rules added during the discussion (rules 3–9):**

1. Pre-flight warnings on credential-output commands
2. No credential echo in specs / reports / chat
3. Dev-prod boundary discipline
4. Pause for significant issues (four-condition threshold)
5. Audit before answering "any outstanding issues"
6. Read target files in full before spec drafting
7. Phase-completion security audit cadence

Rationale for each rule ties to specific April 2026 incidents
(April 18 credentials leak, April 19 env.py migration, April
20 Procfile near-miss) or past spec-level failures (Session
165-B diagnostic error, Session 166-A morning audit surprise).

**Agents (3 reviewed):**

| Agent | Score |
|---|---|
| @technical-writer (sub via general-purpose) | 8.7/10 |
| @code-reviewer | 9.2/10 |
| @architect-review | 8.5/10 |
| **Average** | **8.8/10** |

**Files:**

- `CLAUDE.md` (new H2 section added before Current Costs)
- `docs/REPORT_167_A.md` (new completion report)

**Commit:** `a2843fa`.

---

### Session 166 — April 21, 2026 (Sessions 164–165 Consolidated Catch-Up)

**Focus:** Bundled 11 documentation fixes identified in the
2026-04-21 handoff review, catching up CLAUDE.md /
CLAUDE_CHANGELOG.md documentation after Sessions 164–165.

**P1 (must-fix):**

- Fill in 165-B commit hash (`<hash>` → `a457da2`, 2
  occurrences in CLAUDE_CHANGELOG Session 165 entry);
  agent-avg placeholder `9.XX/10` → `9.23/10`
- Add Session 164 and 165 rows to CLAUDE.md Recently
  Completed (table stopped at Session 163)
- Bump version footer 4.54 → 4.56, date April 20 → April 21

**P2 (should-fix):**

- Phase REP dashboard row: split "Cloudinary full removal"
  into "UserProfile done" + "Prompt fields pending"; surface
  rate-limiting audit summary with pointer to detail section
- Append correction note to Session 161 CHANGELOG entry —
  original 161-A paragraph claimed `str(CloudinaryResource)`
  returns object repr; Session 162-C investigation showed
  current SDK returns `self.public_id`. CLAUDE.md Recently
  Completed row already had this correction; CHANGELOG now
  matches

**P3 (worth-fixing):**

- Document `django_summernote` drift as known upstream
  warning, not actionable. Sited near Heroku Release Phase
  subsection
- Condense Session 163 Recently Completed entry (was single
  ~800-word paragraph, now terse 2–4 line summary matching
  style of surrounding rows; every factual claim preserved)
- Document 2026-04-18 credentials rotation (SECRET_KEY,
  FERNET_KEY, OPENAI_API_KEY) sited near existing Cloudinary
  typo correction note
- Document April 2026 profanity word list policy decision
  (occultic / fantasy vocabulary deactivated for artistic
  prompts)
- Add env.py safety gate to Quick Start Checklist as item 4
  (between CLAUDE_CHANGELOG check and micro-spec creation) —
  ensures future sessions see the gate before migration work

**Docs-only.** Zero code changes. Zero new migrations.
`python manage.py check` clean pre and post.

**Agents (3 reviewed):**

| Agent | Score |
|---|---|
| @technical-writer (sub via general-purpose) | 8.8/10 |
| @code-reviewer | 9.4/10 |
| @architect-review | 9.0/10 |
| **Average** | **9.07/10** |

**Files:**

- `CLAUDE.md` (11 targeted edits across dashboard, Phase REP,
  infrastructure, Quick Start Checklist, version footer)
- `CLAUDE_CHANGELOG.md` (165-B hash fill + Session 161
  correction appended)
- `docs/REPORT_166_A.md` (new completion report)

**Commit:** `82a8541`.

---

### Session 165 — April 21, 2026 (Deployment Safety Hardening)

**Two-spec session.** 165-A added the Procfile release phase so
future deploys apply pending migrations automatically. 165-B
resolved the first model-vs-migration drift that the newly-active
release phase surfaced on its first deploy — structural deployment
safety doing its job on day one.

**Specs:**
- **165-A** (commit `4d874d4`): Procfile release phase +
  CLAUDE.md note + CLAUDE_CHANGELOG entry
- **165-B** (commit `a457da2`): Migration 0086 aligning
  `UserProfile.avatar_url` migration state with current model
  definition (no-op SQL)

---

**165-A — Procfile Release Phase.** Adds `release: python
manage.py migrate --noinput` to Procfile so future deploys apply
pending migrations automatically before new code starts serving
traffic.

#### ⚠️ 2026-04-20 Production Near-Miss

After Session 163's avatar pipeline rebuild was deployed (v758),
production served 500s for ~12 minutes because migration 0085
did not run automatically on deploy. Root cause: the Procfile
declared only `web` and `worker` process types — no `release`
phase was defined, so Heroku skipped the migration step entirely.

Heroku's build output confirmed: `Procfile declares types -> web,
worker`. v758 code expected `prompts_userprofile.avatar_url` and
`prompts_userprofile.avatar_source` columns; the production
schema still had the pre-0085 columns (`avatar`, `b2_avatar_url`).
Every page that loaded a UserProfile failed with
`django.db.utils.ProgrammingError: column
prompts_userprofile.avatar_url does not exist`.

**Impact:**
- 12 minutes of 500s on UserProfile-touching pages
- 1 visible 500 in the log tail (AhrefsBot crawler hitting the
  homepage with a tag filter)
- Real users essentially unaffected — low-traffic window,
  affected only crawlers
- Recovery: developer ran
  `heroku run python manage.py migrate prompts --app mj-project-4`
  manually after noticing the missing release-phase line

**Why this matters:** The 2026-04-19 incident applied a migration
to production accidentally (via env.py's DATABASE_URL). The
2026-04-20 near-miss FAILED to apply a migration to production
when it should have (via the missing release phase). Mirror-image
failure modes around the same migration. Together they justify
structural deployment safety, not just procedural discipline.

**Remediation — structural:** This session's Procfile change. Every
future `git push heroku main` will run `python manage.py migrate
--noinput` during release phase before web dynos start serving
the new code. If migration fails, release fails, traffic stays on
the previous release. The schema-vs-code window cannot occur.

**Lesson:** Heroku's release phase is opt-in. Repos that have never
needed it can drift into production with no migration automation
for years before a schema change exposes the gap. New Heroku apps
should add `release: python manage.py migrate --noinput` from day
one, even when they have no migrations yet.

#### Specs (Session 165 combined)

| Spec | Commit | Scope | Agent Avg | Agents ≥ 8.0 |
|------|--------|-------|-----------|--------------|
| 165-A | `4d874d4` | Procfile release phase + CLAUDE.md note + CLAUDE_CHANGELOG entry | 9.18/10 | 6/6 |
| 165-B | `a457da2` | Migration 0086 aligning `UserProfile.avatar_url` field-state with model (no-op SQL) | 9.23/10 | 6/6 |

#### Key decisions

- **`--noinput` flag** — required to prevent migrate from prompting
  for confirmation on destructive operations in non-interactive
  release-dyno context
- **`python` (no version suffix)** — matches the existing `worker`
  line's convention. Heroku's Python buildpack pins the version
  via `.python-version`
- **No collectstatic in release** — Heroku Python buildpack already
  runs `collectstatic --noinput` during build. Adding to release
  would be redundant work and slow every deploy
- **No `--check` before migrate** — would add latency without
  benefit; if migrations fail, the release fails either way
- **Separate from env.py policy** — env.py prevents migrations from
  leaking onto production from a developer machine; release phase
  ensures migrations DO apply on production via the proper channel.
  Complementary, not overlapping
- **Existing `web` + `worker` lines preserved byte-for-byte** — no
  tidying, no flag changes. Only the new `release` line was
  appended

#### Files changed

- `Procfile` — appended one line
- `CLAUDE.md` — new `### Heroku Release Phase` subsection added
  after `### Production Infrastructure Notes`, cross-referencing
  the env.py policy note
- `CLAUDE_CHANGELOG.md` — this entry

#### Test count

Unchanged (1364). Procfile is not testable via Django's test
suite (Heroku reads it, Django doesn't). The real test is the
next deploy that includes a pending migration — but the developer
should not deploy a synthetic migration just to test this. Trust
the Heroku release-phase mechanism (well-documented, widely used).

---

**165-B — UserProfile.avatar_url field-state drift fix.**
Adds migration 0086 aligning migration state with the current
model definition. No-op SQL at the PostgreSQL level.

#### 2026-04-21 — Post-Deploy Drift Discovery (165-B)

When 165-A deployed (v759, 2026-04-21) and the newly-active
release phase ran its first `manage.py migrate`, Django reported:

```
No migrations to apply.
Your models in app(s): 'django_summernote', 'prompts' have changes
that are not yet reflected in a migration, and so won't be applied.
```

Local diagnosis via `makemigrations --dry-run prompts`:

```
Migrations for 'prompts':
  prompts/migrations/0086_alter_userprofile_avatar_url.py
    ~ Alter field avatar_url on userprofile
```

**Root cause:** `UserProfile.avatar_url` in `prompts/models.py`
has an updated `help_text` (set in Session 163-B, commit
`de75e9c`), but migration 0084 (`0084_add_b2_avatar_url_to_user
profile.py`) recorded the ORIGINAL help_text from when the field
was named `b2_avatar_url`:

- **0084 help_text (stale):** "B2/Cloudflare CDN URL for avatar
  (replaces Cloudinary). Populated by migrate_cloudinary_to_b2
  management command. Templates should check this first, fallback
  to Cloudinary avatar."
- **Model help_text (current, 163-B):** "B2/Cloudflare CDN URL
  for avatar. Empty string means the user has no uploaded avatar;
  the letter-placeholder is rendered instead. Written by the
  direct-upload flow (163-C) and social-login capture (163-D)."

Migration 0085 renamed `b2_avatar_url` → `avatar_url` but did NOT
update the help_text. The field class remained `URLField`
throughout (spec's original diagnosis was slightly off — the drift
is help_text-only, not field class — but the fix mechanism
is identical).

Both values are `varchar(500)` in PostgreSQL, and help_text is a
Django introspection concern, not a database concern. `sqlmigrate`
confirms the migration is a pure no-op at the PostgreSQL column
level.

**Drift origin:** single commit `de75e9c` ("feat(models): drop
CloudinaryField from UserProfile + avatar_url + avatar_source",
Session 163-B). Both the model help_text change and migration
0085 were in the same commit, but 0085 only renames the field —
it does not re-declare field metadata (Django's `RenameField`
operation preserves the field class and metadata from the previous
migration).

**Resolution:** Migration 0086 generated via
`python manage.py makemigrations prompts`. Contains a single
`AlterField` operation realigning migration state to the current
model's help_text (field class URLField unchanged). Verified via
`python manage.py sqlmigrate prompts 0086` that SQL is a no-op
(`BEGIN; -- (no-op) COMMIT;`). Behavioral effect on runtime:
none. The migration is a metadata-only record update for Django's
migration state tracker.

**django_summernote drift:** out of scope. Known upstream package
quirk, not our code. Added to Deferred items below.

#### Why 165-B is in Session 165 (not its own session)

165-A's release-phase work *surfaced* this drift on the first
deploy after activation. Keeping both specs in Session 165
documents the complete "we added release phase → release phase
surfaced a pre-existing drift → we fixed the drift" arc as a
single narrative. Structural deployment safety doing its job on
day one.

#### Key decisions (165-B)

- **Generated via makemigrations, not hand-authored** — Django's
  autogeneration is the correct tool; hand-authoring invites
  subtle divergences from actual model state
- **Dry-run first, then real generation** — spec-mandated guard
  against unexpected additional drift surfacing during file
  generation. Dry-run output matched exact expected pattern
  (one migration, one AlterField, avatar_url only) before real
  generation ran
- **`sqlmigrate` verification before trusting the fix** —
  confirms PostgreSQL sees no column change, so production
  migration will be a metadata-only update to the
  `django_migrations` table
- **No data migration** — every existing avatar_url value is
  either a valid URL (from Session 163-C's direct-upload
  pipeline) or an empty string (field default). No data touched
- **No hand edits to the generated migration** — Django's
  autogeneration produces canonical output; editing would
  invalidate the sqlmigrate verification
- **Kept in Session 165 rather than 166** — 165-A surfaced this
  drift; narrative cohesion matters for institutional memory
- **Diagnosis discrepancy noted, not papered over** — spec
  diagnosed "CharField vs URLField" drift; actual drift is
  help_text-only. Fix mechanism is the same (autogenerated
  `AlterField`). Documented in completion report Section 6 so
  future readers know the spec's diagnosis ran slightly ahead
  of the evidence

#### Files changed (165-B)

- `prompts/migrations/0086_alter_userprofile_avatar_url.py` (new,
  autogenerated)
- `CLAUDE_CHANGELOG.md` (this 165-B subsection added, Session
  165 heading + preamble updated to two-spec scope, 165-A
  commit hash filled in, Specs table expanded)
- `PROJECT_FILE_STRUCTURE.md` (migration count + latest-migration
  reference updated from 0085 → 0086)

#### Test count (165-B)

Unchanged (1364). No new tests required — the change is migration
state alignment, not behavior. Existing `UserProfile` tests
continue to pass because the field-class change (help_text) does
not affect runtime read/write behavior on existing data.

#### What happens on next deploy

When developer next runs `git push heroku main`, release phase
will run `manage.py migrate` and apply migration 0086. Expected
release log:

```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying prompts.0086_alter_userprofile_avatar_url... OK
```

The `django_summernote` drift warning will continue to appear
(out of scope). The `prompts` app warning will disappear.

**This is also the first real test of release-phase auto-applying
a migration** (165-A's deploy had "No migrations to apply").
Expected duration: 2–5 seconds on the release dyno.

---

#### Deferred items (Session 165 combined, carried forward from prior sessions)

- Google OAuth credentials configuration (Session 163-D plumbing
  inert until done)
- Single generator implementation (Phase SUB prerequisite)
- Phase SUB implementation (Stripe + credit enforcement)
- Extension-mismatch B2 orphan keys (Session 163-C P2)
- CDN cache staleness for OTHER viewers post avatar update
  (Session 163-C P3)
- Non-atomic rate-limit increment (Session 163-C P3)
- AvatarChangeLog model rename (Session 163-A Gotcha 8)
- Prompt model CloudinaryField → B2 migration
- **django_summernote migration drift** — upstream package quirk
  surfaced by 165-A's release phase. Third-party, not our code.
  Will continue to show a "changes not yet reflected" warning on
  every deploy. No action unless it starts causing actual issues

---

### Session 164 — April 20, 2026 (Monetization Strategy Restructure)

**Focus:** Complete monetization strategy documentation for Phase
SUB launch. Restructure tier pricing (supersedes Session 154 4-tier
framework), document upgrade psychology, capture reasoning for
future decisions.

**Documentation changes:**

- **CLAUDE.md** — "Business Model & Monetisation Plan" subsection
  rewritten with 3-tier launch structure. Four new H2 sections
  added: "Monetization Strategy & Upgrade Psychology",
  "Profitability Targets & Market Context", "Credit System Design
  Principles", "Post-Launch Recommendations". Net addition
  approximately 860 lines.
- **CLAUDE_CHANGELOG.md** — this entry.
- **Session 154 changelog entry** not modified; stays frozen as
  historical record of original 4-tier decision.

**Key decisions (supersedes Session 154 where conflicting):**

- **3 tiers at launch** (Free + Pro + Studio), not 4. Creator tier
  ($9) deferred to Month 4–6 pending signal data. Reasoning: no
  user data yet to validate 4-tier segmentation; choice paralysis
  hurts conversion; Creator tier strategically weakest without
  bulk generator; learning priority favors cleaner data.
- **Launch pricing:** Pro $14/mo (~~$19~~), Studio $39/mo (~~$49~~)
  with annual discount of ~18%. Regular pricing: Pro $19/mo,
  Studio $49/mo.
- **Grandfather launch pricing to annual subscribers forever**
  (while subscription continuously active); monthly subscribers
  get 3 months at launch rate then auto-transition.
- **Launch pricing ends** after first 200 annual subscribers OR
  6 months post-launch, whichever first.
- **Credit system: 100:1 internal ratio** (never exposed to
  users). Markup 14–27% per model above raw API cost with
  psychological rounding.
- **Model lineup corrected:** Flux Schnell, GPT-Image-1.5 (BYOK),
  Flux Dev, Flux 1.1 Pro, FLUX 2 Pro, Grok Imagine, Nano Banana 2
  (1K/2K/4K), FLUX 2 Pro 4MP HD. Studio-only access for 4K and
  HD variants.
- **Free tier:** 100 one-time signup credits, Flux Schnell only.
  No recurring free credits.
- **No trial at launch.** Free tier IS the trial. Re-evaluate
  trials Month 2–3 based on conversion data.
- **Stripe metadata tracking required at launch** for conversion
  attribution (trigger_feature, trigger_source, previous_tier,
  time_on_free_tier_days, generations_consumed_pre_upgrade,
  launch_pricing_applied).
- **Welcome email sequence** (Day 1, 3, 7, 14, 28) required at
  launch, regardless of trial structure.
- **Visible cap counters** in UI rather than hidden. Color-coded
  (neutral → amber → red → block).
- **Countdown timer** during last 7 days of launch pricing only.
  Real deadline, no resetting, tiered urgency, dismissible but
  reappears after 24 hours.
- **Studio priority processing** for bulk generation jobs (Studio
  jobs dequeue before Pro jobs).
- **Anonymous browsing:** 100 views before login wall, modal
  every 50 views. Logged-in Free: 200 views/day.

**Deferred items (timing noted):**

- Creator tier ($9) — Month 4–6 pending 4 specific signals
- Formal trial period (CC-required) — Month 2–3 pending
  conversion data
- Referral program — Month 3+ post-launch (after conversion
  mechanics validated)
- Advanced search filter tier gating — after filter feature ships
- Visible cap counter UI implementation — during Phase SUB
  frontend work

**Supersedes (from Session 154):**

- 4-tier structure (Starter/Creator/Pro/Studio)
- Original credit pricing table (some credit costs changed)
- Annual discount of ~22% (now 18% standard; 22% reserved for
  promotional campaigns)

**Does NOT supersede:**

- OpenAI BYOK architecture (Session 154)
- Replicate/xAI platform mode (Session 154)
- `GeneratorModel` as single source of truth (Session 154)
- Scheduled promotions via `scheduled_available_from/until`
  (Session 154)
- Content seeding before monetisation sequencing (Session 154)

**Agents:**

| Agent | Score | Key Findings |
|---|---|---|
| @technical-writer | 8.9/10 | Institutional-memory writing textbook-quality. Voice matches existing CLAUDE.md. H2 emoji pattern integrates. Worked examples (NB2, Grok, Flux Schnell margin floor) concrete and useful. Minor non-blocking nits on unsourced benchmarks and word repetition. |
| @code-reviewer | 9.2/10 | All 8 factual-accuracy checks PASS. Pricing reconciles across all sections. All 10 credit-cost rows match canonical lineup. Markup arithmetic verified. Annual discount math verified (17.9%/17.1%/17.9%/18.4%). Scale milestone at 500 subs verified. Session 154 preserved. |

**Avg:** 9.05/10. **Both ≥ 8.0.**

**Next steps:**

- Phase SUB implementation spec (Stripe integration, credit
  enforcement, cap logic, hover-to-run teaser, welcome email
  sequence, Stripe metadata tracking)
- Single generator implementation (prerequisite for hover-to-run)
- Social login activation (independent track)

---

### Session 163 — April 20, 2026 (Avatar Pipeline Rebuild)

**Focus:** Drop Cloudinary from UserProfile entirely. Rebuild avatar
upload with B2 direct flow. Add social-login avatar capture plumbing
(Google scope). Session ran as v2 after a 2026-04-19 production
incident — see incident section below.

**Specs:** 163-A (read-only investigation, committed pre-v2 redesign),
163-B (model cleanup + migration 0085), 163-C (B2 direct upload
pipeline), 163-D (social-login signal plumbing), 163-E (sync-from-
provider button), 163-F (this docs rollup).

**Migrations:** 1 new — `0085_drop_cloudinary_avatar_add_avatar_source`
(three atomic operations: RemoveField avatar, RenameField
`b2_avatar_url`→`avatar_url`, AddField `avatar_source`
CharField with 5 choices).

---

#### ⚠️ 2026-04-19 Production Incident

During the first (v1) attempt at 163-B, migration 0085 was
inadvertently applied to the production Heroku Postgres database by a
local `python manage.py migrate prompts` command.

**Root cause:** `env.py` (gitignored, local-dev config) contained
`os.environ.setdefault("DATABASE_URL", "postgres://...")` pointing at
the production cluster. The line had been there for a long time with
an innocuous comment ("production database for local testing"). No
local `migrate` had ever been run while it was active, so the loaded
gun went unnoticed. When 163-B's Phase 2 developer-run migration fired
locally, Django followed the `DATABASE_URL` env var straight to prod
— migrating the live cluster instead of SQLite.

**Impact:**
- Production schema drifted from deployed code (v757 still expected
  `avatar` column; DB had `avatar_url` + `avatar_source` instead)
- Every page that loaded a UserProfile returned 500
- ~30 minutes of outage before recovery completed
- **Zero data loss** — no avatars existed in production (the April 19
  diagnostic run had already confirmed 0 legacy avatars on production)

**Recovery:**
- Manual SQL on the production cluster restored the 0084 schema: ADD
  COLUMN `avatar` (Cloudinary field), RENAME `avatar_url` back to
  `b2_avatar_url`, DROP `avatar_source`
- Deleted the stale 0085 row from production's `django_migrations`
  table so Heroku redeploys would see 0084 as the head
- 163-B code rolled back on the local branch (migration file, test
  file, partial report deleted; working tree reverted)

**Remediation — structural, not just procedural:**
- `env.py` edited: the `DATABASE_URL` line commented out with a
  deactivation block citing this incident. Local dev now falls
  through to `settings.py`'s SQLite fallback (`db.sqlite3`)
- `settings.py` verified — when `DATABASE_URL` is unset, Django uses
  SQLite. Confirmed via `python -c "import env; ..."`
- Session 163 specs redesigned as v2:
  - **env.py safety gate** added at the top of every code spec (a
    pre-work grep + Python check that `DATABASE_URL` is unset)
  - Migration commands explicitly marked **DEVELOPER RUNS THIS** with
    a prohibition note in every spec header
  - 163-B restructured into three phases: **CC prepares**, developer
    runs migration, **CC verifies** (Phase 1/2/3 handoff)
  - Run instructions redesigned with check-ins at migration
    boundaries

**Lesson:** Gitignored config files can contain loaded guns that
don't surface until the right (wrong) command fires. Investigation
specs should explicitly read and flag config file contents as a
risk surface. The 163-A investigation DID read env.py but treated
it as a reference, not a risk.

Future sessions: if the v2 safety pattern (env.py gate, no-migrate-by-
CC, three-phase migration handoff) proves durable, it may be codified
into CC_SPEC_TEMPLATE. For now it lives in Session 163's run
instructions and the per-spec safety gates. Decision deferred per
163-F Section 4.

---

#### Specs

| Spec | Commit | Scope | Agent Avg | Agents ≥ 8.0 |
|------|--------|-------|-----------|--------------|
| 163-A | `a0b99e2` | Read-only avatar pipeline investigation (pre-incident) | 9.3/10 | 2/2 |
| 163-B | `de75e9c` | Migration 0085: drop CloudinaryField, rename → `avatar_url`, add `avatar_source`. Admin + 6 templates updated. Three-phase protocol. | 8.8/10 | 6/6 |
| 163-C | `785ffa7` | B2 direct upload pipeline: new presign endpoints, `avatar_upload_service`, `avatar-upload.js`, `edit_profile.html` rewrite. | 8.7/10 | 6/6 (one round 2 to re-pass ≥ 8.0) |
| 163-D | `b4069ad` | Social-login plumbing: `AUTHENTICATION_BACKENDS`, `SOCIALACCOUNT_PROVIDERS['google']`, `OpenSocialAccountAdapter`, `social_signals.py`, `social_avatar_capture.py`. PyJWT dep added. | 8.76/10 | 7/7 |
| 163-E | `76951b5` | "Sync from provider" button on `edit_profile`. Shared rate bucket prevents bypass. Ownership guard + `types.SimpleNamespace`. | 8.57/10 | 7/7 |
| 163-F | (this) | End-of-session docs rollup (including incident section). | — | 2/2 |

#### Key decisions

- **Single migration 0085** holding three atomic operations rather
  than three separate migrations — simpler rollback, Django
  transaction wraps all ops atomically on Postgres.
- **Rename `b2_avatar_url` → `avatar_url`** (not kept as dual field)
  — April 19 confirmed 0 avatar data in production, so a clean rename
  is safe. Future avatar systems will just use `avatar_url`.
- **`avatar_source` CharField with 5 choices** (default/direct/google/
  facebook/apple) — db_index=True; enables filtering
  `UserProfile.objects.filter(avatar_source='direct')` for admin
  reporting.
- **Extend `b2_presign_service`** (not fork) — `generate_upload_key`
  accepts `folder`/`user_id`/`source`; avatars folder returns
  deterministic key `avatars/<source>_<user_id>.<ext>` so re-uploads
  overwrite rather than orphan.
- **BOTH allauth signals** (`user_signed_up` AND `social_account_added`)
  — per 163-A R5. First-time signup uses one; existing password user
  linking Google uses the other. Neither alone covers both cases.
- **Google-first, extensible later.** Facebook + Apple providers not
  configured in settings; their URL extractors exist but return None.
  Adding a new provider is a trivial settings diff when ready.
- **`force=False` default** preserves user-uploaded avatars. 163-E's
  sync button is the only call site that passes `force=True`.
- **Distinct session + cache keys for avatar upload** per 163-A Gotcha
  4: `pending_avatar_upload` session key, `b2_avatar_upload_rate:{user.id}`
  cache key. Prevents cross-contamination with prompt-upload flow.
- **Shared cache key between 163-C direct and 163-E sync** — both
  flows count against the same 5/hour bucket to prevent bypass via
  alternating.

#### v2 protocol decisions (new)

- **Migration handoff protocol:** CC prepares migration file + code
  changes (Phase 1), developer runs `python manage.py migrate`
  (Phase 2), CC verifies schema + runs tests (Phase 3). This is the
  post-incident pattern.
- **env.py safety gate** at the top of every code spec — grep +
  Python check that `DATABASE_URL` is NOT SET.
- **Explicit prohibition on CC running `migrate` commands.** Even
  when tests pass locally. Even when the developer has "already run
  it." CC verifies with `showmigrations`, never `migrate`.

#### Absorbed cross-spec fixes (Rule 2)

- **163-C** — `presignResp.ok` check in `avatar-upload.js` (flagged
  by `@frontend-developer`); `<label for="avatar-file-input">` for
  a11y; `profile.full_clean(exclude=['user'])` in
  `avatar_upload_complete` view (architect-review); removed unused
  `_extension_for_content_type` import.
- **163-D** — `follow_redirects=False` on `httpx.Client` (SSRF
  hardening, flagged by both `@backend-security-coder` and
  `@architect-review`); happy-path test for `_download_provider_photo`
  added (tdd-orchestrator).
- **163-E** — `types.SimpleNamespace` replaces ad-hoc `_FakeSocialLogin`
  local class (python-pro + architect-review); `aria-live="polite"
  aria-atomic="true"` on `#avatar-sync-status` (frontend-developer).

#### Deferred items (see individual REPORT_163_* Section 5 for detail)

- **Google OAuth credentials** — developer must configure
  `GOOGLE_OAUTH_CLIENT_ID` + `_CLIENT_SECRET` on Heroku OR create a
  Google `SocialApp` admin row before the social-login path
  activates end-to-end.
- **Facebook + Apple providers** — extractor stubs exist; add
  entries to `SOCIALACCOUNT_PROVIDERS` when ready.
- **`AvatarChangeLog` rename** — schema unchanged per 163-A Gotcha 8.
  Field still named `cloudinary_url` even though avatars are now B2.
  Cosmetic; defer.
- **CloudinaryField → CharField migration on Prompt** — separate spec
  after every prompt has `b2_image_url` populated. Requires data
  migration to preserve stored public_ids.
- **Bare `except Exception:` audit** (carried forward from Session
  162-E) — narrow to specific exceptions where safe.
- **Admin CAPTCHA** and **Google Authenticator for admin 2FA** —
  carried forward.
- **Streaming download for provider photo size cap** (163-D Section
  5, P3) — use `client.stream('GET', url)` + running byte counter.
- **Avatar rate-limit helper consolidation** (163-E Section 5, P3)
  — DRY the 163-C + 163-E atomic `cache.add`/`cache.incr` pattern.

#### Files added

- `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py` (163-B)
- `prompts/services/avatar_upload_service.py` (163-C)
- `static/js/avatar-upload.js` (163-C)
- `prompts/services/social_avatar_capture.py` (163-D, 163-E extended)
- `prompts/social_signals.py` (163-D)
- `prompts/tests/test_userprofile_163b_schema.py` (163-B, 7 tests)
- `prompts/tests/test_avatar_upload.py` (163-C, 19 tests)
- `prompts/tests/test_social_avatar_capture.py` (163-D, 26 tests)
- `prompts/tests/test_avatar_sync.py` (163-E, 9 tests)
- `docs/REPORT_163_A.md` through `docs/REPORT_163_F.md`

#### Files removed (content, not files)

- `UserProfileForm.clean_avatar()` method (163-B)
- `UserProfileForm.avatar` ImageField (163-B)
- `store_old_avatar_reference` + `delete_old_avatar_after_save`
  signal handlers in `prompts/signals.py` (163-B — Option A, no
  B2 cleanup needed because deterministic keys overwrite)
- `_migrate_avatar` method in `migrate_cloudinary_to_b2` (163-B
  follow-up — no avatar data existed in production)
- `fix_admin_avatar.py` management command + its README (163-B —
  Cloudinary-specific, obsolete)
- `test_edit_profile_html_not_modified_by_163b` (163-F suite gate —
  obsolete scope-bleed guard; 163-C legitimately owns the template)
- `env.py` `DATABASE_URL` production setting (2026-04-19 incident
  remediation; kept as commented deactivation block with context)

#### Commits (chronological, Session 163 total = 5)

| Commit | Message |
|--------|---------|
| `a0b99e2` | docs(investigation): 163-A avatar pipeline investigation report |
| `de75e9c` | feat(models): drop CloudinaryField from UserProfile + avatar_url + avatar_source |
| `785ffa7` | feat(avatars): direct upload pipeline — B2 presign + edit_profile rebuild |
| `b4069ad` | feat(avatars): social-login avatar capture — allauth signal plumbing |
| `76951b5` | feat(avatars): "Sync from provider" button on edit_profile |
| (163-F hash) | END OF SESSION DOCS UPDATE: session 163 — avatar pipeline rebuild |

#### Test count

1321 → 1364 (+43 net). 61 new tests added across four new files:
7 schema (`test_userprofile_163b_schema.py`), 19 upload
(`test_avatar_upload.py`), 26 social capture
(`test_social_avatar_capture.py`), 9 sync (`test_avatar_sync.py`).
Offset by ~18 tests removed / consolidated in the 163-B cleanup —
`test_avatar_templates_b2_first.py` rewritten (23 → 10 tests: the
3-branch pattern had more permutations to cover than the 2-branch
replacement), `test_migrate_cloudinary_to_b2.py` avatar class
removed (11 → 6 tests), and one obsolete scope-guard test
(`test_edit_profile_html_not_modified_by_163b`) deleted in 163-F's
suite gate after 163-C legitimately took ownership of the template.
12 skipped unchanged. Full suite OK.

---

### Session 162 — April 19, 2026

**Focus:** Close Session 161's Cloudinary migration cleanup. Ship the
xAI SDK billing→quota alignment that has been deferred five sessions
since 156. Codify Session 161 retrospective findings into
CC_SPEC_TEMPLATE v2.7. Ran as a two-batch session (162a: specs A, B,
C, H; 162b: specs D, E, G).

**Specs:** 162-A (queryset filter), 162-B (avatar templates B2-first),
162-C (vision_moderation public_id), 162-D (xAI SDK billing→quota),
162-E (narrow bare except), 162-H (template v2.7), 162-G (this docs
update).

**Tests:** 1321 passing (1286 + 35 new across 162-A/B/C/D/E — 9 in
162-A, 23 in 162-B, 4 in 162-C, 2 in 162-D, 3 in 162-E; 162 total
delta accounts for test-scaffolding consolidations during review),
0 failures, 12 skipped.

**Migrations:** No new migrations in Session 162.

**Key outcomes:**

- **162-A — Cloudinary migration queryset filter fix:** root cause
  was SQL `WHERE col IN ('', NULL)` returning UNKNOWN for NULL rows
  (three-valued logic). Broken queryset reported 0 migratable
  records despite production holding 36 legacy images + 14 legacy
  videos. Fixed via Q-objects:
  `Q(b2_image_url='') | Q(b2_image_url__isnull=True)` across image,
  video, and avatar filters. Integration tests use real ORM rows
  (Rule 1) — the original SimpleNamespace mocks in 160-F/161-A were
  what let this survive 12 agent reviews across two sessions.
  Absorbed a cross-spec print-condition fix (Rule 2) so dry-run
  batches <10 records now surface "would-migrate" status to stdout.
  Agents avg 9.07/10. Commit `67aa0ad`.

- **162-B — Avatar templates B2-first:** six avatar-rendering
  templates now use the three-branch B2-first pattern
  (`b2_avatar_url` → Cloudinary `avatar.url` → letter placeholder),
  preparing the rendering layer for Session 163 F1's upload pipeline
  switch. `edit_profile.html` explicitly reserved for Session 164 F2
  — its `{% cloudinary %}` face-crop transform has no direct B2
  equivalent until the upload pipeline lands. 23 tests (7 structure
  + 16 render). Agents avg 9.0/10. Commit `ad94533`.

- **162-C — vision_moderation public_id pattern:** four call sites
  across `vision_moderation.py` and `fix_cloudinary_urls.py` moved
  from `str(CloudinaryField_value)` to explicit
  `getattr(..., 'public_id', ...) or (...)` three-branch extraction.
  **Key discovery during implementation:** the spec's premise — that
  `str(CloudinaryResource)` returns an object repr — is FACTUALLY
  INCORRECT for the current cloudinary SDK. A direct test showed
  `str(CloudinaryResource(public_id='legacy/foo')) == 'legacy/foo'`.
  The earlier 161-A claim that `str()` returned repr was wrong. The
  fix is still independently justified: the real latent bug is
  `str(None) == 'None'` producing `'legacy/None.jpg'` URLs when the
  field is null; the new pattern resolves to `''` instead. 4 tests.
  Agents avg 8.58/10. Commit `d3b92dd`.

- **162-D — xAI primary SDK path billing→quota alignment:** one-line
  fix closing a gap deferred since Session 156. The SDK path
  returned `error_type='billing'` which had no handler in
  `tasks._apply_generation_result`, so billing exhaustion fell into
  the generic retry loop and wasted credits. Now returns
  `error_type='quota'` matching the httpx-direct edits path fixed in
  161-F. Static error message (no f-string interpolation of raw
  exception) mirrors 161-F's no-leak decision. 2 regression tests:
  paired positive/negative routing assertion, and a secret-leak
  regression guard. Agents avg 8.83/10. Commit `18a918e`.

- **162-E — Narrow bare except in bulk generator job view:** the
  `except Exception:` around provider-registry cost lookup was
  swallowing all failures silently and falling back to OpenAI cost
  map — visible as wrong prices on Replicate/xAI job pages with no
  log signal. Narrowed to
  `except (ValueError, ImportError, AttributeError, KeyError) as e:`
  with `logger.warning(...)` added. Step 0 grep of
  `image_providers/registry.py:39` confirmed `get_provider` raises
  `ValueError` (not `KeyError` as the spec draft assumed) — tuple
  adjusted accordingly. Fallback behavior intentionally unchanged
  — this is purely observability hardening. 3 regression tests
  (happy path, ValueError + 5 log-content assertions, TypeError
  propagation proving the narrowing works). Agents avg 9.03/10.
  Commit `a872a11`.

- **162-H — CC_SPEC_TEMPLATE v2.7:** three new rules codifying
  Session 161's retrospective findings. (1) Queryset Integration
  Test Rule — SimpleNamespace mocks are explicitly disallowed for
  queryset tests; must use real ORM rows with refresh_from_db.
  Evidence: 160-F → 161-A → 162-A queryset bug chain. (2)
  Cross-Spec Bug Absorption Policy — agent-flagged bugs under 5
  lines in files already being edited must be absorbed, not
  deferred. Evidence: xAI SDK billing→quota was flagged in Session
  156, re-flagged in 161-F, and finally shipped in 162-D — five
  sessions carrying a one-line fix. (3) Stale Narrative Text Grep
  Rule — any spec changing existing behavior must grep for
  narrative text describing the old behavior before writing code.
  Evidence: 161-E shipped with an "avatar NOT supported" docstring
  caught by @django-pro at 9.0/10 requiring a follow-up.
  `CC_COMMUNICATION_PROTOCOL.md` version bumped to match. Agents
  avg 9.2/10. Commit `e90f9b3`.

**Documentation correction (161-A claim):** CLAUDE.md and
REPORT_161_A had stated that `str(CloudinaryResource)` returned the
object repr. Per 162-C direct test evidence, the current cloudinary
SDK's `CloudinaryResource.__str__` returns `self.public_id`.
CLAUDE.md lines 78 and 1588 corrected in 162-G. The underlying bug
that 161-A fixed remains real — `str(None)` returning `'None'` for
NULL CloudinaryField values — but the "repr" framing was incorrect.

**Process lessons captured in template v2.7:**

- Agent reviews pass vacuously when test scaffolding bypasses the
  code path under test. `SimpleNamespace(public_id=...)` mocks must
  be rejected for queryset tests.
- Over-rigid scope discipline carries costs. Deferring an
  obviously-right 1-line fix for 5 sessions wasted real money every
  time xAI billing exhausted.
- Specs that describe old behavior in prose need a Step 0 grep for
  that prose before implementation — otherwise comments/docstrings
  drift into saying one thing while code does another.

**Commits (chronological, Session 162 total = 7):**

| Spec | Hash | Message |
|------|------|---------|
| 162-A | `67aa0ad` | fix(migration): Cloudinary migration command — filter NULL rows correctly |
| 162-B | `ad94533` | feat(templates): avatar templates prefer b2_avatar_url over Cloudinary |
| 162-C | `d3b92dd` | fix(moderation): use .public_id not str() on CloudinaryResource |
| 162-H | `e90f9b3` | docs(template): CC_SPEC_TEMPLATE v2.7 — integration tests + absorption |
| 162-D | `18a918e` | fix(providers): xAI primary SDK path — billing → quota alignment |
| 162-E | `a872a11` | fix(views): narrow bare except in bulk generator job view |
| 162-G | (this commit) | END OF SESSION DOCS UPDATE |

**Deferred to Session 163:**

- **F1 — Avatar upload pipeline Cloudinary → B2 (P1).** 162-B
  prepared the rendering layer; F1 is the upload-side switch.
  Investigation prerequisite confirmed via grep on April 19 2026:
  zero writes to `b2_avatar_url` exist in `prompts/*.py` outside the
  migration command and its tests — the `edit_profile` form still
  writes to Cloudinary. F1 is a high-risk session; gets its own
  isolated run.

**Deferred to Session 164:**

- **F2 — edit_profile.html B2-aware avatar display with CSS
  `object-fit: cover` (Option 2 cropping).** Depends on F1 landing
  in production. Reserved from 162-B as out-of-scope.

**Deferred to later sessions:**

- 8 other bare `except Exception:` blocks in `bulk_generator_views.py`
  (lines 783, 847, 988, 1154, 1356, 1445, 1550, 1569) — structural
  audit pass flagged by @architect-review in 162-E. P2.
- `_download_image` TransportError catch in xAI provider (P3, 161-F
  Section 6).
- `_download_image` deduplication between Replicate/xAI providers
  (P3, pre-existing).
- 6 remaining f-string leak paths in `xai_provider.py` at lines 187,
  200, 211, 290, 309, 363 — would need dedicated regression tests;
  too large to absorb in 162-D. P2.
- `fix_admin_avatar.py` `str(CloudinaryResource)` cleanup (P3,
  diagnostic logs only, 162-C scope excluded).
- SSRF hardening of `_fetch()` — `urllib.parse.quote(public_id,
  safe='/')` + stricter host match (P3, 161-A Section 6).
- `create_job()` mixed-tier QUALITY/SIZE cost accounting for NB2
  jobs (P2, 161-D Section 5).
- Rate Limiting Audit for Replicate + xAI (P2, carried forward
  from 161-G backlog).
- Non-OpenAI semantic fallback correctness in
  `bulk_generator_job_view` — wrong cost displayed when
  registry.get_provider fails for a Replicate/xAI job. 162-E fixed
  observability only; semantic fix (pull cost from
  GeneratorModel.credit_cost as secondary fallback) deferred. P2.
- Field-type migration: `UserProfile.avatar` CloudinaryField →
  CharField; `Prompt.featured_image` / `featured_video`
  CloudinaryField → CharField (after F1 + F2 confirmed in
  production).
- Cloudinary package removal from `requirements.txt` (after
  field-type migration).
- CC_SPEC_TEMPLATE v3.0 consolidation pass — the template is now
  700+ lines; PRE-AGENT SELF-CHECK and policy sections could be
  deduplicated. Noted by @docs-architect in 162-H. P3.

---

### Session 161 — April 18, 2026

**Focus:** Cloudinary migration command fix + avatar support, autosave
AI Direction save/restore + reset clears draft, Reset to master
preserves user content, results page pricing accuracy, Grok httpx
billing + transport error routing.

**Specs:** 161-A through 161-G (5 code specs + 1 migration spec + 1
docs spec).

**Tests:** 1286 passing (1278 + 8 new across 161-A/D/E/F), 0 failures,
12 skipped.

**Key outcomes:**

- **161-A — Cloudinary migration command fix:** B2 credential check
  now uses `B2_ACCESS_KEY_ID`/`B2_SECRET_ACCESS_KEY` (the actual
  Django settings names), not the non-existent
  `B2_APPLICATION_KEY_ID`/`B2_APPLICATION_KEY`. `CloudinaryResource`
  public_id extraction changed from `str(featured_image.public_id)`
  with `str(featured_image)` fallback (returns object repr!) to
  `getattr(..., "public_id", "") or ""`. Dry-run now correctly
  identifies ~36 records on Heroku. Agents avg 8.75/10. Commit
  `220337b`.

  **Correction (Session 162-C investigation):** The pre-fix
  code's `str(featured_image)` was later shown to return
  `self.public_id` in the current cloudinary SDK — NOT object
  repr as originally claimed. The real latent bug the 161-A
  change fixed was `str(None) == 'None'` producing malformed
  URLs when the field was NULL. The `getattr(..., "public_id",
  "") or ""` pattern remains the correct fix regardless
  (defends against both NULL values and future SDK changes).

- **161-B — Autosave AI Direction + Reset clears draft:** the 160-D
  autosave correctly captured `vision_direction` text but the input
  event listener only fired `scheduleSave` for three specific
  classes — `.bg-vision-direction-input` was missing, so typing
  into AI Direction never triggered a save. Fix adds it to the
  OR-chain. Separately, the master Reset button now calls
  `I.clearDraft()` before hiding the modal so refreshing after
  Reset no longer restores pre-reset settings. Hardened
  `clearSavedPrompts()` to also cancel any pending debounce timer
  (TOCTOU fix). Agents avg 9.12/10. Commit `c0595af`.

- **161-C — Reset to master preserves AI Direction:** the per-box
  Reset button was clearing AI Direction checkbox state, row
  visibility, AND textarea text. AI Direction is user-entered
  content and must survive a settings-only reset (same contract as
  prompt text). `resetBoxOverrides()` no longer hides the AI
  Direction row or clears its textarea. Added a 6-line doc comment
  explaining the settings/user-content boundary. Agents avg
  9.12/10. Commit `585fd5f`.

- **161-D — Results page pricing for all models:** root cause was
  the view recalculating `estimated_total_cost` from master-level
  `(total_prompts × images_per_prompt) × master_cost_per_image`
  while ignoring `job.actual_total_images` (the resolved per-prompt
  count) AND the stored Decimal `job.estimated_cost` (computed at
  job creation with resolved counts). Fix uses both stored fields
  with fallback for legacy jobs. Kept Decimal type end-to-end — no
  `float()` conversion, Django `floatformat` renders Decimal
  natively. 2 new regression tests. Agents avg 8.83/10. Commit
  `dbd329c`.

- **161-E — b2_avatar_url field + avatar migration support:** added
  `b2_avatar_url = URLField(max_length=500, blank=True, default='')`
  to `UserProfile` alongside the existing `CloudinaryField('avatar',
  ...)`. Migration 0084 (AddField — PG11+ fast-path, no table
  rewrite). Extended `migrate_cloudinary_to_b2` with
  `_migrate_avatar()` method + `--model userprofile` choice.
  `handle()` refactored into `run_prompts`/`run_profiles` branches.
  Summary now shows Avatars counts. 4 new regression tests. Agents
  avg 8.78/10. Commit `c67d2cd`.

- **161-F — Grok httpx billing + TransportError catch:** the
  httpx-direct edits path (`_call_xai_edits_api`) missed two
  critical error routings. 400 with 'billing' keyword now returns
  `error_type='quota'` (routes to `tasks.py:2617` job-stop logic
  — billing exhaustion is not retryable). `httpx.TransportError`
  (parent of `ConnectError`/`ReadError`/`WriteError`/
  `RemoteProtocolError`) now caught before generic `Exception` and
  returns `error_type='server_error'` for retry via
  `_run_generation_with_retry`. 2 new regression tests. Agents avg
  9.03/10. Commit `f88cccc`.

**Deferred (P2):** The SDK-path billing branch at
`xai_provider.py:173` still uses `error_type='billing'` (not
`'quota'`). Aligning it with the httpx path is a narrow follow-up
spec — noted in REPORT_161_F Section 6.

---

### Session 160 — April 18, 2026

**Focus:** Profanity error UX polish, quality section disabled/greyed
restoration, per-prompt cost fix, full draft autosave unification,
pricing accuracy, Cloudinary → B2 migration command.

**Specs:** 160-A through 160-G (5 code specs + 1 data-migration spec
+ 1 docs spec).

**Tests:** 1278 passing (1274 + 4 new 160-F tests), 0 failures, 12 skipped.

**Key outcomes:**

- **160-A — Profanity error UX:** backend `validate_prompts()` now
  attaches `prompt_num` (1-based) to every error dict AND
  `flagged_words_display` (escaped, comma-joined) to profanity errors
  with non-empty `found_words`. Frontend `showValidationErrors()`
  renders a clickable "Prompt N" anchor for every backend error
  (empty / profanity / duplicate) and wraps triggered word(s) in
  `<strong><em>` via DOM API — no `innerHTML`. Agents avg 8.7/10.
  4 new tests. Commit `968dc0a`.

- **160-B — Quality section disabled + grid fix:** non-quality models
  (Flux Schnell/Dev/Pro, Grok) now show the Quality dropdown visible
  but disabled, greyed, locked to "High". Two-column grid layout
  restored (no gridColumn stretch on Dimensions). CSS classes
  `bg-setting-group--disabled` and `bg-box-override--disabled` apply
  `opacity: 0.75` + `cursor: not-allowed`. Future-proofs per-prompt
  model selection. Agents avg 8.58/10. Commit `f9d0293`.

- **160-C — Per-prompt cost fix:** root cause was `updateCostEstimate`
  had two cost computations — a per-box accumulator respecting
  per-box quality, and a final display block that discarded the
  accumulator for non-BYOK models (NB2) and recomputed from master
  quality. Fix: totalCost accumulator is now the single source of
  truth for all model types. Added `console.warn` for unmapped
  models. Agents avg 8.83/10. Commit `7f1ff8c`.

- **160-D — Full draft autosave:** unified all session state (master
  settings + per-prompt content + overrides + all toggle states)
  into a single versioned JSON blob under `pf_bg_draft`. Replaces
  4 legacy keys (`bulkgen_prompts` and three `pf_bg_*` keys) via
  one-shot migration. Draft persists across page refresh AND after
  generation submit (cleared only by "Clear All Prompts"). Schema
  maps cleanly to future `PromptDraft` server-side model:
  `settings` → `settings_json`, `prompts` → `prompts_json`. Version
  check accepts `>=1 && <=current` for forward-compat. Tier, button
  groups, and all toggles now trigger `scheduleSave`. Agents avg
  8.92/10. Commit `f99b03e`.

- **160-E — Pricing accuracy:** `{{ cost|floatformat:"-3" }}` on the
  results page + `parseFloat(amount.toFixed(3)).toString()` in JS.
  $0.067 now displays as $0.067 (not $0.07); $0.003 as $0.003 (not
  $0.00); $0.04 as $0.04 (trailing zero stripped). Unified input
  page sticky-bar format — dropped the 2-vs-3-decimal split.
  Agents avg 9.0/10. Commit `4db7edd`.

- **160-F — Cloudinary → B2 migration command:** new
  `migrate_cloudinary_to_b2` management command handles 36 legacy
  prompts' featured_image + featured_video fields via existing
  `upload_image` / `upload_video` services. Flags: `--dry-run`,
  `--limit N`, `--model {prompt,all}`. Idempotent, per-record error
  handling, fail-fast B2 credential check, 50MB streaming size cap,
  `res.cloudinary.com` hostname allow-list for SSRF defence. Cloud
  name confirmed `dj0uufabo` (corrected from historical
  `dj0uufabot` typo). Avatar migration deferred — UserProfile lacks
  `b2_avatar_url` field. Developer runs manually on Heroku:
  `--dry-run` → `--limit 3` → full. Agents avg 8.45/10. 4 tests.
  Commit `027f80d`.

- **160-G — Docs update:** This entry + CLAUDE.md Version 4.51 +
  Feature 4 localStorage ↔ server-side section + Draft Versioning
  tier table + Cloudinary Migration Status run sequence +
  PROJECT_FILE_STRUCTURE.md refreshes.

**Blockers / follow-ups:**
- Developer must run the migration command on Heroku and verify
  B2 images load before any Cloudinary code removal.
- Avatar migration requires a future spec to add `b2_avatar_url`
  field + model migration before the command can be extended.
- B2 path prefix (`migrated/` vs interleaved with fresh uploads) is
  a P3 discoverability concern for the eventual Cloudinary audit —
  not a correctness blocker.

### Session 159 — April 2026

**Focus:** Per-prompt box complete fix, profanity feedback, autosave restore,
NB2 progress bar, Cloudinary audit

**Specs:** 159-A through 159-F

**Tests:** 1270 passing, 0 failures, 12 skipped

**Key outcomes:**
- Profanity filter now shows exact triggered words in error message (was
  generic "Content flagged"). html.escape() for XSS defense. 2 new tests.
- Per-prompt boxes: NB2 shows 1K/2K/4K labels (was Low/Medium/High), quality
  hidden entirely for non-quality models (was disabled/greyed), master quality
  group also hidden for consistency, dimensions spans full row when quality
  hidden, results page uses actual_cost from API for per-resolution accuracy.
- Autosave restore: pageshow event handler for bfcache back navigation,
  aspect ratio restored after handleModelChange rebuilds buttons, quality
  label mismatch resolved by 159-B per-box label fix.
- NB2 progress bar stall resolved — root cause: CSS animation QUALITY_DURATIONS
  calibrated for OpenAI (10-40s) but NB2 via Replicate takes 15-50s. Fixed
  with provider-aware durations (data-provider template attribute).
- Cloudinary removal blocked: CloudinaryField used by 3 model fields, 8
  templates use cloudinary_tags, signal handlers call cloudinary.uploader.
  Only unused top-level import in vision_moderation.py removed. Full removal
  requires dedicated migration spec.
- 1270 tests (2 new profanity tests from 159-A).

### Session 158 — April 17, 2026

**Focus:** NB2 per-prompt cost accuracy, opacity cleanup, autosave settings

**Specs:** 158-A (remove opacity), 158-B (per-prompt cost), 158-C (autosave),
158-D (docs)

**Tests:** 1268 passing, 0 failures, 12 skipped

**Key outcomes:**
- Removed inline opacity:0.45 from disabled ref image and quality groups —
  sections now appear at full opacity; cursor state and disabled attrs
  provide sufficient visual feedback (developer confirmed).
- Per-prompt cost now model-aware: BYOK uses COST_MAP, NB2 uses tier costs
  ($0.067/$0.101/$0.151), platform models use _apiCosts. Each prompt box
  reads its own quality selector, not the master dropdown.
- Master header settings (model, quality, aspect ratio) now saved to
  localStorage on every change via PF_STORAGE_KEYS (pf_ namespace).
  Restored on page load — back-navigation and return visits restore
  last-used configuration. No API keys or sensitive data persisted.
  try/catch for private browsing safety.

### Session 157 — April 17, 2026

**Focus:** NB2 cost display accuracy, quality labels, upload zone hover fix,
progress bar fix

**Specs:** 157-A (NB2 labels + JS cost), 157-B (results page cost),
157-C (upload zone hover), 157-D (NB2 progress bar), 157-E (docs)

**Tests:** 1268 passing, 0 failures, 12 skipped

**Key outcomes:**
- NB2 quality dropdown now shows 1K/2K/4K instead of Low/Medium/High.
  Internal option values (low/medium/high) unchanged — only display text.
- Sticky bar cost updates dynamically per NB2 quality tier:
  $0.067 (1K) / $0.101 (2K) / $0.151 (4K). Added NB2_TIER_COSTS dict.
- Results page replaced flat _PROVIDER_COSTS dict with
  provider.get_cost_per_image() — single source of truth for all models.
  NB2 now shows correct per-resolution cost on results page.
- Upload zone hover effect suppressed when model doesn't support reference
  images. New .bg-ref-upload--disabled CSS class toggled in handleModelChange().
  cursor:not-allowed retained; border/background hover visual removed.
- NB2 progress bar stall at ~85% resolved. Root cause: progress bar counted
  only completed images, not generating ones. During download/B2-upload
  phase, images stay in generating status. Fix: progress bar now counts
  completed + generating images. Cost display still uses completed only.

### Session 156 — April 16, 2026

**Focus:** Phase REP production readiness — Grok reference image fix,
cost display audit + fix, FLUX 2 Pro, Nano Banana 2 resolution tiers

**Specs:** 156-A (cursor label), 156-B (Grok httpx), 156-C (cost audit),
156-D (cost fix), 156-E (FLUX 2 Pro), 156-F (NB2 resolution tiers),
156-G (docs)

**Tests:** 1268 passing, 0 failures, 12 skipped

**Key outcomes:**
- Cursor fix: added explanatory comment documenting why cursor:not-allowed
  is set on #refUploadZone directly, not the parent container (Session 155
  hotfix already removed the parent cursor line).
- Grok reference image: fixed indefinite hang by replacing
  client.images.edit(image=b'') with direct httpx POST to /v1/images/edits.
  Root cause: SDK multipart/extra_body encoding conflict. New
  _call_xai_edits_api() method with full HTTP status handling.
- Cost display audit (156-C): mapped full cost data flow across 5 layers.
  Root cause of $0.034 for non-OpenAI models: tasks.py called
  get_image_cost() which only has OpenAI pixel-dimension keys — aspect
  ratio strings like '1:1' fell back to $0.034 default.
- Cost display fix (156-D): tasks.py now uses provider.get_cost_per_image()
  via cost_per_image parameter. Flux Dev $0.030→$0.025, NB2 $0.060→$0.067,
  credit_cost updated (Flux Dev 10→8, NB2 20→22). JS _apiCosts synced.
- FLUX 2 Pro: added black-forest-labs/flux-2-pro with reference image
  support (input_images array, max 8 images). Step 0b confirmed schema.
  5 credits ($0.015/MP text-to-image).
- Nano Banana 2 resolution tiers: wired resolution parameter (1K/2K/4K)
  to quality dropdown. Per-resolution costs: $0.067/$0.101/$0.151.
  supports_quality_tiers=True in seed.

### Session 155 — April 16, 2026

**Focus:** Phase REP production readiness — P1 blockers resolved

**Specs:** 155-A (cursor fix), 155-B (xAI NSFW), 155-C (Grok ref image),
155-D (Nano Banana 2 ref image), 155-E (footer white text), 155-F (P2/P3
cleanup), 155-G (docs)

**Tests:** 1254 passing, 0 failures, 12 skipped

**Key outcomes:**
- Disabled setting groups now show cursor:not-allowed on hover — removed
  pointer-events:none from quality group, per-prompt wrappers, ref image
  group in bulk-generator.js. Added disabled guards to ref upload zone
  click/keydown/drop handlers in bulk-generator-autosave.js.
- xAI NSFW keyword detection broadened to 8 keywords (forbidden, violation,
  blocked, inappropriate, nsfw, not allowed + original 2). Module-level
  `_POLICY_KEYWORDS` tuple with `logger.info` audit trail.
- Grok reference image wired via /v1/images/edits endpoint — branches in
  xai_provider.py generate() when reference_image_url is present.
  `_validate_reference_url` with HTTPS check, strip, 2048-char length cap.
- Nano Banana 2 reference image wired via `image_input` array parameter.
  Confirmed via Heroku schema dump (Step 0b Case A). `_MODEL_IMAGE_INPUT_PARAM`
  lookup dict in replicate_provider.py.
- Footer: all text and links set to white via CSS inheritance + `footer a` override.
  WCAG contrast: 16.4:1 (white on #202020).
- P2/P3: TypeError confirmed absent from xai_provider.py. logger.warning
  added to Replicate str() fallback for diagnostic visibility.

---

### Session 154 — April 2026

**Focus:** Phase REP — Replicate + xAI provider integration, credit tracking
data layer, dynamic model selector UI, provider fixes, documentation standards

**Specs:** 154-A through 154-R + 2 hotfixes (Batches 1–6)
**Tests:** 1245 passing, 0 failures, 12 skipped
**Migration:** 0082 (GeneratorModel, UserCredit, CreditTransaction)

**Batch 1 (154-A through 154-E):**
- 154-A: Data Layer — `GeneratorModel`, `UserCredit`, `CreditTransaction` models.
  Migration 0082. Admin with list_editable toggles. Seed command (6 models).
- 154-B: Providers — `ReplicateImageProvider` (Flux Schnell/Dev/1.1-Pro/Nano
  Banana 2) via `replicate` SDK. `XAIImageProvider` (Grok Imagine) via OpenAI-
  compatible xAI API.
- 154-C: Task Layer — Platform mode key resolution. `_get_platform_api_key()`.
  `_deduct_generation_credits()`.
- 154-D: UI Layer — Dynamic model dropdown from DB. BYOK toggle. Aspect ratio
  selector. `getMasterDimensions()`.
- 154-E: Docs update — 4-tier subscription, credit system, key learnings.

**Batch 2 (154-F through 154-I):**
- 154-F: BYOK UX redesign — toggle removed, API key section driven by model.
- 154-G: CSS skin — #f9f8f6 background, btn-outline-standard, reset buttons.
- 154-H: JS init — `updateCostEstimate`/`updateGenerateBtn` moved before
  `handleModelChange`. `tierSection` hide/show.
- 154-I: Final JS init fix — `handleModelChange()` after `addBoxes(4)`.

**Batch 3 (154-J through 154-M):**
- 154-J: API key gate for platform models, aspect ratios from model, credits.
- 154-K: FileOutput crash fix, per-box quality hide, TEMP dollar display.
- 154-L: `supports_reference_image` BooleanField on GeneratorModel.
- 154-M: CSS — aspect ratio flex-wrap, border/background updates.

**Batch 4 (154-N through 154-P):**
- 154-N: ModelError NSFW message, dimensions regression, generate button fix.
- 154-O: Disable (opacity + pointerEvents) for Quality + Ref Image sections.
- 154-P: Results page — `model_display_name`, `gallery_aspect` for ratios.

**Batch 5 (154-Q):**
- 154-Q: Grok 400 fix (constrain xAI sizes), Flux FileOutput URL fix, disabled
  cursor CSS. Round 1 avg 7.3 → Round 2 avg 8.7 after fixes. 16 new tests.

**Batch 6 (154-R + hotfixes):**
- 154-R: xAI provider rewrite — `aspect_ratio` passthrough via `extra_body`,
  URL response + `_download_image()`, disabled cursor via native `disabled`.
  10 new tests. 6 agents avg 8.92/10.
- Hotfix: `aspect_ratio` via `extra_body` (OpenAI SDK rejects unknown kwargs).
- Hotfix: Provider-specific `cost_per_image` on results page.

**Key decisions:**
- OpenAI GPT-Image-1.5 is ALWAYS BYOK (no platform OpenAI key)
- Replicate/xAI run in platform mode (master keys in Heroku env vars)
- `GeneratorModel` is single source of truth for model availability
- Credit enforcement deferred to Phase SUB (Stripe)
- 4-tier: Starter (free), Creator ($9), Pro ($19), Studio ($49)
- Flux Dev has NO image input on official Replicate model
- Nano Banana 2 uses `image_input` (ARRAY type, up to 14 URLs)
- Agent minimum raised from 2-3 to 6 per spec (CC_SPEC_TEMPLATE v2.6)

**Quality notes:**
- 154-Q: 2 agents → 3 below threshold. Lesson: 2-3 insufficient.
- 154-R: 6 agents, all first-round pass, avg 8.92/10. Session high.

### Session 153 — April 11–12, 2026

**Focus:** GPT-Image-1.5 upgrade, pricing accuracy, end-to-end billing
error path, progress-bar refresh accuracy, BYOK UX

**Specs:** 153-A, 153-B, 153-C, 153-D, 153-E, 153-F (Batch 1);
153-G, 153-H, 153-I, 153-J (Batch 2)

**Key outcomes (Batch 1 — shipped):**

- **153-A — GPT-Image-1.5 upgrade.** Both `images.edit()` and
  `images.generate()` API paths upgraded from `gpt-image-1` to
  `gpt-image-1.5`. 7 production files plus 2 new choice tests.
  Migration 0080 adds `gpt-image-1.5` to `AI_GENERATOR_CHOICES`.
- **153-C — IMAGE_COST_MAP updated to GPT-Image-1.5 pricing.** 20%
  reduction across all quality tiers and sizes. Propagated to 10
  files: `constants.py`, 3 Python fallback defaults, JS `COST_MAP`,
  user-facing template string, docstring, and 27 test assertions
  (Option B Step 3b regression fix per `CC_MULTI_SPEC_PROTOCOL`).
- **153-D — Billing hard limit error messaging.** OpenAI's
  `billing_hard_limit_reached` arrives as a `BadRequestError` (400),
  NOT a `RateLimitError` (429), so the existing `insufficient_quota`
  handler did not catch it. A new branch in the `BadRequestError`
  handler now returns `error_type='quota'` with an actionable
  message pointing to `platform.openai.com/settings/organization/
  billing`.
- **153-E — Full billing chain end-to-end fix.** Three gaps closed
  in one commit: (1) `_sanitise_error_message` in
  `bulk_generation.py` had no billing branch — added BEFORE the
  quota check, matches `'billing limit'` (two words, not three) to
  catch the 153-D cleaned message; (2) `process_bulk_generation_job`
  quota-alert notification filter widened from
  `icontains='quota'` to `Q(quota) | Q(billing)`; (3) JS
  `reasonMap` in `bulk-generator-config.js` gained `'Billing limit
  reached'` entry and `'Quota exceeded'` was rewritten to remove
  misleading "contact admin" (BYOK users ARE the admin). 4 new
  tests cover all three gaps.
- **153-F — Progress bar accuracy on page refresh.** New nullable
  `GeneratedImage.generating_started_at` DateTimeField
  (migration 0081). `_run_generation_loop` sets the timestamp
  atomically with the `status='generating'` transition via
  `tz.now()`. Status API returns the ISO string. JS
  `updateSlotToGenerating` uses a negative CSS `animation-delay`
  (e.g. `-8s` on a 20s animation = bar starts at 40% and continues
  forward) so the bar reflects real elapsed time on both initial
  load AND page refresh. `isFirstRenderPass` flag fully removed.
  Also caught a missed `I.COST_MAP` update in `bulk-generator.js`
  that 153-C had overlooked — sticky-bar input-page cost estimate
  was still GPT-Image-1 pricing. Updated to GPT-Image-1.5 prices
  and fallback default.

**Key outcomes (Batch 2 — in progress):**

- **153-G — End-of-session documentation update** (this entry).
- **153-H — `needs_seo_review=True` on bulk-created pages** — fixes
  the priority blocker that bulk-seeded content silently bypasses
  the SEO review queue.
- **153-I — P2/P3 cleanup batch:** `spinLoader` added to
  `prefers-reduced-motion` block, quota notification body updated
  from "quota ran out" → "credit ran out" (covers billing case),
  billing check adds `hasattr(e, 'code')` structured-field guard,
  `openai_provider.py` class + method docstrings updated to
  GPT-Image-1.5, test method renamed from
  `test_vision_called_with_gpt_image_1` → `_15`, Safari `+00:00`
  ISO parse fix (`new Date(iso.replace('+00:00', 'Z'))`).
- **153-J — `get_image_cost()` helper refactor.** Eliminates the
  three duplicated `IMAGE_COST_MAP.get().get()` call sites in
  `openai_provider.py`, `tasks.py`, and `bulk_generator_views.py`.
  Single source of truth for price lookups.

**Key architectural learnings:**

- **JS ↔ Python constant drift.** `bulk-generator.js` has its own
  `I.COST_MAP` that must be kept in sync with Python
  `IMAGE_COST_MAP`. 153-C missed this; 153-F caught it in a
  Step 0 grep. 153-J adds `get_image_cost()` as a partial
  mitigation; full fix requires future template context injection
  so JS prices are generated from Python at render time.
- **Negative CSS `animation-delay` is the correct primitive for
  elapsed-time accuracy.** Starts an animation as if it began N
  seconds ago — not a pause. Combines with a 90% cap to prevent
  near-complete display for slow-running images.
- **Backend sanitiser keywords must be verified against the
  canonical provider message.** The 153-D cleaned billing message
  is `'API billing limit reached...'` (two words `billing limit`),
  NOT `'billing hard limit'`. Using the three-word form would make
  the sanitiser branch a no-op. Always verify the exact text with
  `python -c` before adding a keyword branch.
- **Agent name registry drift.** CC has consistently substituted
  agent names (`@backend-security-coder` for `@django-security`,
  `@ui-visual-validator` for `@accessibility-expert`,
  `@tdd-orchestrator` for `@tdd-coach`). Session 153 Batch 2 run
  instructions added a hard rule forbidding substitution without
  explicit developer authorization. Spec templates should be
  updated to use registry-correct names going forward.

**Migrations:** 0080 (`gpt-image-1.5` in AI_GENERATOR_CHOICES),
0081 (`GeneratedImage.generating_started_at`).

**Tests:** 1221 passing, 12 skipped, 0 failures (up from 1213 at
the start of the session — +8 new tests total: +2 in 153-A (new
`gpt-image-1.5` choice assertions), +4 in 153-E (sanitiser billing
branch, raw-code fallback, branch-ordering regression guard, and
the quota/billing notification filter), +2 in 153-F
(`generating_started_at` API shape and the task-write atomicity
test)).

---

### Session 152-B — April 11, 2026

**Focus:** Progress bar exclude-failed query, Vision composition accuracy

**Specs:** 152-B

**Key outcomes:**
- Progress bar query changed from `filter(status__in=[...])` to `exclude(status='failed')` — fixes missing `queued` images that were not counted
- Vision system prompt enhanced with frame-position (LEFT/RIGHT/CENTRE from viewer's perspective), depth/distance, crowd/group counts, anti-bokeh instruction
- Vision composition accuracy improved for spatial relationships

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 152-A — April 11, 2026

**Focus:** Vision `detail: 'high'`, direction decoupled from Vision, progress bar generating state

**Specs:** 152-A

**Key outcomes:**
- Vision API upgraded from `detail: 'low'` to `detail: 'high'` — `detail: 'low'` compressed images to ~85×85px, losing spatial/depth information needed for accurate composition descriptions
- Direction instructions decoupled from Vision analysis — previously direction was passed INTO the Vision call, causing it to reinterpret rather than describe. Now: Step 1 = Vision describes image (no direction), Step 1.5 = direction edits the Vision output via GPT-4o-mini (two-step approach)
- Progress bar now counts `generating` + `completed` images (was only counting `completed`)

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 151-C — April 10, 2026

**Focus:** Vision prompt logging, placeholder safety, live progress bar

**Specs:** 151-C

**Key outcomes:**
- Vision-generated prompts logged (first 300 chars) for debugging
- Two-layer placeholder safety check: `VISION_PLACEHOLDER_PREFIX in p` (not `p.startswith(...)`) because charDesc prepending moves the placeholder to mid-string position
- `data-completed-count` uses live DB query instead of stale template variable

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 151-B — April 9, 2026

**Focus:** Vision text override fix, diff suppression, overlay CSS, Reset label, Vision prompt quality

**Specs:** 151-B

**Key outcomes:**
- Vision text override fixed: was always using placeholder text instead of Vision-generated prompt
- Diff display suppressed for Vision placeholder prompts (no useful diff to show)
- Overlay underline CSS artifacts fixed
- "Reset" button renamed to "Reset to master"
- Vision system prompt improved: "RECREATE not reinterpret" instruction, spatial accuracy emphasis

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 151-A — April 8, 2026

**Focus:** Vision empty prompt validation fix, Reset and AI Direction layout

**Specs:** 151-A

**Key outcomes:**
- "Prompt cannot be empty" validation bug fixed for Vision-enabled boxes (Vision boxes use placeholder, don't require user text)
- Reset button moved from prompt box footer to header
- AI Direction textarea moved above Source Image URL / Credit fields for better flow

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 150 — March 31, 2026

**Focus:** Bug fixes, UI cleanup, Vision quality, AI Direction for all boxes, diff display on results page

**Specs:** 150-A (bug fixes), 150-B (UI cleanup), 150-C (Vision quality), 150-D (AI Direction all boxes), 150-E (diff display), 150-F (docs)

**Key outcomes:**
- Generate button now activates for Vision-enabled boxes and after any setting change (dropdowns, toggles, back navigation)
- Progress bars initialise from server state immediately on page refresh (no 0% flash before first poll)
- API key missing error now scrolls to API key field and shakes input (matching tier error UX)
- Tooltip system built (CSS-only, hover + focus-visible, accessible). All inline hints converted to tooltips: Character Reference Image, Character Selection, Remove Watermarks, AI Direction.
- "Staff-only tool." removed from subtitle
- Tier options now show ~ prefix (approximate not guaranteed)
- "I know my tier" warning strengthened with OpenAI account restriction note
- Vision system prompt improved: no sentence limit, covers attire/age/background/props, visible watermarks in source images now ignored. max_tokens increased 200→500 for richer Vision output.
- AI Direction field now available for ALL prompt boxes (not just Vision). "Add Direction" checkbox always visible. Text prompt direction applies targeted edits via GPT-4o-mini before generation (Step 1.5 in pipeline: Vision → Text direction → Translate/watermark).
- Diff display on results page: strikethrough removed words, highlighted green added words. Shows changes from translation, watermark removal, direction edits. Clean text on publish. No diff shown if prompt unchanged.
- Migration 0079: `original_prompt_text` field on GeneratedImage (blank=True, default='' — only stored when differs from prepared text)

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 149 — March 31, 2026

**Focus:** Feature 2 — Generate Prompt from Source Image (Vision API) + Remove Watermarks toggle

**Specs:** 149-A (frontend UI), 149-B (backend Vision), 149-C (autosave), 149-E (Remove Watermarks toggle), 149-D (docs)

**Key outcomes:**
- Per-prompt "Prompt from Image" dropdown added alongside "Images" in each prompt box. Default "No". Selecting "Yes" disables/strikes the prompt textarea (text preserved), shows a resizable direction instructions textarea, and marks the source image URL field as required.
- Direction instructions textarea allows user to guide the Vision AI (e.g. "Replace the man with a blonde woman in a golden dress"). Up to 500 chars.
- Backend: `_generate_prompt_from_image()` helper in `bulk_generator_views.py` calls GPT-4o-mini Vision (detail:low) with base64-encoded source image + direction instructions. Returns 1-2 sentence generation-ready prompt. HTTPS URL validation + 10 MB size cap for defense-in-depth.
- Vision calls run BEFORE translate/watermark batch in `api_prepare_prompts` — so Vision output is also cleaned by the translate/watermark pass.
- Vision failure always falls back to original prompt text — non-blocking.
- Platform `OPENAI_API_KEY` used for Vision calls (~$0.003 per prompt).
- Autosave extended: `visionEnabled` and `visionDirections` arrays saved to localStorage. Vision side-effects (disabled textarea, direction row) correctly restored on page refresh.
- "Remove Watermarks (Beta)" toggle added to Column 4 between Visibility and Translate to English. ON by default. When OFF, TASK 2 (watermark removal) is skipped in the prepare-prompts system prompt and the Vision system prompt omits the "no watermarks" rule. Examples section is also conditional — translate-only examples shown when OFF.
- Reset handler clears Vision state (dropdown, direction textarea, textarea disabled state).
- `collectPrompts` updated to include Vision-only prompts (empty text with Vision=Yes).
- Feature 2B (Master "Prompt from Image" Mode) documented as planned future feature.

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 148 — March 30, 2026

**Focus:** Prepare prompts fixes, tier UX improvements, P3 cleanup

**Specs:** 148-A (prepare prompts fixes), 148-B (P3 cleanup), 148-C (docs)

**Key outcomes:**
- OPENAI_API_KEY wired from env to Django settings — fixes 401 error
  that prevented translation and watermark removal from working
- Translation toggle added to Column 4 (alongside Visibility), ON by default.
  When OFF, watermark removal still runs but translation is skipped.
- Tier error now scrolls page to tier section + shakes tierConfirmPanel
  to direct user to the area requiring their attention
- Tier error message simplified (scroll/shake replaces the directional hint)
- Prepare-prompts endpoint rate limited (20 calls/hr per user)
- Error banner auto-dismiss extended 5s → 8s; suppressed entirely for
  prefers-reduced-motion users
- Stale test patch in D3InterBatchDelayTests confirmed already correct
  (was fixed in prior session)

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 147 — March 30, 2026

**Focus:** Tier UX bug fixes + Prepare Prompts pipeline

**Specs:** 147-A (tier UX fixes), 147-B (prepare prompts), 147-C (docs)

**Key outcomes:**
- Fixed template comment rendering as visible text below tier panel
- Tier confirmation error now uses prominent bottom-bar banner
  (showGenerateErrorBanner) matching the API key error style + warning emoji
- New "Prepare Prompts" pipeline step added between validation and
  generation start: one GPT-4o-mini batch call translates non-English
  prompts to English AND strips watermark/branding instructions
- Prepare step is non-blocking — falls back to original prompts on any error
- New endpoint: POST /api/bulk-generator/prepare-prompts/
- Platform OPENAI_API_KEY used for prepare call (not user's BYOK key)
- Users see "Preparing prompts..." status during the ~1-3 second step
- 6 few-shot examples in system prompt for accurate watermark detection

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 146 — March 29, 2026

**Focus:** Production bug fixes from Session 145 browser testing

**Specs:** 146-A (delay logic fix), 146-B (cost estimate fix),
146-C (Django-Q timeout + duration display), 146-E (conditional tier UX),
146-D (docs)

**Key outcomes:**
- Global delay override was acting as floor not ceiling — removed entirely.
  OPENAI_INTER_BATCH_DELAY is now deprecated; per-job _TIER_RATE_PARAMS
  controls all delay. BULK_GEN_MAX_CONCURRENT remains as concurrent ceiling.
- Cost estimate now size-aware: portrait/landscape shows correct pricing
  ($0.063 medium portrait, not $0.042 square). I.COST_MAP replaced with
  nested size → quality structure matching constants.py IMAGE_COST_MAP.
- Django-Q timeout increased from 2 minutes to 2 hours — high-quality
  3-prompt jobs were being killed mid-run and re-queued, causing 1 of 3
  images to always fail. max_attempts reduced to 1 to prevent credit waste.
- "Done in Xs" client-side timer removed from job page — was showing
  page-load time not job duration, conflicting with accurate server-side
  "Duration: Xm Ys" display.
- Conditional tier UX: Tier 1 has zero friction; Tier 2-5 shows confirmation
  panel with auto-detect ($0.011 test image reads rate limit headers) or
  manual confirmation. Generate blocked until confirmed.

**Tests:** 1213 passing, 12 skipped, 0 failures

---

### Session 145 — March 29, 2026

**Focus:** Billing path cost fix, proxy hardening, per-job tier rate limiting,
Replicate provider planning

**Specs:** 145-A (billing fallback), 145-B (proxy minor fixes),
145-C (per-job tier + rate limiting), 145-D (CLAUDE.md architecture),
145-E (docs)

**Key outcomes:**
- Stale 0.034 billing fallback fixed in tasks.py `_apply_generation_result()`
  — this is the actual cost recording path (more consequential than view fix)
- All stale 0.034 fallbacks now resolved across entire codebase (confirmed by
  @security-auditor)
- Proxy rate limiter: ValueError race guard added to `cache.incr()`, redundant
  HttpResponse alias removed
- D2 generation retry confirmed already implemented (Phase 5C) — no rebuild needed
- `openai_tier` field added to BulkGenerationJob (migration 0078)
- `_TIER_RATE_PARAMS` lookup added to `_run_generation_loop()` — per-job concurrency
  and delay derived from tier + quality combination
- Global `BULK_GEN_MAX_CONCURRENT` and `OPENAI_INTER_BATCH_DELAY` now act as
  ceilings only — per-job params take precedence when lower
- Tier 1–5 dropdown added to bulk generator input page UI
- CLAUDE.md updated: D4 architecture, Replicate provider plans,
  D2 already-built note

**Tests:** 1213 passing, 12 skipped
**Migration:** 0078

---

### Session 144 — March 28, 2026

**Focus:** P1 bug fixes, thumbnail proxy hardening, P3/P4 cleanup batch

**Specs:** 144-A (PASTE-DELETE fix), 144-B (stale cost fallback),
144-C (proxy hardening), 144-D (P3 cleanup), 144-E (P4 fixes),
144-F (docs)

**Key outcomes:**
- PASTE-DELETE ✕ button fix: `.classList.contains()` → `.closest()`
  pattern, matching deleteBtn and resetBtn above it in same listener
- Stale 0.034 cost fallback updated to 0.042 in bulk_generator_views.py
  (flagged Medium severity by @security-auditor in Session 143-H)
- Thumbnail proxy: request.user.pk added to all 7 [IMAGE-PROXY] log
  lines; per-user rate limit added (60 req/min, cache.add/incr pattern)
- .finally() removed from validateApiKey (ES2015 compat); replaced with
  .then() chain that correctly passes result through
- Dead I.urlValidateRef property removed from bulk-generator.js
- .container max-width rule moved from lightbox.css to style.css
- ref_file.name now sniffs Content-Type instead of hardcoding 'reference.png'
- deleteBox .catch now logs console.warn (was silent)
- OPENAI_INTER_BATCH_DELAY hoisted above generation loop (was re-read
  per iteration)
- CLAUDE.md quota capitalisation fixed: "quota exhausted" → "Quota exceeded"

**Tests:** 1213 passing, 12 skipped, 0 failures
**Commits:** d2facfe, 9e46999, a6d0ed0, 1f9f250, 91ef568

---

### Session 143 — March 26, 2026

**Focus:** bulk-generator.js split, D1 pending sweep, D3 rate limit delay, QUOTA-1
error distinction, pricing correction, security hardening

**Specs:** 143-D (JS split), 143-E (docs safeguard D), 143-F (D1+D3),
143-G (quota error), 143-H (pricing), 143-I (docs)

**Key outcomes:**
- bulk-generator.js split: 1685 → 725 lines; extracted `bulk-generator-generation.js`
  (625 lines) and `bulk-generator-autosave.js` (376 lines) via `window.BulkGenInput` namespace
- D1 pending sweep: orphaned queued/generating images now swept to failed after loop exits;
  `failed_count` recalculated from DB
- D3 inter-batch delay: `OPENAI_INTER_BATCH_DELAY` setting added; set to 12s in Heroku
  for Tier 1 rate limit compliance
- QUOTA-1: quota exhaustion now returns `error_type='quota'` (distinct from `rate_limit`);
  no retry; fires `openai_quota_alert` bell notification; new migration 0077
- Pricing correction: `IMAGE_COST_MAP` corrected (medium 0.034→0.042, high 0.067→0.167
  square / 0.092→0.250 portrait); `COST_MAP` removed from `openai_provider.py`;
  `get_cost_per_image()` now delegates to `IMAGE_COST_MAP` (single source of truth)
- Safeguard Section D added to CLAUDE.md: D1/D2/D3 architecture + QUOTA/P2-B/P2-C plans
- Cloudflare Bot Fight Mode enabled on promptfinder.net (Security → Settings → Bot traffic)
- `OPENAI_INTER_BATCH_DELAY=12` set in Heroku config vars

**Bug discovered (not yet fixed):**
- [PASTE-DELETE] ✕ button uses `.classList.contains()` not `.closest()` — fix in Session 144
- Stale 0.034 fallback in `bulk_generator_views.py` — flagged by @security-auditor in 143-H

**Tests:** 1209 passing, 12 skipped, 0 failures
**Commits:** ca1bbad, c02b0a7, a6a8493, 98fc1aa, 82ab410, 8871a5d, 3e5d33c, 128cb34

---

### Session 142 — March 21, 2026

**Focus:** Security hardening, protocol closure, lightbox fix, P3 batch

**Specs:** 142-A (thumbnail proxy review), 142-B (141-D closure + lightbox),
142-C (P3 batch), 142-D (docs)

**Key outcomes:**
- Thumbnail proxy (`/api/bulk-gen/image-proxy/`) formally reviewed with
  STRIDE threat model — all 12 security controls confirmed. Source URL
  preview now works for hotlink-protected and Next.js optimised URLs.
- 141-D protocol violation formally closed — @django-pro and @python-pro
  confirmed openai_provider.py reference image fix is correctly implemented
- gallery.js lightbox close button confirmed on overlay (not inner) —
  caption fully removed, aria-describedby removed (already correct from 141)
- prompt_detail.html and lightbox.css confirmed already correct (no changes)
- Single-box ✕ clear now fires B2 delete before clearing URL field
- X-Content-Type-Options: nosniff added to download proxy
- OpenAI SDK images.edit() vs images.generate() documented in CLAUDE.md
- **Tests:** 1193 passing, 0 failures, 12 skipped
- **Commits:** e20a536, 8c3f5ef, c2272e6

---

### Session 141 — March 21, 2026

**Focus:** Recurring bug fixes, lightbox structure, reference image fix

**Specs:** 141-A (download proxy + blur thumbnail), 141-B (clear all cleanup),
141-C (lightbox close button), 141-D (reference image fix), 141-E (docs)

**Key outcomes:**
- Download button now works via server-side proxy endpoint
  (`/api/bulk-gen/download/`) — bypasses CORS restriction on CDN URLs
- Blur thumbnail preview confirmed already present (Session 140 fix verified)
- Clear All hardened — paste URLs captured into array before fields cleared,
  full paste state reset in single loop with `console.warn` on fetch failure
- Single-box ✕ clear now resets `thumb.src` and `thumb.onerror`
- Lightbox close button absolutely positioned on overlay (not in flow)
  — no longer appears below image on mobile
- Lightbox caption fully removed from results page lightbox
- Lightbox CSS extracted to `static/css/components/lightbox.css`
  (removed from both `bulk-generator-job.css` and `prompt-detail.css`)
- Reference image fix — GPT-Image-1 now receives reference image as
  BytesIO file object via `client.images.edit()` (was silently ignored
  since feature was built; SDK `images.generate()` has no `image` param)
- **Tests:** 1193 passing, 0 failures, 12 skipped
- **Commits:** d1e1e14, 475f62e, 1e42d02, 63056d1

---

### Session 140 — March 20, 2026

**Focus:** Bug fixes, lightbox desktop layout, P3 cleanup, protocol v2.2

**Specs:** 140-A (JS bug fixes), 140-B (backend/CSS fixes), 140-C (lightbox layout),
140-D (P3 cleanup), 140-E (protocol v2.2), 140-F (docs)

**Key outcomes:**
- Download button now uses fetch+blob (fixes cross-origin download failure)
- Thumbnail preview now shows on blur for valid typed source URLs
- Clear All now fully resets paste state (URL, lock, preview, thumbnail, status)
- Server-side URL validator now handles CDN URLs with query strings
- Error banner now shows jump links after server-side validation rejection
- Textarea prompt field is now user-resizable (wrapper resize: vertical)
- Lightbox desktop layout: full height image, × and links in right panel
- Source image thumbnail: object-fit: contain, cursor: zoom-in
- P3 batch: Space preventDefault, B2 domain guard, focus-visible, aria-hidden,
  docstring update, dimension fallback
- Protocol v2.2: WCAG 1.4.11, focus trap, reduced-motion, cross-origin fetch
  added to mandatory PRE-AGENT SELF-CHECK
- Tests: 1193+ passing, 12 skipped, 0 failures

---

### Session 139 — March 19, 2026

**Focus:** Prompt detail redesign, global lightbox, results page fixes, new features docs

**Specs:** 139-A (source image card), 139-B (global lightbox), 139-C (results fixes),
139-D (new features docs), 139-E (docs)

**Key outcomes:**
- Source credit + source image merged into one row on prompt detail
- Bootstrap modal replaced with custom lightbox (consistent with results page)
- Hero image on prompt detail opens in lightbox on click
- Lightbox caption/prompt text removed from results page lightbox
- "Open in new tab" added to prompt detail lightbox
- .btn-select hover isolation fixed (circle only reacts on direct hover)
- 2:3 set as default master dimension
- WebP conversion added to source image B2 upload via Pillow
- clearAllConfirm fires paste cleanup before clearing boxes
- Published slot lightbox guard added
- .btn-select dark halo for WCAG 1.4.11 contrast on light images
- New features documented: translate, vision prompt gen, watermark removal, save draft
- Session 138 Spec C unconfirmed score closed (gray-600 + --primary verified)

**Final state:** 1193 tests, 12 skipped, 0 failures.

---

### Session 138 — March 18, 2026

**Focus:** Bug fixes, SRC-6 pipeline, results page UI, paste orphan cleanup

**Specs:** 138-A (delete focus fix), 138-B (SRC-6 pipeline fix),
138-C (results page UI), 138-D (paste orphan cleanup), 138-E (docs),
138-F (P3 cleanup)

**Final state:** 1193 tests, 12 skipped, 0 failures.

**Key outcomes:**
- Fixed delete box focus always jumping to last prompt (captured boxIndex before .removing)
- Fixed SRC-6: source image URL now correctly flows from JS payload to GeneratedImage records (key name mismatch between client and server)
- Source Image card now appears on prompt detail page after publish (pending Mateo verification)
- Results page: lightbox on image click, queued/generating placeholder states (clock→spinner+progress bar), checkbox dark circle redesign (top-left, check on hover, blue fill selected)
- B2 paste orphan cleanup: new `/api/bulk-gen/source-image-paste/delete/` endpoint, deletes old paste file on re-paste and prompt box delete
- P3: `aria-label="Go to Prompt N"` on error links, `__init__.py` direct imports from domain modules (removed shim hop)
- Updated 3 source image URL tests to use per-prompt dict format (matched SRC-6 fix)

---

### Session 137 — March 16, 2026

**Focus:** Protocol hardening, P3 cleanup

**Specs:** 137-A (protocol v2.1), 137-B (P3 cleanup batch), 137-C (docs)

**Key outcomes:**
- CC_MULTI_SPEC_PROTOCOL.md v2.1 — docs gate re-run rule added
- BulkGenUtils.debounce dead code removed
- Banner error text reads from err.message (no duplicate copy)
- Paste lock state replaced with .bg-paste-locked CSS class
- 136-E and 134-D unconfirmed scores closed

---

### Session 136 — March 16, 2026

**Focus:** CSS migration, paste module extraction, P3 fixes, views docs

**Final state:** 1193 tests, 12 skipped, 0 failures. `bulk-generator.js` reduced from 1,605 → 1,546 lines.

#### Spec A — CSS Migration (commit 6328db2)
- Moved paste/badge inline CSS from `bulk_generator.html` to `bulk-generator.css`
- 11 rule blocks moved verbatim — zero visual changes
- Flush button CSS retained in template (template-specific)
- Agents: @frontend-developer 10/10, @code-reviewer 7.5/10 (false positives on pre-existing diff). Avg 8.75/10

#### Spec B — Paste Module Extraction (commit 3acd654)
- Created `bulk-generator-paste.js` (78 lines) — `BulkGenPaste.init(promptGrid, csrf)`
- Moved `lockPasteInput`/`unlockPasteInput` to `BulkGenUtils` in `bulk-generator-utils.js`
- Removed helpers + global paste listener from `bulk-generator.js` (63 lines removed)
- All call sites updated to namespaced `BulkGenUtils.lockPasteInput()`
- Script load order: utils → paste → main
- Agents: @frontend-developer 9.5/10, @code-reviewer 8.5/10, @security-auditor 9.0/10. Avg 9.0/10

#### Spec C — P3 Batch (commit 75dcab8)
- `prefers-reduced-motion` support on error link scroll (`behavior: 'auto'`, `setTimeout(0)`)
- `IMAGE_EXT_RE` anchored with `(?:[?#&]|$)` lookahead — blocks `/photo.jpgfoo`
- `@accessibility` review: no WCAG AA failures found on `showValidationErrors` error links
- Agents: @frontend-developer 9.5/10, @accessibility 9.0/10. Avg 9.25/10

#### Spec D — Views Structure Docs (commit 5e65138)
- Rewrote `prompts/views/STRUCTURE.txt` and `README.md` for 22-module state
- All line counts exact (0 discrepancies per agent verification)
- Agent: @docs-architect 9.0/10

#### Spec E — Docs Update
- Updated CLAUDE.md: file tier table, Deferred P3 Items (3 resolved, 1 added)
- Session 136 entry added to CLAUDE_CHANGELOG.md
- `bulk-generator-paste.js` added to PROJECT_FILE_STRUCTURE.md

---

### Session 135 — March 16, 2026

**Final state:** 1193 tests, 12 skipped, 0 failures. `prompt_create` dead code removed (~207 lines).

#### Spec A — Bulk Gen UX Fixes (commit 4111114)
- Fixed URL validator to accept CDN/Next.js optimisation URLs (decoded query string check via `_hasImageExtension`)
- Thumbnail reconstruction on draft restore for all source image URLs (not just paste)
- `onerror` handler hides broken thumbnails gracefully with self-clear
- ⚠️ error badge added to prompt boxes with validation errors (`bg-box-error-badge` in `bg-box-header-actions`)
- Scroll offset fix — error link now lands prompt box in readable position (`setTimeout(350)` + `scrollBy(-120)`)
- Fixed badge display reset bug (added base CSS rule `.bg-box-error-badge { display: none; }`)
- Agents: @frontend-developer 9.2, @ui-ux-designer 8.5, @code-reviewer 8.5. Avg 8.73/10

#### Spec B — Cleanup Batch (commit 8dee2dc)
- Extracted `lockPasteInput`/`unlockPasteInput` helpers — 3 inline lock/unlock patterns replaced
- Added `cursor: not-allowed` on locked paste URL inputs
- `prompt_create` confirmed dead (URL maps to `RedirectView`, no template/JS references) — removed ~207 lines from `prompt_edit_views.py`
- Updated shim (`prompt_views.py`), `__init__.py`, and `urls.py` comment
- Agents: @frontend-developer 9.5, @code-reviewer 8.5. Avg 9.0/10

---

### Session 134 — March 16, 2026

**Final state:** 1193 tests, 12 skipped, 0 failures. Migration 0076. `prompt_views.py` split into 4 domain modules.

#### Spec A — Bulk Gen JS/CSS Fixes (commit a0dc41b)
- Clickable error links: `showValidationErrors` builds `<a>` tags with `scrollIntoView` + `focus()` when `err.promptNum` provided
- Inline error persistence: per-prompt errors with `err.index` fire `.bg-box-error` alongside the banner
- Draft restore: reconstructs paste thumbnail preview from localStorage for `/source-paste/` URLs
- URL field lock: `readonly` + `opacity: 0.6` + tooltip after paste; clear button removes all three
- `https://` validation: added to both `isValidSourceImageUrl` and `validateSourceImageUrls`
- `.is-paste-target` CSS: `outline` replaced with `border-color` + `box-shadow` (matches `:focus-within`)
- Agents: @frontend-developer 8.5, @ui-ux-designer 8.2, @code-reviewer 8.5. Avg 8.4/10

#### Spec B — bytearray + Content-Length Pre-check (commit fad5d92)
- `_download_and_encode_image`: `b''` + `+=` → `bytearray()` + `.extend()` (O(n^2) → O(n))
- `_download_source_image`: same bytearray fix + Content-Length header pre-check (parity with `_download_and_encode_image`)
- `bytes(content)` return in `_download_source_image` (callers expect `bytes`)
- 1 new test: `test_content_length_precheck_rejects_large_source_image`
- Agents: @django-pro 10/10, @code-reviewer 9/10. Avg 9.5/10

#### Spec C — prompt_views.py Split (commit 2affd60)
- Split 1,694-line `prompt_views.py` into 4 domain modules:
  - `prompt_list_views.py` (620 lines) — PromptList, prompt_detail, related_prompts_ajax
  - `prompt_edit_views.py` (528 lines) — prompt_edit, prompt_create
  - `prompt_comment_views.py` (139 lines) — comment_edit, comment_delete
  - `prompt_trash_views.py` (396 lines) — prompt_delete, trash_bin, prompt_restore, prompt_publish, prompt_permanent_delete, empty_trash
- `prompt_views.py` is now a 50-line shim re-exporting all 13 public names
- `urls.py` updated to import from domain modules directly
- Fixed stray blank lines between decorators and `def` (bandit + security auditor)
- Fixed `hashlib.md5` → `usedforsecurity=False` (bandit)
- Removed unused imports (`login_required`, `Tag`) from `prompt_list_views.py`
- Agents: @django-pro 9.0, @code-reviewer 8.0, @security-auditor 7.0→9.0 (round 2). Avg 8.7/10

### Session 133 — March 15, 2026

**Final state:** 1192 tests, 12 skipped, 0 failures. Migration 0076.

#### SRC Blur Validation
- Source URL inline blur validation with error display
- `isValidSourceImageUrl` + `validateSourceImageUrls` in `bulk-generator-utils.js`

#### SRC Paste Upload
- Active row selection + global paste for source image upload
- Solves Facebook URL problem (users can paste images directly)
- New endpoint: `/api/bulk-gen/source-image-paste/`
- B2 upload to `source-paste/` prefix

#### SSRF Hardening
- `_is_private_ip_host()` private IP filter in `_download_source_image`
- `allow_redirects=False` with manual redirect validation
- Reject non-HTTPS redirects and private host redirects

#### P3 Cleanup
- `_get_b2_client()` DRY helper extracted
- `rel="noreferrer"` on external links
- Direct unit tests for `_download_source_image`

### Session 132 — March 15, 2026

**Final state:** 1176 tests, 12 skipped, 0 failures. Migration 0076.

#### SRC-6 Source Image Download + B2 Upload
- `_download_source_image()` in `tasks.py` — downloads from any HTTPS URL
- B2 upload pipeline for source images (completes SRC pipeline)
- New test file: `prompts/tests/test_src6_source_image_upload.py`

#### Session 131 Cleanup
- Regex module-level compilation
- Thumbnail max-height constraint
- Modal open-in-new-tab link

### Session 131 — March 14, 2026

**Final state:** 1162 tests, 12 skipped, 0 failures. Migration 0076.

#### Reactive P2 Fixes
- Regex path fix (B2 prefix allowlist)
- Docstring corrections
- Debug log cleanup

#### SRC-5 Staff Source Image Display
- Staff-only source image display on prompt detail page
- Lightbox viewer for source images
- `source_credit` and `source_credit_url` display

### Session 130 — March 14, 2026

**Focus:** SRC pipeline Phase 4 — source image copy on publish + B2 hard delete

**Key outcomes:**
- `b2_source_image_url` copied from `GeneratedImage` to `Prompt` on publish (commit 2d687cb)
- Source image deleted from B2 on `hard_delete()` — extends existing cleanup path
- SRC-3: Parse and validate `source_image_urls` in backend, save to `GeneratedImage` (commit 3e46c94)

---

### Session 129 — March 14, 2026

**Focus:** SRC pipeline Phases 1-2 — source image URL model fields + frontend input

**Key outcomes:**
- SRC-1: `source_image_url` fields added to `GeneratedImage` and `Prompt` models (commit 4d4a93a)
- SRC-2: Source image URL input field in bulk generator UI with client-side validation (commit a7e7ac0)
- `renumberBoxes` aria-label fix, placeholder extension display, version header cleanup (commit 7ff7a58)
- JS refactor: extracted `bulk-generator-utils.js` companion module from `bulk-generator.js` (commit 9b6d06b)

---

### Session 128 — March 14, 2026

**Focus:** File size audit + api_views.py split + working constraints documentation

**Key outcomes:**
- File size audit: identified 7 Critical (2000+), 8 High Risk (1200-1999), 13 Caution (800-1199) files (commit 968098b)
- `api_views.py` split into 4 domain modules: `ai_api_views.py`, `moderation_api_views.py`, `social_api_views.py`, `upload_api_views.py` + compatibility shim (commit 9ef06a0)
- Added CC Working Constraints & Spec Guidelines section to `CLAUDE.md` (commit bf6f5a6)
- Updated `urls.py` to import from domain modules directly (commit 46e55ea)
- `NSFWViolationAdmin` read-only admin class added (commit bf9b938)

---

### Session 127 — March 13, 2026

**Focus:** N4 open item closure + admin fixes + debug cleanup

**Key outcomes:**
- Admin `save_model` fix: queue `rename_prompt_files_for_seo` for B2 prompts (commit bb93256)
- Removed 13 debug `print()` statements from `upload_views.py` + dead cloudinary import (commit 598b6ad)
- N4 cleanup audit: confirmed ARIA comment, stale entries closed, marked 100% complete (commit 4640a92)
- Cloudinary views audit: `admin_views.py` + `upload_views.py` findings documented (commit 50aef7c)

---

### Session 126 — March 13, 2026

**Focus:** Notification admin alerts + upload cleanup

**Key outcomes:**
- NOTIF-ADMIN-1: NSFW repeat offender admin alerts (commit b8b4ac2)
- NOTIF-ADMIN-2: Scheduled task outcome notifications (commit dea0a71)
- Upload cleanup: remove dead Cloudinary upload path, rename `cloudinary_id` field (commit 54dde7a)
- `cancel_upload` audit documented (commit d9f2788)
- Upload views refactor: rename `cloudinary_id` var, fix dead redirects, sanitise cancel error (commit 285286f)

---

### Session 125 — March 13, 2026

**Focus:** Cloudinary audit + bulk gen notifications + vision moderation rename

**Key outcomes:**
- Cloudinary codebase audit report — findings only, no code changes (commit 8d911a4)
- Renamed `cloudinary_moderation.py` → `vision_moderation.py` — all import sites updated (commit f2e7a6f)
- Added 4 bulk gen notification types: `bulk_gen_job_completed`, `bulk_gen_job_failed`, `bulk_gen_published`, `bulk_gen_partial` (commit 9508743)
- Migration 0073. New test file: `prompts/tests/test_bulk_gen_notifications.py` (6 tests)
- Fixed hardcoded URLs in notification helpers with `reverse()` (commit f7dd17e)
- 1149 → 1155 tests

---

### Session 124 — March 13, 2026

**Focus:** Bulk gen header stats + session 123 docs

**Key outcomes:**
- Added Total Duration to bulk gen job page header stats dashboard (commit 8eab63b)
- End-of-session 123 docs update (commit d2fb499)

---

### Session 123 — March 13, 2026

**Final state:** 1149 tests, 12 skipped, 0 failures. Migrations unchanged (0072). 5 JS modules.

#### MICRO-CLEANUP-1 — Seven cleanup items (commit a222d15)
- Group footer separator changed from `·` (U+00B7) to `|` with symmetric `margin: 0 0.4rem`, `font-weight: 400`, `color: var(--gray-500)`
- ID rename: `header-quality-col-th` → `header-quality-item`, `header-quality-col-td` → `header-quality-value` in `bulk_generator_job.html` + `bulk-generator-ui.js`
- Quality column reveal: `style.removeProperty('display')` replaced with `.is-quality-visible` CSS class toggle. CSS owns `display: none` default; JS adds class only
- `VALID_PROVIDERS`, `VALID_VISIBILITIES` → `frozenset` in `bulk_generator_views.py` (all 5 `VALID_*` constants now frozenset)
- `VALID_SIZES` → `frozenset` in `create_test_gallery.py`
- `@csp_exempt` blank line removed in `upload_views.py` — decorator was silently not applied. Bonus: same fix on `extend_upload_time` (`@require_POST` blank lines removed)
- `replace('x', '×')` → anchored regex `/(\d+)x(\d+)/i` in `bulk-generator-ui.js` — prevents false match on future prefixed size strings
- Agents: @frontend-developer 8.8, @code-reviewer 9.0, @django-pro 8.5. Avg 8.77/10

#### DETECT-B2-ORPHANS — New management command (commit 61edad1)
- New file: `prompts/management/commands/detect_b2_orphans.py` (404 lines)
- Read-only B2 bucket audit — lists orphaned files (no deletes, ever)
- `SCAN_PREFIXES = ['media/', 'bulk-gen/']` — prefix allowlist prevents static/admin paths from being flagged
- DB coverage: `Prompt.all_objects` (7 B2 fields: b2_image_url, b2_thumb_url, b2_medium_url, b2_large_url, b2_webp_url, b2_video_url, b2_video_thumb_url) + `GeneratedImage.image_url` + `BulkGenerationJob.reference_image_url`
- Credential safety: `_safe_error_message()` uses structured `ClientError.response['Error']` fields; `raise CommandError(...) from None` suppresses boto3 traceback; bucket name only (not endpoint) in all output
- `.iterator(chunk_size=500)` on all DB queries — memory-safe for large datasets
- `Config(retries={'max_attempts': 3, 'mode': 'adaptive'})` — handles B2 429/503 transients
- Flags: `--days N` (default 30), `--all`, `--dry-run`, `--output PATH`, `--verbose`/`--no-verbose`
- CSV output: `docs/orphans_b2.csv` by default
- All error paths use `CommandError` (not `sys.exit`)
- Agents: @security-auditor 9.0, @django-pro 9.0, @code-reviewer 8.5. Avg 8.83/10
- Prerequisite for bulk job deletion now complete

---

### Session 122 — March 12, 2026

**Final state:** 1149 tests, 12 skipped, 0 failures. Migration 0072. 5 JS modules.

#### CLEANUP-SLOTS-REFACTOR
- Removed unreachable `:not(.placeholder-terminal)` from `cleanupGroupEmptySlots()`
- Agents: @frontend-developer 9.1, @code-reviewer 9.2

#### Bulk Gen 6E-A — Per-prompt size override
- `GeneratedImage.size` CharField, migration 0069
- Commit: e1fd774

#### Bulk Gen 6E-B — Per-prompt quality override
- `GeneratedImage.quality` CharField, migration 0070
- Unspecced: `actual_cost` now uses per-image quality/size
- Commit: 87d33fa

#### Bulk Gen 6E-C — Per-prompt image count override
- `GeneratedImage.target_count` PositiveSmallIntegerField, migration 0071
- `VALID_COUNTS = {1,2,3,4}`
- Commit: 7d6efb6 — 1139 tests

#### 6E-HARDENING-1 — Backend hardening
- `BulkGenerationJob.actual_total_images`, migration 0072
- `VALID_SIZES` rebuilt from `SUPPORTED_IMAGE_SIZES`
- 8 new cost/count tests
- Commit: 3b42114 — 1147 tests

#### 6E-HARDENING-2 — Frontend display
- `G.totalImages` three-level fallback
- Group headers show per-group size + quality
- Per-group placeholder aspect ratios
- Commit: 7b1ff65 — 1147 tests

#### 6E-CLEANUP-1 — Python micro-cleanup
- frozenset on VALID_SIZES/QUALITIES/COUNTS
- `total_images_estimate` → `resolved_total_images`
- `> 0` guard in `get_job_status()`
- Commit: 0b6b720

#### 6E-CLEANUP-2 — JS module split
- New file: `static/js/bulk-generator-gallery.js` (452 lines)
- `bulk-generator-ui.js` 766 → 338 lines
- Functions extracted: cleanupGroupEmptySlots, markCardPublished, markCardFailed, fillImageSlot, fillFailedSlot, lightbox functions
- Load order: config → ui → gallery → polling → selection
- Commit: 5f1ced3

#### 6E-CLEANUP-3 — JS bug + quality
- Cancel-path `G.totalImages` fix: `data-actual-total-images` attr + `initPage()` reads it
- `parseGroupSize()` helper replaces 3× inline split in `createGroupRow()`
- ARIA `progressAnnouncer` clear-then-50ms-set pattern
- Dead ternary guards removed from `renderImages()`
- Commit: 90ac2cb — 1147 tests

#### N4H-UPLOAD-RENAME-FIX
- `upload_views.py`: guard changed from `is_b2_upload and prompt.pk` to `prompt.b2_image_url`
- `async_task` import moved to module level
- New file: `prompts/tests/test_upload_views.py` (2 tests)
- Discovery: core call was already present from Session 67 — fix tightened the guard
- Closes N4h blocker from CLAUDE.md Current Blockers
- Commit: a9acbc4 — 1149 tests

---

### Session 121 — March 11, 2026

**Focus:** SMOKE2 Production Smoke Test Series + HARDENING-1 + JS-SPLIT-1 + HARDENING-2

---

#### SMOKE2 Series — Production Smoke Test (Fixes A–E)

**Context:** First full production smoke test of the bulk generator publish flow. Six bulk-gen published prompt pages showed "Media Missing" on detail pages. Root cause traced to three compounding bugs in the publish pipeline.

**Fix A — `processing_complete=False` on bulk-gen prompts**
- `Prompt` constructor in both `publish_prompt_pages_from_job` and `create_prompt_pages_from_job` defaulted `processing_complete` to `False`
- Template gates ALL media display on this field
- Fix: added `processing_complete=True` to both constructors in `prompts/tasks.py`
- Commit: `615741e` | Backfill: 4 prompts updated, Remaining: 0

**Fix B — Focus ring on page load**
- `initPage()` called `focusFirstGalleryCard()` unconditionally on terminal-at-load jobs
- Fix: removed unconditional `setTimeout(focusFirstGalleryCard, 200)` from terminal fetch callback in `static/js/bulk-generator-job.js`
- Commit: `779c106`

**Fix C — `b2_large_url` never set (Media Missing root cause)**
- `display_large_url` property checks `b2_large_url` with NO fallback to `b2_image_url`
- Publish pipeline never set `b2_large_url` → `display_large_url` returned `None` → template rendered Media Missing
- Fix: added `prompt_page.b2_large_url = gen_image.image_url` to both publish functions
- Commit: `523586d` | Backfill: 6 prompts updated, Remaining: 0

**Fix D — SEO rename task never queued for bulk-gen prompts**
- `rename_prompt_files_for_seo` was never queued from the bulk-gen publish path
- Additionally: all 4 URL fields pointed to same physical B2 file — original loop deleted source on first rename, causing `NoSuchKey` for remaining 3 fields. Fixed with group-by-URL deduplication logic
- Fix: queue `async_task('prompts.tasks.rename_prompt_files_for_seo', prompt_page.pk)` outside `transaction.atomic()`, guarded by `not _already_published`
- Commits: `0b1618a` + `f0f965d` | Backfill: 6 renamed, Remaining: 0

**Fix E — Images stored at wrong `bulk-gen/` path**
- Bulk-gen images landed at `bulk-gen/{job_id}/{seo-name}.jpg` instead of `media/images/{year}/{month}/large/{seo-name}.jpg`
- Added `move_file(old_url, target_directory, new_filename)` and `cleanup_empty_prefix(prefix)` to `B2RenameService`
- `rename_prompt_files_for_seo` now detects `'bulk-gen/' in prompt.b2_image_url` and routes to `move_file`
- Commit: `64c3ab1` | Backfill: 6 relocated, 7 orphan B2 files deleted, Remaining: 0

**Heroku releases:** v649 → v653. All backfills clean.

---

#### HARDENING-1 — Sibling-Check Unit Tests + Batch Mirror Field Saves

**Commit:** `3149a9a`

**Part A — 5 unit tests in `prompts/tests/test_bulk_gen_rename.py` (new, 283 lines):**
- `test_sibling_files_present_skips_cleanup` — `KeyCount=1` → no cleanup delete
- `test_empty_prefix_logs_not_deletes` — `KeyCount=0` → log emitted, no cleanup delete
- `test_non_bulk_gen_prompt_no_sibling_check` — standard path → `list_objects_v2` never called
- `test_sibling_check_exception_is_nonfatal` — `ClientError` on sibling check → task returns `status='success'` (non-blocking contract confirmed)
- `test_mirror_fields_batched_into_single_save` — 3 mirror fields saved in exactly 1 `prompt.save(update_fields=[...])` call

**Part B — Batch mirror field saves:**
- Mirror field update loop in `rename_prompt_files_for_seo` previously issued one `prompt.save()` per mirror field
- Refactored to collect all mirror fields and issue single `save(update_fields=mirror_fields_to_save)`
- For bulk-gen prompts with 4 sharing URL fields: mirror-field DB writes reduced from 3 → 1

**Agent Reviews:**
- @django-pro Round 1: 9.5/10 ✅
- @test-automator Round 1: 7.5/10 ❌ — missing exception-swallowing test, no positive assertions in non-bulk-gen test
- @test-automator Round 2: 8.5/10 ✅ (after adding `test_sibling_check_exception_is_nonfatal` + positive assertions)
- **Final average: 9.0/10 ✅**

**Tests:** 1117 passing, 12 skipped (+5 vs Session 119)

---

#### JS-SPLIT-1 — Bulk Generator JS File Split

**Commit:** `e723650`

`bulk-generator-job.js` had grown to 1830 lines (above the 800-line CC safety threshold). Split into 4 logical modules with no behaviour change:

| File | Lines | Contents |
|------|-------|----------|
| `bulk-generator-config.js` | 156 | Namespace init, constants, state variable declarations, utility functions |
| `bulk-generator-ui.js` | 722 | Progress UI, gallery cleanup, card state management, gallery rendering, lightbox |
| `bulk-generator-polling.js` | 408 | Terminal state UI, polling loop, cancel handler, focus management, `initPage`, `DOMContentLoaded` |
| `bulk-generator-selection.js` | 581 | Selection, trash, download, toast, publish bar, publish flow, retry |

- Original `bulk-generator-job.js` deleted
- Shared state via `window.BulkGen = window.BulkGen || {}` (aliased as `var G = window.BulkGen` in each IIFE)
- Template `<script>` tags updated: config → ui → polling → selection, all `defer`
- `collectstatic` confirmed: 253 files copied
- SMOKE2-FIX-B regression confirmed clean by @accessibility

**Agent Reviews:**
- @frontend-developer: 8.5/10 ✅
- @code-reviewer: 9.0/10 ✅ (exhaustive 39-function verification)
- @accessibility: 8.6/10 ✅
- **Average: 8.7/10 ✅**

**Tests:** 1117 passing, 12 skipped (unchanged — refactor only)

---

#### HARDENING-2 — `cleanup_empty_prefix` Internal Prefix Guard

**Commit:** *(latest)*

Added `ValueError` guard to `cleanup_empty_prefix` in `prompts/services/b2_rename.py`:

```python
if not prefix.startswith('bulk-gen/') or prefix == 'bulk-gen/':
    raise ValueError(f"Refusing to clean unsafe prefix: {prefix!r}")
```

CC added the `or prefix == 'bulk-gen/'` check beyond the spec requirement — closes additional edge case where bare prefix would enumerate all job objects. Guard placed immediately after docstring, before any B2 calls. Agent: @security-auditor.

**Tests:** 1117 passing, 12 skipped (unchanged)

---

**Session 121 Stale Items Closed:**
- "N4h rename not triggering" blocker — bulk-gen path resolved by SMOKE2-FIX-D. Upload-flow path renamed to separate open item.
- "Indexes migration pending" — confirmed applied (migration 0045, Session 120). Removed from blockers.

**Session 121 Remaining Issues (deferred to Phase 6E):**
- `ui.js` at 722 lines — monitor as Phase 6E adds UI code
- Static selection announcer (dynamic `aria-live` region)
- `b2_image_url=None` early-exit test
- Per-prompt task leaves empty `bulk-gen/{job_id}/` prefixes in B2 indefinitely (cosmetic)
- Documentation refresh: `PROJECT_FILE_STRUCTURE.md`, `CLAUDE_PHASES.md` references to `bulk-generator-job.js` updated in this docs pass

---

### Session 119 — March 10, 2026

**Focus:** Phase 6D — Per-image publish error recovery + retry

**Completed:**
- `.is-failed` CSS state: 0.40 img opacity (distinct from `.is-discarded` 0.55), red badge strip (`#fef2f2`/`#b91c1c` = 5.9:1 WCAG AA), select+trash hidden, download preserved
- `failed-badge` HTML created in `fillImageSlot()` — hidden by default, shown when `.is-failed`
- Module-level state: `failedImageIds`, `submittedPublishIds`, `stalePublishCount`, `lastPublishedCount`
- `markCardFailed(imageId, reason)` — removes transient states, adds `.is-failed`, updates `selections`
- Stale detection in `startPublishProgressPolling()`: threshold 10 polls (~30s), only counts after first publish
- `_restoreRetryCardsToFailed(retryIds)` helper — reverses optimistic CSS on error
- `handleRetryFailed()` — optimistic re-select, POST `{image_ids: retryIds}`, restore on error
- `handleCreatePages()` — tracks `submittedPublishIds`, clears before new batch, resets stale counters
- `updatePublishBar()` — shows retry button when `failedImageIds.size > 0`, handles `count=0/failedCount>0`
- `focusFirstGalleryCard()` — excludes `.is-failed` cards
- Retry Failed button in template publish bar
- `api_create_pages` backend: `image_ids` retry param bypasses per-image `status='completed'` (not job-level guard)
- 6 new Phase 6D tests in `CreatePagesAPITests`
- Fixed `test_non_completed_images_rejected` false positive (job needs `status='completed'`)
- Fixed error_message test assertions to use `assertEqual('Rate limit reached')`

**Agent Reviews:**
- Round 1: 7.175/10 avg (frontend 7.5, UI 6.5, code 7.5, django 7.2) — BELOW 8.0
- Round 2: 8.9/10 avg (frontend 9.0, UI 9.0, code 9.0, django 8.6) — Phase 6D CLOSED ✅

**Tests:** 1106 passing, 12 skipped, 0 failures

**Commit:** `b7643fb`

**Deferred items resolved in 6D Hotfix + Phase 7 (same session — see below).**

---

### Session 119 (continued) — Phase 6D Hotfix

**Focus:** Accessibility gap from Phase 6C-B.1 + CC_SPEC_TEMPLATE v2.5 upgrade

**Completed:**
- `markCardPublished()`: `aria-hidden="true"` removed from `<a>` badge elements
  (WCAG SC 4.1.2 violation — interactive element hidden from accessibility tree)
- `aria-label="Published — view prompt page (opens in new tab)"` added to `<a>` badges
- `<div>` fallback badges (no URL available) retain `aria-hidden="true"` — correct,
  they are decorative and non-interactive
- `a.published-badge:focus-visible`: added `box-shadow: 0 0 0 4px #166534` outer ring —
  now matches double-ring pattern on all other gallery overlay buttons
- `a.published-badge` CSS rule: `pointer-events: auto` documentation comment added to
  prevent future silent removal (override of base `.published-badge { pointer-events: none }`)
- CC_SPEC_TEMPLATE v2.4 → v2.5: Critical Reminder #9 added — every `assertNotIn` /
  `assertNotEqual` must be paired with a positive assertion (`assertEqual`). Pattern
  caused false-confidence passes in Phases 6C-A and 6D.

**Agent Reviews:** @accessibility 8.6, @code-reviewer 8.8. Avg 8.7/10 ✅

**Tests:** 1106 passing, 12 skipped, 0 failures (unchanged — CSS/JS/docs only)

**Commit:** `6decba2`

---

### Session 119 (continued) — Phase 7: Integration Polish + Hardening

**Focus:** Deferred items from Phase 6 series + rate limiting + integration tests

**Completed:**

- **Fix 1 — `.btn-zoom:focus-visible` double-ring:** Replaced single purple `outline`
  with `box-shadow: 0 0 0 2px rgba(0,0,0,0.65), 0 0 0 4px rgba(255,255,255,0.9)`.
  Now matches `.btn-select`/`.btn-trash`/`.btn-download`. Closes last focus-ring
  inconsistency across all four gallery overlay buttons.

- **Fix 2 — Persistent `#publish-status-text`:** Terminal state writes "X created,
  Y failed". Pre-existing `aria-live="polite"` region (declared in template at page
  load — not dynamically injected) announces completion to screen readers.
  `clearInterval` guard added to `startPublishProgressPolling()` to prevent duplicate
  polling intervals if called twice in rapid succession.

- **Fix 3 — Cumulative retry progress bar:** `totalPublishTarget` increments on
  original submit; retry calls do NOT add to target (images already counted).
  `stalePublishCount` and `lastPublishedCount` reset before each poll cycle. Progress
  bar denominator no longer resets to retry-batch size on retry.

- **Fix 4 — Rate limiter on `api_create_pages`:** `_check_create_pages_rate_limit()`
  helper: `cache.add()` (atomic no-op if key exists) + `cache.incr()` (atomic
  increment). Limit: 10 requests/minute per user. Returns 429 with JSON error on
  breach. Frontend: warning toast ("Wait 60 seconds..."), `failedImageIds` Set
  preserved so retry button stays available. `cache.clear()` added to
  `CreatePagesAPITests.setUp()` for test isolation (prevents stale rate-limit key
  from prior test bleeding into next).

- **6 new tests:** `EndToEndPublishFlowTests` (happy path, partial failure + retry,
  rate limit) in `test_bulk_page_creation.py`; `CreatePagesAPITests` additions in
  `test_bulk_generator_views.py`.

- **Note:** Phase 7 completion report erroneously listed Phase 6D as "next feature
  work" — Phase 6D was already complete at commit `b7643fb`. Corrected in this
  docs update.

**Agent Reviews (Round 2 final):**
@django-pro 9.0, @accessibility 8.5, @frontend-developer 8.5, @code-reviewer 8.5.
Avg 8.625/10 ✅

**Tests:** 1112 passing, 12 skipped, 0 failures (+6 new tests vs Phase 6D)

**Commit:** `ff7d362`

**Bulk Generator status:** Feature-complete for staff use.
Next: production smoke test. Then V2 planning (BYOK premium, Replicate models).

---

### Session 118 — March 10, 2026

**Focus:** Phase 6C-B.1 — CSS fixes + test fix + round 3/4 agent confirmation

---

#### Session 118 — Phase 6C-B.1: Keyboard Trap, Opacity Hierarchy, A11Y Fixes + Round 4 Close

**Commits:** `78ab145` (Phase 6C-B.1 all fixes)

**What was done:**

- **Fix 1 — `.btn-zoom:focus-visible` (keyboard trap WCAG 2.4.11):**
  - Added `opacity: 1 !important; outline: 2px solid var(--accent-color-primary)` on `:focus-visible`
  - Zoom button now visible to keyboard users without changing hover-only behaviour

- **Fix 2 — `.is-deselected` opacity hierarchy:**
  - Raised from 0.20 → 0.65 (initial 0.42 in round 3 was still inverted; raised to 0.65 in round 4)
  - Hover restore: 0.60 → 0.85
  - Correct hierarchy: selected (1.0) > deselected (0.65 slot) > discarded (0.55 img-only) > published (0.70 img)

- **Fix 3 — `available_tags` test assertion:**
  - Added `assertGreater(len(available_tags), 0)` after `assertIsInstance(available_tags, list)`
  - Seeded `Tag.objects.get_or_create(name='fixture-tag')` in setUp for CI reliability

- **Fix 4 — `#generation-progress-announcer`:**
  - Confirmed already pre-rendered in HTML template (no change needed)

- **Fix 5 — Lightbox alt text:**
  - `img.alt = 'Full size preview: ' + promptText.substring(0, 100)` (falls back to generic if no prompt text)

- **Additional round 4 fixes (from agent feedback):**
  - `.loading-text`: `--gray-500` → `--gray-600` (3.88:1 fail → 6.86:1 AA pass on `--gray-100` bg)
  - `.published-badge` published link: `<a>` element with `✓ View page →` text and `pointer-events: auto`
  - `prefers-reduced-motion` block: extended to cover `.prompt-image-slot`, `.is-deselected`, `.btn-zoom` transitions

- **Round 3 scores (avg 7.875 — BELOW 8.0):** @accessibility 8.4, @frontend-developer 7.8, @ui-visual-validator 7.3, @code-reviewer 8.0 → triggered round 4
- **Round 4 scores (avg 8.425 — ABOVE 8.0 ✅):** @accessibility 8.4, @frontend-developer 8.6, @ui-visual-validator 8.2, @code-reviewer 8.5

**Phase 6C-B formally closed. Phase 6D (per-image error recovery + retry) is next.**

**Tests:** 1100 passing, 12 skipped, 0 failures

---

### Session 117 — March 9, 2026

**Focus:** Phase 6C-B — Gallery Card Visual States + Published Badge + A11Y-3/5

---

#### Session 117 — Phase 6C-B: Gallery Visual States + Published Badge

**Commits:** `cc38e95` (round-1 agent fixes), `bc60a4f` (round-2 agent fixes), `9e38a21` (Phase 6C-B completion report)

**What was done:**

- **Phase 6C-B — Gallery card states (4 CSS states):**
  - `.is-selected`: 3px `box-shadow` ring in `--accent-color-primary` (box-shadow avoids layout shift; border clips with overflow:hidden)
  - `.is-deselected`: 20% opacity on whole slot; siblings set to deselected when another is selected
  - `.is-discarded`: 55% opacity on image only (`.prompt-image-slot.is-discarded img`)
  - `.is-published`: green "✓ View page →" badge linking to `prompt_page_url` per card

- **A11Y-3 — Live region for progress:**
  - `#generation-progress-announcer` with `aria-live="polite"` and `aria-atomic="true"` (full text replacement requires true)
  - `sr-only` CSS class defined locally (Bootstrap 5 renamed it to `.visually-hidden`)

- **A11Y-5 — Focus management:**
  - `focusFirstGalleryCard()` called when gallery renders new rows
  - Selector excludes `.is-placeholder`, `.is-published`, and `.is-discarded` (btn-select display:none in those states)

- **Opacity-compounding bug fix:**
  - `handleSelection` allSlots query now excludes `.is-discarded` and `.is-published`
  - Prevents `0.55 × 0.20 = 0.11` effective opacity on discarded cards

- **Additional JS fixes:**
  - `handleTrash` undo path calls `updatePublishBar()` (was missing — stale publish bar count)
  - `markCardPublished` removes `.is-discarded` class (cross-session publish race defense)

- **Published badge defensive guard:**
  - `bulk_generation.py` status API: `if img.prompt_page_id and img.prompt_page` (SET_NULL race defense)

- **Test hardening:**
  - URL assertion strengthened: `assertIn('/')` → `assertEqual` against `reverse()`
  - Dead `img` variable assignments removed

- **Focus ring:**
  - Double-ring pattern: `0 0 0 2px rgba(0,0,0,0.65), 0 0 0 4px rgba(255,255,255,0.9)` — works on any image background
  - Applies to `.btn-download`, `.btn-select`, `.btn-trash` on `:focus-visible`

- **Badge contrast:**
  - `rgba(22,163,74,0.92)` (3.07:1 FAIL) → `#166534` (~7.1:1 PASS)

- **`back-to-generator` link contrast:**
  - `--gray-500` (3.88:1 on off-white FAIL) → `--gray-600` (6.86:1 PASS)

- **2-round agent review:** All blocking/high issues fixed; medium/low addressed where feasible; remaining deferred to 6C-A/6D

**Agent scores (round 2):** @code-reviewer 8.5/10, @accessibility 8.2/10, @ui-visual-validator 8.3/10, @django-pro 8.4/10

**Files changed:**
- `static/js/bulk-generator-job.js` — handleSelection, handleTrash, markCardPublished, focusFirstGalleryCard fixes
- `static/css/pages/bulk-generator-job.css` — 4 CSS states, sr-only, double-ring focus, badge contrast, back-to-generator contrast
- `prompts/templates/prompts/bulk_generator_job.html` — aria-atomic="true", aria-hidden on modals
- `prompts/services/bulk_generation.py` — dual-guard for prompt_page_url
- `prompts/tests/test_bulk_generator_views.py` — URL assertion strengthened, dead code removed

**Test count:** ~1100 passing

---

### Sessions 114–116 — March 9, 2026

**Focus:** Phase 6A bug fixes + Phase 6A.5 data correctness + Phase 6B publish flow (concurrent pipeline) + Phase 6B.5 hardening + Phase 6C-A M2M refactor

---

#### Session 114 — Phase 6A Bug Fixes + Phase 6A.5 Data Correctness

**Commits:** (end-of-session docs commit)

**What was done:**

- **Phase 6A — 6 of 7 Phase 4 scaffolding bugs fixed:**
  - Bug 1 (Critical): `prompt_page__isnull=True` filter added to prevent duplicate page creation in `api_create_pages`
  - Bug 2 (High): Visibility mapping — `status=1 if job.visibility == 'public' else 0` in `publish_prompt_pages_from_job`
  - Bug 3 (Medium): Removed `hasattr(prompt_page, 'b2_image_url')` guard (field always present on model)
  - Bug 5 (Medium): `b2_thumb_url = gen_image.image_url` fallback for thumbnail
  - Bug 6 (Low): `moderation_status='approved'` set explicitly for staff-created pages
  - Bug 4/7 handled in 6B's publish task (TOCTOU → DB lock; categories/descriptors → M2M in publish task)
  - Migration 0066: `prompt_page` FK on `GeneratedImage`
  - Migration 0067: `published_count` IntegerField on `BulkGenerationJob`
  - Status API updated with per-image `prompt_page_id` + `prompt_page_url` fields and job-level `published_count`

- **Phase 6A.5 — Data correctness:**
  - `gpt-image-1` model name aligned to OpenAI SDK identifier (was incorrect string)
  - `size`, `quality`, `model` fields on `BulkGenerationJob` populated correctly at job start

---

#### Session 115 — Phase 6B: Publish Flow UI + Concurrent Pipeline

**Agent scores (initial):** @django-pro 7.2/10, @accessibility 7.5/10, @performance 8.0/10, @security 9.0/10
**Agent scores (post-fix re-run):** @django-pro 8.5/10, @accessibility 8.2/10, @performance 8.0/10, @security 9.0/10

**What was done:**

- **`publish_prompt_pages_from_job` task** (`prompts/tasks.py`):
  - `ThreadPoolExecutor` dispatches Prompt creation across worker threads; all ORM writes on main thread after `futures.result()`
  - Per-image DB-level idempotency lock: `select_for_update()` inside `with transaction.atomic()` — must be inside transaction or lock releases immediately (autocommit mode)
  - `_already_published` flag pattern — `continue` is illegal inside `with transaction.atomic()` body
  - `IntegrityError` on slug collision: UUID suffix appended to title/slug; full M2M block re-applied in second `transaction.atomic()` (Django rolls back original block on `IntegrityError` — M2M must be duplicated in retry path)
  - `published_count` incremented via `F('published_count') + 1` for race-safe counting
  - `_sanitise_error_message` imported locally inside function to avoid circular import

- **Template** (`bulk_generator_job.html`):
  - Sticky publish bar with "Create Pages" button + publish progress bar
  - Static `<div id="bulk-toast-announcer" role="status" aria-live="polite" class="sr-only" aria-atomic="true">` added at page load (not dynamically injected — required for reliable screen reader announcement)

- **JS** (`bulk-generator-job.js`):
  - `handleCreatePages()` — POST to `api_create_pages`, disable button after submit, poll for `published_count`, show toast feedback
  - `showToast()` updated: clear-then-set pattern on static announcer (50ms timeout between clear and populate)
  - Removed `role="status"` and `aria-live="polite"` from dynamic toast element (decoupled visual from AT announcement)

- **Tests** (`test_bulk_generator_views.py`):
  - Fixed existing `test_non_completed_images_rejected` assertion: `'not found or not completed'` → `assertIn('not complete', ...)`
  - Added `PublishFlowTests` class (9 tests): view rejects in-progress job, view rejects oversized list, status API includes `prompt_page_id`/`prompt_page_url`/`published_count`, publish task uses concurrent workers, all ORM writes on main thread, progress counter increments per page, second POST returns zero (idempotency)

- **Report created:** `docs/REPORT_BULK_GEN_PHASE6B.md` (14-section technical report)

**Tests:** 1067 → 1076 passing, 12 skipped

**Key patterns established (apply to all future work):**
- `select_for_update()` must be inside `with transaction.atomic()` — locks release immediately in autocommit mode
- `continue` is illegal inside `with transaction.atomic()` — use flag pattern
- M2M must be duplicated in `IntegrityError` retry block — Django rolls back full atomic block
- Static `aria-live` regions must exist at page load — dynamic injection is unreliable for screen readers

#### Session 116 — Phase 6B.5: Transaction Hardening & Quick Wins

**Commit:** 99e62fa

**Agent scores:** @django-pro 8.5/10 (PASS), @code-reviewer 8.5/10 (PASS), @security-reviewer 9.0/10 (PASS)

**What was done:**

- **`create_prompt_pages_from_job`** (`prompts/tasks.py`):
  - All ORM writes now inside `transaction.atomic()` with per-image `select_for_update()` re-check — previously a no-op in autocommit mode
  - `_already_published` flag pattern — `continue` illegal inside `with transaction.atomic()`
  - `IntegrityError` retry now re-applies full M2M block inside its own `transaction.atomic()` — previously only called `save()`, losing all M2M relationships
  - `errors.append(str(e)[:200])` → `errors.append(_sanitise_error_message(str(e)))` — routes through security boundary
  - `available_tags` pre-fetched before loop via `Tag.objects.order_by('id').values_list('name', flat=True)[:200]`
  - `logger.warning(...)` added on AI content failure path
  - Stale docstring updated: "content_generation service" → "_call_openai_vision()"

- **`publish_prompt_pages_from_job`** (`prompts/tasks.py`):
  - `F('published_count') + 1` update moved inside `transaction.atomic()` block (both primary and IntegrityError retry paths) — previously outside, risking phantom counts on crash
  - `available_tags` pre-fetched before worker closure with `order_by('id')`
  - `skipped_count` clarifying comment added to return dict

- **`_call_vision_for_image` worker closure** (`prompts/tasks.py`):
  - `str(exc)[:200]` → `_sanitise_error_message(str(exc))` — fixes security boundary bypass

- **`hasattr(prompt_page, 'tags')` guards removed** — dead code from early scaffolding; always true at runtime. All 4 occurrences replaced with bare `if raw_tags:`

- **`BulkGenerationJob.generator_category` default** (`prompts/models.py`): `'ChatGPT'` → `'gpt-image-1'`

- **Migration 0068** (`prompts/migrations/0068_fix_generator_category_default.py`): `AlterField` + `RunPython` backfill — updated 35 rows from `'ChatGPT'` to `'gpt-image-1'`

- **Tests** (`test_bulk_page_creation.py`): `TransactionHardeningTests` (8 tests) — atomic rollback on M2M failure, concurrent idempotency, already-published skip, error sanitisation, available_tags plumbing, F() increment, migration data backfill

**Tests:** 1076 → 1084 passing, 12 skipped

#### Session 116 (continued) — Phase 6C-A: M2M Helper Extraction + Publish Task Tests

**Commit:** `1c630db`

**What was done:**

- **Extract `_apply_m2m_to_prompt()` helper** (`prompts/tasks.py`):
  - Eliminated 4 duplicate M2M blocks (tags, categories, descriptors) across primary path + IntegrityError retry in both `create_prompt_pages_from_job` and `publish_prompt_pages_from_job`
  - Helper applies tags, categories, descriptors, `source_credit`, `generator_category` + optional `b2_image_url`
  - Reduces maintenance risk — M2M logic now in one place

- **14 PublishTaskTests** (`prompts/tests/test_bulk_generator_views.py`):
  - Concurrent race: two threads don't double-publish same image
  - IntegrityError retry: full M2M re-applied in retry path
  - Partial failure: some succeed, some fail, `errors[]` populated correctly
  - `_sanitise_error_message` boundary: raw exception strings not in errors
  - `available_tags` passed to `_call_openai_vision`
  - Stale test corrections: `available_tags` assertion updated, `generator_category` default corrected

**Tests:** 1084 → 1098 passing, 12 skipped
**Report:** `docs/REPORT_BULK_GEN_PHASE6CA.md`

---

### Sessions 108–113 — March 7–8, 2026

**Focus:** Phase 5D complete (concurrent generation + Failure UX hardening) + Phase 6 architect review + Phase 6 architecture decisions

---

#### Sessions 108–111 — Phase 5D: Concurrent Generation + Failure UX

**Commits:** 775f0dc, 4ceb89b, 40b0c32, a737ad6, 50c5051, 59ff672, a7e0205, 94347ff, 0222c38, 05de661

**Phase 5D bug fixes:**
- **Bug A — Concurrent generation (ThreadPoolExecutor):** Replaced sequential `_run_generation_loop` with `ThreadPoolExecutor(max_workers=4)`. `BULK_GEN_MAX_CONCURRENT` env var added to `settings.py` (default 4). Worker creates own provider per thread; all ORM saves on main thread after `future.result()`. Cancel detection between batches.
- **Bug B — Count mismatch:** `handleTerminalState()` now uses actual `completed_count` from API response instead of hardcoded `totalImages`. Partial-completion message shown when some images failed.
- **Bug C — Dimension override UI:** Per-prompt `<select>` disabled with `title="Per-prompt dimensions coming in v1.1"` tooltip, `(v1.1)` label, and `data-future-feature` marker.
- **P2 — Per-image F() progress:** `completed_count` and `failed_count` updated via atomic `F()` expressions after each individual image (instead of once per batch). Progress bar updates every 15–45s per image.
- **P2 — Configurable concurrency:** `BULK_GEN_MAX_CONCURRENT` in `settings.py` enables Heroku config var change without code deploy.

**Failure UX hardening:**
- `_sanitise_error_message()` security boundary in `bulk_generation.py` — whitelist-style mapper to 6 fixed output categories. Keyword-ordered (specific before broad) to prevent masking. 'quota' keyword added for OpenAI billing errors. 'rate' → 'rate limit' to prevent false positive on 'generate'.
- `get_job_status()` returns `error_message` (sanitised) per image and `error_reason` at job level.
- Gallery failure slots: reason text + 60-char truncated prompt + aria-label for screen readers.
- JS `_getReadableErrorReason()` refactored from substring matching to exact-match map against 6 fixed backend strings.
- `role=alert` on terminal error regions (was `role=status` — wrong for terminal errors).
- CSS: `.failed-reason` (#b91c1c, 5.78:1 on gray-100), `.failed-prompt` (--gray-600, 7.07:1).

**Test fixes:**
- List-based `side_effect` mocks replaced with prompt-keyed functions (deterministic under `ThreadPoolExecutor`).
- Added `ConcurrentGenerationLoopTests` (4 tests), `SanitiseErrorMessageTests` (17 tests), `JobStatusErrorReasonTests` (5 tests).
- `FERNET_KEY` added to `ConcurrentGenerationLoopTests`.
- Renamed `test_max_concurrent_constant_is_four` → `test_max_concurrent_reads_from_settings` (env-aware).

**Process upgrade:**
- CC_SPEC_TEMPLATE upgraded to v2.3 — mandatory SELF-IDENTIFIED ISSUES POLICY section added.
- CLAUDE.md: off-white contrast note added — `--gray-500` fails AA on `--gray-100` (3.88:1); `--gray-600` required as minimum on tinted backgrounds.

**Agent scores:** @django-pro 9/10, @security-auditor 9/10, @performance-optimizer 9/10, @accessibility-specialist 8.5/10, @code-reviewer 9/10 (Session 108); @django-pro 9/10, @code-reviewer 9/10, @performance-engineer 8/10 (Session 110); @django-pro 9.2/10, @code-reviewer 9.0/10 (Session 111 post-fix)

**Tests:** 990 → 1008 passing, 12 skipped

---

#### Session 112 — Phase 6 Architect Review (design only, no commits)

**Deliverable:** `PHASE6_DESIGN_REVIEW.md` (project root)

Codebase review of Phase 4 scaffolding code before building Phase 6 UI. Three specialist agents consulted.

**7 bugs found in existing scaffolding:**
1. Duplicate page creation — `api_create_pages` missing `prompt_page__isnull=True` (Critical)
2. Visibility not mapped — `create_prompt_pages_from_job` hardcodes `status=0` regardless of `job.visibility` (High)
3. `hasattr(prompt_page, 'b2_image_url')` always True — model field always present (Medium)
4. TOCTOU race in `_ensure_unique_title` / `_generate_unique_slug` — check-then-act pattern (Medium)
5. Missing `b2_thumb_url` — full-size URL assigned but thumb URL never set (Medium)
6. Wrong `moderation_status` — defaults to `'pending'` for staff-created pages (Low)
7. Missing categories/descriptors — ai_content response contains them but M2M never populated (Low)

**8 architectural decisions documented** in `PHASE6_DESIGN_REVIEW.md`: sub-phase breakdown (6A→6D), b2_thumb_url fallback strategy, visibility mapping, TOCTOU protection, idempotency guard, categories/descriptors assignment, frontend wiring, post-creation feedback (Option D: toast + View badge).

**Agent scores:** @architect-review 8.0/10, @django-pro 6.5/10 (reflecting existing code quality), @ui-ux-designer 8.5/10
**Average:** 7.67/10 — below 8.0 threshold, but @django-pro score reflects real bugs in existing code (not spec quality). Review documents this explicitly.

---

#### Session 113 — Phase 6 Architecture Decisions (design only, no commits)

**Deliverable:** `PHASE6_DESIGN_REVIEW.md` updated; `docs/REPORT_PHASE6_ARCHITECT_REVIEW.md` created (1239 lines)

Architecture decisions confirmed for Phase 6 implementation:
- **Two-page architecture:** Temp staging page (Phase 6) + archive staging page (future phase — Phase L or M)
- **One image per prompt published:** Prevents near-duplicate content in search/feed
- **Non-selected variations:** Archived (not deleted immediately); retained for tier window
- **Retention window:** 2–10 days by tier (storage-cost-realistic at this stage)
- **Visibility mapping confirmed:** `'private'` = Draft (`status=0`); `'public'` = Published (`status=1`)
- **Phase 6D confirmed in scope:** Per-image error recovery and retry
- **Archive staging page:** Future phase (Phase L or M) — not Phase 6

---

### Session 108 — March 7, 2026

**Focus:** Bulk Generator Phase 5D — Bug fixes A/B/C (concurrent generation, count display, dimension select)

**Commit:** 775f0dc

**What was done:**

- **Bug A — Concurrent image generation (ThreadPoolExecutor):**
  - Replaced sequential `_run_generation_loop` with `ThreadPoolExecutor(max_workers=4)` batch processing
  - `MAX_CONCURRENT_IMAGE_REQUESTS = 4` constant added
  - Worker creates its own provider instance per thread (thread-safe)
  - All ORM saves (`image.save()`, `job.save()`, `clear_api_key()`) moved OUT of worker threads into main thread after `future.result()` — prevents SQLite write contention in tests; improves safety on PostgreSQL
  - Cancel detection fires between batches via `job.refresh_from_db()`

- **Bug B — Fix count mismatch in job page (bulk-generator-job.js):**
  - `handleTerminalState('completed')` was hardcoding `totalImages + ' of ' + totalImages`
  - Now uses actual `completed` count from API response; shows partial-completion message when some images failed

- **Bug C — Disable per-prompt Dimensions select (bulk-generator.js):**
  - Added `disabled`, `title="Per-prompt dimensions coming in v1.1"`, `data-future-feature="per-prompt-dimensions"`
  - Label updated with `(v1.1)` visible span

- **Test updates:**
  - 4 new `ConcurrentGenerationLoopTests` (constant value, multi-batch, worker exception, exact-4-batch)
  - `test_auth_error_stops_job`: updated `assertEqual(call_count, 1)` → `assertLessEqual(call_count, 3)` (concurrent semantics)
  - `test_process_job_cancelled_mid_processing`: rewrote using `patch.object(BulkGenerationJob, 'refresh_from_db')` to avoid SQLite cross-thread transaction isolation issue
  - Root cause: `_run_generation_with_retry` was calling `image.save()` from worker threads; SQLite TestCase transaction wrapping made cross-thread DB writes return "table is locked"

- **Test results:** 990 passing, 12 skipped, 0 failures

- **Agent ratings:** django-pro 9/10, security-auditor 9/10, performance-optimizer 9/10, accessibility-specialist 8.5/10, code-reviewer 9/10

---

### Sessions 101–107 — March 6–7, 2026

**Focus:** Bulk Generator Phase 5C + 5B + P1/P2 production hardening + Phase 5D spec

**Commits:** b77edf7, ee98e5f, d841913, c7c6f57, 77019eb, 62568e6, 1e88b06

**What was done:**

- **Phase 5C — Real GPT-Image-1 generation confirmed end-to-end:**
  - Upgraded openai SDK 1.54.0 → 2.26.0; old SDK silently injected `response_format='b64_json'` which GPT-Image-1 rejects
  - Full pipeline confirmed: job creation → Django-Q2 task → `provider.generate()` → B2 upload → CDN URL → DB record → gallery render
  - boto3 1.35.0 → 1.42.62, botocore 1.35.99 → 1.42.62, s3transfer 0.10.4 → 0.16.0 (resolved Heroku build v644 dependency conflict)

- **Phase 5B bug fixes (Sessions 102–103):**
  - Bug 1: `images_per_prompt` — task loop now correctly iterates all slots; gallery renders all variation records, not just slot 1
  - Bug 2: Aspect ratio end-to-end — `job.size` passed through task → provider → `client.images.generate(size=)`; gallery CSS applies correct class
  - Bug 3: Unsupported dropdown options — `1792x1024` and others hidden with `d-none` + `data-future="true"`; default reset to `1024x1024`

- **P1/P2 hardening (Sessions 104–107):**
  - DRY-1: `SUPPORTED_IMAGE_SIZES` + `ALL_IMAGE_SIZES` centralised in `prompts/constants.py`; all files import from constants — no more local `VALID_SIZES` definitions
  - CRIT-1/2/3: test references constants; `1792x1024` annotated UNSUPPORTED in `SIZE_CHOICES`; removed from `create_test_gallery.py`
  - SEC-1: Fixed `isinstance(bool, int)` bypass in `images_per_prompt` validation
  - SEC-4: Verbatim comment added to `flush_all` `@login_required` decorator explaining why not `@staff_member_required`
  - SEC-5: `api_validate_openai_key` no longer leaks raw exception strings
  - UX-1: Unsupported dimension options use `disabled` attribute + "(coming soon)" text
  - A11Y-1: `aria-atomic="true"` added to `#dimensionLabel`
  - A11Y-4: `aria-describedby="dimensionLabel"` added to dimension radiogroup
  - Migration 0065: choices-only `SIZE_CHOICES` label update (no DDL)

- **Flush button — "Trash Test Results" (Sessions 104–105):**
  - Staff-only `POST /tools/bulk-ai-generator/api/flush-all/` endpoint
  - Deletes B2 files in batches of 1000 via `delete_objects`; deletes unpublished DB images then jobs; published records (`prompt_page_id IS NOT NULL`) never touched
  - Uses `@login_required` + explicit staff check (not `@staff_member_required` — would redirect instead of returning 403 JSON)
  - Frontend: confirm modal, error modal, success banner with counts + 1.5s redirect
  - Located in sticky bar on both `bulk_generator.html` and `bulk_generator_job.html`
  - 8 new `FlushAllEndpointTests`

- **Phase 5D spec written:** Bug A (ThreadPoolExecutor), Bug B (count mismatch), Bug C (per-prompt override UI). Ready to run with CC.

**Agent reviews:**
- Phase 5B: 6 agents, avg 7.5/10 (4 below threshold — led directly to P1/P2 spec)
- P1/P2: 6 agents, avg 8.37/10 (all above threshold — approved)

**Tests:** 985 passing, 12 skipped (up from 976)

**Key learnings:**
- **Django 5.2 DOES generate migrations for `choices` label changes** — `CC_SPEC_TEMPLATE.md` boilerplate previously stated it did not; this was wrong and caused spec discrepancies twice this session. Template corrected.
- **`ThreadPoolExecutor` (not `asyncio`) required in Django-Q2 task context** — `asyncio.run()` does not work inside Django-Q2 tasks; use `concurrent.futures.ThreadPoolExecutor` for concurrent GPT-Image-1 calls.
- **`flush_all` intentionally uses `@login_required` + manual staff check** — `@staff_member_required` redirects non-staff to login (HTML response), breaking AJAX callers expecting JSON. Manual check returns `JsonResponse({'error': ...}, status=403)`. Documented with verbatim comment in view.
- **GPT-Image-1 sequential loop causes 2-minute+ waits** — At Tier 1 (5 images/min), 8 images = ~90s minimum sequentially. `ThreadPoolExecutor` in Phase 5D will parallelize within rate limits.

**Status at end of session:** Phase 5D spec written and ready to run with CC. Phase 6 (image selection + page creation) follows after Phase 5D completes.

---

### Session 104 - March 6, 2026

**Focus:** Phase 5C debugging + end-of-session documentation update

**Completed:**

- **Phase 5C investigation spec executed:** Added `[BULK-DEBUG]` diagnostic logging to three locations:
  - `BulkGenerationService.start_job()` in `prompts/services/bulk_generation.py` — logs before/after `async_task()`, captures `task_id` return value
  - `process_bulk_generation_job()` in `prompts/tasks.py` — logs at entry point to confirm task execution
  - `_upload_generated_image_to_b2()` in `prompts/tasks.py` — logs at entry and on successful upload with final CDN URL

- **Key finding — Django-Q2 sync behavior in local dev:** Tasks queued via ORM broker execute in the web process (runserver), not the qcluster process. `[BULK-DEBUG] process_bulk_generation_job CALLED` confirmed for job `0df5ec9f` in runserver output. Production behavior (separate Heroku worker dyno) is unaffected.

- **End-of-session docs updated** (this session): CLAUDE.md, CLAUDE_PHASES.md, PROJECT_FILE_STRUCTURE.md

**Key Findings:**
- `prompts.tasks` imports cleanly — not the source of queue issues
- Django-Q2 runs synchronously in local dev; tasks execute in web process (`runserver.log`), not `qcluster.log`
- `[BULK-DEBUG] process_bulk_generation_job CALLED` confirmed for job `0df5ec9f`
- Full E2E image generation (OpenAI call → B2 upload → DB record) not yet confirmed — carried over to Session 105

**Tests:** 976 passing, 12 skipped

**Status:** Phase 5C ✅ complete. E2E verification pending → Phase 6 next after E2E confirmed.

---

### Session 101 - March 6, 2026

**Focus:** Post-commit fixes from Session 100 agent reviews — layer separation, key clearing, flaky test

**Context:** Session 100 completed Phase 5C and committed. Agent reviews flagged two code quality issues (@django-pro 7.5/10, @security 7.0/10) plus a flaky test discovered in the full suite (`TypeError` at `except AuthenticationError:`).

**Completed:**

- **`IMAGE_COST_MAP` layer separation** (`prompts/constants.py` + affected files):
  - Moved `IMAGE_COST_MAP` from `prompts/views/bulk_generator_views.py` to `prompts/constants.py`
  - Fixes `tasks.py` → `bulk_generator_views.py` layer boundary violation flagged by @django-pro
  - Updated imports in `tasks.py`, `bulk_generator_views.py`, and `test_bulk_generator_job.py`

- **`try/finally` for BYOK key clearing** (`prompts/tasks.py`):
  - Wrapped the generation loop + finalization in `try/finally`
  - `BulkGenerationService.clear_api_key(job)` now guaranteed to run on any exit path
  - Fixes @security finding: unhandled exceptions could leave encrypted API key in DB
  - `clear_api_key()` is idempotent (`if job.api_key_encrypted:` guard), so double-calls are safe
  - Updated `test_auth_error_stops_job`: `assert_called_once_with` → `assert_called_with` (double-call expected)

- **`openai_provider.py` exception import fix** (`prompts/services/image_providers/openai_provider.py`):
  - Moved `from openai import (AuthenticationError, RateLimitError, BadRequestError, APIStatusError)` OUTSIDE the `try` block
  - Only `from openai import OpenAI` stays inside the `try` block
  - Fixes flaky `TypeError: catching classes that do not inherit from BaseException` in full suite
  - Root cause: if `sys.modules['openai']` gets contaminated by any test, exception classes bound inside the `try` would be MagicMocks, causing `TypeError` at the `except` clauses
  - 4 `OpenAIProviderGenerateTests` confirmed passing after fix

- **CLAUDE_PHASES.md** updated: Phase 5C marked complete, version bumped to 4.8

**Tests:** 76 critical tests (test_bulk_generation_tasks + test_bulk_generator_job) all passing. Full suite running.

**Agent Scores:** N/A (fixes-only session — no new spec)

**Next up:** Phase 5D — Gallery interactive features (lightbox, download, selection, trash)

---

### Session 100 - March 6, 2026

**Focus:** Bulk AI Image Generator — Phase 5C: Real OpenAI Generation, BYOK, Rate Limiting, Retry Logic

**Context:** Following Session 99 which set up the OpenAI API and ran Phase 5B audit fixes, this session wired up real GPT-Image-1 generation to replace mock mode.

**Completed:**

- **Phase 5C Spec 2 — Real OpenAI Generation:**
  - Replaced mock generation with real OpenAI API calls in `OpenAIImageProvider.generate()`
  - Extended `GenerationResult` dataclass with `error_type` and `retry_after` fields
  - Structured error handling: auth → stop job, rate_limit/server_error → exponential backoff (30s→60s→120s, max 3 retries), content_policy → fail image only, unknown → fail image only
  - BYOK: `api_key_encrypted` decrypted from job record using Fernet; passed to provider's `generate()`
  - 13-second delay between images (tier 1: 5 images/min); skipped for first image
  - Cancel check via `job.refresh_from_db(fields=['status'])` before every image
  - Cost from `IMAGE_COST_MAP` (not from `result.cost`) after successful generation
  - Auth failure now correctly sets `job.status='failed'`; finalization skips both `'cancelled'` and `'failed'`
  - `images.count()` cached before loop to avoid repeated DB queries
  - `decrypt_api_key` wrapped in try/except to handle corrupted keys gracefully

- **Refactoring (complexity reduction):**
  - Extracted `_run_generation_with_retry()` — retry logic helper (reduces McCabe complexity)
  - Extracted `_apply_generation_result()` — B2 upload + image DB update
  - Extracted `_run_generation_loop()` — full for loop with rate limiting and cancel detection
  - `process_bulk_generation_job()` McCabe complexity reduced from 21 → under 15

- **Test updates (5 files, 975 total, all passing):**
  - `ProcessBulkJobTests`: all 6 tests updated to use `_make_job()` helper (BYOK compatibility)
  - `test_process_job_actual_cost`: fixed expected cost from `Decimal('0.1')` → `Decimal('0.068')` (uses IMAGE_COST_MAP)
  - `EdgeCaseTests`: added `FERNET_KEY` to override_settings + `_make_job()` helper
  - New `RetryLogicTests` class (5 tests): auth stops job + verifies `clear_api_key` called, content_policy continues job, rate_limit retries then succeeds, rate_limit exhaustion fails image, missing API key fails fast
  - New `OpenAIProviderGenerateTests` class (4 tests): success, auth error, rate_limit, content_policy
  - Fixed `test_bulk_generator.py` `test_openai_provider_generate_failure`: replaced `patch.dict(sys.modules)` with `patch('openai.OpenAI')` to avoid TypeError with structured exception handling

- **Bug fix found during auth test:** `process_bulk_generation_job` was overwriting `job.status='failed'` (set by auth path) with `'completed'` because finalization only excluded `'cancelled'`. Fixed: `if job.status not in ('cancelled', 'failed'):`

**Agent Scores (Session 100):**
- @django-pro: 8.6/10 (re-review after fixes; was ~6.5)
- @security: 7.0/10 (CRITICAL: pre-existing FERNET_KEY in git history; HIGH: no key clearing on unhandled exceptions — partially fixed via decrypt try/except)
- @test-engineer: 8.2/10 (re-review after rate-limit exhaustion + clear_api_key assertion added)
- @code-reviewer: 7.5/10 (initial; views→tasks import structural concern, hardcoded 13s sleep)

**Commit:** `e6c9f3b` — `feat(bulk-gen): Phase 5C — real OpenAI generation with BYOK, rate limiting, retry logic`

**Tests:** 975 total (up from 971), all passing, 12 skipped

**Next up (Phase 5C remaining / Phase 5D):**
- Phase 5D: Gallery interactive features (lightbox, download, selection, trash)
- Phase 6: Page creation workflow from gallery
- Phase 7: Integration + polish

---

## 📦 Older sessions archived

Sessions 13 through 99 (December 13, 2025 through March 4–5, 2026) have been archived to [`archive/changelog-sessions-13-99.md`](archive/changelog-sessions-13-99.md) to reduce CHANGELOG read overhead.

For chronological context, the most recent archived session is Session 99 (March 4–5, 2026). The oldest is Session 13 (December 13, 2025). The "Session XX - [Date]" template stub previously at the file footer was also moved to the archive.

If you need to add a new session entry, follow the format established in Sessions 100+ above. The template stub is no longer in this active file.

— Archived per Session 168-B refactor (168-A audit recommendation)
