# REPORT 154-Q — Provider Fixes Batch 2 (Detailed)

**Session:** 154 (Batch 5)
**Spec:** `CC_SPEC_154_Q_PROVIDER_FIXES2`
**Date:** April 2026
**Commits:** `b7f54e6` (implementation + tests), `b0188f0` (report hash fill-in)
**Test delta:** 1233 → 1249 passing (+16), 12 skipped, 0 failures
**Files changed:** 3 source + 2 new test files
**Agent rounds:** 2 (Round 1 avg 7.3/10 → Round 2 avg 8.7/10)
**Status:** Complete and merged to `main`

---

## 1. Overview

Spec 154-Q is a post-rollout bug-fix batch that hardens the Phase REP provider layer shipped in Session 154 Batch 3 (`GeneratorModel` registry + Replicate + xAI providers). Production smoke-testing surfaced three distinct regressions: every Grok Imagine job was returning HTTP 400 from xAI; every Flux Schnell / Flux Dev job was failing at the HTTPS URL guard; and the disabled-state UX introduced by spec 154-O gave no cursor feedback on hover, leaving users unsure which controls were actually interactive.

All three issues were remediated in a single commit, backed by 16 new unit tests, and validated through two rounds of agent review. None of the three bugs had been caught by the existing suite because they live at the provider-SDK boundary (xAI HTTP contract, Replicate SDK return-type coercion) and in pure CSS cursor behaviour — surfaces the existing Python tests did not exercise.

## 2. Expectations

The spec was scoped as a targeted bug-fix batch, not a feature. The success criteria were:

- Grok Imagine jobs produce images on the job page without HTTP 400.
- Flux Schnell and Flux Dev jobs produce images without tripping the HTTPS validation guard.
- Disabled form groups (fields suppressed by spec 154-O) display `cursor: not-allowed` on hover across both the group itself and its descendant controls.
- No regressions in the 1233-test baseline.
- At least 3 agents clearing 8.0/10; average across all agents at 8.5+/10.

All five criteria were met.

## 3. Improvements Done

### 3.1 Grok Imagine — xAI dimension contract

`prompts/services/image_providers/xai_provider.py` was rewritten around a hard-coded `_XAI_VALID_SIZES` frozenset of the three sizes xAI Aurora accepts (`1024x1024`, `1792x1024`, `1024x1792`). The prior `_ASPECT_TO_DIMENSIONS` dict mapped nine aspect ratios to bespoke pixel sizes — five of which xAI rejects outright. The new mapping collapses all nine ratios into those three valid sizes by orientation (square / landscape / portrait).

`_resolve_dimensions` now:

1. Accepts either an aspect string (`"16:9"`) or a pixel string (`"1344x768"`).
2. For pixel strings, validates membership in `_XAI_VALID_SIZES` and snaps to the nearest valid size by orientation if not a member.
3. Falls back to `1024x1024` on unparseable input.

This is defence in depth — the `GeneratorModel.supported_aspect_ratios` seed should already prevent invalid ratios reaching the provider, but the snap-to-nearest fallback guarantees no 400s even under seed drift.

### 3.2 Flux — Replicate FileOutput coercion

`prompts/services/image_providers/replicate_provider.py` now extracts the URL with a `hasattr(first_output, 'url')` guard:

```python
if hasattr(first_output, 'url'):
    image_url = str(first_output.url)
else:
    image_url = str(first_output)
```

The bug was that newer Replicate SDK versions return a `FileOutput` object whose `__str__` yields `"FileOutput(url='https://...')"` rather than the raw URL. The downstream `image_url.startswith('https://')` guard then rejected the entire response. The `hasattr` guard is version-agnostic: old SDKs returning a plain string still work via the fallback branch.

### 3.3 Disabled-state cursor

`static/css/pages/bulk-generator.css` gained an attribute-selector rule targeting the inline style set by 154-O:

```css
.bg-setting-group[style*="pointer-events: none"],
.bg-setting-group[style*="pointer-events: none"] * {
    cursor: not-allowed;
}
```

The descendant selector is needed because `pointer-events: none` cascades but `cursor` does not — without the `*` selector, only the group itself reports the disabled cursor while inputs and labels inside it fall back to their default cursor.

### 3.4 Tests

Two new test files:

- `prompts/tests/test_xai_provider.py` (14 tests) — covers valid aspect mapping, pixel-string passthrough, snap-to-nearest for all three orientations, unparseable input fallback, and `_XAI_VALID_SIZES` membership invariants.
- `prompts/tests/test_replicate_provider.py` (2 tests) — covers both the `FileOutput`-with-`.url` branch and the legacy plain-string branch via a lightweight stub.

## 4. Issues Encountered and Resolved

**flake8 E241 on aligned dict.** The first draft of `_ASPECT_TO_DIMENSIONS` used extra spacing to visually align the values. flake8 rejected this with E241 ("multiple spaces after ':'"). Resolved by collapsing to single-space format and using trailing comments for visual grouping.

**Round 1 agent scores below threshold.** Three of six agents scored below 8.0 on the first review pass: `@frontend-developer` (6.0), `@tdd-orchestrator` (6.0), `@architect-review` (6.5). Three targeted follow-up fixes were applied:

- `_resolve_dimensions` nested ternary flattened to explicit `if/elif/else` (readability — `@python-pro`, `@code-reviewer`).
- Redundant no-space CSS selector variant (`[style*="pointer-events:none"]`) dropped (`@frontend-developer` noted CSS engines normalise whitespace in attribute-value matching for this case, so the second selector was dead weight).
- 16 unit tests added where the first pass had zero (`@tdd-orchestrator`).

Round 2 avg rose to 8.7/10 with all six agents clearing 8.0.

**Pre-existing architectural smell surfaced.** `@architect-review` flagged that `BulkGenerationJob.size` stores pixel strings (`"1024x1024"`) for OpenAI jobs but aspect strings (`"1:1"`) for Replicate/xAI jobs — a polymorphic column that the provider layer has to sniff on every call. The user explicitly deferred this to a separate architectural spec: it is not a bug, it predates 154-Q, and folding it into a bug-fix batch would have inflated scope and risk.

## 5. Remaining Issues with Solutions

None block production. The following are deferred with explicit rationale:

| Issue | Solution | Owner |
|---|---|---|
| `BulkGenerationJob.size` type ambiguity | Split into `size_pixels` + `aspect_ratio` columns, or add a `size_format` discriminator. Requires migration + provider-layer refactor. | New architectural spec |
| Silent snap-to-nearest in xAI provider | Restrict `GeneratorModel.supported_aspect_ratios` seed to the 3 genuine Aurora ratios for xAI models so the snap code is defensive-only, and log a `logger.warning` when it triggers. | Future UX spec |
| BEM refactor of disabled-state hook | Replace `[style*="pointer-events: none"]` attribute selector with an explicit `.bg-setting-group--disabled` class toggled by 154-O's JS. Cleaner specificity, easier to grep. | Future cleanup |

## 6. Concerns and Areas for Improvement

The following were raised by agents but deliberately not fixed in this spec. Each has a specific actionable recommendation so a later session can pick them up without re-discovery.

**`_XAI_VALID_SIZES` as frozenset of strings round-trips through f-strings.** `@python-pro` noted the provider repeatedly does `f"{w}x{h}"` and checks membership. Cleaner: store as `frozenset[tuple[int, int]]` — `frozenset({(1024, 1024), (1792, 1024), (1024, 1792)})` — and compare tuples directly. Eliminates string formatting in the hot path. Est. 10-line change in `xai_provider.py`.

**Dead `TypeError` branch in `_resolve_dimensions`.** After the `'x' in size` guard, the subsequent `int(w)` / `int(h)` can only raise `ValueError`, not `TypeError`. `@python-pro` recommends narrowing the `except` clause to `ValueError` alone. One-line change.

**CSS cursor rule specificity.** The descendant selector `.bg-setting-group[style*="..."] *` has specificity `(0,1,1)` and could theoretically lose to a more-specific child rule declaring `cursor: pointer`. `@frontend-developer` audited the current stylesheet and found no conflicts, but if one is added later it would silently break the disabled cursor. Recommendation: bump specificity by doubling the class (`.bg-setting-group.bg-setting-group[...] *`) or — preferably — adopt the BEM refactor above.

**Safari ignores `cursor` on `<select>` elements.** Known WebKit limitation, cosmetic only. No fix possible in pure CSS. Recommendation: accept and document.

**Replicate fallback path has no telemetry.** `@code-reviewer` noted that if a future Replicate SDK regresses and `hasattr(first_output, 'url')` becomes false in production, the fallback works silently and we lose signal. Recommendation: add `logger.warning("Replicate FileOutput lacked .url attribute; using str() fallback")` in the `else` branch so regressions show up in Heroku logs.

**No automated browser test for CSS cursor.** `@tdd-orchestrator` flagged this as the one uncovered regression surface. Playwright-style end-to-end tests are outside the current test infrastructure. Recommendation: add a visual regression test when (and if) browser automation is introduced — do not add a browser dep just for this rule.

**Unbounded integer parse in `_resolve_dimensions`.** `int("999999999999")` succeeds and the resulting arithmetic is safe, but wasteful. `@backend-security-coder` rated this as defensive-only. Recommendation: cap inputs at `int(w) < 10000` before comparison — one-line guard.

## 7. Detailed Agent Ratings

Six agents were run in each of two rounds, per the Session 154 Batch 5 run-instructions mandate on EXACT agent names (no substitutions without documentation).

| Agent | Round 1 | Round 2 | Notes |
|---|---|---|---|
| `@backend-security-coder` | 9.0 | 9.3 | Substitution for `@django-security` (Option B, pre-approved) |
| `@code-reviewer` | 9.0 | 9.5 | Highest R2 score; flagged Replicate telemetry gap |
| `@frontend-developer` | 6.0 | 8.5 | R1 sub-threshold — driven by redundant CSS selector + specificity concern |
| `@python-pro` | 7.5 | 8.2 | R1 sub-threshold — driven by nested ternary and broad `except` |
| `@tdd-orchestrator` | 6.0 | 8.5 | Substitution for `@tdd-coach` (Option B, pre-approved) — R1 sub-threshold driven by zero tests |
| `@architect-review` | 6.5 | 8.2 | R1 sub-threshold — driven by `BulkGenerationJob.size` smell (deferred) |
| **Average** | **7.33** | **8.70** | All six cleared 8.0 in R2 |

`@ui-visual-validator` (Option B substitution for `@accessibility-expert`) was not invoked — the change has no keyboard, focus, or ARIA surface. The `cursor: not-allowed` addition is purely presentational on already-disabled controls.

Both rounds were full re-runs on the complete diff, not projected or partial scores — per the CLAUDE.md Agent Rating Protocol.

## 8. Additional Agents Recommended for Future Use

- `@sdk-compatibility-auditor` (if it exists in the registry) for the Replicate `FileOutput` class of bug. The root cause was an SDK return-type change between minor versions; a focused agent on pinned-dependency vs installed-dependency drift would have caught this pre-production.
- `@contract-test-author` for the xAI 400 class of bug. The fix is correct but could be strengthened by contract tests that assert every `GeneratorModel.supported_aspect_ratios` entry for a given provider resolves to a provider-accepted dimension — a property-based test rather than the enumerated tests shipped here.
- `@observability-reviewer` to catch the missing `logger.warning` on the Replicate fallback branch proactively, rather than as a code-review callout.

## 9. How to Test

### Automated

```bash
python manage.py test prompts.tests.test_xai_provider
python manage.py test prompts.tests.test_replicate_provider
python manage.py test   # full suite, expect 1249 passing / 12 skipped
```

All three should pass with no new skips and no new warnings.

### Manual — Grok Imagine (xAI)

1. Navigate to `/tools/bulk-ai-generator/` as a staff user.
2. Select model **Grok Imagine**.
3. Choose any aspect ratio including the previously-broken ones (16:9, 9:16, 4:3, 3:4).
4. Enter a benign test prompt and generate 1 image.
5. Expected: image delivered on job page with no HTTP 400. Generated image will be square for 1:1 and near-ratios, landscape 1792x1024 for 16:9 / 4:3, portrait 1024x1792 for 9:16 / 3:4.

### Manual — Flux Schnell / Flux Dev (Replicate)

1. Select model **Flux Schnell** (fastest — ~2s).
2. Generate 1 image with any prompt.
3. Expected: image renders in gallery. Check Heroku logs for no `ValueError: image_url must start with https://`.
4. Repeat for **Flux Dev** to confirm the fix covers both Replicate models using the same code path.

### Manual — Disabled-state cursor

1. Select a model whose `supported_features` excludes character-reference image (e.g. Flux Schnell).
2. Hover over the disabled Character Reference Image group.
3. Expected: `not-allowed` cursor on the group background AND on the file input, label text, and any helper text inside it.
4. Select a model that supports it (e.g. GPT-Image-1.5) and verify the cursor returns to default / pointer on the same elements.

## 10. What to Work on Next (Ordered)

1. **`BulkGenerationJob.size` split.** Architectural spec, migration, provider-layer update. Unblocks the snap-to-nearest cleanup and removes a class of latent polymorphism bugs.
2. **Restrict xAI `supported_aspect_ratios` seed to 3 ratios + warn on snap.** Small data + one-line log — makes the snap code defensive-only and surfaces future seed drift.
3. **Replicate fallback telemetry.** One `logger.warning` line, no tests needed. Buys regression visibility for near-zero effort.
4. **`_XAI_VALID_SIZES` tuple refactor + `except ValueError` narrowing.** Single PR, small diff, clean-up hygiene.
5. **BEM refactor of disabled-state CSS hook.** Coordinate with 154-O's JS to toggle a class rather than inline style. Improves specificity hygiene and grep-ability.
6. **Contract tests for provider aspect ratios.** Assert every seeded `supported_aspect_ratios` entry resolves to a provider-accepted dimension. Catches the 154-Q class of bug at seed-time rather than job-time.
7. **Resume main Session 154 arc** — Phase SUB (Stripe + credit enforcement) is the next large feature per CLAUDE.md.

## 11. Commits

| Commit | Scope | Files | Description |
|---|---|---|---|
| `b7f54e6` | fix | 5 | `fix(providers): Grok 400, Flux FileOutput URL, disabled cursor + 16 tests` — the implementation commit. Contains xai_provider.py rewrite, replicate_provider.py URL guard, bulk-generator.css cursor rule, and both new test files. |
| `b0188f0` | docs | 1 | `docs(report): fill commit hash for 154-Q report` — post-commit hash fill-in for this report file. |

---

**Report drafted with:** @docs-architect
**File paths referenced:** `/prompts/services/image_providers/xai_provider.py`, `/prompts/services/image_providers/replicate_provider.py`, `/static/css/pages/bulk-generator.css`, `/prompts/tests/test_xai_provider.py`, `/prompts/tests/test_replicate_provider.py`
