# REPORT: 154-P — Results Page Friendly Model Name + Aspect Ratio Placeholder Cards

**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Two small polish issues on the bulk generator job detail page surfaced
after Phase REP shipped Replicate and xAI models. First, the Model row
showed the raw `model_identifier` (e.g. `google/nano-banana-2`) instead
of the friendly `GeneratorModel.name` ("Nano Banana 2"). Second,
placeholder cards in the gallery always rendered 1:1 for Replicate jobs
because `gallery_aspect` was computed assuming pixel dimensions
(`1024x1536`), and Replicate jobs store `job.size` as an aspect ratio
string (`2:3`). The pixel split silently fell through to the 1:1
fallback. This spec fixes both without any migration — pure view and
template changes.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `model_display_name` computed in job detail view | ✅ Met |
| Falls back to raw `job.model_name` when no `GeneratorModel` exists | ✅ Met |
| Template uses `model_display_name` instead of `job.model_name` | ✅ Met |
| `gallery_aspect` handles `x` (pixel) format | ✅ Met |
| `gallery_aspect` handles `:` (aspect ratio) format | ✅ Met |
| Both formats have `try/except` fallback to `"1 / 1"` | ✅ Met |
| `python manage.py check` → 0 issues | ✅ Met |
| Test coverage for all 6 new branches | ✅ Met (6 tests, all passing) |

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Lines 118–144 (job detail view): Replaced the single pixel-only
  `gallery_aspect` block with a two-branch check:
  - Outer `if job.size:` guard against None/empty.
  - `if 'x' in job.size:` — pixel split (legacy OpenAI path).
  - `elif ':' in job.size:` — aspect ratio split (Replicate/xAI path).
  - Each branch has `try/except (ValueError, TypeError)` fallback to
    `"1 / 1"`.
- Lines 139–143: Added inline `GeneratorModel` lookup:
  `GenModel.objects.filter(model_identifier=job.model_name).first()`.
  Falls back to raw `job.model_name` if no match. Local import is used
  to avoid bloating the top-of-file import list for a single use.
- Line 166: Added `'model_display_name': model_display_name` to the
  render context.

### prompts/templates/prompts/bulk_generator_job.html
- Line 49: Replaced `{{ job.model_name }}` with `{{ model_display_name }}`
  in the Model setting row.

### prompts/tests/test_bulk_generator_views.py
- Appended new test class `JobDetailViewContextTests` (~85 lines,
  6 tests) covering all new branches:
  1. `gallery_aspect` pixel format `'1024x1536'` → `'1024 / 1536'`
  2. `gallery_aspect` aspect ratio format `'2:3'` → `'2 / 3'`
  3. `gallery_aspect` empty size → `'1 / 1'`
  4. `gallery_aspect` garbage size (`'garbagexinput'`) → try/except
     fallback to `'1 / 1'`
  5. `model_display_name` resolves via `GeneratorModel.name` when
     identifier matches
  6. `model_display_name` falls back to raw `job.model_name` when no
     `GeneratorModel` exists
- Each test creates a minimal `BulkGenerationJob` via `_make_job` helper.
- Test 5 explicitly creates a `GeneratorModel` row because the test DB
  does not run the `seed_generator_models` command by default.

## Section 4 — Issues Encountered and Resolved

**Issue:** Test 5 (`test_model_display_name_from_generator_model`) failed
on first run with `AssertionError: 'black-forest-labs/flux-dev' != 'Flux Dev'`.
**Root cause:** `seed_generator_models` is a management command, not a
migration. Test databases are built from migrations only, so the
`GeneratorModel` table is empty at test start.
**Fix applied:** Replaced the `.update()` pattern (which silently no-ops
on an empty table) with explicit `GeneratorModel.objects.create(...)`.
**File:** `prompts/tests/test_bulk_generator_views.py`, test 5.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met. @tdd-orchestrator
suggested an additional garbage-colon fallback test (`size='abc:xyz'`)
for full branch coverage. Not added — the logic mirrors the pixel
garbage path which is already tested, and the agent noted "identical
guard — low risk." Could be added in a future micro-cleanup.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `display_size = job.size.replace('x', '×')` (line 116) is
unchanged. For aspect ratio jobs (`2:3`), this is a no-op and the
display string remains `2:3` — acceptable, but the size row in the UI
now looks different depending on the model family. Users may briefly
wonder why a Flux job shows "2:3" instead of pixels.
**Impact:** Cosmetic; users can infer from context.
**Recommended action:** Consider showing a tooltip or subtitle
explaining that aspect ratio models don't use fixed pixel dimensions.
Low priority. Location: `prompts/templates/prompts/bulk_generator_job.html`
around line 53 (size row).

**Concern:** `GeneratorModel` lookup runs on every job detail page
render. For a staff-only page this is negligible, but if this pattern
spreads the query count could grow.
**Impact:** Negligible.
**Recommended action:** None currently. Revisit only if the `GenModel`
lookup starts showing up in slow-query logs.

## Section 7 — Agent Ratings

**Agent name substitutions (Option B authorised):**
- `@tdd-coach` → `@tdd-orchestrator` ✅ (used here)
- `@django-security` → `@backend-security-coder` (not used this spec)
- `@accessibility-expert` → `@ui-visual-validator` (not used this spec)

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 8.5/10 | Format detection reliable; `try/except` guards correct; fallback to raw `model_name` preserves legacy jobs; suggested test for colon branch; minor style note on inline import | No test added immediately — addressed via TDD orchestrator's test suite |
| 1 | @tdd-orchestrator | 7.5/10 | **All 6 new branches untested** — blocked below 8.0 threshold | Yes — added 6 tests for every branch |
| 2 | @tdd-orchestrator | 9.2/10 | All 6 branches now covered; minor gap on colon-branch garbage path (not critical — identical guard) | Documented in Section 5 as an optional follow-up |
| **Average** (Round 2) | | **8.85/10** | | Pass ≥8.0 ✅ |

## Section 8 — Recommended Additional Agents

**@frontend-developer:** Would have verified the aspect-ratio
placeholder cards render correctly in the browser across multiple
ratios (2:3, 16:9, 9:16, 5:4). Deferred to developer manual browser
checks after full suite passes.

## Section 9 — How to Test

*(Filled in after full suite passes.)*

## Section 10 — Commits

*(Filled in after full suite passes.)*

## Section 11 — What to Work on Next

1. Run full test suite — must pass before committing any of N/O/P.
2. Developer browser checks per Run Instructions:
   - Flux Dev job results page → "Flux Dev" displayed (not identifier)
   - Flux 2:3 job → placeholder cards render portrait
   - OpenAI 1024x1536 job → still renders portrait
3. Optional micro-cleanup: add colon-branch garbage fallback test
   (Section 5).
