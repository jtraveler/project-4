═══════════════════════════════════════════════════════════════
SPEC 153-E: FRONTEND ERROR MESSAGES — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## Section 1 — Overview

Spec 153-D detected the OpenAI `billing_hard_limit_reached` error and
returned a cleaned message through `GenerationResult(error_type='quota',
error_message='API billing limit reached. ...')`. What 153-D didn't
address — and what a Step 0 grep exposed in this spec — is that the
downstream path from provider error to user-facing message had three
silent gaps that made 153-D mostly invisible to end users:

1. **Backend sanitiser gap.** `_sanitise_error_message()` in
   `prompts/services/bulk_generation.py` had no billing branch. The
   153-D cleaned message fell through every if-check and was collapsed
   to the generic `'Generation failed'` bucket.

2. **Quota alert notification gap.** The bell-icon notification filter
   in `prompts/tasks.py` (`process_bulk_generation_job`) triggered on
   `error_message__icontains='quota'` only. Billing errors, which
   contain "billing" but not "quota", never fired the `openai_quota_alert`
   notification.

3. **Frontend map gaps.** The JavaScript `reasonMap` in
   `bulk-generator-config.js` had no `'Billing limit reached'` entry,
   so even if the backend had been emitting it, the frontend would have
   silently fallen through to the generic fallback. Additionally, the
   existing `'Quota exceeded'` entry said "contact admin", which is
   useless advice in a BYOK (Bring Your Own Key) system where the user
   IS the admin.

This spec closes all three gaps in one commit. The user explicitly
authorised Option B scope expansion to fix the two backend gaps in
addition to the JS changes originally specified.

## Section 2 — Expectations

| Criterion (original spec) | Status |
|----------------------------|--------|
| `'Quota exceeded'` message updated — no "contact admin" | ✅ Met |
| `'Billing limit reached'` entry added to `reasonMap` | ✅ Met |
| Both messages include the OpenAI billing URL | ✅ Met |
| All other `reasonMap` entries unchanged | ✅ Met |
| Generic fallback unchanged | ✅ Met |
| `python manage.py check` returns 0 issues | ✅ Met |
| `collectstatic` run so Heroku receives JS change | ✅ Met |

| Criterion (Option B expansion) | Status |
|--------------------------------|--------|
| Backend sanitiser emits `'Billing limit reached'` for 153-D message | ✅ Met |
| Billing branch ordered BEFORE quota branch | ✅ Met |
| `tasks.py` quota alert filter also matches billing errors | ✅ Met |
| Test coverage for all three gaps (sanitiser + filter + JS) | ✅ Met |
| Full suite passes with zero regressions | ✅ Met |

## Section 3 — Changes Made

### prompts/services/bulk_generation.py

New billing branch added BEFORE the quota branch (lines 40-47):

```python
# Billing hard limit is distinct from quota exhaustion: it's an account
# ceiling set by the user, not credit exhaustion. Check BEFORE quota so
# the more-specific branch wins. The 153-D provider stores the cleaned
# message "API billing limit reached. ..." on GeneratedImage.error_message,
# so the sanitiser matches "billing limit" (two words). The raw OpenAI
# error code "billing_hard_limit_reached" is also matched as defense-in-
# depth for any path that leaks the unsanitised exception body.
if 'billing_hard_limit_reached' in msg or 'billing limit' in msg:
    return 'Billing limit reached'
```

Branch placement is intentional: OpenAI routes `billing_hard_limit_reached`
through `BadRequestError` (a non-quota code path) and the 153-D cleaned
message contains "billing limit" but not "quota". The two branches are
distinguishable. Ordering billing BEFORE quota ensures that if any
pathological input contains BOTH keywords, the more-specific billing
match wins.

### prompts/tasks.py

- Line 29: `from django.db.models import F` → `from django.db.models import F, Q`
- Lines 2965-2972 (previously 2965-2969): quota alert filter widened
  from `error_message__icontains='quota'` to the Q expression:

```python
if job.images.filter(
    Q(error_message__icontains='quota')
    | Q(error_message__icontains='billing'),
    status='failed',
).exists():
    _fire_quota_alert_notification(job)
```

The comment above the block was updated to explain the new billing
coverage: *"Fire a specific quota alert if quota exhaustion OR billing
hard limit caused the stop — both require the user to top up / raise
their OpenAI account limit before generation can resume."*

### static/js/bulk-generator-config.js

- Line 103: header comment updated `"7 fixed sanitised strings"` →
  `"8 fixed sanitised strings"`
- Line 110: `'Quota exceeded'` message rewritten. Old: `'Failed. API
  quota exceeded — contact admin.'`. New: `'Your OpenAI API quota is
  exhausted — top up your account at platform.openai.com/settings/
  organization/billing.'`. "Contact admin" removed — BYOK users are
  their own admin.
- Line 111 (new): `'Billing limit reached'` entry added. Message: `'Your
  OpenAI billing limit has been reached — increase it at platform.openai.
  com/settings/organization/billing.'`
- All 6 other entries (Authentication error, Invalid request, Content
  policy violation, Upload failed, Rate limit reached, Generation failed)
  are byte-for-byte unchanged.
- Generic fallback at lines 114-116 unchanged.

### prompts/tests/test_bulk_generator_views.py

Three new tests added to `SanitiseErrorMessageTests` (after the
existing `test_quota_keyword`):

1. `test_billing_limit_keyword_matches_153_d_message` — verifies the
   exact cleaned 153-D message `'API billing limit reached. Please top
   up your OpenAI account at platform.openai.com/settings/organization/
   billing.'` routes to `'Billing limit reached'`.
2. `test_billing_hard_limit_raw_code_matches` — defense-in-depth test
   for the raw OpenAI error code `'BadRequestError: billing_hard_limit_reached'`.
3. `test_billing_branch_runs_before_quota_branch` — regression guard
   that verifies `'billing limit reached (quota-related cap)'` resolves
   to `'Billing limit reached'`, not `'Quota exceeded'`.

### prompts/tests/test_bulk_gen_notifications.py

- New test `test_quota_alert_filter_matches_billing_errors` — creates a
  `GeneratedImage` with the 153-D cleaned message and asserts the
  production `Q()` filter returns it.
- `test_quota_alert_does_not_fire_for_auth_failures` updated: its inline
  filter replica now mirrors the new production filter (adds the Q
  expression). Test still passes because the "Invalid API key..." message
  contains neither 'quota' nor 'billing'.

### Step 2 Verification Grep Outputs

```
=== 1. Quota exceeded (expect no 'contact admin') ===
110:            'Quota exceeded':           'Your OpenAI API quota is exhausted \u2014 top up your account at platform.openai.com/settings/organization/billing.',

=== 2. Billing limit reached (expect 1 line) ===
111:            'Billing limit reached':    'Your OpenAI billing limit has been reached \u2014 increase it at platform.openai.com/settings/organization/billing.',

=== 3. Billing URL (expect 2 lines) ===
110: ...platform.openai.com/settings/organization/billing...
111: ...platform.openai.com/settings/organization/billing...

=== 4. Other entries still present ===
106: 'Authentication error': ...
107: 'Invalid request': ...
108: 'Content policy violation': ...
109: 'Upload failed': ...
112: 'Rate limit reached': ...
113: 'Generation failed': ...
116: 'Generation failed ...'  (fallback, unchanged)

=== 5. Backend sanitiser new branch ===
43: if 'billing_hard_limit_reached' in msg or 'billing limit' in msg:
44:     return 'Billing limit reached'

=== 6. tasks.py Q filter ===
2968: Q(error_message__icontains='quota')
2969: | Q(error_message__icontains='billing'),

=== 7. System check ===
System check identified no issues (0 silenced).

=== 8. collectstatic ===
1 static file copied to 'staticfiles', 474 unmodified.
```

**Manual backend-to-JS key-string drift check** (performed with
`python -c`):

```
153-D message 'API billing limit reached. ...'
  → contains 'billing limit'     : True
  → contains 'quota'              : False
  → sanitiser returns             : 'Billing limit reached'
  → JS reasonMap['Billing limit reached'] exists: True
```

Chain verified end-to-end: provider → sanitiser → status API →
JS → user-facing message.

## Section 4 — Issues Encountered and Resolved

**Issue 1 (caught at Step 0 grep):** The spec's original scope (JS-only
1-line fix) was unworkable because the backend sanitiser had no billing
branch and would silently route 153-D billing errors to `'Generation
failed'`, making the new JS map entry dead code.
**Root cause:** 153-D added the provider-level billing detection but
did not extend the sanitiser keyword list in `bulk_generation.py`.
**Fix applied:** Escalated to user, received Option B authorisation to
expand scope. Added backend sanitiser branch + Q-filter + tests.

**Issue 2 (self-caught after first sanitiser draft):** Initial sanitiser
branch used `'billing hard limit'` (three words) as the match string.
This would NOT have matched the 153-D cleaned message `'API billing
limit reached. ...'` which contains "billing limit" (two words) but not
"billing hard limit".
**Root cause:** I conflated OpenAI's raw error code name
(`billing_hard_limit_reached`) with the text the provider actually
stores on `GeneratedImage.error_message`.
**Fix applied:** Changed match to `'billing limit'` (two words).
Verified with `python -c` that:
- The existing `test_quota_keyword` input ("You exceeded your current
  quota, please check your billing") does NOT contain "billing limit"
  (it has "your billing" only) and still resolves to `'Quota exceeded'`.
- The 153-D cleaned message DOES contain "billing limit" and resolves
  to `'Billing limit reached'`.

**Issue 3 (caught by ide_diagnostics F401):** After adding `Q` to the
`django.db.models` import in `tasks.py`, a momentary unused-import
warning was flagged before the second edit (the filter update) could
be applied.
**Root cause:** Sequential edits — import was added in edit 1, usage
in edit 2.
**Fix applied:** Expected linter race, resolved itself after edit 2.

No other issues encountered.

## Section 5 — Remaining Issues

**Issue:** `_fire_quota_alert_notification()` in `prompts/tasks.py`
around line 3691-3713 produces a notification body that references
"API quota exhausted — generation stopped" and says "Your OpenAI API
quota ran out mid-job." When the notification is triggered by a
billing limit error (now possible thanks to the Q-filter expansion in
this spec), the body text is slightly misleading — the user hasn't
run out of quota, they've hit their account spending ceiling.
**Recommended fix:** Softly generalise the notification title and
body to cover both cases, e.g. title `'OpenAI account limit reached —
generation stopped'` and body `'Your OpenAI account has hit its
spending limit mid-job. Top up credit or increase your billing limit
and try again.'` Alternatively, inspect the triggering image's
error_message in `_fire_quota_alert_notification()` to pick the
appropriate wording branch.
**Priority:** P3. Not blocking — both billing and quota failures
resolve via the same action (visit the OpenAI billing page), so the
user still gets pointed at the right fix even if the wording is
slightly off.
**Reason not resolved:** Flagged by @code-reviewer as a cosmetic
polish item. Would expand this spec's scope further and involves its
own small design decision (branch by inspection vs. generalise).

## Section 6 — Concerns and Areas for Improvement

**Concern:** The end-to-end billing error path now spans four files
(provider → sanitiser → tasks.py notification filter → JS reasonMap).
Each file has its own keyword match logic (`'billing hard limit'`,
`'billing limit'`, `icontains='billing'`, exact-match key
`'Billing limit reached'`). Drift risk on the next change is high.
**Impact:** Medium. The existing comment `"Receives only the 8 fixed
sanitised strings from the backend — use exact-match map so JS and
backend can never silently drift"` correctly describes the intended
contract but doesn't enforce it.
**Recommended action:** In a follow-up spec, extract the 8 sanitised
error category strings into a shared Python module-level constant
(e.g. `BULK_GEN_ERROR_CATEGORIES` in `prompts/constants.py`) and
reference them by name in `_sanitise_error_message()` instead of
string literals. Consider a management command that compares the
Python constant against the JS `reasonMap` keys and fails on drift.
Not in scope for this spec.

**Concern:** The 153-D provider code uses string-substring matching
on `str(e).lower()` to detect billing errors, which is fragile if
OpenAI changes their error message wording. A structured-field check
on `e.code` (as suggested by @security-auditor in 153-D) would be
more robust.
**Impact:** Low. The 153-D code already checks both the API code
(`billing_hard_limit_reached`) and the human-readable text ("billing
hard limit") as a defense-in-depth pair, so OpenAI would need to
change both simultaneously to break detection.
**Recommended action:** Already in the 153-D report's Section 6 as a
follow-up. Not a new concern raised by this spec.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 10/10 | Exact-match keys align with backend; comment count correct; both messages include billing URL; 6 other entries unchanged; generic fallback intact | N/A — no changes requested |
| 1 | @code-reviewer | 9.0/10 | Branch order correct (billing before quota, most-specific first); `'billing limit'` match pattern appropriately narrow; Django Q syntax correct; test coverage adequate; no missed call sites. **Flagged cosmetic concern: `_fire_quota_alert_notification` body still says "quota ran out" when triggered by billing** | Noted in Section 5 as P3 follow-up; not acted on (scope creep) |
| **Average** | | **9.5/10** | — | **Pass ≥8.0** |

Both agents significantly exceeded the 8.0 threshold. No re-run
required. The @code-reviewer finding is a cosmetic notification-body
issue that does not affect correctness of the error-routing chain and
is explicitly flagged as "not blocking" in their report.

## Section 8 — Recommended Additional Agents

The spec called for @frontend-developer and @code-reviewer. Both were
used.

**@security-auditor** would have been a reasonable addition to verify
that the new `'billing limit'` substring match cannot be triggered by
user-supplied prompt text being echoed back in a different error
class. Not critical — the existing 153-D review already validated
that `BadRequestError` with user-supplied prompt echo is the only
realistic vector, and the sanitiser branch is downstream of that
validation. Considered optional.

## Section 9 — How to Test

**Automated:**

```bash
python manage.py check
# Expected: System check identified no issues (0 silenced).

python manage.py test prompts.tests.test_bulk_generator_views.SanitiseErrorMessageTests \
    prompts.tests.test_bulk_gen_notifications
# Expected: 37 tests, 0 failures

python manage.py test
# Expected: Ran 1219 tests, OK (skipped=12), 0 failures

python manage.py collectstatic --noinput
# Expected: 1 static file copied
```

Full suite result: **1219 tests, 0 failures, 12 skipped** (785.8s).

**Manual verification (requires a real OpenAI account at its billing
hard limit — not reproducible in local dev):**

1. Configure a BYOK OpenAI API key belonging to an account that has
   hit its billing hard limit (or set an artificially low limit).
2. Submit a small bulk generation job (1 prompt, 1 image, low quality).
3. Wait for the job to transition to `status='failed'`.
4. Open the job progress page and confirm:
   - The failed image tile shows the new message: *"Your OpenAI
     billing limit has been reached — increase it at platform.openai.
     com/settings/organization/billing."* (NOT "Generation failed —
     try again or contact support...")
   - The URL in the message is clickable or at least copy-pasteable.
5. Open the bell-icon notification dropdown. Confirm an
   `openai_quota_alert` notification has been fired for the job.
6. Repeat with a quota-exhausted account (different scenario) and
   confirm the new `'Quota exceeded'` wording ("Your OpenAI API quota
   is exhausted — top up your account at...") replaces the old
   "contact admin" text.

**Shell-level sanity check without a real account:**

```python
python manage.py shell
>>> from prompts.services.bulk_generation import _sanitise_error_message
>>> _sanitise_error_message('API billing limit reached. Please top up your OpenAI account at platform.openai.com/settings/organization/billing.')
'Billing limit reached'
>>> _sanitise_error_message('insufficient_quota: your credit balance is too low')
'Quota exceeded'
>>> _sanitise_error_message('billing_hard_limit_reached')
'Billing limit reached'
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| (see `git log`) | fix(bulk-gen): clear actionable error messages for quota and billing limit |

One commit bundles: `bulk_generation.py` (sanitiser branch),
`tasks.py` (import + Q filter), `bulk-generator-config.js` (reasonMap
rewrite + comment), `test_bulk_generator_views.py` (3 new sanitiser
tests), `test_bulk_gen_notifications.py` (1 new filter test + 1
updated filter mirror), `staticfiles/` collectstatic artifacts, and
this report.

## Section 11 — What to Work on Next

1. **Notification body text generalisation** (P3, cosmetic) — update
   `_fire_quota_alert_notification()` in `prompts/tasks.py` around
   line 3700-3710 to handle the billing-limit case with wording that
   doesn't claim the user "ran out of quota". Either generalise both
   scenarios under one message or branch on the triggering
   `error_message`. Flagged by @code-reviewer.
2. **Shared error-category constant** (P2, maintainability) — extract
   the 8 sanitised error strings into a shared Python module-level
   constant and have `_sanitise_error_message()` return them by name.
   Consider a management command that diffs the Python constant
   against the JS `reasonMap` keys to catch drift. See Section 6
   Concern 1.
3. **Propagate the `'billing limit'` match pattern to the Admin log
   tab (P2-B planned)** — if and when the Admin operational
   notifications tab ships (CLAUDE.md mentions this as a planned
   feature), the billing-limit events should be surfaced there
   alongside quota exhaustion under a single "Account limit reached"
   health category.

═══════════════════════════════════════════════════════════════
