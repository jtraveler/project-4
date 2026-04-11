# CC_SPEC_153_D_BILLING_LIMIT_ERROR.md
# Fix Billing Hard Limit Error Message in OpenAI Provider

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** 1 str_replace in `prompts/services/image_providers/openai_provider.py`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`openai_provider.py` is ✅ SAFE** — normal editing
4. **DO NOT COMMIT** until agent scores confirmed ≥ 8.0
5. **No migration required**

---

## 📋 OVERVIEW

### Billing Hard Limit — Unhelpful Error Message

When an OpenAI account hits its billing hard limit, the API returns a
`BadRequestError` (400) with code `billing_hard_limit_reached`. The current
`BadRequestError` handler does not check for this code — it falls through to
the generic `invalid_request` path, which surfaces to the user as:

> "Invalid request — check your prompt or settings."

This message is actively misleading. The prompt and settings are fine. The
real problem is the user's OpenAI account is out of credit.

### Confirmed Current State

From `prompts/services/image_providers/openai_provider.py`, the current
`BadRequestError` handler checks for content policy keywords first, then
falls back to a generic error. The `billing_hard_limit_reached` code is
not checked anywhere in this handler.

The existing `RateLimitError` handler already handles `insufficient_quota`
correctly — this spec adds the equivalent check for the billing hard limit
which arrives via a different exception class (`BadRequestError` not
`RateLimitError`).

### Actual OpenAI Error Payload (confirmed from production logs)

```json
{
  "error": {
    "message": "Billing hard limit has been reached.",
    "type": "billing_limit_user_error",
    "param": null,
    "code": "billing_hard_limit_reached"
  }
}
```

---

## 🎯 OBJECTIVES

### Primary Goal

When the OpenAI billing hard limit is reached, the user sees a clear,
actionable message explaining what happened and where to fix it — not a
generic "Invalid request" message.

### Success Criteria

- ✅ `billing_hard_limit_reached` detected in `BadRequestError` handler
- ✅ Returns `error_type='quota'` with a clear, actionable message
- ✅ Billing check comes BEFORE the content policy check
- ✅ Existing content policy and generic error paths unchanged
- ✅ `python manage.py check` returns 0 issues
- ✅ No other files modified

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full BadRequestError handler to get exact current text
grep -n "BadRequestError\|billing\|content_policy\|invalid_request" \
    prompts/services/image_providers/openai_provider.py

# 2. Read the exact handler block for safe str_replace anchor
sed -n '/except BadRequestError/,/except APIStatusError/p' \
    prompts/services/image_providers/openai_provider.py | head -20

# 3. Confirm existing insufficient_quota handling in RateLimitError
grep -n "insufficient_quota" prompts/services/image_providers/openai_provider.py

# 4. Check file size
wc -l prompts/services/image_providers/openai_provider.py
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Update `BadRequestError` handler

**File:** `prompts/services/image_providers/openai_provider.py`
**str_replace call: 1 of 1**

From Step 0 grep 2, read the exact current `BadRequestError` block.
It will look like:

```python
        except BadRequestError as e:
            error_body = str(e).lower()
            if any(
                kw in error_body
                for kw in ('safety', 'content_policy', 'violated', 'content policy')
            ):
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message=(
                        'Image rejected by content policy. Try modifying the prompt.'
                    ),
                )
            return GenerationResult(
                success=False,
                error_type='invalid_request',
                error_message=f'Invalid request: {str(e)}',
            )
```

**Use the exact text from Step 0 grep 2 as your str_replace anchor.**

Replace with:

```python
        except BadRequestError as e:
            error_body = str(e).lower()
            if 'billing_hard_limit_reached' in error_body or 'billing hard limit' in error_body:
                return GenerationResult(
                    success=False,
                    error_type='quota',
                    error_message=(
                        'API billing limit reached. Please top up your OpenAI account '
                        'at platform.openai.com/settings/organization/billing.'
                    ),
                )
            if any(
                kw in error_body
                for kw in ('safety', 'content_policy', 'violated', 'content policy')
            ):
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message=(
                        'Image rejected by content policy. Try modifying the prompt.'
                    ),
                )
            return GenerationResult(
                success=False,
                error_type='invalid_request',
                error_message=f'Invalid request: {str(e)}',
            )
```

⚠️ The billing check must come BEFORE the content policy check. Do not
reorder the content policy or generic fallback paths.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm billing check is present
grep -n "billing_hard_limit_reached\|billing hard limit" \
    prompts/services/image_providers/openai_provider.py
# Expected: 1 line — the new check

# 2. Confirm error_type='quota' is returned for billing error
grep -n "billing_hard_limit_reached" \
    prompts/services/image_providers/openai_provider.py -A 5
# Expected: shows error_type='quota' in the block

# 3. Confirm content policy check still present and unchanged
grep -n "content_policy\|content policy" \
    prompts/services/image_providers/openai_provider.py
# Expected: still present

# 4. System check
python manage.py check
# Expected: 0 issues
```

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Step 2 verification greps all return expected results (shown in report)
- [ ] Billing check appears BEFORE content policy check in the handler
- [ ] `error_type='quota'` returned (consistent with `insufficient_quota` path)
- [ ] Error message is actionable — includes the billing URL
- [ ] Content policy path unchanged
- [ ] Generic `invalid_request` fallback unchanged
- [ ] No other files modified
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. Both must score 8.0+.

### 1. @code-reviewer
**Verify the fix is correct and complete.**
- Confirm billing check comes before content policy check
- Confirm `error_type='quota'` is consistent with the existing
  `insufficient_quota` handling in `RateLimitError`
- Confirm the error message is actionable and includes the billing URL
- Confirm content policy and generic fallback paths are unchanged
- Show Step 2 verification grep outputs
- Rating requirement: **8+/10**

### 2. @django-security
**Confirm no security or information disclosure issues.**
- Confirm the billing URL in the error message is safe to surface to users
  (it is a public OpenAI URL, not an internal system detail)
- Confirm `str(e).lower()` string matching cannot be spoofed by a
  crafted prompt to trigger a false billing error message
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- Billing check comes AFTER content policy check (wrong order)
- `error_type` is not `'quota'`
- Content policy path modified
- Step 2 verification greps not shown in report

---

## 📊 CC COMPLETION REPORT FORMAT

```markdown
═══════════════════════════════════════════════════════════════
SPEC 153-D: BILLING LIMIT ERROR FIX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | X/10 | [findings] | Yes/No |
| 1 | @django-security | X/10 | [findings] | Yes/No |
| Average | | X.X/10 | — | Pass ≥8.0 / Fail |

## 📁 FILES MODIFIED

prompts/services/image_providers/openai_provider.py — billing check added

## 🧪 TESTING PERFORMED

[python manage.py check output]

## ✅ SUCCESS CRITERIA MET

[Checklist]

## 🔄 DATA MIGRATION STATUS

N/A

## 🔁 SELF-IDENTIFIED FIXES APPLIED

[If none: "None identified."]

## 🔁 DEFERRED — OUT OF SCOPE

[If none: "None identified."]

## 📝 NOTES

[Step 2 verification grep outputs must be shown here]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): show clear billing limit error instead of generic invalid request message

When OpenAI returns billing_hard_limit_reached (400 BadRequestError),
the user now sees an actionable message directing them to their billing
settings instead of the misleading "Invalid request — check your prompt
or settings" message.
```

---

## ⛔ CRITICAL REMINDERS (Repeated)

- **Billing check MUST come before content policy check**
- **`error_type='quota'`** — consistent with existing `insufficient_quota` handling
- **Do not modify content policy or generic fallback paths**
- **1 str_replace call only**

---

**END OF SPEC**
