# REPORT_154_L_CHARACTER_REF_IMAGE.md

**Spec:** CC_SPEC_154_L_CHARACTER_REF_IMAGE.md
**Session:** 154
**Date:** April 14, 2026

---

## Section 1 — Overview

The "Character Reference Image" upload section was always visible in the
bulk generator master settings, but only GPT-Image-1.5 (OpenAI BYOK)
actually consumes the reference image — Replicate and xAI providers
silently ignore it. This created confusion for users who expected the
reference to influence Flux/Grok outputs.

This spec adds a `supports_reference_image` field to `GeneratorModel`,
seeds it `True` only for GPT-Image-1.5, and updates `handleModelChange`
to show/hide the section based on the selected model.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `supports_reference_image` field added with `default=False` | ✅ Met |
| Migration created and applied | ✅ Met (0083) |
| Seed updated — True for GPT only, False for 5 others | ✅ Met |
| Seed re-run idempotent (0 created, 6 updated) | ✅ Met |
| View `.values()` queryset includes new field | ✅ Met |
| `data-supports-ref-image` on BOTH option loops | ✅ Met |
| `handleModelChange` shows/hides ref image section | ✅ Met |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### `prompts/models.py`
- Lines 3334–3343: Added `supports_reference_image = BooleanField(default=False)`
  with help text on `GeneratorModel`. Placed immediately before `sort_order`.

### `prompts/migrations/0083_add_supports_reference_image_to_generator_model.py`
- New migration adding the boolean field to `generatormodel`.

### `prompts/management/commands/seed_generator_models.py`
- GPT-Image-1.5 dict (line ~30): `'supports_reference_image': True`
- All 5 other model dicts: `'supports_reference_image': False`

### `prompts/views/bulk_generator_views.py`
- Line ~88: Added `'supports_reference_image'` to the `.values(...)`
  list on the `generator_models` queryset.

### `prompts/templates/prompts/bulk_generator.html`
- Line ~56: Added `data-supports-ref-image="{{ model.supports_reference_image|yesno:'true,false' }}"` to the non-BYOK option loop.
- Line ~72: Same attribute added to the BYOK option loop.

### `static/js/bulk-generator.js`
- Line 883: Added `var supportsRefImage = opt.dataset.supportsRefImage === 'true';`
- After per-box override hide block, before `I.updateCostEstimate()`:
  added show/hide block targeting `#refUploadZone.closest('.bg-setting-group')`.

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The ref image section's visibility is now driven by client-side
JS reading a data attribute. Server-side validation should also reject
reference images submitted for non-supporting providers.
**Impact:** Currently, a user who pastes a ref image, then switches to
Flux, then generates may still upload + waste B2 storage on a reference
image that the provider ignores.
**Recommended action:** Add a check in `bulk_generation.create_job()` —
if `selected_model.supports_reference_image` is False and a reference URL
was supplied, clear it (or warn). File: `prompts/services/bulk_generation.py`.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder (Option B for @django-security) | 8.5/10 | `default=False` correctly fail-safe — existing models default to NOT supporting ref images until seed runs. Migration safe to roll forward. | N/A |
| 1 | @tdd-orchestrator (Option B for @tdd-coach) | 8.0/10 | Seed idempotency confirmed via test run (0 created, 6 updated). Recommends future test asserting `supports_reference_image=False` for all non-OpenAI providers — deferred to a separate test-only spec. | N/A — recommendation deferred |
| 1 | @code-reviewer | 8.5/10 | `.closest('.bg-setting-group')` correctly targets the ref-image wrapper div (verified at template line 81). `data-supports-ref-image` present on both option loops. JS variable used — IDE hint resolved after refImage block added. | N/A |
| **Average** | | **8.33/10** | | Pass ≥8.0 |

**Agent substitutions:** `@backend-security-coder` for `@django-security`,
`@tdd-orchestrator` for `@tdd-coach` per Option B authorisation.

---

## Section 8 — Recommended Additional Agents

**@accessibility-auditor:** Would verify that hiding the ref image section
via `display: none` correctly removes it from the tab order. The wrapping
`<div class="bg-setting-group">` contains a button-role upload zone, so
toggling visibility implicitly handles focus order — low risk.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts
# Expected: 1227 tests, 0 failures

python manage.py shell -c "
from prompts.models import GeneratorModel
print(GeneratorModel.objects.get(slug='gpt-image-1-5-byok').supports_reference_image)
print(GeneratorModel.objects.get(slug='flux-schnell').supports_reference_image)
"
# Expected: True, False
```

**Manual browser steps:**
1. Navigate to `/tools/bulk-ai-generator/`
2. Default model = GPT-Image-1.5 → Character Reference Image section visible
3. Switch to Flux Schnell → section hidden
4. Switch to Grok Imagine → section hidden
5. Switch back to GPT-Image-1.5 → section visible

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| (TBD) | feat(bulk-gen): hide Character Reference Image for non-supporting models |

---

## Section 11 — What to Work on Next

1. Server-side enforcement (Section 6) — clear `reference_image_url` in
   `create_job()` if the selected model does not support it.
2. Add tests asserting `supports_reference_image=False` for all non-OpenAI
   providers (recommended by tdd agent).
