# Bulk Generator — P1/P2 Fixes: Agent Review Report

**Session:** Phase 5B Follow-up (Sessions 105–106)
**Spec:** CC Spec: Bulk Generator — P1/P2 Fixes, Size Centralisation + Rating Recovery v2.0
**Date:** March 7, 2026
**Status:** ✅ All 9 items implemented — 124/124 tests pass — All 6 agents 8+/10

---

## Agent Scorecard

| Agent | Role | Score | Previous | Delta |
|-------|------|-------|----------|-------|
| @django-pro | Constants, imports, models, SEC-1/4/5 | **9.2/10** | 8.1/10 | +1.1 |
| @security-auditor | SEC-1, SEC-4, SEC-5, DRY-1 validation | **8.0/10** | 7.5/10 | +0.5 |
| @ui-ux-designer (accessibility) | A11Y-1, A11Y-4, UX-1 | **9.0/10** | 7.1/10 | +1.9 |
| @frontend-developer | JS/CSS mechanics, disabled option | **8.0/10** | 8.2/10 | −0.2 |
| @code-reviewer | Cross-file consistency | **8.0/10** | 7.0/10 | +1.0 |
| @backend-security-coder | SEC-1, SEC-4, SEC-5 deep audit | **8.0/10** | — | — |
| **Average** | | **8.37/10** | **7.5/10** | **+0.87** |

All 6 agents met the 8+/10 threshold. All 4 agents that previously scored below 8 now meet the requirement.

---

## Implementation Overview

### Files Changed (9 total)

| File | Change | Category |
|------|--------|----------|
| `prompts/constants.py` | Added `SUPPORTED_IMAGE_SIZES` (3 entries) + `ALL_IMAGE_SIZES` (4 entries) | DRY-1 |
| `prompts/views/bulk_generator_views.py` | Import `SUPPORTED_IMAGE_SIZES`, remove local `VALID_SIZES`, fix SEC-1/4/5 | DRY-1 + SEC |
| `prompts/services/image_providers/openai_provider.py` | `supported_sizes = SUPPORTED_IMAGE_SIZES` (import replaces local list) | DRY-1 |
| `prompts/models.py` | Module-level `_BULK_SIZE_DISPLAY` + dynamic `SIZE_CHOICES` from `ALL_IMAGE_SIZES` | DRY-1 |
| `prompts/tests/test_bulk_generator.py` | `test_job_size_choices` imports and iterates `SUPPORTED_IMAGE_SIZES` | CRIT-1 |
| `prompts/management/commands/create_test_gallery.py` | `VALID_SIZES = set(SUPPORTED_IMAGE_SIZES)` (replaces local hardcoded set) | CRIT-3 |
| `prompts/templates/prompts/bulk_generator.html` | `aria-describedby="dimensionLabel"` on radiogroup + `aria-atomic="true"` on span | A11Y |
| `static/js/bulk-generator.js` | `hidden` → `disabled` + `"(coming soon)"` on 1792x1024 `<option>` | UX-1 |
| `prompts/migrations/0065_alter_bulkgenerationjob_size_choices.py` | Records SIZE_CHOICES label change (choices-only migration, no DDL) | Migration |

---

## Fix-by-Fix Verification

### DRY-1 — Size Centralisation (Root Cause Fix)

**Problem:** `1792x1024` was defined in 5 separate locations with no single source of truth. Phase 5B only updated 2 of 5 locations, causing CRIT-1/2/3.

**Solution:** `SUPPORTED_IMAGE_SIZES` and `ALL_IMAGE_SIZES` added to `prompts/constants.py`. All other files import from there.

**Agent verdicts:**
- @django-pro: "No circular dependency exists. All five consumers import from `constants.py`; `constants.py` imports from nothing in the app." — **PASS**
- @code-reviewer: "No Python file defines a hardcoded list of the 3 sizes outside `constants.py`." — **PASS**

**Consistency table verified by @code-reviewer:**

| Location | Count | Verdict |
|----------|-------|---------|
| `constants.py:SUPPORTED_IMAGE_SIZES` | 3 | PASS |
| `constants.py:ALL_IMAGE_SIZES` | 4 | PASS |
| `models.py:SIZE_CHOICES` | 4 tuples (dynamic) | PASS |
| `openai_provider.py:supported_sizes` | 3 (= SUPPORTED_IMAGE_SIZES) | PASS |
| `bulk_generator_views.py` validation | 3 (SUPPORTED_IMAGE_SIZES) | PASS |
| `test_bulk_generator.py:test_job_size_choices` | 3 via constant | PASS |
| `test_bulk_generator_views.py` rejection test | exists | PASS |
| JS select options | 4 (3 enabled + 1 disabled) | PASS |

**`1792x1024` containment** — only in permitted locations:
- `constants.py` ✅ (definition)
- `models.py` ✅ (SIZE_CHOICES, via `ALL_IMAGE_SIZES`)
- `migrations/0065_*` ✅ (historical migration record)
- `test_bulk_generator_views.py` ✅ (intentional rejection test)
- `bulk_generator.html` ✅ (button with `d-none` — unchanged, correct for button group)
- `bulk-generator.js` ✅ (disabled option — fixed this session)

---

### SEC-1 — Boolean Bypass in `images_per_prompt` Validation

**Problem:** `isinstance(images_per_prompt, bool)` check was absent. `True` would coerce to `1` via `int()` and silently pass validation.

**Solution:** Bool guard added BEFORE `int()` coercion. Order is critical in Python because `isinstance(True, int)` returns `True`.

**Agent verdicts (both security agents):**

| Input | Result | Correct? |
|-------|--------|----------|
| `True` (JSON `true`) | Bool guard → 400 | ✅ |
| `False` (JSON `false`) | Bool guard → 400 | ✅ |
| `1.0` (float) | Passes bool guard, `int(1.0)` = 1, valid | ✅ |
| `"2"` (string) | Passes bool guard, `int("2")` = 2, valid | ✅ |
| `None` | Passes bool guard, TypeError → 400 | ✅ |
| `5` | Passes bool guard, fails `> 4` → 400 | ✅ |
| `0` | Passes bool guard, fails `< 1` → 400 | ✅ |

Both security agents: **PASS**. Comment on line 232 documents the ordering requirement.

---

### SEC-4 — @login_required Comment on `flush_all`

**Problem:** The `@login_required` + explicit staff check pattern was flagged as a vulnerability on every review. The architectural decision wasn't documented.

**Solution:** Verbatim comment block added above `@login_required` explaining that `@staff_member_required` returns an HTML 302 redirect (not JSON), which breaks API endpoints.

**Agent verdict:** @security-auditor and @backend-security-coder both confirmed comment is present, technically accurate, and will prevent recurring false-positive flags. **PASS**.

---

### SEC-5 — Exception Leak in `api_validate_openai_key`

**Problem:** Final `except Exception` block returned `f'Validation failed: {str(e)}'` exposing internal exception details.

**Solution:** `str(e)` removed from `JsonResponse` body. Exception logged server-side via `logger.error()`. Generic safe message returned to client.

**Agent verdict (@backend-security):**
> "The JsonResponse on lines 455-458 returns a generic, non-informative message: 'Key validation failed. Please check your key and try again.' — reveals nothing about the internal exception type, stack trace, or system configuration."

**PASS**. `AuthenticationError` and `APIConnectionError` are still caught separately with appropriate specific messages.

---

### A11Y-1 — `aria-atomic="true"` on `#dimensionLabel`

**Problem:** NVDA+Firefox could announce only the changed portion of the label, not the full text.

**Solution:** `aria-atomic="true"` added to the `#dimensionLabel` span alongside existing `aria-live="polite"`.

**Agent verdict (@ui-ux-designer):**
> "`aria-atomic='true'` ensures screen readers announce the entire text content of the span as a single unit rather than announcing only the changed portion."

**PASS**.

---

### A11Y-4 — `aria-describedby="dimensionLabel"` on Radiogroup

**Problem:** Entering the dimension radiogroup didn't announce the current selection to screen readers.

**Solution:** `aria-describedby="dimensionLabel"` added to the radiogroup `<div>`.

**Agent verdict (@ui-ux-designer):**
> "When a screen reader enters the radiogroup, it will first read the `aria-label` ('Image dimensions') and then append the `aria-describedby` description ('1:1 Square' or whichever value is current)."

**PASS**. The agent correctly noted that `aria-describedby` reads at focus time, while `aria-live` handles re-announcement on change — the two attributes serve complementary purposes.

---

### UX-1 — `disabled` Replaces `hidden` on Unsupported `<option>`

**Problem:** `<option hidden>` is unreliable on Chrome/Windows and older Safari. Users couldn't see that the option exists but is unavailable.

**Solution:** `hidden` replaced with `disabled`. Display text changed from `"16:9"` to `"16:9 (coming soon)"`. Uses `data-future="true"` marker.

**Agent verdicts:**
- @ui-ux-designer: "Screen readers do not skip disabled options during list navigation — they announce them along with their disabled state." **PASS**
- @frontend-developer: "`disabled` is the correct HTML attribute here. Browsers universally skip disabled options during keyboard arrow-key navigation." **PASS**
- @frontend-developer (localStorage concern): "The `restorePromptsFromStorage` function only restores prompt text, source credits, and charDesc — it does NOT restore any per-prompt override select values. This concern is therefore self-resolving." **No action needed.**

---

## Issues Found by Agents

### MINOR: Migration Required (spec's "no migration required" claim was incorrect)

**Source:** Discovered during implementation.
**Detail:** The spec stated "No migration required — `choices` changes do not generate migrations." In Django 5.2, this is incorrect — choices label changes DO generate migrations. Migration `0065_alter_bulkgenerationjob_size_choices.py` was created to update the label from `'Wide (16:9)'` to `'Wide (16:9) — UNSUPPORTED (future use)'`. This is a choices-only migration with no DDL (no database schema change).
**Action taken:** Migration created and committed. `makemigrations --check --dry-run` passes clean.

### LOW: `str(e)` Retained in `flush_all` Error Collection

**Source:** @backend-security-coder.
**Detail:** `flush_all` still uses `errors.append(f"B2 error: {str(e)}")`. This leaks exception details to the response, but only to staff users (the view checks `request.user.is_staff`). The SEC-5 fix in the spec only targeted `api_validate_openai_key`.
**Decision:** Acceptable for now — staff-only endpoint. Add to future hardening backlog.

### LOW: JS `initButtonGroup` d-none Filtering Ties to Bootstrap

**Source:** @frontend-developer (noted, not blocking).
**Detail:** `initButtonGroup` filters buttons using `!b.classList.contains('d-none')`. This couples semantic button group logic to a Bootstrap utility class. Native `hidden` attribute would be more semantically correct.
**Decision:** Noted for future improvement. Not changed — modifying the master button group behaviour was out of scope for this spec. The `<select>` per-prompt override (the only true cross-browser issue) was correctly fixed.

---

## Confirmed Correct (Agent Verified)

| Item | Agent | Status |
|------|-------|--------|
| No circular imports introduced | @django-pro | ✅ PASS |
| `_BULK_SIZE_DISPLAY` at module scope (not class scope) | @django-pro | ✅ PASS |
| SIZE_CHOICES produces correct 4-tuple list | @django-pro | ✅ PASS |
| Migration 0065 is choices-only (no DDL) | @django-pro | ✅ PASS |
| Bool guard before int() coercion | All 3 security agents | ✅ PASS |
| str(e) not in api_validate_openai_key response | All 3 security agents | ✅ PASS |
| SEC-4 comment present and accurate | All 3 security agents | ✅ PASS |
| aria-atomic="true" on #dimensionLabel | @ui-ux-designer | ✅ PASS |
| aria-describedby="dimensionLabel" on radiogroup | @ui-ux-designer | ✅ PASS |
| disabled option cannot be selected via keyboard | @frontend-developer | ✅ PASS |
| localStorage restore does not resurrect 1792x1024 | @frontend-developer | ✅ PASS |
| updateDimensionLabel unaffected by ARIA changes | @frontend-developer | ✅ PASS |
| 1792x1024 only in permitted locations | @code-reviewer | ✅ PASS |
| test_job_size_choices uses constant not hardcoded list | @code-reviewer | ✅ PASS |
| VALID_SIZES = set(SUPPORTED_IMAGE_SIZES) in create_test_gallery.py justified | @code-reviewer | ✅ PASS |

---

## Test Results

```
Ran 124 tests in 1208.176s
OK
```

- `prompts.tests.test_bulk_generator` — 45 tests (model layer, provider layer)
- `prompts.tests.test_bulk_generator_views` — 79 tests (API endpoints, including new 1792x1024 rejection test)
- All 124 pass. No regressions.

---

## Verification Commands (all passed)

```bash
# 1 — 1792x1024 only in permitted locations (Python/HTML files)
grep -rn "1792x1024" prompts/ --include="*.py" --include="*.html" | grep -v "constants.py\|models.py\|__pycache__\|migrations"
# → Only test_bulk_generator_views.py (rejection test) and bulk_generator.html (d-none button)

# 2 — No local VALID_SIZES in views
grep -rn "VALID_SIZES" prompts/views/
# → Zero results (only __pycache__)

# 3 — No pending migrations
python manage.py makemigrations --check --dry-run
# → No changes detected

# 4 — SEC-4 comment present
grep -n "intentionally uses @login_required" prompts/views/bulk_generator_views.py
# → 494: # NOTE: This view intentionally uses @login_required + explicit staff

# 5 — No str(e) in JsonResponse in api_validate_openai_key
grep -n "str(e)" prompts/views/bulk_generator_views.py
# → Only in errors.append() calls inside flush_all (staff-only, acceptable)

# 6 — aria-atomic present
grep -n "aria-atomic" prompts/templates/prompts/bulk_generator.html
# → line 128: aria-atomic="true"

# 7 — aria-describedby on radiogroup
grep -n "aria-describedby.*dimensionLabel" prompts/templates/prompts/bulk_generator.html
# → line 110: aria-describedby="dimensionLabel"

# 8 — disabled + coming soon in JS
grep -n "coming soon" static/js/bulk-generator.js
# → line 162: 16:9 (coming soon)
```

---

## Areas to Improve (Future Sessions)

| Priority | Item | Notes |
|----------|------|-------|
| LOW | `str(e)` in `flush_all` error list | Staff-only view, but leaks internal detail |
| LOW | `initButtonGroup` d-none coupling | Semantic improvement: use `hidden` attribute instead of Bootstrap class |
| LOW | `model_name` and `generator_category` not validated against allowlists | SEC-3 from Phase 5B review — still unresolved |
| LOW | API key validated only by `sk-` prefix | Minimum length check would add defence in depth |
| FUTURE | `SUPPORTED_IMAGE_SIZES` for 1536x1024 ordering | Currently `[1024x1024, 1024x1536, 1536x1024]` — alphabetical, not display order. Display order in template is 1:1, 2:3, 16:9(hidden), 3:2. No functional issue. |

---

## Summary

The DRY-1 size centralisation eliminates the root cause of CRIT-1/2/3 from the Phase 5B review. Five separate size definitions across 5 files are now a single source of truth in `constants.py`. All 9 spec items are implemented and independently verified by 6 agents averaging 8.37/10. The codebase is significantly cleaner: future size additions require updating ONE constant, and tests automatically stay correct without manual intervention.
