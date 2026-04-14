# REPORT: 154-N — Provider + JS Fixes

**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Five unrelated bug fixes to the bulk AI image generator, surfaced by
production testing after the Session 154 Phase REP launch (Replicate + xAI
providers). The issues ranged from an unhelpful generic NSFW error for
Flux 1.1 Pro to a regression that hid per-box Dimensions overrides for all
non-OpenAI models, to UX annoyances (generate button gated on prompt text,
aspect ratio reverting to 1:1 on every model switch). Prioritised now
because all five block a clean usability pass before the Phase SUB launch.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `ModelError` caught → user-friendly content-policy message | ✅ Met |
| Per-box Dimensions override always visible | ✅ Met |
| Quality override still hidden for non-quality models | ✅ Met (display:none) |
| Vision mode no longer auto-enables AI Influence | ✅ Met |
| Generate button active whenever boxes exist | ✅ Met |
| Aspect ratio maintained when switching models | ✅ Met |
| Default aspect ratio `2:3` for Replicate/xAI models | ✅ Met |
| `python manage.py check` → 0 issues | ✅ Met |

## Section 3 — Changes Made

### prompts/services/image_providers/replicate_provider.py
- Lines 231–246: Added `ModelError` handler at top of `_handle_exception`,
  BEFORE the existing `ReplicateError` isinstance check. Wrapped in
  `try/except ImportError` so older Replicate SDK versions that do not
  expose `ModelError` fall through gracefully.

### static/js/bulk-generator.js
- Lines ~333–336 (vision select change handler): Removed
  `dirCheckbox.checked = true` auto-enable block. Replaced with a
  comment stating user must check AI Influence themselves. Remaining
  vision behaviour (textarea disabled, source image `required`,
  placeholder swap, cost + generate button updates) unchanged.
- Lines 787–793 (`updateGenerateBtn`): Replaced
  `getPromptCount() === 0` guard with `hasBoxes` — counts
  `.bg-prompt-box` elements in `I.promptGrid`. Null-safe on
  `I.promptGrid`.
- Lines ~885–904 (`handleModelChange` aspect ratio init): After the
  existing `defaultAspect = opt.dataset.defaultAspect || '1:1'` line,
  added `currentAspect` IIFE (reads active button's `data-value`) and
  `preferredAspect` expression: current → '2:3' → defaultAspect.
  Overwrites `defaultAspect` with `preferredAspect` before the button
  rebuild block.
- Lines ~937–956 (per-box override sync block): Rewrote. Quality override
  still toggles `parentDiv.style.display` on `supportsQuality`. Dimensions
  override explicitly set to `style.display = ''` on every
  `handleModelChange` call, guaranteeing visibility regardless of prior
  state.

### prompts/management/commands/seed_generator_models.py
- Changed `default_aspect_ratio: '1:1'` → `'2:3'` for: Flux Schnell,
  Grok Imagine, Flux Dev, Flux 1.1 Pro, Nano Banana 2. GPT-Image-1.5
  entry unchanged (empty string — uses pixel sizes, not aspect ratios).
- Ran `python manage.py seed_generator_models` — 0 created, 6 updated.

## Section 4 — Issues Encountered and Resolved

**Issue:** First pass of Change 2 accidentally applied Spec O's
opacity+pointerEvents+disabled treatment to the per-box quality override.
**Root cause:** Awareness of Spec O's next-step change caused conflation.
**Fix applied:** Reverted per-box quality to Spec N's original
`display:none` approach. Spec O will then apply the opacity pattern in its
own commit. This keeps each spec's diff atomic.
**File:** `static/js/bulk-generator.js`, per-box override block.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `ModelError` is only imported inside the handler via
`try/except ImportError`. If Replicate ever splits the exception class
across a submodule (e.g. `replicate.exceptions.content`), the import path
could break silently.
**Impact:** Low — failure mode is a fallback to the generic handler.
**Recommended action:** Add a test that raises `ModelError` from the
Replicate SDK and asserts `error_type == 'content_policy'`.
Location: `prompts/tests/test_bulk_generation_tasks.py` or new
`test_replicate_provider.py`.

**Concern:** `preferredAspect` IIFE reads the DOM synchronously. If
`settingAspectRatio` is inside a display:none container at read time,
`.active` button still exists (display:none does not remove from DOM),
so this is safe — but worth noting for future refactors.
**Impact:** None currently.
**Recommended action:** None — document behaviour only.

## Section 7 — Agent Ratings

**Agent name substitutions (Option B authorised):**
- `@django-security` → `@backend-security-coder` (not used this spec)
- `@tdd-coach` → `@tdd-orchestrator` (used in Spec P)
- `@accessibility-expert` → `@ui-visual-validator` (not used this spec)

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.6/10 | Dimensions fix correct, vision decoupling clean, hasBoxes safe, preferredAspect IIFE reads DOM before rebuild (safe order) | N/A — verified correct |
| 1 | @code-reviewer | 9.0/10 | ModelError try/except guard correct; `ModelError` check BEFORE `ReplicateError` handles subclass case; all edge cases in preferredAspect handled; vision handler behaviour preserved | N/A — verified correct |
| **Average** | | **8.8/10** | | Pass ≥8.0 ✅ |

## Section 8 — Recommended Additional Agents

**@backend-security-coder:** Would have reviewed whether the user-visible
content-policy message leaks any exploitable signal (e.g. whether a
specific phrase triggered NSFW). Low risk since the message is static and
contains no prompt echo.

## Section 9 — How to Test

*(Filled in after full suite passes.)*

## Section 10 — Commits

*(Filled in after full suite passes.)*

## Section 11 — What to Work on Next

1. **Spec 154-O** — Disable (not hide) Quality and Character Reference
   Image on non-supporting models, and seed Grok + Nano Banana as
   supporting reference images.
2. **Spec 154-P** — Results page friendly model name + aspect ratio
   placeholder cards.
3. Consider a future test for the `ModelError` handler (Section 6).
