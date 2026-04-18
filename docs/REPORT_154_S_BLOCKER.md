# REPORT_154_S_BLOCKER

**Spec:** CC_SPEC_154_S_REPLICATE_REF_IMAGE.md
**Session:** 154 (Batch 6)
**Date:** 2026-04-15
**Status:** ⛔ BLOCKED — Step 0b findings diverge from spec assumptions

Per `CC_MULTI_SPEC_PROTOCOL.md` Section "🛑 WHEN TO STOP AND REPORT TO
DEVELOPER" — stop immediately when a mandatory Step 0 grep (or 0b
research) reveals the codebase/external-API is in a different state
than the spec assumes. Also per the run instructions' Hard Rule 3:
**"Step 0b is mandatory for 154-S — do not guess parameter names"**.

---

## What Step 0b Found

**Environment limitation:** `REPLICATE_API_TOKEN` is not exported in
the local shell, so the Django shell SDK call returned HTTP 401 for
both models. I fell back to the Replicate web pages and third-party
documentation per the spec's fallback instruction ("If the shell
command fails, check the Replicate web pages directly").

### Finding 1 — Nano Banana 2 parameter is an ARRAY, not a single URL

Source: dev.to beginner's guide + community documentation — confirms
that `google/nano-banana-2` accepts:

- Parameter name: **`image_input`**
- Type: **Array of image URLs (up to 14)**
- Purpose: pass one or more reference/source images for transformation

**Conflict with spec:**

The spec's pseudocode for Change 1c:

```python
if reference_image_url and self.model_name in _MODEL_IMAGE_INPUT_PARAM:
    image_param = _MODEL_IMAGE_INPUT_PARAM[self.model_name]
    input_dict[image_param] = reference_image_url
```

This assigns the URL string directly. For Flux Dev that's (probably)
fine because it expects a single string. For Nano Banana 2 with
`image_input`, the API expects a list — `[reference_image_url]`, not
the bare string. Sending a string where an array is expected will
almost certainly return 422 or 400.

**Required spec amendment:** The pseudocode must differentiate single-URL
parameters from array parameters. Suggested amendment:

```python
_MODEL_IMAGE_INPUT_PARAM = {
    'black-forest-labs/flux-dev':  ('image',       'single'),
    'google/nano-banana-2':        ('image_input', 'array'),
}
...
if reference_image_url and self.model_name in _MODEL_IMAGE_INPUT_PARAM:
    param, kind = _MODEL_IMAGE_INPUT_PARAM[self.model_name]
    input_dict[param] = (
        [reference_image_url] if kind == 'array' else reference_image_url
    )
```

### Finding 2 — `black-forest-labs/flux-dev` may NOT support image input

Source: Hugging Face discussion #14 for FLUX.1-dev, Replicate search
results, fal.ai img2img docs.

- The **official** `black-forest-labs/flux-dev` Replicate model is
  documented purely as text-to-image. No confirmed `image` input
  parameter in its public schema.
- FLUX img2img is available via:
  - Hugging Face `FluxImg2ImgPipeline` (PIL/diffusers — not Replicate)
  - Third-party Replicate forks (e.g. `lucataco/flux-dev-img2img`)
  - fal.ai's `FLUX.1-dev img2img` endpoint (uses `image_url` parameter)
- No public documentation confirms `image` as an accepted input on the
  official `black-forest-labs/flux-dev` Replicate endpoint.

**Conflict with spec:**

The spec states "The expected parameter name for Flux Dev is `image`
(URL string)." This assumption appears unverified and may be wrong.
If we ship `_MODEL_IMAGE_INPUT_PARAM = {'black-forest-labs/flux-dev':
'image', ...}` and the API rejects the unknown parameter, Flux Dev
generation will fail silently or with 422 for every reference-image job.

The spec's own language allows for this: *"The parameter name for
Nano Banana 2 must be confirmed before coding. DO NOT PROCEED with
coding until Step 0b confirms the exact parameter names."*

### Finding 3 — Nano Banana 2 was already seeded `supports_reference_image = True` in 154-O

Memo: per the spec, Nano Banana 2's UI toggle is already on. This
means the UI currently allows users to upload reference images for
Nano Banana 2, but the backend silently drops them. Shipping the
wrong parameter wiring would turn "silently dropped" into
"silently dropped + API error" — a net negative.

---

## What I Need From You Before Coding

1. **Decision on Nano Banana 2 array wiring.** Approve the amended
   `(param, kind)` tuple approach above, or direct me to a simpler
   alternative (e.g. always wrap in array if model name contains
   "nano-banana").

2. **Clarification on Flux Dev.** Three options:
   - (a) You have verified access to Replicate and can run the shell
     command yourself, then paste me the exact parameter name.
   - (b) Drop Flux Dev from 154-S scope entirely. Only wire Nano Banana
     2 (confirmed `image_input` array). Update the seed: Flux Dev
     stays `supports_reference_image = False`.
   - (c) Point me to a specific Replicate docs page or code sample
     that confirms the parameter name on the *official*
     `black-forest-labs/flux-dev` model.

3. **Preferred next step.** Await your clarification and then proceed
   with amended spec, OR skip 154-S this batch and move it to a later
   batch with a dedicated Step 0b verification session.

---

## What Has Been Done So Far for 154-S

- ✅ Step 0 reads of `replicate_provider.py`, `seed_generator_models.py`, template file
- ✅ Step 0b attempted via Django shell (failed — missing token)
- ✅ Step 0b fallback via web docs + search (see findings above)
- ❌ Change 1a (docstring update) — NOT DONE
- ❌ Change 1b (_MODEL_IMAGE_INPUT_PARAM dict) — NOT DONE
- ❌ Change 1c (wire reference image in input_dict) — NOT DONE
- ❌ Change 2 (flux-dev seed flip) — NOT DONE
- ❌ Agent review — NOT RUN
- ❌ Commit — NOT MADE

No code changes were made for 154-S. `replicate_provider.py` and
`seed_generator_models.py` are in their pre-154-S state.

---

## Why This Is A Protocol-Correct Stop

Quoting `CC_MULTI_SPEC_PROTOCOL.md`:

> Stop immediately and report before continuing if ANY of the
> following occur: ... A mandatory Step 0 grep reveals the codebase is
> in a different state than the spec assumes (e.g. a function the spec
> references does not exist)

And from the run instructions:

> **Step 0b is mandatory for 154-S — do not guess parameter names**
> If Step 0b shell fails, check Replicate web API docs before coding

Both conditions apply. Proceeding without clarification risks shipping
a silent production regression for Nano Banana 2 reference-image jobs
and an unverified parameter name for Flux Dev.

---

## Agent Ratings

N/A — no implementation was attempted. Agent review gate not reached.

---

**Awaiting developer clarification before resuming 154-S.**
