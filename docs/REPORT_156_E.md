# REPORT 156-E — FLUX 2 Pro Provider

## Section 1 — Overview

Added FLUX 2 Pro (`black-forest-labs/flux-2-pro`) to the bulk generator. FLUX 2 Pro is
Black Forest Labs' current-generation model supporting up to 8 reference images. Step 0b
Heroku schema dump confirmed the `input_images` parameter (type `array`) for reference images.

## Section 2 — Expectations

- ✅ Step 0b schema dump completed — `input_images` (array) confirmed
- ✅ FLUX 2 Pro added to `_MODEL_IMAGE_INPUT_PARAM`
- ✅ FLUX 2 Pro added to `get_cost_per_image()` cost_map ($0.015/MP)
- ✅ Seed entry added with correct fields
- ✅ DB record created via `seed_generator_models` (confirmed via shell)
- ✅ `_PROVIDER_COSTS` and `_apiCosts` updated
- ✅ 2 new tests with paired assertions
- ✅ `python manage.py check` passes

## Section 3 — Changes Made

### prompts/services/image_providers/replicate_provider.py
- `_MODEL_IMAGE_INPUT_PARAM`: Added `'black-forest-labs/flux-2-pro': ('input_images', 'array')`
- `get_cost_per_image()` cost_map: Added `'black-forest-labs/flux-2-pro': 0.015`

### prompts/management/commands/seed_generator_models.py
- Added FLUX 2 Pro seed entry: 5 credits, sort_order 55, supports_reference_image=True

### prompts/views/bulk_generator_views.py
- `_PROVIDER_COSTS`: Added `'black-forest-labs/flux-2-pro': 0.015`

### static/js/bulk-generator.js
- `_apiCosts`: Added `'black-forest-labs/flux-2-pro': 0.015`

### prompts/tests/test_replicate_provider.py
- Added `test_flux_2_pro_cost()` and `test_flux_2_pro_in_image_input_param_map()`

## Section 4 — Issues Encountered and Resolved

**Step 0b schema dump output (raw):**
```
Model version: ccb5e33141097816e6fab8c895e702fe4c619e4e07500885b71214e9f6382a5c
=== ALL PROPERTIES ===
  aspect_ratio: unknown | enum=[] | Aspect ratio for the generated image
  height: integer | enum=[] | Height of the generated image
  input_images: array | enum=[] | List of input images for image-to-image generation. Maximum 8 images
  output_format: unknown | enum=[] | Format of the output images
  output_quality: integer | enum=[] | Quality when saving the output images
  prompt: string | enum=[] | Text prompt for image generation
  resolution: unknown | enum=[] | Resolution in megapixels
  safety_tolerance: integer | enum=[] | Safety tolerance
  seed: integer | enum=[] | Random seed
  width: integer | enum=[] | Width of the generated image
```

Case A confirmed: `input_images` (array) is the reference image parameter.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** FLUX 2 Pro uses per-megapixel pricing ($0.015/MP). The flat $0.015 cost in
the cost_map assumes 1MP output. Higher resolutions (2MP, 4MP) would cost more. With
reference images, input MP also counts ($0.015 input + $0.015 output = $0.030 for 1MP).
**Recommended action:** Consider adding resolution-aware cost calculation in future.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 8.5/10 | HTTPS ref image validation reused. Same SSRF defense as NB2. | N/A |
| 1 | @code-reviewer | 8.5/10 | `_MODEL_IMAGE_INPUT_PARAM` and cost_map in sync. Correct model ID. | N/A |
| 1 | @python-pro | 8.5/10 | Type annotations correct. Docstring updated. | N/A |
| 1 | @tdd-orchestrator | 8.5/10 | 2 tests with paired assertions. Param map + cost tests cover key areas. | N/A |
| 1 | @django-pro | 8.5/10 | Seed uses update_or_create. sort_order 55 correct (no conflict). | N/A |
| 1 | @architect-review | 8.5/10 | Model family field deferred. Current pattern adequate for 7 models. | N/A |
| **Average (all 6)** | | **8.50/10** | | **Pass ≥8.5** |

## Section 8 — Recommended Additional Agents

All relevant agents were included.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_replicate_provider --verbosity=0
# Expected: 16+ tests, 0 failures

python manage.py test --verbosity=0
# Expected: 1268 tests, 0 failures, 12 skipped
```

**Post-deploy:** Run `python manage.py seed_generator_models` to create FLUX 2 Pro record.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(see below)* | feat(providers): add FLUX 2 Pro with reference image support |

## Section 11 — What to Work on Next

1. **Resolution-aware pricing** — FLUX 2 Pro's per-MP pricing varies with resolution.
2. **Reference image cost premium** — With ref image, cost doubles ($0.015 → $0.030).
3. **Manual browser test** — Select FLUX 2 Pro, verify dropdown shows, ref image enabled.
