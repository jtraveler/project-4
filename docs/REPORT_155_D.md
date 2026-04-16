# REPORT_155_D — Nano Banana 2 Reference Image Wiring

## Section 1 — Overview

Nano Banana 2 (`google/nano-banana-2`) on Replicate accepts reference images via an `image_input` array parameter, but the Replicate provider was not wiring reference image URLs into the API call. This spec adds the `_MODEL_IMAGE_INPUT_PARAM` lookup dict and wires reference images for models that support them.

## Section 2 — Expectations

- ✅ Step 0b schema dump completed — `image_input` confirmed as `array` type (Case A)
- ✅ `_MODEL_IMAGE_INPUT_PARAM` at module level with `('image_input', 'array')` for Nano Banana 2
- ✅ Array wrapping: `[reference_image_url]` when kind == 'array'
- ✅ HTTPS validation before API call
- ✅ Flux models NOT added to `_MODEL_IMAGE_INPUT_PARAM`
- ✅ 3 new tests with paired assertions
- ✅ Docstring updated to reflect reference image support

## Section 3 — Changes Made

### Step 0b — Heroku Schema Dump (raw output)
```
=== ALL PROPERTIES ===
  aspect_ratio: unknown | Aspect ratio of the generated image
  google_search: boolean | Use Google Web Search grounding to generate images based on
  image_input: array | Input images to transform or use as reference (supports up t
  image_search: boolean | Use Google Image Search grounding to find web images as visu
  output_format: unknown | Format of the output image
  prompt: string | A text description of the image you want to generate
  resolution: unknown | Resolution of the generated image. Higher resolutions take l
```
**Case A confirmed:** `image_input` exists as `array` type.

### prompts/services/image_providers/replicate_provider.py
- Lines 50-57: Added `_MODEL_IMAGE_INPUT_PARAM` dict at module level
- Lines 148-157: Added reference image wiring block after `num_inference_steps`
- Line 121: Updated docstring to document reference_image_url support

### prompts/tests/test_replicate_provider.py
- Added `NanoBanana2ReferenceImageTests` class with `_run_generate()` helper
- `test_nano_banana_2_wraps_reference_url_in_list` — array wrapping verified
- `test_no_reference_url_omits_image_input` — no ref URL = no image_input key
- `test_flux_schnell_reference_url_not_wired` — Flux Schnell not in param map

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Nano Banana 2 also has `google_search` and `image_search` boolean params that could enhance results.
**Impact:** Possible quality improvement for generated images.
**Recommended action:** Evaluate adding these as options in a future session.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 8.5/10 | Clean, modular implementation | N/A |
| 1 | @python-pro | 8.5/10 | Type annotations correct, tuple pattern clear | N/A |
| **Average** | | **8.5/10** | | **Pass ≥ 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Manual browser test: Select Nano Banana 2 → upload ref image → generate → verify Heroku logs show `image_input` in API inputs
2. Evaluate `google_search` and `image_search` Nano Banana 2 params
3. Add additional Replicate models to `_MODEL_IMAGE_INPUT_PARAM` as confirmed
