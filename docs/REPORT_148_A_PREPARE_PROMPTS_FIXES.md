# REPORT: 148-A — Prepare Prompts Fixes

## Section 1 — Overview

Session 147 introduced the prepare-prompts pipeline (translate + watermark removal) but it
was failing with 401 errors in production because `OPENAI_API_KEY` existed as a Heroku config
var but was never wired into Django `settings.py`. This spec fixes the 401, adds a translation
toggle so users can opt out of auto-translation, and adds scroll+shake UX to the tier
confirmation error so users are directed to the area requiring attention.

## Section 2 — Expectations

- ✅ `OPENAI_API_KEY` wired in `settings.py` via `os.environ.get`
- ✅ Translation toggle added to Column 4, matches Visibility toggle structure
- ✅ Toggle defaults to checked (On)
- ✅ Label updates between "On" / "Off" on change
- ✅ `@keyframes bg-tier-shake` added to CSS with `prefers-reduced-motion` suppression
- ✅ Tier error scrolls to `#tierSection` (smooth or auto based on motion preference)
- ✅ `tierConfirmPanel` shakes via `is-shaking` class with reflow trick
- ✅ `translate` flag sent in prepare-prompts payload
- ✅ View reads `translate` flag and conditionally skips translation in system prompt

## Section 3 — Changes Made

### prompts_manager/settings.py
- Line 45-47: Added `OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')` with comment
  explaining it is the platform key (not BYOK)

### prompts/templates/prompts/bulk_generator.html
- Lines 168-182: Added translation toggle (`bg-setting-group`) to Column 4, after Visibility
  toggle and before Reset button. Uses identical structure: `bg-visibility-card`,
  `bg-toggle-switch`, `bg-toggle-slider`. Checkbox `id="settingTranslate"` with
  `aria-labelledby="translateGroupLabel translateLabel"`. Defaults to `checked`. Includes
  `bg-setting-hint` with explanation text.

### static/css/pages/bulk-generator.css
- Lines 1190-1210: Added `@keyframes bg-tier-shake` (damped translateX oscillation),
  `.bg-tier-confirm-panel.is-shaking` rule (0.5s ease-in-out), and
  `@media (prefers-reduced-motion: reduce)` block setting `animation: none`.

### static/js/bulk-generator.js
- Lines 48-49: Added `I.settingTranslate` and `I.translateLabel` refs via `getElementById`
- Lines 636-640: Added change listener on `settingTranslate` — updates label text "On"/"Off".
  Guarded with `if (I.settingTranslate)`.

### static/js/bulk-generator-generation.js
- Lines 604-636: Replaced tier error block. Now scrolls to `#tierSection` using
  `scrollIntoView` with `behavior: reducedMotion ? 'auto' : 'smooth'`. Shakes
  `tierConfirmPanel` by removing/re-adding `is-shaking` class with reflow trick
  (`void offsetWidth`). Class removed after 600ms. Error message simplified.
- Line 755: Prepare fetch body now sends `translate: I.settingTranslate ? I.settingTranslate.checked : true`
  (falls back to `true` if toggle absent).

### prompts/views/bulk_generator_views.py
- Line 671: Added `translate = bool(data.get('translate', True))`
- Lines 689-696: System prompt Task 1 now includes conditional: "Only perform this task if
  the input JSON includes `"translate": true`. If `"translate": false` — skip translation."
- Lines 798-801: User message now includes `'translate': translate` in the JSON payload.

### Step 8 Verification Grep Outputs

```
# 1. OPENAI_API_KEY in settings.py
47:OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# 2. Translation toggle in template
169:  <span class="bg-setting-label" id="translateGroupLabel">Translate to English</span>
172:  <span class="bg-visibility-label" id="translateLabel">On</span>
175:  <input type="checkbox" id="settingTranslate"
176:         aria-labelledby="translateGroupLabel translateLabel"

# 3. Shake animation in CSS
1192:@keyframes bg-tier-shake {
1202:.bg-tier-confirm-panel.is-shaking {
1203:    animation: bg-tier-shake 0.5s ease-in-out;
1207:    .bg-tier-confirm-panel.is-shaking {

# 4. Scroll + shake in JS
609:  var tierSection = document.getElementById('tierSection');
614:  tierSection.scrollIntoView({
622:  I.tierConfirmPanel.classList.remove('is-shaking');
625:  I.tierConfirmPanel.classList.add('is-shaking');

# 5. Translate flag in prepare fetch
755:  translate: I.settingTranslate ? I.settingTranslate.checked : true,

# 6. Translate flag in view
671:    translate = bool(data.get('translate', True))
```

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

**Issue:** `aria-describedby` not added to translate checkbox for the hint text.
**Recommended fix:** Add `id="translateHint"` to the hint span and
`aria-describedby="translateHint"` to the checkbox input in `bulk_generator.html`.
**Priority:** P3
**Reason not resolved:** Consistent with existing Visibility toggle pattern which also
lacks `aria-describedby`. Flagged by accessibility agent but not in spec scope.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `role="alert"` and `aria-live="assertive"` are both set on the error banner
(pre-existing pattern). Some older screen readers may double-announce.
**Impact:** Minor — most modern screen readers handle this correctly.
**Recommended action:** Audit all `showGenerateErrorBanner` usages in a future a11y pass
and remove the redundant `aria-live="assertive"` where `role="alert"` is already present.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | OPENAI_API_KEY correctly wired, translate flag read with sensible default, getattr fallback now resolves. Minor: bool() cast redundant but harmless. | No — cosmetic only |
| 1 | @frontend-developer | 9.2/10 | Toggle matches Visibility structure exactly, shake CSS well-formed, reduced-motion suppresses correctly. Minor: hint creates slight height asymmetry vs Visibility toggle. | No — intentional (translation needs explanation) |
| 1 | @javascript-pro | 9.5/10 | Reflow trick correct, 600ms timeout appropriate (100ms buffer over 500ms animation), translate fallback to true is correct opt-out pattern. | N/A — no issues |
| 1 | @accessibility (code-reviewer) | 8.5/10 | aria-labelledby pattern correct, reduced-motion respected in CSS and JS scroll, no focus trap. Minor: missing aria-describedby on hint, redundant aria-live on banner (pre-existing). | No — P3 deferred items |
| **Average** | | **9.05/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value
for this spec.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=1
# Expected: 1213 tests, 0 failures, 12 skipped
```

**Manual browser steps (Mateo):**
1. Select Tier 2, click Generate without confirming → page scrolls to tier section,
   panel shakes, red banner appears
2. Translation toggle ON + Spanish prompt → Generate → logs show
   `[PREPARE-PROMPTS] Prepared X prompts` (no 401 error)
3. Translation toggle OFF + Spanish prompt → Generate → prompt unchanged
   (watermark removal still runs)
4. Toggle label switches between "On" and "Off" correctly

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 5429852 | fix(bulk-gen): wire OPENAI_API_KEY, scroll/shake on tier error, translation toggle |

## Section 11 — What to Work on Next

1. Add `aria-describedby` to translate checkbox hint — P3 accessibility improvement
2. Audit `showGenerateErrorBanner` for redundant `aria-live`/`role="alert"` — P3 a11y pass
3. Browser-verify translation toggle ON/OFF behaviour in production (Mateo)
