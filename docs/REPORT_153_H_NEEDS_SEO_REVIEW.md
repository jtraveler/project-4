═══════════════════════════════════════════════════════════════
SPEC 153-H: NEEDS_SEO_REVIEW ON BULK PAGES — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

⏸ **STATUS: HOLD — partial report. Sections 9 and 10 pending full
suite pass** (per `CC_MULTI_SPEC_PROTOCOL.md` §Gate Sequence for
code specs in a multi-spec batch).

---

## Section 1 — Overview

Priority blocker before large-scale content seeding: the bulk
image generator's page-creation pipeline created `Prompt` objects
without setting `needs_seo_review=True`. Bulk-seeded pages
silently bypassed the SEO review queue, so the ~hundreds of pages
planned for Phase 1 content seeding would have shipped without
passing through the SEO workflow — violating the same demographic
SEO rules (Phase 2B-6/7) the queue is designed to enforce.

The single-upload pipeline correctly sets `needs_seo_review=True`
at `tasks.py:1437` and `:1538`, but the bulk pipeline was
overlooked. This fix brings the bulk pipeline in line with the
single-upload pattern and adds regression tests for both bulk
code paths.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `needs_seo_review=True` set on all Prompt objects created by the bulk pipeline | ✅ Met |
| Stale "GPT-Image-1" comment at line ~3323 updated to "GPT-Image-1.5" | ✅ Met |
| All Prompt creation sites in the bulk pipeline verified and fixed | ✅ Met (both sites: 3315 and 3583) |
| Full suite passes | ⏸ Pending — partial report |

## Section 3 — Changes Made

### prompts/tasks.py (🔴 Critical tier — 2 sed edits)

Step 0 grep 1 confirmed **two** `prompt_page = Prompt(...)`
constructors in the bulk pipeline:

- **Line 3315** — `create_prompt_pages_from_job` (sequential path,
  older)
- **Line 3583** — `publish_prompt_pages_from_job` (concurrent
  ThreadPoolExecutor path, Phase 6B)

The spec only explicitly flagged line 3315, but Step 0 grep 3
asked me to verify whether `publish_prompt_pages_from_job` also
creates `Prompt` objects. It does — so the fix covers **both**
sites.

**Change 1 — Add `needs_seo_review=True` to both constructors.**
The sed anchor `processing_complete=True,      # bulk-gen prompts
are fully processed at creation time` is unique to these two
constructors, so a single sed `/g` command hits both sites
simultaneously and guarantees they stay in lockstep:

```bash
sed -i "s|                processing_complete=True,      # bulk-gen prompts are fully processed at creation time|                processing_complete=True,      # bulk-gen prompts are fully processed at creation time\n                needs_seo_review=True,         # bulk-created pages always require SEO review (153-H)|g" prompts/tasks.py
```

Result after edit:

```python
# Line 3315-3326 (create_prompt_pages_from_job)
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1.5',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1.5 content policy applied at generation time
    processing_complete=True,      # bulk-gen prompts are fully processed at creation time
    needs_seo_review=True,         # bulk-created pages always require SEO review (153-H)
)

# Line 3583-3594 (publish_prompt_pages_from_job, concurrent path)
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1.5',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1 content policy applied at gen time
    processing_complete=True,      # bulk-gen prompts are fully processed at creation time
    needs_seo_review=True,         # bulk-created pages always require SEO review (153-H)
)
```

Note: the stale comment at line 3591 still reads "GPT-Image-1
content policy applied at gen time". That's a different string
than the one at 3323 ("GPT-Image-1 already applied content
policy") and is out of scope for 153-H — Spec 153-I fixes it next
as a bundled cleanup item.

**Change 2 — Fix stale comment at line 3323.**

```bash
sed -i "s|moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy|moderation_status='approved',  # staff-created; GPT-Image-1.5 content policy applied at generation time|" prompts/tasks.py
```

The anchor string is unique to line 3323 — line 3591 has
different wording, so this sed is scoped.

### prompts/tests/test_bulk_page_creation.py (✅ Safe tier)

**Test 1 — added to `VisibilityMappingTests` class (line ~345):**

```python
@patch('prompts.tasks._call_openai_vision')
def test_bulk_created_pages_have_needs_seo_review_true(self, mock_vision):
    """153-H: ... Regression guard — both public and private
    visibility must set the flag."""
    mock_vision.return_value = MOCK_AI_CONTENT

    job_public = _make_job(self.staff_user, visibility='public')
    img_public = _make_image(job_public)
    create_prompt_pages_from_job(str(job_public.id), [str(img_public.id)])
    img_public.refresh_from_db()
    self.assertTrue(img_public.prompt_page.needs_seo_review, ...)

    job_private = _make_job(self.staff_user, visibility='private')
    img_private = _make_image(job_private)
    create_prompt_pages_from_job(str(job_private.id), [str(img_private.id)])
    img_private.refresh_from_db()
    self.assertTrue(img_private.prompt_page.needs_seo_review, ...)
```

Covers the sequential `create_prompt_pages_from_job` path for
both public and private visibility.

**Test 2 — added to `PublishTaskTests` class (line ~1272):**

Added after agent review flagged the coverage gap. Both
@tdd-orchestrator (8.2/10) and @code-reviewer (8.7/10) noted that
the first test only covered the sequential path, not the
concurrent `publish_prompt_pages_from_job` path. Since the two
paths have independent `Prompt(...)` constructors that could
drift, both paths need their own regression guard.

```python
@patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
def test_publish_sets_needs_seo_review_true(self, _mock_vision):
    """153-H: The concurrent publish path must also set
    needs_seo_review=True on the created Prompt. ..."""
    self.publish(str(self.job.id), [str(self.img.id)])

    self.img.refresh_from_db()
    self.assertIsNotNone(self.img.prompt_page)
    self.assertTrue(self.img.prompt_page.needs_seo_review, ...)
```

Both tests pass. Targeted run:
```
Ran 2 tests in 1.524s
OK
```

### Step 2 Verification Outputs

```
=== 1. needs_seo_review in tasks.py ===
1437:                    prompt.needs_seo_review = True
1438:                    prompt.save(update_fields=['needs_seo_review'])
1538:        prompt.needs_seo_review = True  # Flag for manual review
1539:        prompt.save(update_fields=['title', 'excerpt', 'slug', 'processing_complete', 'needs_seo_review'])
3325:                needs_seo_review=True,         # bulk-created pages always require SEO review (153-H)
3594:                needs_seo_review=True,         # bulk-created pages always require SEO review (153-H)

=== 2. Stale comment fixed at 3323 ===
3323:                moderation_status='approved',  # staff-created; GPT-Image-1.5 content policy applied at generation time

=== 3. processing_complete still intact ===
3324:                processing_complete=True,      # bulk-gen prompts are fully processed at creation time
3593:                processing_complete=True,      # bulk-gen prompts are fully processed at creation time

=== 4. python manage.py check ===
System check identified no issues (0 silenced).
```

## Section 4 — Issues Encountered and Resolved

**Issue 1:** The spec flagged only the line 3315 constructor, but
Step 0 grep 1 revealed a second constructor at line 3583 in
`publish_prompt_pages_from_job`. Without fixing both, the
concurrent publish path would still have shipped pages without
`needs_seo_review=True`.
**Root cause:** The spec's Step 0 grep 3 explicitly asked me to
check for a second Prompt constructor, which is exactly how this
was caught. The spec author anticipated this possibility.
**Fix applied:** The sed command used the `/g` global flag to
deliberately hit both sites in one operation. The anchor is
identical in both constructors, so this produces lockstep updates
and prevents the two paths from drifting in the future.

**Issue 2:** After initial agent review, both @tdd-orchestrator
(8.2/10) and @code-reviewer (8.7/10) flagged a coverage gap: the
initial test covered `create_prompt_pages_from_job` (sequential)
but not `publish_prompt_pages_from_job` (concurrent). Since the
two paths have independent constructors that could drift, both
needed their own regression guard.
**Root cause:** I initially wrote a single test for the spec's
primary target function and did not add a parallel test for the
second constructor I had just patched.
**Fix applied:** Added a second test
(`test_publish_sets_needs_seo_review_true`) in the `PublishTaskTests`
class. Both tests pass. The fix was applied before this partial
report was written, so both agent findings are closed on the
first round — no re-run needed.

No other issues encountered.

## Section 5 — Remaining Issues

**Issue (noted by @backend-security-coder):** Line 3591 still
reads `"# staff-created; GPT-Image-1 content policy applied at
gen time"`. This is a stale "GPT-Image-1" reference that should
say "GPT-Image-1.5".
**Recommended fix:** Already in scope for Spec 153-I (the next
spec in this batch). Will be fixed as part of item 3 of that
spec's cleanup list.
**Priority:** P3 (cosmetic — code behavior is correct).
**Reason not resolved in this spec:** Out of scope. Spec 153-H is
about the `needs_seo_review` flag; the stale comment is a
separate cleanup item bundled into 153-I.

**Issue (noted by @tdd-orchestrator):** The IntegrityError retry
test (`SlugRaceConditionTests.test_integrity_error_triggers_uuid_suffix_retry`)
does not currently assert `needs_seo_review=True` on the
retried Prompt. Since the retry path reuses the same
`prompt_page` instance and only mutates `title`/`slug` before
re-saving (confirmed by @backend-security-coder via code
inspection), the flag is preserved automatically — but a
regression guard would lock this in.
**Recommended fix:** Add a one-line
`self.assertTrue(prompt_page.needs_seo_review)` inside the
existing retry test.
**Priority:** P3 — additional test coverage, not a bug fix.
**Reason not resolved:** Out of scope for this spec. The flag is
already preserved by the retry path's mechanics, and the two
added tests give adequate coverage for the two constructor sites
themselves.

## Section 6 — Concerns and Areas for Improvement

**Concern (noted by @code-reviewer):** The single-upload pipeline
uses a post-save pattern (`prompt.needs_seo_review = True` +
`prompt.save(update_fields=[...])`) while the bulk pipeline now
uses a constructor-argument pattern (`Prompt(...,
needs_seo_review=True)`). Both achieve identical end state, but
the inconsistency could confuse future readers.
**Impact:** Low. Both patterns are valid Django idioms and both
are atomic with the `.save()` call. The constructor approach is
slightly cleaner for the bulk case because the AI content is
already in hand at construction time and doesn't need an
additional save round-trip.
**Recommended action:** Consider adding an inline comment at the
single-upload site explaining why it uses post-save (because the
flag is set after async AI content arrives) and an inline comment
at the bulk site explaining why it uses constructor-argument
(because AI content is in hand at construction time). Not in
scope for this spec; flag for a future cleanup pass.

**Concern:** `needs_seo_review=True` is now a boolean literal at
the constructor site. If the bulk pipeline ever needs conditional
review (e.g. "skip review if the image is in an allowlisted
category"), the current hardcoded `=True` will need to become a
function call. Not a current issue — the SEO review queue's
policy is "all bulk-seeded pages require review" — but worth
flagging for when Phase 1 content seeding reveals real-world
review fatigue.

## Section 7 — Agent Ratings

**Agent name mapping (Option B — authorised by developer for this
batch only):**
- Spec nominally required `@django-security` → substituted with
  **`@backend-security-coder`** (most relevant registry agent for
  backend Django input-validation + atomic-write review).
- Spec nominally required `@tdd-coach` → substituted with
  **`@tdd-orchestrator`** (the registry TDD review agent).
- `@code-reviewer` required no substitution.

Per the Session 153 Batch 2 run instructions, the hard rule
("use exact agent names, stop and report if unavailable") is
lifted one time for this batch and reinstated for future
sessions. Spec templates should be updated to use
registry-correct names going forward.

| Round | Agent (registry name) | Score | Key Findings | Acted On? |
|-------|-----------------------|-------|--------------|-----------|
| 1 | @backend-security-coder (spec: `@django-security`) | 9.5/10 | All 5 verification points pass: atomic constructor, complete coverage (both 3325 and 3594), IntegrityError retry preserves the flag (retry block reuses same `prompt_page` instance), no data leakage, model field confirmed at line 880. Flagged the P3 lingering "GPT-Image-1" comment at line 3591 as noted in Section 5. | No — deferred to 153-I (in scope there) |
| 1 | @tdd-orchestrator (spec: `@tdd-coach`) | 8.2/10 | Confirmed coverage adequate for `create_prompt_pages_from_job`; **flagged gap: no test covers `publish_prompt_pages_from_job` independently**. Also noted IntegrityError retry test could assert the flag. Class placement in `VisibilityMappingTests` acceptable. | **Yes** — added `test_publish_sets_needs_seo_review_true` in `PublishTaskTests`. Both tests pass. |
| 1 | @code-reviewer | 8.7/10 | sed `/g` flag correct, stale comment fix scoped (line 3323 only, line 3591 untouched), single-upload vs bulk pattern difference acceptable. **Same coverage gap as @tdd-orchestrator** — add parallel test for concurrent path. | **Yes** — same fix as above |
| **Average** | | **8.8/10** | — | **Pass ≥8.0** |

The @tdd-orchestrator and @code-reviewer coverage gap was
identified before agent scores were considered final, fixed
immediately, and both tests verified passing. The 8.2/10 score
from @tdd-orchestrator was awarded before the fix was applied;
post-fix the coverage complaint is resolved but I did not re-run
the agent because the average already exceeds 8.0 and the gap is
closed.

## Section 8 — Recommended Additional Agents

The spec required 3 agents; 3 were used (with the two Option B
substitutions documented above). No additional agents would have
added material value.

**@django-pro** could have been an optional second-opinion
reviewer for the Django constructor pattern (post-save vs
constructor-argument) but the @code-reviewer finding already
covered that ground.

## Section 9 — How to Test

*To be filled in after full test suite passes at the end of this
batch (per the batch's run instructions — code specs H, I, J all
write partial reports and commit together after one full suite
run).*

## Section 10 — Commits

*To be filled in after full test suite passes.*

Intended single commit (from spec):

```
fix(bulk-gen): set needs_seo_review=True on bulk-created prompt pages

All Prompt objects created by create_prompt_pages_from_job now have
needs_seo_review=True. Previously bulk-created pages silently bypassed
the SEO review queue. Also fixes stale 'GPT-Image-1' comment.
```

## Section 11 — What to Work on Next

1. **Proceed to Spec 153-I** — the P2/P3 cleanup batch spec. Will
   fix the remaining stale "GPT-Image-1 content policy applied at
   gen time" comment at line 3591 flagged by
   @backend-security-coder in this review.
2. **Optional: strengthen IntegrityError retry test coverage
   (P3)** — add a one-line
   `self.assertTrue(prompt_page.needs_seo_review)` inside
   `test_integrity_error_triggers_uuid_suffix_retry` in
   `SlugRaceConditionTests`. Locks in the automatic preservation
   that @backend-security-coder verified via code inspection.
   Not in scope for this spec; flag for a future cleanup pass.
3. **Optional: inline comments explaining the post-save vs
   constructor-argument pattern difference (P3)** — flagged by
   @code-reviewer as a readability improvement. Single-upload uses
   post-save because AI content arrives asynchronously; bulk uses
   constructor-argument because AI content is in hand at
   construction time.

═══════════════════════════════════════════════════════════════
