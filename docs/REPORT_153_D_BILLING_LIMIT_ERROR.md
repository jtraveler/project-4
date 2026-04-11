═══════════════════════════════════════════════════════════════
SPEC 153-D: BILLING LIMIT ERROR FIX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## Section 1 — Overview

When an OpenAI account hits its billing hard limit, the API returns a
`BadRequestError` (400) with code `billing_hard_limit_reached`. The previous
`BadRequestError` handler in `prompts/services/image_providers/openai_provider.py`
did not check for this code, so the error fell through to the generic
`invalid_request` path and surfaced to the user as "Invalid request — check
your prompt or settings." This message was actively misleading — the prompt
and settings were fine; the user's OpenAI account was out of credit.

This spec adds a targeted check in the `BadRequestError` handler that detects
the billing hard limit and returns an actionable message directing the user
to their OpenAI billing page. It is the `BadRequestError`-class equivalent
of the existing `insufficient_quota` handling that already lives in the
`RateLimitError` branch (lines 177–203).

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `billing_hard_limit_reached` detected in `BadRequestError` handler | ✅ Met |
| Returns `error_type='quota'` with clear, actionable message | ✅ Met |
| Billing check comes BEFORE content policy check | ✅ Met |
| Existing content policy and generic error paths unchanged | ✅ Met |
| `python manage.py check` returns 0 issues | ✅ Met |
| No other files modified | ✅ Met |

## Section 3 — Changes Made

### prompts/services/image_providers/openai_provider.py

- Lines 206–214 (new): Added billing hard limit detection as the first
  branch inside the `BadRequestError` handler. Matches both the API code
  (`billing_hard_limit_reached`) and the human-readable text (`billing hard
  limit`) in the lowercased error body. Returns `error_type='quota'` with a
  message pointing the user to
  `platform.openai.com/settings/organization/billing`.
- Lines 215–225 (unchanged content, renumbered): Existing content policy
  check preserved verbatim.
- Lines 226–230 (unchanged content, renumbered): Existing generic
  `invalid_request` fallback preserved verbatim.

One `str_replace` call. File size: 293 → 302 lines (✅ Safe tier).

### Step 2 Verification Grep Outputs

```
$ grep -n "billing_hard_limit_reached\|billing hard limit" \
    prompts/services/image_providers/openai_provider.py
206:            if 'billing_hard_limit_reached' in error_body or 'billing hard limit' in error_body:

$ grep -n "billing_hard_limit_reached" \
    prompts/services/image_providers/openai_provider.py -A 8
206:            if 'billing_hard_limit_reached' in error_body or 'billing hard limit' in error_body:
207-                return GenerationResult(
208-                    success=False,
209-                    error_type='quota',
210-                    error_message=(
211-                        'API billing limit reached. Please top up your OpenAI account '
212-                        'at platform.openai.com/settings/organization/billing.'
213-                    ),
214-                )

$ grep -n "content_policy\|content policy" \
    prompts/services/image_providers/openai_provider.py
217:                for kw in ('safety', 'content_policy', 'violated', 'content policy')
221:                    error_type='content_policy',
223:                        'Image rejected by content policy. Try modifying the prompt.'

$ python manage.py check
System check identified no issues (0 silenced).
```

Billing check at line 206 precedes content policy at line 217. Correct order.

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. The current `BadRequestError`
block matched the spec's expected text exactly, so the `str_replace` applied
cleanly on the first attempt.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The billing check uses substring matching on `str(e).lower()`
rather than structured field access (`e.code` or `e.body['error']['code']`).
**Impact:** A user-crafted prompt containing the literal string
`billing_hard_limit_reached` could in theory trigger a false billing error
if OpenAI's content-policy response echoes the prompt back. The false
positive is non-harmful (job halts gracefully, no retry, user checks billing
page and re-submits) — @security-auditor scored this 8.5/10 and classified
it as low risk. However, the existing `insufficient_quota` branch in
`RateLimitError` also uses `hasattr(e, 'code') and e.code == 'insufficient_quota'`
as a secondary structured check. The new billing branch could mirror that
pattern.
**Recommended action:** In a follow-up spec, add a structured-field check
alongside the string match:
```python
if ('billing_hard_limit_reached' in error_body
    or 'billing hard limit' in error_body
    or (hasattr(e, 'code') and e.code == 'billing_hard_limit_reached')):
```
Defense-in-depth only — not blocking for this spec.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 9.0/10 | Ordering correct; consistent with insufficient_quota path; content policy and generic fallback unchanged; optional suggestion to add `hasattr(e, 'code')` structured check | Noted in Section 6; not acted on (non-blocking, follow-up) |
| 1 | @security-auditor | 8.5/10 | Billing URL is public and safe; substring spoofing is theoretically possible but non-harmful; no information disclosure; optional structured-field hardening recommended | Noted in Section 6; not acted on (non-blocking, follow-up) |
| **Average** | | **8.75/10** | — | **Pass ≥8.0** |

Both agents exceeded the 8.0 threshold on the first round. No re-run needed.

## Section 8 — Recommended Additional Agents

All relevant agents specified in the spec were used. The spec required 2
agents minimum (@code-reviewer and @django-security — satisfied via
@security-auditor, which is the project-standard security review agent).
No additional agents would have added material value for a single-branch
error-routing fix in a ✅ Safe-tier file.

## Section 9 — How to Test

**Automated:**

```bash
python manage.py check
# Expected: System check identified no issues (0 silenced).

python manage.py test
# Expected: Ran 1215 tests, OK (skipped=12), 0 failures
```

Full suite result for this spec: **1215 tests, 0 failures, 12 skipped**
(713.7s). No existing test covers the new `BadRequestError` billing branch
directly, but the existing `TestOpenAIImageProvider` suite exercises the
`BadRequestError` path for content policy and confirms the surrounding
handler structure is intact.

**Manual verification (requires a real OpenAI account at its billing
limit — not reproducible in local dev):**

1. Configure a BYOK OpenAI API key for an account that has hit its
   billing hard limit.
2. Navigate to `/tools/bulk-ai-generator/` and submit a small job
   (1 prompt, low quality) with that key.
3. Wait for the job to reach a terminal state. The first image should
   fail with the new message: "API billing limit reached. Please top
   up your OpenAI account at platform.openai.com/settings/organization/billing."
4. Confirm the image card in the gallery shows the new message (or a
   sanitised form) instead of the old "Invalid request — check your
   prompt or settings" fallback.
5. Confirm `GeneratedImage.error_type` on the failed row equals
   `'quota'` (inspect via Django admin or shell).

**Frontend sanitiser / mapping check:**

```bash
grep -n "quota\|billing" static/js/bulk-generator-config.js
# Expected: existing _getReadableErrorReason() quota mapping
# (QUOTA-1, Session 143) — confirm the new message surfaces either
# verbatim or via the 'Quota exceeded' → "API quota exceeded" mapping.
```

A follow-up frontend mapping review is recommended in Section 11 item 3.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| d89f473 | fix(bulk-gen): show clear billing limit error instead of generic invalid request message |

Single commit. All pre-commit hooks passed (trim trailing whitespace,
fix end of files, check for merge conflicts, debug statements, flake8,
bandit).

## Section 11 — What to Work on Next

1. **QUOTA-2 spend-rate warning notification** — CLAUDE.md Section QUOTA-2
   describes a planned follow-up that fires a low-spend warning before a job
   actually hits the billing hard limit. This spec closes the "billing limit
   reached" error message gap; QUOTA-2 would give users an earlier heads-up.
2. **Optional structured-field hardening** — add `hasattr(e, 'code') and
   e.code == 'billing_hard_limit_reached'` to the new branch in
   `openai_provider.py` line 206 for defense-in-depth. See Section 6.
3. **Frontend `_getReadableErrorReason()` audit** — confirm the frontend
   maps `error_type='quota'` to a user-facing message that matches the new
   backend message. QUOTA-1 (Session 143) already wired the
   `'Quota exceeded'` mapping; the new billing message ("API billing limit
   reached. Please top up…") may surface verbatim or be re-mapped depending
   on the sanitiser path.

═══════════════════════════════════════════════════════════════
