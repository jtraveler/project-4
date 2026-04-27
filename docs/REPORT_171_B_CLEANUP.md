# REPORT_171_B_CLEANUP

## Cleanup — Quality Labels, Try-In URLs, 170-B P2/P3

**Spec:** `CC_SPEC_171_B_CLEANUP.md`
**Cluster shape:** BATCHED (Memory Rule #15)
**Partial report:** Sections 1–8 + 11 written now; Sections 9–10 filled after full suite gate per CC_MULTI_SPEC_PROTOCOL v2.2.

---

## Section 1 — Overview

Four cleanup items addressed in a single spec:

1. **Quality label override (Nano Banana 2 → 1K/2K/4K):** Per-generator
   `quality_label_map` field added to `AI_GENERATORS['nano-banana-2']`.
   Surfaces a coherent UI between the input page (already hardcoded
   1K/2K/4K via `bulk-generator.js:1003-1037`) and the job results page
   (now reads the same map via `G.formatQualityLabel`). Other generators
   continue to render Low/Medium/High via the default capitalize fallback.

2. **AI_GENERATORS website URL audit:** All 7 bulk-gen entries' `website`
   URLs verified via WebFetch / WebSearch and replaced with the official
   model-owner page (or fallback to model-owner root when the specific
   page no longer exists).

3. **170-B P3 (auth wording divergence):** The typed-error map at
   `bulk-generator-config.js:111` and the legacy `reasonMap` at line 141
   previously diverged ("Authentication failed — update your API key."
   vs "Invalid API key — check your key and try again."). Unified both
   to the typed-map value to prevent confusion when a backend returns
   the legacy `'Authentication error'` sanitised string.

4. **170-B P2 (Done auto-focus guard):** `setPublishModalTerminal` now
   guards against `doneBtn` already having focus before calling `.focus()`,
   preventing screen-reader announcement thrash when the terminal-state
   path re-enters (e.g., retry-after-failure → second terminal call).

## Section 2 — Expectations

| Spec criterion | Outcome |
|----------------|---------|
| Add `quality_label_map` to `AI_GENERATORS['nano-banana-2']` | ✅ Met |
| Other generators omit the field (default fallback preserved) | ✅ Met (verified by `@code-reviewer`, `@frontend-developer`) |
| Audit and update all 7 bulk-gen `website` URLs via web fetch | ✅ Met (verbatim evidence in Section 4) |
| Unify auth wording | ✅ Met (`bulk-generator-config.js:141` updated) |
| Done auto-focus guard | ✅ Met (`bulk-generator-selection.js:399-401`) |
| `python manage.py check` 0 issues | ✅ Met |
| str_replace counts within ✅ Safe tier | ✅ Met (constants.py 8, view 2, template 1, config.js 3, polling.js 1, ui.js 2, selection.js 1) |
| No regressions in `test_bulk_generator` suite | ⏸ To verify at full suite gate (Section 9) |

### Step 0 verification (verbatim outputs)

```
$ grep -n "AI_GENERATORS\s*=" prompts/constants.py
11:AI_GENERATORS = {

$ wc -l prompts/constants.py
     585 prompts/constants.py
(✅ Safe tier — under 800 lines)

$ grep -n "_NANO_BANANA_RESOLUTION_MAP\|'1K'\|'2K'\|'4K'" prompts/services/image_providers/replicate_provider.py | head -5
65:_NANO_BANANA_RESOLUTION_MAP: dict[str, str] = {
66:    'low': '1K',       # $0.067/image
67:    'medium': '2K',    # $0.101/image
68:    'high': '4K',      # $0.151/image
73:    '1K': 0.067,
(Confirms backend already maps low→1K, medium→2K, high→4K — UI label
 should align with cost calculation source of truth.)

$ grep -n "Authentication failed\|Invalid API key" static/js/bulk-generator-config.js
(pre-fix)
111:                'auth':            'Authentication failed — update your API key.',
140:            'Authentication error':     'Invalid API key — check your key and try again.',
(divergence confirmed)

$ grep -n "setPublishModalTerminal\|doneBtn.focus" static/js/bulk-generator-selection.js
374:    G.setPublishModalTerminal = function (failedCount, publishedCount, total) {
395:            if (closeBtn !== document.activeElement) doneBtn.focus();
(target line 395 confirmed)
```

### Step 0 web fetches (verbatim — captured 2026-04-26)

| Generator | Old URL | Verified URL | Method | Outcome |
|-----------|---------|--------------|--------|---------|
| `grok-imagine` | `https://x.ai` | `https://x.ai/api/imagine` | WebSearch (xAI direct fetch returned 403; WebSearch returned official xAI URLs) | xAI's official Grok Imagine API page. Strongest signal: `x.ai/api/imagine` ranked #2 result on a "Grok Imagine official product page 2026" search; the `news/grok-imagine-api` page was #1 but is a launch-announcement page (less stable as a long-term `website` value). |
| `gpt-image-1-5-byok` | `https://openai.com` | `https://platform.openai.com/docs/models/gpt-image-1.5` | WebSearch site:openai.com | Official OpenAI model docs page. Top hit: `https://platform.openai.com/docs/models/gpt-image-1.5`. Includes per-quality/size pricing data referenced in CLAUDE.md Session 153-C. |
| `flux-schnell` | `https://blackforestlabs.ai` | `https://bfl.ai/` | WebFetch (301 redirect from `blackforestlabs.ai` → `bfl.ai/`) + content inspection | BFL homepage now shows current FLUX.2 family (klein, max, pro, flex) but **does NOT document older variants** (Flux Schnell, Flux Dev, Flux 1.1 Pro). Per spec decision rule, falls back to model-owner root official page. |
| `flux-dev` | `https://blackforestlabs.ai` | `https://bfl.ai/` | Same as above | Same fallback. |
| `flux-1-1-pro` | `https://blackforestlabs.ai` | `https://bfl.ai/` | Same as above | Same fallback. |
| `flux-2-pro` | `https://blackforestlabs.ai` | `https://bfl.ai/` | Same as above | BFL homepage does mention "FLUX.2 [pro]" as a variant in the model selector. Model comparison URL `/models/flux-2-max#comparison` exists but is comparison-focused rather than a single-model landing page. Root URL is the safer fallback. |
| `nano-banana-2` | `https://nanobanana.ai` | `https://gemini.google/overview/image-generation/` | WebFetch (nanobanana.ai → ECONNREFUSED; gemini.google page resolves and explicitly mentions "Nano Banana 2 ist da") + WebSearch | Old URL is unreachable. Confirmed via WebSearch + WebFetch that Nano Banana 2 is a Google DeepMind / Gemini model and the canonical official URL is the Gemini image-generation overview page, which prominently features Nano Banana 2 by name. Mateo's spec-stated preference matches verified evidence. |

### Post-fix verification (verbatim)

```
$ sed -n '344,440p' prompts/constants.py | grep "'website':"
        'website': 'https://x.ai/api/imagine',
        'website': 'https://platform.openai.com/docs/models/gpt-image-1.5',
        'website': 'https://bfl.ai/',
        'website': 'https://bfl.ai/',
        'website': 'https://bfl.ai/',
        'website': 'https://bfl.ai/',
        'website': 'https://gemini.google/overview/image-generation/',

$ grep -A 12 "'nano-banana-2': {" prompts/constants.py | head -14
'nano-banana-2': {
        'name': 'Nano Banana 2',
        'slug': 'nano-banana-2',
        'seo_subheader': 'Nano Banana 2 AI Image Examples',
        'seo_description': 'Browse Nano Banana 2 prompts on PromptFinder.',
        'description': '<p>Nano Banana 2 is a stylized AI image generation model powered by Google\'s Gemini.</p>',
        'website': 'https://gemini.google/overview/image-generation/',
        'icon': 'images/generators/nano-banana-icon.png',
        'choice_value': 'nano-banana-2',
        'supports_images': True,
        'supports_video': False,
        # Per-generator quality label override. Replicate's Nano Banana 2 uses
        # resolution tiers (1K/2K/4K) rather than perceptual quality (Low/

$ grep -n "Authentication failed\|Invalid API key" static/js/bulk-generator-config.js
112:                'auth':            'Authentication failed — update your API key.',
141:            'Authentication error':     'Authentication failed — update your API key.',
(unified — both branches now use the same wording)

$ grep -B 2 -A 5 "doneBtn\.focus" static/js/bulk-generator-selection.js
            // Move focus to Done button so keyboard users can dismiss easily.
            // 170-B P2: also guard against re-focusing if Done already has focus
            // (prevents focus thrash mid-screen-reader-announcement on terminal
            // state re-entry — possible if a previous polling cycle's terminal
            // path already focused Done before a retry triggered another).
            if (closeBtn !== document.activeElement
                && doneBtn !== document.activeElement) {
                doneBtn.focus();
            }
        }

$ python manage.py check
System check identified no issues (0 silenced).
```

## Section 3 — Changes Made

### prompts/constants.py
- **Line 355:** `'website': 'https://x.ai'` → `'website': 'https://x.ai/api/imagine'`
- **Line 367:** `'website': 'https://openai.com'` → `'website': 'https://platform.openai.com/docs/models/gpt-image-1.5'`
- **Line 379:** `'website': 'https://blackforestlabs.ai'` (flux-schnell) → `'website': 'https://bfl.ai/'`
- **Line 391:** Same change for `flux-dev`
- **Line 403:** Same change for `flux-1-1-pro`
- **Line 415:** Same change for `flux-2-pro`
- **Line 427:** `'website': 'https://nanobanana.ai'` → `'website': 'https://gemini.google/overview/image-generation/'`
- **Lines 432-440 (added):** New `quality_label_map: {'low':'1K','medium':'2K','high':'4K'}` field on `'nano-banana-2'` entry, with 7-line explanatory comment documenting why Nano Banana 2 uses resolution tiers and that omission falls back to default Low/Medium/High.

### prompts/views/bulk_generator_views.py
- **Lines ~192-202 (added):** New `quality_label_map_json` lookup. Imports `AI_GENERATORS` (function-level, mirrors existing `GeneratorModel` import pattern), derives `_gen_slug` from `_gen_model.slug`, computes `json.dumps(_AI_GENERATORS.get(_gen_slug, {}).get('quality_label_map', {}))`. Defensive double-`.get()` chain returns `{}` for any missing key.
- **Line ~218 (added):** `'quality_label_map_json': quality_label_map_json,` in render context dict.

### prompts/templates/prompts/bulk_generator_job.html
- **Line 30 (added):** `data-quality-label-map="{{ quality_label_map_json }}"` attribute on `#bulk-generator-job` div, between `data-provider` and `data-create-pages-url`.

### static/js/bulk-generator-config.js
- **Line 74 (added):** `G.qualityLabelMap = {};` state initialization.
- **Lines 153-165 (added):** New `G.formatQualityLabel(quality)` helper that maps via `G.qualityLabelMap[quality]` first, falls back to `quality.charAt(0).toUpperCase() + quality.slice(1)`. Handles falsy input with empty-string return.
- **Line 141:** Auth wording unified — `'Invalid API key — check your key and try again.'` → `'Authentication failed — update your API key.'` to match the typed-map equivalent at line 112.

### static/js/bulk-generator-polling.js
- **Lines 347-355 (added):** `initPage` now reads `G.root.dataset.qualityLabelMap` and parses JSON via try/catch (defaults to `{}` on parse error or missing attribute). Set BEFORE the `aria-live` announcer creation so all subsequent `G.formatQualityLabel` calls see the populated map.

### static/js/bulk-generator-ui.js
- **Lines ~395-401 (`createGroupRow`):** Per-prompt-group meta now uses `G.formatQualityLabel(groupQuality)` instead of inline capitalize. Job-level fallback (when groupQuality empty) routes through `G.formatQualityLabel(G.jobQuality.toLowerCase())` first, falls back to `G.qualityDisplay` (raw server-rendered get_quality_display) only if both fail. Five-line comment documents intent.
- **Lines ~552-563 (`updateHeaderStats`):** Quality column "Mixed"/single-quality logic now branches: when only one distinct quality present (still an override case), renders that quality's label via `G.formatQualityLabel(qualKeys[0])` so Nano Banana 2 shows "1K"/"2K"/"4K" instead of generic "Mixed". Two+ distinct qualities still get "Mixed".

### static/js/bulk-generator-selection.js
- **Lines 394-401 (`setPublishModalTerminal`):** Done auto-focus call now compound-guards `closeBtn !== document.activeElement && doneBtn !== document.activeElement` before `doneBtn.focus()`. Four-line comment cites Sessions 138-C / 139-B / 170-B P2 as the recurring-miss precedent.

## Section 4 — Issues Encountered and Resolved

**Issue:** WebFetch of `https://x.ai`, `https://openai.com`, and
`https://nanobanana.ai` returned non-200 results (xAI and OpenAI: 403
Cloudflare bot block; nanobanana.ai: ECONNREFUSED).

**Root cause:** Cloudflare bot detection blocks automated WebFetch
requests on the major AI provider sites. nanobanana.ai appears defunct
(connection refused, not just 403).

**Fix applied:** Switched to WebSearch for the three blocked URLs, which
returned official site:domain results from each model owner. Used the
search-result URLs as the verification source (with explicit per-result
confirmation that each is from the model owner's domain). For BFL, the
WebFetch followed the 301 redirect from `blackforestlabs.ai` to
`bfl.ai/` and the redirect target resolved successfully — used that.

**File:** N/A (Step 0 evidence-gathering issue, not a code issue).

**Issue:** Per-generator URL fallback decision needed for the 4 BFL
entries (Flux Schnell / Dev / 1.1 Pro / 2 Pro).

**Root cause:** BFL's current homepage (`bfl.ai/`) only documents the
FLUX.2 family (klein/max/pro/flex) and no longer enumerates older
variants. The previously-used `https://blackforestlabs.ai` redirected
to the same root, so URL granularity loss is upstream-imposed.

**Fix applied:** All 4 BFL entries fall back to `https://bfl.ai/` per
spec section 4 decision rule ("If the URL returns 404 / redirects to a
marketing landing page that obscures the model / is otherwise
unofficial, fall back to the model owner's root official page").
Documented in Section 2 web-fetch table.

**File:** `prompts/constants.py` lines 379, 391, 403, 415.

**Issue:** Three `{# %}` → `{% comment %}` template conversions are
visible in the `bulk_generator_job.html` diff that appears in Spec B's
agent reviews.

**Root cause:** Spec A landed those changes earlier in this session.
Both specs' commits are HOLD until full suite gate; agents reviewing
Spec B saw the cumulative diff including Spec A's changes.

**Fix applied:** No fix needed — the changes are scoped to Spec A's
commit (per per-spec commit isolation in CC_MULTI_SPEC_PROTOCOL v2.2).
Each spec gets exactly one commit. The agent observation is correctly
flagged in Section 6 below for transparency.

**File:** `prompts/templates/prompts/bulk_generator_job.html` (Spec A
edits — already covered in `REPORT_171_A_COMMENT_FIX.md`).

## Section 5 — Remaining Issues

No remaining issues against Spec B's stated objectives. All four cleanup
items are complete and verified.

The input-page hardcoded 1K/2K/4K swap (`bulk-generator.js:1003-1037`)
was NOT refactored to consume `G.qualityLabelMap`. The spec scope
explicitly bounded the implementation to the JS surfaces on the JOB
RESULTS page; the input page already produces the correct labels via
hardcode (it predates the centralized map). Refactoring the input-page
hardcode to consume the centralized map is a P3 candidate captured in
Section 6.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Input-page (`bulk-generator.js:1003-1037`) hardcodes
1K/2K/4K labels for Nano Banana 2 instead of consuming the new
centralized `G.qualityLabelMap` from `AI_GENERATORS['nano-banana-2']`.

**Impact:** Two sources of truth for the same data. If a future
generator gains a custom label map (e.g. FLUX.2 with byte-tier names)
the input-page logic would need to be updated separately from the
constants. Drift risk is low today (only Nano Banana 2 has a label
map) but compounds as more generators get added.

**Recommended action:** P3 follow-up — refactor `bulk-generator.js`
input-page label swap to consume `AI_GENERATORS[slug].quality_label_map`
via a data attribute injected by the template. Defer until at least one
more generator gains a label map (no practical drift risk before then).

---

**Concern:** Function-level imports in `bulk_generator_views.py`
(`from prompts.constants import AI_GENERATORS as _AI_GENERATORS` and
`from prompts.models import GeneratorModel as GenModel`) could be
hoisted to module-top imports for cleaner organization.

**Impact:** Style-only — no circular-import risk because both modules
are stable consumers of view-side state. The current pattern matches
the existing line-186 precedent so was preserved for consistency.

**Recommended action:** Leave as-is unless a broader views.py
refactor pass touches the import block. Surface as a P3 micro-cleanup
candidate.

---

**Concern (raised by `@accessibility-expert` review):** Verify in QA
that `closeBtn` and `doneBtn` are queried fresh inside
`setPublishModalTerminal` rather than cached at modal-init time.

**Impact:** If references were cached and the DOM re-rendered, the
focus guard would silently bypass. Examined the code — both refs ARE
queried fresh at `setPublishModalTerminal` entry (lines 376-377). Safe.

**Recommended action:** None needed — already correct.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 9.0/10 | All 7 URL updates verified against captured evidence; auth wording unified; Done focus guard correct; scope discipline preserved; flagged that Spec A's `{% comment %}` conversions appear in the diff (cross-spec context) | Yes — documented in Section 4 |
| 1 | @frontend-developer | 9.0/10 | `G.formatQualityLabel` is clean and correct; falsy guard handles null/undefined; both per-group and header consume helper; default behavior preserved for non-overriding generators; Django auto-escape + browser dataset un-escape chain correctly handles JSON; Done focus guard compound condition handles all four states | N/A — defensive double-check `G.qualityLabelMap && ...` is harmless redundancy; no action needed |
| 1 | @django-pro | 9.0/10 | AI_GENERATORS shape consistency preserved; `.get()` chain safely handles missing slug AND missing field; `json.dumps({})` safe; function-level import pattern matches existing line-186 precedent; no migration needed | N/A — non-blocking observation about hoisting imports captured in Section 6 |
| 1 | @accessibility-expert (sub via general-purpose) | 9.0/10 | Label semantics preserve meaning (1K/2K/4K is established convention); focus guard is textbook fix for screen-reader announcement thrash; first-entry behavior preserves UX; no ARIA regression; recurring-miss pattern (Sessions 138-C, 139-B, 170-B) explicitly cited in code comment per substitution recommendation | Yes — code comment was already added at edit time citing 170-B P2 |
| **Average** | | **9.0/10** | | **Pass ≥ 8.0** ✅ |

Substitution disclosure: `@accessibility-expert` substituted with
`general-purpose` running an accessibility-expert persona, per the
project's documented Agent Substitution Convention.

## Section 8 — Recommended Additional Agents

All required agents per spec section 9 were used. No additional agents
would have added material value — the change is well-bounded to dict
data, view context, template attribute, and JS state-management.

## Section 9 — How to Test

### Automated

```bash
python manage.py test
# Result: Ran 1396 tests in 665.816s. OK (skipped=12).
# 0 failures, 0 errors. No regressions from Spec B's view-context
# injection, JS module additions, or auth-wording / Done-focus-guard
# changes.
```

### Memory Rule #14 closing checklist for this spec

**Migrations to apply:** N/A — no DB changes in 171-B.

**Manual browser tests (max 2 at a time, with explicit confirmation
between each):**

Round 1 (Try-in URLs):
1. Click each "Try in [model]" link on a published prompt detail page
   — verify each resolves to the official model owner's page (no
   404, no marketing aggregator)
2. Specifically test: Grok Imagine → `x.ai/api/imagine`, GPT-Image-1.5
   → `platform.openai.com/docs/models/gpt-image-1.5`, all 4 Flux
   variants → `bfl.ai/`, Nano Banana 2 → `gemini.google/overview/image-generation/`

Round 2 (Quality labels):
1. Run a small Nano Banana 2 bulk job at "Medium" quality (= 2K) →
   verify job results page shows "2K" in the Quality column AND in
   each prompt-group meta row (not "Medium")
2. Run a small Flux Schnell or Grok job at any quality → verify job
   results page still shows "Low"/"Medium"/"High" capitalize labels
   (default fallback behavior preserved)

Round 3 (Auth wording):
1. Trigger an OpenAI auth failure (e.g., expired BYOK key) → verify
   the per-card error reason text reads "Authentication failed —
   update your API key." (not "Invalid API key — check your key and
   try again.")

Round 4 (Done focus guard — keyboard navigation):
1. Run a small bulk job with one image that fails to publish → after
   publish completes, verify Done button receives focus once and
   keyboard Enter activates it
2. Trigger Retry Failed → verify Done button does NOT re-focus
   mid-announcement (test with VoiceOver or NVDA enabled if possible)

**Failure modes to watch for:**
- If Nano Banana 2 still shows "Medium"/"High" labels after deploy,
  hard-refresh to bust cached `bulk-generator-job.css` or template.
- If new Try-in URLs 404 → BFL or Google may have moved pages
  again; re-verify and update.
- If Done auto-focus doesn't fire on first terminal entry, the guard
  may be too aggressive — should fire when neither btn is focused.

**Backward-compatibility verification:**
- Generators without `quality_label_map` MUST still render
  Low/Medium/High via the capitalize fallback. Verify with at least
  one Flux job and one Grok job.
- The `auth` typed-map at line 112 was not changed — only the legacy
  `reasonMap` value at line 141 was unified. Backend sanitised string
  `'Authentication error'` still maps to the same final reason text.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| `6a58ef9` | fix(bulk-gen): cleanup — quality labels, Try-in URLs, 170-B P2/P3 (Session 171-B) |

## Section 11 — What to Work on Next

1. Spec 171-C (GPT Image 2 BYOK integration) immediately follows in
   this session per the BATCHED cluster execution.
2. Post-deploy: Mateo verifies the four Round-of-2 manual tests above
   (Memory Rule #14).
3. P3 candidate from Section 6: refactor `bulk-generator.js` input-page
   label swap to consume `AI_GENERATORS[slug].quality_label_map` from
   the same single-source-of-truth dict. Defer until at least one more
   generator gains a custom quality label map.
4. P3 candidate from Section 6: hoist function-level imports in
   `bulk_generator_views.py` to module-top during the next broader
   views.py refactor pass.

---

**END OF REPORT_171_B_CLEANUP (PARTIAL)**
