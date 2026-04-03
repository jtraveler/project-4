# REPORT_152_A_VISION_QUALITY_AND_PROGRESS.md
# Vision Quality + Two-Step Direction + Progress Bar Fix

**Spec:** CC_SPEC_152_A_VISION_QUALITY_AND_PROGRESS.md
**Session:** 152-A
**Date:** April 3, 2026

---

## Section 1 — Overview

Three issues in the bulk AI image generator's Vision pipeline and progress bar were fixed, all in `prompts/views/bulk_generator_views.py`:

1. **Progress bar 0% on refresh** — the query only counted `status='completed'` images. During active generation, images are in `status='generating'` so the count was always 0. Fixed to count both states.

2. **Vision detail:low losing spatial accuracy** — at `detail: 'low'`, OpenAI compresses the source image to ~85x85 pixels, making it impossible for the Vision model to determine spatial positions, background people, or fine details. Upgraded to `detail: 'high'` (~$0.009/call vs $0.003).

3. **Direction corrupting Vision analysis** — passing direction INTO the Vision call caused the model to reinterpret rather than describe the image, changing ethnicity, positions, and composition. Fixed with a two-step approach: Vision describes purely, then direction is applied as a text edit via the existing Step 1.5 pipeline.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `detail` is `'high'` not `'low'` | ✅ Met |
| Direction NOT passed into Vision analysis call | ✅ Met |
| Progress bar counts `generating` + `completed` | ✅ Met |
| Vision direction NOT silently dropped | ✅ Met — routed via `combined_directions` to Step 1.5 |
| Text box direction not regressed | ✅ Met — same values, different routing |

---

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py

**Step 1 — Progress bar query (lines 97-102):**
- Changed `job.images.filter(status='completed').count()` to `job.images.filter(status__in=['completed', 'generating']).count()`
- Images in `generating` state have active API calls and will resolve shortly

**Step 2 — Vision detail (line 828):**
- Changed `'detail': 'low'` to `'detail': 'high'`
- Comment updated to explain spatial accuracy rationale

**Step 3 — Direction removal from Vision (lines 762-768, 833-835):**
- `direction_block` is now unconditionally `''` (old conditional block removed)
- `+ direction_block` removed from user message
- Docstring updated to document `direction` param as intentionally ignored

**Step 4 — Two-step direction routing (lines 950-954, 978-993):**
- Vision call now passes `''` as direction instead of `vision_directions[i]`
- Removed `if vision_enabled[i]: continue` guard from Step 1.5
- Added `combined_directions` list that merges `vision_directions` (for Vision boxes) and `text_directions` (for text boxes)
- Step 1.5 loop iterates `combined_directions` instead of `text_directions`

### Step 5 Verification Grep Outputs

**Grep 1 — Progress bar counts generating + completed:**
```
101:        status__in=['completed', 'generating']
```

**Grep 2 — detail is now high:**
```
828:                    'detail': 'high',  # High detail preserves spatial accuracy for faithful recreation
```

**Grep 3 — direction_block always empty:**
```
768:        direction_block = ''
```
No `Incorporate` matches found — old conditional block fully removed.

**Grep 4 — Vision call passes empty string:**
```
700:def _generate_prompt_from_image(
952:        generated = _generate_prompt_from_image(
```
Line 952-954 shows `src_url, '', platform_api_key` — empty string confirmed.

**Grep 5 — Vision exclusion removed:**
```
No matches found
```
No `vision_enabled[i]...continue` or `Only apply.*non-Vision` — guard fully removed.

**Grep 6 — combined_directions used:**
```
981:    combined_directions = []
985:            combined_directions.append(
989:            combined_directions.append(
994:    for i, direction in enumerate(combined_directions):
```

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Docstring for `_generate_prompt_from_image` still described `direction` as "Optional user guidance" after direction was decoupled.
**Root cause:** Spec did not include docstring update.
**Fix applied:** Updated docstring to state direction is kept for backwards compatibility but intentionally ignored, and that direction is applied in Step 1.5.
**File:** `prompts/views/bulk_generator_views.py:706-718`

---

## Section 5 — Remaining Issues

**Issue:** CLAUDE.md still states Vision costs ~$0.003/call (`detail: 'low'`). Now stale with `detail: 'high'` (~$0.009-0.015/call).
**Recommended fix:** Update Session 149 notes in CLAUDE.md to reflect new cost.
**Priority:** P3
**Reason not resolved:** Documentation-only, out of scope for this code spec.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `direction_block` local variable (line 768) is now dead code — assigned `''` but never read since `+ direction_block` was removed from the user message.
**Impact:** Low — cosmetic dead code, no functional issue.
**Recommended action:** Remove `direction_block = ''` and its comment block entirely in a future cleanup pass. The comment explaining the architectural decision could be moved to the function docstring (where it was just added).

**Concern:** Bounds guards in `combined_directions` loop (`i < len(vision_enabled)`, `i < len(vision_directions)`) are unreachable because both lists are already padded to `len(prompts)` at lines 916-921.
**Impact:** None — defensive but dead code.
**Recommended action:** P3 cleanup — remove guards or add comment noting they're defensive.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.8/10 | Routing correct; dead bounds guards in combined_directions | No — P3 cosmetic |
| 1 | @python-pro | 8.5/10 | Direction fully decoupled; docstring stale | Yes — docstring updated |
| 1 | @code-reviewer | 9.0/10 | No direction dropped; dead direction_block var; CLAUDE.md cost stale | Partially — docstring fixed, CLAUDE.md noted as P3 |
| **Average** | | **8.77/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The changes are Python-only with no template, JS, or CSS modifications.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=1
# Result: Ran 1213 tests — OK (skipped=12), 0 failures
```

**Manual browser checks:**

1. **Progress bar** — Start generation → let 1 image begin generating (not complete) → refresh page → bar should show >0% immediately

2. **Vision quality (no direction)** — Paste family painting → Vision="Yes", no direction → Generate → verify spatial accuracy (positions, background people, clothing detail)

3. **Vision + direction (two-step)** — Same source image → Vision="Yes" → Add Direction: "Futuristic. Inspired by Tomorrowland." → Generate → verify direction applied without corrupting ethnicity/composition

4. **Text box direction (regression)** — Write text prompt → Add AI Direction → Generate → confirm direction still applies correctly

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 57d0784 | fix(bulk-gen): Vision detail high, two-step direction, progress bar generating state |

---

## Section 11 — What to Work on Next

1. **Test Vision quality in production** — generate with `detail: 'high'` and compare spatial accuracy against previous `detail: 'low'` outputs
2. **Test two-step direction** — verify direction edits don't over-rewrite the Vision description
3. **Update CLAUDE.md** — correct Vision cost from $0.003 to ~$0.009-0.015 per call
4. **Clean up dead code** — remove `direction_block` variable and unreachable bounds guards (P3)

---

**END OF REPORT**
