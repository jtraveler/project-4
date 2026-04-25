# Postmortem: tasks.py Modular Split (Session 168-E)

**Date written:** April 24, 2026
**Status:** Refactor abandoned — see "Outcome" below
**Source file:** `prompts/tasks.py` (3,822 lines, unchanged on origin/main as of this writing)
**Audit recommendation that triggered this work:** Session 168-A "top 5 refactor opportunities" — `tasks.py` ranked #2 by line count

**Outcome in one sentence:** the planned 8-submodule split into a `prompts/tasks/` package was attempted in two phases; Phase 1 (168-E-A) extracted 3 of 4 planned submodules successfully but had to inline a 4th (`b2_storage`) back into the package shim because Python's `@patch` mock semantics break across submodule boundaries — a constraint that fundamentally changes the cost/benefit of any further split.

**Why this matters:** anyone reading this who is considering a similar refactor (whether of `tasks.py` again, or any other heavily-mocked Python module) should understand the failure mode encountered here BEFORE drafting a spec. The work is not impossible — but it requires either accepting consumer test file changes as scope, or designing around mock propagation in a way 168-E-A did not.

The current state — `prompts/tasks.py` as a 3,822-line single file — is the correct state for now. Treat this postmortem as the gate any future revisit must pass through, not as an open invitation to retry.

---

## 1. Summary

The tasks.py refactor was attempted in two phases following the prep work documented in commit `aa13ed7`:

- **Phase 1 (168-E-A) — attempted, reverted before commit.** Targeted the 4 lowest-risk submodules from the prep analysis. Tests passed (1,364 OK), agents averaged 9.625/10, but the package's `__init__.py` ended up at 3,667 lines after one of the planned submodules had to be inlined back. The user reviewed the report and concluded the cost/benefit didn't justify shipping. The local working tree was reverted to `aa13ed7` and no commit referencing 168-E-A exists on origin.
- **Phase 2 (168-E-B) — never started.** Was to extract the higher-risk submodules (bulk generation, AI content, B2 rename) once Phase 1 stabilized.

The architectural finding behind the abandonment: Python's `unittest.mock.patch` decorator targets a single module's namespace. When functions move from `prompts.tasks` into `prompts.tasks.<submodule>`, sibling submodules that import them via `from .submodule import X` bind to the underlying function object at import time. The `@patch('prompts.tasks.X')` decorator at the test layer continues to patch the shim's namespace — but the call sites in sibling submodules no longer look there, so the mock never fires.

This is not a Python defect. It's correct mock semantics interacting with the project's existing test patterns (heavy reliance on `@patch('prompts.tasks.X')` decorators across ~30+ test files). The interaction is what made the split unworkable without out-of-scope test changes.

---

## 2. Context

### 2.1 What 168-A audit said

The Session 168-A repository audit (commit `5b7b26d`) ranked the top-five refactor candidates by line count:

1. `static/css/style.css` (4,479 lines) — split in 168-C
2. **`prompts/tasks.py` (3,822 lines)** — this work
3. `prompts/models.py` (3,517 lines) — split in 168-D
4. `prompts/admin.py` (2,459 lines) — split in 168-F
5. Docs archive pass — completed in 168-B

The pattern across the other four was: extract a directory, preserve the public import contract via `__init__.py` re-exports, run the test suite, agent-review, ship. Each of those four shipped successfully with ≥8.5/10 average agent scores and zero test count change.

The expectation going into 168-E was that the same playbook would work on tasks.py.

### 2.2 What 168-E-prep produced

The prep spec (committed as `aa13ed7`) was a read-only analysis covering:

- **49 functions** catalogued by name, line count, and called-from sites
- **15 module-level constants**
- **34 in-function lazy imports** (deliberately deferred to runtime to avoid circular imports)
- **41-name shim contract** that `prompts.tasks` exposes externally:
  - 7 Django-Q string-reference entry points (e.g. `'prompts.tasks.process_bulk_generation_job'`)
  - 12 public function/class names imported elsewhere in the codebase
  - 20 private (`_`-prefixed) functions that are nonetheless imported from at least one site
  - 9 module-level constants imported elsewhere
- **0 DB-stored Schedule rows** referencing `prompts.tasks.*` — confirmed via repo-wide grep against the Django-Q `Schedule` model
- **0 `schedule()` calls** in the codebase — Django-Q schedules are configured exclusively via the management command path

The prep also catalogued **14 split-blockers** with severity ranking, of which the highest-severity item was "Django-Q string references must continue to resolve" — a constraint addressable by re-exports in `__init__.py`.

The prep was substantive and accurate as far as it went. What it did not catalogue was the test layer's mock targets — see Section 7.

### 2.3 The tasks.py shim contract

The reason a directory split was even considered safe: Python lets a package's `__init__.py` re-export names so that `from prompts.tasks import process_bulk_generation_job` continues to work whether `process_bulk_generation_job` is defined in `__init__.py` or imported into it from a submodule. Django-Q's string-reference scheduling (which uses dotted paths to locate functions at runtime) resolves through the same `__init__.py` namespace.

So in principle, the shim contract is preserved as long as every name in the 41-name list is either defined in `__init__.py` or imported into it from a submodule. That principle holds.

What the principle does not address is what happens when **other submodules** in the same package import those names. A name re-exported by the shim still has its canonical residence in the submodule — and that's where call sites in sibling submodules end up bound.

### 2.4 Why the refactor was queued

The "why" was straightforward: at 3,822 lines, tasks.py is unwieldy to navigate. The other four 168-A targets shipped cleanly. There was no a priori reason to expect tasks.py to be different.

The expected outcome was: an 8-submodule package, each submodule between 200 and 800 lines, with `__init__.py` reduced to a thin re-export shim of perhaps 100-150 lines. Cognitive load when editing per-domain code drops because each domain is its own file.

The achieved outcome was different.

---

## 3. What was attempted

### 3.1 Phase split decision

The prep report recommended splitting the work into two phases:

- **168-E-A (low-risk)** — extract 4 submodules whose contents were already cohesive and whose call graphs were narrow:
  - `notifications.py` — `_fire_*` helpers for bell notifications
  - `nsfw_moderation.py` — vision moderation orchestration
  - `b2_storage.py` — `_download_source_image`, B2 upload helpers, size constants
  - `placeholders.py` — placeholder image generation utilities
  - Plus a transitional `_remainder.py` to hold everything not yet extracted, so `__init__.py` could be a clean orchestration layer ahead of Phase 2.

- **168-E-B (higher-risk)** — extract the more entangled domains:
  - `bulk_generation.py` — the bulk image generation orchestration
  - `ai_content.py` — title/description/tag generation via OpenAI
  - `b2_rename.py` — SEO file rename orchestration

The split rationale: the 168-E-A submodules had **few or no internal callers** within tasks.py beyond their domain. The 168-E-B submodules had many cross-domain callers and would have required more careful re-export plumbing.

### 3.2 168-E-A design

Per `CC_SPEC_168_E_A.md` (the local-only spec; not committed), the targeted structure was:

```
prompts/tasks/
├── __init__.py              # orchestration + re-export shim
├── notifications.py         # ~120 lines
├── nsfw_moderation.py       # ~140 lines
├── b2_storage.py            # ~170 lines
├── placeholders.py          # ~75 lines
└── _remainder.py            # everything not yet extracted (Phase 2 targets)
```

Each submodule would import from `prompts.tasks` peers via `from .b2_storage import _download_source_image` and similar. `__init__.py` would re-export every name on the 41-name shim contract.

### 3.3 Submodule boundary rationale

Quoting the prep report's cohesion analysis (paraphrased):

> The 4 low-risk submodules form natural cohesion clusters. Each set of functions has internal cross-references but few outbound references to the rest of tasks.py. They are good candidates for early extraction because moving them does not require rewiring the broader call graph.

This was correct as far as static call analysis goes. It did not anticipate the mock-binding interaction.

---

## 4. What worked

Three of the four planned submodules extracted cleanly:

### 4.1 `notifications.py` (~120 lines)

Contents: `_fire_bulk_gen_job_notification`, `_fire_bulk_gen_publish_notification`, `_fire_avatar_*` notifications, related helper utilities for assembling notification payloads.

Integration: `__init__.py` did `from .notifications import _fire_bulk_gen_job_notification, ...` and re-exported. Direct callers in the codebase (e.g. `prompts/views/...`) continued to do `from prompts.tasks import _fire_bulk_gen_job_notification`, which resolved through the shim namespace and worked unchanged.

**Why it worked:** zero `@patch('prompts.tasks._fire_*')` references in the test suite. The test layer wasn't trying to mock these helpers. They're used by integration tests that exercise the full notification flow, not by unit tests that need to stub them out.

### 4.2 `nsfw_moderation.py` (~140 lines)

Contents: vision moderation orchestration, severity-mapping helpers, fallback handling for moderation API failures.

Integration: same pattern — re-exported through `__init__.py`.

**Why it worked:** the few tests that exercise NSFW paths use `@patch('prompts.services.vision_moderation.VisionModerationService.moderate_image')` — patching the service layer below tasks.py. Tasks.py's wrapper functions weren't direct mock targets. Splitting them did not break any mock contract.

### 4.3 `placeholders.py` (~75 lines)

Contents: PIL-based placeholder image generation, color helpers, size validation for the placeholder path.

Integration: re-exported through `__init__.py`.

**Why it worked:** placeholder code is exercised in tests via the full image-generation pipeline. There is no `@patch('prompts.tasks.placeholder_*')` anywhere in the suite. Same as the previous two — the test layer wasn't trying to stub placeholder code at the tasks.py level.

### 4.4 The pattern

All three modules that worked share the same property: **zero or near-zero `@patch('prompts.tasks.X')` references in the test suite for any function or constant the submodule contained.** When tests don't depend on the function's residence in the `prompts.tasks` namespace, moving it is invisible to tests.

This was the implicit assumption the refactor playbook was built on — and it held for three of the four 168-E-A submodules. It did not hold for the fourth.

---

## 5. What broke (the central finding)

This is the most important section of the postmortem. The mechanism described here is the single reason 168-E-A was abandoned.

### 5.1 The b2_storage extraction

`b2_storage.py` was planned to contain:

- `_download_source_image(url, max_size_bytes=...)` — downloads an external image into memory with size guard, returns bytes
- `_upload_to_b2(...)` — wrapper around the B2 SDK with retry/timeout handling
- `MAX_IMAGE_SIZE` — a module-level constant capping download size
- A handful of related helpers

These functions are heavily used by both the bulk generation path and the upload path — they're how every external image gets pulled into B2 storage.

### 5.2 The progression of test failures

CC's execution log for 168-E-A shows four progressive test-suite runs as the b2_storage extraction was attempted:

| Run | Failures | Action taken between runs |
|-----|----------|---------------------------|
| 1   | 132      | Initial extraction with `from .b2_storage import _download_source_image` in sibling submodules |
| 2   | 91       | Inlined `_download_source_image` back into `__init__.py`; left the rest of `b2_storage` as a submodule |
| 3   | 30       | Inlined `MAX_IMAGE_SIZE` and `_upload_to_b2` back into `__init__.py` |
| 4   | 1        | Inlined the last B2 helper back; only an unrelated test remained failing |
| 5   | 0        | Fixed the unrelated test (a flake unrelated to the refactor) |

By Run 5, all 1,364 tests passed. The cost: `b2_storage.py` was effectively empty. Everything originally planned to live there had been inlined back into `__init__.py`. The package's `__init__.py` ended up at 3,667 lines.

### 5.3 The mechanism — why @patch failed to propagate

The diagnosis below explains every one of the 132 → 91 → 30 → 1 progression: each round inlined more of `b2_storage` into the shim namespace, restoring the binding the `@patch` decorators expected.

> Python's `@patch('prompts.tasks._download_source_image')` mock decorator replaces the name in the `prompts.tasks` module namespace. But once `_download_source_image` lives in `prompts.tasks.b2_storage`, the function's call sites in OTHER submodules (e.g., `_remainder.py` or `bulk_generation.py` after Phase 2) have already imported the function via `from .b2_storage import _download_source_image` at module load time. That import binds the name to the underlying function object at the CALL SITE's module namespace. The `@patch` decorator patches the SHIM's namespace (`prompts.tasks`), not the call site's namespace.
>
> Net effect: `@patch('prompts.tasks._download_source_image')` appears to succeed (no AttributeError) but the mock never fires because the actual function called at runtime is still bound to the original implementation in the call site's module.

This is correct, documented Python mock behavior. The standard library reference for `unittest.mock.patch` includes a section titled "where to patch" that describes exactly this: you patch the namespace where the name is **used**, not where it is **defined**. When `tasks.py` was a single file, those two namespaces were the same. Once it became a package, they diverged — and the test suite continued patching the namespace where the function was previously **used by tests**, which is no longer where production code calls it from.

### 5.4 Concrete example

A representative failure pattern from `prompts/tests/test_bulk_generation_tasks.py` (the file containing the largest concentration of mock-related failures during 168-E-A):

```python
@patch('prompts.tasks._download_source_image')
def test_bulk_image_download_size_guard(self, mock_download):
    mock_download.return_value = b'fake_bytes'
    # ... exercise a code path that internally calls _download_source_image ...
    self.assertEqual(mock_download.call_count, 1)
```

When `_download_source_image` lived in `prompts/tasks.py` (single file), this patch worked correctly:

1. `@patch('prompts.tasks._download_source_image')` → replaces the name in `prompts.tasks`'s namespace
2. Any production code that called `_download_source_image` from within `prompts.tasks` resolved to the patched name
3. `mock_download.call_count == 1` — pass

When `_download_source_image` was moved to `prompts/tasks/b2_storage.py`:

1. `__init__.py` did `from .b2_storage import _download_source_image` to satisfy the shim contract — fine, the name is in `prompts.tasks`'s namespace
2. Sibling submodule `_remainder.py` (which holds the production code that calls `_download_source_image`) also did `from .b2_storage import _download_source_image` — this binds `_remainder._download_source_image` to the underlying function object
3. `@patch('prompts.tasks._download_source_image')` → replaces the name in `prompts.tasks`'s namespace. But `_remainder._download_source_image` is unaffected — it points at the original function object, not at the name in `prompts.tasks`
4. Production code runs in `_remainder`. It calls `_download_source_image` and reaches the original function, NOT the mock
5. `mock_download.call_count == 0` — fail

A similar pattern affected `@patch('prompts.tasks.MAX_IMAGE_SIZE', 100)` style patches in the same test file: the constant was being patched in the shim's namespace, but the size check ran against the constant as imported into the call site's module.

### 5.5 Why CC's incremental fixes worked progressively

Each iteration in the 132 → 91 → 30 → 1 progression involved CC inlining one more piece of `b2_storage` back into `__init__.py`. Once a function or constant lived in `__init__.py` directly (rather than being imported from `b2_storage`), the call sites that used `from prompts.tasks import X` (or that already lived in `__init__.py`'s `_remainder` content) bound to `__init__.py`'s namespace — which is the same namespace `@patch('prompts.tasks.X')` modifies.

So progressive inlining restored progressive correctness. By Run 4, only one unrelated flake remained. The fix was complete — at the cost of `b2_storage.py` being functionally empty.

### 5.6 The honest reading

Three takeaways:

1. **The mock-propagation issue is not a CC failure or a prep failure.** It's a correct interaction between Python mock semantics and the project's test patterns. The interaction is invisible from a static call-graph analysis. The only way to detect it before execution is to enumerate `@patch()` targets across the test suite — and the prep did not do this.

2. **The fix was structurally correct, but it defeated the refactor's purpose.** Inlining `b2_storage` back into `__init__.py` made the tests pass. It also meant the file-size reduction was nearly nothing. The refactor was asking for a structural change; the only available path forward was to NOT make that structural change.

3. **The test suite's reliance on `@patch('prompts.tasks.X')` is itself a design choice.** A more typical pattern in modern Django codebases is to mock at the service layer (e.g. `@patch('prompts.services.b2.upload')`) rather than at the task-orchestration layer. The fact that PromptFinder's test suite mocks at the task-orchestration layer is a consequence of the task functions being the primary integration point. It is not wrong — but it is what makes the structural refactor expensive.

---

## 6. The 4% reduction problem

Concrete numbers from the 168-E-A end state:

- `prompts/tasks.py` before: 3,822 lines (single file)
- `prompts/tasks/__init__.py` after: 3,667 lines (after b2_storage inlining)
- Three extracted submodules: ~120 + ~140 + ~75 = ~335 lines, plus per-file headers and imports → roughly 337 total LOC
- Aggregate package size after: 3,667 + 337 = 4,004 lines

So the package as a whole was **larger** than the original single file by ~5%, while the file most contributors actually open and edit was **smaller** by only ~4%.

### 6.1 The stated goal vs. the achieved outcome

The stated goal of any large-file split is to reduce cognitive load for someone editing the file. That goal isn't met when the dominant content stays in a 3,667-line file simply renamed from `tasks.py` to `tasks/__init__.py`. The cognitive footprint when opening that file is essentially unchanged.

The marketing benefit — "tasks.py is now a package!" — is real but cosmetic. The substantive benefit — "I can edit this file without scrolling through unrelated domains" — is not delivered.

### 6.2 The decision

The user reviewed the 168-E-A completion report and concluded the cost-benefit didn't justify shipping. The ship/no-ship calculus they applied:

- **Cost of shipping:** carrying a 5%-larger aggregate code surface (more imports, more file boundaries, more chances for circular dependencies, more diff churn for unrelated future work) for a 4% reduction in the file most often opened.
- **Cost of NOT shipping:** the work is wasted, but the wasted work is bounded — the working tree can be reverted to `aa13ed7` and the only artifact is institutional knowledge.

The decision was not to ship. The local working tree was reverted. No commit referencing 168-E-A was created on origin. The branch state of origin/main remains exactly as it was after `aa13ed7`.

This decision is not negotiable in retrospect. It was the correct decision given the achieved outcome.

---

## 7. Why the prep report didn't predict this

The 168-E-prep report (commit `aa13ed7`) was substantive, accurate, and well-structured. Both reviewing agents (@code-reviewer and @architect-review) gave it 9.7+/10 for analytical depth and structural rigor.

It still did not predict the mock-propagation issue.

### 7.1 What the prep DID catalogue

- Every top-level function, class, constant, and signal handler
- Import sites within and outside the module
- Lazy import patterns (deliberately deferred imports inside function bodies for circular-import avoidance)
- The 41-name shim contract
- Django-Q registration paths
- Cohesion clusters for split candidates
- 14 split-blockers ranked by severity

### 7.2 What the prep DID NOT catalogue

- `@patch('prompts.tasks.X')` decorator targets across the test suite
- `mock.patch.object(prompts.tasks, ...)` and similar variant invocations
- Test-layer assumptions about which namespace a function is patched in
- Whether sibling-submodule imports would shadow the shim namespace from a mock-propagation standpoint

### 7.3 The investigation that would have caught it

A single `grep` across the test suite would have surfaced the scope of the mock-propagation problem:

```bash
grep -rn "@patch.*['\"]prompts\.tasks\." prompts/tests/ --include="*.py" | wc -l
```

A nontrivial count (and the actual count is in the dozens) is a leading indicator that any naïve split will run into `@patch` propagation issues. The prep should have run this grep, classified each patch target by which submodule it would move to, and flagged the ones whose tests would need updating.

### 7.4 This isn't a criticism of the prep

The constraint was not visible from import-graph data alone. The prep optimised for what could be statically derived from the production code. The test layer's mock targets are a separate dimension that the prep didn't sample.

The honest lesson is: **future prep specs for similar refactors should include an explicit `@patch` audit alongside the import-graph audit.** Both dimensions matter; either alone is insufficient.

---

## 8. Possible solutions for a future attempt

The list below enumerates strategies that could, in principle, unblock the split. Each comes with cost/benefit notes. None of them have been validated end-to-end. If this work is ever revisited, the next-attempt spec should pick one strategy and run a small POC (see Section 9.2) before committing to the full refactor.

### 8.1 Update test patch paths as scope

- **Approach:** every test that does `@patch('prompts.tasks.X')` changes to `@patch('prompts.tasks.submodule.X')` (or to the call site's namespace, depending on what the test is trying to verify). Variant invocations (`mock.patch.object`, `patch.multiple`, etc.) get analogous updates.
- **Estimated cost:** 30-40 test files touched, perhaps 100-200 patch-decorator changes across them.
- **Risk:** mock semantics are subtle. Patching the wrong namespace can yield false-positive tests that pass without actually exercising the mock. Each change should be reviewed individually — there is no safe blanket find-and-replace.
- **Benefit:** unblocks the full split. Aligns mock targets with the new module structure, which is also a long-term hygiene win.
- **Discipline note:** this violates the "no consumer changes" rule that the project's other splits (style.css, models.py, admin.py) respected. Acknowledged scope expansion. The next-attempt spec should call this out explicitly so the user can decide whether the scope expansion is acceptable before any code is touched.

### 8.2 Re-import-from-shim pattern in submodules

- **Approach:** every submodule, instead of doing `from .b2_storage import _download_source_image`, does `from prompts.tasks import _download_source_image`. This routes the name resolution through the shim's namespace, which `@patch('prompts.tasks.X')` would actually replace.
- **Risk:** introduces import cycles unless carefully ordered. Submodule load order during package initialization becomes load-bearing. May mask circular dependency issues at runtime, surfacing them only under specific test orderings.
- **Benefit:** preserves "no consumer changes" rule. Test files don't need updating.
- **Open question:** does this actually work for all mock patterns? Unverified. A small POC on 3-5 functions (Section 9.2) would validate before commitment. Specifically: what happens when `_remainder` does `from prompts.tasks import _download_source_image` while `prompts.tasks.__init__` is itself mid-initialization and hasn't yet executed its own `from .b2_storage import _download_source_image`?

### 8.3 Co-locate tests with submodules

- **Approach:** move test files for each domain alongside their submodule (e.g. `prompts/tasks/test_b2_storage.py` next to `prompts/tasks/b2_storage.py`). Patch paths use in-package relative references that always resolve locally.
- **Risk:** large test reorganization. Doesn't match the rest of the project's `prompts/tests/` convention. Test discovery configuration may need updating. Diff churn is enormous.
- **Benefit:** clear ownership. Mock targets always resolve to the local submodule.
- **Verdict:** probably out of scope. Too disruptive to test organization for a single refactor. Would only be worthwhile as part of a much broader test-architecture redesign.

### 8.4 Selective extraction (the "easy wins" subset)

- **Approach:** only extract submodules where ZERO tests patch any of their contents. From 168-E-A, this is exactly notifications, placeholders, and most of nsfw_moderation. Accept that the heavily-mocked half stays in `__init__.py` permanently or until 8.1/8.2 land.
- **Cost:** low — already partially done in 168-E-A. The work is already designed.
- **Benefit:** low — file size barely shrinks (~5%). The cognitive-load benefit doesn't really materialize because the dominant content stays put.
- **When justified:** if some other reason demands the package structure (e.g. adding a new task domain like social-share automation that would naturally live in its own file), then setting up the package now and adding a clean new submodule later is easier than splitting an even-larger monolith later.
- **Verdict:** marginal value if the goal is file-size reduction. Defensible only as a structural prep for unrelated future work.

### 8.5 Don't split. Reduce complexity instead

- **Approach:** instead of structural split, target the 6 `noqa: C901` complexity-flagged functions in tasks.py for extraction into helper functions or refactored control flow. This reduces the file's *complexity* (the actual day-to-day maintenance pain) without changing its *structure*.
- **Cost:** per-function refactor specs, each scoped to one function. Testable in isolation. Each spec can pass agent review on its own merits.
- **Benefit:** genuine maintainability gain. The thing that makes tasks.py hard to work in isn't the line count per se — it's that several of its functions have high cyclomatic complexity. Bringing those down would meaningfully improve the editing experience, and would do so without any structural risk.
- **Verdict:** probably the better long-term play. The goal "tasks.py is easier to work in" is more truthfully addressed by reducing function complexity than by splitting the file. The line-count metric was always a proxy for cognitive load, not a goal in itself.

### 8.6 Cost/benefit summary

| Strategy | Test-file changes | Risk | Benefit | When to choose |
|----------|-------------------|------|---------|----------------|
| 8.1 Update patch paths | Yes (~100-200 changes) | Medium | Full split unblocked | If user accepts scope expansion |
| 8.2 Re-import-from-shim | No | Medium-High (import cycles) | Full split, no consumer changes | If POC (9.2) confirms it works |
| 8.3 Co-locate tests | Yes (massive) | High | Clear local ownership | Only as part of broader test redesign |
| 8.4 Selective extraction | No | Low | Marginal (~5%) | If new task domain motivates package structure anyway |
| 8.5 Reduce complexity instead | No | Low | Genuine maintainability gain | Probably the right play if the actual problem is C901 complexity |

---

## 9. Investigations to perform before next attempt

If a future session decides to retry the tasks.py split, perform these investigations FIRST — analogous to a prep spec, but tighter scoped than 168-E-prep.

### 9.1 Comprehensive `@patch` audit

```bash
grep -rn "@patch.*['\"]prompts\.tasks\." prompts/tests/ \
    --include="*.py" | grep -v __pycache__
```

Catalog every patch target. Group by target function. For each:

- Which submodule would it move to under the planned split?
- Would the patch still resolve at the expected namespace?
- If not, is the answer 8.1 (update the patch) or 8.2 (re-route the import)?

Also include variant invocations:

```bash
grep -rn "patch\.object.*prompts\.tasks\|patch\.multiple.*prompts\.tasks" prompts/tests/ \
    --include="*.py"
```

Total count from this audit determines the test-file scope of any split attempt.

### 9.2 Mock propagation POC

Pick ONE function that is NOT patched anywhere in the test suite (e.g. one of the `_fire_*` helpers). Move it to a submodule. Run the full test suite. Confirm 0 failures.

Then pick ONE function that IS patched in at least 2 test files (e.g. `_download_source_image`). Move it to a submodule. Run the full test suite. Document exactly which tests fail and why.

If solution 8.2 is the chosen path, repeat the second half with the re-import-from-shim pattern in place. Document whether all mocks now propagate correctly. If yes, 8.2 is validated; if not, 8.2 is dead and only 8.1 remains.

This POC should take less than half a day and would have prevented all of 168-E-A.

### 9.3 Import cycle audit

If solution 8.2 is being considered, verify that doing `from prompts.tasks import X` inside a submodule does NOT create an import cycle when `prompts.tasks` itself is mid-loading.

Specific scenarios to test:

- Import `prompts.tasks` cold (no cached imports). Does package initialization complete?
- Import a submodule directly via `from prompts.tasks.b2_storage import _download_source_image`. Does it trigger `prompts.tasks.__init__` first? Does that succeed?
- Run a test in isolation that exercises a Django-Q string-reference path. Does the runtime resolution of `'prompts.tasks.process_bulk_generation_job'` succeed?

### 9.4 Estimate test-update scope honestly

If solution 8.1 is being considered, count the actual lines that need to change. Not just `@patch` decorators — `mock.patch.object(prompts.tasks, 'X')`, `with patch(...)` context managers, fixture-level patches, `unittest.mock.patch.dict` — all variants need updating.

Estimate review cost realistically. If the count is ~50, the scope expansion is manageable. If the count is ~500, it's a separate project and should be treated as such, not bundled into a structural refactor spec.

### 9.5 Define the success threshold

Before re-attempting, write down what would justify the work. Without a defined threshold, a re-attempt would be vulnerable to the same 4%-reduction trap — the work would proceed simply because someone started it, not because it was earning its weight.

Examples of legitimate thresholds:

- "tasks.py grows past 5,000 lines" — natural-growth-driven trigger
- "More than 2 developers complain about navigation in a 3-month window" — felt-pain-driven trigger
- "A new task domain (e.g. social-share automation) requires ~500 lines and would naturally live in its own file" — new-feature-driven trigger
- "We commit to fixing the 6 C901 complexity-flagged functions anyway, and a directory structure makes that work easier" — bundled-with-other-work trigger
- "We accept solution 8.1's scope expansion (test patch paths) as part of normal scope, not a special case" — discipline-policy-driven trigger

Without one of these (or a comparably specific trigger) holding true at the moment a re-attempt is contemplated, the re-attempt should not happen.

---

## 10. Hard threshold for "next time"

This section reproduces 9.5's bullet list as a top-level heading so a future Claude or developer reading this postmortem can hit it within 30 seconds and ask: **"Does any of this apply right now?"**

A future attempt at the tasks.py split is justified only if at least ONE of the following conditions is true at the time the spec is being drafted:

- **`tasks.py` has grown past 5,000 lines.** Single-file growth past this point makes navigation friction high enough to motivate a split even at marginal reduction.
- **Two or more developers have raised tasks.py navigation as friction in a defined recent window** (e.g. a 3-month window). Felt pain from real users justifies engineering investment.
- **A new task domain is being added that would naturally live in its own file.** Adding a 500-line `social_share.py` module is cleaner than appending another 500 lines to tasks.py. In this case, the package structure is set up not to reduce existing line count but to provide a home for new code.
- **The 6 `noqa: C901` complexity-flagged functions are scheduled for refactor anyway.** A directory structure makes per-function refactor specs cleaner. Bundling the structural change with the complexity reduction earns more total value.
- **The next-attempt spec explicitly accepts solution 8.1 (test patch path updates) as in-scope.** The user has reviewed the estimated test-file-change count from investigation 9.4 and approved it.

If none of the threshold conditions are met, do not re-attempt. The current 3,822-line file is acceptable.

---

## Appendix A — Document trail

- `5b7b26d` — 168-A audit (the original ranking that put tasks.py at #2)
- `aa13ed7` — 168-E-prep, on origin/main (the read-only analysis this postmortem references)
- 168-E-A — local-only attempt, never committed; reverted before push
- This postmortem (`docs/POSTMORTEM_168_E_TASKS_SPLIT.md`) — written April 24, 2026 in Session 168-E-postmortem

## Appendix B — Other splits this postmortem does NOT apply to

Past successful splits that are NOT affected by the mock-propagation issue described here:

- **`static/css/style.css` → `static/css/partials/`** (Session 168-C). CSS has no mock layer. The split was byte-identical and shipped cleanly.
- **`prompts/models.py` → `prompts/models/`** (Session 168-D). Worked because the test suite mocks model methods (e.g. `@patch.object(MyModel, 'save')`) rather than module-level patches. Submodule re-exports through `__init__.py` preserved every external import without breaking any mock.
- **`prompts/admin.py` → `prompts/admin/`** (Session 168-F). Worked for similar reasons — admin classes are tested via `@patch.object(MyAdmin, 'method')` patterns, not via module-namespace patches.

The pattern across all three of those: tests targeted **objects** (model classes, admin classes, CSS files), not **module-level functions and constants**. tasks.py's tests target module-level functions and constants. That's the difference.

Future refactors of files in the codebase that use heavy `@patch('module.X')` patterns should reference this postmortem before drafting a spec. Files in this category include (but are not limited to):

- `prompts/tasks.py` (this file)
- `prompts/services/bulk_generation.py` (heavily mocked at function level)
- `prompts/services/content_generation.py` (similar pattern)

The mock-propagation constraint is not unique to tasks.py. It's a general property of the project's test-patching style.

---

**END OF POSTMORTEM**
