═══════════════════════════════════════════════════════════════
SPEC 153-J: PRICE HELPER REFACTOR — DETAILED COMPLETION REPORT
═══════════════════════════════════════════════════════════════

**Spec:** CC_SPEC_153_J_PRICE_HELPER.md
**Session:** 153 (Batch 2, Spec 4 of 4)
**Date:** April 12, 2026
**Commit:** `9744a5e`
**Full Suite:** 1226 tests passing, 0 failures, 12 skipped (652.7s)

---

## Section 1 — Overview

### The Problem

`IMAGE_COST_MAP.get(quality, {}).get(size, 0.034)` — a two-level
dictionary lookup with a hardcoded fallback — was duplicated across
three Python files. When pricing changed (Session 153-C updated
`IMAGE_COST_MAP` from GPT-Image-1 to GPT-Image-1.5 pricing), all
three fallback defaults had to be updated in lockstep. Two of the
three were missed:

- **153-C** missed the JS `I.COST_MAP` entirely (caught by 153-F)
- **153-C** missed the `|| 0.042` fallback in `bulk-generator.js`
  line 846 (caught by 153-F Step 1 verification grep)
- **153-C** missed the `0.042` fallback in
  `openai_provider.py:302` and `bulk_generator_views.py:82`
  (caught by agents during 153-C review)

This pattern of "update the constant, miss the scattered fallbacks"
was unsustainable. The solution: a single `get_image_cost()` helper
that encapsulates both the lookup chain AND the fallback default,
so call sites import and call a function instead of repeating a
two-level `.get().get()` pattern with a magic number.

### What Was Done

A `get_image_cost(quality, size, fallback=0.034)` helper was added
to `prompts/constants.py`. All three Python call sites were migrated
to use it. The `fallback` parameter defaults to `0.034` (the
medium-square GPT-Image-1.5 price), matching the value that was
previously hardcoded at each call site. A dead `IMAGE_COST_MAP`
import in `bulk_generator_views.py` was removed after migration.
Three direct unit tests were added for the helper at the
recommendation of the @tdd-orchestrator agent.

### Scope Boundary

This spec covers **Python call sites only**. The JavaScript
`I.COST_MAP` in `bulk-generator.js` (the input-page sticky bar)
remains a hardcoded client-side copy. Replacing it with a Django
template context variable that injects pricing from Python at render
time is a planned follow-up. The JS copy was updated to
GPT-Image-1.5 values in 153-F and is currently consistent with the
Python constant — but the drift risk remains.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| `get_image_cost()` helper added to `constants.py` | ✅ Met | Lines 456-472, with full docstring |
| All 3 Python call sites use the helper | ✅ Met | `openai_provider.py:306`, `tasks.py:2664`, `views:82` |
| `IMAGE_COST_MAP` import removed from `openai_provider.py` `get_cost_per_image` | ✅ Met | Now imports `get_image_cost` instead |
| Dead `IMAGE_COST_MAP` import removed from `bulk_generator_views.py` | ✅ Met | Caught by @code-reviewer; removed |
| No bare `IMAGE_COST_MAP.get().get()` at the 3 call sites | ✅ Met | Verified via grep — 0 results |
| `python manage.py check` returns 0 issues | ✅ Met | |
| Direct unit tests for the helper | ✅ Met | 3 tests in `GetImageCostHelperTests` |
| Full suite passes | ✅ Met | 1226 tests, 0 failures, 12 skipped |

---

## Section 3 — Changes Made

### prompts/constants.py — New helper function (lines 456-472)

```python
def get_image_cost(quality: str, size: str, fallback: float = 0.034) -> float:
    """Return cost per image for the given quality and size.

    Single source of truth for all image cost lookups. Call sites should
    use this helper instead of IMAGE_COST_MAP.get().get() directly, so
    future pricing changes only need to update IMAGE_COST_MAP.

    Args:
        quality: Quality tier string ('low', 'medium', 'high').
        size: Size string ('1024x1024', '1024x1536', '1536x1024').
        fallback: Price to return if quality/size not in map (default: 0.034
                  — the medium square price as of GPT-Image-1.5 pricing).

    Returns:
        Cost per image as a float.
    """
    return IMAGE_COST_MAP.get(quality, {}).get(size, fallback)
```

The `fallback` parameter exists for future flexibility (e.g. a
Replicate provider with different pricing) but no current call site
overrides it. The default `0.034` is the canonical medium-square
GPT-Image-1.5 price — the same value that was hardcoded at all
three original call sites.

### prompts/services/image_providers/openai_provider.py — Call site 1 (lines 296-306)

**Before:**
```python
from prompts.constants import IMAGE_COST_MAP
return IMAGE_COST_MAP.get(quality, {}).get(size, 0.034)
```

**After:**
```python
from prompts.constants import get_image_cost
return get_image_cost(quality, size)
```

The local import pattern is maintained (consistent with the existing
style in this file, which uses function-level imports to avoid
circular dependencies between `prompts.services.image_providers` and
`prompts.constants`). The docstring was updated from "Delegates to
IMAGE_COST_MAP" to "Delegates to get_image_cost()".

### prompts/tasks.py — Call site 2 (lines 2663-2667)

**Before (3 lines):**
```python
cost = IMAGE_COST_MAP.get(
    image.quality or job.quality or 'medium', {}
).get(image.size or job.size, 0.034)
```

**After (5 lines):**
```python
from prompts.constants import get_image_cost
cost = get_image_cost(
    image.quality or job.quality or 'medium',
    image.size or job.size,
)
```

Because `tasks.py` is a 🔴 Critical-tier file at 3,719 lines, this
edit was performed using a Python string replacement script instead
of the `str_replace` tool, per the project's large-file editing
protocol. The quality/size resolution logic (preferring per-image
values with job-level fallback via `or` chains) is unchanged.

### prompts/views/bulk_generator_views.py — Call site 3 (lines 22, 82)

**Import (line 22) — before:**
```python
from prompts.constants import IMAGE_COST_MAP, SUPPORTED_IMAGE_SIZES, get_image_cost
```

**Import (line 22) — after (dead import removed):**
```python
from prompts.constants import SUPPORTED_IMAGE_SIZES, get_image_cost
```

The @code-reviewer agent flagged `IMAGE_COST_MAP` as no longer
referenced anywhere in the file after the call site was migrated.
`grep -n "IMAGE_COST_MAP" prompts/views/bulk_generator_views.py`
confirmed only the import line matched — zero usage sites. The dead
import was removed.

**Call site (line 82) — before:**
```python
cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)
```

**Call site (line 82) — after:**
```python
cost_per_image = get_image_cost(job.quality, job.size)
```

### prompts/tests/test_bulk_generator_job.py — New test class (lines 277-291)

```python
class GetImageCostHelperTests(TestCase):
    """153-J: Direct tests for the get_image_cost() helper in constants.py."""

    def test_known_quality_and_size(self):
        from prompts.constants import get_image_cost
        self.assertEqual(get_image_cost('medium', '1024x1024'), 0.034)

    def test_unknown_quality_returns_default_fallback(self):
        from prompts.constants import get_image_cost
        self.assertEqual(get_image_cost('unknown', '1024x1024'), 0.034)

    def test_custom_fallback_is_honoured(self):
        from prompts.constants import get_image_cost
        self.assertEqual(get_image_cost('unknown', '9999x9999', fallback=0.099), 0.099)
```

These three tests were added at the recommendation of the
@tdd-orchestrator agent (8.5/10), who noted that:

- The helper was only covered **indirectly** via existing
  `ImageCostMapTests` (9 exact-price assertions) and
  `GetCostPerImageDelegationTests` (6 delegation tests including
  the unknown-quality fallback)
- The custom `fallback` parameter was **completely untested**
- A pure-refactoring function should have a direct "contract" test
  to lock in its behaviour independently of the call-site tests

The tests run in 0.002 seconds.

### Verification Grep Outputs

```
=== 1. helper exists ===
prompts/constants.py:456:def get_image_cost(quality: str, ...

=== 2. all 3 call sites use get_image_cost ===
openai_provider.py:305: from prompts.constants import get_image_cost
openai_provider.py:306: return get_image_cost(quality, size)
tasks.py:2663:          from prompts.constants import get_image_cost
tasks.py:2664:          cost = get_image_cost(
views/bulk_generator_views.py:22: from prompts.constants import SUPPORTED_IMAGE_SIZES, get_image_cost
views/bulk_generator_views.py:82: cost_per_image = get_image_cost(job.quality, job.size)

=== 3. no bare .get().get() at call sites ===
(0 results — clean)

=== 4. python manage.py check ===
System check identified no issues (0 silenced).
```

---

## Section 4 — Issues Encountered and Resolved

**Issue 1 — Dead `IMAGE_COST_MAP` import in `bulk_generator_views.py`**

After migrating the call site at line 82 to `get_image_cost()`, the
`IMAGE_COST_MAP` name was no longer referenced anywhere in
`bulk_generator_views.py`. The import at line 22 became dead code.

**Root cause:** The spec instructed me to "keep `IMAGE_COST_MAP` in
the import — it may be used elsewhere in the views file." I followed
this initially, but the @code-reviewer agent checked and confirmed
zero usages remained.

**Fix applied:** Removed `IMAGE_COST_MAP` from the import line.
`grep -n "IMAGE_COST_MAP" prompts/views/bulk_generator_views.py`
now returns only the import line with `get_image_cost`, confirming
the dead import is gone.

**Issue 2 — Helper function had no direct unit tests**

The @tdd-orchestrator agent noted that while the helper was
exercised indirectly through 15+ existing price tests, the custom
`fallback` parameter path had zero coverage. A future change to the
fallback default could pass all existing tests while silently
breaking any call site that relies on the default value.

**Root cause:** The spec was written as a "pure refactoring" and
did not include test additions. However, the agent correctly argued
that a named public function with 3 parameters needs its own
contract test to lock in its behaviour independently of its callers.

**Fix applied:** Added `GetImageCostHelperTests` class with 3 test
methods covering known quality+size, unknown-quality default
fallback, and explicit custom fallback parameter. All pass.

---

## Section 5 — Remaining Issues

### Issue 1 — JS `I.COST_MAP` is still a hardcoded client-side copy

**Description:** `static/js/bulk-generator.js` (lines 95-101)
contains a hardcoded JavaScript object mirroring `IMAGE_COST_MAP`
from `prompts/constants.py`. When the Python constant changes, the
JS copy must be updated manually — and Session 153 proved this is
error-prone (153-C missed the JS copy entirely; 153-F caught it in
a Step 0 grep).

**Recommended fix:** Inject `IMAGE_COST_MAP` into the bulk generator
template context as a JSON variable:

```python
# In bulk_generator_views.py
import json
from prompts.constants import IMAGE_COST_MAP

context['cost_map_json'] = json.dumps(IMAGE_COST_MAP)
```

```html
<!-- In bulk_generator.html -->
<script>
    window.BulkGenInput.COST_MAP = {{ cost_map_json|safe }};
</script>
```

This makes the Python constant the single source of truth for both
backend and frontend. The JS `I.COST_MAP` initialisation code at
lines 95-101 would be removed entirely.

**Priority:** P2 — prevents a known drift pattern. Estimated scope:
1 small spec, 2 files (view + template), ~20 lines.

### Issue 2 — Redundant `IMAGE_COST_MAP` parameter passing

**Description:** `_apply_generation_result()` in `prompts/tasks.py`
(~line 2645) receives `IMAGE_COST_MAP` as a function parameter
passed down from `_run_generation_loop()`. Now that the helper uses
a local import inside the function body (`from prompts.constants
import get_image_cost`), the parameter is dead code.

**Recommended fix:** Remove `IMAGE_COST_MAP` from the function
signatures of `_apply_generation_result()` and its caller
`_run_generation_loop()`. Update the call sites to remove the
argument. This also removes the `IMAGE_COST_MAP` import at
`tasks.py:2915` which is currently used only for this parameter
passing.

**Priority:** P3 — cosmetic cleanup. Estimated scope: 1 small spec,
~15 lines across 2 functions in `tasks.py`.

### Issue 3 — Three separate `prefers-reduced-motion` CSS blocks

**Description:** `static/css/pages/bulk-generator-job.css` has three
separate `@media (prefers-reduced-motion: reduce)` blocks at lines
527, 1056, and 1197. `.loading-spinner { animation: none; }` appears
in both line 528 and line 1058 — a redundancy discovered during
Spec 153-I.

**Recommended fix:** Consolidate into a single block (or two
maximum — one for placeholder-specific rules, one for page-level
rules). Merge overlapping selectors.

**Priority:** P3 — CSS hygiene. Estimated scope: 10 minutes of
manual editing.

---

## Section 6 — Concerns and Areas for Improvement

### Concern 1 — Price literals are now scattered across 6+ files

Even with the helper, price-related values appear in:
- `prompts/constants.py` — `IMAGE_COST_MAP` (authoritative)
- `prompts/constants.py` — `get_image_cost()` fallback default
  `0.034` (must match medium square price)
- `static/js/bulk-generator.js` — `I.COST_MAP` (client-side copy)
- `static/js/bulk-generator.js` — `|| 0.034` fallback (line 846)
- `prompts/templates/prompts/bulk_generator.html` — `$0.009`
  detect-tier cost string
- `prompts/views/bulk_generator_views.py` — `$0.009` docstring
- 27+ test assertions with literal prices

**Impact:** The next pricing change (e.g. when Replicate models
arrive) must update all of these. The helper eliminates 3 of the
Python call sites but doesn't address the JS or template string
duplications.

**How to improve:** The JS template context injection (Section 5
Issue 1) is the single highest-leverage improvement. After that,
consider extracting the detect-tier cost string into a context
variable as well, so the template reads `{{ detect_tier_cost }}`
instead of a hardcoded `$0.009`.

### Concern 2 — `fallback` parameter creates a hidden contract

The `fallback=0.034` default in `get_image_cost()` is tied to the
current medium-square price in `IMAGE_COST_MAP`. If the map changes
and the fallback doesn't, calls with unknown quality/size will
return a stale price.

**How to improve:** Consider computing the fallback dynamically:
```python
_DEFAULT_FALLBACK = IMAGE_COST_MAP.get('medium', {}).get('1024x1024', 0.034)

def get_image_cost(quality, size, fallback=_DEFAULT_FALLBACK):
    ...
```
This binds the fallback to the map at import time, so updating the
map automatically updates the fallback. The current approach is
simpler but requires manual synchronisation.

---

## Section 7 — Agent Ratings

**Agent name mapping (Option B — authorised by developer for this
batch only):** `@tdd-coach` (spec name) → `@tdd-orchestrator`
(registry name). `@code-reviewer` used directly, no substitution.

The hard rule ("use exact agent names, do not substitute") stands
for future sessions. Spec templates should be updated to use
registry-correct names: `@tdd-orchestrator` instead of `@tdd-coach`.

| Round | Agent (registry name) | Spec name | Score | Key Findings | Acted On? |
|-------|-----------------------|-----------|-------|--------------|-----------|
| 1 | @code-reviewer | @code-reviewer | 8.5/10 | All 3 call sites migrated correctly; fallback 0.034 matches everywhere; **flagged dead `IMAGE_COST_MAP` import in `bulk_generator_views.py`** after migration left it unused | **Yes** — dead import removed |
| 1 | @tdd-orchestrator | @tdd-coach | 8.5/10 | Existing indirect coverage sufficient (15+ price tests) but the custom `fallback` parameter was completely untested; **recommended adding direct `GetImageCostHelperTests`** with known-quality, default-fallback, and custom-fallback cases | **Yes** — 3 direct tests added |
| **Average** | | | **8.5/10** | — | **Pass ≥8.0** |

Both agents' findings were material improvements to the spec. The
dead import would have failed a future linter audit; the missing
direct test left the `fallback` parameter's contract unverified.
Both were fixed before the full suite run and are included in the
commit.

**Total agents used for this spec:** 2 (matches spec minimum).

---

## Section 8 — Recommended Additional Agents

The spec required 2 agents and both were used. No additional agents
would have added material value for a pure Python refactoring that
introduces no new endpoints, no UI changes, and no security surface.

**@django-pro** could have been optionally added for a second
opinion on the local-import pattern in `tasks.py` (function-level
`from prompts.constants import get_image_cost` inside
`_apply_generation_result`), but this pattern is well-established in
the codebase and the @code-reviewer's 8.5/10 already covers it.

**@performance-engineer** could verify that the added function call
overhead (one extra stack frame per cost lookup) is negligible
compared to the network latency of the OpenAI API calls that
surround it. Not a practical concern — the helper body is a single
`dict.get().get()` chain, identical to the inlined version.

---

## Section 9 — How to Test

### Automated

```bash
# Run the 3 new direct helper tests
python manage.py test prompts.tests.test_bulk_generator_job.GetImageCostHelperTests -v 2
# Expected: 3 tests, 0 failures (0.002s)

# Run the existing price delegation tests (indirect coverage)
python manage.py test prompts.tests.test_bulk_generator_job.GetCostPerImageDelegationTests -v 2
# Expected: 6 tests, 0 failures

# Run the full IMAGE_COST_MAP assertion suite
python manage.py test prompts.tests.test_bulk_generator_job.ImageCostMapTests -v 2
# Expected: 12 tests, 0 failures

# Full suite
python manage.py test
# Expected: 1226 tests, 0 failures, 12 skipped

# System check
python manage.py check
# Expected: 0 issues
```

### Manual Verification

```bash
# Confirm no bare .get().get() at the 3 call sites
grep -n "IMAGE_COST_MAP\.get.*\.get" \
    prompts/services/image_providers/openai_provider.py \
    prompts/views/bulk_generator_views.py
# Expected: 0 results

# Confirm the helper is the only .get().get() on IMAGE_COST_MAP
grep -n "IMAGE_COST_MAP\.get.*\.get" prompts/constants.py
# Expected: 1 result (inside get_image_cost itself)

# Confirm dead import removed
grep -n "IMAGE_COST_MAP" prompts/views/bulk_generator_views.py
# Expected: 0 results
```

### Browser Verification (optional — no UI changes in this spec)

1. Navigate to `/tools/bulk-ai-generator/job/<uuid>/` as staff.
2. Confirm the cost estimate in the page header matches the
   expected value for the job's quality and size settings.
3. Change quality/size in a new job setup and confirm the sticky
   bar on the input page (`/tools/bulk-ai-generator/`) updates
   correctly.

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| `9744a5e` | `refactor(bulk-gen): introduce get_image_cost() helper, eliminate duplicated price lookups` |

**Files in commit (7):**

| File | Change |
|------|--------|
| `prompts/constants.py` | +19 lines (new `get_image_cost()` helper) |
| `prompts/services/image_providers/openai_provider.py` | 4 lines changed (import + call site) |
| `prompts/tasks.py` | 5 lines changed (local import + call site) |
| `prompts/views/bulk_generator_views.py` | 2 lines changed (import cleanup + call site) |
| `prompts/tests/test_bulk_generator_job.py` | +16 lines (3 new test methods) |
| `CC_SPEC_153_J_PRICE_HELPER.md` | +339 lines (spec file archived) |
| `docs/REPORT_153_J_PRICE_HELPER.md` | This report |

**Pre-commit hooks passed:** trim trailing whitespace, fix end of
files, check for merge conflicts, debug statements (python), flake8,
bandit.

**This commit is part of Session 153 Batch 2 (4 commits total):**

```
9744a5e refactor(bulk-gen): introduce get_image_cost() helper
cea6b27 fix(bulk-gen): cleanup batch — spinLoader a11y, billing hardening, stale comments
2ec36eb fix(bulk-gen): set needs_seo_review=True on bulk-created prompt pages
c391681 END OF SESSION DOCS UPDATE: session 153
```

---

## Section 11 — What to Work on Next

1. **JS template context injection (P2, highest priority)** —
   Replace the hardcoded `I.COST_MAP` in `bulk-generator.js` with a
   Django template variable injected from the view. This is the
   single highest-leverage follow-up: it prevents the exact JS↔Python
   drift pattern that Session 153-C/F experienced. Estimated: 1 small
   spec, 2 files (view + template), ~20 lines.

2. **Remove dead `IMAGE_COST_MAP` parameter (P3)** — Clean up the
   `IMAGE_COST_MAP` parameter from `_apply_generation_result()` and
   `_run_generation_loop()` in `tasks.py`. The parameter was used to
   pass the constant down the call chain, but `get_image_cost()` now
   imports it locally. Estimated: 1 small spec, ~15 lines.

3. **Dynamic fallback computation (P3)** — Change the `fallback`
   default in `get_image_cost()` from a hardcoded `0.034` to a
   computed `_DEFAULT_FALLBACK = IMAGE_COST_MAP['medium']['1024x1024']`
   so the fallback tracks the map automatically. Low urgency — only
   matters when pricing changes again.

4. **Consolidate CSS `prefers-reduced-motion` blocks (P3)** — Merge
   the three separate blocks in `bulk-generator-job.css` (lines 527,
   1056, 1197). The `.loading-spinner` rule is currently duplicated at
   lines 528 and 1058. Not urgent but reduces CSS maintenance burden.

═══════════════════════════════════════════════════════════════
