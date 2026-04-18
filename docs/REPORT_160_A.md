# REPORT_160_A.md
# Spec 160-A — Profanity Error UX (Bold/Italic + Prompt Box Link)

**Session:** 160
**Date:** April 18, 2026
**Status:** ✅ Implementation complete, agents pass. Awaiting full suite before commit.

---

## Section 1 — Overview

Session 159-A introduced a profanity filter that surfaces triggered words to the
user, but the word list rendered as plain inline text and the error had no link
to the prompt box. The image-link validation error ("Source image URL for prompt
N is not a valid image link") already rendered a clickable "Prompt N" anchor
that scrolled to the box — profanity, empty, and duplicate errors should follow
the same pattern. Additionally, the triggered word(s) need to be styled bold
and italic so they stand out.

This spec extends the backend-to-frontend error contract:

- Backend `validate_prompts()` now attaches `prompt_num` (1-based) to every error
  dict, plus `flagged_words_display` (escaped, comma-joined) to profanity
  errors with non-empty `found_words`.
- Frontend `showValidationErrors()` normalizes the backend's snake_case
  `prompt_num` into the existing `promptNum` field, renders a clickable
  "Prompt N" link for every backend error (empty, profanity, duplicate), and
  renders the flagged word(s) in `<strong><em>…</em></strong>` built via the
  DOM API (no `innerHTML` — the message itself is never HTML-interpreted).

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Triggered word displayed in bold + italic | ✅ Met via `<strong><em>` DOM nodes |
| Profanity error links to prompt box (scroll + focus) | ✅ Met — same link mechanism as source-URL error |
| Empty and duplicate errors also get prompt link | ✅ Met (bonus — backend now attaches `prompt_num` to all errors) |
| `html.escape()` preserved on flagged words | ✅ Met — no regression from 159-A |
| Frontend avoids `innerHTML` for message content | ✅ Met — all rendering via `createElement`/`appendChild`/`textContent` |
| Existing tests still pass | ✅ Met — message format preserved |

---

## Section 3 — Changes Made

### prompts/services/bulk_generation.py
- Lines ~100–107: Expanded `validate_prompts` docstring to document the new
  `prompt_num` (int, 1-based) and `flagged_words_display` (conditional) fields.
- Lines ~114–120: Empty-prompt error now includes `prompt_num: i + 1`.
- Lines ~124–156: Profanity-error block restructured so `prompt_num` is always
  present; `flagged_words_display` is added only when `found_words` is
  non-empty (same list of escaped words that appears in `message`).
- Lines ~159–168: Duplicate-prompt error now includes `prompt_num: i + 1`.

### static/js/bulk-generator-generation.js
- Function `showValidationErrors` (around lines 550–625):
  - Read `promptNum = err.promptNum || err.prompt_num` into a local (avoids
    mutating the caller's error object).
  - When `err.flagged_words_display` is present, append structured nodes:
    em-dash + label text, then `<strong><em>word(s)</em></strong>`, then
    closing text. Built with `document.createElement` + `textContent` only.
  - Existing "Source image URL for prompt N" prefix stripping preserved.
  - New generic branch: when an error has `promptNum` but is neither a
    source-URL error nor a profanity error, prepend `" — " + message`.

### prompts/tests/test_bulk_generation_tasks.py
- Added `test_validate_prompts_errors_include_prompt_num` — asserts every
  error (empty, profanity, duplicate) has `prompt_num == index + 1`.
- Added `test_validate_prompts_profanity_includes_flagged_words_display` —
  asserts the field is present for profanity with `found_words`, absent for
  the empty-words fallback.
- Added `test_validate_prompts_profanity_bare_string_word` — exercises the
  `str(w)` branch for bare-string items in `found_words`.
- Added `test_validate_prompts_profanity_escapes_html_chars` — asserts
  HTML-special characters in a word are escaped in `flagged_words_display`.

Test count: 76 → 78 in `test_bulk_generation_tasks.py`.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** The frontend's `showValidationErrors` uses `textContent` and
`createTextNode` — embedding raw HTML (`<strong><em>`) in the backend message
string would render as literal text, not styled markup.
**Root cause:** Historical choice to use DOM API rather than `innerHTML` for
XSS safety.
**Fix applied:** Added a structured field (`flagged_words_display`) so the
frontend composes DOM nodes using the existing safe pattern instead of being
forced to interpret HTML in a message string.
**File:** `static/js/bulk-generator-generation.js` (renderer) and
`prompts/services/bulk_generation.py` (producer).

**Issue:** Backend uses snake_case (`prompt_num`) by Django convention;
frontend uses camelCase (`promptNum`) from existing client-side error
constructors.
**Root cause:** Two different conventions meeting at a JSON boundary.
**Fix applied:** Read `promptNum` from either form into a local variable,
avoiding mutation of the caller's object.
**File:** `static/js/bulk-generator-generation.js:550-555`.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The backend `message` string and frontend DOM composition both
describe the same error ("content flagged — the following word(s) were found:
X. Please revise your prompt."). If either is edited in isolation the prose
could drift.
**Impact:** Minor — cosmetic only. Both produce user-visible text and a
discrepancy would be caught in QA.
**Recommended action:** Accept the duplication for now. If a third surface
ever renders the same message, centralise the scaffolding (e.g. in a template
tag) before the third copy is added.

**Concern:** The `aria-label="Go to Prompt N"` on the clickable link is
slightly divergent from WCAG 2.5.3 "Label in Name" best practice — the
visible text "Prompt N" is already the accessible name. Kept for consistency
with the pre-existing source-URL error link that uses the same aria-label.
**Impact:** No functional problem; screen readers announce "Go to Prompt N,
link" instead of "Prompt N, link" — slightly more verbose but clearer.
**Recommended action:** If a future spec touches the source-URL error link,
drop the aria-label from both at the same time.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 9.0/10 | `textContent` is XSS boundary; `html.escape` is defense-in-depth. No injection vector. | N/A (noted) |
| 1 | @frontend-developer | 9.0/10 | Scroll + focus correct. Suggested `var promptNum` local instead of mutating `err`. | Yes — applied. |
| 1 | @code-reviewer | 8.5/10 | Implementation sound. Suggested local var + docstring. | Yes — both applied. |
| 1 | @tdd-orchestrator | 8.5/10 | Solid coverage; asked for bare-string + HTML-escape tests. | Yes — both added. |
| 1 | @django-pro | 9.0/10 | Idiomatic. Suggested docstring return-field details. | Yes — applied. |
| 1 | @ui-visual-validator (a11y) | 8.2/10 | `<strong><em>` acceptable; optional `<mark>` semantic preference. | Partial — spec explicitly requires bold+italic; kept `<strong><em>`. |
| **Average** |  | **8.7/10** | — | Pass ≥8.0 ✅ |

All agents scored ≥8.0. Average 8.7 ≥ 8.5. Threshold met.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added
material value for this spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_bulk_generation_tasks \
    --verbosity=1
# Expected: 78 tests, 0 failures. Includes the 4 new 160-A tests.
```

**Manual (browser):**
1. Go to `/tools/bulk-ai-generator/`, type a known profanity word in
   Prompt 1's textarea and press Generate.
2. The validation banner should show a **clickable "Prompt 1" link**
   followed by `— content flagged. The following word(s) were found:`
   with the triggered word rendered in **bold italic**, then
   `. Please revise your prompt.`
3. Click the "Prompt 1" link → page should scroll to the prompt box
   and focus its textarea.
4. Trigger an empty-prompt error (leave Prompt 2 blank) — banner
   should show `Prompt 2 — Prompt cannot be empty` with the
   clickable link.
5. Trigger a duplicate error — banner should show
   `Prompt N — Duplicate of prompt M` with the clickable link.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 968dc0a | fix(validation): profanity error — bold/italic word, link to prompt box |

Full suite: 1274 tests, 0 failures, 12 skipped.

---

## Section 11 — What to Work on Next

1. Spec 160-B — Quality Section Disabled/Greyed + Grid Fix. Shares the same
   `bulk-generator.js` file modification window, so it must run next.
2. After all code specs commit, validate manually in browser: profanity word
   triggers a "Prompt N" link + bold-italic triggered word, both click and
   visual styling work.
