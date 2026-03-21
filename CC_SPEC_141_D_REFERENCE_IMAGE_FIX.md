# CC_SPEC_141_D_REFERENCE_IMAGE_FIX.md
# Fix Reference Image — Pass to OpenAI GPT-Image-1 API

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 141
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~30 lines in `openai_provider.py`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`openai_provider.py` is ✅ Safe** — normal editing
4. **This is a feature that has NEVER worked** — the reference image has
   always been silently ignored since the provider was built

---

## 📋 OVERVIEW

The `generate()` method in `OpenAIImageProvider` receives `reference_image_url`
as a parameter but NEVER uses it. The `client.images.generate()` call sends
only `model`, `prompt`, `size`, `quality`, and `n=1`. The reference image is
silently dropped every time.

**The correct API call** (confirmed from OpenAI GPT-Image-1 documentation):

```javascript
// JavaScript example from OpenAI docs
const result = await openai.images.generate({
  model: "gpt-image-1",
  prompt: "A man matching the appearance of the reference image speaking at a podium",
  images: [referenceImageFile],  // File-like object, not a URL
  size: "1024x1024"
});
```

**In Python:** The `images` parameter expects a list of file-like objects
(not URLs). The reference image URL must be fetched and converted to a
`BytesIO` file-like object before passing to the API.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full generate() method to see exact current state
cat prompts/services/image_providers/openai_provider.py

# 2. Check what HTTP libraries are available in the project
grep -rn "^import requests\|^import httpx\|^import urllib\|from requests\|from httpx" \
    prompts/services/image_providers/openai_provider.py \
    prompts/tasks.py | head -10

# 3. Check how other parts of the codebase download external images
grep -n "_download_and_encode_image\|urllib.request\|requests.get\|httpx.get" \
    prompts/tasks.py | head -10

# 4. Read _download_and_encode_image for reference pattern
grep -n "def _download_and_encode_image" prompts/tasks.py
# Then read that function:
# sed -n '<line>+50p' prompts/tasks.py  (use the line number found above)

# 5. Check OpenAI SDK version available
grep -n "openai" requirements.txt 2>/dev/null || \
grep -n "openai" Pipfile 2>/dev/null || \
pip show openai 2>/dev/null | grep Version

# 6. Confirm B2_CUSTOM_DOMAIN for allowed domain validation
grep -n "B2_CUSTOM_DOMAIN\|ALLOWED_REFERENCE_DOMAINS" \
    prompts/views/bulk_generator_views.py | head -5
```

**Do not proceed until all greps are complete.**
Use the download pattern from Step 0 grep 3/4 as the reference
implementation — match the existing codebase pattern exactly.

---

## 📁 STEP 1 — Update `generate()` to pass reference image

**File:** `prompts/services/image_providers/openai_provider.py`

The fix: when `reference_image_url` is provided, download the image bytes
and wrap in a `BytesIO` file-like object, then pass as `images=[...]` to
the API call.

**Find the current `generate()` method. The API call currently looks like:**

```python
            response = client.images.generate(
                model='gpt-image-1',
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
```

**Replace with:**

```python
            # Build base generation params
            gen_params = {
                'model': 'gpt-image-1',
                'prompt': prompt,
                'size': size,
                'quality': quality,
                'n': 1,
            }

            # If a reference image URL is provided, download and attach it.
            # GPT-Image-1 requires a file-like object, not a URL string.
            # This enables the model to use the reference image as visual context.
            if reference_image_url:
                try:
                    import io
                    import urllib.request as _urllib_req
                    req = _urllib_req.Request(
                        reference_image_url,
                        headers={'User-Agent': 'PromptFinder/1.0'}
                    )
                    with _urllib_req.urlopen(req, timeout=20) as _resp:
                        ref_bytes = _resp.read()
                    # Limit to 20MB to prevent runaway memory usage
                    if len(ref_bytes) > 20 * 1024 * 1024:
                        logger.warning(
                            "[REF-IMAGE] Reference image too large (%d bytes), skipping",
                            len(ref_bytes)
                        )
                    else:
                        ref_file = io.BytesIO(ref_bytes)
                        ref_file.name = 'reference.png'
                        gen_params['images'] = [ref_file]
                        logger.info(
                            "[REF-IMAGE] Attached reference image: %s",
                            reference_image_url
                        )
                except Exception as ref_exc:
                    # Non-fatal: proceed without reference image on any failure
                    logger.warning(
                        "[REF-IMAGE] Failed to download reference image %s: %s",
                        reference_image_url, ref_exc
                    )

            response = client.images.generate(**gen_params)
```

⚠️ From Step 0 grep 2, use the download pattern that already exists in the
codebase. If `urllib.request` is the standard pattern (as seen in tasks.py),
use it. If `requests` or `httpx` is used elsewhere, match that instead.

⚠️ The `images` parameter name is specific to the OpenAI Python SDK. From
Step 0 grep 5, verify the OpenAI SDK version supports this parameter for
GPT-Image-1. If the SDK is older and doesn't support `images`, check for
alternative parameter names in the SDK docs.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# Verify reference_image_url is now used in the generate method
grep -n "reference_image_url\|gen_params\|images.*ref_file\|REF-IMAGE" \
    prompts/services/image_providers/openai_provider.py

# Verify the fallback (no reference image) still works — gen_params without 'images'
grep -n "gen_params\[.images.\]\|gen_params\.get\|images.*gen_params" \
    prompts/services/image_providers/openai_provider.py
```

**Both greps MUST return results. Show the output in the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — download pattern identified
- [ ] Step 2 verification greps pass (show output in report)
- [ ] `reference_image_url` is now used inside `generate()`
- [ ] Download uses the same pattern as the rest of the codebase
- [ ] 20MB size limit prevents memory issues
- [ ] On download failure: logs warning and proceeds WITHOUT reference image
- [ ] `gen_params['images']` only set when download succeeds
- [ ] `ref_file.name = 'reference.png'` set for SDK compatibility
- [ ] No change to the mock mode path
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @django-pro
- Verify the `BytesIO` + `.name` pattern is correct for the OpenAI Python SDK
- Verify `urllib.request` usage is consistent with the codebase pattern
- Verify the timeout (20s) is appropriate for a background worker context
- Verify the non-fatal exception handling is correctly structured
- Rating requirement: 8+/10

### 2. @security-auditor
- **SSRF risk:** The `reference_image_url` is fetched server-side from the
  `openai_provider.py` worker. This URL comes from `job.reference_image_url`.
  Verify where `reference_image_url` is validated before reaching this point —
  check if `ALLOWED_REFERENCE_DOMAINS` validation happens in the view layer
  before the job is created. If it does, confirm it's sufficient.
- Verify 20MB size limit prevents memory exhaustion attacks
- Verify the `User-Agent` header doesn't expose internal system details
- Rating requirement: 8+/10

### 3. @code-reviewer
- **Verify Step 2 verification greps are shown in report**
- Verify generation still works correctly when `reference_image_url` is empty
  (no `images` key in `gen_params` — confirm with grep that the key is only
  set inside the `if reference_image_url:` block)
- Verify the existing mock mode path is completely unchanged — `_generate_mock`
  must not be affected by this change
- Verify `python manage.py test prompts.tests.test_bulk_generator` passes —
  show the test output in the report
- Verify no import added at the module level that wasn't there before
  (all new imports must be inside the function)
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `reference_image_url` parameter still not used in `client.images.generate()`
- Download failure causes generation to fail (must be non-fatal)
- No size limit on reference image download

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test prompts.tests.test_bulk_generator
```

**Manual verification (Mateo — after deploying to Heroku):**
1. Open the bulk generator input page
2. Upload a reference image (the face/character upload at the top)
3. Enter a prompt like: "The person from the reference image standing at a podium giving a speech, cinematic lighting, 8K"
4. Generate
5. Check Heroku logs: `heroku logs --app mj-project-4 --num 100 | grep "REF-IMAGE"`
   → Verify `[REF-IMAGE] Attached reference image:` entry appears
6. Verify the generated image shows the correct person/character from the
   reference image rather than a random person

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): pass reference image to GPT-Image-1 API (was silently ignored since feature was built)
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_141_D_REFERENCE_IMAGE_FIX.md`

**Section 3 MUST include Step 2 verification grep output.**

---

**END OF SPEC**
