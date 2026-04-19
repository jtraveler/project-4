# REPORT_162_D — xAI Primary SDK Path: Billing → Quota Alignment

**Spec:** CC_SPEC_162_D_XAI_SDK_BILLING_TO_QUOTA.md
**Date:** April 19, 2026
**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Before this spec, `prompts/services/image_providers/xai_provider.py`
had two code paths for handling xAI billing exhaustion, and they
disagreed:

- **Primary SDK path** (`generate()` method, `except BadRequestError`
  at lines 161–180): returned `error_type='billing'`. No handler
  exists for `'billing'` in `prompts/tasks.py._apply_generation_result`,
  so the scheduler fell through to the generic retry loop, wasting
  credits on every retry against an exhausted account.
- **httpx-direct edits path** (`_call_xai_edits_api`, lines 273–278):
  returned `error_type='quota'`, which routes to the canonical
  job-stop branch at `tasks.py:2617`. This was fixed in 161-F.

Session 156 originally identified the SDK-path version, deferred it
from 161-F's scope as "out of scope", and noted it as a P2 backlog
item. Five sessions of drift later, this spec closes that gap with a
one-line `error_type` change plus static-string hardening.

The routing consequence is concrete: a user with exhausted xAI credits
submitting a bulk job without a reference image now stops the entire
job on the first billing failure, instead of burning retry attempts
against every queued image.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `xai_provider.py:173` `error_type='billing'` → `'quota'` | ✅ Met |
| Error message static string matching 161-F wording exactly | ✅ Met |
| Explanatory comment above the branch explains tasks.py routing | ✅ Met (8 lines, references tasks.py:~2617 and 161-F) |
| Regression test for quota routing (paired assertions) | ✅ Met — `test_sdk_path_400_billing_returns_quota` |
| Regression test for static-string / no raw-exception leak | ✅ Met — `test_sdk_path_static_error_message_no_raw_exception_leak` |
| All other `'billing'` error-type references audited | ✅ Met — only substring matches in `error_str` / `error_text` remain; zero `error_type='billing'` assignments anywhere |
| Stale narrative text grep (Rule 3) completed | ✅ Met — comments in SDK and httpx paths already reference 'quota' routing; no stale "billing is a distinct error_type" narrative found |
| `python manage.py check` clean | ✅ Met |
| Tests in prompts.tests.test_xai_provider pass | ✅ Met (23/23) |

## Section 3 — Changes Made

### prompts/services/image_providers/xai_provider.py (+8 lines net)

Lines 170–183: changed `error_type='billing'` → `error_type='quota'`;
adjusted message punctuation from `'. Check your xAI account.'` →
`' — check your xAI account.'` to match the httpx-direct path (161-F)
wording exactly. Inserted an 8-line comment block above the `if`
explaining the tasks.py:~2617 routing, the cost of mis-routing, and
the 161-F precedent.

### prompts/tests/test_xai_provider.py (+63 lines)

Added new class `XAISDKBillingToQuotaTests` (SimpleTestCase) with two
tests:

- `test_sdk_path_400_billing_returns_quota` — constructs a real
  `openai.BadRequestError` via `(message, response, body)` and patches
  `openai.OpenAI` to raise it. Asserts positive (`error_type == 'quota'`,
  `'billing' in error_message.lower()`, `result.success is False`) and
  paired negative (`error_type != 'billing'`). Failure message on the
  positive assertEqual points future developers to tasks.py:~2617 and
  this spec ID.
- `test_sdk_path_static_error_message_no_raw_exception_leak` — puts a
  secret-shaped token (`account_id=acct_SECRET_LEAK_123`) in the raw
  BadRequestError message and asserts the token does NOT appear in the
  user-facing `error_message`. Second paired negative checks that the
  substring `'debug:'` (also from the raw exception) doesn't leak.
  This regression-guards the static-string decision against a future
  developer reintroducing an f-string.

## Section 4 — Issues Encountered and Resolved

No implementation issues. The fix was a one-line change in a section
of the file already well-understood from the 161-F work. The tests
were written in a style consistent with `XAINSFWKeywordTests` (same
`BadRequestError` construction pattern, same `patch('openai.OpenAI')`
technique).

All 23 tests in `prompts.tests.test_xai_provider` passed on first run.
`python manage.py check` returned 0 issues on first run.

## Section 5 — Remaining Issues

**Issue:** The SDK path `BadRequestError` fallback at
`xai_provider.py:187` still uses `f'Bad request: {str(e)[:200]}'`,
which could leak raw exception content. Same f-string pattern appears
at lines 200, 211, 290, 309, 363 across the file. The billing path is
now static (fix shipped), but unknown 400s, connection errors, and
generic edits failures can still surface raw xAI content to the user
and the DB.
**Recommended fix:** Replace with static user-facing strings,
`logger.warning/error`-ing the raw exception server-side. Symmetric
with the content_policy and billing branches.
**Priority:** P2 (flagged by @backend-security-coder in review).
**Reason not resolved:** Out of scope per Session 162 Rule 2 —
individually under 5 lines each, but there are 6 call sites and each
would need a dedicated test to prove no regression. Too large for
absorption, appropriate for its own spec. Deferred to a future
security-hardening session.

**Issue:** The 'billing' keyword check is duplicated across the SDK
path (line 179) and the httpx-direct edits path (line 280). DRY
extraction was considered and rejected.
**Recommended fix:** None at current scale — one keyword, two paths.
If the keyword set ever grows (e.g. 'payment', 'credit') or a third
provider reuses the pattern, extract to a `_classify_400_error(text)
-> str | None` helper that returns the `error_type` string directly.
**Priority:** P3 — YAGNI currently.
**Reason not resolved:** Premature abstraction at current scale.

**Issue:** The two regression tests share 90% of their setup but
don't extract a helper. `XAINSFWKeywordTests` already has a
`_generate_with_bad_request` helper that could have been reused (or
the new class could subclass it).
**Recommended fix:** Extract `_generate_with_bad_request` into a
module-level helper or a shared base class when a third class needs
it. For now, explicit setup in both tests aids readability.
**Priority:** P3 — stylistic.
**Reason not resolved:** Flagged by @tdd-orchestrator as a consistency
gap but not a defect; ~20 lines of duplicated setup is acceptable
given test coverage is correct.

## Section 6 — Concerns and Areas for Improvement

**Concern:** @tdd-orchestrator noted no test covers the `images.edit()`
SDK path (reference-image SDK route). The primary `generate()` test
patches `images.generate.side_effect`, but if xAI billing were to
surface on the `edit` route and that route ever falls back to the SDK
(currently the reference-image flow uses the httpx direct path in
`_call_xai_edits_api`), it's uncovered.
**Impact:** Low. The architecture now pushes all reference-image
traffic through the httpx path (covered by 161-F's
`test_edit_api_400_billing_returns_quota`). If future refactoring
moves reference-image back to the SDK path, this coverage gap would
apply.
**Recommended action:** None now. Add coverage only if the routing
architecture changes.

**Concern:** @python-pro noted the test's `mock_response.json.return_value`
setup is unnecessary — `BadRequestError` doesn't call `.json()` during
construction; `body` provides the dict directly.
**Impact:** None. Minor cosmetic noise in the test. Decision: leave
as-is to match `XAINSFWKeywordTests._generate_with_bad_request`'s
existing pattern (consistency over minimalism in this file).
**Recommended action:** None.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.2/10 | Routing via tasks.py:2617 correct; scheduler stops immediately on `stop_job=True`; D1 pending-sweep mops up residual images; all other exception paths preserved; no ORM/transaction concerns | N/A — clean pass |
| 1 | @code-reviewer | 9.0/10 | Minimal, correct; mirror of 161-F wording; no dead code left; comment accurate; flagged 3 absorption candidates (lines 187, 200 f-strings) but noted none meet Rule 2 absorption bar given test scope needed | Noted in Section 5 as P2 |
| 1 | @python-pro | 9.2/10 | Exception ordering preserved (policy first, billing second, generic fallback last); idiomatic BadRequestError construction; paired assertions present; minor −0.8 for unnecessary `mock_response.json.return_value` noise | Noted in Section 6 — intentional for consistency with existing pattern |
| 1 | @tdd-orchestrator | 8.6/10 | Routing outcome covered via error_type assertion; paired assertions present; class structure consistent with XAINSFWKeywordTests; small gap: no test for images.edit() path (architecturally covered by httpx tests, not applicable here); would have caught the Session 156 bug | Noted in Section 6; no action — architecture makes the gap non-applicable |
| 1 | @backend-security-coder | 8.5/10 | Static message eliminates the previous f-string leak at billing path; no SSRF/credential surface introduced; flagged 6 other f-string paths (lines 187, 200, 211, 290, 309, 363) as remaining leak surfaces | Captured in Section 5 as P2 follow-up |
| 1 | @architect-review | 8.5/10 | DRY extraction correctly rejected (YAGNI — one keyword, two paths); `_POLICY_KEYWORDS` pattern is not analogous; 1-line fix + 8-line comment is architecturally sufficient at 424-line file size; line 187 fallback leak is correct for unknown 400s where operator visibility matters | Noted — YAGNI confirmed |
| **Average** | | **8.83/10** | | **Pass** ≥ 8.0 |

## Section 8 — Recommended Additional Agents

All six required agents ran and scored 8.5+ without a re-run needed.
The spec's required set (@django-pro, @code-reviewer, @python-pro,
@tdd-orchestrator, @backend-security-coder, @architect-review) covered
routing correctness, code quality, test structure, security, and
architecture. No additional agent would have added material value to
this one-line fix.

## Section 9 — How to Test

### Automated

```bash
python manage.py test prompts.tests.test_xai_provider --verbosity=2
# Expected: 23 tests, 0 failures (21 existing + 2 new).

python manage.py test prompts --verbosity=1
# Confirmed: 1318 tests (1316 from session 162a + 2 new 162-D).
# After 162-E: 1321 total.

python manage.py check
# Expected: 0 issues.
```

### Manual Heroku verification (developer step, after deploy)

1. Wait for a real xAI billing exhaustion event (or trigger one on a
   staging key with near-zero balance). Submit a bulk job WITHOUT a
   reference image — forces the primary SDK path.
2. Confirm the job transitions to `failed` immediately after the first
   image fails; no retries on subsequent queued images.
3. Confirm logs show the static message `'API billing limit reached —
   check your xAI account.'` and no account IDs or raw error content.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 18a918e | fix(providers): xAI primary SDK path — billing → quota alignment |

## Section 11 — What to Work on Next

1. **F-string leak hardening across xai_provider.py (P2)** — 6 call
   sites (lines 187, 200, 211, 290, 309, 363) still interpolate raw
   exception or response-body content into user-facing error messages.
   Appropriate for its own spec with 6 dedicated regression tests.
2. **DRY extraction if a third '400 classification' path appears** —
   introduce `_classify_400_error(text: str) -> str | None` helper
   returning the `error_type` string. Not needed at current scale.
3. **images.edit() SDK-path coverage** — only if the routing
   architecture reverts the reference-image path to the SDK. Currently
   architecturally unnecessary since 161-F moved reference images to
   the httpx direct path.
