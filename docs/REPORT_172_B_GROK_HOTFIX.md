# REPORT_172_B_GROK_HOTFIX

## Grok Content Moderation Hotfix — `_POLICY_KEYWORDS` Expansion

**Spec:** `CC_SPEC_172_B_GROK_HOTFIX.md`
**Status:** PARTIAL — Sections 9 and 10 filled in after full suite gate
**Cluster shape (Memory Rule #15):** BATCHED with prior-session evidence capture

---

## Section 1 — Overview

Session 170-B shipped per-card error chips routing failed bulk-gen images
through a typed taxonomy: `content_policy` failures display the red
"Content blocked" chip while `invalid_request` failures show the legacy
"Failed — Invalid request" text.

After 170-B deployed, Mateo verified Round 2 in production:
**Nano Banana 2 NSFW failures correctly displayed the red chip**, but
**Grok NSFW failures continued to show the legacy "Invalid request"
text** — no chip rendering. The 171-INV investigation concluded the chip
pipeline was structurally intact and ranked the regression as cosmetic
conflation. That conclusion was wrong.

Mateo's prior-session capture of the production `prompts_generatedimage`
table via `heroku pg:psql` revealed the actual root cause: xAI returns
the rejection wording **"Generated image rejected by content moderation."**
but `_POLICY_KEYWORDS` (line 37 of `xai_provider.py`) contained no entry
matching `'moderation'` or `'rejected'`. The keyword check fell through
to the `invalid_request` branch.

This spec adds `'moderation'` and `'rejected'` to the tuple (defense-in-
depth: either keyword catches the wording even if xAI varies it slightly)
plus a Memory Rule #13 `logger.info` on the BadRequestError fallthrough
path so future investigations can read Heroku logs instead of querying
Postgres.

---

## Section 2 — Expectations

| Success criterion | Status |
|---|---|
| `_POLICY_KEYWORDS` expanded with 'moderation' and 'rejected' | ✅ Met |
| Memory Rule #13 `logger.info` added on BadRequestError fallthrough | ✅ Met |
| Test 1: keyword expansion regression test (Mateo's exact wording) | ✅ Met |
| Test 2: Memory Rule #13 fallthrough logging test | ✅ Met |
| All new tests pass | ✅ Met |
| `python manage.py check` passes | ✅ Met |
| Both content_policy detection paths (SDK + httpx-direct) benefit | ✅ Met (shared tuple) |
| All 4 agents ≥ 8.0/10, average ≥ 8.5 | ✅ Met (9.275/10) |

### Step 0 verbatim grep outputs

```bash
$ sed -n '35,42p' prompts/services/image_providers/xai_provider.py
# Keywords in xAI BadRequestError messages that indicate content policy rejection.
# Checked against str(e).lower(). Broad set to catch varied xAI error phrasing.
_POLICY_KEYWORDS = (
    'content policy', 'safety', 'forbidden', 'violation',
    'blocked', 'inappropriate', 'nsfw', 'not allowed',
)

$ grep -n "_POLICY_KEYWORDS" prompts/services/image_providers/xai_provider.py
37:_POLICY_KEYWORDS = (
166:            if any(kw in error_str for kw in _POLICY_KEYWORDS):
292:                if any(kw in error_text for kw in _POLICY_KEYWORDS):

$ grep -n "^logger\|^import logging\|getLogger" prompts/services/image_providers/xai_provider.py | head -5
14:import logging
22:logger = logging.getLogger(__name__)

$ ls prompts/tests/test_xai*.py
prompts/tests/test_xai_provider.py

$ wc -l prompts/services/image_providers/xai_provider.py
449 prompts/services/image_providers/xai_provider.py
```

File is in ✅ Safe tier (449 lines). 2 str_replaces well within budget.

### Verification grep outputs (Step 6)

```bash
$ grep -n "moderation\|rejected" prompts/services/image_providers/xai_provider.py | head -10
38:# Session 172-B: added 'moderation' and 'rejected' after Mateo captured the
40:#   "Generated image rejected by content moderation."
42:# evidence trail. Both 'moderation' and 'rejected' added (rather than just one)
48:    'moderation', 'rejected',
180:                    error_message='Image rejected by content policy. Try modifying the prompt.',
318:                        error_message='Image rejected by content policy. Try modifying the prompt.',

$ grep -n "BadRequestError fallthrough" prompts/services/image_providers/xai_provider.py
203:                "xAI BadRequestError fallthrough (no keyword match): %s",

$ grep -n "test_xai_content_moderation\|test_xai_unrecognized_400" prompts/tests/test_xai_provider.py
107:    def test_xai_content_moderation_classified_as_content_policy(self):
122:    def test_xai_unrecognized_400_logs_at_info(self):

$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py test prompts.tests.test_xai_provider -v 2 2>&1 | tail -5
Ran 25 tests in 0.287s
OK
```

---

## Section 3 — Changes Made

### `prompts/services/image_providers/xai_provider.py` (2 str_replaces)

**Edit 1 — `_POLICY_KEYWORDS` tuple expansion (lines 37-49):**

- Added 8-line comment block explaining the addition with full evidence
  trail (verbatim Mateo psql wording, defense-in-depth rationale)
- Tuple expanded from 8 keywords to 10 by adding `'moderation', 'rejected'`
  on a new last line (preserves diff minimality)

**Edit 2 — Memory Rule #13 logger.info on fallthrough (lines 195-205):**

- Added 7-line `logger.info` call between the `'billing'` check (line ~187)
  and the `invalid_request` `GenerationResult` return (line ~206)
- Message format: `"xAI BadRequestError fallthrough (no keyword match): %s"`
  with `str(e)[:300]` truncation
- Comment block explains the rationale (Session 171's Postgres-query workaround)

### `prompts/tests/test_xai_provider.py` (1 str_replace adding 2 tests)

- Added 2 new test methods to the existing `XAINSFWKeywordTests` class
  (which already has the `_generate_with_bad_request` helper):
  - `test_xai_content_moderation_classified_as_content_policy` — uses
    Mateo's exact captured rejection wording, asserts `error_type ==
    'content_policy'` and message contains 'content policy'
  - `test_xai_unrecognized_400_logs_at_info` — uses `assertLogs` against
    `prompts.services.image_providers.xai_provider` at INFO level, with
    a deliberately-crafted message that avoids all `_POLICY_KEYWORDS` AND
    avoids `'billing'` (so the fallthrough branch is the only possible
    path), asserts the fallthrough log line fires

Test file was 339 → 374 lines (35 new lines including a single in-test
comment). Both tests reuse the existing helper rather than constructing
custom mocks — mirrors codebase convention.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** First run of `test_xai_unrecognized_400_logs_at_info` failed
with `AssertionError: no logs of level INFO or higher triggered`.
**Root cause:** My initial test wording was
`'malformed parameter foobar — neither billing nor a known policy keyword'`.
The substring `'billing'` was in there. The xAI provider's BadRequestError
handler checks `if 'billing' in error_str` BEFORE my new fallthrough
logger.info, so the test routed to the quota path instead of the
fallthrough.
**Fix applied:** Changed the test message to
`'malformed parameter foobar — unrecognised 400'` (no `_POLICY_KEYWORDS`
match, no `'billing'`) so the fallthrough branch is the only possible
path. Added an in-test comment explaining the wording constraint.
**File:** `prompts/tests/test_xai_provider.py:127-130`

This issue was caught at first test run, before agent review. Test now
passes; all 25 xai_provider tests pass cleanly.

### Memory Rule #13 application notes

Per Session 169-B's established rule, silent-fallback paths must log.
The BadRequestError fallthrough is a **silent fallback** in the strict
sense: the code returns `error_type='invalid_request'` without any log
entry, so a frontend regression like Mateo's was invisible to anyone
not actively querying the production database.

The chosen log level is `info` (not `warning`):

- This branch fires whenever xAI rejects for a reason we don't pre-classify
- It's not an error condition — the user gets a clear `invalid_request`
  classification, just not the more specific `content_policy`
- Logging at info means it appears in Heroku logs without flooding warning
  channels

The `[:300]` truncation on `str(e)` is an order-of-magnitude safety
margin over the `[:200]` cap used on the user-facing `error_message`
field. xAI 400 bodies can include cost-tracking JSON and request IDs;
truncating at 300 keeps log lines manageable while preserving enough
text for triage.

### Evidence anchoring

Mateo's `heroku pg:psql` output (verbatim, both rows identical):

```
error_type      | error_message
----------------+-------------------------------------------------------------------
invalid_request | Bad request: Error code: 400 - {'code': 'Client specified an
                |   invalid argument', 'error': 'Generated image rejected by content
                |   moderation.', 'usage': {'cost_in_usd_ticks': 200000000}}
```

This exact wording is locked into Test 1's assertion fixture (line ~115
of `test_xai_provider.py`), so any future regression that breaks the
keyword match against this specific string would fail at CI time.

### False-positive risk analysis (per spec Section 3.4)

- **`'moderation'`** — xAI doesn't use this word in non-moderation 400
  errors. Risk: low.
- **`'rejected'`** — could potentially appear in unrelated rejections
  (e.g. parameter validation failures). Risk: medium-low. Mitigation:
  the keyword check fires inside `except BadRequestError` AFTER the
  `'billing'` check, so quota errors are routed away first. The
  remaining 400s containing `'rejected'` are most likely content
  moderation rejections.
- If false positives are observed in production, the fix is to narrow
  to `'rejected by content'` (more specific phrase). Track via the new
  `logger.info` fallthrough output post-deploy (Memory Rule #14
  closing checklist).

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

The architect-review agent surfaced architectural concerns documented
in Section 6 — these are tracked as future P3 items, not Session 172
blockers.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `'rejected'` is the weakest keyword in the tuple — it's a
common English word that could appear in any xAI 400 describing
parameter validation failures.
**Impact:** Low (the `'billing'` guard precedes it; check fires only
inside `BadRequestError`) but not airtight. Future xAI 400 bodies for
malformed `aspect_ratio` or model name could contain 'rejected'.
**Recommended action:** Add a P3 row tracking "consider narrowing
`'rejected'` to `'rejected by content'` if false-positive rate observed
post-deploy via the new `logger.info` fallthrough output." Action only
when evidence justifies it.

**Concern:** Cross-provider inconsistency in content-policy detection.
xAI uses keyword substring matching (free-text 400 bodies); OpenAI uses
structured `error.code == 'content_policy_violation'`.
**Impact:** Architectural debt — future contributors touching the OpenAI
provider won't find the same detection pattern in xAI's provider.
**Recommended action:** Document in `xai_provider.py` module docstring
that the keyword approach is xAI-specific (driven by API shape, not
provider preference). A shared `detect_content_policy(error_str,
structured_code=None)` utility could unify both paths in a future
refactor — defer until a third provider needs detection (Replicate's
NSFW UX is already a Phase REP P2 blocker).

**Concern:** `_POLICY_KEYWORDS` is xAI-specific but its name doesn't
signal that. A future Replicate provider also needing keyword matching
could accidentally reuse or shadow the constant.
**Impact:** Low (current single-provider use, but Phase REP roadmap
includes Replicate provider work).
**Recommended action:** Rename to `_XAI_POLICY_KEYWORDS` in a future
cleanup pass. Trivial diff once the constant is widely-imported.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 9.3/10 | Evidence anchoring is exemplary (Mateo's verbatim psql output → keyword choice → test fixture in clean traceability chain). Memory Rule #13 application correct. No scope creep. | N/A — no issues to act on |
| 1 | @debugger | 9.5/10 | Verified the fix mechanically: lowercased `"Generated image rejected by content moderation."` substring-matches both 'moderation' and 'rejected'. Test passed in 0.006s. Returned error_message satisfies frontend taxonomy. Logger.info fallthrough is meaningful bonus. | N/A |
| 1 | @test-automator | 9.5/10 | Both new tests pass. assertLogs path is correct (matches __name__ of xai_provider.py). Tests reuse existing helper rather than custom mock setup — fully consistent with class pattern. Locks in exact wording at CI time. | N/A |
| 1 | @architect-review | 8.8/10 | Keyword approach correctly chosen for xAI's API shape (no structured error.code field). 'billing' guard is load-bearing. 2-keyword redundancy justified as defense-in-depth. Surfaced 3 architectural concerns (none blocking). | Yes — concerns documented in Section 6 as future work |
| **Average** | | **9.275/10** | | **Pass ≥ 8.0** |

All scores ≥ 8.0. Average 9.275 ≥ 8.5 threshold. No re-run required.

---

## Section 8 — Recommended Additional Agents

**@frontend-developer:** Would have verified the chip-render pipeline
end-to-end — i.e. confirming that an `error_type='content_policy'`
result produces the red chip in the frontend. We covered the backend
classification layer; the frontend taxonomy was assumed working from
170-B's own verification (Round 2 NB2 chip confirmed). Acceptable
scope limit for this hotfix; flag if Round 3 verification fails.

**@security-auditor:** Would have reviewed whether the new
`logger.info` truncated string `str(e)[:300]` could leak user-facing
content to logs. Not a concern here (xAI 400 bodies don't include
user prompts beyond the original request, and 300 chars is shorter
than typical full bodies), but worth considering. Spec Section 4.3
addresses the credential angle; the user-content angle is out of
scope.

For the narrow scope of "fix the keyword tuple, add Memory Rule #13
logging, lock in via tests," the 4 chosen agents covered material
concerns adequately.

---

## Section 9 — How to Test

*To be filled after full test suite gate (post Spec C).*

### Closing checklist (Memory Rule #14 — populated now, results post-gate)

**Migrations:** N/A — no model field changes in this spec.

**Manual browser tests (max 2 at a time, with explicit confirmation between):**

Round 1 (172-B keyword expansion):
1. Reproduce the NSFW Grok prompt that previously showed "Failed —
   Invalid request" → verify it now shows the red **"Content blocked"**
   chip per the 170-B taxonomy.
2. Open Heroku logs and grep for `"xAI BadRequestError fallthrough"` —
   confirms the new Memory Rule #13 logger.info is wired correctly.
   Should NOT appear for the NSFW-rejection test (matches 'moderation'
   keyword, takes content_policy path) but SHOULD appear if a
   non-content-policy 400 occurs (e.g. malformed aspect_ratio).

**Failure modes to watch for:**
- Grok NSFW still shows "Invalid request" → keyword expansion didn't
  apply or didn't deploy. Verify by SSH'ing into a Heroku dyno and
  running `python -c "from prompts.services.image_providers.xai_provider
  import _POLICY_KEYWORDS; print('moderation' in _POLICY_KEYWORDS)"`.
- New `logger.info` floods logs → indicates many xAI 400s are missing
  keyword classification. Inspect log output to identify additional
  keywords needed (or move to narrowing `'rejected'`).
- False positive: a malformed parameter 400 gets misclassified as
  `content_policy` → indicates the medium-low risk identified in spec
  Section 3.4 has materialized. Narrow `'rejected'` to `'rejected by
  content'` in a follow-up spec.

**Backward-compatibility verification:**
- Existing NB2 NSFW chip rendering unaffected (NB2 uses Replicate, not
  xAI; this change is xAI-specific).
- httpx-direct edits path (line 292) automatically benefits from the
  shared `_POLICY_KEYWORDS` tuple — same rejection wording for the
  reference-image edit endpoint will now route correctly.
- Existing `_POLICY_KEYWORDS` matches (forbidden, blocked, etc.)
  unchanged — additive expansion only.

**Automated test results:**

```bash
$ python manage.py test prompts.tests.test_xai_provider -v 2 2>&1 | tail -5
Ran 25 tests in 0.287s
OK

$ python manage.py test
...
Ran 1400 tests in 1647.668s
OK (skipped=12)
```

Pre-Session 172: 1396 tests. Post-Session 172: 1400 tests. Spec B
contributed 2 new tests (`test_xai_content_moderation_classified_as_content_policy`,
`test_xai_unrecognized_400_logs_at_info`). Both pass. xai_provider test
file went from 23 → 25 tests; full suite from 1396 → 1400 (Spec B 2 +
Spec C 2). 0 failures, 0 errors, 12 skipped (unchanged from pre-session).

---

## Section 10 — Commits

*Hash filled in post-commit; will ride into Session 172-D docs commit per the project's established pattern (see REPORT_170_B precedent).*

| Hash | Message |
|------|---------|
| TBD  | fix(bulk-gen): expand xAI _POLICY_KEYWORDS to catch "rejected by content moderation" (Session 172-B) |

---

## Section 11 — What to Work on Next

1. **Run Spec 172-C** (overlay restore on page load) immediately —
   independent file surface (`bulk-generator-ui.js`), can run in series.
2. **Full test suite gate** after 172-C — the commit gate for all three
   code specs A/B/C.
3. **Post-deploy verification (Memory Rule #14):** see Section 9
   closing checklist Round 1.
4. **Future P3 follow-ups (from architect-review):**
   - Watch new `logger.info` fallthrough output for any false positives
     on `'rejected'` keyword
   - Document module-level docstring noting the keyword approach is
     xAI-specific (driven by API shape)
   - Consider renaming `_POLICY_KEYWORDS` → `_XAI_POLICY_KEYWORDS` if
     other providers add similar detection
