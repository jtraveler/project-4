# REPORT_162_C — Vision Moderation: .public_id not str()

**Spec:** CC_SPEC_162_C_VISION_MODERATION_PUBLIC_ID.md
**Date:** April 19, 2026
**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Before this spec, four call sites used `str(CloudinaryField_value)` to
get a public_id for downstream URL construction or substring matching:
one in the video-moderation fallback path (`vision_moderation.py:~676`)
and three in the `fix_cloudinary_urls` diagnostic command (lines 72,
110, 131).

**Premise discovery during implementation:** The spec's root-cause
claim — that `str(CloudinaryResource)` returns the object repr —
turns out to be FACTUALLY INCORRECT for the current cloudinary SDK
version. A direct test confirmed:

```python
>>> r = CloudinaryResource(public_id='legacy/foo', ...)
>>> str(r)
'legacy/foo'   # Returns the public_id, NOT the repr
```

So the pre-162-C code was NOT producing malformed Cloudinary URLs in
production for CloudinaryResource inputs. This partially invalidates
the spec's stated motivation.

**However, the fix is still independently justified:**

1. **Latent None-interpolation bug.** If `featured_video` is None,
   `str(None)` returns `'None'`, which the old code would interpolate
   into a Cloudinary URL path. The new pattern resolves to `''`,
   producing a safe empty-URL outcome instead of `legacy/None.jpg`.
2. **Defense against SDK upgrades.** `CloudinaryResource.__str__` is
   implementation-defined. A future cloudinary package version could
   change this behavior silently. Explicit `.public_id` access
   decouples from that risk.
3. **Pattern consistency.** Matches the 161-A migration command
   which uses explicit `.public_id` extraction.

The report documents the premise discrepancy transparently so future
readers aren't confused by the divergence between the spec's prose
and the actual pre-fix behavior.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `vision_moderation.py:~676` uses `.public_id` pattern | ✅ Met |
| `fix_cloudinary_urls.py:72` (avatar) uses pattern | ✅ Met |
| `fix_cloudinary_urls.py:110` (featured_image) uses pattern | ✅ Met |
| `fix_cloudinary_urls.py:131` (featured_video) uses pattern | ✅ Met |
| Each fix has a 2-4 line defensive comment | ✅ Met |
| Regression test for `vision_moderation.py` | ✅ Met (3 tests) |
| Empty / None branch tested | ✅ Met — explicit triple paired assertion |
| `fix_admin_avatar.py` NOT modified (P3 out of scope) | ✅ Met — verified via grep |
| Stale narrative text grep (Rule 3) | ✅ Met — no remaining references to `str()` producing repr |
| `python manage.py check` clean | ✅ Met |

## Section 3 — Changes Made

### prompts/services/vision_moderation.py (+9 lines net)

- Lines 673–695 (`_get_video_frame_url` else branch): replaced
  `cloudinary.CloudinaryImage(str(prompt_obj.featured_video))` with
  an explicit public_id extraction:
  ```python
  public_id = (
      getattr(prompt_obj.featured_video, 'public_id', None)
      or (prompt_obj.featured_video if isinstance(
          prompt_obj.featured_video, str
      ) else '')
  )
  frame_url = cloudinary.CloudinaryImage(public_id).build_url(...)
  ```
  Added 7-line comment explaining pattern rationale, empty-URL
  safety guarantee, and cross-reference to 161-A / 162-C.

### prompts/management/commands/fix_cloudinary_urls.py (+24 lines net)

- Lines 72–82: `str(profile.avatar)` → same public_id extraction
  pattern with `isinstance(..., str)` fallback.
- Lines 110–119: `str(prompt.featured_image)` → same pattern.
- Lines 131–140: `str(prompt.featured_video)` → same pattern.
- Each site has a 4-line comment referencing 161-A / 162-C for
  consistency.

### prompts/tests/test_vision_moderation_public_id.py (NEW, 139 lines)

Two test classes, 4 tests:

- `VisionModerationPublicIdTests`:
  - `test_cloudinary_resource_takes_build_url_branch` — real Prompt,
    `refresh_from_db()`, CloudinaryResource built_url path; asserts
    URL contains public_id + `mock_image.assert_not_called()`
    (paired positive+negative).
  - `test_plain_string_fallback_uses_public_id_pattern` — inline
    class with plain-string `featured_video`, asserts
    `CloudinaryImage(public_id)` called exactly.
  - `test_none_featured_video_falls_back_to_empty_public_id` — the
    critical regression test with triple paired assertion:
    `assert_called_once_with('')` + `assertNotEqual(called_arg,
    'None')` + `assertNotIn('None', called_arg)`. This pins down
    the latent `str(None)` → `'None'` bug the new pattern fixes.

- `FixCloudinaryUrlsSmokeTests`:
  - `test_command_dry_run_does_not_crash_on_real_data` — runs
    `fix_cloudinary_urls --dry-run` against a real ORM fixture with
    Cloudinary avatar + featured_image. Paired positive
    (`assertIn('Scanning')`) + negative (`assertNotIn('Traceback')`)
    assertions.

### NOT modified (scope respected)

- `prompts/management/commands/fix_admin_avatar.py` lines 60, 123 —
  P3 per spec (diagnostic log output only, not in URL or data path).

## Section 4 — Issues Encountered and Resolved

**Issue:** Spec claimed `str(CloudinaryResource)` returns object repr;
direct Python test showed it returns `public_id` in the current
cloudinary SDK version.
**Root cause:** The cloudinary SDK's `CloudinaryResource.__str__`
returns `self.public_id`. The 161-A report that motivated this spec
appears to have been based on either a different SDK version or an
incorrect observation.
**Fix applied:** Proceeded with the spec's intended fix anyway — it's
still independently justifiable (see Section 1). Documented the
discrepancy transparently in this report so future readers understand
why the comments reference `str(CloudinaryResource).__str__` concerns
even though the current SDK's `__str__` is benign.
**File:** N/A — report-level documentation.

**Issue:** First test run's plain-string fallback test included a dead
`MagicMock` setup followed by `del prompt_stub.featured_video` that
was never used (abandoned in favour of an inline class).
**Root cause:** Initial approach tried MagicMock but MagicMock's
auto-attribute-creation defeated the `hasattr(..., 'build_url') is
False` check the test needed.
**Fix applied:** Removed the dead MagicMock code. Kept only the
inline class approach. Flagged by three agents
(@code-reviewer, @python-pro, @tdd-orchestrator) on first pass and
cleaned up in-session.
**File:** `prompts/tests/test_vision_moderation_public_id.py` —
`test_plain_string_fallback_uses_public_id_pattern`.

## Section 5 — Remaining Issues

**Issue:** `prompts/management/commands/fix_admin_avatar.py` lines
60 and 123 still use `str(admin_profile.avatar)` for diagnostic log
output. Pattern-inconsistent with the 4 sites fixed here.
**Recommended fix:** Apply the same `.public_id` pattern in a future
defensive consistency spec, OR delete `fix_admin_avatar.py` entirely
if its one-off diagnostic purpose is no longer needed.
**Priority:** P3
**Reason not resolved:** Explicitly out of scope per spec — diagnostic
log only, no URL/data path impact. Preserved to avoid scope creep.

**Issue:** Pattern divergence from 161-A's simpler `getattr(field,
"public_id", "") or ""`. 162-C adds the `isinstance(field, str)`
fallback arm for the plain-string case that 161-A doesn't need
(migration command only operates on CloudinaryResource).
**Recommended fix:** Optionally extract to a shared utility
`prompts/utils/cloudinary.py::get_public_id(field)` in a future
cleanup spec, or leave as duplicated pattern in both call sites given
the Cloudinary migration's bounded lifetime.
**Priority:** P3
**Reason not resolved:** YAGNI. The pattern dies when `CloudinaryField`
is removed from models; extraction would need to be created, imported,
tested, then deleted within 1-2 sessions. Inline duplication is
correct for transitional code.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The spec's root-cause premise was factually incorrect
(`str(CloudinaryResource)` does not return repr in the current SDK).
Documenting this in the report, not burying it, prevents future
readers from being confused.
**Impact:** Moderate for future spec authors — the 161-A report's
claim that `str()` returned repr led to this entire spec chain, and
that claim was wrong. If similar claims appear in future specs, they
should be verified with a direct test.
**Recommended action:** Add a note to Session 162's end-of-session
closer (162-G) recommending the 160-F / 161-A `__str__` claim be
corrected in CLAUDE.md's narrative section.

**Concern:** The inline comments across the 4 sites reference
"161-A / 162-C pattern" but the 162-C pattern has a different shape
than 161-A (adds `isinstance` fallback). A future reader cross-
referencing 161-A in `migrate_cloudinary_to_b2.py` will see a
simpler pattern than 162-C uses.
**Impact:** Low.
**Recommended action:** When touching these sites again, either
align wording to say "162-C pattern" specifically, or extract a
shared helper. Deferred as P3 since the pattern is transitional.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 9.0/10 | No new SSRF surface, None case now safer, test fixtures clean, `isinstance` fallback preserves substring matching semantics | N/A — clean pass |
| 1 | @code-reviewer | 8.7/10 | All 4 sites identical pattern, comments consistent, imports clean, `fix_admin_avatar.py` correctly excluded. Noted dead MagicMock scaffolding in plain-string test | Yes — dead MagicMock code removed |
| 1 | @python-pro | 8.5/10 | Idiomatic `getattr + or` fallback, inline class pattern correct, test names follow convention. Dead MagicMock noted | Yes — removed |
| 1 | @django-pro | 8.5/10 | Pattern handles all 3 CloudinaryField states correctly, `refresh_from_db` placement right, all required Prompt fields provided in fixtures. Dead MagicMock + try/except patterns noted | Yes — MagicMock removed, try/except replaced with plain `call_command` + `assertNotIn('Traceback')` negative assertion |
| 1 | @tdd-orchestrator | 8.6/10 | Paired positive+negative assertions in all 4 tests, None case has strongest triple-assertion pattern, smoke test scope appropriate. Dead MagicMock + try/except noted | Yes — both cleaned up |
| 1 | @architect-review | 8.2/10 | Pattern correctness strong, None-safety elimination most valuable change, YAGNI on helper extraction correct, factual premise discrepancy needs clear report documentation, pattern divergence from 161-A is a minor doc issue | Documented in Sections 1 + 5 + 6 |
| **Average** | | **8.58/10** | | **Pass** ≥ 8.0 |

No re-run required — all agents ≥ 8.0 on first pass. Non-blocking
fixable findings (dead MagicMock, try/except) were acted on in-session.

## Section 8 — Recommended Additional Agents

All six agents from the spec's required set were run. @frontend-
developer was not needed (no template/UI change). The six-agent
baseline correctly covered security, code quality, Python idiom,
Django/ORM, TDD, and architecture. No additional agents would have
added material value.

## Section 9 — How to Test

### Automated

```bash
python manage.py test prompts.tests.test_vision_moderation_public_id --verbosity=2
# Expected: 4 tests (3 VisionModerationPublicIdTests + 1 FixCloudinaryUrlsSmokeTests), 0 failures.

python manage.py test prompts --verbosity=1
# Expected (session 162a final state): 1316 tests passing, 12 skipped.

python manage.py check
# Expected: 0 issues.
```

### Grep verification

```bash
# No remaining `str()` on CloudinaryField at the 4 target sites:
grep -n "str(.*\.featured_image\|str(.*\.featured_video\|str(.*\.avatar)" \
    prompts/services/vision_moderation.py \
    prompts/management/commands/fix_cloudinary_urls.py
# Expected: 0 matches.

# `fix_admin_avatar.py` lines 60, 123 still have `str()` (deferred P3):
grep -n "str(.*\.avatar)" prompts/management/commands/fix_admin_avatar.py
# Expected: 2 matches — line 60 and line 123.
```

### Manual Heroku verification (after deploy)

Tail logs during a video upload:
```bash
heroku logs --tail --app mj-project-4 | grep -i "vision\|moderation\|CloudinaryImage"
```
Confirm no malformed-URL or 404 errors from CloudinaryImage construction.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| d3b92dd | fix(moderation): use .public_id not str() on CloudinaryResource |

## Section 11 — What to Work on Next

1. **Proceed to full suite gate** — 162-A, 162-B, 162-C are all on
   HOLD with partial reports. Run the full test suite, fill Sections
   9 and 10, commit in order.
2. **Correct the `__str__` claim in CLAUDE.md and REPORT_161_A** —
   both documents state that `str(CloudinaryResource)` returns
   object repr. Current SDK evidence shows it returns public_id.
   Address in 162-G end-of-session closer.
3. **Future: align inline comments** — the 4 sites reference
   "161-A pattern" but use a different three-branch form. Either
   rename references or extract a helper. P3.
4. **Future: `fix_admin_avatar.py` cleanup** — if the file is still
   kept, apply the same pattern to lines 60 and 123 for consistency.
   If it's a one-off diagnostic that's no longer needed, delete.
5. **Post-full-suite: Heroku manual verification** per spec — upload
   a test video, tail logs, confirm no malformed URL errors from
   CloudinaryImage construction.
