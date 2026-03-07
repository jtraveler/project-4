# Bulk Generator Phase 5B Bug Fixes — 6-Agent Review Report

**Session:** March 7, 2026
**Commit:** `62568e6` — fix(bulk-generator): fix images_per_prompt, aspect ratio, and dropdown bugs
**Scope:** Three bugs fixed across 6 files (Bug 1: hide 1792x1024, Bug 2: images_per_prompt gallery slots, Bug 3C: dimension label)
**Test Results:** 78 + 45 = 123 tests, all passing at time of commit

---

## Scorecard

| Agent | Focus Area | Rating |
|-------|-----------|--------|
| @django-pro | Task loop, ORM queries, API call chain | 8.1/10 |
| @security-auditor | Input validation, auth, API key handling | 7.5/10 |
| @accessibility-specialist | aria-live, keyboard nav, WCAG AA | 7.1/10 |
| @ux-ui-designer | Gallery layout, dropdown UX, breakpoints | 7.1/10 |
| @frontend-developer | JS/CSS mechanics, race conditions | 8.2/10 |
| @code-reviewer | Cross-file consistency, test coverage | 7.0/10 |
| **Average** | | **7.5/10** |

---

## Critical Issues (Must Fix Before Next Phase)

### CRIT-1 — `test_job_size_choices` not updated [@code-reviewer, HIGH]

**File:** `prompts/tests/test_bulk_generator.py` line ~107

The `test_openai_provider_supported_sizes` test was correctly updated from 4 to 3 sizes. However, `test_job_size_choices` was missed:

```python
# STILL WRONG — test says 4 sizes are valid model choices:
def test_job_size_choices(self):
    """Test all 4 size values are valid."""   # docstring says 4
    sizes = ['1024x1024', '1024x1536', '1536x1024', '1792x1024']  # still 4
```

The test passes only because `models.py` `SIZE_CHOICES` was also not updated — the inconsistency is internally self-consistent but externally incorrect. A Django admin user could create a job with `1792x1024` (model allows it), it would pass model validation, but fail at generation time (API rejects it).

**Fix:** Update the test docstring to "3" and remove `1792x1024` from the sizes list.

---

### CRIT-2 — `models.py` SIZE_CHOICES still includes 1792x1024 [@code-reviewer, HIGH]

**File:** `prompts/models.py` (BulkGenerationJob model)

```python
SIZE_CHOICES = [
    ('1024x1024', 'Square (1:1)'),
    ('1024x1536', 'Portrait (2:3)'),
    ('1536x1024', 'Landscape (3:2)'),
    ('1792x1024', 'Wide (16:9)'),   # <-- still marked as a valid choice
]
```

The model says "valid", the API view says "invalid", the provider says "invalid". This three-way mismatch means a Django admin could inadvertently start a job that will fail mid-generation.

**Fix (no migration required):** Keep the entry but annotate it clearly:
```python
('1792x1024', 'Wide (16:9) — UNSUPPORTED (future use)'),
```

---

### CRIT-3 — `create_test_gallery.py` mirrors old VALID_SIZES [@code-reviewer, MEDIUM-HIGH]

**File:** `prompts/management/commands/create_test_gallery.py`

The management command has a comment saying it mirrors `VALID_SIZES` from `bulk_generator_views.py`, but still contains `1792x1024` in both its local constant and in a test prompt config.

**Fix:** Update `create_test_gallery.py` to remove `1792x1024` from its local `VALID_SIZES` set and remove the test prompt that uses it.

---

## Security Issues

### SEC-1 — `isinstance(True, int)` passes validation [@security-auditor, MEDIUM] + [@django-pro]

**File:** `bulk_generator_views.py`

In Python `bool` is a subclass of `int`, so `isinstance(True, int)` returns `True`. A JSON payload with `"images_per_prompt": true` would pass the current check and be treated as `1`. More importantly, the current pattern rejects `float` values (`isinstance(1.0, int)` returns `False`), but the error message "must be a positive integer" doesn't tell callers whether floats are the problem.

The fix also handles the case identified by @django-pro where a JSON float `1.0` from misconfigured HTTP clients is confusingly rejected with a misleading error:

```python
# Replace both isinstance checks in api_start_generation:
images_per_prompt = data.get('images_per_prompt', 1)
if isinstance(images_per_prompt, bool):
    return JsonResponse(
        {'error': 'images_per_prompt must be a positive integer'},
        status=400,
    )
try:
    images_per_prompt = int(images_per_prompt)
except (TypeError, ValueError):
    return JsonResponse(
        {'error': 'images_per_prompt must be a positive integer'},
        status=400,
    )
if images_per_prompt < 1 or images_per_prompt > 4:
    return JsonResponse(
        {'error': 'images_per_prompt must be between 1 and 4'},
        status=400,
    )
```

---

### SEC-2 — API key prefix-only validation [@security-auditor, LOW-MEDIUM]

**File:** `bulk_generator_views.py`

The check `api_key.startswith('sk-')` accepts a 4-character string like `sk-x`, which is clearly not a real key. This wastes a Django-Q task slot, creates a job record, and only fails asynchronously when the background task runs.

**Fix:**
```python
if not api_key or not api_key.startswith('sk-') or len(api_key) < 20:
    return JsonResponse(
        {'error': 'A valid OpenAI API key (starting with sk-) is required.'},
        status=400,
    )
```

---

### SEC-3 — `model_name` and `generator_category` unvalidated [@security-auditor, MEDIUM]

**File:** `bulk_generator_views.py`

Both fields pass through from user input without allowlist validation:
```python
model_name=data.get('model', 'gpt-image-1'),
generator_category=data.get('generator_category', 'ChatGPT'),
```

`generator_category` in particular renders in templates and could be a stored XSS vector if ever rendered with `|safe` or `mark_safe`.

**Fix:** Add explicit validation:
```python
VALID_MODELS = {'gpt-image-1'}
VALID_GENERATOR_CATEGORIES = {'ChatGPT', 'DALL-E', 'Midjourney', 'Stable Diffusion', 'Other'}

model_name = data.get('model', 'gpt-image-1')
if model_name not in VALID_MODELS:
    return JsonResponse({'error': f'Invalid model.'}, status=400)

generator_category = data.get('generator_category', 'ChatGPT')
if generator_category not in VALID_GENERATOR_CATEGORIES:
    generator_category = 'ChatGPT'  # or reject: return JsonResponse({'error': ...}, 400)
```

---

### SEC-4 — `@login_required` vs `@staff_member_required` on `flush_all` [@django-pro, MEDIUM]

**File:** `bulk_generator_views.py`

`bulk_generator_flush_all` uses `@login_required` + manual `is_staff` check, while every other endpoint in the file uses `@staff_member_required`. The behavioural difference: an unauthenticated request to `flush_all` gets a 302 redirect (to login), not a JSON 403. If the JS flush handler follows the redirect silently on session timeout, it may interpret the login HTML as a JSON parse error rather than an auth error.

**Fix:** Replace `@login_required` with `@staff_member_required` and remove the manual `is_staff` guard.

---

## Accessibility Issues

### A11Y-1 — Missing `aria-atomic="true"` on dimension label [@accessibility-specialist, MEDIUM]

**File:** `bulk_generator.html`

Without `aria-atomic="true"`, NVDA on Firefox may announce only the changed portion of the text node rather than the full updated string. Add it:

```html
<span class="bg-setting-hint" id="dimensionLabel"
      aria-live="polite" aria-atomic="true">1:1 Square</span>
```

---

### A11Y-2 — `role="radio"` on `<button>` is a WAI-ARIA role conflict [@accessibility-specialist, MEDIUM-HIGH]

**File:** `bulk_generator.html`

`<button>` has an implicit native role of `button`. Applying `role="radio"` creates a host element mismatch. WAI-ARIA 1.2 lists valid host elements for `role="radio"` as non-interactive elements (`<div>`, `<span>`), not `<button>`. Some screen readers expose this as "button" ignoring the overridden radio role.

The correct fix changes the element type:
```html
<div class="bg-btn-group-option active" data-value="1024x1024"
     role="radio" aria-checked="true" tabindex="0">
    1:1
    <span class="bg-dim-icon" data-ratio="1:1" aria-hidden="true"></span>
</div>
```

However, this requires JS focus management changes (`.focus()` works on `<div>` with `tabindex`, so no change needed there). This is a medium-effort fix. For a staff-only tool, it may be deferred.

---

### A11Y-3 — Button accessible names too terse [@accessibility-specialist, LOW-MEDIUM]

**File:** `bulk_generator.html`

"1:1", "2:3", "3:2" are announced as "one colon one" etc. on many screen readers. Add `aria-label` with the human-readable form:

```html
<button ... data-value="1024x1024" aria-label="1:1 Square" role="radio" ...>
    1:1
    ...
</button>
<button ... data-value="1024x1536" aria-label="2:3 Portrait" role="radio" ...>
    2:3
    ...
</button>
<button ... data-value="1536x1024" aria-label="3:2 Landscape" role="radio" ...>
    3:2
    ...
</button>
```

---

### A11Y-4 — Radiogroup missing `aria-describedby` linking to dimensionLabel [@accessibility-specialist, LOW-MEDIUM]

**File:** `bulk_generator.html`

When a screen reader enters the radiogroup, it announces "Image dimensions" but not the current selection description. Linking to `dimensionLabel` would announce "Image dimensions — 1:1 Square":

```html
<div class="bg-btn-group" id="settingDimensions"
     role="radiogroup"
     aria-label="Image dimensions"
     aria-describedby="dimensionLabel">
```

---

## UX / Frontend Issues

### UX-1 — `<option hidden>` browser compatibility [@ux-ui-designer, MEDIUM]

**File:** `static/js/bulk-generator.js` (dynamically generated per-box override select)

The `hidden` attribute on `<option>` elements is not reliably supported across all browsers. Chrome on Windows does not always hide `<option hidden>` elements in the native dropdown. The option remains visible and selectable.

```javascript
// CURRENT (unreliable on Chrome/Windows):
'<option value="1792x1024" hidden data-future="true">16:9</option>'

// SAFER — use disabled + a visual indicator instead:
'<option value="1792x1024" disabled data-future="true">16:9 (coming soon)</option>'
```

`disabled` options are universally supported across all browsers — they render grayed out and are not selectable. This is more UX-honest than hiding them entirely.

Note: @frontend-developer assessed the `hidden` attribute on `<option>` as broadly supported across modern browsers and did not flag this. The safer option remains `disabled` + "(coming soon)" text.

---

### UX-2 — Dimension label at 11px is undersized for dynamic state text [@ux-ui-designer, LOW-MEDIUM]

**File:** `static/css/pages/bulk-generator.css`

`.bg-setting-hint` renders at `0.6875rem` (11px). For static helper text like "Must be a clear photo of a person" this is acceptable. For the dimension label which updates dynamically and is the only textual confirmation of the selected dimension, 11px is undersized.

**Fix:** Add a modifier or override for the dimension label specifically:
```css
#dimensionLabel {
    font-size: 0.8125rem;  /* 13px — matches other label text */
}
```

This avoids changing `.bg-setting-hint` globally.

---

### FE-1 — Bootstrap class used for keyboard navigation logic [@frontend-developer, MEDIUM]

**File:** `static/js/bulk-generator.js`

The keyboard exclusion logic:
```javascript
function (b) { return !b.classList.contains('d-none'); }
```

This ties the "is this button available?" semantic to a Bootstrap CSS class. If Bootstrap is ever swapped, tree-shaken, or the hiding mechanism changes, keyboard navigation silently breaks. The `buttons` array is also a snapshot captured at `initButtonGroup` call time — it does not update if visibility changes at runtime.

**Preferred fix:** Use the native `hidden` HTML attribute for the unsupported button and filter on that:
```html
<!-- In HTML: replace d-none with hidden -->
<button ... hidden data-future="true" ...>
```
```javascript
// In JS:
function (b) { return !b.hidden; }
```

This is semantically correct (the button is genuinely hidden, not just visually styled) and has no framework dependency. The visual `d-none` class can be removed entirely as `hidden` applies `display: none` natively.

---

### FE-2 — `updateDimensionLabel` may not fire on per-box override change [@frontend-developer, LOW]

**File:** `static/js/bulk-generator.js`

The `updateDimensionLabel` function is wired to the master settings dimension button group and to the reset handler. However, if the per-box override dimension select is changed, the master label does not update (it reflects master settings, not per-box). This is technically correct behavior, but if a user changes a per-box override and then looks at the master label, they may perceive it as stale. This is a UX documentation concern rather than a bug.

**Recommendation:** Add a comment to the `updateDimensionLabel` function clarifying it reflects master settings only:
```javascript
// Updates the master settings dimension label only.
// Per-box overrides do not affect this label by design.
function updateDimensionLabel(value) { ... }
```

---

## DRY Violations and Architecture Notes

### DRY-1 — Size definitions spread across 4+ locations [@code-reviewer, MEDIUM]

The "valid sizes" concept is defined separately in:
1. `bulk_generator_views.py` — `VALID_SIZES` (set)
2. `openai_provider.py` — `supported_sizes` (list)
3. `models.py` — `SIZE_CHOICES` (list of tuples)
4. `constants.py` — `IMAGE_COST_MAP` (nested dict keys)
5. `create_test_gallery.py` — local `VALID_SIZES` (set)

When a new size is added or removed, all 5 must be updated. The Phase 5B fix updated only 2 of 5, which is why CRIT-1, CRIT-2, and CRIT-3 exist.

**Recommendation:** Create a single source of truth in `prompts/constants.py`:
```python
# All sizes supported by GPT-Image-1 for generation
SUPPORTED_IMAGE_SIZES = ['1024x1024', '1024x1536', '1536x1024']

# All sizes ever used (including future/historical) — for model choices
ALL_IMAGE_SIZES = SUPPORTED_IMAGE_SIZES + ['1792x1024']  # 1792x1024: reserved, not exposed
```

Then import and use `SUPPORTED_IMAGE_SIZES` in `bulk_generator_views.py` and `openai_provider.py`.

---

### DRY-2 — `DIMENSION_LABELS` in JS not linked to backend constants [@code-reviewer, LOW]

```javascript
var DIMENSION_LABELS = {
    '1024x1024': '1:1 Square',
    '1024x1536': '2:3 Portrait',
    '1536x1024': '3:2 Landscape',
};
```

This is a fifth separate representation of the dimension-to-label mapping. For a staff tool with infrequent changes this is acceptable, but a comment cross-referencing `VALID_SIZES` in the views would help future maintenance.

---

## Areas to Improve (Future Work)

These are not bugs — they are quality-of-life improvements that would make the code more maintainable and robust.

| # | Area | Description | Priority |
|---|------|-------------|----------|
| 1 | Size canonicalization | Single `SUPPORTED_IMAGE_SIZES` constant in `constants.py`, imported by all files | High |
| 2 | `data-future` convention | Document in `PROJECT_FILE_STRUCTURE.md` or a code comment what `data-future="true"` means and what steps to take to enable a future option | Medium |
| 3 | Model constraint | Add a `BulkGenerationJob` model-level validator that checks `size` is in `SUPPORTED_IMAGE_SIZES` (not just `SIZE_CHOICES`) | Medium |
| 4 | `role="radio"` on `<button>` | Refactor dimension and images-per-prompt button groups to use `<div role="radio">` per WAI-ARIA spec | Medium (Phase 6) |
| 5 | Dimension label font size | Increase `#dimensionLabel` from 11px to 13px for dynamic state text readability | Low |
| 6 | Gallery slot mobile behavior | Add explicit CSS or JS documentation for how 2-4 image slots per prompt group behave at mobile breakpoints (single-column layout) | Low |
| 7 | `initButtonGroup` snapshot | Add a comment noting the `buttons` array is a snapshot; re-call `initButtonGroup` if visibility changes at runtime | Low |
| 8 | `generator_category` allowlist | Add `VALID_GENERATOR_CATEGORIES` set and validate against it to prevent arbitrary string storage | Medium |

---

## Confirmed Correct (Passes All Agents)

The following were identified as risks in the spec but confirmed correct:

| Item | Finding |
|------|---------|
| `aria-live="polite"` placement | Correct choice (polite vs assertive) |
| `d-none` removes from accessibility tree | Confirmed — `display:none` removes from a11y tree |
| `aria-checked` as strings `"true"`/`"false"` | Correct per HTML spec |
| `img.onload` race condition in Bug 2 fix | No race condition — `classList.remove` is sync, `onload` is async. Fix is sound |
| `reference_image_url` domain check | `parsed.netloc` is an exact match; subdomain bypass not possible |
| `textContent` vs `innerHTML` for label | `textContent` is XSS-safe and correct |
| `source_credits` pad loop | Functionally correct; no OOB risk |
| `gallery_aspect` calculation | Safe from injection; only produces `"W / H"` format strings |
| Gallery 4-slot layout at mobile | Confirmed correct — CSS forces `repeat(2, 1fr)` at ≤989px and `1fr` at ≤480px using `!important`; empty slots hidden via `display:none` |
| Loop bounds (images_per_prompt, prompts, retries) | All confirmed bounded: max 200 images/job, max 3 retries, cancel-check before every image |
| Prompt injection in `character_description` | By design — staff-only tool; user intentionally controls prompt text |

---

## Actionable Fix Summary

Ordered by priority:

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| P1 | CRIT-1: `test_job_size_choices` not updated | `test_bulk_generator.py` | Update docstring + remove 1792x1024 from list |
| P1 | CRIT-2: `SIZE_CHOICES` still includes 1792x1024 | `models.py` | Add `— UNSUPPORTED (future use)` to display name |
| P1 | CRIT-3: `create_test_gallery.py` out of sync | `create_test_gallery.py` | Update local VALID_SIZES and remove 1792x1024 prompt |
| P2 | SEC-1: `isinstance(bool, int)` bypass | `bulk_generator_views.py` | Add `isinstance(..., bool)` guard + use `int()` coercion |
| P2 | SEC-4: `@login_required` inconsistency on flush_all | `bulk_generator_views.py` | Change to `@staff_member_required` |
| P2 | UX-1: `<option hidden>` cross-browser | `bulk-generator.js` | Change to `disabled` + "(coming soon)" text |
| P3 | SEC-2: API key length check | `bulk_generator_views.py` | Add `len(api_key) < 20` check |
| P3 | SEC-3: `model_name`/`generator_category` unvalidated | `bulk_generator_views.py` | Add `VALID_MODELS` + `VALID_GENERATOR_CATEGORIES` sets |
| P3 | SEC-5: Exception `str(e)` leaked to client | `bulk_generator_views.py` | Replace `f'Validation failed: {str(e)}'` with generic message in `api_validate_openai_key` |
| P3 | A11Y-1: Missing `aria-atomic="true"` | `bulk_generator.html` | Add to `dimensionLabel` span |
| P3 | A11Y-4: Missing `aria-describedby` on radiogroup | `bulk_generator.html` | Add `aria-describedby="dimensionLabel"` |
| P4 | FE-1: Bootstrap class in nav logic | `bulk-generator.js` | Change `d-none` to `hidden` attribute + filter on `!b.hidden` |
| P4 | A11Y-2: `role="radio"` on `<button>` | `bulk_generator.html` | Defer to Phase 6; document the gap |
| P4 | A11Y-3: Terse button accessible names | `bulk_generator.html` | Add `aria-label` with full dimension description |
| P4 | A11Y-5: `btn.focus()` fires on mouse clicks | `bulk-generator.js` | Guard `btn.focus()` in `activateButton()` behind a `fromKeyboard` boolean to prevent scroll-jump on mouse clicks |
| P5 | UX-2 / A11Y-6: 11px text too small | `bulk-generator.css` | Raise `.bg-setting-hint` base to `0.75rem` (12px minimum for informational text); or add `#dimensionLabel { font-size: 0.8125rem }` override |
| P5 | DRY-1: Size definitions in 5 locations | `constants.py` + all | Centralize into `SUPPORTED_IMAGE_SIZES` constant |
| P5 | DRY-2: DIMENSION_LABELS in JS | `bulk-generator.js` | Add cross-reference comment |
| P5 | Missing `select_related` on jobs query | `bulk_generator_views.py` | Add `.select_related('created_by')` to `bulk_generator_page` jobs query to prevent up to 10 extra queries per page load |

---

## Next Steps

P1 items (CRIT-1, CRIT-2, CRIT-3) should be fixed immediately as a follow-up commit since they represent real inconsistencies introduced by the Phase 5B fix. P2/P3 items can be bundled into Phase 5D or Phase 6. P4/P5 items are polish and can be deferred.

**Phase 5D (E2E verification)** remains the primary next step per the CLAUDE.md roadmap: confirm the full pipeline works (API call → B2 upload → CDN URL → DB record → UI render) using the `[BULK-DEBUG]` logging added in Session 104.
